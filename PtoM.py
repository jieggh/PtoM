#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PtoM - PDF to Markdown Converter
作者: BOOM
功能：
1. 将PDF文件转换为Markdown格式
2. 自动提取PDF中的图片
3. 自动优化Markdown文档（移除页面标记、优化代码块、修复格式等）

使用方法：
    python PtoM.py <PDF文件> [输出文件]
    
如果不指定输出文件，将自动生成（原文件名.md）
"""

import re
import sys
import os


def print_banner():
    """打印Banner"""
    # 使用ASCII字符，确保在Windows终端中正确显示
    banner = """
=================================================================
                                                                 
     ██████╗ ████████╗ ███╗   ███╗                              
    ██╔══██╗╚══██╔══╝ ████╗ ████║                              
    ██████╔╝   ██║    ██╔████╔██║                              
    ██╔═══╝    ██║    ██║╚██╔╝██║                              
    ██║        ██║    ██║ ╚═╝ ██║                              
    ╚═╝        ╚═╝    ╚═╝     ╚═╝                              
                                                                 
              PDF to Markdown Converter                         
                                                                 
                     ----BOOM/小胖                                 
                                                                 
=================================================================
"""
    print(banner)


class PDFToMarkdownConverter:
    """PDF转Markdown转换器"""
    
    def __init__(self, output_dir=None, output_file=None):
        self.output_dir = output_dir
        self.output_file = output_file  # Markdown输出文件路径
        self.images_dir = None
        self.image_counter = 0
        self.check_dependencies()
    
    def check_dependencies(self):
        """检查依赖库"""
        try:
            import pdfplumber
            self.pdfplumber = pdfplumber
        except ImportError:
            print("正在安装pdfplumber库...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfplumber", "-q"])
            import pdfplumber
            self.pdfplumber = pdfplumber
        
        # 检查PyMuPDF（用于更好的图片提取）
        try:
            import fitz
            self.fitz = fitz
            self.has_fitz = True
        except ImportError:
            try:
                import PyMuPDF as fitz
                self.fitz = fitz
                self.has_fitz = True
            except ImportError:
                self.has_fitz = False
                print("提示: 未安装PyMuPDF，图片提取功能可能受限。建议安装: pip install PyMuPDF")
    
    def setup_images_directory(self, pdf_path, output_file=None):
        """设置图片保存目录"""
        if self.output_dir:
            base_dir = self.output_dir
        else:
            # 如果指定了输出文件，使用输出文件所在目录
            if output_file:
                base_dir = os.path.dirname(os.path.abspath(output_file))
                if not base_dir:
                    base_dir = os.path.dirname(os.path.abspath(pdf_path))
            else:
                base_dir = os.path.dirname(os.path.abspath(pdf_path))
        
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        self.images_dir = os.path.join(base_dir, f"{pdf_name}_images")
        
        # 创建图片目录
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
        
        return self.images_dir
    
    def extract_images_with_fitz(self, pdf_doc, page_num, output_file=None):
        """使用PyMuPDF提取图片（使用已打开的文档）"""
        images = []
        if not self.has_fitz or not pdf_doc:
            return images
        
        try:
            page = pdf_doc[page_num - 1]  # fitz使用0-based索引
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = pdf_doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # 保存图片
                    self.image_counter += 1
                    image_filename = f"page_{page_num}_img_{img_index + 1}.{image_ext}"
                    image_path = os.path.join(self.images_dir, image_filename)
                    
                    with open(image_path, "wb") as img_file:
                        img_file.write(image_bytes)
                    
                    # 生成相对路径（用于Markdown）
                    # 相对于输出Markdown文件所在目录
                    if output_file:
                        output_dir = os.path.dirname(os.path.abspath(output_file))
                        if output_dir:
                            relative_path = os.path.relpath(image_path, output_dir)
                        else:
                            relative_path = os.path.basename(image_path)
                    else:
                        # 如果没有输出文件，相对于PDF文件所在目录
                        pdf_dir = os.path.dirname(os.path.abspath(self.pdf_path))
                        if pdf_dir:
                            relative_path = os.path.relpath(image_path, pdf_dir)
                        else:
                            relative_path = os.path.basename(image_path)
                    
                    # 统一使用正斜杠（Markdown标准）
                    relative_path = relative_path.replace('\\', '/')
                    images.append({
                        'path': relative_path,
                        'filename': image_filename,
                        'index': self.image_counter
                    })
                except Exception as e:
                    print(f"  警告: 提取第{page_num}页第{img_index+1}张图片失败: {e}")
                    continue
        except Exception as e:
            print(f"  警告: 处理第{page_num}页图片时出错: {e}")
        
        return images
    
    def extract_images_with_pdfplumber(self, pdf_path, page_num):
        """使用pdfplumber提取图片（备用方法）"""
        images = []
        try:
            with self.pdfplumber.open(pdf_path) as pdf:
                if page_num > len(pdf.pages):
                    return images
                
                page = pdf.pages[page_num - 1]
                
                # pdfplumber的图片提取功能有限，主要尝试提取嵌入的图片
                # 注意：pdfplumber对图片的支持不如PyMuPDF
                if hasattr(page, 'images') and page.images:
                    for img_index, img in enumerate(page.images):
                        try:
                            # 尝试提取图片数据
                            if hasattr(img, 'stream') and img.stream:
                                self.image_counter += 1
                                image_filename = f"page_{page_num}_img_{self.image_counter}.png"
                                image_path = os.path.join(self.images_dir, image_filename)
                                
                                # 保存图片（pdfplumber可能无法直接获取图片数据）
                                # 这里需要根据实际情况调整
                                relative_path = os.path.relpath(image_path, os.path.dirname(pdf_path))
                                images.append({
                                    'path': relative_path,
                                    'filename': image_filename,
                                    'index': self.image_counter
                                })
                        except Exception as e:
                            continue
        except Exception as e:
            pass  # 静默失败，使用PyMuPDF作为主要方法
        
        return images
    
    def convert(self, pdf_path, output_file=None):
        """将PDF转换为Markdown"""
        print(f"正在读取PDF文件: {pdf_path}")
        
        # 保存pdf_path供后续使用
        self.pdf_path = pdf_path
        
        # 设置图片保存目录
        self.setup_images_directory(pdf_path, output_file)
        print(f"图片将保存到: {self.images_dir}")
        
        markdown_content = []
        pdf_doc = None
        
        # 打开PDF文档用于图片提取（如果支持）
        if self.has_fitz:
            try:
                pdf_doc = self.fitz.open(pdf_path)
            except Exception as e:
                print(f"警告: 无法使用PyMuPDF打开PDF: {e}")
                pdf_doc = None
        
        try:
            with self.pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"总页数: {total_pages}")
                
                for i, page in enumerate(pdf.pages, 1):
                    if i % 10 == 0 or i == 1:
                        print(f"处理第 {i}/{total_pages} 页...")
                    
                    # 提取图片（优先使用PyMuPDF）
                    images = []
                    if pdf_doc:
                        images = self.extract_images_with_fitz(pdf_doc, i, output_file)
                    elif self.has_fitz:
                        # 如果之前打开失败，尝试重新打开
                        try:
                            pdf_doc = self.fitz.open(pdf_path)
                            images = self.extract_images_with_fitz(pdf_doc, i, output_file)
                        except:
                            pass
                    
                    if images:
                        print(f"  提取到 {len(images)} 张图片")
                    
                    # 添加页面分隔符（后续优化时会移除）
                    if i > 1:
                        markdown_content.append("\n---\n")
                    markdown_content.append(f"## 第 {i} 页\n\n")
                    
                    # 插入图片（如果有）
                    if images:
                        for img in images:
                            # 使用相对路径，确保Markdown可以正确显示
                            img_path = img['path']  # 已经是正斜杠格式
                            # 如果路径不是相对于输出文件的，需要调整
                            if output_file:
                                output_dir = os.path.dirname(os.path.abspath(output_file))
                                if output_dir and not os.path.isabs(img_path):
                                    # 确保路径相对于输出文件
                                    pass  # 已经在extract_images_with_fitz中处理了
                            markdown_content.append(f"![图片 {img['index']}]({img_path})\n\n")
                    
                    # 提取文本
                    text = page.extract_text()
                    
                    if text:
                        markdown_content.append(text)
                        markdown_content.append("\n")
                    
                    # 尝试提取表格
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            if table:
                                # 检查表格是否有效（至少2行，且不是纯文本内容）
                                valid_table = False
                                if len(table) >= 2:
                                    # 检查第一行是否像表头（通常表头较短）
                                    first_row = [str(cell).strip() if cell else "" for cell in table[0]]
                                    first_row_text = " ".join(first_row).strip()
                                    
                                    # 如果第一行太长（>200字符），可能是文本内容而不是表格
                                    if len(first_row_text) < 200:
                                        # 检查是否有明显的表格结构（至少2列）
                                        if len([c for c in first_row if c]) >= 2:
                                            valid_table = True
                                
                                if valid_table:
                                    markdown_content.append("\n### 表格\n\n")
                                    # 转换为Markdown表格格式
                                    for row_idx, row in enumerate(table):
                                        if row:
                                            # 清理None值
                                            row = [str(cell) if cell is not None else "" for cell in row]
                                            row_text = " ".join(row).strip()
                                            
                                            # 跳过明显是文本内容的行（单列且内容很长）
                                            if len(row) == 1 and len(row_text) > 100:
                                                continue
                                            
                                            markdown_content.append("| " + " | ".join(row) + " |\n")
                                            if row_idx == 0:
                                                # 添加表头分隔符
                                                markdown_content.append("| " + " | ".join(["---"] * len(row)) + " |\n")
                                    markdown_content.append("\n")
        
        except Exception as e:
            print(f"错误: PDF转换失败 - {e}")
            raise
        finally:
            # 关闭PDF文档
            if pdf_doc:
                pdf_doc.close()
        
        if self.image_counter > 0:
            print(f"✓ 共提取 {self.image_counter} 张图片，保存在: {self.images_dir}")
        else:
            if not self.has_fitz:
                print("提示: 未检测到图片。如需提取图片，请安装PyMuPDF: pip install PyMuPDF")
        
        return ''.join(markdown_content)


class MarkdownOptimizer:
    """Markdown优化器"""
    
    def __init__(self):
        pass
        
    def remove_page_markers(self, lines):
        """移除页面标记和分隔符（保留图片引用）"""
        result = []
        for line in lines:
            # 跳过页面标记
            if re.match(r'^##\s*第\s*\d+\s*页', line.strip()):
                continue
            # 跳过页面分隔符
            if line.strip() == '---' and result and result[-1].strip() == '':
                continue
            # 保留图片引用（以![开头的行）
            if line.strip().startswith('!['):
                result.append(line)
                continue
            result.append(line)
        return result
    
    def fix_title_hierarchy(self, lines):
        """修复标题层级"""
        result = []
        seen_first_title = False  # 标记是否已经处理过第一个标题
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 跳过空行和图片引用
            if not stripped or stripped.startswith('!['):
                result.append(line)
                continue
            
            # 如果已经是Markdown标题格式，直接保留（避免重复添加）
            if stripped.startswith('#'):
                result.append(line)
                if not seen_first_title:
                    seen_first_title = True
                continue
            
            # 如果已经看到第一个标题，就不再自动添加主标题
            # 处理主标题（如果文档开头有标题，且还没有看到任何标题）
            if not seen_first_title and len(result) < 5 and not stripped.startswith('|'):
                # 检查是否是标题（短行且不包含标点，且不是命令或配置项）
                is_command = re.match(r'^(yum|rpm|systemctl|vi|cp|tar|cd|\./|sudo|mysqladmin|tail|cat|nikto|/usr/|apt|pip|npm|dnf|ls|nano|suricata|kill|add-apt-repository)', stripped, re.IGNORECASE)
                is_config = re.match(r'^[A-Z_]+:', stripped) or re.match(r'^[a-z_]+\.[a-z_]+:', stripped)
                
                if len(stripped) < 50 and not any(c in stripped for c in '。，、；：') and not is_command and not is_config:
                    # 检查下一行是否是章节标题（一、二、三等）
                    next_stripped = ''
                    if i + 1 < len(lines):
                        next_stripped = lines[i + 1].strip()
                    
                    # 如果下一行是章节标题，说明当前行可能是主标题
                    # 但为了避免重复，检查是否已经有主标题格式
                    if re.match(r'^[一二三四五六七八九十]+ ', next_stripped):
                        # 下一行是章节标题，当前行可能是主标题
                        # 检查是否在结果中已经有主标题
                        has_main_title = False
                        for prev_line in result:
                            if prev_line.strip().startswith('# ') and len(prev_line.strip()) < 100:
                                has_main_title = True
                                break
                        
                        if not has_main_title:
                            result.append('# ' + stripped)
                            result.append('')
                            seen_first_title = True
                            continue
            
            # 处理章节标题（一、二、三等）
            if re.match(r'^[一二三四五六七八九十]+ ', stripped):
                if not stripped.startswith('##'):
                    result.append('## ' + stripped)
                else:
                    result.append(line)
                result.append('')
                if not seen_first_title:
                    seen_first_title = True
                continue
            
            # 处理小节标题（如"2.1"）
            if re.match(r'^\d+\.\d+ ', stripped) and not re.match(r'^\d+\.\d+\.', stripped):
                if not stripped.startswith('###'):
                    result.append('### ' + stripped)
                else:
                    result.append(line)
                result.append('')
                continue
            
            # 处理子小节标题（如"2.2.1"）
            if re.match(r'^\d+\.\d+\.\d+', stripped):
                if not stripped.startswith('####'):
                    result.append('#### ' + stripped)
                else:
                    result.append(line)
                result.append('')
                continue
            
            result.append(line)
        return result
    
    def optimize_code_blocks(self, lines):
        """优化代码块使用"""
        result = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # 检测代码块开始
            if stripped.startswith('```'):
                lang = stripped[3:].strip()
                code_lines = []
                i += 1
                
                # 收集代码块内容
                while i < len(lines):
                    if lines[i].strip().startswith('```'):
                        break
                    code_lines.append(lines[i])
                    i += 1
                
                # 跳过结束标记
                if i < len(lines):
                    i += 1
                
                # 处理代码块
                code_content = '\n'.join(code_lines).strip()
                
                # 检查是否可以与下一个代码块合并
                if code_content and self._can_merge_with_next(lines, i, lang):
                    merged = self._merge_code_blocks(code_lines, lines, i, lang)
                    result.extend(merged['lines'])
                    i = merged['next_index']
                    continue
                
                # 单独处理代码块
                if code_content:
                    result.append(f'```{lang}')
                    for cl in code_lines:
                        result.append(cl)
                    result.append('```')
                    result.append('')
                
                continue
            
            # 检测命令（扩展命令识别模式）
            # 包括：系统命令、包管理器、工具命令、路径开头的命令等
            command_pattern = r'^(yum|rpm|systemctl|vi|cp|tar|cd|\./|sudo|mysqladmin|tail|cat|nikto|/usr/|apt|pip|npm|dnf|ls|nano|suricata|kill|add-apt-repository|apt-get|apt-cache|wget|curl|git|docker|kubectl|psql|mysql|python|python3|node|npm|yarn|make|cmake|gcc|g\+\+|javac|java|go|rustc|cargo|perl|ruby|php|bash|sh|zsh|fish|ssh|scp|rsync|grep|sed|awk|find|chmod|chown|mount|umount|df|du|top|htop|ps|killall|pkill|service|journalctl|log|tail|head|less|more|vim|emacs|nano|gedit|code|subl|atom|firefox|chrome|chromium|xdg-open|open|start|echo|printf|export|source|\.|\.\.|/etc/|/var/|/usr/|/opt/|/home/|/root/|/tmp/)'
            
            if re.match(command_pattern, stripped, re.IGNORECASE):
                # 检查前面是否已经有代码块
                if not result or not result[-1].strip().startswith('```'):
                    result.append('```bash')
                    result.append(line)
                    # 继续收集相关命令
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j]
                        next_stripped = next_line.strip()
                        
                        # 空行时，检查下一行是否还是命令
                        if next_stripped == '':
                            # 跳过空行，检查下一行
                            if j + 1 < len(lines):
                                next_next = lines[j + 1].strip()
                                if re.match(command_pattern, next_next, re.IGNORECASE):
                                    result.append('')
                                    j += 1
                                    continue
                            break
                        
                        # 如果遇到标题，停止收集
                        if re.match(r'^#{1,6}\s+', next_stripped) or re.match(r'^\d+\.', next_stripped):
                            break
                        
                        # 注释行也包含在代码块中
                        if next_stripped.startswith('#'):
                            result.append(next_line)
                            j += 1
                        # 继续收集命令
                        elif re.match(command_pattern, next_stripped, re.IGNORECASE):
                            result.append(next_line)
                            j += 1
                        # 配置项也可能在同一代码块中（如环境变量设置）
                        elif re.match(r'^[A-Z_]+=', next_stripped) or re.match(r'^export\s+', next_stripped):
                            result.append(next_line)
                            j += 1
                        else:
                            break
                    result.append('```')
                    result.append('')
                    i = j
                    continue
            
            # 检测配置项（扩展配置项识别模式）
            # 包括：YAML配置（如 network.host:）、环境变量（如 HOME_NET:）、带引号的配置等
            config_patterns = [
                r'^[a-z_]+\.[a-z_]+:',  # network.host:
                r'^[A-Z_]+:\s*',  # HOME_NET:, HTTP_PORTS: (包括后面可能有引号的情况)
                r'^[a-z_]+:\s*["\[{]',  # 带引号或括号的配置项
            ]
            
            is_config = False
            for pattern in config_patterns:
                if re.match(pattern, stripped) and not stripped.startswith('```'):
                    is_config = True
                    break
            
            if is_config:
                # 检查前面是否有未闭合的yaml代码块
                if result and result[-1].strip() == '```':
                    result.pop()
                    result.append('```yaml')
                    result.append(line)
                    # 继续收集配置项
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j]
                        next_stripped = next_line.strip()
                        
                        if next_stripped == '':
                            # 空行时，检查下一行是否还是配置项
                            if j + 1 < len(lines):
                                next_next = lines[j + 1].strip()
                                is_next_config = False
                                for pattern in config_patterns:
                                    if re.match(pattern, next_next):
                                        is_next_config = True
                                        break
                                if is_next_config:
                                    result.append('')
                                    j += 1
                                    continue
                            break
                        
                        # 如果遇到标题或命令，停止收集
                        if re.match(r'^#{1,6}\s+', next_stripped) or re.match(r'^\d+\.', next_stripped):
                            break
                        
                        # 检查是否是配置项或注释
                        is_next_config = False
                        for pattern in config_patterns:
                            if re.match(pattern, next_stripped):
                                is_next_config = True
                                break
                        
                        if is_next_config or next_stripped.startswith('#') or next_stripped.startswith('-') or next_stripped.startswith('|'):
                            result.append(next_line)
                            j += 1
                        elif re.match(r'^(yum|rpm|systemctl|vi|cp|tar|cd|\./|dnf|ls|nano|suricata)', next_stripped, re.IGNORECASE):
                            break
                        else:
                            break
                    result.append('```')
                    result.append('')
                    i = j
                    continue
                # 如果前面没有代码块，创建一个新的
                elif not result or not result[-1].strip().startswith('```'):
                    # 检查前面是否有说明文字
                    if result and result[-1].strip() and not result[-1].strip().startswith('#'):
                        result.append('')
                    result.append('```yaml')
                    result.append(line)
                    # 继续收集配置项
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j]
                        next_stripped = next_line.strip()
                        
                        if next_stripped == '':
                            # 空行时，检查下一行是否还是配置项
                            if j + 1 < len(lines):
                                next_next = lines[j + 1].strip()
                                is_next_config = False
                                for pattern in config_patterns:
                                    if re.match(pattern, next_next):
                                        is_next_config = True
                                        break
                                if is_next_config:
                                    result.append('')
                                    j += 1
                                    continue
                            break
                        
                        if re.match(r'^#{1,6}\s+', next_stripped) or re.match(r'^\d+\.', next_stripped):
                            break
                        
                        # 检查是否是配置项或注释
                        is_next_config = False
                        for pattern in config_patterns:
                            if re.match(pattern, next_stripped):
                                is_next_config = True
                                break
                        
                        if is_next_config or next_stripped.startswith('#') or next_stripped.startswith('-') or next_stripped.startswith('|'):
                            result.append(next_line)
                            j += 1
                        elif re.match(r'^(yum|rpm|systemctl|vi|cp|tar|cd|\./|dnf|ls|nano|suricata)', next_stripped, re.IGNORECASE):
                            break
                        else:
                            break
                    result.append('```')
                    result.append('')
                    i = j
                    continue
                else:
                    result.append(line)
            else:
                result.append(line)
            
            i += 1
        
        return result
    
    def _can_merge_with_next(self, lines, start_idx, lang):
        """检查是否可以与下一个代码块合并"""
        idx = start_idx
        while idx < len(lines) and lines[idx].strip() == '':
            idx += 1
        
        if idx >= len(lines):
            return False
        
        if not lines[idx].strip().startswith('```'):
            return False
        
        next_lang = lines[idx].strip()[3:].strip()
        return (next_lang == lang) or (lang == 'bash' and next_lang == 'bash') or (not lang and not next_lang)
    
    def _merge_code_blocks(self, first_code, lines, start_idx, lang):
        """合并代码块"""
        result_lines = []
        result_lines.append(f'```{lang}')
        result_lines.extend(first_code)
        
        idx = start_idx
        while idx < len(lines) and lines[idx].strip() == '':
            idx += 1
        
        if idx < len(lines) and lines[idx].strip().startswith('```'):
            idx += 1
        
        while idx < len(lines):
            if lines[idx].strip().startswith('```'):
                idx += 1
                break
            result_lines.append(lines[idx])
            idx += 1
        
        result_lines.append('```')
        result_lines.append('')
        
        return {'lines': result_lines, 'next_index': idx}
    
    def format_links(self, lines):
        """格式化链接"""
        result = []
        for line in lines:
            # 处理URL链接
            if re.match(r'^https?://', line.strip()) and '[' not in line and ']' not in line:
                url = line.strip()
                result.append(f'参考链接: [{url}]({url})')
                result.append('')
                continue
            result.append(line)
        return result
    
    def clean_extra_blank_lines(self, lines):
        """清理多余的空行（最多连续2个）"""
        result = []
        empty_count = 0
        
        for line in lines:
            if line.strip() == '':
                empty_count += 1
                if empty_count <= 2:
                    result.append('')
            else:
                empty_count = 0
                result.append(line)
        
        return result
    
    def remove_duplicate_content(self, lines):
        """移除重复的内容段落"""
        result = []
        seen_paragraphs = {}  # 存储已见过的段落（用于去重）
        current_paragraph = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # 跳过图片引用、代码块标记、表格标记等
            if (stripped.startswith('![') or 
                stripped.startswith('```') or 
                stripped.startswith('|') or
                stripped == '---' or
                re.match(r'^#{1,6}\s+', stripped)):
                # 如果当前有段落，先处理它
                if current_paragraph:
                    para_text = ' '.join(current_paragraph).strip()
                    if para_text and len(para_text) > 20:  # 只处理较长的段落
                        # 检查是否与已见过的段落相似（相似度>80%）
                        is_duplicate = False
                        for seen_text, seen_count in seen_paragraphs.items():
                            if self._text_similarity(para_text, seen_text) > 0.8:
                                is_duplicate = True
                                seen_paragraphs[seen_text] = seen_count + 1
                                break
                        
                        if not is_duplicate:
                            result.extend(current_paragraph)
                            seen_paragraphs[para_text] = 1
                    else:
                        result.extend(current_paragraph)
                    current_paragraph = []
                
                result.append(line)
                i += 1
                continue
            
            # 空行表示段落结束
            if stripped == '':
                if current_paragraph:
                    para_text = ' '.join(current_paragraph).strip()
                    if para_text and len(para_text) > 20:
                        is_duplicate = False
                        for seen_text, seen_count in seen_paragraphs.items():
                            if self._text_similarity(para_text, seen_text) > 0.8:
                                is_duplicate = True
                                seen_paragraphs[seen_text] = seen_count + 1
                                break
                        
                        if not is_duplicate:
                            result.extend(current_paragraph)
                            result.append('')
                            seen_paragraphs[para_text] = 1
                        else:
                            # 是重复的，跳过
                            pass
                    else:
                        result.extend(current_paragraph)
                        result.append('')
                    current_paragraph = []
                else:
                    result.append('')
            else:
                current_paragraph.append(line)
            
            i += 1
        
        # 处理最后一个段落
        if current_paragraph:
            para_text = ' '.join(current_paragraph).strip()
            if para_text and len(para_text) > 20:
                is_duplicate = False
                for seen_text, seen_count in seen_paragraphs.items():
                    if self._text_similarity(para_text, seen_text) > 0.8:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    result.extend(current_paragraph)
            else:
                result.extend(current_paragraph)
        
        return result
    
    def _text_similarity(self, text1, text2):
        """计算两个文本的相似度（简单的字符重叠度）"""
        if not text1 or not text2:
            return 0.0
        
        # 移除空白字符进行比较
        text1_clean = re.sub(r'\s+', '', text1)
        text2_clean = re.sub(r'\s+', '', text2)
        
        if len(text1_clean) == 0 or len(text2_clean) == 0:
            return 0.0
        
        # 计算较短的文本在较长文本中的重叠度
        shorter = text1_clean if len(text1_clean) < len(text2_clean) else text2_clean
        longer = text2_clean if len(text1_clean) < len(text2_clean) else text1_clean
        
        # 使用滑动窗口计算最大重叠
        max_overlap = 0
        for i in range(len(longer) - len(shorter) + 1):
            overlap = sum(1 for j in range(len(shorter)) if shorter[j] == longer[i + j])
            max_overlap = max(max_overlap, overlap)
        
        return max_overlap / len(shorter) if len(shorter) > 0 else 0.0
    
    def clean_duplicate_tables(self, lines):
        """清理表格中的重复内容"""
        result = []
        i = 0
        in_table = False
        table_lines = []
        table_start_idx = -1
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # 检测表格开始
            if stripped.startswith('|') and not in_table:
                in_table = True
                table_start_idx = i
                table_lines = [line]
                i += 1
                continue
            
            # 在表格中
            if in_table:
                # 表格结束（空行或非表格行，且不是表格分隔符）
                if not stripped.startswith('|') and stripped != '':
                    # 处理收集到的表格
                    table_text = ' '.join([l.strip() for l in table_lines]).strip()
                    
                    # 检查表格内容是否与前面的文本内容重复
                    if table_text and len(table_text) > 100:
                        # 向前查找，检查是否有重复内容
                        is_duplicate = False
                        lookback_start = max(0, table_start_idx - 100)  # 向前查找100行
                        prev_text_blocks = []
                        
                        # 收集前面的文本块
                        for j in range(lookback_start, table_start_idx):
                            prev_line = lines[j].strip()
                            # 跳过表格、图片、代码块、标题等
                            if (prev_line.startswith('|') or 
                                prev_line.startswith('![') or 
                                prev_line.startswith('```') or
                                prev_line == '---' or
                                re.match(r'^#{1,6}\s+', prev_line)):
                                continue
                            
                            if prev_line and len(prev_line) > 20:
                                prev_text_blocks.append(prev_line)
                        
                        # 合并前面的文本块
                        prev_text = ' '.join(prev_text_blocks)
                        
                        # 检查相似度
                        if prev_text and self._text_similarity(table_text, prev_text) > 0.6:
                            is_duplicate = True
                        
                        # 如果表格内容与前面文本高度重复，跳过整个表格
                        if is_duplicate:
                            # 跳过表格标题行（如果有）
                            if i < len(lines) and lines[i].strip().startswith('### 表格'):
                                i += 1
                            in_table = False
                            table_lines = []
                            result.append(line)  # 保留非表格行
                            i += 1
                            continue
                    
                    # 不是重复的，输出表格
                    if table_lines:
                        result.extend(table_lines)
                    in_table = False
                    table_lines = []
                    result.append(line)
                    i += 1
                    continue
                
                # 继续收集表格行
                if stripped.startswith('|'):
                    table_lines.append(line)
                i += 1
                continue
            
            result.append(line)
            i += 1
        
        # 处理最后一个表格（如果文档以表格结束）
        if in_table and table_lines:
            table_text = ' '.join([l.strip() for l in table_lines]).strip()
            if table_text and len(table_text) > 100:
                lookback_start = max(0, table_start_idx - 100)
                prev_text_blocks = []
                for j in range(lookback_start, table_start_idx):
                    prev_line = lines[j].strip()
                    if (prev_line.startswith('|') or 
                        prev_line.startswith('![') or 
                        prev_line.startswith('```') or
                        prev_line == '---' or
                        re.match(r'^#{1,6}\s+', prev_line)):
                        continue
                    if prev_line and len(prev_line) > 20:
                        prev_text_blocks.append(prev_line)
                
                prev_text = ' '.join(prev_text_blocks)
                if not (prev_text and self._text_similarity(table_text, prev_text) > 0.6):
                    result.extend(table_lines)
            else:
                result.extend(table_lines)
        
        return result
    
    def fix_specific_issues(self, content):
        """修复特定的格式问题"""
        # 修复logstash配置的代码块问题
        content = re.sub(
            r'```ruby\ninput \{\nbeats \{\nport => 5044\n```\n\n\n\}\n\n```ruby',
            '```ruby\ninput {\n  beats {\n    port => 5044\n  }\n}\n\nfilter {',
            content
        )
        
        # 修复配置项格式（合并到同一个代码块）
        content = re.sub(
            r'```yaml\n([^\n]+)\n```\n\n([a-z_]+\.[a-z_]+:[^\n]+)',
            r'```yaml\n\1\n\2\n```',
            content
        )
        
        # 修复单独的配置项（不在代码块中）
        content = re.sub(
            r'([^\n`])\n([a-z_]+\.[a-z_]+:[^\n]+)\n([^\n`])',
            r'\1\n\n```yaml\n\2\n```\n\n\3',
            content
        )
        
        # 修复被拆分的搜索语法
        content = re.sub(
            r'```\n(index=[^\n]+)\n```\n\n([^\n]+)',
            r'```\n\1  # \2\n```',
            content,
            flags=re.MULTILINE
        )
        
        # 修复重复的代码块开始标记
        content = re.sub(r'```bash\n([^\n]+)\n\n```bash', r'```bash\n\1', content)
        
        # 修复孤立的代码块结束标记
        content = re.sub(r'\n```\n\n```\n', '\n', content)
        content = re.sub(r'\n```\n\n```bash', '\n```bash', content)
        
        # 合并连续的bash代码块
        content = re.sub(
            r'```bash\n([^\n`]+)\n```\n\n```bash\n([^\n`]+)\n```',
            r'```bash\n\1\n\2\n```',
            content
        )
        
        return content
    
    def optimize(self, content):
        """执行所有优化步骤"""
        lines = content.split('\n')
        
        # 步骤1: 移除页面标记
        lines = self.remove_page_markers(lines)
        
        # 步骤2: 清理重复的表格内容（在去重之前先处理表格）
        lines = self.clean_duplicate_tables(lines)
        
        # 步骤3: 移除重复的内容段落
        lines = self.remove_duplicate_content(lines)
        
        # 步骤4: 修复标题层级
        lines = self.fix_title_hierarchy(lines)
        
        # 步骤5: 优化代码块
        lines = self.optimize_code_blocks(lines)
        
        # 步骤6: 格式化链接
        lines = self.format_links(lines)
        
        # 步骤7: 清理多余空行
        lines = self.clean_extra_blank_lines(lines)
        
        # 步骤8: 修复特定问题
        result = '\n'.join(lines)
        result = self.fix_specific_issues(result)
        
        return result


def main():
    # 打印Banner
    print_banner()
    
    # 设置输出编码为UTF-8（Windows兼容性）
    import io
    if sys.platform == 'win32':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except:
            pass  # 如果已经设置过，忽略错误
    
    if len(sys.argv) < 2:
        print("=" * 60)
        print("PtoM - PDF to Markdown Converter")
        print("=" * 60)
        print("\n使用方法:")
        print("    python PtoM.py <PDF文件> [输出文件]")
        print("\n如果不指定输出文件，将自动生成（原文件名.md）")
        print("\n示例:")
        print("    python PtoM.py document.pdf")
        print("    python PtoM.py document.pdf output.md")
        print("=" * 60)
        sys.exit(1)
    
    # 处理中文文件名（Windows编码问题）
    import glob
    
    pdf_file_arg = sys.argv[1]
    
    # 如果文件不存在，尝试使用glob查找（处理编码问题）
    if not os.path.exists(pdf_file_arg):
        # 尝试在当前目录查找PDF文件
        current_dir = os.getcwd()
        pdf_files = glob.glob(os.path.join(current_dir, "*.pdf"))
        if pdf_files:
            # 如果只有一个PDF文件，使用它
            if len(pdf_files) == 1:
                pdf_file = pdf_files[0]
                print(f"自动检测到PDF文件: {os.path.basename(pdf_file)}")
            else:
                # 尝试匹配文件名（忽略编码问题）
                pdf_file = None
                for f in pdf_files:
                    if os.path.basename(f).lower().replace(' ', '') == pdf_file_arg.lower().replace(' ', ''):
                        pdf_file = f
                        break
                if not pdf_file:
                    print(f"错误: 找不到PDF文件 '{pdf_file_arg}'")
                    print(f"当前目录中的PDF文件:")
                    for f in pdf_files:
                        print(f"  - {os.path.basename(f)}")
                    sys.exit(1)
        else:
            print(f"错误: PDF文件 '{pdf_file_arg}' 不存在")
            sys.exit(1)
    else:
        pdf_file = os.path.abspath(pdf_file_arg)
    
    # 确定输出文件
    if len(sys.argv) > 2:
        output_file_arg = sys.argv[2]
        # 如果输出文件路径不存在，使用当前目录
        if os.path.dirname(output_file_arg):
            output_file = os.path.abspath(output_file_arg)
        else:
            output_file = os.path.join(os.path.dirname(pdf_file), output_file_arg)
    else:
        # 自动生成输出文件名
        base_name = os.path.splitext(os.path.basename(pdf_file))[0]
        output_dir = os.path.dirname(pdf_file)
        output_file = os.path.join(output_dir, base_name + ".md")
    
    # 确保输出文件路径有效（处理编码问题）
    try:
        output_file = os.path.abspath(output_file)
        # 测试是否可以创建文件（Windows编码兼容性）
        test_file = output_file + '.test'
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('test')
        os.remove(test_file)
    except (UnicodeEncodeError, OSError) as e:
        # 如果编码失败，使用ASCII安全的文件名
        output_dir = os.path.dirname(output_file)
        base_name = os.path.basename(output_file)
        # 只保留ASCII字符和常见符号
        safe_name = "".join(c for c in base_name if ord(c) < 128 or c in (' ', '-', '_', '.'))
        if not safe_name.endswith('.md'):
            safe_name = safe_name.rsplit('.', 1)[0] + '.md'
        output_file = os.path.join(output_dir, safe_name)
        print(f"注意: 输出文件名已调整为ASCII安全格式: {os.path.basename(output_file)}")
    
    if not pdf_file.lower().endswith('.pdf'):
        print(f"错误: '{pdf_file}' 不是PDF文件")
        sys.exit(1)
    
    print("=" * 60)
    print("PtoM - PDF转Markdown转换")
    print("=" * 60)
    print(f"输入文件: {pdf_file}")
    print(f"输出文件: {output_file}")
    print("=" * 60)
    
    # 步骤1: 转换PDF为Markdown
    print("\n[步骤 1/2] 正在转换PDF为Markdown...")
    try:
        # 确定输出目录（用于保存图片）
        output_dir = os.path.dirname(os.path.abspath(output_file)) if os.path.dirname(output_file) else os.path.dirname(os.path.abspath(pdf_file))
        converter = PDFToMarkdownConverter(output_dir=output_dir)
        markdown_content = converter.convert(pdf_file, output_file)
        print(f"✓ PDF转换完成，共提取 {len(markdown_content)} 字符")
        
        # 如果提取了图片，显示图片目录信息
        if converter.image_counter > 0:
            print(f"✓ 图片已保存到: {converter.images_dir}")
    except Exception as e:
        print(f"✗ 错误: PDF转换失败 - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 步骤2: 优化Markdown
    print("\n[步骤 2/2] 正在优化Markdown文档...")
    try:
        optimizer = MarkdownOptimizer()
        optimized_content = optimizer.optimize(markdown_content)
        print(f"✓ Markdown优化完成")
    except Exception as e:
        print(f"✗ 错误: Markdown优化失败 - {e}")
        sys.exit(1)
    
    # 保存文件
    print(f"\n正在保存到: {output_file}")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(optimized_content)
        print(f"✓ 文件保存成功")
    except Exception as e:
        print(f"✗ 错误: 无法保存文件 - {e}")
        sys.exit(1)
    
    # 统计信息
    print("\n" + "=" * 60)
    print("转换完成！")
    print("=" * 60)
    print(f"原PDF文件: {pdf_file}")
    print(f"输出Markdown: {output_file}")
    print(f"文件大小: {len(optimized_content)} 字符")
    print("=" * 60)


if __name__ == "__main__":
    main()
