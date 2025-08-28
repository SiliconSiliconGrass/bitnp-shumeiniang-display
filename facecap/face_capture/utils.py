import numpy as np

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