from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

globalEnableDictation = True
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

# 设置 enableDictation 等状态变量
@app.route('/message', methods=['POST'])
def handle_message():
    global globalEnableDictation
    data = request.get_json()
    if 'enableDictation' not in data:
        return jsonify({"error": "Missing 'enableDictation' in request"}), 400
    if not isinstance(data['enableDictation'], bool):
        return jsonify({"error": "'enableDictation' must be a bool"}), 400

    globalEnableDictation = data['enableDictation']
    print("Set enableDictation to:", globalEnableDictation)
    
    return jsonify({"message": "'enableDictation' stored successfully"}), 200

# 获取 enableDictation 等状态变量
@app.route('/get_message', methods=['GET'])
def get_message():
    global globalEnableDictation
    print("Sending enableDictation:", globalEnableDictation)
    return jsonify({"enableDictation": globalEnableDictation}), 200

if __name__ == '__main__':
    port = 9236 # stt backend port
    app.run(port = port, debug=True)
