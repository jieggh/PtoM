# PtoM
转换PDF并自动生成Markdown文件
这是一个集成的脚本，可以：

1. **PDF转Markdown**：自动提取PDF中的文本和表格，转换为Markdown格式
2. **自动优化**：转换后自动优化文档格式，包括：
   - 移除页面标记和分隔符
   - 优化代码块使用
   - 修复标题层级
   - 格式化链接
   - 提升整体可读性

## 安装依赖

脚本会自动检测并安装所需依赖，首次运行时会自动安装 `pdfplumber` 库。

**推荐安装（支持图片提取）：**

```bash
pip install pdfplumber PyMuPDF
```

**最小安装（仅文本提取）：**

```bash
pip install pdfplumber
```

> **注意**：如果未安装 `PyMuPDF`，图片提取功能可能受限。建议安装以获得更好的图片提取效果。
