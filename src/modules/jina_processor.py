#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
丁香园爬虫 - Jina AI处理模块

该模块负责通过Jina AI API处理药物详情页链接，获取结构化的内容。
Jina AI可以将网页内容转换为更易于处理的格式，提高数据提取效率。

主要功能:
- 通过Jina AI API处理药物详情页链接
- 获取结构化的页面内容
- 处理API请求和响应
- 错误处理和重试机制

作者: AI Assistant
版本: 1.0.0
创建时间: 2024-01-15
"""

import requests
import time
import json
from typing import Optional, Dict, Any
from urllib.parse import urljoin

from .logger import LoggerManager
from .config import Config


class JinaProcessor:
    """
    Jina AI处理器
    
    负责通过Jina AI API处理药物详情页链接，获取结构化内容。
    """
    
    def __init__(self, config: Config, logger_manager: LoggerManager):
        """
        初始化Jina AI处理器
        
        Args:
            config (Config): 配置管理器实例
            logger_manager (LoggerManager): 日志管理器实例
        """
        self.config = config
        self.logger = logger_manager.get_logger('jina_processor')
        self.performance_logger = logger_manager.get_performance_logger()
        
        # Jina AI配置
        self.jina_base_url = self.config.JINA_API_URL
        self.timeout = self.config.JINA_TIMEOUT
        self.max_retries = self.config.JINA_MAX_RETRIES
        self.retry_delay = 1  # 默认重试延迟1秒
        
        # 请求会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        self.logger.info("Jina AI处理器初始化完成")
    
    def process_url(self, drug_detail_url: str) -> Optional[Dict[str, Any]]:
        """
        通过Jina AI处理药物详情页URL
        
        Args:
            drug_detail_url (str): 药物详情页URL
            
        Returns:
            Optional[Dict[str, Any]]: 处理后的结构化内容，失败时返回None
            
        Raises:
            Exception: 当所有重试都失败时抛出异常
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"开始通过Jina AI处理URL: {drug_detail_url}")
            
            # 构建Jina AI处理URL
            jina_url = self._build_jina_url(drug_detail_url)
            self.logger.debug(f"Jina AI处理URL: {jina_url}")
            
            # 执行请求
            result = self._make_request_with_retry(jina_url)
            
            if result:
                processing_time = time.time() - start_time
                self.logger.info(
                    f"Jina AI处理成功 - URL: {drug_detail_url}, "
                    f"处理时间: {processing_time:.2f}s, "
                    f"内容长度: {len(str(result))}"
                )
                self.logger.info(f"Jina AI处理完成，耗时: {processing_time:.2f}s")
                return result
            else:
                self.logger.error(f"Jina AI处理失败: {drug_detail_url}")
                return None
                
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Jina AI处理异常: {str(e)}, 耗时: {processing_time:.2f}s")
            raise
    
    def _build_jina_url(self, original_url: str) -> str:
        """
        构建Jina AI处理URL
        
        Args:
            original_url (str): 原始药物详情页URL
            
        Returns:
            str: Jina AI处理URL
        """
        # 在原始URL前添加r.jina.ai前缀
        if original_url.startswith('http'):
            jina_url = f"{self.jina_base_url}/{original_url}"
        else:
            jina_url = f"{self.jina_base_url}/https://{original_url}"
            
        self.logger.debug(f"构建Jina URL: {original_url} -> {jina_url}")
        return jina_url
    
    def _make_request_with_retry(self, jina_url: str) -> Optional[Dict[str, Any]]:
        """
        带重试机制的请求执行
        
        Args:
            jina_url (str): Jina AI处理URL
            
        Returns:
            Optional[Dict[str, Any]]: 处理后的内容，失败时返回None
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"第 {attempt + 1} 次尝试请求Jina AI")
                
                # 发送POST请求
                response = self.session.post(
                    jina_url,
                    timeout=self.timeout,
                    verify=True
                )
                
                # 检查响应状态
                if response.status_code == 200:
                    content = self._parse_response(response)
                    if content:
                        self.logger.info(f"Jina AI请求成功 (尝试 {attempt + 1}/{self.max_retries + 1})")
                        return content
                    else:
                        self.logger.warning(f"Jina AI响应内容为空 (尝试 {attempt + 1}/{self.max_retries + 1})")
                else:
                    self.logger.warning(
                        f"Jina AI请求失败 - 状态码: {response.status_code}, "
                        f"响应: {response.text[:200]}... (尝试 {attempt + 1}/{self.max_retries + 1})"
                    )
                    
            except requests.exceptions.Timeout as e:
                last_exception = e
                self.logger.warning(f"Jina AI请求超时 (尝试 {attempt + 1}/{self.max_retries + 1}): {str(e)}")
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                self.logger.warning(f"Jina AI请求异常 (尝试 {attempt + 1}/{self.max_retries + 1}): {str(e)}")
                
            except Exception as e:
                last_exception = e
                self.logger.error(f"Jina AI处理未知异常 (尝试 {attempt + 1}/{self.max_retries + 1}): {str(e)}")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < self.max_retries:
                wait_time = self.retry_delay * (2 ** attempt)  # 指数退避
                self.logger.info(f"等待 {wait_time}s 后重试...")
                time.sleep(wait_time)
        
        # 所有重试都失败
        self.logger.error(f"Jina AI处理最终失败，已尝试 {self.max_retries + 1} 次")
        if last_exception:
            raise last_exception
        return None
    
    def _parse_response(self, response: requests.Response) -> Optional[Dict[str, Any]]:
        """
        解析Jina AI响应内容
        
        Args:
            response (requests.Response): HTTP响应对象
            
        Returns:
            Optional[Dict[str, Any]]: 解析后的内容，失败时返回None
        """
        try:
            # 获取响应内容
            content_type = response.headers.get('content-type', '').lower()
            
            if 'application/json' in content_type:
                # JSON响应
                data = response.json()
                self.logger.debug(f"收到JSON响应，数据键: {list(data.keys()) if isinstance(data, dict) else 'non-dict'}")
                return {
                    'type': 'json',
                    'content': data,
                    'url': response.url,
                    'status_code': response.status_code,
                    'headers': dict(response.headers)
                }
            else:
                # 文本响应
                text_content = response.text
                self.logger.debug(f"收到文本响应，长度: {len(text_content)}")
                return {
                    'type': 'text',
                    'content': text_content,
                    'url': response.url,
                    'status_code': response.status_code,
                    'headers': dict(response.headers)
                }
                
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失败: {str(e)}")
            # 尝试作为文本处理
            return {
                'type': 'text',
                'content': response.text,
                'url': response.url,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'parse_error': str(e)
            }
            
        except Exception as e:
            self.logger.error(f"响应解析异常: {str(e)}")
            return None
    
    def extract_drug_info(self, jina_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        从Jina AI结果中提取药物信息
        
        Args:
            jina_result (Dict[str, Any]): Jina AI处理结果
            
        Returns:
            Optional[Dict[str, Any]]: 提取的药物信息，失败时返回None
        """
        try:
            self.logger.info("开始从Jina AI结果提取药物信息")
            
            content = jina_result.get('content', '')
            content_type = jina_result.get('type', 'text')
            
            if content_type == 'json' and isinstance(content, dict):
                # 处理JSON格式的结构化数据
                return self._extract_from_json(content)
            else:
                # 处理文本格式的数据
                return self._extract_from_text(str(content))
                
        except Exception as e:
            self.logger.error(f"药物信息提取异常: {str(e)}")
            return None
    
    def _extract_from_json(self, json_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        从JSON内容中提取药物信息
        
        Args:
            json_content (Dict[str, Any]): JSON格式的内容
            
        Returns:
            Dict[str, Any]: 提取的药物信息
        """
        # 这里可以根据Jina AI返回的具体JSON结构进行调整
        extracted_info = {
            'source': 'jina_ai',
            'raw_data': json_content,
            'processed_time': time.time()
        }
        
        # 尝试提取常见字段
        if 'title' in json_content:
            extracted_info['drug_name'] = json_content['title']
        
        if 'content' in json_content:
            extracted_info['content'] = json_content['content']
        
        if 'text' in json_content:
            extracted_info['text'] = json_content['text']
            
        self.logger.debug(f"从JSON提取信息完成，字段数: {len(extracted_info)}")
        return extracted_info
    
    def _extract_from_text(self, text_content: str) -> Dict[str, Any]:
        """
        从文本内容中提取药物信息
        
        Args:
            text_content (str): 文本格式的内容
            
        Returns:
            Dict[str, Any]: 提取的药物信息
        """
        extracted_info = {
            'source': 'jina_ai',
            'content': text_content,
            'content_length': len(text_content),
            'processed_time': time.time()
        }
        
        # 简单的文本处理，提取可能的药物名称
        lines = text_content.split('\n')
        if lines:
            # 假设第一行可能包含药物名称
            first_line = lines[0].strip()
            if first_line:
                extracted_info['potential_drug_name'] = first_line
        
        self.logger.debug(f"从文本提取信息完成，内容长度: {len(text_content)}")
        return extracted_info
    
    def close(self):
        """
        关闭处理器，清理资源
        """
        try:
            if hasattr(self, 'session'):
                self.session.close()
            self.logger.info("Jina AI处理器已关闭")
        except Exception as e:
            self.logger.error(f"关闭Jina AI处理器时发生异常: {str(e)}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


# 测试代码
if __name__ == "__main__":
    # 简单测试
    from config import Config
    from logger import LoggerManager
    
    # 初始化配置和日志
    config = Config()
    logger_manager = LoggerManager(config)
    
    # 创建Jina处理器
    with JinaProcessor(config, logger_manager) as processor:
        # 测试URL
        test_url = "https://drugs.dxy.cn/drug/132701.htm"
        
        try:
            result = processor.process_url(test_url)
            if result:
                print(f"处理成功: {result['type']}")
                print(f"内容长度: {len(str(result['content']))}")
                
                # 提取药物信息
                drug_info = processor.extract_drug_info(result)
                if drug_info:
                    print(f"提取信息: {list(drug_info.keys())}")
            else:
                print("处理失败")
                
        except Exception as e:
            print(f"测试异常: {str(e)}")