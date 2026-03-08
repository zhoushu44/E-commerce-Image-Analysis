import streamlit as st
import os
import base64
import time
from openai import OpenAI
from PIL import Image
import io
import yaml

# 配置文件路径
CONFIG_FILE = "image_tool_config.yaml"

# 加载配置
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {
        "api_key": "",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
        "detail_page_prompt": "请根据以下所有详情页的分析数据，进行综合分析，给出专业的建议和优化方案：\n\n"
    }

# 初始化配置
config = load_config()

# Streamlit 应用
st.set_page_config(
    page_title="智能图片分析工具",
    page_icon="🖼️",
    layout="wide"
)

# 侧边栏配置
with st.sidebar:
    st.header("配置管理")
    
    # API 配置（可折叠）
    with st.expander("API 设置"):
        api_key = st.text_input("API Key", value=config.get("api_key", ""), type="password")
        base_url = st.text_input("Base URL", value=config.get("base_url", "https://api.openai.com/v1"))
        model = st.text_input("Model", value=config.get("model", "gpt-4o"))
    
    # 建议提示词配置（可折叠）
    with st.expander("建议提示词设置"):
        detail_page_prompt = st.text_area("详情页提示", value=config.get("detail_page_prompt", "请根据以下所有详情页的分析数据，进行综合分析，给出专业的建议和优化方案：\n\n"), height=100)

# 模式3: 详情页分析
st.title("模式3: 详情页分析")

# 第一行：图片上传、分析结果、分析建议（各占三分之一）
col1, col2, col3 = st.columns(3)

# 图片上传
with col1:
    st.header("图片上传")
    # 批量上传图片
    uploaded_files = st.file_uploader("上传图片（可多选，文件名包含数字标识符）", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
    
    # 按文件名中的数字标识符排序并分类
    sorted_files = []
    if uploaded_files:
        # 提取文件名中的数字并排序
        def extract_number(filename):
            import re
            numbers = re.findall(r'\d+', filename)
            return int(numbers[0]) if numbers else 0
        
        sorted_files = sorted(uploaded_files, key=lambda x: extract_number(x.name))
        st.write("已上传的图片：")
        for i, file in enumerate(sorted_files):
            st.write(f"- 详情页{i+1}: {file.name}")
    
    # 分析按钮
    if st.button("开始分析"):
        if not api_key:
            st.error("请先配置 API Key！")
        elif not uploaded_files:
            st.error("请上传图片！")
        else:
            # 初始化 OpenAI 客户端
            client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            
            # 分析所有详情页
            all_results = {}
            start_time = time.time()
            
            for i, uploaded_file in enumerate(sorted_files):
                detail_page_key = f"详情页{i+1}"
                # 获取详情页配置
                if "detail_page_configs" not in st.session_state:
                    st.session_state["detail_page_configs"] = {}
                
                if detail_page_key not in st.session_state["detail_page_configs"]:
                    st.session_state["detail_page_configs"][detail_page_key] = {
                        "name": detail_page_key,
                        "prompt": f"请分析这张图片的内容，给出详细的分析结果。"
                    }
                
                detail_page_config = st.session_state["detail_page_configs"][detail_page_key]
                detail_page_name = detail_page_config["name"]
                prompt = detail_page_config["prompt"]
                
                # 读取图片
                image = Image.open(uploaded_file)
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                
                # 执行分析任务
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{img_base64}"
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens=1000
                    )
                    result = response.choices[0].message.content
                    all_results[detail_page_name] = {"result": result, "prompt": prompt}
                except Exception as e:
                    all_results[detail_page_name] = {"result": f"错误：{str(e)}", "prompt": prompt}
            
            total_time = time.time() - start_time
            
            # 保存结果到会话状态
            st.session_state["analysis_results"] = all_results
            st.session_state["total_time"] = total_time
            st.session_state["mode"] = "模式3"
            st.session_state["sorted_files"] = sorted_files
            st.rerun()

