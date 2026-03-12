# 改用完整的 Python 3.9 镜像（包含基础编译环境）
FROM python:3.9

# 设置工作目录
WORKDIR /app

# 安装系统级依赖（解决 opencv、torch、PyQt 等包的依赖问题）
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 编译依赖
    build-essential \
    gcc \
    g++ \
    make \
    # OpenCV 依赖
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    # PyQt 依赖
    libx11-xcb1 \
    libxcb1 \
    # 其他系统依赖
    libssl-dev \
    libffi-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 优化 pip 安装（阿里云源 + 超时设置 + 忽略缓存）
RUN pip install --upgrade pip \
    && pip install --no-cache-dir \
    --timeout 120 \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    -r requirements.txt

# 复制项目代码
COPY . .

# 暴露 Streamlit 默认端口
EXPOSE 8501

# 启动 Streamlit 应用（适配你的项目）
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]