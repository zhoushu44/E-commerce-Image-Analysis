@echo off

rem 切换到脚本所在目录
cd /d %~dp0

rem 运行Streamlit应用
python -m streamlit run image_analyzer_v3.py --server.port=8501 --server.address=127.0.0.1 --browser.gatherUsageStats=false

pause
