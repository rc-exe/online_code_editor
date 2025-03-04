from flask import Flask, render_template, request, jsonify
import subprocess
import os

app = Flask(__name__)

# Configure a directory to save code snippets
CODE_DIR = "saved_codes"
os.makedirs(CODE_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_code():
    data = request.json
    code = data.get('code', '')
    language = data.get('language', 'python')
    
    if language == 'python':
        try:
            result = subprocess.run(['python', '-c', code], capture_output=True, text=True, timeout=5)
            output = result.stdout + result.stderr
        except Exception as e:
            output = str(e)
    
    elif language == 'javascript':
        try:
            result = subprocess.run(['node', '-e', code], capture_output=True, text=True, timeout=5)
            output = result.stdout + result.stderr
        except Exception as e:
            output = str(e)

    
    else:
        output = "Execution not supported for this language."
    
    return jsonify({'output': output})

@app.route('/save', methods=['POST'])
def save_code():
    data = request.json
    filename = data.get('filename', 'untitled')
    code = data.get('code', '')
    
    filepath = os.path.join(CODE_DIR, f"{filename}.txt")
    with open(filepath, 'w') as file:
        file.write(code)
    
    return jsonify({'message': 'Code saved successfully!'})

@app.route('/load', methods=['GET'])
def load_code():
    filename = request.args.get('filename', 'untitled')
    filepath = os.path.join(CODE_DIR, f"{filename}.txt")
    
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            code = file.read()
        return jsonify({'code': code})
    else:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
