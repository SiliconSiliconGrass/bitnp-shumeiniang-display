import time as t
import time
import numpy as np
import torch
import sounddevice as sd
import soundfile as sf
import requests

from threading import Lock
from funasr import AutoModel
from silero_vad import load_silero_vad, get_speech_timestamps

STT_BACKEND_PORT = 9236 # stt backend port

# 初始化模型
vad_model = load_silero_vad()
stt_model = AutoModel(
    model="paraformer-zh",
    disable_log=True,
    disable_update=True
)

# 配置参数
SAMPLE_RATE = 16000  # 必须16kHz
CHUNK_DURATION = 1  # VAD处理的音频块时长(秒)
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
FRAME_DURATION = 0.5  # 音频回调的帧时长(秒)
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION)

# 全局变量
vad_buffer = np.zeros(CHUNK_SIZE, dtype=np.float32)
speech_buffer = np.array([], dtype=np.float32)
recording = False
speech_ends = False
enable_dictation = True
buffer_lock = Lock()  # 用于线程安全的锁
test_file_count = 0

def vad_callback(indata, frames, time, status):
    """麦克风音频回调函数"""
    global enable_dictation, vad_model, vad_buffer, recording, speech_buffer, speech_ends, buffer_lock

    if not enable_dictation:
        with buffer_lock:
            vad_buffer = np.zeros(CHUNK_SIZE, dtype=np.float32)
            speech_buffer = np.array([], dtype=np.float32)
            recording = False
        return

    if status.input_overflow:
        print("⚠️ 输入溢出！数据丢失")

    # 获取当前音频帧（单声道）
    audio_frame = indata[:, 0].copy()

    with buffer_lock:
        # 更新VAD缓冲区（滑动窗口）
        vad_buffer = np.roll(vad_buffer, -frames)
        vad_buffer[-frames:] = audio_frame

        # 如果是语音状态，累积到speech_buffer
        if recording:
            speech_buffer = np.concatenate([speech_buffer, audio_frame])

    # VAD检测（使用完整的CHUNK_SIZE窗口）
    vad_buffer_tensor = torch.from_numpy(vad_buffer).to(torch.float32)
    speech_timestamps = get_speech_timestamps(
        vad_buffer_tensor,
        vad_model,
        sampling_rate=SAMPLE_RATE,
        return_seconds=True
    )

    # 状态转移检测
    prev_recording = recording
    recording = len(speech_timestamps) > 0

    if not prev_recording and recording:
        # 语音开始
        with buffer_lock:
            speech_buffer = audio_frame.copy()  # 重置speech_buffer
        print(f"🔊 语音开始 @ {t.strftime('%H:%M:%S', t.localtime(t.time()))}")

    elif prev_recording and not recording:
        # 语音结束
        speech_ends = True
        print(f"🔇 语音结束 @ {t.strftime('%H:%M:%S', t.localtime(t.time()))}")

# 开始实时流式检测
print("开始流式VAD检测 (按Ctrl+C停止)...")
with sd.InputStream(
    samplerate=SAMPLE_RATE,
    blocksize=FRAME_SIZE,
    channels=1,
    dtype='float32',
    callback=vad_callback
):
    try:
        while True:
            # 从后端的/get_message端口获取enableDictation参数
            try:
                response = requests.get(f'http://localhost:{STT_BACKEND_PORT}/get_message')
                response.raise_for_status()  # 检查请求是否成功
                data = response.json()
                enable_dictation = data.get('enableDictation', True)  # 默认值设为True

            except requests.RequestException as e:
                print(f"获取enableDictation参数失败: {e}")
                continue

            # 进行语音识别
            if speech_ends:
                speech_ends = False

                # 拷贝当前语音缓冲区的完整内容
                with buffer_lock:
                    current_speech = speech_buffer.copy()
                    speech_buffer = np.array([], dtype=np.float32)  # 重置缓冲区

                # 保存和识别
                if len(current_speech) > 0:
                    # sf.write(f"test/test_file{test_file_count}.wav", current_speech, SAMPLE_RATE) # debug
                    # test_file_count += 1

                    result = stt_model.generate(
                        input=current_speech,
                        audio_fs=SAMPLE_RATE,
                        batch_size=1
                    )
                    print(f"识别结果: {result[0]['text'] if result else '无结果'}")

                    result = result[0]['text'] if result else ""
                    try:
                        # 将识别结果发送到9236端口的/put_dictation接口
                        response = requests.post(f'http://localhost:{STT_BACKEND_PORT}/put_dictation', json={'dictation': result})
                        response.raise_for_status()  # 检查请求是否成功
                        print(f"发送结果成功，状态码: {response.status_code}")
                    except requests.RequestException as e:
                        print(f"发送结果失败: {e}")

            time.sleep(0.1) # 降低CPU占用
    except KeyboardInterrupt:
        print("停止检测")