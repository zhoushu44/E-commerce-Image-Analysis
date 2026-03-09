@echo off

:: 显示启动信息
echo 启动智能图片分析工具...
echo 正在检查并安装必要的依赖包...

:: 检查并安装依赖包
echo 升级 pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo 升级 pip 失败，请检查网络连接或权限
    pause
    exit /b 1
)

echo 安装依赖包中...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 安装依赖包失败，请检查网络连接或权限
    pause
    exit /b 1
)

echo 安装 streamlit...
python -m pip install streamlit
if %errorlevel% neq 0 (
    echo 安装 streamlit 失败，请检查网络连接或权限
    pause
    exit /b 1
)

:: 启动应用
echo 依赖包安装完成，启动智能图片分析工具...
python run_app.py
if %errorlevel% neq 0 (
    echo 启动应用失败，请检查错误信息
    pause
    exit /b 1
)

pause