# 宝塔 Docker 部署完整指南

## 📋 前置条件

1. 宝塔面板已安装 Docker
2. 服务器已安装 Docker
3. 项目文件已准备好

---

## 🚀 部署步骤

### 步骤 1：上传项目文件到服务器

#### 方式一：使用宝塔文件管理（推荐）

1. **登录宝塔面板**
   - 访问：`http://your-server-ip:8888`
   - 输入用户名和密码

2. **进入文件管理**
   - 左侧菜单 -> 文件
   - 进入 `/www/wwwroot/`

3. **创建项目目录**
   - 点击"新建文件夹"
   - 文件夹名称：`image-analysis`

4. **上传项目文件**
   - 进入 `/www/wwwroot/image-analysis/`
   - 点击"上传"
   - 选择以下文件并上传：
     - `image_analyzer_v3.py`
     - `requirements.txt`
     - `image_tool_config.yaml`
     - `.streamlit/config.toml`

5. **创建必要的目录**
   - 在 `/www/wwwroot/image-analysis/` 下创建：
     - `data/` 文件夹
     - `logs/` 文件夹
     - `.streamlit/` 文件夹
     - `icons/` 文件夹（可选）

#### 方式二：使用 FTP/SFTP

1. **使用 FileZilla、WinSCP 等工具**
   - 连接到服务器
   - 上传整个项目文件夹到 `/www/wwwroot/image-analysis/`

#### 方式三：使用 Git（推荐）

1. **在宝塔中克隆仓库**
   - 左侧菜单 -> 软件商店
   - 搜索 "Git"
   - 安装 Git 管理器

2. **克隆项目**
   - 点击"添加项目"
   - 输入 Git 仓库地址
   - 选择克隆目录：`/www/wwwroot/image-analysis`

---

### 步骤 2：在宝塔中使用 Docker

#### 1. 打开 Docker 管理

- 左侧菜单 -> Docker
- 确保已安装 Docker

#### 2. 创建镜像（两种方式）

##### 方式 A：使用宝塔 Docker 构建镜像

1. **点击"镜像"标签**

2. **点击"构建镜像"**

3. **填写构建信息**
   - 镜像名称：`image-analysis`
   - Dockerfile 路径：`/www/wwwroot/image-analysis/Dockerfile`
   - 上下文路径：`/www/wwwroot/image-analysis`

4. **点击"提交"开始构建**

5. **等待构建完成**
   - 构建过程可能需要几分钟
   - 查看构建日志

##### 方式 B：使用命令行构建（推荐）

1. **SSH 登录服务器**
   ```bash
   ssh root@your-server-ip
   ```

2. **进入项目目录**
   ```bash
   cd /www/wwwroot/image-analysis
   ```

3. **构建镜像**
   ```bash
   docker build -t image-analysis:latest .
   ```

4. **查看镜像**
   ```bash
   docker images | grep image-analysis
   ```

---

### 步骤 3：创建并运行容器

#### 方式 A：使用宝塔 Docker 界面（推荐）

1. **点击"容器"标签**

2. **点击"创建容器"**

3. **填写容器信息**

**基本配置**
```
容器名称: image-analysis-app
镜像: image-analysis:latest
```

**端口映射**
```
容器端口: 8501
主机端口: 8501
```

**目录映射**
```
容器目录: /app/data
主机目录: /www/wwwroot/image-analysis/data

容器目录: /app/logs
主机目录: /www/wwwroot/image-analysis/logs

容器目录: /app/image_tool_config.yaml
主机目录: /www/wwwroot/image-analysis/image_tool_config.yaml
读写权限: 只读
```

**环境变量**
```
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
STREAMLIT_SERVER_HEADLESS=true
TZ=Asia/Shanghai
```

**重启策略**
```
选择: 总是重启
```

4. **点击"提交"创建容器**

5. **点击"启动"按钮**

#### 方式 B：使用命令行创建（推荐）

