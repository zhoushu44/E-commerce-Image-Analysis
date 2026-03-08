import sys
import os
import subprocess

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

# 运行 Streamlit 应用
try:
    print(f"Base path: {base_path}")
    script_path = os.path.join(base_path, 'image_analyzer_v3.py')
    print(f"Script path: {script_path}")
    if os.path.exists(script_path):
        print("Script found, running Streamlit app...")
        
        # 尝试找到系统的Python解释器
        python_exe = None
        
        # 检查常见的Python安装路径
        possible_python_paths = [
            'python.exe',
            'python3.exe',
            os.path.join(os.environ.get('PYTHON_HOME', ''), 'python.exe'),
            os.path.join(os.environ.get('PYTHON_HOME', ''), 'python3.exe'),
            os.path.join(os.environ.get('ProgramFiles', ''), 'Python313', 'python.exe'),
            os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'Python313', 'python.exe'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'Python', 'Python313', 'python.exe'),
        ]
        
        for path in possible_python_paths:
            if os.path.exists(path):
                python_exe = path
                break
        
        if python_exe:
            print(f"Found Python interpreter: {python_exe}")
            
            # 运行Streamlit应用
            cmd = f"{python_exe} -m streamlit run {script_path} --server.port=8501 --server.address=127.0.0.1 --browser.gatherUsageStats=false"
            print(f"Running command: {cmd}")
            subprocess.run(cmd, shell=True)
        else:
            print("Error: Python interpreter not found!")
            print("Please install Python and add it to your PATH.")
    else:
        print(f"Error: Script not found at {script_path}")
except Exception as e:
    # 捕获并显示错误
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
    # 避免在无控制台模式下使用 input()
    if hasattr(sys, 'stdin'):
        input("Press Enter to exit...")
    else:
        # 在无控制台模式下，等待一段时间后退出
        import time
        time.sleep(5)
