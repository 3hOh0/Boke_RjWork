# 点赞/收藏功能测试用例

## 快速开始

### 1. 生成测试数据

```bash
# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 生成默认测试数据（10篇文章，5个用户，30个点赞，8个收藏夹）
python manage.py create_interaction_testdata

# 自定义数量
python manage.py create_interaction_testdata --articles 20 --users 8 --likes 50 --folders 15
```

### 2. 启动开发服务器

```bash
python manage.py runserver
```

### 3. 访问测试页面

- **首页**: http://127.0.0.1:8000/
- **文章详情页**: http://127.0.0.1:8000/article/1/ （替换1为任意文章ID）
- **收藏夹管理**: http://127.0.0.1:8000/interaction/dashboard/
- **排行榜**: http://127.0.0.1:8000/interaction/leaderboard/
- **公开收藏夹发现**: http://127.0.0.1:8000/interaction/public/

---

## 测试用例列表

### 一、点赞功能测试

#### TC-001: 匿名用户点赞
**前置条件**: 未登录状态  
**测试步骤**:
1. 访问任意文章详情页
2. 点击"Like"按钮
3. 观察点赞数是否增加
4. 再次点击"Like"按钮
5. 观察点赞数是否减少（取消点赞）

**预期结果**:
- ✅ 匿名用户可以点赞
- ✅ 点赞数实时更新
- ✅ 可以取消点赞

#### TC-002: 登录用户点赞
**前置条件**: 已登录（用户名: testuser1，密码: test123456）  
**测试步骤**:
1. 登录系统
2. 访问文章详情页
3. 点击"Like"按钮
4. 刷新页面，确认点赞状态保持

**预期结果**:
- ✅ 登录用户可以点赞
- ✅ 点赞状态持久化
- ✅ 同一用户不能重复点赞同一文章

#### TC-003: 点赞数统计
**测试步骤**:
1. 访问多篇文章
2. 观察每篇文章的点赞数
3. 访问排行榜页面
4. 验证排行榜按点赞数排序

**预期结果**:
- ✅ 点赞数正确显示
- ✅ 排行榜排序正确

---

### 二、收藏功能测试

#### TC-004: 快速收藏（匿名用户）
**前置条件**: 未登录状态  
**测试步骤**:
1. 访问文章详情页
2. 点击"⭐ Save"按钮
3. 在弹出的模态框中输入收藏夹名称
4. 点击"保存"
5. 验证文章已保存

**预期结果**:
- ✅ 匿名用户可以创建收藏夹
- ✅ 文章成功保存到收藏夹

#### TC-005: 快速收藏（登录用户）
**前置条件**: 已登录  
**测试步骤**:
1. 登录系统
2. 访问文章详情页
3. 点击"⭐ Save"按钮
4. 选择已有收藏夹或创建新收藏夹
5. 保存文章

**预期结果**:
- ✅ 可以选择已有收藏夹
- ✅ 可以创建新收藏夹
- ✅ 文章成功保存

#### TC-006: 收藏夹管理
**前置条件**: 已登录  
**测试步骤**:
1. 访问收藏夹Dashboard: http://127.0.0.1:8000/interaction/dashboard/
2. 创建新收藏夹
3. 编辑收藏夹名称和描述
4. 删除收藏夹
5. 查看收藏夹中的文章列表

**预期结果**:
- ✅ 可以创建收藏夹
- ✅ 可以编辑收藏夹
- ✅ 可以删除收藏夹
- ✅ 可以查看收藏夹内容

#### TC-007: 重复收藏控制
**前置条件**: 已登录，收藏夹设置为"不允许重复"  
**测试步骤**:
1. 将文章A添加到收藏夹F（allow_duplicates=False）
2. 再次尝试将文章A添加到收藏夹F
3. 观察系统响应

**预期结果**:
- ✅ 第二次添加失败
- ✅ 返回错误提示（400状态码）

#### TC-008: 允许重复收藏
**前置条件**: 已登录，收藏夹设置为"允许重复"  
**测试步骤**:
1. 将文章A添加到收藏夹F（allow_duplicates=True）
2. 再次将文章A添加到收藏夹F
3. 查看收藏夹内容

**预期结果**:
- ✅ 可以重复添加同一文章
- ✅ 收藏夹中显示多条记录

---

### 三、分享功能测试

#### TC-009: 公开收藏夹分享
**前置条件**: 已登录，有公开收藏夹  
**测试步骤**:
1. 在Dashboard中将收藏夹设置为"公开"
2. 复制分享链接
3. 在无痕浏览器中打开分享链接
4. 验证可以查看收藏夹内容

**预期结果**:
- ✅ 公开收藏夹可以访问
- ✅ 分享链接有效
- ✅ 未登录用户可以查看

#### TC-010: 私有收藏夹保护
**前置条件**: 已登录，有私有收藏夹  
**测试步骤**:
1. 在Dashboard中将收藏夹设置为"私有"
2. 复制分享链接
3. 在无痕浏览器中打开分享链接
4. 观察系统响应

**预期结果**:
- ✅ 私有收藏夹无法通过分享链接访问
- ✅ 返回404错误

#### TC-011: 分享链接重新生成
**前置条件**: 已登录  
**测试步骤**:
1. 获取收藏夹的分享链接
2. 在Dashboard中重新生成分享令牌
3. 验证旧链接失效
4. 验证新链接有效

