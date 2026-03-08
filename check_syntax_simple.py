import ast

try:
    with open('image_analyzer_v3.py', 'r', encoding='utf-8') as f:
        code = f.read()
    ast.parse(code)
    print("语法正确")
except SyntaxError as e:
    print(f"语法错误: {e.lineno}, {e.offset}, {e.msg}")
except Exception as e:
    print(f"其他错误: {e}")