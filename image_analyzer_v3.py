import base64
import io
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import streamlit as st
import yaml
from openai import OpenAI
from PIL import Image

CONFIG_FILE = "image_tool_config.yaml"
MAX_IMAGE_BYTES = 1024 * 1024
MAX_FEATURE_WORKERS = 4
MODE_OPTIONS = {
    "模式1: 单图分析": "mode1",
    "模式2: 多图对比分析": "mode2",
    "模式3: 详情页分析": "mode3",
}
CONDITION_OPTIONS = ["", "大于", "小于", "等于", "大于等于", "小于等于"]
DEFAULT_FEATURES = [{'name': '计算比例', 'prompt': '你正在执行“模式1：单图分析”的电商主图单图评估。请只围绕当前这一张图片本身分析，不要做多图对比、详情页对比或竞品判断。\n\n请完成以下内容：\n1. 输出图片宽度、高度、宽高比，并将宽高比化为最简比例。\n2. 判断它更接近哪类主图比例：1:1、4:3、3:4、16:9、9:16 或其他。\n3. 评估当前比例是否适合电商主图/搜索列表缩略图展示，重点说明移动端缩略图中主体是否容易被看清。\n4. 估算产品/主体在画面中的面积占比，给出区间判断：过小（<60%）、适中（60%-80%）、过大（>80%）。\n5. 检查是否存在边缘裁切、主体贴边、留白不足、画面过宽/过扁导致信息稀释等问题。\n6. 给出“比例与主体占比优化建议”，必须具体到可执行动作，例如裁成 1:1、扩大主体、增加边距、调整到中心或轻微水平偏移等。\n\n输出格式：\n- 基础尺寸：\n- 宽高比例：\n- 主体占比判断：\n- 缩略图适配：\n- 主要问题：\n- 优化建议：', 'is_numeric': False, 'condition': '', 'threshold': '', 'condition2': '', 'threshold2': ''}, {'name': '对比度分析', 'prompt': '你正在执行“模式1：单图分析”的电商主图单图评估。请只围绕当前这一张图片本身分析，不要做多图对比、详情页对比或竞品判断。\n\n请从电商主图点击率视角分析对比度与视觉显著性：\n1. 判断主体与背景之间的明暗对比、颜色对比、饱和度对比是否足够让主体快速跳出来。\n2. 按 1-5 级给出对比强度等级：1级几乎无对比，2级弱对比，3级达标，4级强对比，5级极强对比。\n3. 判断背景是否干净，是否存在复杂纹理、杂物、强色块、人物面部、过亮/过暗区域等分散注意力的干扰。\n4. 如果图片含文字，检查文字与背景的可读性、文字颜色对比、是否遮挡产品核心区域。\n5. 判断当前对比是否适合移动端小图浏览：用户 0.5-3 秒内能否识别主体和核心卖点。\n6. 给出可执行优化动作，例如加深/提亮背景、增加阴影或描边、降低背景复杂度、模糊背景、减少干扰元素、提升文字底色对比等。\n\n输出格式：\n- 对比强度等级：\n- 主体突出度：\n- 背景干扰：\n- 文字可读性：\n- 移动端识别风险：\n- 优化建议：', 'is_numeric': False, 'condition': '', 'threshold': '', 'condition2': '', 'threshold2': ''}, {'name': '内容描述', 'prompt': '你正在执行“模式1：单图分析”的电商主图单图评估。请只围绕当前这一张图片本身分析，不要做多图对比、详情页对比或竞品判断。\n\n请用“电商运营审核”的方式描述并诊断这张主图：\n1. 先说明图片中出现的主体产品、人物/模特、场景、文字、价格/促销/标签、品牌或信任元素。\n2. 判断用户 3 秒内能否回答四个问题：这是什么、有什么用、好在哪、为什么要点开。\n3. 梳理视觉层级：第一眼看到什么，第二眼看到什么，产品、文字、背景、装饰之间优先级是否正确。\n4. 分析构图方式：中心构图、三分法、黄金分割、对角线、负空间或其他；判断焦点是否集中。\n5. 如果有文字，评估是否一图一核心、是否信息过载、是否存在多卖点堆砌、是否遮挡主体。\n6. 评估信任感：清晰度、真实感、材质/细节呈现、过度修图、廉价感、违规/夸张表达风险。\n7. 最后给出“保留项”和“优先修改项”，修改项按影响点击率的优先级排序。\n\n输出格式：\n- 画面内容：\n- 3秒识别结论：\n- 视觉层级：\n- 构图与焦点：\n- 图文信息：\n- 信任感风险：\n- 保留项：\n- 优先修改项：', 'is_numeric': False, 'condition': '', 'threshold': '', 'condition2': '', 'threshold2': ''}, {'name': '提取主色调', 'prompt': '你正在执行“模式1：单图分析”的电商主图单图评估。请只围绕当前这一张图片本身分析，不要做多图对比、详情页对比或竞品判断。\n\n请分析这张主图的色彩策略：\n1. 提取 3-6 个主要颜色，尽量用十六进制 RGB 色值表示，并说明大致占比。\n2. 区分主体色、背景色、文字/标签色、强调色。\n3. 判断色彩是否服务于产品识别、情绪表达和点击吸引，而不是只评价“好不好看”。\n4. 检查是否存在颜色过多、饱和度过高、主体与背景融色、促销色抢主体、文字颜色不可读等问题。\n5. 评估色彩与电商主图场景的适配性：是否高级、可信、干净、醒目，是否适合缩略图。\n6. 给出可执行配色建议，包括建议保留的颜色、需要弱化的颜色、背景替换方向、文字/标签颜色建议。\n\n输出格式：\n- 主色调列表：\n- 色彩角色分工：\n- 色彩对比与识别：\n- 情绪与品类适配：\n- 色彩问题：\n- 配色优化建议：', 'is_numeric': False, 'condition': '', 'threshold': '', 'condition2': '', 'threshold2': ''}]


def normalize_feature(feature):
    feature = feature or {}
    return {
        "name": feature.get("name", ""),
        "prompt": feature.get("prompt", ""),
        "is_numeric": bool(feature.get("is_numeric", False)),
        "condition": feature.get("condition", ""),
        "threshold": str(feature.get("threshold", "") or ""),
        "condition2": feature.get("condition2", ""),
        "threshold2": str(feature.get("threshold2", "") or ""),
    }


def get_default_config():
    return {
        "api_key": "",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
        "api_key_2": "",
        "base_url_2": "https://api.openai.com/v1",
        "model_2": "gpt-4o",
        "suggestion_prompt": "请根据以下图片分析数据，给出专业的分析建议和优化方案：\n\n",
        "multi_image_prompt": "请根据以下多张图片的分析数据，进行对比分析，给出专业的建议和优化方案：\n\n",
        "detail_page_prompt": "请根据以下主详情页与竞品详情页的分析数据，进行对比分析，给出专业的建议和优化方案：\n\n",
        "mode_configs": {
            "mode1": {"features": [normalize_feature(feature) for feature in DEFAULT_FEATURES]},
            "mode2": {"features": []},
            "mode3": {"features": []},
        },
    }


