@echo off
setlocal
cd /d "%~dp0"

if exist "C:\Users\user\AppData\Local\Python\pythoncore-3.14-64\python.exe" (
    "C:\Users\user\AppData\Local\Python\pythoncore-3.14-64\python.exe" main.py
) else (
    python main.py
)
