# 基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制所有代码
COPY . .

# 暴露 Streamlit 默认端口
EXPOSE 8501

# 启动命令（根据你的实际启动文件修改）
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]