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

while (capture.isOpened()):
    retval, img = capture.read()
    try:
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    except:
        continue
    img = mp.Image(image_format=mp.ImageFormat.SRGB, data=imgRGB)
    detection_result = detector.detect(img)

    img = draw_landmarks_on_image(img.numpy_view(), detection_result)

    

    if len(detection_result.face_blendshapes) >= 1:
        categories = detection_result.face_blendshapes[0]
        landmarks = detection_result.face_landmarks[0]

        pitch, yaw, roll = get_rotation(landmarks) # 计算头部旋转角度 (粗略近似)

        dict_params = {}

        dict_params["rotatePitch"] = pitch
        dict_params["rotateYaw"] = yaw
        dict_params["rotateRoll"] = roll

        for category in categories:
            dict_params[category.category_name] = category.score

        # 向后端发送POST请求，携带面部参数
        try:
            response = requests.post(f'http://localhost:{BACKEND_PORT}/put', json={'faceParams': dict_params})
            response.raise_for_status()    # 检查请求是否成功
        except requests.RequestException as e:
            print(f"请求发送失败: {e}")
            pass

    c_time = time.time()
    fps = 1 / (c_time - p_time)
    p_time = c_time

    img = img[:,::-1,:] # 镜像

    cv2.imshow("Video", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    key = cv2.waitKey(1)
    if key == 32:
        break

capture.release()
cv2.destroyAllWindows()
