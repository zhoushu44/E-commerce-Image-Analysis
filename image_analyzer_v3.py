import streamlit as st
import yaml
import os
import base64
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from PIL import Image
import io
import json

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
        "suggestion_prompt": "请根据以下图片分析数据，给出专业的分析建议和优化方案：\n\n",
        "multi_image_prompt": "请根据以下多张图片的分析数据，进行对比分析，给出专业的建议和优化方案：\n\n",
        "detail_page_prompt": "请根据以下所有详情页的分析数据，进行综合分析，给出专业的建议和优化方案：\n\n",
        "features": [
            {
                "name": "计算比例",
                "prompt": "请分析这张图片的宽高比例，以最简分数形式表示（例如：4:3），并计算具体的宽高像素值。",
                "is_numeric": False,
                "condition": "",
                "threshold": "",
                "condition2": "",
                "threshold2": ""
            },
            {
                "name": "对比度分析",
                "prompt": "请分析这张图片的对比度情况，评价其明暗对比是否适中，并给出专业的分析结果。",
                "is_numeric": False,
                "condition": "",
                "threshold": "",
                "condition2": "",
                "threshold2": ""
            },
            {
                "name": "内容描述",
                "prompt": "请详细描述这张图片的内容，包括场景、主体、色彩、构图等方面。",
                "is_numeric": False,
                "condition": "",
                "threshold": "",
                "condition2": "",
                "threshold2": ""
            },
            {
                "name": "提取主色调",
                "prompt": "请提取这张图片的主要颜色，以十六进制RGB值表示，并描述每种颜色的占比和视觉效果。",
                "is_numeric": False,
                "condition": "",
                "threshold": "",
                "condition2": "",
                "threshold2": ""
            }
        ]
    }

# 保存配置
def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

# 初始化配置
config = load_config()

# Streamlit 应用
st.set_page_config(
    page_title="智能图片分析工具",
    page_icon="🖼️",
    layout="wide"
)

# 添加模式选择
mode = st.sidebar.selectbox("选择模式", ["模式1: 单图分析", "模式2: 多图对比分析", "模式3: 详情页分析"])

