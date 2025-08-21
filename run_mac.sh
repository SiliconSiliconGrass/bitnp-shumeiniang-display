#!/bin/bash

# 函数：在新终端窗口执行命令
run_in_new_window() {
  osascript <<EOF
tell application "Terminal"
  do script "cd $(pwd) && $1"
  activate
end tell
EOF
}

# 1. 启动展示前端
run_in_new_window "cd frontend && npm run serve"
echo "✅ 展示前端已启动 (PORT:9233)"

# 2. 启动面捕后端
run_in_new_window "python facecap/backend/backend.py"
echo "✅ 面捕后端已启动 (PORT:9234)"

# 3. 启动面捕摄像头
run_in_new_window "python facecap/face_capture/face_capture.py"
echo "✅ 面捕摄像头已启动"

# 4. 启动面捕前端
run_in_new_window "cd facecap/frontend && npm run serve"
echo "✅ 面捕前端已启动 (PORT:9235)"

# 5. 启动GPT-SoVITS
run_in_new_window "cd /Users/indexerror/Documents/MyStuff/Projects/Playground/GPT-SoVITS && conda activate gptsovits && python api_silicon.py"
echo "✅ GPT-SoVITS已启动 (PORT:9880)"

# 6. 启动语音识别
run_in_new_window "python stt/stt.py"
run_in_new_window "python stt/stt_backend.py"
echo "✅ 语音识别系统已启动 (PORT:9236)"

echo "所有服务已启动完成！"