```bash
# SSH 登录服务器
ssh root@your-server-ip

# 进入项目目录
cd /www/wwwroot/image-analysis

# 创建必要的目录
mkdir -p data logs

# 运行容器
docker run -d \
  --name image-analysis-app \
  -p 8501:8501 \
  -v /www/wwwroot/image-analysis/data:/app/data \
  -v /www/wwwroot/image-analysis/logs:/app/logs \
  -v /www/wwwroot/image-analysis/image_tool_config.yaml:/app/image_tool_config.yaml:ro \
  -e STREAMLIT_SERVER_PORT=8501 \
  -e STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
  -e STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
  -e STREAMLIT_SERVER_HEADLESS=true \
  -e TZ=Asia/Shanghai \
  --restart unless-stopped \
  image-analysis:latest
```

---

### 步骤 4：配置 API 密钥

1. **进入宝塔文件管理**
   - 左侧菜单 -> 文件
   - 进入 `/www/wwwroot/image-analysis/`

2. **编辑配置文件**
   - 找到 `image_tool_config.yaml`
   - 点击"编辑"

3. **修改 API 配置**
   ```yaml
   api_key: "your-openai-api-key"
   base_url: "https://api.openai.com/v1"
   model: "gpt-4o"
   suggestion_prompt: 根据数值给出图片优化建议
   multi_image_prompt: 请根据以下多张图片的分析数据，进行对比分析，给出专业的建议和优化方案：
   detail_page_prompt: 请根据以下所有详情页的分析数据，进行综合分析，给出专业的建议和优化方案：
   features: []
   ```

4. **保存文件**

5. **重启容器**
   - 在宝塔 Docker -> 容器中
   - 找到 `image-analysis-app`
   - 点击"重启"

---

### 步骤 5：访问应用

1. **在浏览器中打开**
   ```
   http://your-server-ip:8501
   ```

2. **或者使用域名**（如果已配置）
   ```
   http://your-domain.com:8501
   ```

---

## 🔧 常用操作

### 查看容器状态

**宝塔界面**
- 左侧菜单 -> Docker -> 容器
- 查看容器运行状态

**命令行**
```bash
# 查看运行中的容器
docker ps

# 查看所有容器（包括停止的）
docker ps -a

# 查看容器详细信息
docker inspect image-analysis-app
```

### 查看容器日志

**宝塔界面**
- 左侧菜单 -> Docker -> 容器
- 点击容器名称
- 点击"日志"标签

**命令行**
```bash
# 查看实时日志
docker logs -f image-analysis-app

# 查看最近 100 行日志
docker logs --tail=100 image-analysis-app

# 查看最近 1 小时的日志
docker logs --since=1h image-analysis-app
```

### 重启容器

**宝塔界面**
- 左侧菜单 -> Docker -> 容器
- 找到容器
- 点击"重启"

**命令行**
```bash
docker restart image-analysis-app
```

### 停止容器

**宝塔界面**
- 左侧菜单 -> Docker -> 容器
- 找到容器
- 点击"停止"

**命令行**
```bash
docker stop image-analysis-app
```

### 删除容器

**宝塔界面**
- 左侧菜单 -> Docker -> 容器
- 找到容器
- 点击"删除"

**命令行**
```bash
docker stop image-analysis-app
docker rm image-analysis-app
```

### 更新应用

1. **上传新文件**
   - 通过宝塔文件管理上传更新的文件

2. **重新构建镜像**
   ```bash
   cd /www/wwwroot/image-analysis
   docker build -t image-analysis:latest .
   ```

