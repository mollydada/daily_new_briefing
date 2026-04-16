#!/usr/bin/env python3
"""
Daily News Briefing Generator — runs in GitHub Actions at 7 AM CST.
依赖：pip install anthropic duckduckgo-search
需要环境变量：ANTHROPIC_API_KEY
"""

import anthropic
import datetime
import json
import os
import re
import sys
import time
from pathlib import Path
from zoneinfo import ZoneInfo

# ─── 基础配置 ─────────────────────────────────────────────────────────────
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 16000
MAX_TOOL_ITERATIONS = 40
REPO_ROOT = Path(__file__).parent.parent
CST = ZoneInfo("Asia/Shanghai")

now = datetime.datetime.now(tz=CST)
TODAY = now.strftime("%Y-%m-%d")
TODAY_WEEKDAY = ["一", "二", "三", "四", "五", "六", "日"][now.weekday()]
TODAY_DISPLAY = f"{now.strftime('%Y年%m月%d日')} 星期{TODAY_WEEKDAY}"

# ─── 搜索工具 ─────────────────────────────────────────────────────────────
def search_web(query: str, max_results: int = 10) -> str:
    from duckduckgo_search import DDGS
    for attempt in range(3):
        try:
            with DDGS() as ddgs:
                raw = list(ddgs.text(query, max_results=max_results, safesearch="off"))
            results = [
                {"title": r.get("title", ""), "url": r.get("href", ""), "body": r.get("body", "")[:600]}
                for r in raw
            ]
            return json.dumps(results, ensure_ascii=False)
        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                return json.dumps({"error": str(e)})

TOOLS = [
    {
        "name": "web_search",
        "description": "搜索互联网获取最新新闻和具体文章 URL。可多次调用，每次聚焦一个主题。",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询字符串，建议用英文或中英混合以获得更广泛结果"
                },
                "max_results": {
                    "type": "integer",
                    "description": "返回结果数量，默认 10",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    }
]

# ─── 系统提示 ─────────────────────────────────────────────────────────────
SYSTEM = f"""你是一位专业新闻编辑，今天的日期是 {TODAY}（北京时间 {TODAY_DISPLAY}）。
你的任务是：通过多次搜索收集当日新闻，然后生成一份完整的新闻简报，包含 HTML 和 Markdown 两个版本。

## 信源规则
- 优先信源：Reuters, Associated Press, BBC News, The Economist, NYTimes, WSJ, NPR, The Guardian, Al Jazeera, SCMP, The Times of India, Nikkei Asia, 财新, 端传媒, Bloomberg, Sinocism, MERICS
- 不在以上名单的媒体，其信息原则上不采用，除非以上信源均未涵盖，而他们输出了相当强劲的报道。

## 内容板块（按顺序）
1. 当日头条新闻（3-6 条，全球范围内最需要关注的）
2. 当日市场总览（标普500，BTC，TAIEX，CSI 300，DXY，美债收益率——面向一般理财者，通俗解读）
3. 深度报道（近几日最热门或最相关深度调查，优先 NYTimes 和 WSJ）
4. 东亚/中国聚焦
5. 全球科技行业聚焦
6. 国际政治聚焦
7. 社交媒体热议（3-6 条，当天或前一天最热话题）

## 采信与编辑规则
1. 所有媒体均纳入，不限语言，简报输出全部为简体中文
2. 存在媒体立场分歧时，直接呈现不同立场并一句话总结分歧
3. 每条新闻必须附具体文章 URL（非媒体首页、非栏目页）
4. 同一新闻多媒体报道时：立场趋同选一条（优先 NYT/WSJ，次选免费 URL）；立场不同分别呈现
5. 禁止使用任何媒体首页或栏目页作为链接

## HTML 文件规格
- 深色头部 #1a1a2e，白色卡片，各板块彩色左边框：
  头版 #c0392b | 市场 #27ae60 | 深度 #16a085 | 东亚 #e67e22 | 科技 #2980b9 | 国政 #8e44ad | 社交 #e84393
- 每条新闻卡片包含：来源标签、中文标题、2-4 句摘要、具体文章链接

## Markdown 文件规格（Obsidian 兼容）
- 文件必须以 YAML frontmatter 开头，第一行就是 ---，frontmatter 之前不得有任何内容
- frontmatter 包含：date: {TODAY}，category: ["news"]
- ## 分隔各板块，板块标题含 emoji
- 每条新闻 ### 标题 + 摘要 + 引用行（> 来源：[媒体名](URL)）
- 板块间用 --- 分隔
- 不在 Markdown 文件里放任何 HTML file:// 链接

## 搜索策略
请依次搜索以下主题（可自行增减查询）：
1. "top world news today {TODAY}" site:reuters.com OR site:bbc.com OR site:apnews.com
2. "breaking news {TODAY}" Reuters AP BBC
3. "stock market S&P 500 {TODAY}" Bloomberg
4. "Bitcoin crypto market {TODAY}"
5. "China East Asia news {TODAY}" Nikkei SCMP
6. "AI tech news {TODAY}" Bloomberg WSJ
7. "international politics {TODAY}" NYT Guardian
8. "social media trending {TODAY}"
9. (按需追加具体主题的搜索)

## 输出格式
完成所有搜索后，在回复最后按以下格式输出两个文件的完整内容：

<<<HTML_START>>>
[完整 HTML 文件内容，不要截断]
<<<HTML_END>>>

<<<MD_START>>>
[完整 Markdown 文件内容，不要截断]
<<<MD_END>>>
"""

