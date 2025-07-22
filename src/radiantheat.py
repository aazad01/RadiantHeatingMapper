import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.collections import LineCollection
import matplotlib.colors as mcolors
import time

def create_arc(start_point, end_point, bend_radius, num_points=10):
    """
    Creates a smooth arc between two points with a given bend radius.
    Returns list of points forming the arc.
    """
    # Get vector between points
    dx = end_point[0] - start_point[0]
    dy = end_point[1] - start_point[1]
    
    # If points are too close for the bend radius, adjust radius
    min_distance = np.sqrt(dx**2 + dy**2)
    if min_distance < 2 * bend_radius:
        bend_radius = min_distance / 2.5
    
    # Calculate center point of the arc
    mid_x = (start_point[0] + end_point[0]) / 2
    mid_y = (start_point[1] + end_point[1]) / 2
    
    # Calculate angle between points
    angle = np.arctan2(dy, dx)
    
    # Create arc points
    if abs(dx) > abs(dy):  # Horizontal to vertical transition
        if dy > 0:  # Going up
            start_angle = -np.pi/2
            end_angle = 0 if dx > 0 else -np.pi
        else:  # Going down
            start_angle = np.pi/2
            end_angle = 0 if dx > 0 else -np.pi
    else:  # Vertical to horizontal transition
        if dx > 0:  # Going right
            start_angle = np.pi if dy > 0 else 0
            end_angle = np.pi/2 if dy > 0 else -np.pi/2
        else:  # Going left
            start_angle = 0 if dy > 0 else -np.pi
            end_angle = np.pi/2 if dy > 0 else -np.pi/2
    
    # Generate arc points
    angles = np.linspace(start_angle, end_angle, num_points)
    arc_points = []
    for angle in angles:
        x = mid_x + bend_radius * np.cos(angle)
        y = mid_y + bend_radius * np.sin(angle)
        arc_points.append((x, y))
    
    return arc_points

def generate_grid(room_length, room_width, pipe_spacing):
    """
    Generate grid lines based on pipe spacing.
    Returns lists of x and y coordinates for grid lines.
    """
    # Calculate grid lines with spacing
    x_min = pipe_spacing
    x_max = room_width - pipe_spacing
    y_min = pipe_spacing
    y_max = room_length - pipe_spacing
    
    # Calculate number of possible vertical and horizontal lines in the grid
    num_vertical_lines = int((room_width - 2 * pipe_spacing) / pipe_spacing) + 1
    num_horizontal_lines = int((room_length - 2 * pipe_spacing) / pipe_spacing) + 1
    
    # Ensure we have enough space for at least a 2x2 grid
    if num_vertical_lines < 2 or num_horizontal_lines < 2:
        raise ValueError("Room too small for specified spacing")
    
    # Make number of vertical lines even for symmetrical layout
    if num_vertical_lines % 2 != 0:
        num_vertical_lines -= 1  # Decrease to ensure we don't exceed room width
    
    # Calculate actual positions of grid lines with exact spacing
    x_positions = []
    for i in range(num_vertical_lines):
        x = x_min + i * pipe_spacing
        if x <= x_max:  # Only add points within room bounds
            x_positions.append(x)
    
    y_positions = []
    for i in range(num_horizontal_lines):
        y = y_min + i * pipe_spacing
        if y <= y_max:  # Only add points within room bounds
            y_positions.append(y)
    
    print(f"\nGrid Information:")
    print(f"Vertical lines: {len(x_positions)}")
    print(f"Horizontal lines: {len(y_positions)}")
    print(f"Grid spacing: {pipe_spacing}m")
    
    return x_positions, y_positions, len(x_positions), len(y_positions)

def calculate_pipe_length(coords):
    """
    Calculate the total length of pipe used in meters.
    """
    total_length = 0
    for i in range(1, len(coords)):
        dx = coords[i][0] - coords[i-1][0]
        dy = coords[i][1] - coords[i-1][1]
        segment_length = np.sqrt(dx**2 + dy**2)
        total_length += segment_length
    return total_length

