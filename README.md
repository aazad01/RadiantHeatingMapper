# Radiant Heating Layout Generator

This Python script generates and visualizes radiant heating pipe layouts for rooms. It creates an efficient serpentine pattern that ensures even heat distribution while minimizing pipe length.

## Features

- Interactive visualization of pipe installation
- Automatic calculation of total pipe length
- Support for any room size
- Animated installation process for rooms under 600m²
- Static layout display for larger rooms
- Coverage statistics and grid information

## Project Structure

```
RadiantHeating/
├── src/
│   └── radiantheat.py      # Core implementation
├── tests/
│   ├── test_radiantheat.py # Unit tests
│   └── test_coordinates.json # Test data
├── requirements.txt        # Dependencies
└── README.md              # Documentation
```

## Installation

1. Clone this repository
2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the script:
```bash
python src/radiantheat.py
```

You will be prompted to enter:
- Room length (in meters)
- Room width (in meters)
- Pipe spacing (in meters, typically 0.2)

### Example Output

For a 10x10 room with 1m spacing:

```
Grid Information:
Vertical lines: 8
Horizontal lines: 8
Grid spacing: 1.0m

Coverage Information:
Room area: 100.00m²
Covered area: 64.00m²
Coverage percentage: 64.0%

Pipe Information:
Total pipe length: 77.00m
Pipe length per m² of room: 0.77m/m²
```

### Visualization

The script provides two types of visualizations:

1. **Animated Installation (Rooms < 600m²)**
   
   ![Animated Installation](https://raw.githubusercontent.com/aazad01/RadiantHeatingMapper/main/docs/images/animation_example.gif)

   Shows the pipe being installed in real-time with:
   - Red → Yellow gradient for supply line
   - Blue gradient for return line
   - Installation point tracker
   - Progress percentage

2. **Static Layout (Rooms ≥ 600m²)**
   
   ![Static Layout](https://raw.githubusercontent.com/aazad01/RadiantHeatingMapper/main/docs/images/static_example.png)

   Shows the complete layout with:
   - Red line for supply
   - Blue line for return
   - Grid overlay
   - Room boundaries

## Testing

Run the unit tests:
```bash
python -m pytest tests/test_radiantheat.py -v
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request 