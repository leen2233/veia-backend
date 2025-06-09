import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

IMGBB_API_KEY = os.getenv('IMGBB_API_KEY')

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # convert file to base64
    import base64
    encoded_file = base64.b64encode(file.read()).decode('utf-8')

    # upload to imgbb
    response = requests.post(
        'https://api.imgbb.com/1/upload',
        data={
            'key': IMGBB_API_KEY,
            'image': encoded_file
        }
    )

    if response.status_code == 200:
        data = response.json()
        return jsonify({'url': data['data']['url']})
    else:
        return jsonify({'error': 'Upload failed', 'details': response.text}), 500

if __name__ == '__main__':
    app.run(debug=True)