# 分析结果
with col2:
    st.header("分析结果")
    if "analysis_results" in st.session_state and st.session_state.get("mode") == "模式3":
        all_results = st.session_state["analysis_results"]
        total_time = st.session_state["total_time"]
        
        st.info(f"总耗时：{total_time:.2f} 秒")
        
        # 滚动区域
        st.markdown('<div class="scrollable">', unsafe_allow_html=True)
        for detail_page_name, data in all_results.items():
            with st.expander(f"{detail_page_name}"):
                # 显示分析结果
                st.write(data["result"])
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.write("请上传图片并点击开始分析")

# 分析建议
with col3:
    st.header("分析建议")
    if "analysis_results" in st.session_state and st.session_state.get("mode") == "模式3":
        all_results = st.session_state["analysis_results"]
        
        # 生成数据汇总
        analysis_data = []
        for detail_page_name, data in all_results.items():
            analysis_data.append({
                "详情页": detail_page_name,
                "分析结果": data["result"]
            })
        
        if analysis_data:
            # 生成建议的提示词
            detail_page_prompt = config.get("detail_page_prompt", "请根据以下所有详情页的分析数据，进行综合分析，给出专业的建议和优化方案：\n\n")
            for item in analysis_data:
                detail_page_prompt += f"- {item['详情页']}: {item['分析结果'][:100]}..."  # 只取前100个字符，避免提示词过长
                detail_page_prompt += "\n"
            
            # 调用大模型生成建议
            try:
                client = OpenAI(
                    api_key=api_key,
                    base_url=base_url
                )
                
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": detail_page_prompt
                        }
                    ],
                    max_tokens=1000
                )
                
                suggestion = response.choices[0].message.content
                # 滚动区域
                st.markdown('<div class="scrollable">', unsafe_allow_html=True)
                st.write(suggestion)
                st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"生成建议时出错：{str(e)}")
    else:
        st.write("分析后将显示建议")

# 第二行：数据汇总（占满整行）
if "analysis_results" in st.session_state and st.session_state.get("mode") == "模式3":
    all_results = st.session_state["analysis_results"]
    sorted_files = st.session_state.get("sorted_files", [])
    
    st.header("数据汇总")
    analysis_data = []
    for i, (detail_page_name, data) in enumerate(all_results.items()):
        file_name = sorted_files[i].name if i < len(sorted_files) else ""
        analysis_data.append({
            "详情页": detail_page_name,
            "文件名": file_name,
            "分析结果": data["result"]
        })
    if analysis_data:
        # 使用 st.dataframe 而不是 st.table，以更好地处理混合类型数据
        st.dataframe(analysis_data, use_container_width=True)

# 详细页面模块
st.header("详细页面")
with st.expander("详细页面配置"):
    # 动态生成详情页子模块，根据上传的图片数量
    sorted_files = st.session_state.get("sorted_files", [])
    num_detail_pages = len(sorted_files) if sorted_files else 10
    
    # 初始化详情页配置
    if "detail_page_configs" not in st.session_state:
        st.session_state["detail_page_configs"] = {}
    
    # 确保每个详情页都有配置
    for i in range(num_detail_pages):
        page_key = f"详情页{i+1}"
        if page_key not in st.session_state["detail_page_configs"]:
            st.session_state["detail_page_configs"][page_key] = {
                "name": page_key,
                "prompt": f"请分析这张图片的内容，给出详细的分析结果。"
            }
    
    # 显示详情页配置
    for i in range(num_detail_pages):
        page_key = f"详情页{i+1}"
        with st.expander(page_key):
            # 每个子模块包含可编辑的功能名称和提示词字段
            st.subheader(f"{page_key} 配置")
            # 编辑详情页名称
            new_name = st.text_input(f"详情页名称", value=st.session_state["detail_page_configs"][page_key]["name"], key=f"detail_page_name_{i}")
            # 编辑提示词
            new_prompt = st.text_area(f"提示词", value=st.session_state["detail_page_configs"][page_key]["prompt"], key=f"detail_page_prompt_{i}")
            # 更新配置
            if new_name != st.session_state["detail_page_configs"][page_key]["name"] or new_prompt != st.session_state["detail_page_configs"][page_key]["prompt"]:
                st.session_state["detail_page_configs"][page_key]["name"] = new_name
                st.session_state["detail_page_configs"][page_key]["prompt"] = new_prompt

# 页脚
st.markdown("---")
st.markdown("智能图片分析工具 - 基于大模型能力的插件化解决方案")
