#!/usr/bin/env python3

import os
import uuid
import base64
from io import BytesIO
from typing import Dict, Any, List, Optional
import numpy as np
from PIL import Image
from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2

# Set OMP_NUM_THREADS to 1 to avoid conflicts
os.environ['OMP_NUM_THREADS'] = '1'

# Import FaceFusion modules
from facefusion import state_manager
from facefusion.face_analyser import get_many_faces, get_one_face, get_average_face
from facefusion.face_selector import sort_faces_by_order
from facefusion.common_helper import get_first
from facefusion.processors.modules import face_swapper
from facefusion.vision import read_image, read_static_image, write_image
from facefusion.filesystem import is_image

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Create temp directory for uploads if it doesn't exist
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize FaceFusion state
def initialize_state():
    # Set default values for required state items
    state_manager.init_item('face_swapper_model', 'inswapper_128_fp16')
    state_manager.init_item('face_selector_mode', 'one')
    state_manager.init_item('face_mask_types', ['box'])
    state_manager.init_item('face_mask_blur', 0.3)
    state_manager.init_item('face_mask_padding', 0)
    state_manager.init_item('face_swapper_pixel_boost', '1x')
    state_manager.init_item('face_mask_regions', ['skin'])
    state_manager.init_item('reference_face_distance', 0.6)
    state_manager.init_item('output_image_resolution', '1x')
    
    # Pre-check to ensure models are downloaded
    if not face_swapper.pre_check():
        raise RuntimeError("Face swapper models not available. Please run FaceFusion normally first to download models.")

# Initialize state when the module is loaded
initialize_state()

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

@app.route('/swap-face', methods=['POST'])
def swap_face():
    """
    API endpoint to swap faces
    
    Expects JSON with:
    - source_face: base64 encoded image of the source face
    - target_image: base64 encoded image where faces should be replaced
    - options: (optional) dictionary with processing options
    
    Returns:
    - result_image: base64 encoded result image
    - faces_detected: number of faces detected in target image
    - success: boolean indicating if the operation was successful
    """
    try:
        data = request.json
        
        if not data or 'source_face' not in data or 'target_image' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: source_face and target_image'
            }), 400
        
        # Get options if provided
        options = data.get('options', {})
        
        # Update state with options
        if 'face_swapper_model' in options:
            state_manager.set_item('face_swapper_model', options['face_swapper_model'])
        
        if 'face_selector_mode' in options:
            state_manager.set_item('face_selector_mode', options['face_selector_mode'])
        
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
        
        # Check if files are valid images
        if not is_image(source_path) or not is_image(target_path):
            return jsonify({
                'success': False,
                'error': 'Uploaded files are not valid images'
            }), 400
        
        # Process the face swap
        source_frames = [read_static_image(source_path)]
        source_faces = []
        
        for source_frame in source_frames:
            temp_faces = get_many_faces([source_frame])
            temp_faces = sort_faces_by_order(temp_faces, 'large-small')
            if temp_faces:
                source_faces.append(get_first(temp_faces))
        
        if not source_faces:
            return jsonify({
                'success': False,
                'error': 'No face detected in source image'
            }), 400
        
        source_face = get_average_face(source_faces)
        target_vision_frame = read_static_image(target_path)
        
        # Get number of faces in target image
        target_faces = get_many_faces([target_vision_frame])
        faces_detected = len(target_faces)
        
        if faces_detected == 0:
            return jsonify({
                'success': False,
                'error': 'No faces detected in target image'
            }), 400
        
        # Process the face swap
        output_vision_frame = face_swapper.process_frame({
            'reference_faces': None,
            'source_face': source_face,
            'target_vision_frame': target_vision_frame
        })
        
        # Save the result
        write_image(output_path, output_vision_frame)
        
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
            'result_image': result_base64,
            'faces_detected': faces_detected
        })
    
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
    app.run(host='0.0.0.0', port=5000, debug=True)
