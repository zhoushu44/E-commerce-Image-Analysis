import streamlit as st
import os
import base64
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
            }
        ]
    }

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
        suggestion_prompt = st.text_area("单图建议提示词", value=config.get("suggestion_prompt", "请根据以下图片分析数据，给出专业的分析建议和优化方案：\n\n"), height=100)
        multi_image_prompt = st.text_area("多图对比提示词", value=config.get("multi_image_prompt", "请根据以下多张图片的分析数据，进行对比分析，给出专业的建议和优化方案：\n\n"), height=100)
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
                detail_page_name = f"详情页{i+1}"
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
                
                all_results[detail_page_name] = results
            
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
        for detail_page_name, results in all_results.items():
            with st.expander(f"{detail_page_name}"):
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
    if "analysis_results" in st.session_state and st.session_state.get("mode") == "模式3":
        all_results = st.session_state["analysis_results"]
        
        analysis_data = []
        for detail_page_name, results in all_results.items():
            for feature_name, data in results.items():
                # 如果是数值功能且有数值，使用数值
                if data.get("is_numeric", False) and data.get("numeric_value") is not None:
                    value = data["numeric_value"]
                else:
                    # 如果不是数值功能或没有数值，使用生成的文本内容
                    value = data["result"]
                
                analysis_data.append({
                    "详情页": detail_page_name,
                    "功能名称": feature_name,
                    "提取的数值": value,
                    "条件1": f"{data.get('condition', '')} {data.get('threshold', '')}" if data.get('condition') else "无",
                    "条件1结果": "满足" if data.get('condition_met') else "不满足" if data.get('condition_met') is not None else "无",
                    "条件2": f"{data.get('condition2', '')} {data.get('threshold2', '')}" if data.get('condition2') else "无",
                    "条件2结果": "满足" if data.get('condition_met2') else "不满足" if data.get('condition_met2') is not None else "无"
                })
        
        if analysis_data:
            # 生成建议的提示词
            detail_page_prompt = config.get("detail_page_prompt", "请根据以下所有详情页的分析数据，进行综合分析，给出专业的建议和优化方案：\n\n")
            for item in analysis_data:
                detail_page_prompt += f"- {item['详情页']} - {item['功能名称']}: {item['提取的数值']}"
                if item['条件1'] != "无":
                    detail_page_prompt += f" (条件1: {item['条件1']}, 结果: {item['条件1结果']})"
                if item['条件2'] != "无":
                    detail_page_prompt += f" (条件2: {item['条件2']}, 结果: {item['条件2结果']})"
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
    for i, (detail_page_name, results) in enumerate(all_results.items()):
        file_name = sorted_files[i].name if i < len(sorted_files) else ""
        for feature_name, data in results.items():
            # 如果是数值功能且有数值，使用数值
            if data.get("is_numeric", False) and data.get("numeric_value") is not None:
                value = data["numeric_value"]
            else:
                # 如果不是数值功能或没有数值，使用生成的文本内容
                value = data["result"]
            
            analysis_data.append({
                "详情页": detail_page_name,
                "文件名": file_name,
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

# 详细页面模块
st.header("详细页面")
with st.expander("详细页面配置"):
    # 动态生成详情页子模块，根据上传的图片数量
    sorted_files = st.session_state.get("sorted_files", [])
    num_detail_pages = len(sorted_files) if sorted_files else 10
    
    for i in range(num_detail_pages):
        with st.expander(f"详情页{i+1}"):
            # 每个子模块包含与主要功能模块相同的配置选项
            st.subheader(f"详情页{i+1} 配置")
            # 这里可以添加具体的配置选项，根据需要扩展
            st.write("详情页配置选项")

# 页脚
st.markdown("---")
st.markdown("智能图片分析工具 - 基于大模型能力的插件化解决方案")
