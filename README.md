# Radiant Heating Layout Generator

This Python script generates and visualizes radiant heating pipe layouts for rooms. It creates an efficient serpentine pattern that ensures even heat distribution while minimizing pipe length.

## Features

- Interactive visualization of pipe installation
- Automatic calculation of total pipe length
- Support for any room size
- Animated installation process for rooms under 600m²
- Static layout display for larger rooms
- Coverage statistics and grid information

## Installation

1. Clone this repository
2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the script:
```bash
python radiantheat.py
```

You will be prompted to enter:
- Room length (in meters)
- Room width (in meters)
- Pipe spacing (in meters, typically 0.2)

The script will then:
1. Generate the optimal pipe layout
2. Display coverage statistics
3. Show an animated visualization of the installation process
4. Calculate the total pipe length required

## Testing

Run the unit tests:
```bash
python -m unittest test_radiantheat.py -v
``` 