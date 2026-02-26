#!/bin/bash
# GitHub 推送修复脚本
# 在本地运行此脚本同步最新更改

echo "修复启动脚本..."

# 修复 start_mac.sh
cat > start_mac.sh << 'EOF'
#!/bin/bash
# AnotherYou ECO v0.6 - AI灵魂版

echo "=========================================="
echo "  AnotherYou ECO v0.6 - AI灵魂版"
echo "=========================================="
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到Python3"
    echo "macOS: brew install python3"
    echo "Linux: sudo apt install python3"
    exit 1
fi

echo "[1/4] Python版本:"
python3 --version

echo ""
echo "[2/4] 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

echo ""
echo "[3/4] 安装依赖..."
source venv/bin/activate
pip install -q pygame numpy

echo ""
echo "[4/4] 启动游戏..."
echo ""
echo "控制说明:"
echo "  空格   - 切换玩家控制/AI自主"
echo "  WASD   - 移动"
echo "  ESC    - 释放控制（切回AI）"
echo "  F12    - 上帝模式"
echo "  1/2/3  - 速度"
echo ""
echo "按回车键启动..."
read

python3 main.py
EOF

chmod +x start_mac.sh

echo "✅ start_mac.sh 已修复"

# 修复 start_windows.bat
cat > start_windows.bat << 'EOF'
@echo off
chcp 65001 >nul
echo ==========================================
echo  AnotherYou ECO v0.6 - AI灵魂版
echo ==========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] 检查Python版本...
python --version

echo.
echo [2/4] 创建虚拟环境...
if not exist venv (
    python -m venv venv
)

echo.
echo [3/4] 安装依赖...
call venv\Scripts\activate
pip install -q pygame numpy

echo.
echo [4/4] 启动游戏...
echo.
echo 控制说明:
echo   空格   - 切换玩家控制/AI自主
echo   WASD   - 移动
echo   ESC    - 释放控制（切回AI）
echo   F12    - 上帝模式
echo   1/2/3  - 速度
echo.
echo 按任意键启动...
pause >nul

python main.py

echo.
echo 游戏已退出
pause
EOF

echo "✅ start_windows.bat 已修复"
echo ""
echo "现在可以运行: ./start_mac.sh 或 python main.py"
