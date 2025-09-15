#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
丁香园爬虫 - 页面解析模块

该模块负责解析丁香园网站的页面内容，包括搜索结果页面和药物详情页面。
提取药物信息、说明书内容等关键数据。

主要功能:
- 解析搜索结果页面，提取药物列表
- 解析药物详情页面，提取说明书内容
- 处理HTML结构，提取文本信息
- 数据清洗和格式化
- 支持多种解析策略

作者: AI Assistant
版本: 1.0.0
创建时间: 2024-01-15
"""

import re
import json
import time
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag, NavigableString
import requests

from .logger import LoggerManager
from .config import Config


class PageParser:
    """
    页面解析器
    
    负责解析丁香园网站的各种页面，提取结构化数据。
    """
    
    def __init__(self, config: Config, logger_manager: LoggerManager):
        """
        初始化页面解析器
        
        Args:
            config (Config): 配置管理器实例
            logger_manager (LoggerManager): 日志管理器实例
        """
        self.config = config
        self.logger = logger_manager.get_logger('parser')
        self.performance_logger = logger_manager.get_performance_logger()
        
        # 解析配置
        self.base_url = self.config.BASE_URL
        
        self.logger.info("页面解析器初始化完成")
    
    def parse_search_results(self, html_content: str) -> List[Dict[str, Any]]:
        """
        解析搜索结果页面
        
        Args:
            html_content (str): 搜索结果页面HTML内容
            
        Returns:
            List[Dict[str, Any]]: 药物信息列表
        """
        try:
            self.logger.info("开始解析搜索结果页面")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            drugs = []
            
            # 方法1: 查找药物卡片容器
            drug_cards = self._find_drug_cards(soup)
            if drug_cards:
                for card in drug_cards:
                    drug_info = self._extract_drug_from_card(card)
                    if drug_info:
                        drugs.append(drug_info)
            
            # 方法2: 如果方法1失败，尝试查找链接模式
            if not drugs:
                drug_links = self._find_drug_links(soup)
                for link_info in drug_links:
                    drugs.append(link_info)
            
            # 方法3: 如果前两种方法都失败，尝试通过JavaScript数据提取
            if not drugs:
                js_data = self._extract_js_data(soup)
                if js_data:
                    drugs = self._parse_js_drug_data(js_data)
            
            self.logger.info(f"解析完成，找到 {len(drugs)} 个药物")
            return drugs
            
        except Exception as e:
            self.logger.error(f"解析搜索结果异常: {str(e)}")
            return []
    
    def _find_drug_cards(self, soup: BeautifulSoup) -> List[Tag]:
        """
        查找药物卡片元素
        
        Args:
            soup (BeautifulSoup): 页面解析对象
            
        Returns:
            List[Tag]: 药物卡片元素列表
        """
        # 尝试多种可能的选择器
        selectors = [
            '.drug-card',
            '.drug-item',
            '.search-result-item',
            '.drug-list-item',
            '[class*="drug"]',
            '[class*="search"][class*="item"]'
        ]
        
        for selector in selectors:
            cards = soup.select(selector)
            if cards:
                self.logger.debug(f"使用选择器 '{selector}' 找到 {len(cards)} 个卡片")
                return cards
        
        self.logger.debug("未找到药物卡片元素")
        return []
    
    def _extract_drug_from_card(self, card: Tag) -> Optional[Dict[str, Any]]:
        """
        从药物卡片中提取信息
        
        Args:
            card (Tag): 药物卡片元素
            
        Returns:
            Optional[Dict[str, Any]]: 药物信息，失败时返回None
        """
        try:
            drug_info = {}
            
            # 提取药物名称
            name_selectors = ['h3', 'h4', '.drug-name', '.title', 'a']
            for selector in name_selectors:
                name_elem = card.select_one(selector)
                if name_elem:
                    drug_info['name'] = name_elem.get_text(strip=True)
                    break
            
            # 提取链接
            link_elem = card.find('a', href=True)
            if link_elem:
                href = link_elem['href']
                # 过滤掉无效的链接，只保留药物详情页链接
                if '/drug/' in href and href != '/pc' and href != '/pc/':
                    if href.startswith('/'):
                        drug_info['url'] = urljoin(self.base_url, href)
                    else:
                        drug_info['url'] = href
                else:
                    # 如果当前链接无效，尝试查找其他链接
                    all_links = card.find_all('a', href=True)
                    for alt_link in all_links:
                        alt_href = alt_link['href']
                        if '/drug/' in alt_href and alt_href != '/pc' and alt_href != '/pc/':
                            if alt_href.startswith('/'):
                                drug_info['url'] = urljoin(self.base_url, alt_href)
                            else:
                                drug_info['url'] = alt_href
                            break
            
            # 提取描述信息
            desc_selectors = ['.description', '.drug-desc', 'p']
            for selector in desc_selectors:
                desc_elem = card.select_one(selector)
                if desc_elem:
                    drug_info['description'] = desc_elem.get_text(strip=True)
                    break
            
            # 提取其他可能的信息
            drug_info['raw_html'] = str(card)
            
            if 'name' in drug_info and 'url' in drug_info:
                return drug_info
            else:
                self.logger.debug(f"卡片信息不完整: {drug_info}")
                return None
                
        except Exception as e:
            self.logger.error(f"提取卡片信息异常: {str(e)}")
            return None
    
    def _find_drug_links(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        查找药物链接
        
        Args:
            soup (BeautifulSoup): 页面解析对象
            
        Returns:
            List[Dict[str, Any]]: 药物链接信息列表
        """
        drugs = []
        
        # 查找所有可能的药物链接
        link_patterns = [
            r'/pc/drug/\d+',
            r'/drug/\d+\.htm',
            r'/drugs/\d+',
            r'drug.*\d+'
        ]
        
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link['href']
            
            # 检查是否匹配药物链接模式
            for pattern in link_patterns:
                if re.search(pattern, href):
                    drug_name = link.get_text(strip=True)
                    if drug_name and len(drug_name) > 1:  # 过滤空链接
                        full_url = urljoin(self.base_url, href) if href.startswith('/') else href
                        drugs.append({
                            'name': drug_name,
                            'url': full_url,
                            'source': 'link_pattern'
                        })
                    break
        
        self.logger.debug(f"通过链接模式找到 {len(drugs)} 个药物")
        return drugs
    
    def _extract_js_data(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        提取页面中的JavaScript数据
        
        Args:
            soup (BeautifulSoup): 页面解析对象
            
        Returns:
            Optional[Dict[str, Any]]: JavaScript数据，失败时返回None
        """
        try:
            # 查找包含数据的script标签
            script_tags = soup.find_all('script')
            
            for script in script_tags:
                if script.string:
                    script_content = script.string
                    
                    # 尝试提取JSON数据
                    json_patterns = [
                        r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                        r'window\.__DATA__\s*=\s*({.*?});',
                        r'var\s+searchData\s*=\s*({.*?});',
                        r'const\s+drugList\s*=\s*(\[.*?\]);'
                    ]
                    
                    for pattern in json_patterns:
                        match = re.search(pattern, script_content, re.DOTALL)
                        if match:
                            try:
                                data = json.loads(match.group(1))
                                self.logger.debug(f"提取到JavaScript数据: {list(data.keys()) if isinstance(data, dict) else 'array'}")
                                return data
                            except json.JSONDecodeError:
                                continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"提取JavaScript数据异常: {str(e)}")
            return None
    
    def _parse_js_drug_data(self, js_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析JavaScript中的药物数据
        
        Args:
            js_data (Dict[str, Any]): JavaScript数据
            
        Returns:
            List[Dict[str, Any]]: 药物信息列表
        """
        drugs = []
        
        try:
            # 尝试不同的数据结构
            possible_keys = ['drugs', 'drugList', 'searchResults', 'data', 'results']
            
            for key in possible_keys:
                if key in js_data and isinstance(js_data[key], list):
                    for item in js_data[key]:
                        if isinstance(item, dict):
                            drug_info = self._normalize_drug_data(item)
                            if drug_info:
                                drugs.append(drug_info)
                    break
            
            self.logger.debug(f"从JavaScript数据解析出 {len(drugs)} 个药物")
            return drugs
            
        except Exception as e:
            self.logger.error(f"解析JavaScript药物数据异常: {str(e)}")
            return []
    
    def _normalize_drug_data(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        标准化药物数据格式
        
        Args:
            raw_data (Dict[str, Any]): 原始药物数据
            
        Returns:
            Optional[Dict[str, Any]]: 标准化后的药物数据
        """
        try:
            drug_info = {}
            
            # 提取名称
            name_keys = ['name', 'drugName', 'title', 'productName']
            for key in name_keys:
                if key in raw_data and raw_data[key]:
                    drug_info['name'] = str(raw_data[key]).strip()
                    break
            
            # 提取URL
            url_keys = ['url', 'link', 'href', 'detailUrl']
            for key in url_keys:
                if key in raw_data and raw_data[key]:
                    url = str(raw_data[key])
                    if url.startswith('/'):
                        drug_info['url'] = urljoin(self.base_url, url)
                    else:
                        drug_info['url'] = url
                    break
            
            # 提取其他信息
            if 'description' in raw_data:
                drug_info['description'] = str(raw_data['description']).strip()
            
            if 'id' in raw_data:
                drug_info['drug_id'] = str(raw_data['id'])
            
            # 保存原始数据
            drug_info['raw_data'] = raw_data
            
            if 'name' in drug_info and 'url' in drug_info:
                return drug_info
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"标准化药物数据异常: {str(e)}")
            return None
    
    def parse_drug_detail(self, html_content: str, drug_url: str) -> Optional[Dict[str, Any]]:
        """
        解析药物详情页面
        
        Args:
            html_content (str): 详情页面HTML内容
            drug_url (str): 药物详情页URL
            
        Returns:
            Optional[Dict[str, Any]]: 药物详细信息，失败时返回None
        """
        try:
            self.logger.info(f"开始解析药物详情页面: {drug_url}")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            drug_detail = {
                'url': drug_url,
                'parse_time': time.time()
            }
            
            # 提取药物基本信息
            basic_info = self._extract_basic_info(soup)
            drug_detail.update(basic_info)
            
            # 提取说明书内容
            manual_content = self._extract_manual_content(soup)
            if manual_content:
                drug_detail['manual'] = manual_content
            
            # 提取其他信息
            additional_info = self._extract_additional_info(soup)
            drug_detail.update(additional_info)
            
            self.logger.info(f"药物详情解析完成: {drug_detail.get('name', '未知')}")
            return drug_detail
            
        except Exception as e:
            self.logger.error(f"解析药物详情异常: {str(e)}")
            return None
    
    def _extract_basic_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        提取药物基本信息
        
        Args:
            soup (BeautifulSoup): 页面解析对象
            
        Returns:
            Dict[str, Any]: 基本信息
        """
        basic_info = {}
        
        try:
            # 提取药物名称
            title_selectors = ['h1', '.drug-title', '.page-title', 'title']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    if title_text and '说明书' not in title_text:
                        basic_info['name'] = title_text
                        break
            
            # 提取药物ID（从URL中）
            if 'url' in basic_info:
                id_match = re.search(r'/(\d+)\.htm', basic_info['url'])
                if id_match:
                    basic_info['drug_id'] = id_match.group(1)
            
            self.logger.debug(f"提取基本信息: {basic_info}")
            return basic_info
            
        except Exception as e:
            self.logger.error(f"提取基本信息异常: {str(e)}")
            return {}
    
    def _extract_manual_content(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        提取药物说明书内容
        
        Args:
            soup (BeautifulSoup): 页面解析对象
            
        Returns:
            Optional[Dict[str, Any]]: 说明书内容，失败时返回None
        """
        try:
            manual = {}
            
            # 查找说明书容器
            manual_selectors = [
                '.drug-manual',
                '.manual-content',
                '.drug-instruction',
                '.content-main',
                '#manual-content'
            ]
            
            manual_container = None
            for selector in manual_selectors:
                container = soup.select_one(selector)
                if container:
                    manual_container = container
                    break
            
            if not manual_container:
                # 如果没找到专门的容器，使用整个body
                manual_container = soup.find('body')
            
            if manual_container:
                # 提取各个章节
                sections = self._extract_manual_sections(manual_container)
                if sections:
                    manual['sections'] = sections
                
                # 提取纯文本内容
                text_content = manual_container.get_text(separator='\n', strip=True)
                manual['full_text'] = text_content
                
                # 提取HTML内容（用于备份）
                manual['html_content'] = str(manual_container)
            
            return manual if manual else None
            
        except Exception as e:
            self.logger.error(f"提取说明书内容异常: {str(e)}")
            return None
    
    def _extract_manual_sections(self, container: Tag) -> Dict[str, str]:
        """
        提取说明书各个章节
        
        Args:
            container (Tag): 说明书容器元素
            
        Returns:
            Dict[str, str]: 章节内容字典
        """
        sections = {}
        
        try:
            # 常见的说明书章节
            section_keywords = {
                '成份': ['成份', '成分', '主要成份'],
                '性状': ['性状', '外观'],
                '适应症': ['适应症', '适应证', '主治'],
                '规格': ['规格', '包装规格'],
                '用法用量': ['用法用量', '用法', '用量', '服用方法'],
                '不良反应': ['不良反应', '副作用', '毒副反应'],
                '禁忌': ['禁忌', '禁忌症'],
                '注意事项': ['注意事项', '注意'],
                '孕妇及哺乳期妇女用药': ['孕妇及哺乳期妇女用药', '孕妇用药', '哺乳期用药'],
                '儿童用药': ['儿童用药', '小儿用药'],
                '老年用药': ['老年用药', '老年患者用药'],
                '药物相互作用': ['药物相互作用', '相互作用'],
                '药物过量': ['药物过量', '过量'],
                '药理毒理': ['药理毒理', '药理作用', '毒理研究'],
                '药代动力学': ['药代动力学'],
                '贮藏': ['贮藏', '储存', '保存'],
                '包装': ['包装'],
                '有效期': ['有效期', '保质期'],
                '执行标准': ['执行标准', '标准'],
                '批准文号': ['批准文号', '国药准字'],
                '生产企业': ['生产企业', '生产厂家', '制造商']
            }
            
            # 查找标题和内容
            all_elements = container.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'span'])
            
            current_section = None
            current_content = []
            
            for elem in all_elements:
                text = elem.get_text(strip=True)
                if not text:
                    continue
                
                # 检查是否是章节标题
                is_section_title = False
                for section_name, keywords in section_keywords.items():
                    for keyword in keywords:
                        # 改进的标题检测条件：
                        # 1. 文本完全等于关键词，或
                        # 2. 文本以关键词开头且长度合理（避免包含大段内容），或
                        # 3. 关键词在文本中且文本较短（可能是标题）
                        text_clean = text.strip('：: \t\n')
                        if (text_clean == keyword or 
                            text.startswith(keyword) or
                            (keyword in text and len(text) <= 30)):
                            # 额外检查：如果是"用法用量"关键词，确保不包含"不良反应"内容
                            if keyword == '用法用量' and '不良反应' in text:
                                continue
                            
                            # 保存之前的章节
                            if current_section and current_content:
                                sections[current_section] = '\n'.join(current_content)
                            
                            # 开始新章节
                            current_section = section_name
                            current_content = []
                            is_section_title = True
                            break
                    if is_section_title:
                        break
                
                # 如果不是标题，添加到当前章节内容
                if not is_section_title and current_section:
                    # 检查是否包含表格
                    tables = elem.find_all('table')
                    if tables:
                        self.logger.debug(f"在章节 {current_section} 中发现 {len(tables)} 个表格")
                        # 如果包含表格，先添加表格外的文本内容
                        # 创建元素副本并移除表格，获取剩余文本
                        elem_copy = elem.__copy__()
                        for table in elem_copy.find_all('table'):
                            table.decompose()
                        remaining_text = elem_copy.get_text(strip=True)
                        if remaining_text:
                            current_content.append(remaining_text)
                            self.logger.debug(f"添加表格外文本: {remaining_text[:100]}...")
                        
                        # 然后添加转换后的表格
                        for i, table in enumerate(tables):
                            table_markdown = self._convert_table_to_markdown(table)
                            if table_markdown:
                                current_content.append(table_markdown)
                                self.logger.debug(f"成功转换表格 {i+1}: {len(table_markdown)} 字符")
                            else:
                                self.logger.warning(f"表格 {i+1} 转换失败")
                    else:
                        # 普通文本内容
                        current_content.append(text)
            
            # 保存最后一个章节
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content)
            
            self.logger.debug(f"提取到 {len(sections)} 个说明书章节")
            return sections
            
        except Exception as e:
            self.logger.error(f"提取说明书章节异常: {str(e)}")
            return {}
    
    def _convert_table_to_markdown(self, table: Tag) -> str:
        """
        将HTML表格转换为Markdown格式
        
        Args:
            table (Tag): HTML表格元素
            
        Returns:
            str: Markdown格式的表格
        """
        try:
            markdown_lines = []
            rows = table.find_all('tr')
            
            if not rows:
                return ""
            
            # 处理表头
            header_row = rows[0]
            headers = []
            header_cells = header_row.find_all(['th', 'td'])
            
            for cell in header_cells:
                cell_text = cell.get_text(strip=True)
                headers.append(cell_text)
            
            if headers:
                # 添加表头行
                markdown_lines.append('| ' + ' | '.join(headers) + ' |')
                # 添加分隔行
                markdown_lines.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
            
            # 处理数据行
            data_rows = rows[1:] if headers else rows
            for row in data_rows:
                cells = row.find_all(['td', 'th'])
                row_data = []
                
                for cell in cells:
                    cell_text = cell.get_text(strip=True)
                    # 处理换行符和特殊字符
                    cell_text = cell_text.replace('\n', '<br>')
                    row_data.append(cell_text)
                
                if row_data:
                    # 确保列数一致
                    while len(row_data) < len(headers):
                        row_data.append('')
                    markdown_lines.append('| ' + ' | '.join(row_data[:len(headers)]) + ' |')
            
            return '\n'.join(markdown_lines) + '\n'
            
        except Exception as e:
            self.logger.error(f"转换表格为Markdown异常: {str(e)}")
            # 如果转换失败，返回原始HTML
            return f"\n```html\n{str(table)}\n```\n"
    
    def _extract_additional_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        提取其他附加信息
        
        Args:
            soup (BeautifulSoup): 页面解析对象
            
        Returns:
            Dict[str, Any]: 附加信息
        """
        additional_info = {}
        
        try:
            # 提取meta信息
            meta_description = soup.find('meta', attrs={'name': 'description'})
            if meta_description and meta_description.get('content'):
                additional_info['meta_description'] = meta_description['content']
            
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords and meta_keywords.get('content'):
                additional_info['meta_keywords'] = meta_keywords['content']
            
            # 提取页面标题
            title_tag = soup.find('title')
            if title_tag:
                additional_info['page_title'] = title_tag.get_text(strip=True)
            
            return additional_info
            
        except Exception as e:
            self.logger.error(f"提取附加信息异常: {str(e)}")
            return {}
    
    def clean_text(self, text: str) -> str:
        """
        清理文本内容
        
        Args:
            text (str): 原始文本
            
        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # 移除HTML实体
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        
        return text.strip()


# 测试代码
if __name__ == "__main__":
    # 简单测试
    from config import Config
    from logger import LoggerManager
    
    # 初始化配置和日志
    config = Config()
    logger_manager = LoggerManager(config)
    
    # 创建解析器
    parser = PageParser(config, logger_manager)
    
    # 测试HTML解析
    test_html = """
    <html>
    <body>
        <div class="drug-card">
            <h3>测试药物</h3>
            <a href="/drug/123.htm">查看详情</a>
            <p>这是药物描述</p>
        </div>
    </body>
    </html>
    """
    
    results = parser.parse_search_results(test_html)
    print(f"解析结果: {results}")