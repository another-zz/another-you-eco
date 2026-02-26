#!/bin/bash
# AnotherYou ECO v0.4 - macOS/Linux 启动器

echo "=========================================="
echo "  AnotherYou ECO v0.4 - 本地启动器"
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
pip install -q pygame numpy aiohttp

echo ""
echo "[4/4] 启动游戏..."
echo ""
echo "控制说明:"
echo "  F12    - 切换上帝视角"
echo "  TAB    - 管理员面板"
echo "  WASD   - 移动相机"
echo "  滚轮   - 缩放"
echo "  空格   - 暂停"
echo "  1/2/3  - 速度"
echo ""
echo "按回车键启动..."
read

python3 main_v4.py
