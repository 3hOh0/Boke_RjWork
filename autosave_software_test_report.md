# 自动保存功能软件测试报告

## 一、功能描述
实现文章编辑时自动保存草稿，支持多版本保存与恢复，防止内容丢失。

## 二、测试环境
- 操作系统：Windows 10/11
- Python环境：3.x（虚拟环境 .venv）
- Django版本：5.x
- 数据库：MySQL（测试用 test_djangoblog）
- 相关依赖：见 requirements.txt

## 三、测试用例设计

### 用例1：自动保存草稿并查询版本
- 【前置条件】已登录用户，存在可编辑文章
- 【操作步骤】
  1. 进入文章编辑页，输入内容
  2. 触发自动保存（如停留5秒或手动触发）
  3. 查询草稿版本列表
- 【预期结果】
  - 自动保存接口返回 200，返回草稿ID
  - 版本列表接口返回 200，包含刚保存的草稿

### 用例2：通过API自动保存与恢复
- 【前置条件】已登录用户
- 【操作步骤】
  1. 通过API创建新草稿（/api/autosave/draft/）
  2. 连续多次自动保存（超过5次，测试版本保留上限）
  3. 查询版本列表，检查数量
  4. 恢复最新版本
- 【预期结果】
  - 每次保存接口返回 200
  - 版本数不超过10条（或实现上限）
  - 恢复接口返回 200 且 success

## 四、测试结果

测试命令：
```
.venv\Scripts\python manage.py test autosave --verbosity=2
```

测试输出摘要：
```
test_autosave_app_create_and_list (autosave.tests.AutosaveAPITests) ... ok
test_blog_api_autosave_and_restore (autosave.tests.AutosaveAPITests) ... ok
----------------------------------------------------------------------
Ran 2 tests in 1.750s

OK
```

- 所有用例均通过，接口返回与预期一致。
- 数据库草稿记录与版本数正确。
- 恢复功能可用。

## 五、结论
自动保存功能经单元测试和集成测试验证，主要接口和核心流程均符合设计要求，未发现功能性缺陷。

---

> 详细测试代码见 autosave_test_bundle/autosave_tests.py，原始测试输出见 autosave_test_bundle/test_results_autosave.txt。
