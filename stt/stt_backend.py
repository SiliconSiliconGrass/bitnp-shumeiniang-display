from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

global_dictation = None
global_upload_time = -1

@app.route('/put_dictation', methods=['POST'])
def put_dictation():
    global global_dictation, global_upload_time
    data = request.get_json()
    if 'dictation' not in data:
        return jsonify({"error": "Missing 'dictation' in request"}), 400
    if not isinstance(data['dictation'], str):
        return jsonify({"error": "'dictation' must be a str"}), 400

    global_upload_time = time.time()
    global_dictation = data['dictation']
    
    print("Got dictation:", global_dictation)
    
    return jsonify({"message": "dictation stored successfully"}), 200

@app.route('/get_dictation', methods=['GET'])
def get_dictation():
    global global_dictation, global_upload_time
    print("Sending dictation:", global_dictation)
    if global_dictation is None:
        return jsonify({"dictation": {}, "time": global_upload_time}), 200
    return jsonify({"dictation": global_dictation, "time": global_upload_time}), 200

if __name__ == '__main__':
    port = 9236 # stt backend port
    app.run(port = port, debug=True)
