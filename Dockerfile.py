# 基础镜像（Python 3.9 精简版）
FROM python:3.9-slim

# 设置容器内工作目录
WORKDIR /app

# 复制依赖文件到容器
COPY requirements.txt .

# 安装依赖（用清华源加速）
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制所有代码到容器
COPY . .

# 暴露端口（和代码一致）
EXPOSE 5000

# 容器启动命令
CMD ["python", "app.py"]