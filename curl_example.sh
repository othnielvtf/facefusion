#!/bin/bash

# FaceFusion API curl example
# This script demonstrates how to use curl to interact with the FaceFusion API

# Configuration
API_URL="http://localhost:5005/swap-face"
SOURCE_IMAGE="./test_images/source.jpg"
TARGET_IMAGE="./test_images/target.jpg"
OUTPUT_IMAGE="./test_images/output/curl_result.jpg"

# Check if source and target images exist
if [ ! -f "$SOURCE_IMAGE" ] || [ ! -f "$TARGET_IMAGE" ]; then
    echo "Error: Source or target image not found."
    echo "Please place images at $SOURCE_IMAGE and $TARGET_IMAGE"
    echo "Or modify this script to point to your image files."
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$(dirname "$OUTPUT_IMAGE")"

# Convert images to base64
echo "Converting images to base64..."
SOURCE_BASE64=$(base64 "$SOURCE_IMAGE" | tr -d '\n')
TARGET_BASE64=$(base64 "$TARGET_IMAGE" | tr -d '\n')

# Create JSON payload
echo "Creating API request..."
JSON_PAYLOAD="{
    \"source_face\": \"$SOURCE_BASE64\",
    \"target_image\": \"$TARGET_BASE64\"
}"

# Send API request
echo "Sending request to $API_URL..."
echo "This may take a while, especially on first run..."

curl -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d "$JSON_PAYLOAD" \
    -o "response.json"

# Check if request was successful
if [ $? -ne 0 ]; then
    echo "Error: API request failed."
    exit 1
fi

# Check if response contains success field
SUCCESS=$(cat response.json | grep -o '"success": *true' || echo "")
if [ -z "$SUCCESS" ]; then
    echo "Error: Face swap failed."
    echo "Response:"
    cat response.json
    exit 1
fi

# Extract and save the result image
echo "Extracting result image..."
cat response.json | grep -o '"result_image": *"[^"]*"' | sed 's/"result_image": *"\(.*\)"/\1/' | base64 --decode > "$OUTPUT_IMAGE"

# Check if output image was created
if [ -f "$OUTPUT_IMAGE" ]; then
    echo "Success! Result saved to $OUTPUT_IMAGE"
    
    # Try to display the image if on macOS
    if [ "$(uname)" == "Darwin" ]; then
        echo "Opening result image..."
        open "$OUTPUT_IMAGE"
    fi
else
    echo "Error: Failed to save output image."
    exit 1
fi

# Clean up
rm response.json

echo "Done!"
