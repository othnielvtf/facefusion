#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description='Test FaceFusion face swapping')
    parser.add_argument('--source', required=True, help='Path to source face image')
    parser.add_argument('--target', required=True, help='Path to target image')
    parser.add_argument('--output', required=True, help='Path to output image')
    parser.add_argument('--model', default='inswapper_128', help='Face swapper model to use')
    parser.add_argument('--timeout', type=int, default=300, help='Timeout in seconds')
    
    args = parser.parse_args()
    
    # Validate input files
    if not os.path.exists(args.source):
        print(f"Error: Source file {args.source} does not exist")
        return 1
        
    if not os.path.exists(args.target):
        print(f"Error: Target file {args.target} does not exist")
        return 1
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Build the FaceFusion command
    cmd = [
        'python3', 'facefusion.py',
        'headless-run',
        '--source', args.source,
        '--target', args.target,
        '--output-path', args.output,
        '--face-swapper-model', args.model
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        # Run the command with timeout
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = process.communicate(timeout=args.timeout)
        stdout_str = stdout.decode('utf-8')
        stderr_str = stderr.decode('utf-8')
        
        print(f"Command output:")
        print(f"STDOUT: {stdout_str}")
        print(f"STDERR: {stderr_str}")
        
        if process.returncode != 0:
            print(f"Error: FaceFusion process failed with return code {process.returncode}")
            return process.returncode
        
        if os.path.exists(args.output):
            print(f"Success! Output saved to {args.output}")
            return 0
        else:
            print(f"Error: Output file {args.output} was not created")
            return 1
            
    except subprocess.TimeoutExpired:
        process.kill()
        print(f"Error: FaceFusion process timed out after {args.timeout} seconds")
        return 1
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
