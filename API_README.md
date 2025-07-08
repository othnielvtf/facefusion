# FaceFusion API

This API allows you to use FaceFusion's face swapping capabilities programmatically. You can send a source face image and a target image, and the API will return the processed image with the face swapped.

## Setup

### Prerequisites

1. Make sure you have FaceFusion installed and working correctly
2. Ensure FFmpeg is installed and available in your PATH
   ```
   # On macOS with Homebrew
   brew install ffmpeg
   
   # On Ubuntu/Debian
   sudo apt-get install ffmpeg
   ```
3. Install additional requirements for the API:
   ```
   pip install flask flask-cors pillow
   ```

### Running the API

You have two options for running the API:

#### Option 1: Full API (api.py)
```
python api.py
```
The API will be available at `http://localhost:5000`

#### Option 2: Simple API (simple_api.py)
```
python simple_api.py
```
The API will be available at `http://localhost:5005`

### First Run Considerations

On the first run, FaceFusion will download necessary models which may take some time. The API has a 5-minute timeout to accommodate this initial setup.

## API Endpoints

### POST /swap-face

Swaps a face from the source image onto faces in the target image.

**Request Body (JSON):**

```json
{
  "source_face": "base64_encoded_image",
  "target_image": "base64_encoded_image",
  "options": {
    "face_swapper_model": "inswapper_128_fp16",
    "face_selector_mode": "one"
  }
}
```

- `source_face`: Base64 encoded image containing the face you want to use
- `target_image`: Base64 encoded image where you want to replace faces
- `options`: (Optional) Configuration options:
  - `face_swapper_model`: Model to use for face swapping (default: "inswapper_128_fp16")
  - `face_selector_mode`: Face selection mode - "one" (default), "many", or "reference"

**Response (JSON):**

```json
{
  "success": true,
  "result_image": "base64_encoded_result_image",
  "faces_detected": 1
}
```

- `success`: Boolean indicating if the operation was successful
- `result_image`: Base64 encoded result image with faces swapped
- `faces_detected`: Number of faces detected in the target image

**Error Response:**

```json
{
  "success": false,
  "error": "Error message"
}
```

### GET /health

Simple health check endpoint to verify the API is running.

**Response:**

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

## Web Demo

A simple web demo is included to test the API. After starting the API server, open one of these URLs in your browser to use the demo interface:

- Full API: `http://localhost:5000/static/index.html`
- Simple API: `http://localhost:5005`

## Debugging Tools

### Test Face Swap Script

A standalone Python script is provided to test face swapping directly without using the API:

```bash
python test_face_swap.py --source /path/to/source.jpg --target /path/to/target.jpg --output /path/to/output.jpg
```

Options:
- `--source`: Path to source face image (required)
- `--target`: Path to target image (required)
- `--output`: Path to output image (required)
- `--model`: Face swapper model to use (default: inswapper_128)
- `--timeout`: Timeout in seconds (default: 300)

### Debug Shell Script

A shell script is provided to help diagnose issues with FaceFusion:

```bash
./debug_facefusion.sh [--download]
```

The `--download` flag will automatically download sample images for testing.

This script will:
1. Check Python and FFmpeg installations
2. Verify FaceFusion availability
3. Run a test face swap with detailed output
4. Report success or failure with diagnostic information

## Example Usage

### Using curl

```bash
# Convert images to base64
SOURCE_BASE64=$(base64 -i source_face.jpg)
TARGET_BASE64=$(base64 -i target_image.jpg)

# Send API request
curl -X POST http://localhost:5005/swap-face \
  -H "Content-Type: application/json" \
  -d "{
    \"source_face\": \"$SOURCE_BASE64\",
    \"target_image\": \"$TARGET_BASE64\"
  }" \
  -o response.json

# Extract and save the result image
cat response.json | jq -r '.result_image' | base64 -d > result.jpg
```

For convenience, a ready-to-use curl example script is provided:

```bash
# Make the script executable
chmod +x curl_example.sh

# Run the script
./curl_example.sh
```

This script will automatically handle base64 encoding/decoding and save the result to `test_images/output/curl_result.jpg`.

### Using Python

```python
import requests
import base64

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

# Load images
source_base64 = image_to_base64("source_face.jpg")
target_base64 = image_to_base64("target_image.jpg")

# Prepare request
payload = {
    "source_face": source_base64,
    "target_image": target_base64,
    "options": {
        "face_selector_mode": "one"
    }
}

# Make API request
response = requests.post("http://localhost:5000/swap-face", json=payload)
data = response.json()

if data["success"]:
    # Save result image
    result_base64 = data["result_image"]
    result_bytes = base64.b64decode(result_base64)
    
    with open("result.jpg", "wb") as f:
        f.write(result_bytes)
    
    print("Face swap successful! Result saved as result.jpg")
else:
    print(f"Error: {data['error']}")
```

## API Implementations

This project provides two different API implementations:

### 1. Full API (api.py)

- Integrates directly with FaceFusion's Python modules
- More efficient as it doesn't spawn separate processes
- Supports more configuration options
- May have more complex dependency requirements

### 2. Simple API (simple_api.py)

- Uses subprocess to call FaceFusion CLI
- More robust against dependency issues
- Easier to debug and troubleshoot
- Includes improved error handling and timeout management
- Slightly slower due to process overhead

## Troubleshooting

### Common Issues

1. **Port already in use**
   - Kill existing Python processes or change the port in the API script
   - `ps aux | grep python` to find running processes
   - `kill <PID>` to terminate a specific process

2. **FFmpeg not found**
   - Ensure FFmpeg is installed: `brew install ffmpeg` (macOS) or `apt-get install ffmpeg` (Ubuntu/Debian)
   - Verify it's in your PATH: `which ffmpeg`

3. **First run timeout**
   - The first run downloads models which can take time
   - Try running the debug script first: `./debug_facefusion.sh --download`
   - Increase timeout in `simple_api.py` if needed

4. **Face detection issues**
   - Ensure source image has a clear, well-lit face
   - Try different face detection models: add `--face-detector-model retinaface` to the command

5. **Missing dependencies**
   - Install all required packages: `pip install -r requirements.txt`
   - For specific errors, install the missing package: `pip install <package_name>`

## Notes

- The API creates temporary files in the `uploads` directory and automatically cleans them up after processing
- For best results, use clear images with visible faces
- The source image should contain only one face for best results
