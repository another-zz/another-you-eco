@echo off
chcp 65001 >nul
echo ==========================================
echo  AnotherYou ECO v0.4 - 本地启动器
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
pip install -q pygame numpy aiohttp

echo.
echo [4/4] 启动游戏...
echo.
echo 控制说明:
echo   F12    - 切换上帝视角
echo   TAB    - 管理员面板
echo   WASD   - 移动相机
echo   滚轮   - 缩放
echo   空格   - 暂停
echo   1/2/3  - 速度
echo.
echo 按任意键启动...
pause >nul

python main_v4.py

echo.
echo 游戏已退出
pause
