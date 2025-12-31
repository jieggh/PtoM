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
>
> @echo off
chcp 65001 >nul
echo ========================================
echo PDF转Markdown并优化脚本 - 使用示例
echo ========================================
echo.

REM 示例1: 转换PDF并自动生成Markdown文件
echo 示例1: 转换PDF并自动生成Markdown文件
echo python pdf_to_markdown_optimizer.py "Test.pdf"
echo.
echo 这将生成: Test.md
echo.

REM 示例2: 转换PDF并指定输出文件名
echo 示例2: 转换PDF并指定输出文件名
echo python pdf_to_markdown_optimizer.py "document.pdf" "output.md"
echo.

echo ========================================
echo 使用方法:
echo   python pdf_to_markdown_optimizer.py ^<PDF文件^> [输出文件]
echo.
echo 如果不指定输出文件，将自动生成（原文件名.md）
echo ========================================
echo.
pause