def generate_coordinates(room_length, room_width, pipe_spacing):
    """
    Step by step pipe layout for a 10x10 room with 1m spacing:
    
    1. Start at (1,1)
    2. Go up vertically to (1,9)
    3. Serpentine pattern until (8,2)
    4. Go down to (8,1)
    5. Return along bottom row to (2,1)
    
    Returns:
    - coords: List of (x,y) coordinates for the pipe path
    - x_positions: List of x coordinates for grid lines
    - y_positions: List of y coordinates for grid lines
    - num_vertical_lines: Number of vertical grid lines
    - num_horizontal_lines: Number of horizontal grid lines
    - total_length: Total length of pipe used in meters
    """
    # Calculate grid points
    x_min = 1.0
    x_max = room_width - 1.0
    y_min = 1.0
    y_max = room_length - 1.0
    
    # Calculate number of vertical and horizontal lines
    num_vertical_lines = int((room_width - 2) / pipe_spacing) + 1
    num_horizontal_lines = int((room_length - 2) / pipe_spacing) + 1
    
    # Ensure we have enough space for at least a 2x2 grid
    if num_vertical_lines < 2 or num_horizontal_lines < 2:
        raise ValueError("Room too small for specified spacing")
    
    # Make number of vertical lines even for symmetrical layout
    if num_vertical_lines % 2 != 0:
        num_vertical_lines -= 1
    
    # Generate grid points
    x_positions = [x_min + i * pipe_spacing for i in range(num_vertical_lines)]
    y_positions = [y_min + i * pipe_spacing for i in range(num_horizontal_lines)]
    
    coords = []
    
    # Starting point (bottom left corner)
    start_x = x_positions[0]  # This will be 1.0
    start_y = y_positions[0]  # This will be 1.0
    coords.append((start_x, start_y))
    
    # Initial vertical run - go all the way up
    for y in y_positions[1:]:  # Skip first point since we're already there
        coords.append((start_x, y))
    
    # Serpentine pattern
    for i in range(1, len(x_positions)):
        x = x_positions[i]
        
        if i % 2 == 1:  # Moving down
            coords.append((x, y_positions[-1]))  # Move right at top
            
            # Move down to second row
            for y in reversed(y_positions[1:]):  # Include second row
                coords.append((x, y))
            
            # If not last column, move right at second row
            if i < len(x_positions) - 1:
                coords.append((x_positions[i + 1], y_positions[1]))
        else:  # Moving up
            # Move up from second row to top
            for y in y_positions[1:]:  # Start from second row
                coords.append((x, y))
            
            # If not last column, move right at top
            if i < len(x_positions) - 1:
                coords.append((x_positions[i + 1], y_positions[-1]))
    
    # Now we're at the last vertical line, move down to bottom row
    last_x = x_positions[-1]
    coords.append((last_x, y_positions[0]))
    
    # Return path along bottom row (don't go back to start)
    for x in reversed(x_positions[1:-1]):  # Skip first and last points
        coords.append((x, y_positions[0]))
    
    # Remove any duplicate consecutive points while preserving path order
    deduped_coords = []
    for i in range(len(coords)):
        if i == 0 or coords[i] != coords[i-1]:
            deduped_coords.append(coords[i])
    coords = deduped_coords
    
    # Calculate total pipe length
    total_length = calculate_pipe_length(coords)
    
    # Calculate coverage area
    usable_width = room_width - 2
    usable_length = room_length - 2
    coverage_area = usable_width * usable_length
    total_area = room_width * room_length
    coverage_percent = (coverage_area / total_area) * 100
    
    print(f"\nGrid Information:")
    print(f"Vertical lines: {num_vertical_lines}")
    print(f"Horizontal lines: {num_horizontal_lines}")
    print(f"Grid spacing: {pipe_spacing}m")
    print(f"\nCoverage Information:")
    print(f"Room area: {total_area:.2f}m²")
    print(f"Covered area: {coverage_area:.2f}m²")
    print(f"Coverage percentage: {coverage_percent:.1f}%")
    print(f"\nPipe Information:")
    print(f"Total pipe length: {total_length:.2f}m")
    print(f"Pipe length per m² of room: {(total_length/total_area):.2f}m/m²")
    print(f"\nPath Information:")
    print(f"Generated {len(coords)} coordinate points")
    print(f"Path starts at: ({coords[0][0]:.2f}, {coords[0][1]:.2f})")
    print(f"Path ends at: ({coords[-1][0]:.2f}, {coords[-1][1]:.2f})")
    print(f"Coverage: x range [{min(x_positions):.2f}, {max(x_positions):.2f}], "
          f"y range [{min(y_positions):.2f}, {max(y_positions):.2f}]")
    
    return coords, x_positions, y_positions, num_vertical_lines, num_horizontal_lines, total_length