**预期结果**:
- ✅ 可以重新生成分享令牌
- ✅ 旧链接失效
- ✅ 新链接有效

---

### 四、排行榜功能测试

#### TC-012: 排行榜基础功能
**测试步骤**:
1. 访问排行榜页面: http://127.0.0.1:8000/interaction/leaderboard/
2. 查看文章列表
3. 验证按点赞数排序

**预期结果**:
- ✅ 显示文章列表
- ✅ 按点赞数从高到低排序
- ✅ 显示文章标题、作者、点赞数

#### TC-013: 时间筛选功能
**测试步骤**:
1. 访问排行榜页面
2. 选择"最近24小时"筛选
3. 选择"最近7天"筛选
4. 选择"最近30天"筛选
5. 选择"全部时间"筛选
6. 验证结果变化

**预期结果**:
- ✅ 时间筛选正常工作
- ✅ 不同时间段显示不同结果
- ✅ 筛选结果按点赞数排序

#### TC-014: 排行榜API
**测试步骤**:
```bash
# 获取排行榜
curl http://127.0.0.1:8000/interaction/api/leaderboard/

# 按时间筛选
curl "http://127.0.0.1:8000/interaction/api/leaderboard/?since=2024-12-01T00:00:00Z"
```

**预期结果**:
- ✅ 返回JSON格式数据
- ✅ 包含文章列表和点赞数
- ✅ 时间筛选参数生效

---

### 五、公开收藏夹发现

#### TC-015: 浏览公开收藏夹
**测试步骤**:
1. 访问公开收藏夹页面: http://127.0.0.1:8000/interaction/public/
2. 查看公开收藏夹列表
3. 点击"查看"按钮
4. 验证可以访问收藏夹内容

**预期结果**:
- ✅ 显示所有公开收藏夹
- ✅ 显示收藏夹名称、描述、所有者
- ✅ 可以访问收藏夹详情

#### TC-016: 公开收藏夹筛选
**测试步骤**:
1. 创建多个公开和私有收藏夹
2. 访问公开收藏夹页面
3. 验证只显示公开收藏夹

**预期结果**:
- ✅ 只显示公开收藏夹
- ✅ 私有收藏夹不显示

---

### 六、API接口测试

#### TC-017: 点赞API
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

**预期结果**:
- ✅ 返回JSON响应
- ✅ 包含liked状态和like_count

#### TC-018: 收藏夹API
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

**预期结果**:
- ✅ API正常工作
- ✅ 返回正确的JSON数据
- ✅ 错误处理正确

---

## 测试数据说明

### 默认生成的测试数据

运行 `python manage.py create_interaction_testdata` 后会生成：

- **用户**: 5个测试用户（testuser1 ~ testuser5，密码: test123456）
- **文章**: 10篇测试文章
- **点赞**: 30个点赞记录（分布在多篇文章上）
- **收藏夹**: 8个收藏夹（每个用户1-3个）
- **收藏项**: 每个收藏夹包含2-5篇文章
- **匿名数据**: 3个匿名用户的点赞和收藏

### 测试账号

| 用户名 | 密码 | 说明 |
|--------|------|------|
| testuser1 | test123456 | 测试用户1 |
| testuser2 | test123456 | 测试用户2 |
| testuser3 | test123456 | 测试用户3 |
| testuser4 | test123456 | 测试用户4 |
| testuser5 | test123456 | 测试用户5 |

### 数据特点

- 文章创建时间分布在最近30天内
- 点赞数不均匀分布，便于测试排行榜
- 部分收藏夹设置为公开，部分为私有
- 部分收藏夹允许重复，部分不允许
- 包含匿名用户的互动数据

---

## 清理测试数据

如果需要清理测试数据，可以：

```bash
# 进入Django shell
python manage.py shell

# 执行清理命令
from interaction.models import Like, FavoriteFolder, FavoriteItem, InteractionActor
from blog.models import Article
from django.contrib.auth import get_user_model

# 删除所有互动数据
Like.objects.all().delete()
FavoriteItem.objects.all().delete()
FavoriteFolder.objects.all().delete()
InteractionActor.objects.filter(user__username__startswith='testuser').delete()

# 删除测试用户和文章（可选）
User = get_user_model()
User.objects.filter(username__startswith='testuser').delete()
Article.objects.filter(title__contains='第').delete()
```

---

## 常见问题

### Q1: 为什么看不到点赞按钮？
**A**: 确保文章详情页模板已包含互动功能的JavaScript和CSS。

### Q2: 匿名用户收藏后在哪里查看？
**A**: 匿名用户的收藏数据存储在浏览器中，可以通过分享链接访问公开收藏夹。

### Q3: 排行榜为什么是空的？
**A**: 确保有文章被点赞，且文章状态为已发布（status='p'）。

### Q4: 如何测试分享功能？
**A**: 
1. 创建公开收藏夹
2. 复制分享链接
3. 在无痕浏览器中打开链接
4. 验证可以访问

---

## 性能测试建议

对于大量数据的性能测试：

```bash
# 生成大量测试数据
python manage.py create_interaction_testdata --articles 100 --users 20 --likes 500 --folders 50
```

然后测试：
- 排行榜页面加载速度
- 大量点赞时的响应时间
- 收藏夹列表加载速度

