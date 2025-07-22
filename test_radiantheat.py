import unittest
import numpy as np
import json
from radiantheat import generate_grid, generate_coordinates, validate_inputs

class TestRadiantHeating(unittest.TestCase):
    def setUp(self):
        """Set up test cases with common room dimensions"""
        self.room_length = 10.0
        self.room_width = 10.0
        self.pipe_spacing = 1.0
        
        # Load test coordinates from JSON
        with open('test_coordinates.json', 'r') as f:
            self.test_data = json.load(f)
        
    def test_validate_inputs(self):
        """Test input validation function"""
        # Test valid inputs
        is_valid, message = validate_inputs(10.0, 8.0, 0.5)
        self.assertTrue(is_valid)
        
        # Test invalid room length
        is_valid, message = validate_inputs(0, 8.0, 0.5)
        self.assertFalse(is_valid)
        self.assertIn("length", message.lower())
        
        # Test invalid room width
        is_valid, message = validate_inputs(10.0, 0, 0.5)
        self.assertFalse(is_valid)
        self.assertIn("width", message.lower())
        
        # Test invalid pipe spacing
        is_valid, message = validate_inputs(10.0, 8.0, 0)
        self.assertFalse(is_valid)
        self.assertIn("spacing", message.lower())
        
        # Test pipe spacing too large
        is_valid, message = validate_inputs(10.0, 8.0, 5.0)
        self.assertFalse(is_valid)
        self.assertIn("too large", message.lower())
        
        # Test warning for small pipe spacing
        is_valid, message = validate_inputs(10.0, 8.0, 0.05)
        self.assertFalse(is_valid)
        self.assertIn("continue", message.lower())

    def test_generate_grid(self):
        """Test grid generation function"""
        x_positions, y_positions, num_vertical, num_horizontal = generate_grid(
            self.room_length, self.room_width, self.pipe_spacing
        )
        
        # Check that grid dimensions are correct
        self.assertGreater(len(x_positions), 0)
        self.assertGreater(len(y_positions), 0)
        
        # Check that grid lines are within room boundaries
        self.assertGreaterEqual(min(x_positions), self.pipe_spacing)
        self.assertLessEqual(max(x_positions), self.room_width - self.pipe_spacing)
        self.assertGreaterEqual(min(y_positions), self.pipe_spacing)
        self.assertLessEqual(max(y_positions), self.room_length - self.pipe_spacing)
        
        # Check grid spacing
        for i in range(1, len(x_positions)):
            self.assertAlmostEqual(x_positions[i] - x_positions[i-1], self.pipe_spacing)
        for i in range(1, len(y_positions)):
            self.assertAlmostEqual(y_positions[i] - y_positions[i-1], self.pipe_spacing)
        
        # Check that number of lines is even for vertical lines
        self.assertEqual(num_vertical % 2, 0)

    def test_grid_alignment(self):
        """Test that generated coordinates align with grid"""
        coords, x_pos, y_pos, num_vert, num_horiz, _ = generate_coordinates(
            self.room_length, self.room_width, self.pipe_spacing
        )
        
        # Check that all points lie on grid lines
        for x, y in coords:
            # Point should be on a vertical grid line
            self.assertTrue(
                any(np.isclose(x, grid_x) for grid_x in x_pos),
                f"Point {x},{y} not on vertical grid line"
            )
            # Point should be on a horizontal grid line
            self.assertTrue(
                any(np.isclose(y, grid_y) for grid_y in y_pos),
                f"Point {x},{y} not on horizontal grid line"
            )

    def test_invalid_room_size(self):
        """Test handling of rooms too small for specified spacing"""
        # Room too small for even 2x2 grid
        with self.assertRaises(ValueError):
            generate_grid(1.0, 1.0, 0.6)
        
        with self.assertRaises(ValueError):
            generate_coordinates(1.0, 1.0, 0.6)

    def test_coordinate_sequence(self):
        """Test the exact sequence of coordinates for a 10x10 room with 1m spacing"""
        test_case = self.test_data["10x10_1m"]
        coords, _, _, _, _, total_length = generate_coordinates(
            test_case["room_length"],
            test_case["room_width"],
            test_case["pipe_spacing"]
        )
        
        expected_coords = test_case["expected_coords"]
        
        # Verify sequence length
        self.assertEqual(len(coords), len(expected_coords),
            f"Expected {len(expected_coords)} coordinates but got {len(coords)}")
        
        # Verify each coordinate matches
        for i, (expected, actual) in enumerate(zip(expected_coords, coords)):
            self.assertAlmostEqual(actual[0], expected[0], 2,
                f"X coordinate mismatch at position {i}: expected {expected[0]}, got {actual[0]}")
            self.assertAlmostEqual(actual[1], expected[1], 2,
                f"Y coordinate mismatch at position {i}: expected {expected[1]}, got {actual[1]}")
        
        # Verify total pipe length
        self.assertAlmostEqual(total_length, test_case["expected_length"], 2,
            f"Expected pipe length of {test_case['expected_length']}m but got {total_length}m")

    def test_coordinate_spacing(self):
        """Test that all adjacent coordinates maintain proper spacing"""
        coords, _, _, _, _, _ = generate_coordinates(
            self.room_length, self.room_width, self.pipe_spacing
        )
        
        for i in range(1, len(coords)):
            prev = coords[i-1]
            curr = coords[i]
            
            # Calculate distance between points
            dx = curr[0] - prev[0]
            dy = curr[1] - prev[1]
            distance = np.sqrt(dx**2 + dy**2)
            
            # Distance should be either pipe_spacing or 0
            self.assertTrue(
                np.isclose(distance, self.pipe_spacing) or np.isclose(distance, 0),
                f"Invalid spacing {distance} between points {prev} and {curr}"
            )

    def test_90_degree_turns(self):
        """Test that all turns are exactly 90 degrees"""
        coords, _, _, _, _, _ = generate_coordinates(
            self.room_length, self.room_width, self.pipe_spacing
        )
        
        for i in range(1, len(coords) - 1):
            prev = coords[i-1]
            curr = coords[i]
            next = coords[i+1]
            
            # Calculate direction changes
            dx1 = curr[0] - prev[0]
            dy1 = curr[1] - prev[1]
            dx2 = next[0] - curr[0]
            dy2 = next[1] - curr[1]
            
            # At least one direction should be 0 (no diagonal movement)
            self.assertTrue(np.isclose(dx1, 0) or np.isclose(dy1, 0),
                f"Diagonal movement detected at position {i} between {prev} and {curr}")
            self.assertTrue(np.isclose(dx2, 0) or np.isclose(dy2, 0),
                f"Diagonal movement detected at position {i} between {curr} and {next}")
            
            # If both directions change, it should be a 90-degree turn
            if not (np.isclose(dx1, dx2) and np.isclose(dy1, dy2)):  # Direction changed
                dot_product = dx1 * dx2 + dy1 * dy2
                self.assertTrue(np.isclose(dot_product, 0),
                    f"Non-90-degree turn detected at position {i} at point {curr}")

if __name__ == '__main__':
    unittest.main() 