# ─── 主流程 ───────────────────────────────────────────────────────────────
def main():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    messages = [
        {
            "role": "user",
            "content": (
                f"请搜索 {TODAY} 的最新新闻（至少执行 8 次不同主题的搜索），"
                "然后生成完整的每日新闻简报。最后输出完整的 HTML 和 Markdown 两个版本。"
            ),
        }
    ]

    final_text = ""
    print(f"[{TODAY}] Starting briefing generation…", flush=True)

    for iteration in range(MAX_TOOL_ITERATIONS):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "end_turn":
            for block in resp.content:
                if hasattr(block, "text"):
                    final_text += block.text
            print(f"  ✓ Model finished after {iteration + 1} iterations", flush=True)
            break

        elif resp.stop_reason == "tool_use":
            tool_results = []
            for block in resp.content:
                if getattr(block, "type", "") == "tool_use" and block.name == "web_search":
                    query = block.input.get("query", "")
                    max_r = block.input.get("max_results", 10)
                    print(f"  → Search: {query}", flush=True)
                    result = search_web(query, max_r)
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": block.id, "content": result}
                    )
            if tool_results:
                messages.append({"role": "user", "content": tool_results})
            else:
                print("  ⚠ tool_use but no tool calls found, stopping", file=sys.stderr)
                break
        else:
            print(f"  ⚠ Unexpected stop_reason: {resp.stop_reason}", file=sys.stderr)
            break
    else:
        print("⚠ Reached max iterations", file=sys.stderr)

    # ─── 解析输出 ─────────────────────────────────────────────────────────
    html_m = re.search(r"<<<HTML_START>>>(.*?)<<<HTML_END>>>", final_text, re.DOTALL)
    md_m = re.search(r"<<<MD_START>>>(.*?)<<<MD_END>>>", final_text, re.DOTALL)

    if not html_m or not md_m:
        print("ERROR: Could not parse file content from model output", file=sys.stderr)
        print("--- Raw output (first 2000 chars) ---", file=sys.stderr)
        print(final_text[:2000], file=sys.stderr)
        sys.exit(1)

    html_content = html_m.group(1).strip()
    md_content = md_m.group(1).strip()

    html_path = REPO_ROOT / f"news_briefing_{TODAY}.html"
    md_path = REPO_ROOT / f"news_briefing_{TODAY}.md"

    html_path.write_text(html_content, encoding="utf-8")
    md_path.write_text(md_content, encoding="utf-8")

    print(f"  ✓ Saved {html_path.name}")
    print(f"  ✓ Saved {md_path.name}")


if __name__ == "__main__":
    main()