# 添加专业生产级别界面美化 - 紧凑布局
st.markdown("""
<style>
/* 全局样式 */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f5f7fa;
    color: #333;
    line-height: 1.4;
    margin: 0 !important;
    padding: 0 !important;
}

/* 标题样式 */
h1 {
    color: #2c3e50 !important;
    font-weight: 600 !important;
    margin-bottom: 0.8rem !important;
    margin-top: 0.2rem !important;
    font-size: 24px !important;
    padding-top: 0 !important;
}
h2 {
    color: #34495e !important;
    font-size: 18px !important;
    font-weight: 500 !important;
    margin-bottom: 0.4rem !important;
    margin-top: 0.6rem !important;
    padding-bottom: 0.3rem !important;
    border-bottom: none !important;
}

/* 正文和列表样式 */
p, li {
    font-size: 14px !important;
}

/* 卡片样式 */
.stCard {
    background-color: white;
    border-radius: 6px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    padding: 0.8rem;
    margin-bottom: 0.8rem;
}

/* 按钮样式 */
.stButton > button {
    background-color: #3498db !important;
    color: white !important;
    border: none !important;
    border-radius: 4px !important;
    padding: 4px 12px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
    margin: 2px 0 !important;
}

.stButton > button:hover {
    background-color: #2980b9 !important;
    box-shadow: 0 2px 6px rgba(52, 152, 219, 0.3) !important;
    transform: translateY(-1px) !important;
}

/* 输入框和选择框样式 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > select {
    font-size: 14px !important;
    border: 1px solid #ddd !important;
    border-radius: 4px !important;
    padding: 6px 10px !important;
    transition: border-color 0.3s ease !important;
    margin: 2px 0 !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > select:focus {
    border-color: #3498db !important;
    box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2) !important;
}

/* 展开器样式 */
.stExpander {
    margin-bottom: 0.6rem !important;
    border-radius: 6px !important;
    overflow: hidden !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
}

.stExpander > div {
    padding: 0.8rem !important;
    background-color: white !important;
}

/* 表格样式 */
table {
    font-size: 14px !important;
    border-collapse: separate !important;
    border-spacing: 0 !important;
    width: 100% !important;
    margin: 0.6rem 0 !important;
}

th {
    background-color: #f8f9fa !important;
    font-weight: 600 !important;
    padding: 6px 8px !important;
    text-align: left !important;
    border-bottom: 2px solid #3498db !important;
    font-size: 14px !important;
}

td {
    padding: 4px 8px !important;
    border-bottom: 1px solid #e9ecef !important;
    font-size: 14px !important;
}

tr:hover {
    background-color: #f8f9fa !important;
}

/* 信息和错误提示样式 */
.stAlert {
    border-radius: 4px !important;
    padding: 8px !important;
    margin: 0.6rem 0 !important;
    font-size: 14px !important;
}

/* 布局调整 */
.stColumn {
    padding: 0.8rem !important;
}

/* 图片样式 */
.stImage > img {
    border-radius: 6px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.1) !important;
    margin: 0.4rem 0 !important;
}

/* 复选框样式 */
.stCheckbox > label {
    font-size: 14px !important;
    cursor: pointer !important;
    margin: 2px 0 !important;
}

/* 侧边栏样式 */
.sidebar .sidebar-content {
    padding: 0.8rem !important;
}

/* 减小容器间距 */
.streamlit-container {
    padding-top: 0.8rem !important;
    padding-bottom: 0.8rem !important;
}

/* 减小元素间距 */
div[data-testid="stVerticalBlock"] > div {
    margin-bottom: 0.4rem !important;
}

/* 加载动画 */
@keyframes pulse {
    0% {
        opacity: 0.6;
    }
    50% {
        opacity: 1;
    }
    100% {
        opacity: 0.6;
    }
}

.loading {
    animation: pulse 1.5s infinite;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .stColumns {
        flex-direction: column !important;
    }
    
    .stColumn {
        width: 100% !important;
        margin-bottom: 0.8rem !important;
    }
    
    h1 {
        font-size: 20px !important;
    }
    
    h2 {
        font-size: 14px !important;
    }
}

/* 进一步减小间距 */
.stMarkdown {
    margin-bottom: 0.4rem !important;
}

.stFileUploader {
    margin: 0.4rem 0 !important;
}

.stCheckbox {
    margin: 2px 0 !important;
}

/* 紧凑的两列布局 */
.stColumns {
    gap: 0.8rem !important;
}

/* 减小侧边栏元素间距 */
.sidebar-content > * {
    margin-bottom: 0.4rem !important;
}

/* 减小展开器间距 */
.stExpander {
    margin-top: 0.2rem !important;
    margin-bottom: 0.4rem !important;
}

/* 减小功能管理部分的间距 */
div[data-testid="stExpander"] {
    margin-bottom: 0.4rem !important;
}

/* 减小现有功能之间的间距 */
div[data-testid="stExpander"] > div {
    margin-bottom: 0.2rem !important;
}

/* 减小所有容器的内边距 */
.streamlit-container {
    padding-top: 0.2rem !important;
    padding-bottom: 0.2rem !important;
    padding-left: 0.4rem !important;
    padding-right: 0.4rem !important;
}

/* 减小侧边栏的内边距 */
.sidebar-content {
    padding: 0.4rem !important;
}

/* 减小主内容区的内边距 */
.main-content {
    padding: 0.4rem !important;
}

/* 减小垂直块的间距 */
div[data-testid="stVerticalBlock"] {
    gap: 0.2rem !important;
}

/* 减小水平块的间距 */
div[data-testid="stHorizontalBlock"] {
    gap: 0.4rem !important;
}

/* 滚动区域 */
.scrollable {
    max-height: 400px;
    overflow-y: auto;
    padding-right: 10px;
}

/* 自定义滚动条 */
.scrollable::-webkit-scrollbar {
    width: 6px;
}

.scrollable::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
}

.scrollable::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 3px;
}

.scrollable::-webkit-scrollbar-thumb:hover {
    background: #a1a1a1;
}
</style>
""", unsafe_allow_html=True)

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
        suggestion_prompt = st.text_area("单图建议提示词", value=config.get("suggestion_prompt", "请根据以下图片分析数据，给出专业的分析建议和优化方案：\n\n"), height=100)
        multi_image_prompt = st.text_area("多图对比提示词", value=config.get("multi_image_prompt", "请根据以下多张图片的分析数据，进行对比分析，给出专业的建议和优化方案：\n\n"), height=100)
        detail_page_prompt = st.text_area("详情页提示", value=config.get("detail_page_prompt", "请根据以下所有详情页的分析数据，进行综合分析，给出专业的建议和优化方案：\n\n"), height=100)
    
    # 保存 API 配置
    if st.button("保存配置"):
        config["api_key"] = api_key
        config["base_url"] = base_url
        config["model"] = model
        config["suggestion_prompt"] = suggestion_prompt
        config["multi_image_prompt"] = multi_image_prompt
        config["detail_page_prompt"] = detail_page_prompt
        save_config(config)
        st.success("配置保存成功！")
    
    # 功能管理
    st.subheader("功能管理")
    
    # 新增功能
    with st.expander("新增功能"):
        new_feature_name = st.text_input("功能名称", key="new_name")
        new_feature_prompt = st.text_area("提示词", key="new_prompt")
        new_feature_is_numeric = st.checkbox("是否返回数值", key="new_is_numeric")
        condition_options = ["", "大于", "小于", "等于", "大于等于", "小于等于"]
        new_feature_condition = st.selectbox("条件1", condition_options, index=0, disabled=not new_feature_is_numeric, key="new_condition")
        new_feature_threshold = st.text_input("阈值1", disabled=not new_feature_is_numeric, key="new_threshold")
        new_feature_condition2 = st.selectbox("条件2", condition_options, index=0, disabled=not new_feature_is_numeric, key="new_condition2")
        new_feature_threshold2 = st.text_input("阈值2", disabled=not new_feature_is_numeric, key="new_threshold2")
        if st.button("添加功能"):
            if new_feature_name and new_feature_prompt:
                config["features"].append({
                    "name": new_feature_name,
                    "prompt": new_feature_prompt,
                    "is_numeric": new_feature_is_numeric,
                    "condition": new_feature_condition,
                    "threshold": new_feature_threshold,
                    "condition2": new_feature_condition2,
                    "threshold2": new_feature_threshold2
                })
                save_config(config)
                st.success("功能添加成功！")
    
    # 编辑/删除功能
    st.subheader("现有功能")
    for i, feature in enumerate(config["features"]):
        with st.expander(feature["name"]):
            edited_name = st.text_input("功能名称", value=feature["name"], key=f"name_{i}")
            edited_prompt = st.text_area("提示词", value=feature["prompt"], key=f"prompt_{i}")
            edited_is_numeric = st.checkbox("是否返回数值", value=feature.get("is_numeric", False), key=f"is_numeric_{i}")
            condition_options = ["", "大于", "小于", "等于", "大于等于", "小于等于"]
            condition_index = condition_options.index(feature.get("condition", "")) if feature.get("condition", "") in condition_options else 0
            edited_condition = st.selectbox("条件1", condition_options, index=condition_index, disabled=not edited_is_numeric, key=f"condition_{i}")
            edited_threshold = st.text_input("阈值1", value=feature.get("threshold", ""), disabled=not edited_is_numeric, key=f"threshold_{i}")
            condition_index2 = condition_options.index(feature.get("condition2", "")) if feature.get("condition2", "") in condition_options else 0
            edited_condition2 = st.selectbox("条件2", condition_options, index=condition_index2, disabled=not edited_is_numeric, key=f"condition2_{i}")
            edited_threshold2 = st.text_input("阈值2", value=feature.get("threshold2", ""), disabled=not edited_is_numeric, key=f"threshold2_{i}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("更新", key=f"update_{i}"):
                    config["features"][i]["name"] = edited_name
                    config["features"][i]["prompt"] = edited_prompt
                    config["features"][i]["is_numeric"] = edited_is_numeric
                    config["features"][i]["condition"] = edited_condition
                    config["features"][i]["threshold"] = edited_threshold
                    config["features"][i]["condition2"] = edited_condition2
                    config["features"][i]["threshold2"] = edited_threshold2
                    save_config(config)
                    st.success("功能更新成功！")
            with col2:
                if st.button("删除", key=f"delete_{i}"):
                    config["features"].pop(i)
                    save_config(config)
                    st.success("功能删除成功！")

# 提取文本中的数值
def extract_numeric_value(text):
    import re
    # 提取所有数字（包括小数）
    numbers = re.findall(r'[-+]?\d*\.?\d+', text)
    if numbers:
        try:
            return float(numbers[0])
        except:
            return None
    return None

# 判断条件是否满足
def check_condition(value, condition, threshold):
    if value is None or not threshold:
        return None
    try:
        threshold = float(threshold)
        if condition == "大于":
            return value > threshold
        elif condition == "小于":
            return value < threshold
        elif condition == "等于":
            return abs(value - threshold) < 0.001
        elif condition == "大于等于":
            return value >= threshold
        elif condition == "小于等于":
            return value <= threshold
    except:
        return None
    return None

# 根据选择的模式显示不同的界面
if mode == "模式1: 单图分析":
    # 第一行：图片上传、分析结果、分析建议（各占三分之一）
    col1, col2, col3 = st.columns(3)

    # 图片上传
    with col1:
        st.header("图片上传")
        uploaded_file = st.file_uploader("选择图片", type=["jpg", "jpeg", "png", "webp"])
        
        if uploaded_file:
            st.image(uploaded_file, caption="上传的图片", width="stretch")
            
            # 功能选择
            st.header("分析功能")
            selected_features = []
            for feature in config["features"]:
                if st.checkbox(feature["name"]):
                    selected_features.append(feature)
            
            # 分析按钮
            if st.button("开始分析"):
                if not api_key:
                    st.error("请先配置 API Key！")
                elif not selected_features:
                    st.error("请至少选择一个分析功能！")
                else:
                    # 读取图片
                    image = Image.open(uploaded_file)
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='PNG')
                    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                    
                    # 初始化 OpenAI 客户端
                    client = OpenAI(
                        api_key=api_key,
                        base_url=base_url
                    )
                    
                    # 并发执行分析任务
                    results = {}
                    start_time = time.time()
                    
                    def analyze_feature(feature):
                        feature_start = time.time()
                        try:
                            response = client.chat.completions.create(
                                model=model,
                                messages=[
                                    {
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": feature["prompt"]},
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
                            feature_time = time.time() - feature_start
                            # 提取数值（如果需要）
                            numeric_value = None
                            if feature.get("is_numeric", False):
                                numeric_value = extract_numeric_value(result)
                            # 检查条件
                            condition_met = None
                            condition_met2 = None
                            if numeric_value is not None and feature.get("condition") and feature.get("threshold"):
                                condition_met = check_condition(numeric_value, feature["condition"], feature["threshold"])
                            if numeric_value is not None and feature.get("condition2") and feature.get("threshold2"):
                                condition_met2 = check_condition(numeric_value, feature["condition2"], feature["threshold2"])
                            return feature["name"], result, feature_time, numeric_value, condition_met, condition_met2, feature.get("is_numeric", False), feature.get("condition", ""), feature.get("threshold", ""), feature.get("condition2", ""), feature.get("threshold2", "")
                        except Exception as e:
                            feature_time = time.time() - feature_start
                            return feature["name"], f"错误：{str(e)}", feature_time, None, None, None, False, "", "", "", ""
                    
                    with ThreadPoolExecutor(max_workers=len(selected_features)) as executor:
                        future_to_feature = {executor.submit(analyze_feature, feature): feature for feature in selected_features}
                        for future in as_completed(future_to_feature):
                            feature_name, result, feature_time, numeric_value, condition_met, condition_met2, is_numeric, condition, threshold, condition2, threshold2 = future.result()
                            results[feature_name] = {"result": result, "time": feature_time, "numeric_value": numeric_value, "condition_met": condition_met, "condition_met2": condition_met2, "is_numeric": is_numeric, "condition": condition, "threshold": threshold, "condition2": condition2, "threshold2": threshold2}
                    
                    total_time = time.time() - start_time
                    
                    # 保存结果到会话状态
                    st.session_state["analysis_results"] = results
                    st.session_state["total_time"] = total_time
                    st.session_state["mode"] = "模式1"
                    st.rerun()

    # 分析结果
    with col2:
        st.header("分析结果")
        if "analysis_results" in st.session_state and st.session_state.get("mode") == "模式1":
            results = st.session_state["analysis_results"]
            total_time = st.session_state["total_time"]
            
            st.info(f"总耗时：{total_time:.2f} 秒")
            
            # 滚动区域
            st.markdown('<div class="scrollable">', unsafe_allow_html=True)
            for feature_name, data in results.items():
                with st.expander(f"{feature_name} (耗时：{data['time']:.2f} 秒)"):
                    # 显示数值（如果有）
                    if data.get("is_numeric", False) and data.get("numeric_value") is not None:
                        # 根据数值范围显示不同颜色
                        numeric_value = data['numeric_value']
                        if numeric_value < 30:
                            color = "red"
                        elif numeric_value < 70:
                            color = "orange"
                        else:
                            color = "green"
                        st.write(f"提取的数值：<span style='color:{color}; font-weight:bold;'>{numeric_value}</span>", unsafe_allow_html=True)
                    # 显示条件判断结果
                    if data.get("condition_met") is not None:
                        if data["condition_met"]:
                            st.success(f"条件1满足：{data['condition']} {data['threshold']}")
                        else:
                            st.error(f"条件1不满足：{data['condition']} {data['threshold']}")
                    # 显示第二个条件判断结果
                    if data.get("condition_met2") is not None:
                        if data["condition_met2"]:
                            st.success(f"条件2满足：{data['condition2']} {data['threshold2']}")
                        else:
                            st.error(f"条件2不满足：{data['condition2']} {data['threshold2']}")
                    # 显示原始结果
                    st.write(data["result"])
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.write("请上传图片并选择分析功能开始分析")

    # 分析建议
    with col3:
        st.header("分析建议")
        if "analysis_results" in st.session_state and st.session_state.get("mode") == "模式1":
            results = st.session_state["analysis_results"]
            analysis_data = []
            for feature_name, data in results.items():
                # 如果是数值功能且有数值，使用数值
                if data.get("is_numeric", False) and data.get("numeric_value") is not None:
                    value = data["numeric_value"]
                else:
                    # 如果不是数值功能或没有数值，使用生成的文本内容
                    value = data["result"]
                
                analysis_data.append({
                    "功能名称": feature_name,
                    "提取的数值": value,
                    "条件1": f"{data.get('condition', '')} {data.get('threshold', '')}" if data.get('condition') else "无",
                    "条件1结果": "满足" if data.get('condition_met') else "不满足" if data.get('condition_met') is not None else "无",
                    "条件2": f"{data.get('condition2', '')} {data.get('threshold2', '')}" if data.get('condition2') else "无",
                    "条件2结果": "满足" if data.get('condition_met2') else "不满足" if data.get('condition_met2') is not None else "无"
                })
            
            if analysis_data:
                # 生成建议的提示词
                suggestion_prompt = config.get("suggestion_prompt", "请根据以下图片分析数据，给出专业的分析建议和优化方案：\n\n")
                for item in analysis_data:
                    suggestion_prompt += f"- {item['功能名称']}: {item['提取的数值']}"
                    if item['条件1'] != "无":
                        suggestion_prompt += f" (条件1: {item['条件1']}, 结果: {item['条件1结果']})"
                    if item['条件2'] != "无":
                        suggestion_prompt += f" (条件2: {item['条件2']}, 结果: {item['条件2结果']})"
                    suggestion_prompt += "\n"
                
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
                                "content": suggestion_prompt
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
    if "analysis_results" in st.session_state and st.session_state.get("mode") == "模式1":
        results = st.session_state["analysis_results"]
        analysis_data = []
        for feature_name, data in results.items():
            # 如果是数值功能且有数值，使用数值
            if data.get("is_numeric", False) and data.get("numeric_value") is not None:
                value = data["numeric_value"]
            else:
                # 如果不是数值功能或没有数值，使用生成的文本内容
                value = data["result"]
            
            analysis_data.append({
                "功能名称": feature_name,
                "分析结果": value,
                "条件1": f"{data.get('condition', '')} {data.get('threshold', '')}" if data.get('condition') else "无",
                "条件1结果": "满足" if data.get('condition_met') else "不满足" if data.get('condition_met') is not None else "无",
                "条件2": f"{data.get('condition2', '')} {data.get('threshold2', '')}" if data.get('condition2') else "无",
                "条件2结果": "满足" if data.get('condition_met2') else "不满足" if data.get('condition_met2') is not None else "无"
            })
        if analysis_data:
            st.header("数据汇总")
            # 使用 st.dataframe 而不是 st.table，以更好地处理混合类型数据
            st.dataframe(analysis_data, use_container_width=True)

elif mode == "模式2: 多图对比分析":
    # 第一行：图片上传、分析结果、分析建议（各占三分之一）
    col1, col2, col3 = st.columns(3)

    # 图片上传
    with col1:
        st.header("图片上传")
        # 主图上传
        st.subheader("主图")
        main_image = st.file_uploader("上传主图", type=["jpg", "jpeg", "png", "webp"])
        if main_image:
            st.image(main_image, caption="主图", width="stretch")
        
        # 竞品图上传
        st.subheader("竞品图")
        competitor_images = st.file_uploader("上传竞品图（可多选）", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
        if competitor_images:
            st.write("已上传的竞品图：")
            for i, img in enumerate(competitor_images):
                st.write(f"- 竞品{i+1}: {img.name}")
        
        # 功能选择
        st.header("分析功能")
        selected_features = []
        for feature in config["features"]:
            if st.checkbox(feature["name"]):
                selected_features.append(feature)
        
        # 分析按钮
        if st.button("开始分析"):
            if not api_key:
                st.error("请先配置 API Key！")
            elif not selected_features:
                st.error("请至少选择一个分析功能！")
            elif not main_image:
                st.error("请上传主图！")
            else:
                # 准备所有图片
                images = []
                if main_image:
                    # 提取主图的本地名字
                    main_image_name = main_image.name.split('.')[0] if '.' in main_image.name else main_image.name
                    images.append((f"主图 ({main_image_name})", main_image, main_image_name))
                for i, img in enumerate(competitor_images):
                    # 提取竞品图的本地名字
                    img_name = img.name.split('.')[0] if '.' in img.name else img.name
                    images.append((f"竞品{i+1} ({img_name})", img, img_name))
                
                # 初始化 OpenAI 客户端
                client = OpenAI(
                    api_key=api_key,
                    base_url=base_url
                )
                
                # 分析所有图片
                all_results = {}
                image_names = {}
                start_time = time.time()
                
                for image_display_name, uploaded_file, image_local_name in images:
                    # 读取图片
                    image = Image.open(uploaded_file)
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='PNG')
                    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                    
                    # 并发执行分析任务
                    results = {}
                    
                    def analyze_feature(feature):
                        feature_start = time.time()
                        try:
                            response = client.chat.completions.create(
                                model=model,
                                messages=[
                                    {
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": feature["prompt"]},
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
                            feature_time = time.time() - feature_start
                            # 提取数值（如果需要）
                            numeric_value = None
                            if feature.get("is_numeric", False):
                                numeric_value = extract_numeric_value(result)
                            # 检查条件
                            condition_met = None
                            condition_met2 = None
                            if numeric_value is not None and feature.get("condition") and feature.get("threshold"):
                                condition_met = check_condition(numeric_value, feature["condition"], feature["threshold"])
                            if numeric_value is not None and feature.get("condition2") and feature.get("threshold2"):
                                condition_met2 = check_condition(numeric_value, feature["condition2"], feature["threshold2"])
                            return feature["name"], result, feature_time, numeric_value, condition_met, condition_met2, feature.get("is_numeric", False), feature.get("condition", ""), feature.get("threshold", ""), feature.get("condition2", ""), feature.get("threshold2", "")
                        except Exception as e:
                            feature_time = time.time() - feature_start
                            return feature["name"], f"错误：{str(e)}", feature_time, None, None, None, False, "", "", "", ""
                    
                    with ThreadPoolExecutor(max_workers=len(selected_features)) as executor:
                        future_to_feature = {executor.submit(analyze_feature, feature): feature for feature in selected_features}
                        for future in as_completed(future_to_feature):
                            feature_name, result, feature_time, numeric_value, condition_met, condition_met2, is_numeric, condition, threshold, condition2, threshold2 = future.result()
                            results[feature_name] = {"result": result, "time": feature_time, "numeric_value": numeric_value, "condition_met": condition_met, "condition_met2": condition_met2, "is_numeric": is_numeric, "condition": condition, "threshold": threshold, "condition2": condition2, "threshold2": threshold2}
                    
                    all_results[image_display_name] = results
                    image_names[image_display_name] = image_local_name
                
                total_time = time.time() - start_time
                
                # 保存结果到会话状态
                st.session_state["analysis_results"] = all_results
                st.session_state["total_time"] = total_time
                st.session_state["mode"] = "模式2"
                st.session_state["images"] = images
                st.session_state["image_names"] = image_names
                st.rerun()

    # 分析结果
    with col2:
        st.header("分析结果")
        if "analysis_results" in st.session_state and st.session_state.get("mode") == "模式2":
            all_results = st.session_state["analysis_results"]
            total_time = st.session_state["total_time"]
            
            st.info(f"总耗时：{total_time:.2f} 秒")
            
            # 滚动区域
            st.markdown('<div class="scrollable">', unsafe_allow_html=True)
            for image_name, results in all_results.items():
                with st.expander(f"{image_name}"):
                    for feature_name, data in results.items():
                        with st.expander(f"{feature_name} (耗时：{data['time']:.2f} 秒)"):
                            # 显示数值（如果有）
                            if data.get("is_numeric", False) and data.get("numeric_value") is not None:
                                # 根据数值范围显示不同颜色
                                numeric_value = data['numeric_value']
                                if numeric_value < 30:
                                    color = "red"
                                elif numeric_value < 70:
                                    color = "orange"
                                else:
                                    color = "green"
                                st.write(f"提取的数值：<span style='color:{color}; font-weight:bold;'>{numeric_value}</span>", unsafe_allow_html=True)
                            # 显示条件判断结果
                            if data.get("condition_met") is not None:
                                if data["condition_met"]:
                                    st.success(f"条件1满足：{data['condition']} {data['threshold']}")
                                else:
                                    st.error(f"条件1不满足：{data['condition']} {data['threshold']}")
                            # 显示第二个条件判断结果
                            if data.get("condition_met2") is not None:
                                if data["condition_met2"]:
                                    st.success(f"条件2满足：{data['condition2']} {data['threshold2']}")
                                else:
                                    st.error(f"条件2不满足：{data['condition2']} {data['threshold2']}")
                            # 显示原始结果
                            st.write(data["result"])
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.write("请上传图片并选择分析功能开始分析")

    # 分析建议
    with col3:
        st.header("分析建议")
        if "analysis_results" in st.session_state and st.session_state.get("mode") == "模式2":
            all_results = st.session_state["analysis_results"]
            image_names = st.session_state.get("image_names", {})
            
            analysis_data = []
            for image_display_name, results in all_results.items():
                image_local_name = image_names.get(image_display_name, "")
                for feature_name, data in results.items():
                    # 如果是数值功能且有数值，使用数值
                    if data.get("is_numeric", False) and data.get("numeric_value") is not None:
                        value = data["numeric_value"]
                    else:
                        # 如果不是数值功能或没有数值，使用生成的文本内容
                        value = data["result"]
                    
                    analysis_data.append({
                        "图片名称": image_display_name,
                        "本地文件名": image_local_name,
                        "功能名称": feature_name,
                        "提取的数值": value,
                        "条件1": f"{data.get('condition', '')} {data.get('threshold', '')}" if data.get('condition') else "无",
                        "条件1结果": "满足" if data.get('condition_met') else "不满足" if data.get('condition_met') is not None else "无",
                        "条件2": f"{data.get('condition2', '')} {data.get('threshold2', '')}" if data.get('condition2') else "无",
                        "条件2结果": "满足" if data.get('condition_met2') else "不满足" if data.get('condition_met2') is not None else "无"
                    })
            
            if analysis_data:
                # 生成建议的提示词
                multi_image_prompt = config.get("multi_image_prompt", "请根据以下多张图片的分析数据，进行对比分析，给出专业的建议和优化方案：\n\n")
                for item in analysis_data:
                    multi_image_prompt += f"- {item['图片名称']} ({item['本地文件名']}) - {item['功能名称']}: {item['提取的数值']}"
                    if item['条件1'] != "无":
                        multi_image_prompt += f" (条件1: {item['条件1']}, 结果: {item['条件1结果']})"
                    if item['条件2'] != "无":
                        multi_image_prompt += f" (条件2: {item['条件2']}, 结果: {item['条件2结果']})"
                    multi_image_prompt += "\n"
                
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
                                "content": multi_image_prompt
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
    if "analysis_results" in st.session_state and st.session_state.get("mode") == "模式2":
        all_results = st.session_state["analysis_results"]
        image_names = st.session_state.get("image_names", {})
        
        st.header("数据汇总")
        analysis_data = []
        for image_display_name, results in all_results.items():
            image_local_name = image_names.get(image_display_name, "")
            for feature_name, data in results.items():
                # 如果是数值功能且有数值，使用数值
                if data.get("is_numeric", False) and data.get("numeric_value") is not None:
                    value = data["numeric_value"]
                else:
                    # 如果不是数值功能或没有数值，使用生成的文本内容
                    value = data["result"]
                
                analysis_data.append({
                    "图片名称": image_display_name,
                    "本地文件名": image_local_name,
                    "功能名称": feature_name,
                    "分析结果": value,
                    "条件1": f"{data.get('condition', '')} {data.get('threshold', '')}" if data.get('condition') else "无",
                    "条件1结果": "满足" if data.get('condition_met') else "不满足" if data.get('condition_met') is not None else "无",
                    "条件2": f"{data.get('condition2', '')} {data.get('threshold2', '')}" if data.get('condition2') else "无",
                    "条件2结果": "满足" if data.get('condition_met2') else "不满足" if data.get('condition_met2') is not None else "无"
                })
        if analysis_data:
            # 使用 st.dataframe 而不是 st.table，以更好地处理混合类型数据
            st.dataframe(analysis_data, use_container_width=True)

else:  # 模式3: 详情页分析
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
                    detail_page_config = st.session_state["detail_page_configs"].get(detail_page_key, {"name": detail_page_key, "prompt": "请分析这张图片的内容，给出详细的分析结果。"})
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
