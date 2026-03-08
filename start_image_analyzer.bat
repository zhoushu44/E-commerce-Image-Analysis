@echo off

:: 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Python 未安装或不在环境变量中
    pause
    exit /b 1
)

:: 检查依赖项
pip show streamlit >nul 2>&1
if %errorlevel% neq 0 (
    echo 安装依赖项...
    pip install streamlit openai Pillow pyyaml
)

:: 启动应用
echo 启动智能图片分析工具...
python -m streamlit run image_analyzer_v3.py --server.port=8501 --server.address=localhost

pause