DEFAULT_CONFIG = get_default_config()


def ensure_config_structure(config):
    defaults = DEFAULT_CONFIG
    config = config or {}

    normalized = {
        "api_key": config.get("api_key", defaults["api_key"]),
        "base_url": config.get("base_url", defaults["base_url"]),
        "model": config.get("model", defaults["model"]),
        "api_key_2": config.get("api_key_2", defaults["api_key_2"]),
        "base_url_2": config.get("base_url_2", defaults["base_url_2"]),
        "model_2": config.get("model_2", defaults["model_2"]),
        "suggestion_prompt": config.get("suggestion_prompt", defaults["suggestion_prompt"]),
        "multi_image_prompt": config.get("multi_image_prompt", defaults["multi_image_prompt"]),
        "detail_page_prompt": config.get("detail_page_prompt", defaults["detail_page_prompt"]),
        "mode_configs": {
            "mode1": {"features": []},
            "mode2": {"features": []},
            "mode3": {"features": []},
        },
    }

    legacy_features = config.get("features")
    mode_configs = config.get("mode_configs", {}) or {}

    if mode_configs.get("mode1", {}).get("features"):
        normalized["mode_configs"]["mode1"]["features"] = [
            normalize_feature(feature) for feature in mode_configs["mode1"].get("features", [])
        ]
    elif legacy_features is not None:
        normalized["mode_configs"]["mode1"]["features"] = [normalize_feature(feature) for feature in legacy_features]
    else:
        normalized["mode_configs"]["mode1"]["features"] = defaults["mode_configs"]["mode1"]["features"]

    for mode_key in ["mode2", "mode3"]:
        normalized["mode_configs"][mode_key]["features"] = [
            normalize_feature(feature) for feature in mode_configs.get(mode_key, {}).get("features", [])
        ]

    return normalized


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            loaded = yaml.safe_load(file)
        return ensure_config_structure(loaded)
    return DEFAULT_CONFIG


def save_config(config):
    normalized = ensure_config_structure(config)
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        yaml.safe_dump(normalized, file, default_flow_style=False, allow_unicode=True, sort_keys=False)


config = load_config()

st.set_page_config(page_title="智能图片分析工具", page_icon="🖼️", layout="wide")

current_mode_key = MODE_OPTIONS[st.session_state.get("mode_label", list(MODE_OPTIONS.keys())[0]) if st.session_state.get("mode_label") in MODE_OPTIONS else list(MODE_OPTIONS.keys())[0]]

