import os
import re
import signal
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple, Optional
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Configuration
CODE_DIR = Path("saved_codes")
CODE_DIR.mkdir(exist_ok=True)
MAX_EXECUTION_TIME = 15  # seconds
MAX_COMPILATION_TIME = 20  # seconds
MAX_OUTPUT_LENGTH = 10000  # characters
ALLOWED_EXTENSIONS = {'.py', '.js', '.c', '.cpp'}

# Security configuration
MAX_FILE_SIZE = 1024 * 1024  # 1MB
SANITIZE_PATTERN = re.compile(r'^[a-zA-Z0-9_\- ]+$')

# Windows-specific setup for subprocess error mode
if os.name == 'nt':
    import ctypes
    ctypes.windll.kernel32.SetErrorMode(0x0001 | 0x0002)


class CodeExecutor:
    @staticmethod
    def execute(command: list, input_data: Optional[str] = None, timeout: int = MAX_EXECUTION_TIME) -> Tuple[str, bool]:
        """
        Safely execute a command with timeout and optional input_data sent to stdin.
        Returns (output, is_error).
        """
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                universal_newlines=True,
                start_new_session=True,
                bufsize=1
            )
            try:
                stdout, stderr = process.communicate(input=input_data, timeout=timeout)
                output = (stdout + stderr)[:MAX_OUTPUT_LENGTH]
                return output, False
            except subprocess.TimeoutExpired:
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.kill()
                return f"Execution timed out after {timeout} seconds", True
        except Exception as e:
            return f"Execution error: {str(e)}", True

    @staticmethod
    def compile(compiler: str, source_path: str, output_path: str) -> Tuple[Optional[str], bool]:
        """
        Compile source code with safety checks.
        Returns (compile_error_message or None, is_error)
        """
        try:
            result = subprocess.run(
                [compiler, source_path, '-o', output_path],
                capture_output=True,
                text=True,
                timeout=MAX_COMPILATION_TIME
            )
            if result.returncode != 0:
                return result.stderr[:MAX_OUTPUT_LENGTH], True
            return None, False
        except subprocess.TimeoutExpired:
            return f"Compilation timed out after {MAX_COMPILATION_TIME} seconds", True
        except Exception as e:
            return f"Compilation error: {str(e)}", True


def validate_filename(filename: str) -> bool:
    """Check if filename is safe and valid."""
    return bool(SANITIZE_PATTERN.match(filename))


def create_temp_file(code: str, extension: str) -> str:
    """Create a temporary file with the given code and return its path."""
    with tempfile.NamedTemporaryFile(
        mode='w+',
        suffix=extension,
        delete=False,
        encoding='utf-8'
    ) as f:
        f.write(code)
        return f.name


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/run', methods=['POST'])
def run_code():
    data = request.json
    code = data.get('code', '').strip()
    language = data.get('language', 'python').lower()
    user_input = data.get('input', '')  # Accept user input string here

    if not code:
        return jsonify({'output': 'Error: No code provided', 'is_error': True})

    if len(code) > MAX_FILE_SIZE:
        return jsonify({
            'output': f'Error: Code exceeds maximum size of {MAX_FILE_SIZE} bytes',
            'is_error': True
        })

    try:
        if language == 'python':
            # Use system default python executable (fix for Windows)
            python_exec = os.environ.get('PYTHON_EXECUTABLE', 'python')
            output, is_error = CodeExecutor.execute([python_exec, '-c', code], input_data=user_input)

        elif language == 'javascript':
            temp_path = create_temp_file(code, '.js')
            try:
                output, is_error = CodeExecutor.execute(['node', temp_path], input_data=user_input)
            finally:
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass

        elif language in ['c', 'cpp']:
            with tempfile.TemporaryDirectory() as temp_dir:
                ext = '.c' if language == 'c' else '.cpp'
                src_path = os.path.join(temp_dir, f'script{ext}')
                exe_path = os.path.join(temp_dir, 'script')

                with open(src_path, 'w', encoding='utf-8') as f:
                    f.write(code)

                compiler = 'gcc' if language == 'c' else 'g++'
                compile_output, compile_error = CodeExecutor.compile(compiler, src_path, exe_path)

                if compile_error:
                    output, is_error = compile_output, True
                else:
                    output, is_error = CodeExecutor.execute([exe_path], input_data=user_input)

        else:
            output, is_error = "Unsupported language", True

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
    if not validate_filename(filename):
        return jsonify({'error': 'Invalid filename'}), 400

    filepath = CODE_DIR / f"{filename}.txt"
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
    if not validate_filename(filename):
        return jsonify({'error': 'Invalid filename'}), 400

    filepath = CODE_DIR / f"{filename}.txt"
    try:
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as file:
                code = file.read()
            return jsonify({'code': code})
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': f"Failed to load: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
