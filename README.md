# bitnp-shumeiniang-display
基于 SiliconVTuber 的树莓娘皮套展示 Demo (临时项目, 只作为 Demo, 可能不会长期维护)

---

## 项目结构
*开发时间有限，项目中的“frontend”和“backend”文件夹命名稍微有点乱，敬请谅解

- `frontend` 展示前端
- `facecap` 面捕
  - `facecap/frontend` 展示面捕得到的模型 (会以一个 `iframe` 的形式在展示前端中集成)
  - `facecap/face_capture` Python 调用摄像头进行面捕计算
  - `facecap/backend` 面捕后端, 用以实现 `facecap/frontend` 与 `facecap/face_capture` 的通信
- `stt` 语音识别 (Speech To Text)

_另外, 本项目还需要使用 GPTSoVITS 进行语音合成, 但并不在此仓库中_

## 运行

### 0. 一键式启动
由于涉及服务较多，我们提供了一键式启动脚本`run_mac.sh` （仅 MacOS 可用）
``` bash
bash run_mac.sh
```
它等同于顺次执行下述的所有命令。

---

### 1. 启动展示前端
``` bash
cd frontend
npm run serve
```

展示前端将运行于 `9233` 端口

---

### 2. 启动面捕后端
``` bash
python facecap/backend/backend.py
```

面捕后端将运行于 `9234` 端口

---

### 3. 启动面捕摄像头
``` bash
python facecap/face_capture/face_capture.py
```

---

### 4. 启动面捕前端
``` bash
cd facecap/frontend
npm run serve
```

面捕前端将运行于 `9235` 端口

---

### 5. 启动 GPT-SoVITS
_使用 `silicon_api.py`_
``` bash
cd /Users/indexerror/Documents/MyStuff/Projects/Playground/GPT-SoVITS
conda activate gptsovits
python api_silicon.py
```
*此处的代码中使用了我电脑上 GPT-SoVITS 的绝对路径, 在其他机器上请自行调整.

GPT-SoVITS 将运行于 `9880` 端口

---

### 6. 启动语音识别
#### 6.1 启动语音识别麦克风
``` bash
python stt/stt.py
```

#### 6.2 启动语音识别后端
``` bash
python stt/stt_backend.py
```

语音识别后端将运行于 `9236` 端口

---

## 端口表
| 端口号 | 用途 | 备注 |
|--------|------|------|
| 9233 | 展示前端 | Vue |
| 9234 | 面捕后端 | Python Flask |
| 9235 | 面捕前端 | Vue |
| 9236 | 语音识别后端 | Python Flask |
| 9880 | GPT-SoVITS | Python uvicorn |

---
作者邮箱: `indexguo@163.com`
出于版权考虑, 仓库没有上传树莓娘的 Live2D 皮套文件, 如有需要, 请通过邮箱联系我.
若有其他任何问题, 请在仓库上提出 issue, 或者直接通过邮箱联系我.