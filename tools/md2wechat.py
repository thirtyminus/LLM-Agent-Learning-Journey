#!/usr/bin/env python3
"""
tools/md2wechat.py — Markdown 转微信公众号文章

用法：
  python3 tools/md2wechat.py < input.md > output.html
  python3 tools/md2wechat.py prompts/examples.md -o article.html

依赖：
  pip install markdown pygments
"""

import argparse
import re
import sys

try:
    import markdown
except ImportError:
    print("请先安装依赖：pip install markdown pygments")
    sys.exit(1)


def convert(md_text: str) -> str:
    """
    将 Markdown 转为微信公众号兼容的 HTML。
    输出可直接粘贴到公众号编辑器（需手动上传图片）。
    """
    # 自定义扩展
    extensions = [
        "markdown.extensions.extra",        # 表格、脚注、缩写等
        "markdown.extensions.codehilite",   # 代码高亮
        "markdown.extensions.toc",          # 目录
        "markdown.extensions.fenced_code",  # 围栏代码块
    ]
    extension_configs = {
        "markdown.extensions.codehilite": {
            "css_class": "codehilite",
            "guess_lang": False,
        },
    }

    html = markdown.markdown(
        md_text,
        extensions=extensions,
        extension_configs=extension_configs,
    )

    # --- 公众号适配处理 ---

    # 1. 图片：添加最大宽度和居中（图片需手动上传公众号素材库）
    html = re.sub(
        r'<img (src="[^"]+")',
        r'<img style="max-width:100%;display:block;margin:10px auto;" \1',
        html,
    )

    # 2. 表格：添加边框
    html = re.sub(
        r'<table>',
        r'<table style="border-collapse:collapse;width:100%;margin:10px 0;">',
        html,
    )
    html = re.sub(
        r'<th>',
        r'<th style="border:1px solid #ddd;padding:8px;background:#f5f5f5;">',
        html,
    )
    html = re.sub(
        r'<td>',
        r'<td style="border:1px solid #ddd;padding:8px;">',
        html,
    )

    # 3. 代码块：公众号用背景色方案
    html = re.sub(
        r'<pre><code',
        r'<pre style="background:#f6f8fa;border-radius:4px;padding:12px;overflow-x:auto;font-size:14px;line-height:1.5;"><code',
        html,
    )

    # 4. 引用块
    html = re.sub(
        r'<blockquote>',
        r'<blockquote style="border-left:4px solid #07c160;padding:10px 15px;margin:10px 0;background:#f9f9f9;">',
        html,
    )

    # 5. 标题：保持清晰层次
    for i in range(1, 4):
        html = re.sub(
            rf'<h{i}>',
            rf'<h{i} style="margin:20px 0 10px;">',
            html,
        )

    # 6. 段落间距
    html = re.sub(
        r'<p>',
        r'<p style="margin:8px 0;line-height:1.75;">',
        html,
    )

    # 组装完整页面
    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
/* 代码高亮主题（GitHub 风格） */
.codehilite .c  {{ color:#998;font-style:italic; }}
.codehilite .k  {{ color:#d73a49;font-weight:bold; }}
.codehilite .s  {{ color:#032f62; }}
.codehilite .mi {{ color:#005cc5; }}
.codehilite .nf {{ color:#6f42c1; }}
.codehilite .kn {{ color:#d73a49; }}
</style>
</head>
<body style="font-family:-apple-system,'Microsoft YaHei',sans-serif;padding:0 10px;color:#333;">
{html}
</body>
</html>"""

    return full_html


def main():
    parser = argparse.ArgumentParser(description="Markdown 转微信公众号文章")
    parser.add_argument("input", nargs="?", help="输入 Markdown 文件（默认 stdin）")
    parser.add_argument("-o", "--output", help="输出文件（默认 stdout）")
    args = parser.parse_args()

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            md_text = f.read()
    else:
        md_text = sys.stdin.read()

    html = convert(md_text)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ 已生成：{args.output}")
    else:
        print(html)


if __name__ == "__main__":
    main()
