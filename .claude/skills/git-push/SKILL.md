---
name: git-push
description: 一键Git提交推送 + 远程仓库描述同步。当你需要提交推送代码时调用。
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*), Bash(git push:*)
---

执行以下步骤：

## 1. 提交推送
1. `git status` — 展示当前改动
2. 如果用户没有附带提交信息，根据变更内容自动生成规范的 commit message（feat/fix/refactor 等前缀）
3. 确认 `.env` `*.db` `data/chroma_db/` `data/models/` `logs/` 不在暂存区
4. 执行：
   ```bash
   git add .
   git commit -m "<提交信息>"
   git push
   ```
5. 报告结果

## 2. 同步仓库描述（推送成功后）
推送成功后，自动用 `GITHUB_TOKEN`（从 `.env` 读取）更新远端仓库的 description，内容根据 PROJECT_SUMMARY.md 的项目定位自动生成。

```python
import requests, urllib3, os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")
if TOKEN:
    urllib3.disable_warnings()
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}
    new_desc = "<根据项目定位生成的中文描述>"
    requests.patch("https://api.github.com/repos/91TangZhu/agent_customer",
        headers=headers, json={"description": new_desc}, verify=False)
```

## 约束
- 禁止 `git push -f`
- 推送前确保 `.env` `*.db` 不在暂存区
- 如果 push 被拒绝，提示用户先 `git pull`
- GITHUB_TOKEN 仅用于更新仓库描述等元信息，不涉及代码操作
