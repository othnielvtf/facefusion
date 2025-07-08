#!/bin/bash

# Debug script for FaceFusion
# This script runs FaceFusion directly with verbose output

echo "FaceFusion Debug Script"
echo "======================="
echo

# Check Python version
echo "Python version:"
python3 --version
echo

# Check if FFmpeg is installed
echo "FFmpeg installation:"
which ffmpeg || echo "FFmpeg not found in PATH"
echo

# Check if FaceFusion is available
echo "FaceFusion availability:"
if [ -f "facefusion.py" ]; then
    echo "facefusion.py found"
else
    echo "ERROR: facefusion.py not found in current directory"
    exit 1
fi
echo

# Create test directories if they don't exist
mkdir -p test_images/output

# Set paths
SOURCE_PATH="test_images/source.jpg"
TARGET_PATH="test_images/target.jpg"
OUTPUT_PATH="test_images/output/result.jpg"

# Check if test images exist
if [ ! -f "$SOURCE_PATH" ] || [ ! -f "$TARGET_PATH" ]; then
    echo "Test images not found. Please place source.jpg and target.jpg in the test_images directory."
    echo "You can do this manually or run this script with the --download flag to use sample images."
    
    if [ "$1" == "--download" ]; then
        echo "Downloading sample images..."
        curl -o "$SOURCE_PATH" "https://raw.githubusercontent.com/facefusion/facefusion-assets/main/examples/source.jpg" 2>/dev/null
        curl -o "$TARGET_PATH" "https://raw.githubusercontent.com/facefusion/facefusion-assets/main/examples/target.jpg" 2>/dev/null
        
        if [ -f "$SOURCE_PATH" ] && [ -f "$TARGET_PATH" ]; then
            echo "Sample images downloaded successfully."
        else
            echo "Failed to download sample images."
            exit 1
        fi
    else
        exit 1
    fi
fi

echo "Running FaceFusion with the following parameters:"
echo "Source: $SOURCE_PATH"
echo "Target: $TARGET_PATH"
echo "Output: $OUTPUT_PATH"
echo

# Run FaceFusion with verbose output
echo "Starting FaceFusion process..."
echo "Command: python3 facefusion.py headless-run --source $SOURCE_PATH --target $TARGET_PATH --output-path $OUTPUT_PATH --face-swapper-model inswapper_128"
echo

python3 facefusion.py headless-run --source "$SOURCE_PATH" --target "$TARGET_PATH" --output-path "$OUTPUT_PATH" --face-swapper-model inswapper_128

# Check result
if [ $? -eq 0 ]; then
    echo
    echo "FaceFusion process completed successfully."
    if [ -f "$OUTPUT_PATH" ]; then
        echo "Output file created: $OUTPUT_PATH"
        echo "Face swapping was successful!"
    else
        echo "Output file was not created despite successful return code."
        echo "This might indicate an issue with the face swapping process."
    fi
else
    echo
    echo "FaceFusion process failed with error code: $?"
    echo "Check the output above for error messages."
fi
