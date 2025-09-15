#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为易安达手工.md文件添加RAG预处理标记的脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.modules.config import Config
from src.modules.logger import LoggerManager
from src.modules.processor import DataExporter

def apply_rag_preprocessing(content: str) -> str:
    """
    应用RAG预处理规则
    
    功能:
    - 智能添加chunk切分标记（确保标题和内容在同一chunk中）
    - 基于语义完整性进行分割
    
    参数:
        content: 原始内容
        
    返回:
        str: 预处理后的内容
    """
    lines = content.split('\n')
    processed_lines = []
    
    # 定义主题分段关键词
    section_keywords = [
        'Title:', 'URL Source:', 'Markdown Content:',  # 文档头部
        '**联合治疗**', '**单药治疗**', '**胃肠道**', '**血液系统**',
        '**全身症状**', '**代谢和营养**', '**皮肤病**', '**呼吸系统**',
        '**神经系统**', '**心血管系统**', '**其它**', '**上市后监测**',
        '表 5', '表 6', '胆碱能综合症', '肝脏', '肾脏', '免疫功能异常',
        '实验室检查', '肌肉骨骼', '心脏异常', '神经系统异常'
    ]
    
    # 添加文档开始标记
    processed_lines.append("====== 文档开始 ======")
    processed_lines.append("")
    
    current_section_lines = []  # 当前章节的行数
    current_section_chars = 0   # 当前章节的字符数
    max_chunk_size = 800        # 最大chunk字符数
    min_chunk_size = 200        # 最小chunk字符数
    
    for i, line in enumerate(lines):
        # 检查是否是主题分段
        is_section_start = any(keyword in line for keyword in section_keywords)
        
        # 如果是新的主题分段，且当前章节有内容
        if is_section_start and current_section_lines:
            # 添加当前章节内容
            processed_lines.extend(current_section_lines)
            
            # 添加chunk边界标记
            processed_lines.append("")
            processed_lines.append("[CHUNK_BOUNDARY]")
            processed_lines.append("")
            
            # 重置当前章节
            current_section_lines = []
            current_section_chars = 0
        
        # 添加当前行到章节
        current_section_lines.append(line)
        current_section_chars += len(line)
        
        # 如果当前章节过长，强制分割
        if current_section_chars > max_chunk_size and len(current_section_lines) > 5:
            # 添加当前章节内容
            processed_lines.extend(current_section_lines)
            
            # 添加chunk边界标记
            processed_lines.append("")
            processed_lines.append("[CHUNK_BOUNDARY]")
            processed_lines.append("")
            
            # 重置当前章节
            current_section_lines = []
            current_section_chars = 0
    
    # 添加最后一个章节的内容
    if current_section_lines:
        processed_lines.extend(current_section_lines)
    
    # 在文档结束添加总体标记
    processed_lines.append("")
    processed_lines.append("[CHUNK_BOUNDARY]")
    processed_lines.append("")
    processed_lines.append("====== 文档结束 ======")
    
    return '\n'.join(processed_lines)

def main():
    """
    主函数：处理易安达手工.md文件
    """
    # 文件路径
    input_file = "/Users/qinxiaoqiang/Downloads/丁香园pc助手说明书获取/output/易安达手工.md"
    output_file = "/Users/qinxiaoqiang/Downloads/丁香园pc助手说明书获取/output/易安达手工_optimized.md"
    
    try:
        # 读取原始文件
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"读取原始文件: {input_file}")
        print(f"原始文件大小: {len(content)} 字符")
        
        # 应用RAG预处理
        optimized_content = apply_rag_preprocessing(content)
        
        # 保存优化后的文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(optimized_content)
        
        print(f"RAG预处理完成: {output_file}")
        print(f"优化后文件大小: {len(optimized_content)} 字符")
        
        # 统计chunk数量
        chunk_count = optimized_content.count('[CHUNK_BOUNDARY]')
        print(f"生成chunk数量: {chunk_count}")
        
    except Exception as e:
        print(f"处理失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())