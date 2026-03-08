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
</style>
""", unsafe_allow_html=True)

st.title("🖼️ 智能图片分析工具 - 版本3")

# 侧边栏配置
with st.sidebar:
    st.header("配置管理")
    
    # API 配置
    st.subheader("API 设置")
    api_key = st.text_input("API Key", value=config.get("api_key", ""), type="password")
    base_url = st.text_input("Base URL", value=config.get("base_url", "https://api.openai.com/v1"))
    model = st.text_input("Model", value=config.get("model", "gpt-4o"))
    
    # 建议提示词配置
    st.subheader("建议提示词设置")
    suggestion_prompt = st.text_area("建议提示词", value=config.get("suggestion_prompt", "请根据以下图片分析数据，给出专业的分析建议和优化方案：\n\n"), height=100)
    
    # 保存 API 配置
    if st.button("保存配置"):
        config["api_key"] = api_key
        config["base_url"] = base_url
        config["model"] = model
        config["suggestion_prompt"] = suggestion_prompt
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

# 主界面
col1, col2 = st.columns([1, 2])

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
                st.rerun()

with col2:
    st.header("分析结果")
    if "analysis_results" in st.session_state:
        results = st.session_state["analysis_results"]
        total_time = st.session_state["total_time"]
        
        st.info(f"总耗时：{total_time:.2f} 秒")
        
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
    else:
        st.write("请上传图片并选择分析功能开始分析")

# 数值汇总表格
if "analysis_results" in st.session_state:
    results = st.session_state["analysis_results"]
    numeric_data = []
    for feature_name, data in results.items():
        if data.get("is_numeric", False) and data.get("numeric_value") is not None:
            numeric_data.append({
                "功能名称": feature_name,
                "提取的数值": data["numeric_value"],
                "条件1": f"{data.get('condition', '')} {data.get('threshold', '')}" if data.get('condition') else "无",
                "条件1结果": "满足" if data.get('condition_met') else "不满足" if data.get('condition_met') is not None else "无",
                "条件2": f"{data.get('condition2', '')} {data.get('threshold2', '')}" if data.get('condition2') else "无",
                "条件2结果": "满足" if data.get('condition_met2') else "不满足" if data.get('condition_met2') is not None else "无"
            })
    if numeric_data:
        st.markdown("---")
        st.header("数值汇总")
        st.table(numeric_data)
        
        # 大模型建议
        st.markdown("---")
        st.header("分析建议")
        
        # 生成建议的提示词
        suggestion_prompt = config.get("suggestion_prompt", "请根据以下图片分析数据，给出专业的分析建议和优化方案：\n\n")
        for item in numeric_data:
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
            st.write(suggestion)
        except Exception as e:
            st.error(f"生成建议时出错：{str(e)}")

# 页脚
st.markdown("---")
st.markdown("智能图片分析工具 - 基于大模型能力的插件化解决方案")
