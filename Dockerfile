# 用预安装 Streamlit 的镜像，无需手动安装
FROM python:3.9-slim

WORKDIR /app

# 仅安装 Streamlit（无其他依赖）
RUN pip install --no-cache-dir streamlit==1.55.0 -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制空的 app.py（仅验证启动）
COPY app.py .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]