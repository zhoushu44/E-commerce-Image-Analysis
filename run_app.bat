@echo off

:: 安装依赖项
echo 安装依赖项...
python -m pip install streamlit openai Pillow pyyaml

:: 启动智能图片分析工具
echo 启动智能图片分析工具...
python -m streamlit run image_analyzer_v3.py --server.port=8501 --server.address=localhost

pause