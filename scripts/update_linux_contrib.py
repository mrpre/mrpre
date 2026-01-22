#!/usr/bin/env python3
"""
查询用户在 torvalds/linux 仓库的 commit 贡献，更新 README.md
"""

import requests
import re
from datetime import datetime

# 配置
GITHUB_USERNAME = "mrpre"
AUTHOR_EMAILS = [
    "mrpre@163.com",
    "jiayuan.chen@shopee.com",
    "jiayuan.chen@linux.dev",
]
REPO = "torvalds/linux"
DISPLAY_RECENT = 10  # 展示最近多少条

# README 中的标记，脚本会替换这两个标记之间的内容
START_MARKER = "<!-- LINUX_CONTRIB_START -->"
END_MARKER = "<!-- LINUX_CONTRIB_END -->"


def fetch_commits_by_author(author: str, per_page: int = 100) -> list:
    """通过 author 参数查询 commit（可以是用户名或邮箱）"""
    commits = []
    page = 1
    
    while True:
        url = f"https://api.github.com/repos/{REPO}/commits"
        params = {
            "author": author,
            "per_page": per_page,
            "page": page,
        }
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        resp = requests.get(url, params=params, headers=headers)
        if resp.status_code != 200:
            print(f"API error for author={author}: {resp.status_code}")
            break
        
        data = resp.json()
        if not data:
            break
        
        commits.extend(data)
        page += 1
        
        # GitHub API 对未认证请求有频率限制，最多取几页就够了
        if page > 10:
            break
    
    return commits


def fetch_all_commits() -> list:
    """查询所有邮箱的 commit 并去重"""
    all_commits = {}
    
    # 先用用户名查
    print(f"Fetching commits by username: {GITHUB_USERNAME}")
    for commit in fetch_commits_by_author(GITHUB_USERNAME):
        sha = commit["sha"]
        all_commits[sha] = commit
    
    # 再用每个邮箱查
    for email in AUTHOR_EMAILS:
        print(f"Fetching commits by email: {email}")
        for commit in fetch_commits_by_author(email):
            sha = commit["sha"]
            if sha not in all_commits:
                all_commits[sha] = commit
    
    # 按时间排序（新的在前）
    commits_list = list(all_commits.values())
    commits_list.sort(
        key=lambda c: c["commit"]["author"]["date"],
        reverse=True
    )
    
    return commits_list


def format_commit(commit: dict) -> str:
    """格式化单条 commit 为 markdown"""
    sha = commit["sha"][:12]
    message = commit["commit"]["message"].split("\n")[0]  # 只取第一行
    url = commit["html_url"]
    date_str = commit["commit"]["author"]["date"][:10]  # YYYY-MM-DD
    
    # 截断过长的 message
    if len(message) > 80:
        message = message[:77] + "..."
    
    return f"- [`{sha}`]({url}) {message} ({date_str})"


def generate_contrib_section(commits: list) -> str:
    """生成贡献统计的 markdown 内容"""
    total = len(commits)
    
    lines = [
        f"### 🐧 Linux Kernel Contributions",
        f"",
        f"Total commits to [{REPO}](https://github.com/{REPO}): **{total}**",
        f"",
    ]
    
    if commits:
        lines.append(f"**Recent {min(DISPLAY_RECENT, total)} commits:**")
        lines.append("")
        for commit in commits[:DISPLAY_RECENT]:
            lines.append(format_commit(commit))
        lines.append("")
    
    lines.append(f"<sub>Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC</sub>")
    
    return "\n".join(lines)


def update_readme(contrib_section: str):
    """更新 README.md 中的贡献部分"""
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        # 如果 README 不存在，创建一个基础的
        content = f"# Hi, I'm {GITHUB_USERNAME}\n\n{START_MARKER}\n{END_MARKER}\n"
    
    # 检查是否有标记
    if START_MARKER not in content:
        # 没有标记，在文件末尾添加
        content = content.rstrip() + f"\n\n{START_MARKER}\n{END_MARKER}\n"
    
    # 替换标记之间的内容
    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL
    )
    new_content = pattern.sub(
        f"{START_MARKER}\n{contrib_section}\n{END_MARKER}",
        content
    )
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print("README.md updated successfully")


def main():
    print("Fetching Linux kernel contributions...")
    commits = fetch_all_commits()
    print(f"Found {len(commits)} commits in total")
    
    contrib_section = generate_contrib_section(commits)
    update_readme(contrib_section)


if __name__ == "__main__":
    main()
