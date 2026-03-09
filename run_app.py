import os
import subprocess
import webbrowser
import time
import sys
import socket

# 启动 Streamlit 服务
print("启动智能图片分析工具...")

# 检查 Python 环境
print("检查 Python 环境...")
print(f"Python 版本: {sys.version}")

# 检查端口是否被占用
def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

# 找到可用的端口
def find_available_port(start_port):
    port = start_port
    while port < start_port + 100:  # 最多尝试100个端口
        if not check_port(port):
            return port
        port += 1
    return None

# 尝试使用默认端口或找到可用端口
port = 8502
if check_port(port):
    print(f"警告: 端口 {port} 已被占用，正在寻找可用端口...")
    new_port = find_available_port(port)
    if new_port:
        port = new_port
        print(f"找到可用端口: {port}")
    else:
        print("错误: 无法找到可用端口，请检查是否有其他服务占用了大量端口")
        sys.exit(1)
else:
    print(f"端口 {port} 可用")

# 启动 Streamlit 进程
print("正在启动 Streamlit 服务...")
print(f"执行命令: python -m streamlit run image_analyzer_v3.py --server.port={port} --server.address=127.0.0.1 --browser.gatherUsageStats=false --server.headless=true")

# 直接运行命令，不捕获输出，以便用户能看到完整的错误信息
process = subprocess.Popen([
    'python', '-m', 'streamlit', 'run', 'image_analyzer_v3.py',
    f'--server.port={port}',
    '--server.address=127.0.0.1',
    '--browser.gatherUsageStats=false',
    '--server.headless=true'
])

# 等待服务启动
print("等待服务启动...")
start_time = time.time()
max_wait_time = 10  # 最多等待10秒

try:
    # 等待服务启动
    time.sleep(3)  # 等待3秒让服务启动
    
    # 检查服务是否启动成功
    if check_port(port):
        print(f"服务已在端口 {port} 启动成功")
    else:
        print(f"警告: 服务可能未成功启动，正在尝试打开浏览器...")
    
    # 打开浏览器
    print("打开浏览器...")
    webbrowser.open(f'http://127.0.0.1:{port}')
    
    # 保持脚本运行
    print("智能图片分析工具已启动！")
    print("按 Ctrl+C 停止服务")
    
    process.wait()
except KeyboardInterrupt:
    print("\n正在停止服务...")
    process.terminate()
    # 等待进程终止
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    print("服务已停止")
except Exception as e:
    print(f"发生错误: {str(e)}")
    process.terminate()
    print("服务已停止")
