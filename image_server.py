import os

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
import redis
from utils.crypt import refresh_access_token, validate_access_token

load_dotenv()

IMGBB_API_KEY = os.getenv('IMGBB_API_KEY')

app = Flask(__name__)
cache = redis.Redis(
    host=os.getenv("REDIS_HOST", ""),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0
)


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    token = request.form.get('token', "")
    if cache.get(token):
        return jsonify({"error": "you caught to rate limiting, please try again in 10 seconds"}), 403

    is_valid = refresh_access_token(token)
    if not is_valid:
        return jsonify({"error": "please give valid refresh_token"}), 403


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
        cache.setex(token, 10, "used")
        return jsonify({'url': data['data']['url']})
    else:
        return jsonify({'error': 'Upload failed', 'details': response.text}), 500

if __name__ == '__main__':
    app.run(debug=True)
