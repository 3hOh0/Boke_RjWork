# 提交分支与创建 PR（PowerShell / Windows）

以下命令在项目根目录运行：

```powershell
# 新建分支
git checkout -b feature/autosave

# 检查改动并提交
git status
git add .
git commit -m "feat(autosave): add autosave app, draft model, APIs, admin UI and tests"

# 推送并创建远程分支
git push -u origin feature/autosave

# 使用 GitHub CLI 创建 PR（可选）
gh pr create --title "feat: Add article autosave (drafts, versions, restore)" --body-file pr_body.md --base main --head feature/autosave
```

如果没有 `gh`，在浏览器打开：

```
https://github.com/<OWNER>/<REPO>/compare/main...feature/autosave?expand=1
```

将 `<OWNER>/<REPO>` 替换为你的仓库路径（可通过 `git remote get-url origin` 查看）。在页面填写标题与正文（可直接复制 `pr_body.md` 内容），然后创建 PR。
