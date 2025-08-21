from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# CORS(app, resources={r"/*": {"origins": "*"}})

global_face_params = None

@app.route('/put', methods=['POST'])
def put_face_params():
    global global_face_params
    data = request.get_json()
    if 'faceParams' not in data:
        return jsonify({"error": "Missing 'faceParams' in request"}), 400
    if not isinstance(data['faceParams'], dict):
        return jsonify({"error": "'faceParams' must be a dictionary"}), 400
    global_face_params = data['faceParams']
    # print("Got face params:", global_face_params) # debug
    return jsonify({"message": "faceParams stored successfully"}), 200

@app.route('/get', methods=['GET'])
def get_face_params():
    global global_face_params
    # print("Sending face params:", global_face_params) # debug
    if global_face_params is None:
        return jsonify({"faceParams": {}}), 200
    return jsonify({"faceParams": global_face_params}), 200

if __name__ == '__main__':
    port = 9234
    app.run(port = port, debug=True)
