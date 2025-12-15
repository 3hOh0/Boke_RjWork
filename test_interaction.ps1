# 功能1测试脚本 (PowerShell)
# 使用方法: .\test_interaction.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "功能1 (Interaction) 测试脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查虚拟环境
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "✓ 找到虚拟环境" -ForegroundColor Green
    Write-Host "激活虚拟环境..." -ForegroundColor Yellow
    
    # 尝试激活虚拟环境
    try {
        & .\venv\Scripts\Activate.ps1
        Write-Host "✓ 虚拟环境已激活" -ForegroundColor Green
    } catch {
        Write-Host "⚠ 激活失败，可能需要设置执行策略" -ForegroundColor Yellow
        Write-Host "运行以下命令设置执行策略：" -ForegroundColor Yellow
        Write-Host "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor White
        Write-Host ""
        Write-Host "然后重新运行此脚本" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "✗ 未找到虚拟环境" -ForegroundColor Red
    Write-Host "创建虚拟环境..." -ForegroundColor Yellow
    
    # 创建虚拟环境
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ 创建虚拟环境失败" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✓ 虚拟环境创建成功" -ForegroundColor Green
    Write-Host "激活虚拟环境..." -ForegroundColor Yellow
    
    & .\venv\Scripts\Activate.ps1
    Write-Host "✓ 虚拟环境已激活" -ForegroundColor Green
    
    # 检查是否已安装依赖
    Write-Host "检查依赖..." -ForegroundColor Yellow
    try {
        python -c "import django" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "安装依赖包..." -ForegroundColor Yellow
            pip install -r requirements.txt
            if ($LASTEXITCODE -ne 0) {
                Write-Host "✗ 依赖安装失败" -ForegroundColor Red
                exit 1
            }
            Write-Host "✓ 依赖安装完成" -ForegroundColor Green
        } else {
            Write-Host "✓ 依赖已安装" -ForegroundColor Green
        }
    } catch {
        Write-Host "安装依赖包..." -ForegroundColor Yellow
        pip install -r requirements.txt
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "运行数据库迁移..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

python manage.py makemigrations interaction
python manage.py migrate interaction

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "运行测试..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 运行测试
python manage.py test interaction --verbosity=2

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ 所有测试通过！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "✗ 测试失败" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "提示：要启动开发服务器进行手动测试，运行：" -ForegroundColor Yellow
Write-Host "python manage.py runserver" -ForegroundColor White

