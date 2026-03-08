import sys
import os

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current directory: {os.getcwd()}")

try:
    import streamlit
    print(f"Streamlit version: {streamlit.__version__}")
except ImportError:
    print("Streamlit is not installed")
