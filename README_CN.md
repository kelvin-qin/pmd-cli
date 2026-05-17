# pmd — Print Markdown

> 终端 Markdown 渲染工具。零依赖。一条命令。

**pmd** 用 ANSI 颜色和 Unicode 框线字符在终端直接渲染 Markdown 文件。不需要浏览器、不需要 GUI、不需要 npm install。只要 Python 3.9+ 和 `pip install pmd-cli`。

<a href="https://pypi.org/project/pmd-cli/"><img src="https://img.shields.io/pypi/v/pmd" alt="PyPI"></a>
<a href="https://pypi.org/project/pmd-cli/"><img src="https://img.shields.io/pypi/pyversions/pmd" alt="Python 3.9+"></a>
<a href="https://pypi.org/project/pmd-cli/"><img src="https://img.shields.io/pypi/l/pmd" alt="License MIT"></a>

## 快速开始

```bash
pip install pmd-cli # 或：pipx install pmd-cli
pmd README.md
cat doc.md | pmd    # 也支持管道输入
```

## 功能

### 标题 — 6 级颜色区分

| 级别 | 样式 | 标记 |
|------|------|------|
| H1 | 白字紫红底 | ■ |
| H2 | 白字蓝底 | ▸ |
| H3 | 黑字青底 | ▸ |
| H4–H6 | 绿 / 黄 / 灰 | ▸ |

无下划线，无 `#` 前缀——只用颜色和符号区分层级。

### 行内格式

- **粗体** `**文字**`
- *斜体* `*文字*`
- ***粗斜体*** `***文字***`
- ~~删除线~~ `~~文字~~`
- `行内代码` — **粗体绿色**，醒目清晰
- [链接](https://example.com) — 蓝色下划线

### 代码块 — 带框线、语言标签

```
┌ python ──────────────────
│ def hello():
│     print("world")
└──────────────────────────
```

干净的框线包围，顶部显示语言标签。不做语法高亮——只求清晰可读。

### 表格 — 自适应宽度、单元格换行、行内格式

```
┌──────────┬───────┬─────────────────┐
│ 名称     │ 年龄  │ 城市            │
├──────────┼───────┼─────────────────┤
│ Alice    │ 30    │ 北京            │
│ Bob      │ 25    │ 上海            │
└──────────┴───────┴─────────────────┘
```

- Unicode 框线字符
- 列宽自适应内容——**默认紧凑布局**
- 长文本在列内自动换行
- 单元格内的 `` `代码` ``、`**粗体**` 等格式正确渲染

### 任务列表

```
  ● 已完成任务
  ○ 待办任务
```

GFM 风格 `- [x]` / `- [ ]` 渲染为绿色实心圆 / 灰色空心圆。可与普通列表项混用。

### 引用块

```
▎ 青色竖线 + 灰色文字
▎ 简洁紧凑
```

### 中英文混排 / Emoji 支持

中文、日文、韩文字符按正确的 2 列显示宽度计算。表格对齐和文本换行在混合语言文档中正常工作。

## 为什么选 pmd？

| 工具 | 语言 | 依赖 |
|------|------|------|
| **pmd** | Python 3 | **零** |
| `glow` | Go | 需要 Go 工具链或预编译二进制 |
| `rich-cli` | Python | `rich` + 10+ 传递依赖 |
| `mdcat` | Rust | 需要 Rust 或预编译二进制 |
| `mdr` | Ruby | 需要 Ruby + `gem install` |

pmd 是最轻量的选择。当你需要在服务器、容器、CI 环境或离线机器上查看 Markdown 时，装编译器或大型包往往不现实——pmd 只需要 Python 3。

## 和 `less` / `cat` 的区别

用 `cat` 或 `less` 看 Markdown 看到的是原始源码：

```
# 标题                   ← 像注释
**粗体** *斜体*          ← 满眼格式符号
| 表格 | 列 |            ← 没对齐看不懂
```

pmd 显示的是**渲染后**的文档——本来该有的样子。

## 安装

```bash
pip install pmd-cli          # 系统级
pip install --user pmd-cli   # 仅当前用户
pipx install pmd-cli         # 隔离环境（推荐）
```

需要 Python 3.9 或以上。无其他依赖。

## 用法

```bash
# 文件
pmd README.md

# 管道输入
curl -s https://example.com/doc.md | pmd

# 剪贴板 (macOS)
pbpaste | pmd

# 剪贴板 (Linux)
xclip -o | pmd
```

## 项目结构

```
src/pmd/
  __init__.py      # 版本号
  __main__.py      # 解析器 + 渲染器（约 850 行）
pyproject.toml     # pip 元数据
```

核心代码单文件——方便内嵌、fork 或集成到其他项目。

## 许可证

MIT
