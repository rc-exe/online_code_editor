from flask import Flask, render_template, request, jsonify
import subprocess
import os
import tempfile
import shutil
import signal
from typing import Tuple, Optional

app = Flask(__name__)

# Configure a directory to save code snippets
CODE_DIR = "saved_codes"
os.makedirs(CODE_DIR, exist_ok=True)

# Windows-specific error handling
if os.name == 'nt':
    import ctypes
    ctypes.windll.kernel32.SetErrorMode(0x0001 | 0x0002)

def execute_code(command: list, input_data: str, timeout: int = 5) -> Tuple[str, bool]:
    """Execute code with proper input handling and timeout."""
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            universal_newlines=True,
            start_new_session=True
        )
        
        stdout, stderr = process.communicate(input=input_data, timeout=timeout)
        return stdout + stderr, False
        
    except subprocess.TimeoutExpired:
        # Clean up the process group
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        return f"Execution timed out after {timeout} seconds", True
    except Exception as e:
        return f"Execution error: {str(e)}", True

def compile_code(compiler: str, source_path: str, output_path: str) -> Tuple[Optional[str], bool]:
    """Compile code and return any errors."""
    try:
        result = subprocess.run(
            [compiler, source_path, '-o', output_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return result.stderr, True
        return None, False
    except subprocess.TimeoutExpired:
        return "Compilation timed out after 10 seconds", True
    except Exception as e:
        return f"Compilation error: {str(e)}", True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_code():
    data = request.json
    code = data.get('code', '').strip()
    language = data.get('language', 'python')
    user_input = data.get('input', '')
    
    if not code:
        return jsonify({'output': 'Error: No code provided'})
    
    try:
        if language == 'python':
            output, is_error = execute_code(['python', '-c', code], user_input)
            
        elif language == 'javascript':
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.js', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            try:
                output, is_error = execute_code(['node', temp_path], user_input)
            finally:
                try:
                    os.unlink(temp_path)
                except:
                    pass
                
        elif language in ['c', 'cpp']:
            with tempfile.TemporaryDirectory() as temp_dir:
                ext = '.c' if language == 'c' else '.cpp'
                src_path = os.path.join(temp_dir, f'script{ext}')
                exe_path = os.path.join(temp_dir, 'script')
                
                with open(src_path, 'w') as f:
                    f.write(code)
                
                # Compile
                compiler = 'gcc' if language == 'c' else 'g++'
                compile_output, compile_error = compile_code(compiler, src_path, exe_path)
                
                if compile_error:
                    output = compile_output
                    is_error = True
                else:
                    # Execute
                    output, is_error = execute_code([exe_path], user_input)
                    
        else:
            output = "Unsupported language"
            is_error = True
            
        return jsonify({
            'output': output,
            'is_error': is_error
        })
        
    except Exception as e:
        return jsonify({
            'output': f"System error: {str(e)}",
            'is_error': True
        })

@app.route('/save', methods=['POST'])
def save_code():
    data = request.json
    filename = data.get('filename', '').strip()
    code = data.get('code', '').strip()
    
    if not filename:
        return jsonify({'error': 'Filename cannot be empty'}), 400
    if not code:
        return jsonify({'error': 'Code cannot be empty'}), 400
    
    # Sanitize filename
    filename = ''.join(c for c in filename if c.isalnum() or c in (' ', '-', '_'))
    if not filename:
        return jsonify({'error': 'Invalid filename'}), 400
    
    filepath = os.path.join(CODE_DIR, f"{filename}.txt")
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(code)
        return jsonify({'message': 'Code saved successfully!'})
    except Exception as e:
        return jsonify({'error': f"Failed to save: {str(e)}"}), 500

@app.route('/load', methods=['GET'])
def load_code():
    filename = request.args.get('filename', '').strip()
    if not filename:
        return jsonify({'error': 'Filename cannot be empty'}), 400
    
    # Sanitize filename
    filename = ''.join(c for c in filename if c.isalnum() or c in (' ', '-', '_'))
    if not filename:
        return jsonify({'error': 'Invalid filename'}), 400
    
    filepath = os.path.join(CODE_DIR, f"{filename}.txt")
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as file:
                code = file.read()
            return jsonify({'code': code})
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': f"Failed to load: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')