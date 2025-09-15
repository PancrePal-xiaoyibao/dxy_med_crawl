#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
丁香园爬虫 - 代理管理模块

该模块负责代理IP的管理，包括代理池维护、代理验证、
代理轮换、失效检测等功能。

主要功能:
- 代理池管理
- 代理验证和测试
- 代理轮换策略
- 失效代理检测和移除
- 代理性能统计
- 代理配置管理

作者: AI Assistant
版本: 1.0.0
创建时间: 2024-01-15
"""

import time
import random
import requests
import threading
from typing import Optional, Dict, Any, List, Tuple, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

from .logger import LoggerManager
from .config import Config


@dataclass
class ProxyInfo:
    """
    代理信息数据类
    
    Attributes:
        host (str): 代理主机
        port (int): 代理端口
        username (str): 用户名（可选）
        password (str): 密码（可选）
        protocol (str): 协议类型（http/https/socks5）
        response_time (float): 响应时间
        success_count (int): 成功次数
        failure_count (int): 失败次数
        last_used (float): 最后使用时间
        last_check (float): 最后检查时间
        is_active (bool): 是否可用
    """
    host: str
    port: int
    username: str = ''
    password: str = ''
    protocol: str = 'http'
    response_time: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    last_used: float = 0.0
    last_check: float = 0.0
    is_active: bool = True
    
    @property
    def url(self) -> str:
        """
        获取代理URL
        
        Returns:
            str: 代理URL
        """
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        else:
            return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def success_rate(self) -> float:
        """
        获取成功率
        
        Returns:
            float: 成功率（0-1）
        """
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total
    
    def __str__(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"


class ProxyManager:
    """
    代理管理器
    
    负责代理IP的管理和轮换，提供高可用的代理服务。
    """
    
    def __init__(self, config: Config, logger_manager: LoggerManager):
        """
        初始化代理管理器
        
        Args:
            config (Config): 配置管理器实例
            logger_manager (LoggerManager): 日志管理器实例
        """
        self.config = config
        self.logger = logger_manager.get_logger('proxy_manager')
        self.performance_logger = logger_manager.get_performance_logger()
        
        # 代理配置
        self.enable_proxy = getattr(config, 'ENABLE_PROXY', False)
        self.proxy_list = getattr(config, 'PROXY_LIST', [])
        self.proxy_check_url = getattr(config, 'PROXY_CHECK_URL', 'http://httpbin.org/ip')
        self.proxy_timeout = getattr(config, 'PROXY_TIMEOUT', 10)
        self.proxy_check_interval = getattr(config, 'PROXY_CHECK_INTERVAL', 300)  # 5分钟
        self.max_failure_count = getattr(config, 'MAX_PROXY_FAILURES', 5)
        
        # 代理池
        self.proxy_pool: List[ProxyInfo] = []
        self.current_proxy_index = 0
        self.proxy_lock = threading.Lock()
        
        # 统计信息
        self.total_requests = 0
        self.proxy_switches = 0
        self.failed_proxies = 0
        
        # 初始化代理池
        if self.enable_proxy:
            self._initialize_proxy_pool()
            # 启动代理检查线程
            self._start_proxy_checker()
        
        self.logger.info(f"代理管理器初始化完成，代理功能: {'启用' if self.enable_proxy else '禁用'}")
    
    def _initialize_proxy_pool(self):
        """
        初始化代理池
        
        从配置中加载代理列表并验证可用性
        """
        if not self.proxy_list:
            self.logger.warning("未配置代理列表")
            return
        
        self.logger.info(f"初始化代理池，共 {len(self.proxy_list)} 个代理")
        
        for proxy_config in self.proxy_list:
            try:
                proxy_info = self._parse_proxy_config(proxy_config)
                if proxy_info:
                    self.proxy_pool.append(proxy_info)
            except Exception as e:
                self.logger.error(f"解析代理配置失败: {proxy_config}, 错误: {str(e)}")
        
        if self.proxy_pool:
            self.logger.info(f"代理池初始化完成，有效代理: {len(self.proxy_pool)} 个")
            # 验证代理可用性
            self._validate_all_proxies()
        else:
            self.logger.warning("代理池为空")
    
    def _parse_proxy_config(self, proxy_config: Union[str, Dict[str, Any]]) -> Optional[ProxyInfo]:
        """
        解析代理配置
        
        Args:
            proxy_config: 代理配置（字符串或字典）
            
        Returns:
            Optional[ProxyInfo]: 解析后的代理信息
        """
        try:
            if isinstance(proxy_config, str):
                # 解析URL格式: protocol://[username:password@]host:port
                parsed = urlparse(proxy_config)
                
                return ProxyInfo(
                    host=parsed.hostname,
                    port=parsed.port,
                    username=parsed.username or '',
                    password=parsed.password or '',
                    protocol=parsed.scheme or 'http'
                )
            
            elif isinstance(proxy_config, dict):
                return ProxyInfo(
                    host=proxy_config['host'],
                    port=proxy_config['port'],
                    username=proxy_config.get('username', ''),
                    password=proxy_config.get('password', ''),
                    protocol=proxy_config.get('protocol', 'http')
                )
            
            else:
                self.logger.error(f"不支持的代理配置格式: {type(proxy_config)}")
                return None
                
        except Exception as e:
            self.logger.error(f"解析代理配置失败: {proxy_config}, 错误: {str(e)}")
            return None
    
    def _validate_all_proxies(self):
        """
        验证所有代理的可用性
        
        使用多线程并发验证以提高效率
        """
        if not self.proxy_pool:
            return
        
        self.logger.info("开始验证代理可用性")
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_proxy = {
                executor.submit(self._check_proxy, proxy): proxy 
                for proxy in self.proxy_pool
            }
            
            for future in as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    is_valid = future.result()
                    proxy.is_active = is_valid
                    proxy.last_check = time.time()
                    
                    if is_valid:
                        self.logger.debug(f"代理验证成功: {proxy}")
                    else:
                        self.logger.warning(f"代理验证失败: {proxy}")
                        
                except Exception as e:
                    self.logger.error(f"代理验证异常: {proxy}, 错误: {str(e)}")
                    proxy.is_active = False
        
        active_count = sum(1 for proxy in self.proxy_pool if proxy.is_active)
        self.logger.info(f"代理验证完成，可用代理: {active_count}/{len(self.proxy_pool)}")
    
    def _check_proxy(self, proxy: ProxyInfo, timeout: Optional[int] = None) -> bool:
        """
        检查单个代理的可用性
        
        Args:
            proxy (ProxyInfo): 代理信息
            timeout (Optional[int]): 超时时间
            
        Returns:
            bool: 代理可用返回True，不可用返回False
        """
        if timeout is None:
            timeout = self.proxy_timeout
        
        try:
            start_time = time.time()
            
            proxies = {
                'http': proxy.url,
                'https': proxy.url
            }
            
            response = requests.get(
                self.proxy_check_url,
                proxies=proxies,
                timeout=timeout,
                verify=False
            )
            
            response_time = time.time() - start_time
            proxy.response_time = response_time
            
            if response.status_code == 200:
                proxy.success_count += 1
                return True
            else:
                proxy.failure_count += 1
                return False
                
        except Exception as e:
            proxy.failure_count += 1
            self.logger.debug(f"代理检查失败: {proxy}, 错误: {str(e)}")
            return False
    
    def _start_proxy_checker(self):
        """
        启动代理检查线程
        
        定期检查代理可用性
        """
        def check_proxies():
            while True:
                try:
                    time.sleep(self.proxy_check_interval)
                    if self.proxy_pool:
                        self.logger.debug("开始定期代理检查")
                        self._validate_all_proxies()
                        self._cleanup_failed_proxies()
                except Exception as e:
                    self.logger.error(f"代理检查线程异常: {str(e)}")
        
        if self.proxy_pool:
            checker_thread = threading.Thread(target=check_proxies, daemon=True)
            checker_thread.start()
            self.logger.info("代理检查线程已启动")
    
    def _cleanup_failed_proxies(self):
        """
        清理失效的代理
        
        移除失败次数过多的代理
        """
        with self.proxy_lock:
            before_count = len(self.proxy_pool)
            
            self.proxy_pool = [
                proxy for proxy in self.proxy_pool
                if proxy.failure_count < self.max_failure_count or proxy.success_count > 0
            ]
            
            after_count = len(self.proxy_pool)
            removed_count = before_count - after_count
            
            if removed_count > 0:
                self.failed_proxies += removed_count
                self.logger.info(f"清理了 {removed_count} 个失效代理，剩余: {after_count} 个")
    
    def get_proxy(self) -> Optional[Dict[str, str]]:
        """
        获取可用的代理
        
        Returns:
            Optional[Dict[str, str]]: 代理配置字典，无可用代理返回None
        """
        if not self.enable_proxy or not self.proxy_pool:
            return None
        
        with self.proxy_lock:
            # 过滤可用代理
            active_proxies = [proxy for proxy in self.proxy_pool if proxy.is_active]
            
            if not active_proxies:
                self.logger.warning("没有可用的代理")
                return None
            
            # 选择代理（轮换策略）
            proxy = self._select_proxy(active_proxies)
            
            if proxy:
                proxy.last_used = time.time()
                self.total_requests += 1
                
                return {
                    'http': proxy.url,
                    'https': proxy.url
                }
            
            return None
    
    def _select_proxy(self, active_proxies: List[ProxyInfo]) -> Optional[ProxyInfo]:
        """
        选择代理
        
        Args:
            active_proxies (List[ProxyInfo]): 可用代理列表
            
        Returns:
            Optional[ProxyInfo]: 选中的代理
        """
        if not active_proxies:
            return None
        
        # 轮换策略
        proxy = active_proxies[self.current_proxy_index % len(active_proxies)]
        self.current_proxy_index += 1
        
        return proxy
    
    def report_proxy_result(self, proxy_url: str, success: bool):
        """
        报告代理使用结果
        
        Args:
            proxy_url (str): 代理URL
            success (bool): 是否成功
        """
        if not self.enable_proxy:
            return
        
        with self.proxy_lock:
            for proxy in self.proxy_pool:
                if proxy.url == proxy_url:
                    if success:
                        proxy.success_count += 1
                    else:
                        proxy.failure_count += 1
                        
                        # 如果失败次数过多，标记为不可用
                        if proxy.failure_count >= self.max_failure_count:
                            proxy.is_active = False
                            self.logger.warning(f"代理失败次数过多，标记为不可用: {proxy}")
                    
                    break
    
    def switch_proxy(self) -> Optional[Dict[str, str]]:
        """
        切换到下一个代理
        
        Returns:
            Optional[Dict[str, str]]: 新的代理配置
        """
        if not self.enable_proxy:
            return None
        
        self.proxy_switches += 1
        self.logger.info("切换代理")
        
        return self.get_proxy()
    
    def add_proxy(self, proxy_config: Union[str, Dict[str, Any]]) -> bool:
        """
        添加新代理
        
        Args:
            proxy_config: 代理配置
            
        Returns:
            bool: 添加成功返回True，失败返回False
        """
        try:
            proxy_info = self._parse_proxy_config(proxy_config)
            if not proxy_info:
                return False
            
            # 检查是否已存在
            with self.proxy_lock:
                for existing_proxy in self.proxy_pool:
                    if (existing_proxy.host == proxy_info.host and 
                        existing_proxy.port == proxy_info.port):
                        self.logger.warning(f"代理已存在: {proxy_info}")
                        return False
                
                # 验证代理可用性
                if self._check_proxy(proxy_info):
                    proxy_info.is_active = True
                    self.proxy_pool.append(proxy_info)
                    self.logger.info(f"添加代理成功: {proxy_info}")
                    return True
                else:
                    self.logger.warning(f"代理验证失败，未添加: {proxy_info}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"添加代理失败: {proxy_config}, 错误: {str(e)}")
            return False
    
    def remove_proxy(self, host: str, port: int) -> bool:
        """
        移除代理
        
        Args:
            host (str): 代理主机
            port (int): 代理端口
            
        Returns:
            bool: 移除成功返回True，失败返回False
        """
        with self.proxy_lock:
            for i, proxy in enumerate(self.proxy_pool):
                if proxy.host == host and proxy.port == port:
                    removed_proxy = self.proxy_pool.pop(i)
                    self.logger.info(f"移除代理: {removed_proxy}")
                    return True
            
            self.logger.warning(f"未找到要移除的代理: {host}:{port}")
            return False
    
    def get_proxy_stats(self) -> Dict[str, Any]:
        """
        获取代理统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self.proxy_lock:
            active_count = sum(1 for proxy in self.proxy_pool if proxy.is_active)
            total_success = sum(proxy.success_count for proxy in self.proxy_pool)
            total_failure = sum(proxy.failure_count for proxy in self.proxy_pool)
            
            stats = {
                'enabled': self.enable_proxy,
                'total_proxies': len(self.proxy_pool),
                'active_proxies': active_count,
                'inactive_proxies': len(self.proxy_pool) - active_count,
                'total_requests': self.total_requests,
                'proxy_switches': self.proxy_switches,
                'failed_proxies': self.failed_proxies,
                'total_success': total_success,
                'total_failure': total_failure,
                'overall_success_rate': total_success / (total_success + total_failure) if (total_success + total_failure) > 0 else 0
            }
            
            # 添加每个代理的详细信息
            stats['proxy_details'] = []
            for proxy in self.proxy_pool:
                stats['proxy_details'].append({
                    'host': proxy.host,
                    'port': proxy.port,
                    'protocol': proxy.protocol,
                    'is_active': proxy.is_active,
                    'success_count': proxy.success_count,
                    'failure_count': proxy.failure_count,
                    'success_rate': proxy.success_rate,
                    'response_time': proxy.response_time,
                    'last_used': proxy.last_used,
                    'last_check': proxy.last_check
                })
            
            return stats
    
    def reset_proxy_stats(self):
        """
        重置代理统计信息
        """
        with self.proxy_lock:
            for proxy in self.proxy_pool:
                proxy.success_count = 0
                proxy.failure_count = 0
                proxy.response_time = 0.0
                proxy.last_used = 0.0
                proxy.last_check = 0.0
            
            self.total_requests = 0
            self.proxy_switches = 0
            self.failed_proxies = 0
            
            self.logger.info("代理统计信息已重置")
    
    def close(self):
        """
        关闭代理管理器
        
        清理资源
        """
        try:
            self.logger.info("代理管理器已关闭")
        except Exception as e:
            self.logger.error(f"关闭代理管理器失败: {str(e)}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()