3. **重启容器**
   ```bash
   docker stop image-analysis-app
   docker rm image-analysis-app
   docker run -d \
     --name image-analysis-app \
     -p 8501:8501 \
     -v /www/wwwroot/image-analysis/data:/app/data \
     -v /www/wwwroot/image-analysis/logs:/app/logs \
     -v /www/wwwroot/image-analysis/image_tool_config.yaml:/app/image_tool_config.yaml:ro \
     -e STREAMLIT_SERVER_PORT=8501 \
     -e STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
     -e STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
     -e STREAMLIT_SERVER_HEADLESS=true \
     -e TZ=Asia/Shanghai \
     --restart unless-stopped \
     image-analysis:latest
   ```

---

## 🔍 故障排查

### 问题 1：容器无法启动

**检查项**
1. 查看容器日志
2. 检查端口是否被占用
3. 检查配置文件是否正确
4. 检查目录权限

**解决方案**
```bash
# 查看详细日志
docker logs image-analysis-app

# 检查端口占用
netstat -tlnp | grep 8501

# 检查目录权限
ls -la /www/wwwroot/image-analysis/
```

### 问题 2：无法访问应用

**检查项**
1. 容器是否在运行
2. 端口映射是否正确
3. 防火墙是否开放端口
4. 安全组是否开放端口

**解决方案**
```bash
# 检查容器状态
docker ps | grep image-analysis-app

# 检查端口监听
netstat -tlnp | grep 8501

# 测试端口连通性
curl http://localhost:8501
```

### 问题 3：API 调用失败

**检查项**
1. API 密钥是否正确
2. API 地址是否可访问
3. 网络连接是否正常
4. 查看容器日志

**解决方案**
1. 检查配置文件
2. 测试 API 连接
3. 查看日志排查

---

## 💡 最佳实践

1. **使用版本标签**
   ```
   image-analysis:v1.0.0
   image-analysis:v1.0.1
   ```

2. **定期备份数据**
   ```bash
   # 备份数据目录
   tar -czf image-analysis-data-backup.tar.gz /www/wwwroot/image-analysis/data
   ```

3. **监控日志**
   ```bash
   # 定期查看日志
   docker logs --tail=100 image-analysis-app
   ```

4. **清理资源**
   ```bash
   # 清理未使用的镜像
   docker image prune -a

   # 清理未使用的容器
   docker container prune
   ```

5. **配置防火墙**
   - 确保防火墙开放 8501 端口
   - 宝塔面板 -> 安全 -> 防火墙

---

## 📚 相关文件说明

### 项目文件
- `image_analyzer_v3.py` - 主程序
- `requirements.txt` - Python 依赖
- `image_tool_config.yaml` - 应用配置
- `.streamlit/config.toml` - Streamlit 配置

### 目录结构
```
/www/wwwroot/image-analysis/
├── image_analyzer_v3.py
├── requirements.txt
├── image_tool_config.yaml
├── .streamlit/
│   └── config.toml
├── data/              # 数据目录
├── logs/              # 日志目录
└── icons/             # 图标目录（可选）
```

---

## 🎯 快速命令参考

```bash
# SSH 登录
ssh root@your-server-ip

# 进入项目目录
cd /www/wwwroot/image-analysis

# 构建镜像
docker build -t image-analysis:latest .

# 运行容器
docker run -d \
  --name image-analysis-app \
  -p 8501:8501 \
  -v /www/wwwroot/image-analysis/data:/app/data \
  -v /www/wwwroot/image-analysis/logs:/app/logs \
  -v /www/wwwroot/image-analysis/image_tool_config.yaml:/app/image_tool_config.yaml:ro \
  -e STREAMLIT_SERVER_PORT=8501 \
  -e STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
  -e STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
  -e STREAMLIT_SERVER_HEADLESS=true \
  -e TZ=Asia/Shanghai \
  --restart unless-stopped \
  image-analysis:latest

# 查看日志
docker logs -f image-analysis-app

# 重启容器
docker restart image-analysis-app

# 停止容器
docker stop image-analysis-app

# 删除容器
docker rm image-analysis-app
```

---

**按照以上步骤，你就可以在宝塔中成功部署应用了！🚀**
