# 智能图片分析工具

一款基于大模型能力的插件化智能图片分析工具，完全使用 Python 开发，无需前端知识即可快速部署和扩展。

## 核心功能

- **多模态图片分析**：上传图片后，通过大模型（如 GPT-4o、Claude）完成各类视觉任务
- **功能多选与并发执行**：支持同时勾选多个分析功能，通过多线程并发调用 API
- **可视化配置管理**：侧边栏直接修改大模型 API Key、Base URL 和 Model
- **零代码扩展**：内置 "功能管理" 界面，无需写代码，通过填写表单即可新增、编辑、删除功能
- **配置持久化**：所有设置和自定义功能自动保存为 image_tool_config.yaml

## 技术架构

- **UI 层**：Streamlit，纯 Python 编写，自动生成 Web 界面
- **逻辑层**：OpenAI SDK 封装大模型调用，concurrent.futures.ThreadPoolExecutor 实现并发
- **数据层**：YAML 文件存储配置，无需数据库

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行应用

```bash
streamlit run image_analyzer.py
```

### 3. 配置 API

在侧边栏填写：
- API Key：您的大模型 API 密钥
- Base URL：API 基础地址（默认：https://api.openai.com/v1）
- Model：模型名称（默认：gpt-4o）

### 4. 使用方法

1. 上传图片（支持 jpg、jpeg、png、webp 格式）
2. 选择需要的分析功能
3. 点击 "开始分析" 按钮
4. 查看分析结果和耗时

## Docker 部署

### 使用 Docker 运行（推荐）

```bash
# 从 Docker Hub 拉取镜像
docker pull zhoushu1/ecommerce-image-analysis:latest

# 运行容器
docker run -d -p 8501:8501 \
  -v /path/to/data:/app/data \
  -v /path/to/logs:/app/logs \
  --name image-analysis-app \
  zhoushu1/ecommerce-image-analysis:latest
```

### 本地构建镜像

```bash
# 克隆项目
git clone https://github.com/your-repo/e-commerce-image-analysis.git
cd e-commerce-image-analysis

# 构建 Docker 镜像
docker build -t ecommerce-image-analysis:latest .

# 运行容器
docker run -d -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --name image-analysis-app \
  ecommerce-image-analysis:latest
```

### 使用 Docker Compose（最简单）

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down
```

访问应用：http://localhost:8501

## 内置功能

- **计算比例**：分析图片的宽高比例和具体像素值
- **对比度分析**：评价图片的明暗对比情况
- **内容描述**：详细描述图片内容，包括场景、主体、色彩、构图等
- **提取主色调**：提取图片的主要颜色，以十六进制 RGB 值表示

## 自定义功能

在侧边栏的 "功能管理" 部分：
1. 点击 "新增功能" 展开表单
2. 填写功能名称和提示词
3. 点击 "添加功能" 按钮
4. 新功能将出现在功能选择列表中

## 典型使用场景

- **电商运营**：批量分析商品主图的比例、色彩、对比度，优化点击率
- **设计师辅助**：快速提取素材图的配色方案、尺寸信息
- **内容审核**：通过自定义提示词，批量检测图片是否包含特定元素

## 注意事项

- 确保您的 API Key 有足够的配额和权限
- 图片大小不宜过大，建议控制在 10MB 以内
- 分析速度取决于网络状况和模型响应速度
- 所有配置将自动保存到 image_tool_config.yaml 文件

## 技术亮点

- **零代码扩展**：新增功能只需写提示词，无需修改 Python 代码
- **并发执行**：总耗时仅等于最慢的一个任务，而非叠加
- **所见即所得**：先占坑式 UI 设计，任务完成后动态刷新结果
- **轻量灵活**：单文件即可运行，兼容所有符合 OpenAI 格式的大模型 API