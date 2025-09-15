#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
丁香园爬虫 - Cookie管理模块

该模块负责处理Cookie的持久化管理，包括Cookie的加载、保存、
验证、刷新等功能。

主要功能:
- Cookie文件读写
- Cookie格式验证
- Cookie过期检测
- Cookie自动刷新
- Cookie有效性验证

作者: AI Assistant
版本: 1.0.0
创建时间: 2024-01-15
"""

import json
import os
import time
import requests
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

from .logger import LoggerManager
from .config import Config


class CookieManager:
    """
    Cookie管理器
    
    负责处理Cookie的持久化管理，包括加载、保存、验证、刷新等功能。
    """
    
    def __init__(self, config: Config, logger_manager: LoggerManager):
        """
        初始化Cookie管理器
        
        Args:
            config (Config): 配置管理器实例
            logger_manager (LoggerManager): 日志管理器实例
        """
        self.config = config
        self.logger = logger_manager.get_logger('cookie_manager')
        
        # Cookie配置
        self.cookie_file = os.path.join(self.config.DATA_DIR, 'cookies.json')
        self.expire_hours = self.config.COOKIE_EXPIRE_HOURS
        self.auto_refresh = self.config.AUTO_REFRESH_COOKIES
        self.validation_enabled = self.config.COOKIE_VALIDATION_ENABLED
        self.retry_attempts = self.config.COOKIE_RETRY_ATTEMPTS
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.cookie_file), exist_ok=True)
        
        self.logger.info("Cookie管理器初始化完成")
    
    def load_cookies(self, session: requests.Session) -> bool:
        """
        从文件加载Cookie到会话中
        
        Args:
            session (requests.Session): 请求会话对象
            
        Returns:
            bool: 加载成功返回True，失败返回False
            
        异常:
            处理文件读取异常，记录错误日志
        """
        try:
            if not os.path.exists(self.cookie_file):
                self.logger.info("Cookie文件不存在，将创建新文件")
                self._create_empty_cookie_file()
                return False
            
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)
            
            # 检查Cookie文件格式
            if not self._validate_cookie_format(cookie_data):
                self.logger.warning("Cookie文件格式无效，重新创建")
                self._create_empty_cookie_file()
                return False
            
            # 检查Cookie是否过期
            if self._is_cookies_expired(cookie_data):
                self.logger.info("Cookie已过期")
                if self.auto_refresh:
                    self.logger.info("尝试刷新Cookie")
                    return self._refresh_cookies(session)
                else:
                    return False
            
            # 加载Cookie到会话
            cookies_loaded = 0
            for cookie_dict in cookie_data.get('cookies', []):
                try:
                    session.cookies.set(
                        name=cookie_dict['name'],
                        value=cookie_dict['value'],
                        domain=cookie_dict.get('domain'),
                        path=cookie_dict.get('path', '/'),
                        secure=cookie_dict.get('secure', False)
                    )
                    cookies_loaded += 1
                except Exception as e:
                    self.logger.warning(f"加载Cookie失败: {cookie_dict.get('name', 'unknown')}, 错误: {str(e)}")
            
            # 设置User-Agent
            if 'user_agent' in cookie_data:
                session.headers['User-Agent'] = cookie_data['user_agent']
            
            self.logger.info(f"成功加载 {cookies_loaded} 个Cookie")
            
            # 验证Cookie有效性
            if self.validation_enabled and cookies_loaded > 0:
                if not self._validate_cookies(session):
                    self.logger.warning("Cookie验证失败，可能需要刷新")
                    if self.auto_refresh:
                        return self._refresh_cookies(session)
                    return False
            
            return cookies_loaded > 0
            
        except Exception as e:
            self.logger.error(f"加载Cookie失败: {str(e)}")
            return False
    
    def save_cookies(self, session: requests.Session, user_agent: str = None) -> bool:
        """
        保存会话中的Cookie到文件
        
        Args:
            session (requests.Session): 请求会话对象
            user_agent (str, optional): 用户代理字符串
            
        Returns:
            bool: 保存成功返回True，失败返回False
            
        异常:
            处理文件写入异常，记录错误日志
        """
        try:
            cookies_list = []
            for cookie in session.cookies:
                cookie_dict = {
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path,
                    'secure': cookie.secure,
                    'expires': cookie.expires
                }
                cookies_list.append(cookie_dict)
            
            cookie_data = {
                'cookies': cookies_list,
                'last_update': time.time(),
                'user_agent': user_agent or session.headers.get('User-Agent', ''),
                'expire_hours': self.expire_hours
            }
            
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookie_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"成功保存 {len(cookies_list)} 个Cookie")
            return True
            
        except Exception as e:
            self.logger.error(f"保存Cookie失败: {str(e)}")
            return False
    
    def _validate_cookie_format(self, cookie_data: Dict[str, Any]) -> bool:
        """
        验证Cookie文件格式
        
        Args:
            cookie_data (Dict[str, Any]): Cookie数据
            
        Returns:
            bool: 格式正确返回True，错误返回False
        """
        required_fields = ['cookies', 'last_update']
        
        if not isinstance(cookie_data, dict):
            return False
        
        for field in required_fields:
            if field not in cookie_data:
                return False
        
        if not isinstance(cookie_data['cookies'], list):
            return False
        
        return True
    
    def _is_cookies_expired(self, cookie_data: Dict[str, Any]) -> bool:
        """
        检查Cookie是否过期
        
        Args:
            cookie_data (Dict[str, Any]): Cookie数据
            
        Returns:
            bool: 过期返回True，未过期返回False
        """
        last_update = cookie_data.get('last_update', 0)
        expire_hours = cookie_data.get('expire_hours', self.expire_hours)
        
        current_time = time.time()
        expire_time = last_update + (expire_hours * 3600)
        
        return current_time > expire_time
    
    def _validate_cookies(self, session: requests.Session) -> bool:
        """
        验证Cookie有效性
        
        Args:
            session (requests.Session): 请求会话对象
            
        Returns:
            bool: 有效返回True，无效返回False
        """
        try:
            # 发送测试请求验证Cookie
            test_url = f"{self.config.BASE_URL}/pc"
            response = session.get(test_url, timeout=10)
            
            # 检查响应状态
            if response.status_code == 200:
                # 可以添加更多验证逻辑，比如检查页面内容
                return True
            else:
                self.logger.warning(f"Cookie验证失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Cookie验证异常: {str(e)}")
            return False
    
    def _refresh_cookies(self, session: requests.Session) -> bool:
        """
        刷新Cookie
        
        Args:
            session (requests.Session): 请求会话对象
            
        Returns:
            bool: 刷新成功返回True，失败返回False
        """
        try:
            self.logger.info("开始刷新Cookie")
            
            # 清除现有Cookie
            session.cookies.clear()
            
            # 访问首页获取新Cookie
            response = session.get(self.config.BASE_URL, timeout=30)
            
            if response.status_code == 200:
                # 保存新Cookie
                user_agent = session.headers.get('User-Agent', '')
                if self.save_cookies(session, user_agent):
                    self.logger.info("Cookie刷新成功")
                    return True
                else:
                    self.logger.error("Cookie刷新后保存失败")
                    return False
            else:
                self.logger.error(f"Cookie刷新失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Cookie刷新异常: {str(e)}")
            return False
    
    def _create_empty_cookie_file(self):
        """
        创建空的Cookie文件
        
        异常:
            处理文件创建异常，记录错误日志
        """
        try:
            empty_data = {
                'cookies': [],
                'last_update': time.time(),
                'user_agent': '',
                'expire_hours': self.expire_hours
            }
            
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(empty_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("创建空Cookie文件成功")
            
        except Exception as e:
            self.logger.error(f"创建Cookie文件失败: {str(e)}")
    
    def clear_cookies(self, session: requests.Session = None) -> bool:
        """
        清除Cookie
        
        Args:
            session (requests.Session, optional): 请求会话对象
            
        Returns:
            bool: 清除成功返回True，失败返回False
        """
        try:
            # 清除会话中的Cookie
            if session:
                session.cookies.clear()
            
            # 清除文件中的Cookie
            self._create_empty_cookie_file()
            
            self.logger.info("Cookie清除成功")
            return True
            
        except Exception as e:
            self.logger.error(f"清除Cookie失败: {str(e)}")
            return False
    
    def get_cookie_info(self) -> Dict[str, Any]:
        """
        获取Cookie信息
        
        Returns:
            Dict[str, Any]: Cookie信息字典
        """
        try:
            if not os.path.exists(self.cookie_file):
                return {
                    'exists': False,
                    'count': 0,
                    'last_update': None,
                    'expired': True
                }
            
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)
            
            return {
                'exists': True,
                'count': len(cookie_data.get('cookies', [])),
                'last_update': cookie_data.get('last_update'),
                'expired': self._is_cookies_expired(cookie_data),
                'user_agent': cookie_data.get('user_agent', ''),
                'file_path': self.cookie_file
            }
            
        except Exception as e:
            self.logger.error(f"获取Cookie信息失败: {str(e)}")
            return {
                'exists': False,
                'count': 0,
                'last_update': None,
                'expired': True,
                'error': str(e)
            }