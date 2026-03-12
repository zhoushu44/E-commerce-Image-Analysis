# 用最稳定的 Python 3.9 基础镜像
FROM python:3.9-slim

WORKDIR /app

# 仅安装最小化系统依赖（解决 pip 编译基础需求）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制精简后的依赖文件
COPY requirements.txt .

# 优化 pip 安装（关闭缓存+阿里云源+升级pip）
RUN pip install --upgrade pip \
    && pip install --no-cache-dir \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    -r requirements.txt

# 复制项目代码（确保只有 app.py 等核心文件）
COPY . .

# 暴露 Streamlit 端口
EXPOSE 8501

# 启动命令（最简版）
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]