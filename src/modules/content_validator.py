#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
丁香园爬虫 - 内容完整性验证模块

该模块负责检测和处理丁香园网站的内容限制问题，
包括检测"网页版仅展示部分"提示，验证关键章节内容完整性等。

主要功能:
- 检测内容限制提示
- 验证关键章节完整性
- 提供内容补全建议
- 生成内容质量报告

作者: AI Assistant
版本: 1.0.0
创建时间: 2025-01-15
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from bs4 import BeautifulSoup

class ContentValidator:
    """
    内容完整性验证器
    
    功能：检测和验证药物说明书内容的完整性
    """
    
    def __init__(self, logger=None):
        """
        初始化内容验证器
        
        参数:
            logger: 日志记录器实例
        """
        self.logger = logger
        
        # 内容限制提示关键词
        self.content_restriction_keywords = [
            "网页版仅展示部分",
            "使用微信扫一扫",
            "在用药助手 App 看",
            "完整内容请在App中查看",
            "更多内容请下载App",
            "详细信息请查看移动端"
        ]
        
        # 关键章节列表（这些章节如果缺失或内容过少，说明可能被限制）
        self.critical_sections = {
            '不良反应': {
                'keywords': ['不良反应', '副作用', '不良事件'],
                'min_length': 50,  # 最小字符数
                'required_elements': ['发生率', '症状', '反应']
            },
            '药物相互作用': {
                'keywords': ['药物相互作用', '相互作用', '药物间相互作用'],
                'min_length': 30,
                'required_elements': ['相互作用', '影响']
            },
            '儿童用药': {
                'keywords': ['儿童用药', '小儿用药', '儿童'],
                'min_length': 20,
                'required_elements': ['儿童', '小儿']
            },
            '孕妇及哺乳期妇女用药': {
                'keywords': ['孕妇', '哺乳期', '妊娠期', '孕期'],
                'min_length': 20,
                'required_elements': ['孕妇', '妊娠', '哺乳']
            },
            '老年用药': {
                'keywords': ['老年用药', '老年人用药', '老年患者'],
                'min_length': 20,
                'required_elements': ['老年']
            }
        }
    
    def validate_content_completeness(self, html_content: str, markdown_content: str = None) -> Dict[str, Any]:
        """
        验证内容完整性
        
        参数:
            html_content: 原始HTML内容
            markdown_content: 处理后的Markdown内容（可选）
            
        返回:
            Dict[str, Any]: 验证结果报告
        """
        try:
            validation_result = {
                'is_complete': True,
                'has_restrictions': False,
                'restriction_messages': [],
                'missing_sections': [],
                'incomplete_sections': [],
                'quality_score': 100,
                'recommendations': []
            }
            
            # 1. 检测内容限制提示
            restriction_info = self._detect_content_restrictions(html_content)
            if restriction_info['has_restrictions']:
                validation_result['has_restrictions'] = True
                validation_result['restriction_messages'] = restriction_info['messages']
                validation_result['is_complete'] = False
                validation_result['quality_score'] -= 30
                
                if self.logger:
                    self.logger.warning(f"检测到内容限制: {restriction_info['messages']}")
            
            # 2. 验证关键章节完整性
            section_analysis = self._analyze_critical_sections(html_content, markdown_content)
            validation_result['missing_sections'] = section_analysis['missing']
            validation_result['incomplete_sections'] = section_analysis['incomplete']
            
            # 计算质量分数
            missing_penalty = len(section_analysis['missing']) * 15
            incomplete_penalty = len(section_analysis['incomplete']) * 10
            validation_result['quality_score'] -= (missing_penalty + incomplete_penalty)
            validation_result['quality_score'] = max(0, validation_result['quality_score'])
            
            if section_analysis['missing'] or section_analysis['incomplete']:
                validation_result['is_complete'] = False
            
            # 3. 生成改进建议
            validation_result['recommendations'] = self._generate_recommendations(validation_result)
            
            return validation_result
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"内容完整性验证失败: {e}")
            return {
                'is_complete': False,
                'has_restrictions': False,
                'error': str(e),
                'quality_score': 0
            }
    
    def _detect_content_restrictions(self, html_content: str) -> Dict[str, Any]:
        """
        检测内容限制提示
        
        参数:
            html_content: HTML内容
            
        返回:
            Dict[str, Any]: 检测结果
        """
        result = {
            'has_restrictions': False,
            'messages': [],
            'restriction_elements': []
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 检查文本内容中的限制提示
            page_text = soup.get_text()
            
            for keyword in self.content_restriction_keywords:
                if keyword in page_text:
                    result['has_restrictions'] = True
                    result['messages'].append(f"发现内容限制提示: {keyword}")
                    
                    # 查找包含该关键词的具体元素
                    elements = soup.find_all(text=re.compile(keyword))
                    for elem in elements:
                        parent = elem.parent if elem.parent else None
                        if parent:
                            result['restriction_elements'].append({
                                'text': elem.strip(),
                                'tag': parent.name,
                                'class': parent.get('class', [])
                            })
            
            # 检查特定的限制提示元素（如二维码提示）
            qr_elements = soup.find_all(['p', 'div'], class_=re.compile(r'tips|qr|app|mobile', re.I))
            for elem in qr_elements:
                text = elem.get_text(strip=True)
                if any(keyword in text for keyword in self.content_restriction_keywords):
                    result['has_restrictions'] = True
                    result['messages'].append(f"发现App引导提示: {text[:50]}...")
            
            return result
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"检测内容限制失败: {e}")
            return result
    
    def _analyze_critical_sections(self, html_content: str, markdown_content: str = None) -> Dict[str, List[str]]:
        """
        分析关键章节完整性
        
        参数:
            html_content: HTML内容
            markdown_content: Markdown内容
            
        返回:
            Dict[str, List[str]]: 分析结果
        """
        result = {
            'missing': [],
            'incomplete': [],
            'present': []
        }
        
        try:
            # 使用Markdown内容进行分析（如果可用），否则使用HTML
            content_to_analyze = markdown_content if markdown_content else html_content
            
            if not markdown_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                content_to_analyze = soup.get_text()
            
            for section_name, section_config in self.critical_sections.items():
                section_found = False
                section_content = ""
                
                # 检查是否存在该章节
                for keyword in section_config['keywords']:
                    if keyword in content_to_analyze:
                        section_found = True
                        # 尝试提取该章节的内容
                        section_content = self._extract_section_content(content_to_analyze, keyword)
                        break
                
                if not section_found:
                    result['missing'].append(section_name)
                else:
                    # 检查章节内容是否完整
                    if len(section_content) < section_config['min_length']:
                        result['incomplete'].append(f"{section_name} (内容过短: {len(section_content)}字符)")
                    elif not self._has_required_elements(section_content, section_config['required_elements']):
                        result['incomplete'].append(f"{section_name} (缺少关键信息)")
                    else:
                        result['present'].append(section_name)
            
            return result
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"分析关键章节失败: {e}")
            return result
    
    def _extract_section_content(self, content: str, section_keyword: str) -> str:
        """
        提取特定章节的内容
        
        参数:
            content: 完整内容
            section_keyword: 章节关键词
            
        返回:
            str: 章节内容
        """
        try:
            # 查找章节标题位置
            pattern = rf'#{{{1,6}}}\s*{re.escape(section_keyword)}.*?(?=#{{{1,6}}}|$)'
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            
            if match:
                return match.group(0)
            
            # 如果没有找到Markdown格式，尝试简单的文本匹配
            lines = content.split('\n')
            section_content = []
            in_section = False
            
            for line in lines:
                if section_keyword in line:
                    in_section = True
                    section_content.append(line)
                elif in_section:
                    # 如果遇到新的章节标题，停止
                    if any(keyword in line for keyword in ['##', '适应症', '用法用量', '禁忌', '注意事项']):
                        if not any(keyword in line for keyword in [section_keyword]):
                            break
                    section_content.append(line)
            
            return '\n'.join(section_content)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"提取章节内容失败: {e}")
            return ""
    
    def _has_required_elements(self, content: str, required_elements: List[str]) -> bool:
        """
        检查内容是否包含必需的元素
        
        参数:
            content: 章节内容
            required_elements: 必需元素列表
            
        返回:
            bool: 是否包含必需元素
        """
        if not content or not required_elements:
            return True
        
        content_lower = content.lower()
        found_elements = sum(1 for element in required_elements if element in content_lower)
        
        # 至少包含一半的必需元素
        return found_elements >= max(1, len(required_elements) // 2)
    
    def _generate_recommendations(self, validation_result: Dict[str, Any]) -> List[str]:
        """
        生成改进建议
        
        参数:
            validation_result: 验证结果
            
        返回:
            List[str]: 建议列表
        """
        recommendations = []
        
        if validation_result['has_restrictions']:
            recommendations.append("检测到内容限制，建议：")
            recommendations.append("1. 尝试使用移动端User-Agent访问")
            recommendations.append("2. 考虑使用API接口获取完整数据")
            recommendations.append("3. 联系数据提供方获取完整访问权限")
        
        if validation_result['missing_sections']:
            missing = ', '.join(validation_result['missing_sections'])
            recommendations.append(f"缺失关键章节: {missing}")
            recommendations.append("建议检查页面结构或使用其他数据源补充")
        
        if validation_result['incomplete_sections']:
            incomplete = ', '.join(validation_result['incomplete_sections'])
            recommendations.append(f"章节内容不完整: {incomplete}")
            recommendations.append("建议验证数据提取逻辑或寻找替代数据源")
        
        if validation_result['quality_score'] < 70:
            recommendations.append("数据质量较低，建议：")
            recommendations.append("1. 验证数据源的可靠性")
            recommendations.append("2. 考虑使用多个数据源进行交叉验证")
            recommendations.append("3. 实施数据质量监控机制")
        
        return recommendations
    
    def generate_quality_report(self, validation_result: Dict[str, Any]) -> str:
        """
        生成数据质量报告
        
        参数:
            validation_result: 验证结果
            
        返回:
            str: 格式化的质量报告
        """
        report_lines = []
        report_lines.append("=" * 50)
        report_lines.append("数据质量评估报告")
        report_lines.append("=" * 50)
        
        # 总体评估
        status = "完整" if validation_result['is_complete'] else "不完整"
        score = validation_result.get('quality_score', 0)
        report_lines.append(f"内容完整性: {status}")
        report_lines.append(f"质量评分: {score}/100")
        
        # 内容限制检测
        if validation_result.get('has_restrictions'):
            report_lines.append("\n⚠️  检测到内容限制:")
            for msg in validation_result.get('restriction_messages', []):
                report_lines.append(f"  - {msg}")
        
        # 缺失章节
        if validation_result.get('missing_sections'):
            report_lines.append("\n❌ 缺失的关键章节:")
            for section in validation_result['missing_sections']:
                report_lines.append(f"  - {section}")
        
        # 不完整章节
        if validation_result.get('incomplete_sections'):
            report_lines.append("\n⚠️  不完整的章节:")
            for section in validation_result['incomplete_sections']:
                report_lines.append(f"  - {section}")
        
        # 改进建议
        if validation_result.get('recommendations'):
            report_lines.append("\n💡 改进建议:")
            for rec in validation_result['recommendations']:
                report_lines.append(f"  {rec}")
        
        report_lines.append("\n" + "=" * 50)
        
        return "\n".join(report_lines)


# 测试代码
if __name__ == "__main__":
    # 创建验证器实例
    validator = ContentValidator()
    
    # 测试HTML内容（包含限制提示）
    test_html = """
    <html>
    <body>
        <div class="drug-info">
            <h1>测试药物</h1>
            <h2>适应症</h2>
            <p>用于治疗某些疾病</p>
            
            <h2>不良反应</h2>
            <p>常见不良反应包括...</p>
            
            <div class="app-tips">
                <p>网页版仅展示部分，【药物相互作用、不良反应、儿童用药等】使用微信扫一扫，在用药助手 App 看</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # 执行验证
    result = validator.validate_content_completeness(test_html)
    
    # 生成报告
    report = validator.generate_quality_report(result)
    print(report)