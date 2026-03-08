import sys
import os

# 确保使用正确的路径
if getattr(sys, 'frozen', False):
    # 打包后的环境
    base_path = sys._MEIPATH
else:
    # 开发环境
    base_path = os.path.dirname(os.path.abspath(__file__))

# 设置工作目录
os.chdir(base_path)

# 导入必要的模块
try:
    import streamlit
    from streamlit.web.bootstrap import run
    import tempfile
    
    # 运行 Streamlit 应用
    script_path = os.path.join(base_path, 'image_analyzer_v3.py')
    if os.path.exists(script_path):
        # 使用 streamlit 的 bootstrap 模块运行应用
        run(script_path, '', [], {})
    else:
        print(f"Error: Script not found at {script_path}")
except Exception as e:
    # 捕获并显示错误
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...")
