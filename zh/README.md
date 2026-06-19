# Word-Lerning 中文版

大模型辅助英语单词记忆 + 翻译练习系统。面向**学习英文的中国用户**。

通过 AI 生成融合 CET-6/考研目标词汇的地道英文文章，在阅读中自然习得单词的冷门含义与地道搭配。

---

## 快速开始

### 1. 一键安装

```bash
# Windows
install.bat

# macOS / Linux
bash install.sh
```

Skills 会被复制到 `~/.claude/skills/`，任意目录下都能使用。

### 2. 初始化词表

在 Claude Code 中输入：

```
/init-wordlist
```

提供你的考纲词表文件（如 CET6.txt），Skill 自动识别格式、配置正则式并自我测试，最后汇报配置结果。

### 3. 词卡分类

运行 `/init-wordlist` 后，手动启动本地服务器：

```bash
# Windows
serve.bat

# macOS / Linux
bash serve.sh
```

然后浏览器打开 `http://localhost:8080/tools/word-triage/`：
- 加载词表文件
- 单击卡片翻转查看释义
- `←` 不熟悉 / `→` 熟悉 / `空格` 翻转 / `↓` 跳过
- 导出 `familiar.txt` 和 `unfamiliar.txt` 放入 `data/`

### 4. 生成记忆文章

```
/generate-article
```

AI 自动完成：
1. 从不熟悉词表加权抽取 200 词（低频优先）
2. 搜索 The Economist / Guardian / BBC 等来源的地道文章
3. **语义查重**（关键词相似度 + LLM 判断）
4. 改写文章融入目标词（优先冷门含义）
5. 附带长难句翻译 + 全文翻译 + 词汇训练表 + 阅读理解题
6. 保存文章并更新计数器

---

## 目录结构

```
zh/
├── tools/
│   ├── word-triage/          # 网页词卡工具
│   │   ├── index.html        # 🔒 Core code (Skill 禁止修改)
│   │   ├── style.css
│   │   ├── app.js            # 🔒 Core code
│   │   └── regex-config.txt  # 🔧 正则配置 (Skill 唯一可改)
│   ├── extract-words.py      # 权重随机提取
│   ├── count-words.py        # 计数器 + 历史记录
│   └── check-similarity.py   # 语义查重
├── .claude/skills/
│   ├── init-wordlist.md      # 词表初始化 Skill
│   └── generate-article.md   # 文章生成 Skill
├── data/                     # 词表 + 计数器 + 历史
├── articles/                 # 生成的文章
├── install.bat / install.sh  # 一键安装
├── serve.bat / serve.sh      # 本地服务器
└── README.md
```

## Troubleshooting

### UnicodeEncodeError（Windows）

```bash
PYTHONIOENCODING=utf-8 python tools/extract-words.py ...
# 或
chcp 65001
```

所有脚本内部已调用 `sys.stdout.reconfigure(encoding='utf-8')`，直接运行通常无问题。仅 `python -c "..."` 内联测试需要加环境变量。
