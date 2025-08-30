import numpy as np
import mediapipe as mp
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2

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

def get_rotation(landmarks):
    """
    粗略近似计算头部旋转角度(欧拉角)
    """
    p1 = landmarks[133] # 左目
    p2 = landmarks[362] # 右目
    p3 = landmarks[4] # 鼻尖
    p4 = landmarks[152] # 下巴尖

    eyes_height = (p1.y + p2.y) / 2

    pitch = (eyes_height - p3.y) / (eyes_height - p4.y)
    pitch = - (pitch - 17/50) * 80

    yaw = (p1.x - p3.x) / (p1.x - p2.x)
    yaw = (yaw - 0.5) * 30

    roll = np.rad2deg(np.arctan2(p4.x - p3.x, p4.y - p3.y))

    # print(f"{pitch=}, {yaw=}, {roll=}") # debug

    return pitch, yaw, roll

def get_face_position_and_size(landmarks):
    p1 = landmarks[10] # top
    p2 = landmarks[152] # bottom
    p3 = landmarks[234] # left
    p4 = landmarks[454] # right
    p5 = landmarks[4] # nose tip

    x = (p3.x + p4.x + p5.x) / 3
    y = (p1.y + p2.y) / 2

    size = np.linalg.norm(np.array([p1.x, p1.y]) - np.array([p2.x, p2.y]))

    return x, y, size

def get_mouth_width(landmarks):
    p1 = landmarks[61] # 左嘴角
    p2 = landmarks[291] # 右嘴角

    abs_mouth_width = np.linalg.norm(np.array([p1.x, p1.y]) - np.array([p2.x, p2.y]))

    p3 = landmarks[234] # left
    p4 = landmarks[454] # right
    face_width = np.linalg.norm(np.array([p3.x, p3.y]) - np.array([p4.x, p4.y]))

    mouth_width = abs_mouth_width / face_width

    # print("get_mouth_width", abs_mouth_width, face_width, mouth_width)

    return mouth_width

def compute_params(detection_result):
    """根据 MediaPipe 的 detection_result 计算面捕参数"""
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
    else:
        dict_params = {}
    
    return dict_params