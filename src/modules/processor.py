#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理和RAG优化模块

主要功能：
- 药物信息结构化处理
- 数据清洗和格式化
- RAG优化和向量化
- 文档分块和索引
- 数据质量评估

作者: AI Assistant
版本: 1.0.0
"""

import re
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path

# 第三方库
try:
    import jieba
    import jieba.posseg as pseg
except ImportError:
    jieba = None
    pseg = None

# 本地模块
from .logger import LoggerManager
from .config import Config
from .content_validator import ContentValidator


@dataclass
class DrugInfo:
    """
    药物信息数据结构
    
    属性:
        name: 药物名称
        generic_name: 通用名
        brand_name: 商品名
        manufacturer: 生产厂家
        approval_number: 批准文号
        specification: 规格
        dosage_form: 剂型
        ingredients: 成分
        indications: 适应症
        usage_dosage: 用法用量
        adverse_reactions: 不良反应
        contraindications: 禁忌
        precautions: 注意事项
        interactions: 药物相互作用
        storage: 贮藏
        validity_period: 有效期
        executive_standard: 执行标准
        source_url: 来源URL
        crawl_time: 爬取时间
        data_quality_score: 数据质量评分
        content_hash: 内容哈希值
    """
    name: str = ""
    generic_name: str = ""
    brand_name: str = ""
    manufacturer: str = ""
    approval_number: str = ""
    specification: str = ""
    dosage_form: str = ""
    ingredients: str = ""
    indications: str = ""
    usage_dosage: str = ""
    adverse_reactions: str = ""
    contraindications: str = ""
    precautions: str = ""
    interactions: str = ""
    storage: str = ""
    validity_period: str = ""
    executive_standard: str = ""
    source_url: str = ""
    crawl_time: str = ""
    data_quality_score: float = 0.0
    content_hash: str = ""
    # 内容验证相关字段
    content_validation: Dict[str, Any] = None
    has_content_restrictions: bool = False
    quality_report: str = ""


class DataProcessor:
    """
    数据处理器
    
    功能:
    - 药物信息结构化处理
    - 数据清洗和标准化
    - 质量评估和验证
    """
    
    def __init__(self, config: Config, logger: LoggerManager):
        """
        初始化数据处理器
        
        参数:
            config: 配置管理器
            logger: 日志管理器
        """
        self.config = config
        self.logger = logger.get_logger('data_processor')
        self.performance_logger = logger.get_performance_logger()
        
        # 初始化内容验证器
        self.content_validator = ContentValidator(self.logger)
        
        # 初始化分词器
        if jieba:
            jieba.initialize()
            # 添加医药领域词汇
            self._load_medical_dict()
    
    def _load_medical_dict(self):
        """
        加载医药领域词典
        
        功能:
        - 加载常用药物名称
        - 加载医学术语
        - 提高分词准确性
        """
        try:
            medical_words = [
                '阿司匹林', '布洛芬', '对乙酰氨基酚', '头孢', '青霉素',
                '适应症', '禁忌症', '不良反应', '用法用量', '注意事项',
                '药物相互作用', '贮藏', '有效期', '批准文号', '执行标准'
            ]
            
            for word in medical_words:
                if jieba:
                    jieba.add_word(word)
                    
        except Exception as e:
            self.logger.error(f"加载医药词典失败: {e}")
    
    def process_drug_data(self, raw_data: Dict[str, Any]) -> DrugInfo:
        """
        处理原始药物数据
        
        参数:
            raw_data: 原始数据字典
            
        返回:
            DrugInfo: 结构化药物信息
            
        异常:
            ValueError: 数据格式错误
        """
        try:
            with self.performance_logger.timer("process_drug_data"):
                # 创建药物信息对象
                drug_info = DrugInfo()
                
                # 首先处理基本信息
                self._extract_basic_fields(raw_data, drug_info)
                
                # 处理说明书章节数据
                self._extract_manual_sections(raw_data, drug_info)
                
                # 设置元数据
                drug_info.source_url = raw_data.get('url', raw_data.get('source_url', ''))
                drug_info.crawl_time = datetime.now().isoformat()
                
                # 计算内容哈希
                drug_info.content_hash = self._calculate_content_hash(drug_info)
                
                # 计算数据质量评分
                drug_info.data_quality_score = self._calculate_quality_score(drug_info)
                
                self.logger.info(f"处理药物数据完成: {drug_info.name}")
                return drug_info
                
        except Exception as e:
            self.logger.error(f"处理药物数据失败: {e}")
            raise ValueError(f"数据处理失败: {e}")
    
    def _extract_basic_fields(self, raw_data: Dict[str, Any], drug_info: DrugInfo) -> None:
        """
        提取基本字段信息
        
        参数:
            raw_data: 原始数据字典
            drug_info: 药物信息对象
        """
        # 数据映射和清洗
        field_mapping = {
            'name': ['药品名称', '名称', 'name', 'drug_name'],
            'generic_name': ['通用名', '通用名称', 'generic_name'],
            'brand_name': ['商品名', '商标名', 'brand_name'],
            'manufacturer': ['生产企业', '厂家', '生产厂家', 'manufacturer'],
            'approval_number': ['批准文号', '国药准字', 'approval_number'],
            'specification': ['规格', 'specification'],
            'dosage_form': ['剂型', 'dosage_form'],
            'ingredients': ['成分', '主要成分', 'ingredients'],
            'indications': ['适应症', '功能主治', 'indications'],
            'usage_dosage': ['用法用量', '用法', '用量', 'usage_dosage'],
            'adverse_reactions': ['不良反应', 'adverse_reactions'],
            'contraindications': ['禁忌', '禁忌症', 'contraindications'],
            'precautions': ['注意事项', 'precautions'],
            'interactions': ['药物相互作用', '相互作用', 'interactions'],
            'storage': ['贮藏', '储存', '保存', 'storage'],
            'validity_period': ['有效期', 'validity_period'],
            'executive_standard': ['执行标准', 'executive_standard']
        }
        
        # 字段映射和清洗
        for field, possible_keys in field_mapping.items():
            value = self._extract_field_value(raw_data, possible_keys)
            if value:
                cleaned_value = self._clean_text(value)
                setattr(drug_info, field, cleaned_value)
    
    def _extract_manual_sections(self, raw_data: Dict[str, Any], drug_info: DrugInfo) -> None:
        """
        从说明书章节中提取信息
        
        参数:
            raw_data: 原始数据字典
            drug_info: 药物信息对象
        """
        # 检查是否有说明书数据
        manual_data = raw_data.get('manual', {})
        if not manual_data:
            return
            
        sections = manual_data.get('sections', {})
        if not sections:
            return
            
        # 从页面标题提取药物名称
        if not drug_info.name:
            page_title = raw_data.get('page_title', '')
            if page_title:
                # 提取药物名称（去掉说明书等后缀）
                name_match = re.search(r'^([^（(]+)', page_title)
                if name_match:
                    drug_info.name = self._clean_text(name_match.group(1))
        
        # 映射说明书章节到字段
        section_mapping = {
            'ingredients': ['成份', '成分'],
            'specification': ['规格'],
            'indications': ['适应症'],
            'usage_dosage': ['用法用量'],
            'adverse_reactions': ['不良反应'],
            'contraindications': ['禁忌'],
            'precautions': ['注意事项'],
            'interactions': ['药物相互作用'],
            'storage': ['贮藏'],
            'validity_period': ['有效期'],
            'executive_standard': ['执行标准'],
            'manufacturer': ['生产企业']
        }
        
        for field, section_names in section_mapping.items():
            for section_name in section_names:
                if section_name in sections and sections[section_name]:
                    current_value = getattr(drug_info, field, '')
                    if not current_value:  # 只在字段为空时设置
                        cleaned_value = self._clean_text(sections[section_name])
                        setattr(drug_info, field, cleaned_value)
                        break
    
    def _extract_field_value(self, data: Dict[str, Any], possible_keys: List[str]) -> str:
        """
        从数据中提取字段值
        
        参数:
            data: 数据字典
            possible_keys: 可能的键名列表
            
        返回:
            str: 提取的值
        """
        for key in possible_keys:
            if key in data and data[key]:
                return str(data[key]).strip()
        return ""
    
    def _clean_text(self, text: str) -> str:
        """
        清洗文本数据
        
        参数:
            text: 原始文本
            
        返回:
            str: 清洗后的文本
        """
        if not text:
            return ""
        
        # 移除多余空白字符
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除特殊字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # 移除网页版提示信息
        unwanted_patterns = [
            r'网页版仅展示部分.*?使用微信扫一扫.*?在用药助手\s*App\s*看',
            r'关于用药助手\|用户协议\|隐私政策\|加入我们\|内容声明\|网站声明\|应用下载\|丁香园官网',
            r'内容声明',
            r'登录.*?登录',
            r'与\s*5-氟尿嘧啶.*?登录',
            r'Ipsen Pharma Biotech\s*Ipsen Pharma Biotech',
        ]
        
        for pattern in unwanted_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # 移除重复的句子或段落
        sentences = text.split('.')
        unique_sentences = []
        seen = set()
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and sentence not in seen and len(sentence) > 10:
                unique_sentences.append(sentence)
                seen.add(sentence)
        
        text = '. '.join(unique_sentences)
        
        # 标准化标点符号
        text = text.replace('：', ':')
        text = text.replace('；', ';')
        text = text.replace('，', ',')
        text = text.replace('。', '.')
        
        return text.strip()
    
    def _calculate_content_hash(self, drug_info: DrugInfo) -> str:
        """
        计算内容哈希值
        
        参数:
            drug_info: 药物信息
            
        返回:
            str: MD5哈希值
        """
        # 选择关键字段计算哈希
        key_fields = [
            drug_info.name, drug_info.generic_name, drug_info.manufacturer,
            drug_info.approval_number, drug_info.ingredients
        ]
        
        content = '|'.join(filter(None, key_fields))
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _calculate_quality_score(self, drug_info: DrugInfo) -> float:
        """
        计算数据质量评分
        
        参数:
            drug_info: 药物信息
            
        返回:
            float: 质量评分 (0-100)
        """
        score = 0.0
        total_weight = 0.0
        
        # 字段权重配置
        field_weights = {
            'name': 20,
            'generic_name': 15,
            'manufacturer': 10,
            'approval_number': 15,
            'ingredients': 10,
            'indications': 10,
            'usage_dosage': 8,
            'adverse_reactions': 5,
            'contraindications': 3,
            'precautions': 2,
            'storage': 2
        }
        
        for field, weight in field_weights.items():
            value = getattr(drug_info, field, '')
            total_weight += weight
            
            if value and len(value.strip()) > 0:
                # 基础分数
                field_score = weight
                
                # 长度奖励
                if len(value) > 10:
                    field_score *= 1.2
                elif len(value) > 50:
                    field_score *= 1.5
                
                score += field_score
        
        return min(100.0, (score / total_weight) * 100) if total_weight > 0 else 0.0


class RAGOptimizer:
    """
    RAG优化器
    
    功能:
    - 文档分块和索引
    - 关键词提取
    - 语义向量化
    - 检索优化
    """
    
    def __init__(self, config: Config, logger: LoggerManager):
        """
        初始化RAG优化器
        
        参数:
            config: 配置管理器
            logger: 日志管理器
        """
        self.config = config
        self.logger = logger.get_logger('rag_optimizer')
        self.performance_logger = logger.get_performance_logger()
    
    def optimize_for_rag(self, drug_info: DrugInfo) -> Dict[str, Any]:
        """
        为RAG优化药物信息
        
        参数:
            drug_info: 药物信息
            
        返回:
            Dict[str, Any]: RAG优化后的数据
        """
        try:
            with self.performance_logger.timer("optimize_for_rag"):
                rag_data = {
                    'id': drug_info.content_hash,
                    'title': drug_info.name or drug_info.generic_name,
                    'content': self._build_content_text(drug_info),
                    'chunks': self._create_chunks(drug_info),
                    'keywords': self._extract_keywords(drug_info),
                    'metadata': self._build_metadata(drug_info),
                    'quality_score': drug_info.data_quality_score
                }
                
                self.logger.info(f"RAG优化完成: {rag_data['title']}")
                return rag_data
                
        except Exception as e:
            self.logger.error(f"RAG优化失败: {e}")
            return {}
    
    def _build_content_text(self, drug_info: DrugInfo) -> str:
        """
        构建完整内容文本
        
        参数:
            drug_info: 药物信息
            
        返回:
            str: 完整内容文本
        """
        sections = []
        
        # 基本信息
        if drug_info.name:
            sections.append(f"药品名称: {drug_info.name}")
        if drug_info.generic_name:
            sections.append(f"通用名: {drug_info.generic_name}")
        if drug_info.manufacturer:
            sections.append(f"生产企业: {drug_info.manufacturer}")
        
        # 详细信息
        detail_fields = [
            ('成分', drug_info.ingredients),
            ('适应症', drug_info.indications),
            ('用法用量', drug_info.usage_dosage),
            ('不良反应', drug_info.adverse_reactions),
            ('禁忌', drug_info.contraindications),
            ('注意事项', drug_info.precautions),
            ('药物相互作用', drug_info.interactions),
            ('贮藏', drug_info.storage)
        ]
        
        for label, value in detail_fields:
            if value:
                sections.append(f"{label}: {value}")
        
        return '\n\n'.join(sections)
    
    def _create_chunks(self, drug_info: DrugInfo) -> List[Dict[str, str]]:
        """
        创建文档分块
        
        参数:
            drug_info: 药物信息
            
        返回:
            List[Dict[str, str]]: 分块列表
        """
        chunks = []
        
        # 基本信息块
        basic_info = []
        if drug_info.name:
            basic_info.append(f"药品名称: {drug_info.name}")
        if drug_info.generic_name:
            basic_info.append(f"通用名: {drug_info.generic_name}")
        if drug_info.manufacturer:
            basic_info.append(f"生产企业: {drug_info.manufacturer}")
        if drug_info.approval_number:
            basic_info.append(f"批准文号: {drug_info.approval_number}")
        
        if basic_info:
            chunks.append({
                'type': 'basic_info',
                'content': '\n'.join(basic_info)
            })
        
        # 功能信息块
        function_fields = [
            ('ingredients', '成分', drug_info.ingredients),
            ('indications', '适应症', drug_info.indications),
            ('usage_dosage', '用法用量', drug_info.usage_dosage)
        ]
        
        for field_name, label, value in function_fields:
            if value and len(value.strip()) > 10:
                chunks.append({
                    'type': field_name,
                    'content': f"{label}: {value}"
                })
        
        # 安全信息块
        safety_info = []
        if drug_info.adverse_reactions:
            safety_info.append(f"不良反应: {drug_info.adverse_reactions}")
        if drug_info.contraindications:
            safety_info.append(f"禁忌: {drug_info.contraindications}")
        if drug_info.precautions:
            safety_info.append(f"注意事项: {drug_info.precautions}")
        
        if safety_info:
            chunks.append({
                'type': 'safety_info',
                'content': '\n'.join(safety_info)
            })
        
        return chunks
    
    def _extract_keywords(self, drug_info: DrugInfo) -> List[str]:
        """
        提取关键词
        
        参数:
            drug_info: 药物信息
            
        返回:
            List[str]: 关键词列表
        """
        keywords = set()
        
        # 添加药品名称相关关键词
        if drug_info.name:
            keywords.add(drug_info.name)
        if drug_info.generic_name:
            keywords.add(drug_info.generic_name)
        if drug_info.brand_name:
            keywords.add(drug_info.brand_name)
        
        # 使用jieba提取关键词
        if jieba and pseg:
            text_fields = [
                drug_info.ingredients,
                drug_info.indications,
                drug_info.usage_dosage
            ]
            
            for text in text_fields:
                if text:
                    words = pseg.cut(text)
                    for word, flag in words:
                        # 保留名词、动词、形容词
                        if flag.startswith(('n', 'v', 'a')) and len(word) > 1:
                            keywords.add(word)
        
        # 医学术语关键词
        medical_terms = [
            '口服', '注射', '外用', '滴眼', '滴鼻',
            '片剂', '胶囊', '颗粒', '溶液', '软膏',
            '感染', '炎症', '疼痛', '发热', '咳嗽'
        ]
        
        content_text = self._build_content_text(drug_info).lower()
        for term in medical_terms:
            if term in content_text:
                keywords.add(term)
        
        return list(keywords)[:20]  # 限制关键词数量
    
    def _build_metadata(self, drug_info: DrugInfo) -> Dict[str, Any]:
        """
        构建元数据
        
        参数:
            drug_info: 药物信息
            
        返回:
            Dict[str, Any]: 元数据字典
        """
        return {
            'source_url': drug_info.source_url,
            'crawl_time': drug_info.crawl_time,
            'manufacturer': drug_info.manufacturer,
            'approval_number': drug_info.approval_number,
            'dosage_form': drug_info.dosage_form,
            'specification': drug_info.specification,
            'quality_score': drug_info.data_quality_score,
            'content_hash': drug_info.content_hash
        }


class DataExporter:
    """
    数据导出器
    
    功能:
    - 多格式数据导出
    - 批量处理
    - 数据验证
    - 直接从链接获取Jina AI内容并导出
    """
    
    def __init__(self, config: Config, logger: LoggerManager):
        """
        初始化数据导出器
        
        参数:
            config: 配置管理器
            logger: 日志管理器
        """
        self.config = config
        self.logger = logger.get_logger('data_exporter')
        
        # 使用独立目录或默认目录
        if config.USE_INDEPENDENT_DIRS and config.CURRENT_SESSION_DIR:
            self.output_dir = config.CURRENT_SESSION_DIR
        else:
            self.output_dir = config.OUTPUT_DIR
        
        self.output_dir.mkdir(exist_ok=True)
    
    def export_drug_info(self, drug_info: DrugInfo, format_type: str = 'json') -> str:
        """
        导出药物信息
        
        参数:
            drug_info: 药物信息
            format_type: 导出格式 ('json', 'txt', 'md')
            
        返回:
            str: 导出文件路径
            
        异常:
            ValueError: 不支持的格式类型
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = re.sub(r'[^\w\-_]', '_', drug_info.name or 'unknown')
            
            if format_type == 'json':
                filename = f"{safe_name}_{timestamp}.json"
                filepath = self.output_dir / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(asdict(drug_info), f, ensure_ascii=False, indent=2)
                    
            elif format_type == 'txt':
                filename = f"{safe_name}_{timestamp}.txt"
                filepath = self.output_dir / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self._format_as_text(drug_info))
                    
            elif format_type == 'md':
                filename = f"{safe_name}_{timestamp}.md"
                filepath = self.output_dir / filename
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self._format_as_markdown(drug_info))
                    
            else:
                raise ValueError(f"不支持的格式类型: {format_type}")
            
            self.logger.info(f"导出药物信息: {filepath}")
            
            # 如果是markdown格式，同时生成RAG优化版本
            if format_type == 'md':
                optimized_filepath = self._generate_rag_optimized_file(filepath)
                self.logger.info(f"生成RAG优化文件: {optimized_filepath}")
                
                # 输出chunk信息
                chunk_info = self.get_chunk_info(optimized_filepath)
                if chunk_info:
                    self.logger.info(f"Chunk分析结果: 共{chunk_info['total_chunks']}个chunk, 平均大小{chunk_info['average_chunk_size']:.0f}字符")
                    self.logger.info(f"Chunk大小分布: {chunk_info['chunk_sizes']}")
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"导出药物信息失败: {e}")
            raise
    
    def _check_table_completeness(self, content: str) -> bool:
        """
        检测内容中表格数据的完整性
        
        参数:
            content: markdown内容
            
        返回:
            bool: True表示表格数据完整，False表示缺少表格数据
        """
        try:
            # 检查是否包含markdown表格格式
            table_patterns = [
                r'\|.*\|.*\|',  # 基本表格格式
                r'\|\s*[-:]+\s*\|',  # 表格分隔符
            ]
            
            has_table_format = any(re.search(pattern, content, re.MULTILINE) for pattern in table_patterns)
            
            # 检查是否只有图片链接而没有实际表格数据
            image_count = len(re.findall(r'!\[.*?\]\(.*?\)', content))
            
            # 如果有图片但没有表格格式，可能表格被转换为图片
            if image_count > 0 and not has_table_format:
                # 检查是否有表格相关的文本描述
                table_keywords = ['表', '不良反应', '发生率', '%', '例数', '临床研究']
                has_table_context = any(keyword in content for keyword in table_keywords)
                
                if has_table_context:
                    self.logger.debug(f"检测到{image_count}个图片和表格相关内容，但缺少表格格式")
                    return False
            
            # 如果有表格格式，认为数据完整
            if has_table_format:
                self.logger.debug("检测到完整的表格格式")
                return True
            
            # 如果没有表格相关内容，也认为是完整的（可能本身就没有表格）
            return True
            
        except Exception as e:
            self.logger.warning(f"表格完整性检测失败: {e}")
            return True  # 检测失败时保守处理，认为是完整的
    
    def _get_enhanced_content_with_tables(self, drug_url: str, jina_content: str) -> str:
        """
        使用传统爬虫方法获取包含完整表格的内容
        
        参数:
            drug_url: 药物详情页面URL
            jina_content: Jina AI获取的基础内容
            
        返回:
            str: 增强后的markdown内容，如果失败返回None
        """
        try:
            from bs4 import BeautifulSoup
            import requests
            
            # 使用传统方法获取页面内容
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(drug_url, headers=headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取表格数据
            tables = soup.find_all('table')
            if not tables:
                self.logger.debug("未找到表格元素")
                return None
            
            # 转换表格为markdown格式
            enhanced_content = jina_content
            table_markdown = "\n\n## 详细数据表格\n\n"
            
            for i, table in enumerate(tables):
                table_md = self._convert_table_to_markdown(table)
                if table_md:
                    table_markdown += f"\n### 表格 {i+1}\n\n{table_md}\n"
            
            # 如果成功提取到表格，将其添加到内容中
            if "### 表格" in table_markdown:
                enhanced_content += table_markdown
                return enhanced_content
            
            return None
            
        except Exception as e:
            self.logger.error(f"传统爬虫获取表格数据失败: {e}")
            return None
    
    def _convert_table_to_markdown(self, table) -> str:
        """
        将HTML表格转换为markdown格式
        
        参数:
            table: BeautifulSoup表格元素
            
        返回:
            str: markdown格式的表格
        """
        try:
            rows = table.find_all('tr')
            if not rows:
                return ""
            
            markdown_rows = []
            
            for row_idx, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                if not cells:
                    continue
                
                # 提取单元格文本
                cell_texts = []
                for cell in cells:
                    text = cell.get_text(strip=True)
                    # 清理文本，移除多余的空白字符
                    text = re.sub(r'\s+', ' ', text)
                    cell_texts.append(text)
                
                # 构建markdown行
                markdown_row = '| ' + ' | '.join(cell_texts) + ' |'
                markdown_rows.append(markdown_row)
                
                # 如果是第一行（表头），添加分隔符
                if row_idx == 0:
                    separator = '| ' + ' | '.join(['---'] * len(cell_texts)) + ' |'
                    markdown_rows.append(separator)
            
            return '\n'.join(markdown_rows)
            
        except Exception as e:
            self.logger.warning(f"表格转换失败: {e}")
            return ""
    
    def _generate_rag_optimized_file(self, original_filepath: str) -> str:
        """
        生成RAG预处理优化后的markdown文件
        
        功能:
        - 添加行号标记（便于定位和引用）
        - 插入chunk切分标记符号（[CHUNK_BOUNDARY]用于向量化时的chunk边界识别）
        - 根据主题进行分段（提高检索准确性）
        - 保持原有内容不变，只进行格式整理
        
        参数:
            original_filepath: 原始markdown文件路径
            
        返回:
            str: 优化后文件路径
            
        异常:
            Exception: 文件处理失败时抛出异常
        """
        try:
            # 读取原始文件内容
            with open(original_filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 生成优化后的内容
            optimized_content = self._apply_rag_preprocessing(content)
            
            # 生成优化后的文件路径
            original_path = Path(original_filepath)
            optimized_filename = original_path.stem + '_optimized' + original_path.suffix
            optimized_filepath = original_path.parent / optimized_filename
            
            # 保存优化后的文件
            with open(optimized_filepath, 'w', encoding='utf-8') as f:
                f.write(optimized_content)
            
            self.logger.info(f"RAG预处理完成: {optimized_filepath}")
            return str(optimized_filepath)
            
        except Exception as e:
            self.logger.error(f"RAG预处理失败: {e}")
            raise
    
    def _apply_rag_preprocessing(self, content: str) -> str:
        """
        应用RAG预处理规则
        
        功能:
        - 为每行添加行号
        - 智能添加chunk切分标记（确保标题和内容在同一chunk中）
        - 基于语义完整性进行分割
        
        参数:
            content: 原始内容
            
        返回:
            str: 预处理后的内容
        """
        lines = content.split('\n')
        processed_lines = []
        line_number = 1
        
        # 定义主题分段关键词
        section_keywords = [
            '# ', '## ', '### ',  # markdown标题
            '基本信息', '成分', '适应症', '用法用量', 
            '不良反应', '禁忌', '注意事项', '药物相互作用',
            '药理毒理', '药代动力学', '贮藏', '包装', 
            '生产企业', '批准文号'
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
            
            # 添加行号和内容
            if line.strip():  # 非空行
                processed_line = f"<{line_number}> {line}"
                line_number += 1
            else:  # 空行保持原样
                processed_line = line
            
            # 如果是新章节开始，且当前章节已有足够内容，则分割
            if is_section_start and current_section_lines and current_section_chars >= min_chunk_size:
                # 添加当前章节内容
                processed_lines.extend(current_section_lines)
                processed_lines.append("")
                processed_lines.append("[CHUNK_BOUNDARY]")
                processed_lines.append("")
                
                # 重置当前章节
                current_section_lines = []
                current_section_chars = 0
            
            # 将当前行添加到当前章节
            current_section_lines.append(processed_line)
            current_section_chars += len(line)
            
            # 如果当前章节过长，且不是在标题行，则分割
            if (current_section_chars >= max_chunk_size and 
                not is_section_start and 
                len(current_section_lines) > 1):
                
                # 添加当前章节内容
                processed_lines.extend(current_section_lines)
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
    
    def split_by_chunk_boundaries(self, rag_optimized_content: str) -> List[str]:
        """
        根据chunk边界标记分割RAG优化后的内容
        
        功能:
        - 使用[CHUNK_BOUNDARY]标记分割文档
        - 返回分割后的chunk列表
        - 每个chunk包含完整的主题段落
        
        参数:
            rag_optimized_content: RAG预处理后的内容
            
        返回:
            List[str]: 分割后的chunk列表
        """
        # 按照chunk边界标记分割
        chunks = rag_optimized_content.split('[CHUNK_BOUNDARY]')
        
        # 清理空白chunk并保留有意义的内容
        cleaned_chunks = []
        for chunk in chunks:
            chunk = chunk.strip()
            if chunk and len(chunk) > 10:  # 过滤掉过短的chunk
                cleaned_chunks.append(chunk)
        
        return cleaned_chunks
    
    def get_chunk_info(self, rag_optimized_filepath: str) -> dict:
        """
        获取RAG优化文件的chunk信息
        
        功能:
        - 分析chunk数量和大小
        - 提供chunk统计信息
        
        参数:
            rag_optimized_filepath: RAG优化文件路径
            
        返回:
            dict: chunk统计信息
        """
        try:
            with open(rag_optimized_filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            chunks = self.split_by_chunk_boundaries(content)
            
            chunk_info = {
                'total_chunks': len(chunks),
                'chunk_sizes': [len(chunk) for chunk in chunks],
                'average_chunk_size': sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0,
                'chunks_preview': [chunk[:100] + '...' if len(chunk) > 100 else chunk for chunk in chunks[:3]]
            }
            
            return chunk_info
            
        except Exception as e:
            self.logger.error(f"获取chunk信息失败: {e}")
            return {}
    
    def export_drug_from_url(self, drug_url: str, drug_name: str = None) -> str:
        """
        直接从药物链接获取Jina AI内容并导出为markdown文件
        如果检测到表格数据缺失，自动降级到传统爬虫方法获取完整数据
        
        参数:
            drug_url: 药物详情页面URL
            drug_name: 药物名称（用于文件名，如果为None则从内容中提取）
            
        返回:
            str: 导出文件路径
            
        异常:
            Exception: 获取或保存内容失败
        """
        try:
            import requests
            from urllib.parse import urlparse, urlunparse
            
            # 清理URL，去除多余的查询参数（如?ky=xxx）
            parsed_url = urlparse(drug_url)
            # 重新构建URL，去掉查询参数
            clean_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))
            
            # 构建Jina AI URL
            jina_url = f"https://r.jina.ai/{clean_url}"
            
            self.logger.info(f"正在通过Jina AI获取内容: {jina_url}")
            
            # 发送请求获取内容
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(jina_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            content = response.text
            
            # 验证和清理内容
            content = self._validate_and_clean_content(content)
            
            # 检测表格数据完整性
            has_complete_tables = self._check_table_completeness(content)
            
            # 如果表格数据不完整，尝试使用传统爬虫方法补充
            if not has_complete_tables:
                self.logger.warning("检测到Jina AI内容缺少表格数据，尝试使用传统爬虫方法获取完整内容")
                try:
                    enhanced_content = self._get_enhanced_content_with_tables(drug_url, content)
                    if enhanced_content:
                        content = enhanced_content
                        self.logger.info("成功使用传统爬虫方法补充表格数据")
                except Exception as e:
                    self.logger.warning(f"传统爬虫方法补充失败，使用原始Jina AI内容: {e}")
            
            # 提取标题作为文件名
            title = self._extract_title_from_content(content)
            if not title and drug_name:
                title = drug_name
            elif not title:
                title = "药物说明书"
            
            # 生成安全的文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_title = re.sub(r'[^\w\-_\u4e00-\u9fff]', '_', title)
            filename = f"{safe_title}_{timestamp}.md"
            filepath = self.output_dir / filename
            
            # 保存内容
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"成功导出markdown文件: {filepath}")
            
            # 生成RAG优化版本
            try:
                optimized_filepath = self._generate_rag_optimized_file(str(filepath))
                self.logger.info(f"成功生成RAG优化文件: {optimized_filepath}")
            except Exception as e:
                self.logger.warning(f"生成RAG优化文件失败: {e}")
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"从URL导出markdown失败: {e}")
            raise
    
    def _validate_and_clean_content(self, content: str) -> str:
        """
        验证和清理从Jina AI获取的内容
        
        功能:
        - 检测章节内容错位问题
        - 修复常见的内容格式问题
        - 确保章节标题和内容的正确对应
        
        参数:
            content: 原始markdown内容
            
        返回:
            str: 清理后的内容
        """
        try:
            lines = content.split('\n')
            cleaned_lines = []
            
            # 定义章节关键词和其预期内容特征
            section_patterns = {
                '用法用量': ['用法', '用量', '服用', '给药', '剂量', '次/日', 'mg', 'ml'],
                '不良反应': ['不良', '副作用', '毒性', '反应', '发生率', '%'],
                '适应症': ['适应', '主治', '用于', '治疗'],
                '禁忌': ['禁忌', '禁用', '不得', '不应'],
                '注意事项': ['注意', '警告', '慎用', '监测']
            }
            
            current_section = None
            section_content = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    cleaned_lines.append('')
                    continue
                
                # 检查是否是章节标题
                is_section_header = False
                for section_name in section_patterns.keys():
                    if line.startswith('## ') and section_name in line:
                        # 验证之前章节的内容是否正确
                        if current_section and section_content:
                            if self._validate_section_content(current_section, section_content, section_patterns):
                                # 内容正确，保存
                                cleaned_lines.extend(section_content)
                            else:
                                # 内容错位，尝试修复或跳过
                                self.logger.warning(f"检测到章节内容错位: {current_section}")
                                # 可以在这里添加更复杂的修复逻辑
                                cleaned_lines.extend(section_content)  # 暂时保留原内容
                        
                        current_section = section_name
                        section_content = [line]
                        is_section_header = True
                        break
                
                if not is_section_header:
                    if current_section:
                        section_content.append(line)
                    else:
                        cleaned_lines.append(line)
            
            # 处理最后一个章节
            if current_section and section_content:
                if self._validate_section_content(current_section, section_content, section_patterns):
                    cleaned_lines.extend(section_content)
                else:
                    self.logger.warning(f"检测到章节内容错位: {current_section}")
                    cleaned_lines.extend(section_content)
            
            return '\n'.join(cleaned_lines)
            
        except Exception as e:
            self.logger.error(f"内容验证和清理失败: {e}")
            return content  # 返回原始内容
    
    def _validate_section_content(self, section_name: str, content_lines: List[str], patterns: Dict[str, List[str]]) -> bool:
        """
        验证章节内容是否与章节名称匹配
        
        参数:
            section_name: 章节名称
            content_lines: 章节内容行
            patterns: 章节模式字典
            
        返回:
            bool: 内容是否匹配
        """
        if section_name not in patterns:
            return True  # 未知章节，默认认为正确
        
        content_text = ' '.join(content_lines).lower()
        expected_keywords = patterns[section_name]
        
        # 检查是否包含预期关键词
        keyword_matches = sum(1 for keyword in expected_keywords if keyword in content_text)
        
        # 如果匹配的关键词数量达到阈值，认为内容正确
        return keyword_matches >= max(1, len(expected_keywords) // 3)
    
    def _extract_title_from_content(self, content: str) -> str:
        """
        从内容中提取标题
        
        参数:
            content: markdown内容
            
        返回:
            str: 提取的标题
        """
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
            elif line.startswith('## ') and '说明书' in line:
                return line[3:].strip()
        return ""
    
    def _format_as_text(self, drug_info: DrugInfo) -> str:
        """
        格式化为文本
        
        参数:
            drug_info: 药物信息
            
        返回:
            str: 格式化的文本
        """
        lines = []
        lines.append(f"药品名称: {drug_info.name}")
        lines.append(f"通用名: {drug_info.generic_name}")
        lines.append(f"生产企业: {drug_info.manufacturer}")
        lines.append(f"批准文号: {drug_info.approval_number}")
        lines.append("")
        
        if drug_info.ingredients:
            lines.append(f"成分: {drug_info.ingredients}")
            lines.append("")
        
        if drug_info.indications:
            lines.append(f"适应症: {drug_info.indications}")
            lines.append("")
        
        if drug_info.usage_dosage:
            lines.append(f"用法用量: {drug_info.usage_dosage}")
            lines.append("")
        
        if drug_info.adverse_reactions:
            lines.append(f"不良反应: {drug_info.adverse_reactions}")
            lines.append("")
        
        if drug_info.contraindications:
            lines.append(f"禁忌: {drug_info.contraindications}")
            lines.append("")
        
        lines.append(f"数据质量评分: {drug_info.data_quality_score:.1f}")
        lines.append(f"爬取时间: {drug_info.crawl_time}")
        lines.append(f"来源: {drug_info.source_url}")
        
        return '\n'.join(lines)
    
    def _format_as_markdown(self, drug_info: DrugInfo) -> str:
        """
        格式化为Markdown
        
        参数:
            drug_info: 药物信息
            
        返回:
            str: 格式化的Markdown
        """
        lines = []
        lines.append(f"# {drug_info.name}")
        lines.append("")
        
        lines.append("## 基本信息")
        lines.append("")
        lines.append(f"- **通用名**: {drug_info.generic_name}")
        lines.append(f"- **生产企业**: {drug_info.manufacturer}")
        lines.append(f"- **批准文号**: {drug_info.approval_number}")
        lines.append(f"- **规格**: {drug_info.specification}")
        lines.append(f"- **剂型**: {drug_info.dosage_form}")
        lines.append("")
        
        if drug_info.ingredients:
            lines.append("## 成分")
            lines.append("")
            lines.append(drug_info.ingredients)
            lines.append("")
        
        if drug_info.indications:
            lines.append("## 适应症")
            lines.append("")
            lines.append(drug_info.indications)
            lines.append("")
        
        if drug_info.usage_dosage:
            lines.append("## 用法用量")
            lines.append("")
            lines.append(drug_info.usage_dosage)
            lines.append("")
        
        if drug_info.adverse_reactions:
            lines.append("## 不良反应")
            lines.append("")
            lines.append(drug_info.adverse_reactions)
            lines.append("")
        
        if drug_info.contraindications:
            lines.append("## 禁忌")
            lines.append("")
            lines.append(drug_info.contraindications)
            lines.append("")
        
        lines.append("## 元数据")
        lines.append("")
        lines.append(f"- **数据质量评分**: {drug_info.data_quality_score:.1f}")
        lines.append(f"- **爬取时间**: {drug_info.crawl_time}")
        lines.append(f"- **来源**: {drug_info.source_url}")
        
        return '\n'.join(lines)


# 测试代码
if __name__ == "__main__":
    from .config import Config
    from .logger import LoggerManager
    
    # 初始化
    config = Config()
    logger = LoggerManager(config)
    
    # 测试数据处理
    processor = DataProcessor(config, logger)
    
    # 模拟原始数据
    raw_data = {
        '药品名称': '阿司匹林肠溶片',
        '通用名': '阿司匹林',
        '生产企业': '拜耳医药保健有限公司',
        '批准文号': '国药准字J20171021',
        '适应症': '用于预防心肌梗死复发，缓解轻至中度疼痛',
        '用法用量': '口服，一次0.3-0.6g，一日3次',
        'source_url': 'https://drugs.dxy.cn/drug/123456'
    }
    
    # 处理数据
    drug_info = processor.process_drug_data(raw_data)
    print(f"处理完成: {drug_info.name}")
    print(f"质量评分: {drug_info.data_quality_score:.1f}")
    
    # 测试RAG优化
    rag_optimizer = RAGOptimizer(config, logger)
    rag_data = rag_optimizer.optimize_for_rag(drug_info)
    print(f"RAG优化完成，分块数量: {len(rag_data.get('chunks', []))}")
    
    # 测试数据导出
    exporter = DataExporter(config, logger)
    json_file = exporter.export_drug_info(drug_info, 'json')
    print(f"导出JSON文件: {json_file}")