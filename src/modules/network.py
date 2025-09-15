#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
丁香园爬虫 - 网络请求模块

该模块负责协调各种网络相关操作，整合HTTP请求、Cookie管理、
浏览器模拟、代理设置等功能。作为网络操作的统一入口。

主要功能:
- 统一的网络操作接口
- 协调各个管理器的工作
- 提供高级网络操作方法
- 统一的错误处理和日志记录

作者: AI Assistant
版本: 2.0.0
创建时间: 2024-01-15
更新时间: 2024-01-15
"""

import time
import requests
from typing import Optional, Dict, Any, List, Union

from .logger import LoggerManager
from .config import Config
from .cookie_manager import CookieManager
from .request_manager import RequestManager
from .browser_manager import BrowserManager
from .proxy_manager import ProxyManager


class NetworkManager:
    """
    网络管理器
    
    作为网络操作的统一入口，协调各个专门的管理器来完成不同的网络任务。
    提供高级的网络操作接口，隐藏底层实现细节。
    """
    
    def __init__(self, config: Config, logger_manager: LoggerManager):
        """
        初始化网络管理器
        
        Args:
            config (Config): 配置管理器实例
            logger_manager (LoggerManager): 日志管理器实例
        """
        self.config = config
        self.logger = logger_manager.get_logger('network')
        self.performance_logger = logger_manager.get_performance_logger()
        
        # 初始化各个管理器
        self.cookie_manager = CookieManager(config, logger_manager)
        self.proxy_manager = ProxyManager(config, logger_manager)
        self.request_manager = RequestManager(config, logger_manager, self.cookie_manager)
        
        # 浏览器管理器（可选）
        self.browser_manager = None
        self.use_browser = getattr(config, 'USE_BROWSER', False)
        
        if self.use_browser:
            try:
                self.browser_manager = BrowserManager(config, logger_manager, self.cookie_manager)
            except ImportError as e:
                self.logger.warning(f"浏览器管理器初始化失败: {str(e)}")
                self.use_browser = False
        
        # 统计信息
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        
        self.logger.info("网络管理器初始化完成")
    
    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        发送GET请求
        
        Args:
            url (str): 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            Optional[requests.Response]: 响应对象，失败时返回None
        """
        self.total_requests += 1
        
        try:
            if self.use_browser and self.browser_manager:
                # 使用浏览器模式
                response = self.browser_manager.get(url, **kwargs)
            else:
                # 使用HTTP请求模式
                response = self.request_manager.get(url, **kwargs)
            
            if response and response.status_code == 200:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
                
            return response
            
        except Exception as e:
            self.failed_requests += 1
            self.logger.error(f"GET请求失败: {url}, 错误: {str(e)}")
            return None
    
    def post(self, url: str, data: Optional[Dict] = None, json_data: Optional[Dict] = None, **kwargs) -> Optional[requests.Response]:
        """
        发送POST请求
        
        Args:
            url (str): 请求URL
            data (Optional[Dict]): 表单数据
            json_data (Optional[Dict]): JSON数据
            **kwargs: 其他请求参数
            
        Returns:
            Optional[requests.Response]: 响应对象，失败时返回None
        """
        self.total_requests += 1
        
        try:
            if self.use_browser and self.browser_manager:
                # 使用浏览器模式
                response = self.browser_manager.post(url, data=data, json_data=json_data, **kwargs)
            else:
                # 使用HTTP请求模式
                response = self.request_manager.post(url, data=data, json_data=json_data, **kwargs)
            
            if response and response.status_code == 200:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
                
            return response
            
        except Exception as e:
            self.failed_requests += 1
            self.logger.error(f"POST请求失败: {url}, 错误: {str(e)}")
            return None
    
    def request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """
        发送HTTP请求（通用方法）
        
        Args:
            method (str): 请求方法
            url (str): 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            Optional[requests.Response]: 响应对象，失败时返回None
        """
        self.total_requests += 1
        
        try:
            if self.use_browser and self.browser_manager:
                # 使用浏览器模式
                response = self.browser_manager.request(method, url, **kwargs)
            else:
                # 使用HTTP请求模式
                response = self.request_manager.request(method, url, **kwargs)
            
            if response and response.status_code == 200:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
                
            return response
            
        except Exception as e:
            self.failed_requests += 1
            self.logger.error(f"{method}请求失败: {url}, 错误: {str(e)}")
            return None
    
    def get_with_browser(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        使用浏览器模式发送GET请求
        
        Args:
            url (str): 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            Optional[requests.Response]: 响应对象，失败时返回None
        """
        if not self.browser_manager:
            self.logger.error("浏览器管理器未初始化")
            return None
            
        self.total_requests += 1
        
        try:
            response = self.browser_manager.get(url, **kwargs)
            
            if response and response.status_code == 200:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
                
            return response
            
        except Exception as e:
            self.failed_requests += 1
            self.logger.error(f"浏览器GET请求失败: {url}, 错误: {str(e)}")
            return None
    
    def search_drug(self, keyword: str) -> Optional[requests.Response]:
        """
        搜索药品信息
        
        Args:
            keyword (str): 搜索关键词
            
        Returns:
            Optional[requests.Response]: 响应对象，失败时返回None
        """
        if self.use_browser and self.browser_manager:
            return self.browser_manager.search_drugs(keyword)
        else:
            return self.request_manager.search_drugs(keyword)
    
    def get_drug_detail(self, drug_id: str) -> Optional[requests.Response]:
        """
        获取药品详情
        
        Args:
            drug_id (str): 药品ID
            
        Returns:
            Optional[requests.Response]: 响应对象，失败时返回None
        """
        if self.use_browser and self.browser_manager:
            return self.browser_manager.get_drug_detail(drug_id)
        else:
            return self.request_manager.get_drug_detail(drug_id)
    
    def download_file(self, url: str, save_path: str, **kwargs) -> bool:
        """
        下载文件
        
        Args:
            url (str): 文件URL
            save_path (str): 保存路径
            **kwargs: 其他请求参数
            
        Returns:
            bool: 下载是否成功
        """
        return self.request_manager.download_file(url, save_path, **kwargs)
    
    # Cookie管理方法
    def save_cookies(self) -> bool:
        """
        保存Cookie到文件
        
        Returns:
            bool: 保存是否成功
        """
        if hasattr(self.request_manager, 'session'):
            return self.cookie_manager.save_cookies(self.request_manager.session)
        return False
    
    def load_cookies(self) -> bool:
        """
        加载Cookie从文件
        
        Returns:
            bool: 加载是否成功
        """
        if hasattr(self.request_manager, 'session'):
            return self.cookie_manager.load_cookies(self.request_manager.session)
        return False
    
    def validate_cookies(self) -> bool:
        """
        验证Cookie是否有效
        
        Returns:
            bool: Cookie是否有效
        """
        return self.cookie_manager.validate_cookies()
    
    def refresh_cookies(self) -> bool:
        """
        刷新Cookie
        
        Returns:
            bool: 刷新是否成功
        """
        return self.cookie_manager.refresh_cookies()
    
    # 代理管理方法
    def set_proxy(self, proxy_info: Optional[Dict] = None) -> bool:
        """
        设置代理
        
        Args:
            proxy_info (Optional[Dict]): 代理信息，None表示使用下一个可用代理
            
        Returns:
            bool: 设置是否成功
        """
        if proxy_info:
            return self.proxy_manager.set_proxy(proxy_info)
        else:
            return self.proxy_manager.rotate_proxy()
    
    def get_current_proxy(self) -> Optional[Dict]:
        """
        获取当前代理信息
        
        Returns:
            Optional[Dict]: 当前代理信息
        """
        return self.proxy_manager.get_current_proxy()
    
    # 统计和管理方法
    def get_request_stats(self) -> Dict[str, Any]:
        """
        获取请求统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': self.successful_requests / max(self.total_requests, 1) * 100,
            'use_browser': self.use_browser,
            'browser_available': self.browser_manager is not None,
            'request_manager_stats': self.request_manager.get_stats() if hasattr(self.request_manager, 'get_stats') else {},
            'cookie_manager_stats': self.cookie_manager.get_stats() if hasattr(self.cookie_manager, 'get_stats') else {},
            'proxy_manager_stats': self.proxy_manager.get_stats() if hasattr(self.proxy_manager, 'get_stats') else {}
        }
    
    def reset_session(self) -> None:
        """
        重置会话
        """
        self.request_manager.reset_session()
        if self.browser_manager:
            self.browser_manager.reset_session()
        
        # 重置统计
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        
        self.logger.info("网络会话已重置")
    
    def close(self) -> None:
        """
        关闭网络管理器，清理资源
        """
        try:
            # 保存Cookie
            self.save_cookies()
            
            # 关闭各个管理器
            if hasattr(self.request_manager, 'close'):
                self.request_manager.close()
            
            if self.browser_manager and hasattr(self.browser_manager, 'close'):
                self.browser_manager.close()
            
            if hasattr(self.proxy_manager, 'close'):
                self.proxy_manager.close()
            
            self.logger.info("网络管理器已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭网络管理器时发生错误: {str(e)}")
    
    def __enter__(self):
        """
        上下文管理器入口
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器出口
        """
        self.close()


if __name__ == "__main__":
    # 测试代码
    from .config import Config
    from .logger import LoggerManager
    
    # 初始化配置和日志
    config = Config()
    logger_manager = LoggerManager(config)
    
    # 测试网络管理器
    with NetworkManager(config, logger_manager) as network:
        # 测试搜索
        response = network.search_drug("阿司匹林")
        if response:
            print(f"搜索成功: {response.status_code}")
            print(f"响应长度: {len(response.text)}")
        else:
            print("搜索失败")
        
        # 打印统计信息
        stats = network.get_request_stats()
        print(f"请求统计: {stats}")