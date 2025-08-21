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
