#!/usr/bin/env python3

import os
import uuid
import base64
import subprocess
import tempfile
from io import BytesIO
from typing import Dict, Any, Optional
from PIL import Image
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

# Create temp directory for uploads if it doesn't exist
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def save_base64_image(base64_data: str, file_path: str) -> bool:
    """Save a base64 encoded image to a file"""
    try:
        # Remove data URL prefix if present
        if ',' in base64_data:
            base64_data = base64_data.split(',', 1)[1]
        
        # Decode base64 data
        image_data = base64.b64decode(base64_data)
        
        # Save to file
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        return True
    except Exception as e:
        print(f"Error saving base64 image: {e}")
        return False

def image_to_base64(image_path: str) -> str:
    """Convert an image file to base64 encoding"""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:image/jpeg;base64,{encoded_string}"

@app.route('/')
def index():
    return send_file('static/index.html')

@app.route('/swap-face', methods=['POST'])
def swap_face():
    """
    API endpoint to swap faces using FaceFusion CLI
    
    Expects JSON with:
    - source_face: base64 encoded image of the source face
    - target_image: base64 encoded image where faces should be replaced
    
    Returns:
    - result_image: base64 encoded result image
    - success: boolean indicating if the operation was successful
    """
    try:
        data = request.json
        
        if not data or 'source_face' not in data or 'target_image' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: source_face and target_image'
            }), 400
        
        # Generate unique filenames
        source_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        result_id = str(uuid.uuid4())
        
        source_path = os.path.join(UPLOAD_FOLDER, f"{source_id}.jpg")
        target_path = os.path.join(UPLOAD_FOLDER, f"{target_id}.jpg")
        output_path = os.path.join(UPLOAD_FOLDER, f"{result_id}.jpg")
        
        # Save uploaded images
        if not save_base64_image(data['source_face'], source_path):
            return jsonify({
                'success': False,
                'error': 'Invalid source face image data'
            }), 400
        
        if not save_base64_image(data['target_image'], target_path):
            return jsonify({
                'success': False,
                'error': 'Invalid target image data'
            }), 400
        
        # Check if files exist
        if not os.path.exists(source_path) or not os.path.exists(target_path):
            return jsonify({
                'success': False,
                'error': 'Failed to save uploaded images'
            }), 400
        
        # Run FaceFusion CLI command
        try:
            # FaceFusion CLI requires a specific command structure
            cmd = [
                'python3', 'facefusion.py',
                'headless-run',
                '--source', source_path,
                '--target', target_path,
                '--output-path', output_path,
                '--face-swapper-model', 'inswapper_128'
            ]
            
            print(f"Running command: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Increase timeout to 5 minutes for the first run which needs to download models
            try:
                stdout, stderr = process.communicate(timeout=300)  # 5 minute timeout
                stdout_str = stdout.decode('utf-8')
                stderr_str = stderr.decode('utf-8')
                
                print(f"Command output:\nSTDOUT: {stdout_str}\nSTDERR: {stderr_str}")
            except subprocess.TimeoutExpired:
                # Kill the process if it times out
                process.kill()
                stdout, stderr = process.communicate()
                stdout_str = stdout.decode('utf-8') if stdout else ''
                stderr_str = stderr.decode('utf-8') if stderr else ''
                
                print(f"Process timed out after 300 seconds.\nPartial output:\nSTDOUT: {stdout_str}\nSTDERR: {stderr_str}")
                
                return jsonify({
                    'success': False,
                    'error': 'FaceFusion process timed out after 300 seconds. This might happen during the first run when models need to be downloaded.'
                }), 504  # Gateway Timeout
            
            if process.returncode != 0:
                return jsonify({
                    'success': False,
                    'error': f'FaceFusion process failed: {stderr_str}',
                    'stdout': stdout_str,
                    'stderr': stderr_str,
                    'returncode': process.returncode
                }), 500
            
            # Check if output file exists
            if not os.path.exists(output_path):
                return jsonify({
                    'success': False,
                    'error': 'FaceFusion did not generate an output file'
                }), 500
            
            # Convert result to base64
            result_base64 = image_to_base64(output_path)
            
            # Clean up temporary files
            try:
                os.remove(source_path)
                os.remove(target_path)
                os.remove(output_path)
            except Exception as e:
                print(f"Error removing temporary files: {e}")
            
            return jsonify({
                'success': True,
                'result_image': result_base64
            })
            
        except subprocess.TimeoutExpired:
            return jsonify({
                'success': False,
                'error': 'FaceFusion process timed out'
            }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error running FaceFusion: {str(e)}'
            }), 500
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'ok',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
