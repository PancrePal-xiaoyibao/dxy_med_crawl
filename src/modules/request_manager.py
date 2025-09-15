#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
丁香园爬虫 - 请求管理模块

该模块负责处理HTTP请求相关功能，包括请求封装、重试机制、
频率控制、User-Agent轮换等。

主要功能:
- HTTP请求封装（GET、POST等）
- 请求重试机制
- 请求频率控制
- User-Agent轮换
- 请求统计
- 响应处理

作者: AI Assistant
版本: 1.0.0
创建时间: 2024-01-15
"""

import requests
import time
import random
from typing import Optional, Dict, Any, List, Union
from urllib.parse import urljoin, urlparse, quote
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .logger import LoggerManager
from .config import Config
from .cookie_manager import CookieManager


class RequestManager:
    """
    请求管理器
    
    负责处理所有HTTP请求，包括重试机制、频率控制、User-Agent轮换等。
    """
    
    def __init__(self, config: Config, logger_manager: LoggerManager, cookie_manager: CookieManager):
        """
        初始化请求管理器
        
        Args:
            config (Config): 配置管理器实例
            logger_manager (LoggerManager): 日志管理器实例
            cookie_manager (CookieManager): Cookie管理器实例
        """
        self.config = config
        self.logger = logger_manager.get_logger('request_manager')
        self.performance_logger = logger_manager.get_performance_logger()
        self.cookie_manager = cookie_manager
        
        # 请求配置
        self.timeout = self.config.TIMEOUT
        self.max_retries = self.config.MAX_RETRIES
        self.retry_delay = (1, 3)  # 默认重试延迟范围
        self.request_delay = self.config.REQUEST_DELAY
        
        # 初始化请求会话
        self.session = self._create_session()
        
        # User-Agent池
        self.user_agents = self._load_user_agents()
        self.current_ua_index = 0
        
        # 加载Cookie
        self.cookie_manager.load_cookies(self.session)
        
        # 请求统计
        self.request_count = 0
        self.last_request_time = 0
        self._retry_count = 0  # 重试计数器
        
        self.logger.info("请求管理器初始化完成")
    
    def _create_session(self) -> requests.Session:
        """
        创建配置好的请求会话
        
        Returns:
            requests.Session: 配置好的会话对象
        """
        session = requests.Session()
        
        # 设置重试策略
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置默认请求头
        session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        return session
    
    def _load_user_agents(self) -> List[str]:
        """
        加载User-Agent池
        
        Returns:
            List[str]: User-Agent列表
        """
        return self.config.USER_AGENTS
    
    def _get_random_user_agent(self) -> str:
        """
        获取随机User-Agent
        
        Returns:
            str: 随机选择的User-Agent
        """
        if not self.user_agents:
            return 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        # 轮换User-Agent
        user_agent = self.user_agents[self.current_ua_index]
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
        
        return user_agent
    
    def _wait_for_rate_limit(self):
        """
        等待请求频率限制
        
        根据配置的请求延迟范围随机等待
        """
        if self.last_request_time > 0:
            elapsed = time.time() - self.last_request_time
            min_delay, max_delay = self.request_delay
            wait_time = random.uniform(min_delay, max_delay) - elapsed
            
            if wait_time > 0:
                self.logger.debug(f"等待 {wait_time:.2f} 秒以控制请求频率")
                time.sleep(wait_time)
    
    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        发送GET请求
        
        Args:
            url (str): 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            Optional[requests.Response]: 响应对象，失败返回None
        """
        return self._make_request('GET', url, **kwargs)
    
    def post(self, url: str, data=None, json_data=None, **kwargs) -> Optional[requests.Response]:
        """
        发送POST请求
        
        Args:
            url (str): 请求URL
            data: 表单数据
            json_data: JSON数据
            **kwargs: 其他请求参数
            
        Returns:
            Optional[requests.Response]: 响应对象，失败返回None
        """
        if json_data is not None:
            kwargs['json'] = json_data
        if data is not None:
            kwargs['data'] = data
            
        return self._make_request('POST', url, **kwargs)
    
    def _make_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """
        执行HTTP请求
        
        Args:
            method (str): 请求方法
            url (str): 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            Optional[requests.Response]: 响应对象，失败返回None
            
        异常:
            处理网络异常，记录错误日志并重试
        """
        start_time = time.time()
        
        # 等待频率限制
        self._wait_for_rate_limit()
        
        # 设置默认参数
        kwargs.setdefault('timeout', self.timeout)
        kwargs.setdefault('allow_redirects', True)
        
        # 更新User-Agent
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        
        if 'User-Agent' not in kwargs['headers']:
            kwargs['headers']['User-Agent'] = self._get_random_user_agent()
        
        retry_count = 0
        last_exception = None
        
        while retry_count <= self.max_retries:
            try:
                self.logger.debug(f"发送{method}请求: {url}")
                
                # 发送请求
                response = self.session.request(method, url, **kwargs)
                
                # 更新统计信息
                self.request_count += 1
                self.last_request_time = time.time()
                
                # 记录性能信息
                duration = time.time() - start_time
                self.logger.info(
                    f"请求完成: {method} {url} - "
                    f"状态码: {response.status_code}, "
                    f"耗时: {duration:.2f}s, "
                    f"响应大小: {len(response.content)}字节"
                )
                
                # 检查响应状态
                if response.status_code == 200:
                    # 保存Cookie
                    if len(self.session.cookies) > 0:
                        user_agent = kwargs['headers'].get('User-Agent', '')
                        self.cookie_manager.save_cookies(self.session, user_agent)
                    
                    return response
                elif response.status_code in [403, 429]:
                    self.logger.warning(f"请求被限制: {response.status_code}, URL: {url}")
                    # 增加等待时间
                    wait_time = random.uniform(5, 10) * (retry_count + 1)
                    self.logger.info(f"等待 {wait_time:.2f} 秒后重试")
                    time.sleep(wait_time)
                elif response.status_code >= 500:
                    self.logger.warning(f"服务器错误: {response.status_code}, URL: {url}")
                else:
                    self.logger.warning(f"请求失败: {response.status_code}, URL: {url}")
                    return response  # 返回非200响应，让调用者处理
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                self.logger.warning(f"请求超时: {url}, 重试 {retry_count + 1}/{self.max_retries + 1}")
                
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                self.logger.warning(f"连接错误: {url}, 重试 {retry_count + 1}/{self.max_retries + 1}")
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                self.logger.error(f"请求异常: {url}, 错误: {str(e)}")
                
            except Exception as e:
                last_exception = e
                self.logger.error(f"未知异常: {url}, 错误: {str(e)}")
            
            retry_count += 1
            self._retry_count += 1
            
            if retry_count <= self.max_retries:
                # 计算重试延迟
                min_delay, max_delay = self.retry_delay
                delay = random.uniform(min_delay, max_delay) * retry_count
                self.logger.info(f"等待 {delay:.2f} 秒后重试")
                time.sleep(delay)
        
        # 所有重试都失败
        self.logger.error(f"请求最终失败: {method} {url}, 最后异常: {str(last_exception)}")
        return None
    
    def search_drugs(self, keyword: str) -> Optional[requests.Response]:
        """
        搜索药品
        
        Args:
            keyword (str): 搜索关键词
            
        Returns:
            Optional[requests.Response]: 搜索结果响应，失败返回None
        """
        try:
            # 构建搜索URL
            search_url = self.config.get_search_url(keyword)
            
            self.logger.info(f"搜索药品: {keyword}")
            
            # 发送搜索请求
            response = self.get(search_url)
            
            if response and response.status_code == 200:
                self.logger.info(f"搜索成功: {keyword}, 响应长度: {len(response.text)}")
            else:
                self.logger.error(f"搜索失败: {keyword}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"搜索异常: {keyword}, 错误: {str(e)}")
            return None
    
    def get_drug_detail(self, drug_url: str) -> Optional[requests.Response]:
        """
        获取药品详情
        
        Args:
            drug_url (str): 药品详情URL
            
        Returns:
            Optional[requests.Response]: 详情页响应，失败返回None
        """
        try:
            self.logger.info(f"获取药品详情: {drug_url}")
            
            # 发送详情请求
            response = self.get(drug_url)
            
            if response and response.status_code == 200:
                self.logger.info(f"获取详情成功: {drug_url}, 响应长度: {len(response.text)}")
            else:
                self.logger.error(f"获取详情失败: {drug_url}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"获取详情异常: {drug_url}, 错误: {str(e)}")
            return None
    
    def download_file(self, url: str, file_path: str) -> bool:
        """
        下载文件
        
        Args:
            url (str): 文件URL
            file_path (str): 保存路径
            
        Returns:
            bool: 下载成功返回True，失败返回False
        """
        try:
            self.logger.info(f"下载文件: {url} -> {file_path}")
            
            response = self.get(url, stream=True)
            
            if response and response.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                self.logger.info(f"文件下载成功: {file_path}")
                return True
            else:
                self.logger.error(f"文件下载失败: {url}")
                return False
                
        except Exception as e:
            self.logger.error(f"文件下载异常: {url}, 错误: {str(e)}")
            return False
    
    def get_request_stats(self) -> Dict[str, Any]:
        """
        获取请求统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'total_requests': self.request_count,
            'total_retries': self._retry_count,
            'last_request_time': self.last_request_time,
            'current_user_agent': self.session.headers.get('User-Agent', ''),
            'cookies_count': len(self.session.cookies),
            'session_active': bool(self.session)
        }
    
    def reset_session(self):
        """
        重置会话
        
        清除所有Cookie和请求历史，重新初始化会话
        """
        try:
            self.logger.info("重置请求会话")
            
            # 关闭当前会话
            if self.session:
                self.session.close()
            
            # 创建新会话
            self.session = self._create_session()
            
            # 重置统计
            self.request_count = 0
            self.last_request_time = 0
            self._retry_count = 0
            
            # 重新加载Cookie
            self.cookie_manager.load_cookies(self.session)
            
            self.logger.info("会话重置完成")
            
        except Exception as e:
            self.logger.error(f"重置会话失败: {str(e)}")
    
    def close(self):
        """
        关闭请求管理器
        
        清理资源，关闭会话
        """
        try:
            if self.session:
                self.session.close()
                self.logger.info("请求管理器已关闭")
        except Exception as e:
            self.logger.error(f"关闭请求管理器失败: {str(e)}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()