请按以下步骤生成今日新闻简报：

**第一步：** 用 bash 获取今天日期并记为 TODAY：
```bash
date +%Y-%m-%d
```

**第二步：** 严格按照以下规格，通过 WebSearch 搜索当日新闻（至少 8 次不同主题的搜索），然后生成完整简报。

---

## 信源规则
- 优先信源：Reuters, Associated Press, BBC News, The Economist, NYTimes, WSJ, NPR, The Guardian, Al Jazeera, SCMP, The Times of India, Nikkei Asia, 财新, 端传媒, Bloomberg, Sinocism, MERICS
- 不在以上名单的媒体，其信息原则上不采用，除非以上信源均未涵盖且他们输出了相当强劲的报道。

## 内容板块（按顺序）
1. 当日头条新闻（3-6 条，全球范围内最需要关注的）
2. 当日市场总览（标普500，BTC，TAIEX，CSI 300，DXY，美债收益率——面向一般理财者，通俗解读）
3. 深度报道（近几日最热门或最相关深度调查，优先 NYTimes 和 WSJ）
4. 东亚/中国聚焦
5. 全球科技行业聚焦
6. 国际政治聚焦
7. 社交媒体热议（3-6 条）

## 采信与编辑规则
1. 所有媒体均纳入，不限语言，简报输出全部为简体中文
2. 存在媒体立场分歧时，直接呈现不同立场并一句话总结分歧
3. 每条新闻必须附具体文章 URL（非媒体首页、非栏目页）
4. 同一新闻多媒体报道：立场趋同选一条（优先 NYT/WSJ，次选免费 URL）；立场不同分别呈现
5. **禁止使用任何媒体首页或栏目页作为链接**

## HTML 文件规格
样式：深色头部 #1a1a2e，白色卡片，各板块彩色左边框：
- 头版 #c0392b | 市场 #27ae60 | 深度 #16a085 | 东亚 #e67e22 | 科技 #2980b9 | 国政 #8e44ad | 社交 #e84393
- 每条新闻卡片：来源标签、中文标题、2-4 句摘要、具体文章链接

## Markdown 文件规格（Obsidian 兼容）
- 文件必须以 YAML frontmatter 开头，第一行就是 ---，frontmatter 之前不得有任何内容
- frontmatter 包含：date: [TODAY]，category: ["news"]
- ## 分隔各板块，板块标题含 emoji
- 每条新闻 ### 标题 + 摘要 + 引用行（`> 来源：[媒体名](URL)`）
- 板块间用 --- 分隔
- 不在 Markdown 文件里放任何 HTML file:// 链接

## 搜索顺序建议
1. "top world news today [TODAY]" Reuters AP BBC
2. "breaking news [TODAY]" international
3. "stock market S&P 500 BTC [TODAY]" Bloomberg
4. "China East Asia news [TODAY]" Nikkei SCMP
5. "AI technology news [TODAY]" Bloomberg WSJ
6. "international politics [TODAY]" NYT Guardian
7. "social media trending [TODAY]"
8. （按当日热点追加具体搜索）

## 输出路径（2026-04 更新到 6 Knowledge/News/）
用 Write 工具直接写入以下路径（替换 [TODAY] 为实际日期）：
- HTML：`/Users/elena/Library/Mobile Documents/iCloud~md~obsidian/Documents/Molly Z/6 Knowledge/News/news_briefing_[TODAY].html`
- Markdown：`/Users/elena/Library/Mobile Documents/iCloud~md~obsidian/Documents/Molly Z/6 Knowledge/News/news_briefing_[TODAY].md`

## Git 推送（每次生成完毕后自动执行）
```bash
cd "/Users/elena/Library/Mobile Documents/iCloud~md~obsidian/Documents/Molly Z/6 Knowledge/News" && \
  git add "news_briefing_[TODAY].html" "news_briefing_[TODAY].md" && \
  git commit -m "briefing: [TODAY]" && \
  git push origin main
```
git 凭证通过本地 `.git-credentials`（gitignored, chmod 600）由 credential.helper store 自动处理，无需手动粘贴 token。
