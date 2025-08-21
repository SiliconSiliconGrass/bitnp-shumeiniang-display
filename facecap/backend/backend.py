from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# CORS(app, resources={r"/*": {"origins": "*"}})

global_face_params = None
global_face_image = None

@app.route('/put_face_params', methods=['POST'])
def put_face_params():
    global global_face_params, global_face_image
    data = request.get_json()
    if 'faceParams' not in data:
        return jsonify({"error": "Missing 'faceParams' in request"}), 400
    if not isinstance(data['faceParams'], dict):
        return jsonify({"error": "'faceParams' must be a dictionary"}), 400

    global_face_params = data['faceParams']
    # print("Got face params:", global_face_params) # debug

    if 'faceImage' in data:
        global_face_image = data['faceImage']

    return jsonify({"message": "faceParams stored successfully"}), 200

@app.route('/get_face_params', methods=['GET'])
def get_face_params():
    global global_face_params
    # print("Sending face params:", global_face_params) # debug
    face_params = global_face_params
    if face_params is None:
        face_params = {}

    return jsonify({"faceParams": face_params}), 200


@app.route('/get_face_image', methods=['GET'])
def get_face_image():
    global global_face_image
    # print("Sending face params:", global_face_params) # debug
    face_image = global_face_image
    if face_image is None:
        face_image = ""

    return jsonify({"faceImage": face_image}), 200
    

if __name__ == '__main__':
    port = 9234
    app.run(port = port, debug=True)