def validate_inputs(room_length, room_width, pipe_spacing):
    """
    Validates the input parameters for the radiant heating layout.
    Returns (is_valid, message) tuple.
    """
    if room_length <= 0:
        return False, "Room length must be greater than 0 meters"
    if room_width <= 0:
        return False, "Room width must be greater than 0 meters"
    if pipe_spacing <= 0:
        return False, "Pipe spacing must be greater than 0 meters"
    
    # Check if pipe spacing is too large relative to room dimensions
    min_dimension = min(room_length, room_width)
    if pipe_spacing >= min_dimension / 2:
        return False, f"Pipe spacing ({pipe_spacing}m) is too large for room dimensions. Must be less than {min_dimension/2:.2f}m"
    
    # Check if pipe spacing is unreasonably small
    if pipe_spacing < 0.1:
        return False, "Warning: Pipe spacing less than 0.1m may be impractical. Continue? (y/n): "
    
    return True, ""

def get_valid_input(prompt, input_type=float, min_value=0):
    """Helper function to get valid numerical input from user"""
    while True:
        try:
            value = input_type(input(prompt))
            if value > min_value:
                return value
            print(f"Please enter a value greater than {min_value}")
        except ValueError:
            print(f"Please enter a valid number")

def radiant_heating_layout(room_length, room_width, pipe_spacing=0.2):
    """
    Creates a radiant heating pipe layout visualization.
    For rooms larger than 600 square meters, shows static layout instead of animation.
    Animation speed is optimized for both small and large rooms.
    """
    try:
        # Validate inputs
        is_valid, message = validate_inputs(room_length, room_width, pipe_spacing)
        if not is_valid:
            if "Continue?" in message:
                response = input(message).lower()
                if response != 'y':
                    print("Operation cancelled by user")
                    return False
            else:
                print(message)
                return False

        print(f"\nCalculating layout for room {room_length}m x {room_width}m with {pipe_spacing}m spacing...")
        
        # Generate coordinates and grid
        try:
            coords, x_positions, y_positions, num_vertical_lines, num_horizontal_lines, total_length = generate_coordinates(room_length, room_width, pipe_spacing)
        except ValueError as e:
            print(f"Error generating coordinates: {str(e)}")
            return False
        except Exception as e:
            print(f"Unexpected error during coordinate generation: {str(e)}")
            return False
        
        if not coords:
            print("Failed to generate valid pipe layout - no coordinates generated")
            return False
            
        if len(coords) < 2:
            print("Failed to generate valid pipe layout - insufficient points for animation")
            return False

        # Calculate room area and determine visualization mode
        room_area = room_length * room_width
        is_large_room = room_area > 600
        
        if is_large_room:
            print(f"\nRoom area ({room_area:.1f}m²) exceeds 600m². Showing static layout.")
        else:
            print(f"\nRoom area ({room_area:.1f}m²). Showing animated layout.")

        # Set up the plot with extra space for legend
        plt.ion()  # Turn on interactive mode
        fig = plt.figure(figsize=(12, 8))  # Make figure wider to accommodate legend
        
        # Create main axes with room for legend on right
        ax = fig.add_axes([0.1, 0.1, 0.7, 0.8])  # [left, bottom, width, height]
        
        # Plot room outline
        room = ax.fill([0, room_width, room_width, 0], [0, 0, room_length, room_length],
                      alpha=0.1, color='gray', label='Room')
        
        # Plot grid
        for x in x_positions:
            ax.plot([x, x], [0, room_length], 'k:', alpha=0.2)
        for y in y_positions:
            ax.plot([0, room_width], [y, y], 'k:', alpha=0.2)
        
        # Plot boundary
        boundary = ax.plot([pipe_spacing, room_width-pipe_spacing, room_width-pipe_spacing, pipe_spacing, pipe_spacing],
                         [pipe_spacing, pipe_spacing, room_length-pipe_spacing, room_length-pipe_spacing, pipe_spacing],
                         'r--', alpha=0.5, label='Pipe Offset Boundary')

        if is_large_room:
            # For large rooms, plot the entire path at once
            # Find the transition point from supply to return
            # This is where we reach the rightmost point before returning
            max_x = max(coord[0] for coord in coords)
            transition_idx = next(i for i, coord in enumerate(coords) if coord[0] == max_x)
            
            # Plot supply section in red->yellow gradient
            supply_x = [coord[0] for coord in coords[:transition_idx + 1]]  # Include transition point
            supply_y = [coord[1] for coord in coords[:transition_idx + 1]]
            ax.plot(supply_x, supply_y, 'r-', linewidth=3, label='Supply Line')
            
            # Plot return section in blue gradient
            return_x = [coord[0] for coord in coords[transition_idx:]]  # Include transition point
            return_y = [coord[1] for coord in coords[transition_idx:]]
            ax.plot(return_x, return_y, 'b-', linewidth=3, label='Return Line')
            
            ax.set_title('Radiant Heating Pipe Layout')
        else:
            # For smaller rooms, use animation
            # Create color gradients for supply and return
            supply_cmap = plt.cm.RdYlBu_r
            return_cmap = plt.cm.RdYlBu
            
            # Initialize empty line collections for installed pipe segments
            installed_segments = LineCollection([], linewidth=3, label='Heating Pipe')
            ax.add_collection(installed_segments)
            
            # Initialize pipe head (installation point) and trail
            pipe_head, = ax.plot([], [], 'ko', markersize=10, label='Installation Point')
            trail, = ax.plot([], [], 'ko', markersize=4, alpha=0.5, label='Installation Trail')
            
            # Add pause frames at start and end
            pause_frames = 20
            
            # Calculate total frames and interval
            total_frames = len(coords) + 2 * pause_frames
            
            # Set minimum and maximum intervals for smooth animation
            min_interval = 5  # milliseconds (fastest)
            max_interval = 30  # milliseconds (slowest)
            target_duration = 10000  # aim for 10 seconds
            
            # Calculate interval to target 10 seconds, but clamp between min and max
            interval = min(max_interval, max(min_interval, target_duration / total_frames))
            
            actual_duration = total_frames * interval / 1000
            print(f"\nAnimation settings:")
            print(f"Total frames: {total_frames}")
            print(f"Frame interval: {interval:.1f}ms")
            print(f"Total duration: {actual_duration:.1f} seconds")
            
            def update(frame):
                # Handle pause frames at start and end
                if frame < pause_frames:
                    actual_frame = 0
                elif frame >= len(coords) + pause_frames:
                    actual_frame = len(coords) - 1
                else:
                    actual_frame = frame - pause_frames

                # Create segments
                if actual_frame > 0:  # Only create segments if we have at least two points
                    segments = []
                    colors = []
                    for i in range(min(actual_frame, len(coords)-1)):
                        segments.append([coords[i], coords[i+1]])
                        # Color based on supply (first half) or return (second half)
                        if i < len(coords) // 2:
                            color = supply_cmap(i / (len(coords) // 2))
                        else:
                            color = return_cmap((i - len(coords) // 2) / (len(coords) // 2))
                        colors.append(color)
                    
                    # Update installed segments
                    installed_segments.set_segments(segments)
                    installed_segments.set_color(colors)
                
                # Update pipe head position and trail
                if actual_frame < len(coords):
                    current_pos = coords[actual_frame]
                    pipe_head.set_data([current_pos[0]], [current_pos[1]])
                    
                    # Create trail effect (last 5 points)
                    trail_length = 5
                    trail_start = max(0, actual_frame - trail_length)
                    trail_x = [coord[0] for coord in coords[trail_start:actual_frame]]
                    trail_y = [coord[1] for coord in coords[trail_start:actual_frame]]
                    trail.set_data(trail_x, trail_y)
                
                # Update progress in title
                if actual_frame == 0:
                    ax.set_title('Radiant Heating Pipe Layout (Starting Installation...)')
                elif actual_frame >= len(coords) - 1:
                    ax.set_title('Radiant Heating Pipe Layout (Installation Complete!)')
                else:
                    progress = (actual_frame / len(coords)) * 100
                    ax.set_title(f'Radiant Heating Pipe Layout ({progress:.1f}% Installed)')
                
                return installed_segments, pipe_head, trail
            
            # Create animation with pause frames and repeat
            anim = FuncAnimation(fig, update, frames=total_frames, interval=interval, 
                               blit=True, repeat=True)
        
        # Set plot properties
        ax.set_xlabel('Width (m)')
        ax.set_ylabel('Length (m)')
        ax.grid(False)  # Turn off default grid since we're drawing our own
        ax.axis('equal')
        
        # Set axis limits with some padding
        padding = pipe_spacing
        ax.set_xlim(-padding, room_width + padding)
        ax.set_ylim(-padding, room_length + padding)
        
        # Place legend outside the plot on the right
        ax.legend(bbox_to_anchor=(1.15, 0.5), loc='center left')
        
        # Calculate coverage
        usable_width = room_width - 2 * pipe_spacing
        usable_length = room_length - 2 * pipe_spacing
        coverage_area = usable_width * usable_length
        total_area = room_width * room_length
        coverage_percent = (coverage_area / total_area) * 100
        
        # Print statistics
        print("\nRoom Configuration:")
        print(f"Room dimensions: {room_length}m x {room_width}m")
        print(f"Room area: {total_area:.1f}m²")
        print(f"Pipe spacing: {pipe_spacing}m")
        print(f"Grid lines: {num_vertical_lines} vertical, {num_horizontal_lines} horizontal")
        print(f"Total pipe length required: {total_length:.2f} meters")
        print(f"Room coverage: {coverage_percent:.1f}%")
        if not is_large_room:
            print("\nStarting visualization...")
        
        # Show the plot
        plt.ioff()  # Turn off interactive mode
        plt.show()
        
        return True
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function with error handling and user interaction"""
    print("Radiant Heating Layout Generator")
    print("===============================")
    print("This program will create an animated visualization of a radiant heating pipe layout.")
    print("Please enter the following measurements in meters:\n")
    
    try:
        # Get room dimensions with validation
        room_length = get_valid_input("Enter the room length in meters: ")
        room_width = get_valid_input("Enter the room width in meters: ")
        pipe_spacing = get_valid_input("Enter the spacing between pipes in meters (e.g., 0.2): ")
        
        # Create the layout
        success = radiant_heating_layout(room_length, room_width, pipe_spacing)
        
        if not success:
            print("\nFailed to create layout. Please check the input values and try again.")
            return
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}")
        print("Please try again with different values")

if __name__ == "__main__":
    main()