st.markdown(
    """
<style>
:root {
    color-scheme: light;
}

html, body, [class*="css"] {
    font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}

[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #f8f9fb 0%, #f3f5f7 100%);
    color: #111827;
}

[data-testid="stHeader"] {
    background: rgba(248, 249, 251, 0.9);
    backdrop-filter: blur(10px);
}

[data-testid="stMain"] {
    width: 100%;
}

[data-testid="stMainBlockContainer"] {
    width: 100%;
    max-width: none;
    padding-top: 1.4rem;
    padding-bottom: 2rem;
}

[data-testid="stAppViewContainer"]:has([data-testid="stSidebar"][aria-expanded="false"]) [data-testid="stMainBlockContainer"] {
    padding-left: 1.5rem;
    padding-right: 1.5rem;
}

[data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(3)) {
    align-items: flex-start;
    gap: 1rem;
}

[data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(3)) > [data-testid="stColumn"] {
    min-width: 0;
}

[data-testid="stAppViewContainer"]:has([data-testid="stSidebar"][aria-expanded="false"]) [data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(3)) {
    display: grid !important;
    grid-template-columns: minmax(220px, 320px) minmax(0, 1fr);
    gap: 1.25rem;
    align-items: start;
}

[data-testid="stAppViewContainer"]:has([data-testid="stSidebar"][aria-expanded="false"]) [data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(3)) > [data-testid="stColumn"]:nth-child(1) {
    grid-column: 1;
    grid-row: 1 / span 2;
}

[data-testid="stAppViewContainer"]:has([data-testid="stSidebar"][aria-expanded="false"]) [data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(3)) > [data-testid="stColumn"]:nth-child(2) {
    grid-column: 2;
    grid-row: 1;
}

[data-testid="stAppViewContainer"]:has([data-testid="stSidebar"][aria-expanded="false"]) [data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(3)) > [data-testid="stColumn"]:nth-child(3) {
    grid-column: 2;
    grid-row: 2;
}

[data-testid="stAppViewContainer"]:has([data-testid="stSidebar"][aria-expanded="false"]) [data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(3)) > [data-testid="stColumn"] {
    width: 100% !important;
    min-width: 0 !important;
    flex: none !important;
}

[data-testid="stSidebar"] {
    min-width: 280px;
    width: clamp(280px, 24vw, 360px) !important;
    background: #fbfbfb;
    border-right: 1px solid #e8eaed;
}

[data-testid="stSidebarContent"] {
    height: 100vh;
    padding: 0.8rem 0.95rem 1.4rem;
    overflow-y: auto;
    background: linear-gradient(180deg, #fcfcfc 0%, #f6f7f8 100%);
}

[data-testid="stSidebarUserContent"] {
    padding-bottom: 1.5rem;
}

[data-testid="stSidebar"] [data-testid="stExpander"] details,
[data-testid="stSidebar"] [data-testid="stTextInputRootElement"],
[data-testid="stSidebar"] [data-baseweb="textarea"],
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    border-radius: 14px !important;
}

[data-testid="stSidebar"] [data-testid="stExpander"] details {
    border: 1px solid #e8eaed;
    background: rgba(255, 255, 255, 0.92);
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}

[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    padding-top: 0.12rem;
    padding-bottom: 0.12rem;
}

[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stTextInputRootElement"],
[data-baseweb="textarea"] {
    border: 1px solid #e5e7eb !important;
    background: rgba(255, 255, 255, 0.96) !important;
    box-shadow: none !important;
}

[data-baseweb="select"] input,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
    font-size: 0.93rem !important;
}

[data-baseweb="input"] input:focus,
[data-baseweb="textarea"] textarea:focus,
[data-baseweb="select"] input:focus {
    box-shadow: none !important;
}

.stButton > button,
[data-testid="stDownloadButton"] > button {
    min-height: 2.6rem;
    border-radius: 12px !important;
    border: 1px solid #111827 !important;
    background: #111827 !important;
    color: #ffffff !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    box-shadow: 0 8px 18px rgba(17, 24, 39, 0.08) !important;
}

.stButton > button:hover,
[data-testid="stDownloadButton"] > button:hover {
    background: #1f2937 !important;
    border-color: #1f2937 !important;
    transform: translateY(-1px) !important;
}

.stButton > button[kind="secondary"] {
    background: #ffffff !important;
    color: #111827 !important;
    border: 1px solid #d8dde3 !important;
    box-shadow: none !important;
}

.stButton > button[kind="secondary"]:hover {
    background: #f8fafc !important;
    border-color: #cfd6de !important;
}

h1,
h2,
h3 {
    color: #111827 !important;
    letter-spacing: -0.01em;
}

h1 {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    margin-bottom: 0.4rem !important;
}

h2 {
    font-size: 1.08rem !important;
    font-weight: 600 !important;
    margin-top: 0.45rem !important;
    margin-bottom: 0.5rem !important;
}

h3 {
    font-size: 0.98rem !important;
    font-weight: 600 !important;
    margin-top: 0.35rem !important;
    margin-bottom: 0.25rem !important;
}

p,
li,
label,
[data-testid="stCaptionContainer"] {
    font-size: 0.92rem !important;
}

[data-testid="stMetric"],
[data-testid="stDataFrame"],
[data-testid="stExpander"] details,
[data-testid="stFileUploader"],
[data-testid="stImage"],
[data-testid="stAlertContainer"],
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px !important;
}

[data-testid="stFileUploader"] section,
[data-testid="stDataFrame"],
[data-testid="stAlertContainer"] {
    border: 1px solid #e7eaee !important;
    background: rgba(255, 255, 255, 0.92) !important;
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.04) !important;
}

[data-testid="stImage"] img {
    border-radius: 16px !important;
}

[data-testid="stAlertContainer"] {
    padding: 0.2rem 0.35rem;
}

[data-testid="stMarkdownContainer"] code {
    border-radius: 8px;
    background: #f3f4f6;
    padding: 0.12rem 0.35rem;
}

[data-testid="stCheckbox"] label {
    padding-top: 0.12rem;
    padding-bottom: 0.12rem;
}

.block-container .element-container {
    margin-bottom: 0.35rem;
}

.scrollable {
    max-height: min(68vh, 720px);
    overflow-y: auto;
    padding-right: 0.35rem;
}

.scrollable::-webkit-scrollbar {
    width: 6px;
}

.scrollable::-webkit-scrollbar-track {
    background: #eef0f2;
    border-radius: 999px;
}

.scrollable::-webkit-scrollbar-thumb {
    background: #c9ced6;
    border-radius: 999px;
}

.scrollable::-webkit-scrollbar-thumb:hover {
    background: #aeb6c1;
}

.app-footer {
    margin-top: 1.2rem;
    color: #6b7280;
    text-align: center;
    font-size: 0.88rem;
}

@media (max-width: 1200px) {
    [data-testid="stSidebar"] {
        min-width: 260px;
        width: min(100vw, 300px) !important;
    }

    [data-testid="stMainBlockContainer"] {
        width: 100%;
        max-width: none;
        padding-top: 1rem;
    }

    [data-testid="stAppViewContainer"]:has([data-testid="stSidebar"][aria-expanded="false"]) [data-testid="stMainBlockContainer"] {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    [data-testid="stAppViewContainer"]:has([data-testid="stSidebar"][aria-expanded="false"]) [data-testid="stMain"] [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(3)) {
        grid-template-columns: 1fr;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


def get_mode_features(mode_key):
    return config["mode_configs"][mode_key]["features"]


def extract_numeric_value(text):
    numbers = re.findall(r"[-+]?\d*\.?\d+", text)
    if numbers:
        try:
            return float(numbers[0])
        except Exception:
            return None
    return None


def check_condition(value, condition, threshold):
    if value is None or not threshold:
        return None
    try:
        threshold = float(threshold)
        if condition == "大于":
            return value > threshold
        if condition == "小于":
            return value < threshold
        if condition == "等于":
            return abs(value - threshold) < 0.001
        if condition == "大于等于":
            return value >= threshold
        if condition == "小于等于":
            return value <= threshold
    except Exception:
        return None
    return None


def get_api_settings(mode_key):
    if mode_key == "mode3":
        return {
            "api_key": config.get("api_key_2", ""),
            "base_url": config.get("base_url_2", DEFAULT_CONFIG["base_url_2"]),
            "model": config.get("model_2", DEFAULT_CONFIG["model_2"]),
        }
    return {
        "api_key": config.get("api_key", ""),
        "base_url": config.get("base_url", DEFAULT_CONFIG["base_url"]),
        "model": config.get("model", DEFAULT_CONFIG["model"]),
    }


def strip_extension(filename):
    return filename.rsplit(".", 1)[0] if "." in filename else filename


def ensure_rgb_image(image):
    if image.mode in ("RGBA", "LA"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.getchannel("A"))
        return background
    if image.mode != "RGB":
        return image.convert("RGB")
    return image


def encode_image_bytes(image, target_format, **save_kwargs):
    buffer = io.BytesIO()
    image.save(buffer, format=target_format, **save_kwargs)
    return buffer.getvalue()


def resize_image_if_needed(image, scale):
    if scale >= 0.999:
        return image
    width = max(1, int(image.width * scale))
    height = max(1, int(image.height * scale))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def compress_image_for_api(uploaded_file, max_bytes=MAX_IMAGE_BYTES):
    uploaded_file.seek(0)
    image = Image.open(uploaded_file)
    image.load()
    original_size = uploaded_file.size or 0
    original_format = (image.format or "PNG").upper()
    uploaded_file.seek(0)

    if original_format == "PNG" and image.mode in ("RGBA", "LA"):
        png_bytes = encode_image_bytes(image, "PNG", optimize=True)
        if len(png_bytes) <= max_bytes:
            return {
                "base64": base64.b64encode(png_bytes).decode("utf-8"),
                "mime_type": "image/png",
                "bytes": len(png_bytes),
                "original_bytes": original_size,
                "width": image.width,
                "height": image.height,
            }

    rgb_image = ensure_rgb_image(image)
    best_bytes = None
    best_meta = None

    scales = [1.0, 0.85, 0.7, 0.55, 0.4, 0.3, 0.25]
    qualities = [90, 75, 60, 45, 30]

    for scale in scales:
        candidate_image = resize_image_if_needed(rgb_image, scale)
        for quality in qualities:
            jpeg_bytes = encode_image_bytes(candidate_image, "JPEG", quality=quality, optimize=True)
            if best_bytes is None or len(jpeg_bytes) < len(best_bytes):
                best_bytes = jpeg_bytes
                best_meta = {
                    "mime_type": "image/jpeg",
                    "bytes": len(jpeg_bytes),
                    "original_bytes": original_size,
                    "width": candidate_image.width,
                    "height": candidate_image.height,
                }
            if len(jpeg_bytes) <= max_bytes:
                return {
                    "base64": base64.b64encode(jpeg_bytes).decode("utf-8"),
                    **best_meta,
                }

    if best_bytes is None:
        fallback_bytes = encode_image_bytes(rgb_image, "JPEG", quality=30, optimize=True)
        best_bytes = fallback_bytes
        best_meta = {
            "mime_type": "image/jpeg",
            "bytes": len(fallback_bytes),
            "original_bytes": original_size,
            "width": rgb_image.width,
            "height": rgb_image.height,
        }

    return {
        "base64": base64.b64encode(best_bytes).decode("utf-8"),
        **best_meta,
    }


def analyze_feature(client, model, image_payload, feature):
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
                                "url": f"data:{image_payload['mime_type']};base64,{image_payload['base64']}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=1000,
        )
        result = response.choices[0].message.content
        feature_time = time.time() - feature_start
        numeric_value = extract_numeric_value(result) if feature.get("is_numeric", False) else None
        condition_met = None
        condition_met2 = None
        if numeric_value is not None and feature.get("condition") and feature.get("threshold"):
            condition_met = check_condition(numeric_value, feature["condition"], feature["threshold"])
        if numeric_value is not None and feature.get("condition2") and feature.get("threshold2"):
            condition_met2 = check_condition(numeric_value, feature["condition2"], feature["threshold2"])
        return feature["name"], {
            "result": result,
            "time": feature_time,
            "numeric_value": numeric_value,
            "condition_met": condition_met,
            "condition_met2": condition_met2,
            "is_numeric": feature.get("is_numeric", False),
            "condition": feature.get("condition", ""),
            "threshold": feature.get("threshold", ""),
            "condition2": feature.get("condition2", ""),
            "threshold2": feature.get("threshold2", ""),
        }
    except Exception as exc:
        feature_time = time.time() - feature_start
        return feature["name"], {
            "result": f"错误：{str(exc)}",
            "time": feature_time,
            "numeric_value": None,
            "condition_met": None,
            "condition_met2": None,
            "is_numeric": False,
            "condition": "",
            "threshold": "",
            "condition2": "",
            "threshold2": "",
        }


def analyze_image_with_features(client, model, uploaded_file, selected_features):
    image_payload = compress_image_for_api(uploaded_file)
    results = {}
    max_workers = min(MAX_FEATURE_WORKERS, max(1, len(selected_features)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(analyze_feature, client, model, image_payload, feature) for feature in selected_features]
        for future in as_completed(futures):
            feature_name, feature_result = future.result()
            results[feature_name] = feature_result
    return {"results": results, "image_payload": image_payload}


def render_feature_result(data):
    if data.get("is_numeric", False) and data.get("numeric_value") is not None:
        numeric_value = data["numeric_value"]
        if numeric_value < 30:
            color = "red"
        elif numeric_value < 70:
            color = "orange"
        else:
            color = "green"
        st.write(
            f"提取的数值：<span style='color:{color}; font-weight:bold;'>{numeric_value}</span>",
            unsafe_allow_html=True,
        )
    if data.get("condition_met") is not None:
        if data["condition_met"]:
            st.success(f"条件1满足：{data['condition']} {data['threshold']}")
        else:
            st.error(f"条件1不满足：{data['condition']} {data['threshold']}")
    if data.get("condition_met2") is not None:
        if data["condition_met2"]:
            st.success(f"条件2满足：{data['condition2']} {data['threshold2']}")
        else:
            st.error(f"条件2不满足：{data['condition2']} {data['threshold2']}")
    st.write(data["result"])


def render_image_payload_info(payload):
    if not payload:
        return
    original_bytes = payload.get("original_bytes") or 0
    compressed_bytes = payload.get("bytes") or 0
    st.caption(
        "压缩信息："
        f"原始 {original_bytes / 1024:.1f} KB → "
        f"发送 {compressed_bytes / 1024:.1f} KB，"
        f"格式 {payload.get('mime_type', '')}，"
        f"尺寸 {payload.get('width', 0)}×{payload.get('height', 0)}"
    )


def get_result_display_value(data):
    if data.get("is_numeric", False) and data.get("numeric_value") is not None:
        return data["numeric_value"]
    return data["result"]


def build_condition_text(data, key_condition, key_threshold):
    if data.get(key_condition):
        return f"{data.get(key_condition, '')} {data.get(key_threshold, '')}".strip()
    return "无"


def build_condition_result_text(value):
    if value is None:
        return "无"
    return "满足" if value else "不满足"


def build_single_mode_summary_rows(results):
    rows = []
    for feature_name, data in results.items():
        rows.append(
            {
                "功能名称": feature_name,
                "分析结果": get_result_display_value(data),
                "条件1": build_condition_text(data, "condition", "threshold"),
                "条件1结果": build_condition_result_text(data.get("condition_met")),
                "条件2": build_condition_text(data, "condition2", "threshold2"),
                "条件2结果": build_condition_result_text(data.get("condition_met2")),
            }
        )
    return rows


def build_multi_mode_summary_rows(all_results, name_label, local_name_field, local_name_map):
    rows = []
    for display_name, results in all_results.items():
        local_name = local_name_map.get(display_name, "")
        for feature_name, data in results.items():
            rows.append(
                {
                    name_label: display_name,
                    local_name_field: local_name,
                    "功能名称": feature_name,
                    "分析结果": get_result_display_value(data),
                    "条件1": build_condition_text(data, "condition", "threshold"),
                    "条件1结果": build_condition_result_text(data.get("condition_met")),
                    "条件2": build_condition_text(data, "condition2", "threshold2"),
                    "条件2结果": build_condition_result_text(data.get("condition_met2")),
                }
            )
    return rows


def build_mode3_summary_rows(main_results, competitor_results, file_name_map):
    rows = []
    for group_name, result_dict in [("主详情页", main_results), ("竞品详情页", competitor_results)]:
        for display_name, results in result_dict.items():
            for feature_name, data in results.items():
                rows.append(
                    {
                        "图片分组": group_name,
                        "图片名称": display_name,
                        "文件名": file_name_map.get(display_name, ""),
                        "功能名称": feature_name,
                        "分析结果": data["result"],
                        "数值提取结果": data.get("numeric_value") if data.get("is_numeric", False) else "无",
                        "条件1": build_condition_text(data, "condition", "threshold"),
                        "条件1结果": build_condition_result_text(data.get("condition_met")),
                        "条件2": build_condition_text(data, "condition2", "threshold2"),
                        "条件2结果": build_condition_result_text(data.get("condition_met2")),
                    }
                )
    return rows


def build_summary_table_rows(rows):
    if not rows:
        return rows

    show_condition1 = any(row.get("条件1") != "无" for row in rows)
    show_condition2 = any(row.get("条件2") != "无" for row in rows)

    filtered_rows = []
    for row in rows:
        filtered_row = dict(row)
        if not show_condition1:
            filtered_row.pop("条件1", None)
            filtered_row.pop("条件1结果", None)
        if not show_condition2:
            filtered_row.pop("条件2", None)
            filtered_row.pop("条件2结果", None)
        filtered_rows.append(filtered_row)
    return filtered_rows


def build_prompt_from_rows(base_prompt, rows, name_label, local_name_field=None):
    prompt = base_prompt
    for row in rows:
        header = f"- {row[name_label]}"
        if local_name_field:
            header += f" ({row[local_name_field]})"
        header += f" - {row['功能名称']}: {row['分析结果']}"
        if row["条件1"] != "无":
            header += f" (条件1: {row['条件1']}, 结果: {row['条件1结果']})"
        if row["条件2"] != "无":
            header += f" (条件2: {row['条件2']}, 结果: {row['条件2结果']})"
        prompt += header + "\n"
    return prompt


def build_mode3_prompt(base_prompt, rows):
    prompt = base_prompt
    for row in rows:
        prompt += (
            f"- {row['图片分组']} | {row['图片名称']} ({row['文件名']}) | {row['功能名称']}: {row['分析结果']}"
        )
        if row["数值提取结果"] != "无":
            prompt += f" | 数值提取结果: {row['数值提取结果']}"
        if row["条件1"] != "无":
            prompt += f" | 条件1: {row['条件1']} ({row['条件1结果']})"
        if row["条件2"] != "无":
            prompt += f" | 条件2: {row['条件2']} ({row['条件2结果']})"
        prompt += "\n"
    return prompt


def export_feature_bundle(config_data):
    normalized = ensure_config_structure(config_data)
    return yaml.safe_dump(
        {
            "api_key": normalized["api_key"],
            "base_url": normalized["base_url"],
            "model": normalized["model"],
            "api_key_2": normalized["api_key_2"],
            "base_url_2": normalized["base_url_2"],
            "model_2": normalized["model_2"],
            "suggestion_prompt": normalized["suggestion_prompt"],
            "multi_image_prompt": normalized["multi_image_prompt"],
            "detail_page_prompt": normalized["detail_page_prompt"],
            "mode_configs": normalized["mode_configs"],
        },
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )


def import_feature_bundle(uploaded_file, config_data):
    try:
        uploaded_file.seek(0)
        imported = yaml.safe_load(uploaded_file.getvalue().decode("utf-8")) or {}
    except Exception as exc:
        return False, f"导入失败：{str(exc)}"

    if not isinstance(imported, dict):
        return False, "导入失败：文件内容格式不正确。"

    imported_mode_configs = imported.get("mode_configs")
    if not isinstance(imported_mode_configs, dict):
        return False, "导入失败：缺少 mode_configs 配置。"

    normalized_current = ensure_config_structure(config_data)
    normalized_current["api_key"] = imported.get("api_key", normalized_current["api_key"])
    normalized_current["base_url"] = imported.get("base_url", normalized_current["base_url"])
    normalized_current["model"] = imported.get("model", normalized_current["model"])
    normalized_current["api_key_2"] = imported.get("api_key_2", normalized_current["api_key_2"])
    normalized_current["base_url_2"] = imported.get("base_url_2", normalized_current["base_url_2"])
    normalized_current["model_2"] = imported.get("model_2", normalized_current["model_2"])
    normalized_current["suggestion_prompt"] = imported.get("suggestion_prompt", normalized_current["suggestion_prompt"])
    normalized_current["multi_image_prompt"] = imported.get("multi_image_prompt", normalized_current["multi_image_prompt"])
    normalized_current["detail_page_prompt"] = imported.get("detail_page_prompt", normalized_current["detail_page_prompt"])

    for mode_key in ["mode1", "mode2", "mode3"]:
        imported_features = imported_mode_configs.get(mode_key, {}).get("features", [])
        normalized_current["mode_configs"][mode_key]["features"] = [
            normalize_feature(feature) for feature in imported_features
        ]

    config_data.update(normalized_current)
    save_config(config_data)
    return True, "配置导入成功！"


def handle_select_all_change(section_key, features):
    value = st.session_state.get(f"{section_key}_select_all", False)
    for index in range(len(features)):
        st.session_state[f"{section_key}_feature_{index}"] = value


def sync_select_all_state(section_key, features):
    select_all_key = f"{section_key}_select_all"
    if not features:
        st.session_state[select_all_key] = False
        return
    st.session_state[select_all_key] = all(
        st.session_state.get(f"{section_key}_feature_{index}", False) for index in range(len(features))
    )


def render_feature_selector(section_key, features):
    if not features:
        st.info("当前模式还没有功能，请先在侧边栏新增功能。")
        return []

    select_all_key = f"{section_key}_select_all"
    current_all_selected = all(
        st.session_state.get(f"{section_key}_feature_{index}", False) for index in range(len(features))
    )
    if st.session_state.get(select_all_key) != current_all_selected:
        st.session_state[select_all_key] = current_all_selected

    st.checkbox(
        "全选功能",
        key=select_all_key,
        on_change=handle_select_all_change,
        args=(section_key, features),
    )

    selected_features = []
    for index, feature in enumerate(features):
        checkbox_key = f"{section_key}_feature_{index}"
        if checkbox_key not in st.session_state:
            st.session_state[checkbox_key] = False
        checked = st.checkbox(
            feature["name"],
            key=checkbox_key,
        )
        if checked:
            selected_features.append(feature)

    return selected_features



def generate_suggestion(prompt_text, api_key, base_url, model):
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt_text}],
        max_tokens=4000,
    )
    return response.choices[0].message.content


def build_mode1_suggestion_prompt(results):
    rows = build_single_mode_summary_rows(results)
    if not rows:
        return None
    prompt = config.get("suggestion_prompt", DEFAULT_CONFIG["suggestion_prompt"])
    for row in rows:
        prompt += f"- {row['功能名称']}: {row['分析结果']}\n"
        if row["条件1"] != "无":
            prompt += f"  条件1: {row['条件1']}, 结果: {row['条件1结果']}\n"
        if row["条件2"] != "无":
            prompt += f"  条件2: {row['条件2']}, 结果: {row['条件2结果']}\n"
    return prompt


def build_mode2_suggestion_prompt(results, image_names):
    rows = build_multi_mode_summary_rows(results, "图片名称", "本地文件名", image_names)
    if not rows:
        return None
    return build_prompt_from_rows(
        config.get("multi_image_prompt", DEFAULT_CONFIG["multi_image_prompt"]),
        rows,
        "图片名称",
        "本地文件名",
    )


def build_mode3_suggestion_prompt(results, file_names):
    rows = build_mode3_summary_rows(
        results.get("main_results", {}),
        results.get("competitor_results", {}),
        file_names,
    )
    if not rows:
        return None
    return build_mode3_prompt(
        config.get("detail_page_prompt", DEFAULT_CONFIG["detail_page_prompt"]),
        rows,
    )


def get_cached_suggestion(cache_key, prompt_text, api_settings):
    if not prompt_text:
        return None
    cached = st.session_state.get(cache_key)
    if not isinstance(cached, dict) or cached.get("prompt") != prompt_text:
        st.session_state[cache_key] = {
            "prompt": prompt_text,
            "value": generate_suggestion(
                prompt_text,
                api_settings["api_key"],
                api_settings["base_url"],
                api_settings["model"],
            ),
        }
    return st.session_state[cache_key]["value"]


with st.sidebar:
    mode_label = st.selectbox("选择模式", list(MODE_OPTIONS.keys()), key="mode_label")
    current_mode_key = MODE_OPTIONS[mode_label]

    with st.expander("配置管理", expanded=False):
        with st.expander("API 设置（模式1 / 模式2）", expanded=False):
            st.caption("模式1、模式2共用这套 API")
            api_key = st.text_input("API Key", value=config.get("api_key", ""), type="password")
            base_url = st.text_input("Base URL", value=config.get("base_url", "https://api.openai.com/v1"))
            model = st.text_input("Model", value=config.get("model", "gpt-4o"))

        with st.expander("API 设置（模式3）", expanded=False):
            st.caption("模式3单独使用这套 API")
            api_key_2 = st.text_input("API Key 2", value=config.get("api_key_2", ""), type="password")
            base_url_2 = st.text_input("Base URL 2", value=config.get("base_url_2", "https://api.openai.com/v1"))
            model_2 = st.text_input("Model 2", value=config.get("model_2", "gpt-4o"))

        with st.expander("建议提示词设置", expanded=False):
            st.caption("这里是通用配置区，但分别对应模式1 / 模式2 / 模式3 的建议生成")
            suggestion_prompt = st.text_area(
                "单图建议提示词（模式1）",
                value=config.get("suggestion_prompt", DEFAULT_CONFIG["suggestion_prompt"]),
                height=100,
            )
            multi_image_prompt = st.text_area(
                "多图对比提示词（模式2）",
                value=config.get("multi_image_prompt", DEFAULT_CONFIG["multi_image_prompt"]),
                height=100,
            )
            detail_page_prompt = st.text_area(
                "详情页对比提示词（模式3）",
                value=config.get("detail_page_prompt", DEFAULT_CONFIG["detail_page_prompt"]),
                height=100,
            )

        with st.expander("配置导入导出", expanded=False):
            st.caption("导出或导入完整配置，包括 API 设置、建议提示词和 3 个模式的功能。")
            feature_bundle_text = export_feature_bundle(config)
            st.download_button(
                "导出完整配置",
                data=feature_bundle_text,
                file_name="image_tool_config_bundle.yaml",
                mime="text/yaml",
                use_container_width=True,
            )
            imported_feature_file = st.file_uploader(
                "导入配置文件",
                type=["yaml", "yml"],
                key="feature_bundle_import",
            )
            if st.button("导入完整配置", key="import_feature_bundle", use_container_width=True):
                if not imported_feature_file:
                    st.error("请先选择要导入的配置文件。")
                else:
                    success, message = import_feature_bundle(imported_feature_file, config)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

        if st.button("保存配置", use_container_width=True):
            config["api_key"] = api_key
            config["base_url"] = base_url
            config["model"] = model
            config["api_key_2"] = api_key_2
            config["base_url_2"] = base_url_2
            config["model_2"] = model_2
            config["suggestion_prompt"] = suggestion_prompt
            config["multi_image_prompt"] = multi_image_prompt
            config["detail_page_prompt"] = detail_page_prompt
            save_config(config)
            st.success("配置保存成功！")

    current_features = get_mode_features(current_mode_key)
    st.subheader(f"功能管理（{mode_label.split(':')[0]}）")

    with st.expander("新增功能", expanded=False):
        new_feature_name = st.text_input("功能名称", key=f"new_name_{current_mode_key}")
        new_feature_prompt = st.text_area("提示词", key=f"new_prompt_{current_mode_key}")
        new_feature_is_numeric = st.checkbox("是否返回数值", key=f"new_is_numeric_{current_mode_key}")
        new_feature_condition = ""
        new_feature_threshold = ""
        new_feature_condition2 = ""
        new_feature_threshold2 = ""
        if new_feature_is_numeric:
            new_feature_condition = st.selectbox(
                "条件1",
                CONDITION_OPTIONS,
                index=0,
                key=f"new_condition_{current_mode_key}",
            )
            new_feature_threshold = st.text_input("阈值1", key=f"new_threshold_{current_mode_key}")
            new_feature_condition2 = st.selectbox(
                "条件2",
                CONDITION_OPTIONS,
                index=0,
                key=f"new_condition2_{current_mode_key}",
            )
            new_feature_threshold2 = st.text_input("阈值2", key=f"new_threshold2_{current_mode_key}")
        if st.button("添加功能", key=f"add_feature_{current_mode_key}", use_container_width=True):
            if new_feature_name and new_feature_prompt:
                current_features.append(
                    normalize_feature(
                        {
                            "name": new_feature_name,
                            "prompt": new_feature_prompt,
                            "is_numeric": new_feature_is_numeric,
                            "condition": new_feature_condition,
                            "threshold": new_feature_threshold,
                            "condition2": new_feature_condition2,
                            "threshold2": new_feature_threshold2,
                        }
                    )
                )
                save_config(config)
                st.success("功能添加成功！")
                st.rerun()
            else:
                st.error("请填写功能名称和提示词。")


    st.subheader("现有功能")
    if not current_features:
        st.write("当前模式暂无功能")

    for index, feature in enumerate(current_features):
        with st.expander(feature["name"] or f"功能{index + 1}"):
            edited_name = st.text_input("功能名称", value=feature["name"], key=f"name_{current_mode_key}_{index}")
            edited_prompt = st.text_area("提示词", value=feature["prompt"], key=f"prompt_{current_mode_key}_{index}")
            edited_is_numeric = st.checkbox(
                "是否返回数值",
                value=feature.get("is_numeric", False),
                key=f"is_numeric_{current_mode_key}_{index}",
            )
            edited_condition = feature.get("condition", "") if edited_is_numeric else ""
            edited_threshold = feature.get("threshold", "") if edited_is_numeric else ""
            edited_condition2 = feature.get("condition2", "") if edited_is_numeric else ""
            edited_threshold2 = feature.get("threshold2", "") if edited_is_numeric else ""
            if edited_is_numeric:
                edited_condition = st.selectbox(
                    "条件1",
                    CONDITION_OPTIONS,
                    index=CONDITION_OPTIONS.index(feature.get("condition", ""))
                    if feature.get("condition", "") in CONDITION_OPTIONS
                    else 0,
                    key=f"condition_{current_mode_key}_{index}",
                )
                edited_threshold = st.text_input(
                    "阈值1",
                    value=feature.get("threshold", ""),
                    key=f"threshold_{current_mode_key}_{index}",
                )
                edited_condition2 = st.selectbox(
                    "条件2",
                    CONDITION_OPTIONS,
                    index=CONDITION_OPTIONS.index(feature.get("condition2", ""))
                    if feature.get("condition2", "") in CONDITION_OPTIONS
                    else 0,
                    key=f"condition2_{current_mode_key}_{index}",
                )
                edited_threshold2 = st.text_input(
                    "阈值2",
                    value=feature.get("threshold2", ""),
                    key=f"threshold2_{current_mode_key}_{index}",
                )
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("更新", key=f"update_{current_mode_key}_{index}", use_container_width=True):
                    current_features[index] = normalize_feature(
                        {
                            "name": edited_name,
                            "prompt": edited_prompt,
                            "is_numeric": edited_is_numeric,
                            "condition": edited_condition,
                            "threshold": edited_threshold,
                            "condition2": edited_condition2,
                            "threshold2": edited_threshold2,
                        }
                    )
                    save_config(config)
                    st.success("功能更新成功！")
                    st.rerun()
            with col_b:
                if st.button("删除", key=f"delete_{current_mode_key}_{index}", use_container_width=True):
                    current_features.pop(index)
                    save_config(config)
                    st.success("功能删除成功！")
                    st.rerun()


if mode_label == "模式1: 单图分析":
    col1, col2, col3 = st.columns(3)
    mode1_api = get_api_settings("mode1")

    with col1:
        st.header("图片上传")
        uploaded_file = st.file_uploader("选择图片", type=["jpg", "jpeg", "png", "webp"])
        mode1_features = get_mode_features("mode1")

        if uploaded_file:
            st.image(uploaded_file, caption="上传的图片", width="stretch")
            st.header("分析功能")
            selected_features = render_feature_selector("mode1_analysis", mode1_features)

            if st.button("开始分析", key="start_mode1"):
                if not mode1_api["api_key"]:
                    st.error("请先配置 API Key！")
                elif not selected_features:
                    st.error("请至少选择一个分析功能！")
                else:
                    client = OpenAI(api_key=mode1_api["api_key"], base_url=mode1_api["base_url"])
                    start_time = time.time()
                    analysis = analyze_image_with_features(client, mode1_api["model"], uploaded_file, selected_features)
                    total_time = time.time() - start_time
                    st.session_state["analysis_results"] = analysis["results"]
                    st.session_state["analysis_payload"] = analysis["image_payload"]
                    st.session_state["mode1_suggestion"] = None
                    st.session_state["total_time"] = total_time
                    st.session_state["mode"] = "模式1"
                    st.rerun()

    with col2:
        st.header("分析结果")
        if "analysis_results" in st.session_state and st.session_state.get("mode") == "模式1":
            results = st.session_state["analysis_results"]
            st.info(f"总耗时：{st.session_state['total_time']:.2f} 秒")
            render_image_payload_info(st.session_state.get("analysis_payload"))
            st.markdown('<div class="scrollable">', unsafe_allow_html=True)
            for feature_name, data in results.items():
                with st.expander(f"{feature_name} (耗时：{data['time']:.2f} 秒)"):
                    render_feature_result(data)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.write("请上传图片并选择分析功能开始分析")

    with col3:
        st.header("分析建议")
        if "analysis_results" in st.session_state and st.session_state.get("mode") == "模式1":
            prompt_text = build_mode1_suggestion_prompt(st.session_state["analysis_results"])
            if prompt_text:
                try:
                    suggestion = get_cached_suggestion("mode1_suggestion", prompt_text, mode1_api)
                    st.markdown('<div class="scrollable">', unsafe_allow_html=True)
                    st.write(suggestion)
                    st.markdown("</div>", unsafe_allow_html=True)
                except Exception as exc:
                    st.error(f"生成建议时出错：{str(exc)}")
        else:
            st.write("分析后将显示建议")

    if "analysis_results" in st.session_state and st.session_state.get("mode") == "模式1":
        rows = build_single_mode_summary_rows(st.session_state["analysis_results"])
        if rows:
            st.header("数据汇总")
            st.dataframe(build_summary_table_rows(rows), use_container_width=True)

elif mode_label == "模式2: 多图对比分析":
    col1, col2, col3 = st.columns(3)
    mode2_api = get_api_settings("mode2")

    with col1:
        st.header("图片上传")
        st.subheader("主图")
        main_image = st.file_uploader("上传主图", type=["jpg", "jpeg", "png", "webp"])
        if main_image:
            st.image(main_image, caption="主图", width="stretch")

        st.subheader("竞品图")
        competitor_images = st.file_uploader(
            "上传竞品图（可多选）",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
        )
        if competitor_images:
            st.write("已上传的竞品图：")
            for index, image in enumerate(competitor_images):
                st.write(f"- 竞品{index + 1}: {image.name}")

        st.header("分析功能")
        mode2_features = get_mode_features("mode2")
        selected_features = render_feature_selector("mode2_analysis", mode2_features)

        if st.button("开始分析", key="start_mode2"):
            if not mode2_api["api_key"]:
                st.error("请先配置 API Key！")
            elif not selected_features:
                st.error("请至少选择一个分析功能！")
            elif not main_image:
                st.error("请上传主图！")
            else:
                images = []
                main_image_name = strip_extension(main_image.name)
                images.append((f"主图 ({main_image_name})", main_image, main_image_name))
                for index, image in enumerate(competitor_images or []):
                    image_name = strip_extension(image.name)
                    images.append((f"竞品{index + 1} ({image_name})", image, image_name))

                client = OpenAI(api_key=mode2_api["api_key"], base_url=mode2_api["base_url"])
                all_results = {}
                image_names = {}
                image_payloads = {}
                start_time = time.time()
                for display_name, uploaded_image, local_name in images:
                    analysis = analyze_image_with_features(client, mode2_api["model"], uploaded_image, selected_features)
                    all_results[display_name] = analysis["results"]
                    image_names[display_name] = local_name
                    image_payloads[display_name] = analysis["image_payload"]
                total_time = time.time() - start_time
                st.session_state["analysis_results"] = all_results
                st.session_state["analysis_payloads"] = image_payloads
                st.session_state["mode2_suggestion"] = None
                st.session_state["total_time"] = total_time
                st.session_state["mode"] = "模式2"
                st.session_state["image_names"] = image_names
                st.rerun()

    with col2:
        st.header("分析结果")
        if "analysis_results" in st.session_state and st.session_state.get("mode") == "模式2":
            all_results = st.session_state["analysis_results"]
            st.info(f"总耗时：{st.session_state['total_time']:.2f} 秒")
            st.markdown('<div class="scrollable">', unsafe_allow_html=True)
            for image_name, results in all_results.items():
                with st.expander(image_name):
                    render_image_payload_info(st.session_state.get("analysis_payloads", {}).get(image_name))
                    for feature_name, data in results.items():
                        with st.expander(f"{feature_name} (耗时：{data['time']:.2f} 秒)"):
                            render_feature_result(data)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.write("请上传图片并选择分析功能开始分析")

    with col3:
        st.header("分析建议")
        if "analysis_results" in st.session_state and st.session_state.get("mode") == "模式2":
            prompt_text = build_mode2_suggestion_prompt(
                st.session_state["analysis_results"],
                st.session_state.get("image_names", {}),
            )
            if prompt_text:
                try:
                    suggestion = get_cached_suggestion("mode2_suggestion", prompt_text, mode2_api)
                    st.markdown('<div class="scrollable">', unsafe_allow_html=True)
                    st.write(suggestion)
                    st.markdown("</div>", unsafe_allow_html=True)
                except Exception as exc:
                    st.error(f"生成建议时出错：{str(exc)}")
        else:
            st.write("分析后将显示建议")

    if "analysis_results" in st.session_state and st.session_state.get("mode") == "模式2":
        rows = build_multi_mode_summary_rows(
            st.session_state["analysis_results"],
            "图片名称",
            "本地文件名",
            st.session_state.get("image_names", {}),
        )
        if rows:
            st.header("数据汇总")
            st.dataframe(build_summary_table_rows(rows), use_container_width=True)

else:
    col1, col2, col3 = st.columns(3)
    mode3_api = get_api_settings("mode3")

    with col1:
        st.header("图片上传")
        st.subheader("主详情页")
        main_detail_image = st.file_uploader("上传主详情页单图", type=["jpg", "jpeg", "png", "webp"])
        if main_detail_image:
            st.image(main_detail_image, caption="主详情页", width="stretch")

        st.subheader("竞品详情页")
        competitor_detail_images = st.file_uploader(
            "上传竞品详情页（可多选）",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
        )
        if competitor_detail_images:
            st.write("已上传的竞品详情页：")
            for index, image in enumerate(competitor_detail_images):
                st.write(f"- 竞品详情页{index + 1}: {image.name}")

        st.header("分析功能")
        mode3_features = get_mode_features("mode3")
        selected_features = render_feature_selector("mode3_analysis", mode3_features)

        if st.button("开始分析", key="start_mode3"):
            if not mode3_api["api_key"]:
                st.error("请先配置 API 设置2！")
            elif not main_detail_image:
                st.error("请上传主详情页！")
            elif not selected_features:
                st.error("请至少选择一个分析功能！")
            else:
                client = OpenAI(api_key=mode3_api["api_key"], base_url=mode3_api["base_url"])
                start_time = time.time()

                main_display_name = f"主详情页 ({strip_extension(main_detail_image.name)})"
                main_analysis = analyze_image_with_features(
                    client,
                    mode3_api["model"],
                    main_detail_image,
                    selected_features,
                )

                competitor_results = {}
                competitor_payloads = {}
                detail_file_names = {main_display_name: main_detail_image.name}
                for index, image in enumerate(competitor_detail_images or []):
                    display_name = f"竞品详情页{index + 1} ({strip_extension(image.name)})"
                    analysis = analyze_image_with_features(client, mode3_api["model"], image, selected_features)
                    competitor_results[display_name] = analysis["results"]
                    competitor_payloads[display_name] = analysis["image_payload"]
                    detail_file_names[display_name] = image.name

                total_time = time.time() - start_time
                st.session_state["analysis_results"] = {
                    "main_results": {main_display_name: main_analysis["results"]},
                    "competitor_results": competitor_results,
                }
                st.session_state["analysis_payloads"] = {
                    "main_payloads": {main_display_name: main_analysis["image_payload"]},
                    "competitor_payloads": competitor_payloads,
                }
                st.session_state["mode3_suggestion"] = None
                st.session_state["detail_page_file_names"] = detail_file_names
                st.session_state["total_time"] = total_time
                st.session_state["mode"] = "模式3"
                st.rerun()

    with col2:
        st.header("分析结果")
        if "analysis_results" in st.session_state and st.session_state.get("mode") == "模式3":
            mode3_results = st.session_state["analysis_results"]
            mode3_payloads = st.session_state.get("analysis_payloads", {})
            st.info(f"总耗时：{st.session_state['total_time']:.2f} 秒")
            st.markdown('<div class="scrollable">', unsafe_allow_html=True)

            st.subheader("主详情页分析结果")
            for display_name, results in mode3_results.get("main_results", {}).items():
                with st.expander(display_name, expanded=True):
                    render_image_payload_info(mode3_payloads.get("main_payloads", {}).get(display_name))
                    for feature_name, data in results.items():
                        with st.expander(f"{feature_name} (耗时：{data['time']:.2f} 秒)"):
                            render_feature_result(data)

            st.subheader("竞品详情页分析结果")
            competitor_results = mode3_results.get("competitor_results", {})
            if competitor_results:
                for display_name, results in competitor_results.items():
                    with st.expander(display_name):
                        render_image_payload_info(mode3_payloads.get("competitor_payloads", {}).get(display_name))
                        for feature_name, data in results.items():
                            with st.expander(f"{feature_name} (耗时：{data['time']:.2f} 秒)"):
                                render_feature_result(data)
            else:
                st.write("未上传竞品详情页，当前仅展示主详情页分析结果。")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.write("请上传图片并选择分析功能开始分析")

    with col3:
        st.header("综合建议")
        if "analysis_results" in st.session_state and st.session_state.get("mode") == "模式3":
            mode3_results = st.session_state["analysis_results"]
            prompt_text = build_mode3_suggestion_prompt(
                mode3_results,
                st.session_state.get("detail_page_file_names", {}),
            )
            if prompt_text:
                try:
                    suggestion = get_cached_suggestion("mode3_suggestion", prompt_text, mode3_api)
                    st.markdown('<div class="scrollable">', unsafe_allow_html=True)
                    st.write(suggestion)
                    st.markdown("</div>", unsafe_allow_html=True)
                except Exception as exc:
                    st.error(f"生成建议时出错：{str(exc)}")
        else:
            st.write("分析后将显示建议")

    if "analysis_results" in st.session_state and st.session_state.get("mode") == "模式3":
        mode3_results = st.session_state["analysis_results"]
        rows = build_mode3_summary_rows(
            mode3_results.get("main_results", {}),
            mode3_results.get("competitor_results", {}),
            st.session_state.get("detail_page_file_names", {}),
        )
        if rows:
            st.header("数据汇总")
            st.dataframe(build_summary_table_rows(rows), use_container_width=True)

st.markdown("---")
st.markdown('<div class="app-footer">智能图片分析工具 · 极简工作台</div>', unsafe_allow_html=True)
