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
import json

from tqdm import tqdm
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2

sys.path.append(os.path.dirname(__file__))
from utils import *


def make_exp(video_path, output_path, show_video = False):
    TASK_FILE_PATH = os.path.join(os.path.dirname(__file__), 'face_landmarker_v2_with_blendshapes.task')

    VIDEO_FILE_PATH = video_path
    OUTPUT_FILE_PATH = output_path

    capture = cv2.VideoCapture(VIDEO_FILE_PATH)

    SHOW_VIDEO = show_video

    base_options = python.BaseOptions(model_asset_path=TASK_FILE_PATH)
    options = vision.FaceLandmarkerOptions(base_options=base_options,
                                        output_face_blendshapes=True,
                                        output_facial_transformation_matrixes=True,
                                        num_faces=1)
    detector = vision.FaceLandmarker.create_from_options(options)

    prev_dict_params = {}

    motion_data = []

    fps = capture.get(cv2.CAP_PROP_FPS)
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    for _ in tqdm(range(total_frames), desc="processing", unit="frame", leave=False):
        retval, img = capture.read()
        try:
            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except:
            continue

        k = 0.5
        new_width = int(imgRGB.shape[1] * k)
        new_height = int(imgRGB.shape[0] * k)
        imgRGB = cv2.resize(imgRGB, (new_width, new_height), interpolation=cv2.INTER_AREA)
        # print(imgRGB.shape)

        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=imgRGB)
        detection_result = detector.detect(img)

        img = draw_landmarks_on_image(img.numpy_view(), detection_result)

        img = img[:,::-1,:] # 镜像

        dict_params = compute_params(detection_result)
        motion_data.append(dict_params)
        
        with open(OUTPUT_FILE_PATH, 'w') as f:
            # json.dump({'fps': fps, 'data': motion_data}, f, indent=4)
            data = json.dumps({'fps': fps, 'data': motion_data}, indent=4)
            data = "export default " + data
            f.write(data)
            

        if SHOW_VIDEO:
            cv2.imshow("Video", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            key = cv2.waitKey(1)
            if key == 32:
                break

    capture.release()

    if SHOW_VIDEO:
        cv2.destroyAllWindows()

if __name__ == "__main__":
    names = [
        "nod", "shake_head", "wink"
    ]

    for name in tqdm(names, desc="making expressions", unit="task"):
        video_path = f"{name}.mp4"
        output_path = f"{name}.faceexp.js"
        make_exp(video_path, output_path, show_video=False)