@echo off
REM 功能1测试脚本 (Windows CMD)
REM 使用方法: test_interaction.bat

echo ========================================
echo 功能1 (Interaction) 测试脚本
echo ========================================
echo.

REM 检查虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo [OK] 找到虚拟环境
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
    echo [OK] 虚拟环境已激活
) else (
    echo [ERROR] 未找到虚拟环境
    echo 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] 创建虚拟环境失败
        exit /b 1
    )
    echo [OK] 虚拟环境创建成功
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
    echo [OK] 虚拟环境已激活
    
    REM 检查是否已安装依赖
    python -c "import django" 2>nul
    if errorlevel 1 (
        echo 安装依赖包...
        pip install -r requirements.txt
        if errorlevel 1 (
            echo [ERROR] 依赖安装失败
            exit /b 1
        )
        echo [OK] 依赖安装完成
    ) else (
        echo [OK] 依赖已安装
    )
)

echo.
echo ========================================
echo 运行数据库迁移...
echo ========================================

python manage.py makemigrations interaction
python manage.py migrate interaction

echo.
echo ========================================
echo 运行测试...
echo ========================================
echo.

REM 运行测试
python manage.py test interaction --verbosity=2

if errorlevel 1 (
    echo.
    echo ========================================
    echo [ERROR] 测试失败
    echo ========================================
    exit /b 1
) else (
    echo.
    echo ========================================
    echo [OK] 所有测试通过！
    echo ========================================
)

echo.
echo 提示：要启动开发服务器进行手动测试，运行：
echo python manage.py runserver

pause

