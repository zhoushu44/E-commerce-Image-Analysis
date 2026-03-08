import os
import subprocess
import shutil

# 清理之前的构建文件
if os.path.exists('dist'):
    shutil.rmtree('dist')
if os.path.exists('build'):
    shutil.rmtree('build')

# 构建应用程序
print("Building application...")
result = subprocess.run([
    'pyinstaller',
    '--onefile',
    '--console',
    '--icon=icons/main_detect.ico',
    '--name=主图检测',
    'start_app.py',
    '--add-data', 'image_analyzer_v3.py;.',
    '--add-data', 'image_tool_config.yaml;.',
    '--add-data', '.streamlit/config.toml;./.streamlit/',
], capture_output=True, text=True)

print("Build output:")
print(result.stdout)
print("Build errors:")
print(result.stderr)
print(f"Build return code: {result.returncode}")

if result.returncode == 0:
    print("Build successful!")
else:
    print("Build failed!")
