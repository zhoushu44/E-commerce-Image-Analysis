import os
import subprocess
import webbrowser
import time

# 启动 Streamlit 服务
print("启动智能图片分析工具...")

# 启动 Streamlit 进程
process = subprocess.Popen([
    'python', '-m', 'streamlit', 'run', 'image_analyzer_v3.py',
    '--server.port=8501',
    '--server.address=localhost',
    '--browser.gatherUsageStats=false'
])

# 等待服务启动
time.sleep(3)

# 打开浏览器
print("打开浏览器...")
webbrowser.open('http://localhost:8501')

# 保持脚本运行
print("智能图片分析工具已启动！")
print("按 Ctrl+C 停止服务")

try:
    process.wait()
except KeyboardInterrupt:
    process.terminate()
    print("服务已停止")
