from PIL import Image, ImageDraw, ImageFont
import os

# 创建一个64x64的图像
img = Image.new('RGB', (64, 64), color='#3498db')
draw = ImageDraw.Draw(img)

# 尝试加载字体，如果失败则使用默认字体
try:
    font = ImageFont.truetype("arial.ttf", 12)
except:
    font = ImageFont.load_default()

# 绘制文字（因为图标小，文字可能看不清，只绘制一个简单的图形）
draw.rectangle([16, 16, 48, 48], fill='#2c3e50')
draw.ellipse([20, 20, 44, 44], fill='#e74c3c')

# 保存为ICO格式（PIL支持ICO）
img.save('main_detect.ico', format='ICO', sizes=[(64,64)])

print("图标已创建: main_detect.ico")