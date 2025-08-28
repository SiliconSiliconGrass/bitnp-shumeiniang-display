"""
通过摄像头获取视频流，识别视频流中的人脸，获取人脸参数，通过POST请求发送到后端
"""
import sys
import cv2
import os
import time
import numpy as np
import mediapipe as mp
import requests
import base64

from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2

sys.path.append(os.path.dirname(__file__))
from utils import *

BACKEND_PORT = 9234 # facecap backend port
TASK_FILE_PATH = os.path.join(os.path.dirname(__file__), 'face_landmarker_v2_with_blendshapes.task')

capture = cv2.VideoCapture(0) # 使用Mac的FaceTime摄像头
# capture = cv2.VideoCapture(1) # 使用iPhone的摄像头(后摄)

SHOW_VIDEO = False # 不需要使用cv2展示摄像头，因为前端会展示的。

p_time = 0    # 上一帧的时间
c_time = 0    # 下一帧的时间

base_options = python.BaseOptions(model_asset_path=TASK_FILE_PATH)
options = vision.FaceLandmarkerOptions(base_options=base_options,
                                       output_face_blendshapes=True,
                                       output_facial_transformation_matrixes=True,
                                       num_faces=1)
detector = vision.FaceLandmarker.create_from_options(options)


def draw_landmarks_on_image(rgb_image, detection_result):
    # from google demo
    face_landmarks_list = detection_result.face_landmarks
    annotated_image = np.copy(rgb_image)

    # Loop through the detected faces to visualize.
    for idx in range(len(face_landmarks_list)):
        face_landmarks = face_landmarks_list[idx]

        # Draw the face landmarks.
        face_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
        face_landmarks_proto.landmark.extend([
            landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in face_landmarks
        ])

        solutions.drawing_utils.draw_landmarks(
                image=annotated_image,
                landmark_list=face_landmarks_proto,
                connections=mp.solutions.face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp.solutions.drawing_styles
                .get_default_face_mesh_tesselation_style())
        solutions.drawing_utils.draw_landmarks(
                image=annotated_image,
                landmark_list=face_landmarks_proto,
                connections=mp.solutions.face_mesh.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp.solutions.drawing_styles
                .get_default_face_mesh_contours_style())
        solutions.drawing_utils.draw_landmarks(
                image=annotated_image,
                landmark_list=face_landmarks_proto,
                connections=mp.solutions.face_mesh.FACEMESH_IRISES,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp.solutions.drawing_styles
                    .get_default_face_mesh_iris_connections_style())

    return annotated_image

prev_dict_params = {}
while (capture.isOpened()):
    retval, img = capture.read()
    try:
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    except:
        continue
    img = mp.Image(image_format=mp.ImageFormat.SRGB, data=imgRGB)
    detection_result = detector.detect(img)

    img = draw_landmarks_on_image(img.numpy_view(), detection_result)

    img = img[:,::-1,:] # 镜像

    # # debug: draw points with index
    # img = img.copy()
    # if len(detection_result.face_landmarks) > 0:
    #     list_index = [61, 291]
    #     # for index, point in enumerate(detection_result.face_landmarks[0]):
    #     for index in list_index:
    #         point = detection_result.face_landmarks[0][index]
    #         x = int((1 - point.x) * img.shape[1])
    #         y = int(point.y * img.shape[0])
    #         img = cv2.circle(img, (x, y), 3, (255,0,0), -1)
    #         img = cv2.putText(img, f"{index}", (x,y), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 1)

    # 转换为 Base64
    _, buffer = cv2.imencode('.png', cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    img_base64 = base64.b64encode(buffer).decode('utf-8')

    dict_params = {}
    if len(detection_result.face_blendshapes) >= 1:
        categories = detection_result.face_blendshapes[0]
        landmarks = detection_result.face_landmarks[0]

        pitch, yaw, roll = get_rotation(landmarks) # 计算头部旋转角度 (粗略近似)
        pos_x, pos_y, face_size = get_face_position_and_size(landmarks)
        mouth_width = get_mouth_width(landmarks)
        face_size /= np.cos(pitch / 180 * np.pi)

        dict_params["rotatePitch"] = pitch
        dict_params["rotateYaw"] = yaw
        dict_params["rotateRoll"] = roll

        dict_params["positionX"] = pos_x
        dict_params["positionY"] = pos_y
        dict_params["faceSize"] = face_size
        dict_params["mouthWidth"] = mouth_width

        for category in categories:
            dict_params[category.category_name] = category.score
        
        prev_dict_params = dict_params
    else:
        dict_params = prev_dict_params

    # 向后端发送POST请求，携带面部参数以及图像
    try:
        response = requests.post(f'http://localhost:{BACKEND_PORT}/put_face_params', json={'faceParams': dict_params, 'faceImage': img_base64})
        response.raise_for_status()    # 检查请求是否成功
    except requests.RequestException as e:
        # print(f"请求发送失败: {e}") # debug
        pass

    c_time = time.time()
    fps = 1 / (c_time - p_time)
    p_time = c_time

    
    if SHOW_VIDEO:
        cv2.imshow("Video", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        key = cv2.waitKey(1)
        if key == 32:
            break

capture.release()

if SHOW_VIDEO:
    cv2.destroyAllWindows()
