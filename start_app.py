import sys
import os
import subprocess
import socket
import webbrowser
import time
import traceback

# 确保使用正确的路径
try:
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        base_path = sys._MEIPATH
    else:
        # 开发环境
        base_path = os.path.dirname(os.path.abspath(__file__))
except AttributeError:
    # 处理 sys._MEIPATH 不存在的情况
    base_path = os.path.dirname(os.path.abspath(__file__))

# 设置工作目录
os.chdir(base_path)

# 日志文件路径
log_file = os.path.join(base_path, 'app.log')

# 写入日志
def write_log(message):
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    print(message)

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

# 运行 Streamlit 应用
try:
    write_log("启动智能图片分析工具...")
    write_log(f"Base path: {base_path}")
    write_log(f"Python executable: {sys.executable}")
    write_log(f"Python version: {sys.version}")
    
    # 检查文件是否存在
    script_path = os.path.join(base_path, 'image_analyzer_v3.py')
    write_log(f"Script path: {script_path}")
    write_log(f"Script exists: {os.path.exists(script_path)}")
    
    # 检查其他文件
    config_path = os.path.join(base_path, 'image_tool_config.yaml')
    write_log(f"Config file exists: {os.path.exists(config_path)}")
    
    streamlit_config_path = os.path.join(base_path, '.streamlit', 'config.toml')
    write_log(f"Streamlit config exists: {os.path.exists(streamlit_config_path)}")
    
    if os.path.exists(script_path):
        write_log("Script found, running Streamlit app...")
        
        # 找到可用端口
        port = 8502
        if check_port(port):
            write_log(f"警告: 端口 {port} 已被占用，正在寻找可用端口...")
            new_port = find_available_port(port)
            if new_port:
                port = new_port
                write_log(f"找到可用端口: {port}")
            else:
                write_log("错误: 无法找到可用端口，请检查是否有其他服务占用了大量端口")
                if hasattr(sys, 'stdin'):
                    input("Press Enter to exit...")
                else:
                    time.sleep(5)
                sys.exit(1)
        else:
            write_log(f"端口 {port} 可用")
        
        # 运行 Streamlit 应用
        cmd = [
            sys.executable,
            '-m', 'streamlit', 'run', script_path,
            '--server.port', str(port),
            '--server.address', '127.0.0.1',
            '--browser.gatherUsageStats', 'false',
            '--server.headless', 'true'
        ]
        
        write_log(f"Running command: {' '.join(cmd)}")
        
        # 启动 Streamlit 进程
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # 等待服务启动
        write_log("等待服务启动...")
        time.sleep(3)  # 等待3秒让服务启动
        
        # 检查服务是否启动成功
        if check_port(port):
            write_log(f"服务已在端口 {port} 启动成功")
        else:
            write_log(f"警告: 服务可能未成功启动，正在尝试打开浏览器...")
        
        # 打开浏览器
        write_log("打开浏览器...")
        webbrowser.open(f'http://127.0.0.1:{port}')
        
        # 保持脚本运行
        write_log("智能图片分析工具已启动！")
        write_log("按 Ctrl+C 停止服务")
        
        # 等待进程结束
        stdout, stderr = process.communicate()
        write_log(f"Streamlit stdout: {stdout}")
        write_log(f"Streamlit stderr: {stderr}")
        
    else:
        write_log(f"错误: Script not found at {script_path}")
        if hasattr(sys, 'stdin'):
            input("Press Enter to exit...")
        else:
            time.sleep(5)
            

except Exception as e:
    # 捕获并显示错误
    error_message = f"Error: {str(e)}"
    write_log(error_message)
    write_log(traceback.format_exc())
    # 避免在无控制台模式下使用 input()
    if hasattr(sys, 'stdin'):
        input("Press Enter to exit...")
    else:
        # 在无控制台模式下，等待一段时间后退出
        time.sleep(5)
