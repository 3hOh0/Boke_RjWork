# 功能1测试指南

## 问题修复：ModuleNotFoundError: No module named 'django'

这个错误是因为没有激活虚拟环境。请按照以下步骤操作：

### 方法1：使用现有虚拟环境（如果已创建）

**Windows PowerShell:**
```powershell
# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 如果遇到执行策略错误，先运行：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 然后再次激活
.\venv\Scripts\Activate.ps1
```

**Windows CMD:**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 方法2：创建新的虚拟环境

**Windows PowerShell:**
```powershell
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 如果遇到执行策略错误
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

**Windows CMD:**
```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 运行测试

### 1. 确保数据库已配置

检查 `djangoblog/settings.py` 中的数据库配置。如果使用 SQLite（测试环境），通常不需要额外配置。

### 2. 运行数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. 运行 interaction 应用的测试

```bash
# 运行所有 interaction 测试
python manage.py test interaction

# 运行特定测试类
python manage.py test interaction.tests.InteractionTests

# 运行特定测试方法
python manage.py test interaction.tests.InteractionTests.test_toggle_like_anonymous

# 详细输出
python manage.py test interaction --verbosity=2
```

### 4. 运行所有测试

```bash
python manage.py test
```

## 手动测试步骤

### 1. 启动开发服务器

```bash
python manage.py runserver
```

### 2. 测试功能点

#### 2.1 点赞功能
1. 访问任意文章详情页：`http://127.0.0.1:8000/article/xxx/`
2. 点击"Like"按钮（无需登录）
3. 检查点赞数是否增加
4. 再次点击取消点赞

#### 2.2 收藏功能
1. 在文章详情页点击"⭐ Save"按钮
2. 弹出快速收藏模态框
3. 创建新收藏夹或选择已有收藏夹
4. 保存文章到收藏夹

#### 2.3 收藏夹管理
1. 访问收藏夹Dashboard：`http://127.0.0.1:8000/interaction/dashboard/`
2. 需要先登录
3. 创建、编辑、删除收藏夹
4. 查看收藏夹中的文章列表

#### 2.4 分享功能
1. 在Dashboard中，将收藏夹设置为"公开"
2. 复制分享链接
3. 在无痕浏览器中访问分享链接
4. 验证可以查看公开收藏夹内容

#### 2.5 排行榜
1. 访问排行榜页面：`http://127.0.0.1:8000/interaction/leaderboard/`
2. 测试时间筛选（24小时/7天/30天/全部）
3. 检查排序是否正确

#### 2.6 公开收藏夹发现
1. 访问：`http://127.0.0.1:8000/interaction/public/`
2. 查看所有公开收藏夹列表

### 3. API 测试

#### 3.1 点赞 API
```bash
# 点赞
curl -X POST http://127.0.0.1:8000/interaction/api/like/ \
  -H "Content-Type: application/json" \
  -d '{"article_id": 1}'

# 取消点赞（再次发送相同请求）
curl -X POST http://127.0.0.1:8000/interaction/api/like/ \
  -H "Content-Type: application/json" \
  -d '{"article_id": 1}'
```

#### 3.2 收藏夹 API
```bash
# 创建收藏夹（需要登录）
curl -X POST http://127.0.0.1:8000/interaction/api/folders/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=xxx" \
  -d '{"name": "测试收藏夹", "description": "描述"}'

# 获取收藏夹列表
curl http://127.0.0.1:8000/interaction/api/folders/

# 添加文章到收藏夹
curl -X POST http://127.0.0.1:8000/interaction/api/favorite-item/ \
  -H "Content-Type: application/json" \
  -d '{"folder_id": 1, "article_id": 1}'
```

#### 3.3 排行榜 API
```bash
# 获取排行榜
curl http://127.0.0.1:8000/interaction/api/leaderboard/

# 按时间筛选
curl "http://127.0.0.1:8000/interaction/api/leaderboard/?since=2024-01-01T00:00:00Z"
```

## 测试检查清单

- [ ] 匿名用户可以点赞
- [ ] 登录用户可以点赞
- [ ] 点赞数正确显示
- [ ] 可以取消点赞
- [ ] 匿名用户可以收藏（通过快速保存）
- [ ] 登录用户可以创建收藏夹
- [ ] 可以添加文章到收藏夹
- [ ] 可以从收藏夹移除文章
- [ ] 收藏夹可以设置为公开
- [ ] 公开收藏夹可以通过分享链接访问
- [ ] 排行榜按点赞数排序
- [ ] 排行榜支持时间筛选
- [ ] Dashboard 需要登录才能访问
- [ ] 所有 AJAX 请求正常工作
- [ ] 前端样式正确显示
- [ ] 响应式设计在不同屏幕尺寸下正常

## 常见问题

### Q1: 执行策略错误（PowerShell）
**错误信息：** `无法加载文件，因为在此系统上禁止运行脚本`

**解决方法：**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q2: 数据库连接错误
**解决方法：**
- 检查 `djangoblog/settings.py` 中的数据库配置
- 确保数据库服务已启动
- 对于测试，可以使用 SQLite（默认）

### Q3: 静态文件404错误
**解决方法：**
```bash
python manage.py collectstatic --noinput
python manage.py compress --force
```

### Q4: 迁移文件冲突
**解决方法：**
```bash
# 删除冲突的迁移文件（谨慎操作）
# 重新生成迁移
python manage.py makemigrations interaction
python manage.py migrate interaction
```

## 测试覆盖率

运行测试覆盖率检查：

```bash
# 安装 coverage（如果未安装）
pip install coverage

# 运行测试并生成覆盖率报告
coverage run --source='interaction' manage.py test interaction
coverage report
coverage html  # 生成 HTML 报告
```

## 性能测试

对于点赞/收藏功能，可以测试并发性能：

```python
# 使用 Django 的测试客户端进行压力测试
from django.test import Client
import threading

def like_article(article_id):
    client = Client()
    client.post('/interaction/api/like/', {'article_id': article_id})

# 创建多个线程同时点赞
threads = []
for i in range(10):
    t = threading.Thread(target=like_article, args=(1,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
```

