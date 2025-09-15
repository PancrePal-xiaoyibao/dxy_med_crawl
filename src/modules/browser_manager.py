#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
丁香园爬虫 - 浏览器管理模块

该模块负责浏览器模拟相关功能，包括浏览器启动、页面操作、
JavaScript执行、反爬虫检测规避等。

主要功能:
- 浏览器实例管理
- 页面导航和操作
- JavaScript执行
- 反爬虫检测规避
- 页面截图
- 元素定位和操作

作者: AI Assistant
版本: 1.0.0
创建时间: 2024-01-15
"""

import time
import random
import asyncio
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    from selenium.common.exceptions import (
        TimeoutException, NoSuchElementException, WebDriverException,
        ElementNotInteractableException, StaleElementReferenceException
    )
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from .logger import LoggerManager
from .config import Config
from .cookie_manager import CookieManager


class BrowserManager:
    """
    浏览器管理器
    
    负责浏览器实例的创建、管理和操作，包括反爬虫检测规避。
    """
    
    def __init__(self, config: Config, logger_manager: LoggerManager, cookie_manager: CookieManager):
        """
        初始化浏览器管理器
        
        Args:
            config (Config): 配置管理器实例
            logger_manager (LoggerManager): 日志管理器实例
            cookie_manager (CookieManager): Cookie管理器实例
            
        异常:
            ImportError: 当Selenium未安装时抛出
        """
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium未安装，请运行: pip install selenium")
        
        self.config = config
        self.logger = logger_manager.get_logger('browser_manager')
        self.performance_logger = logger_manager.get_performance_logger()
        self.cookie_manager = cookie_manager
        
        # 浏览器配置
        self.browser_type = getattr(config, 'BROWSER_TYPE', 'chrome')
        self.headless = getattr(config, 'HEADLESS', True)
        self.window_size = getattr(config, 'WINDOW_SIZE', (1920, 1080))
        self.page_load_timeout = getattr(config, 'PAGE_LOAD_TIMEOUT', 30)
        self.implicit_wait = getattr(config, 'IMPLICIT_WAIT', 10)
        
        # 浏览器实例
        self.driver: Optional[webdriver.Remote] = None
        self.wait: Optional[WebDriverWait] = None
        
        # 反爬虫配置
        self.user_agents = getattr(config, 'USER_AGENTS', [])
        self.current_ua_index = 0
        
        # 操作统计
        self.page_loads = 0
        self.element_interactions = 0
        self.js_executions = 0
        
        self.logger.info("浏览器管理器初始化完成")
    
    def _get_chrome_options(self) -> ChromeOptions:
        """
        获取Chrome浏览器选项
        
        Returns:
            ChromeOptions: Chrome选项配置
        """
        options = ChromeOptions()
        
        # 基础选项
        if self.headless:
            options.add_argument('--headless')
        
        options.add_argument(f'--window-size={self.window_size[0]},{self.window_size[1]}')
        
        # 反爬虫选项
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 性能优化
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript')
        
        # User-Agent
        if self.user_agents:
            user_agent = self._get_random_user_agent()
            options.add_argument(f'--user-agent={user_agent}')
        
        # 其他选项
        options.add_argument('--lang=zh-CN')
        options.add_argument('--accept-lang=zh-CN,zh;q=0.9,en;q=0.8')
        
        return options
    
    def _get_firefox_options(self) -> FirefoxOptions:
        """
        获取Firefox浏览器选项
        
        Returns:
            FirefoxOptions: Firefox选项配置
        """
        options = FirefoxOptions()
        
        if self.headless:
            options.add_argument('--headless')
        
        # User-Agent
        if self.user_agents:
            user_agent = self._get_random_user_agent()
            options.set_preference("general.useragent.override", user_agent)
        
        # 其他配置
        options.set_preference("intl.accept_languages", "zh-CN,zh;q=0.9,en;q=0.8")
        
        return options
    
    def _get_random_user_agent(self) -> str:
        """
        获取随机User-Agent
        
        Returns:
            str: 随机选择的User-Agent
        """
        if not self.user_agents:
            return 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        user_agent = self.user_agents[self.current_ua_index]
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
        
        return user_agent
    
    def start_browser(self) -> bool:
        """
        启动浏览器
        
        Returns:
            bool: 启动成功返回True，失败返回False
            
        异常:
            处理浏览器启动异常，记录错误日志
        """
        try:
            self.logger.info(f"启动{self.browser_type}浏览器")
            
            if self.browser_type.lower() == 'chrome':
                options = self._get_chrome_options()
                self.driver = webdriver.Chrome(options=options)
            elif self.browser_type.lower() == 'firefox':
                options = self._get_firefox_options()
                self.driver = webdriver.Firefox(options=options)
            else:
                raise ValueError(f"不支持的浏览器类型: {self.browser_type}")
            
            # 配置等待
            self.driver.implicitly_wait(self.implicit_wait)
            self.driver.set_page_load_timeout(self.page_load_timeout)
            self.wait = WebDriverWait(self.driver, self.implicit_wait)
            
            # 反爬虫脚本
            self._execute_anti_detection_script()
            
            # 加载Cookie
            self._load_cookies()
            
            self.logger.info("浏览器启动成功")
            return True
            
        except Exception as e:
            self.logger.error(f"浏览器启动失败: {str(e)}")
            return False
    
    def _execute_anti_detection_script(self):
        """
        执行反检测脚本
        
        隐藏浏览器自动化特征
        """
        try:
            # 隐藏webdriver属性
            script = """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // 隐藏自动化标识
            window.chrome = {
                runtime: {},
            };
            
            // 修改插件数量
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // 修改语言
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en'],
            });
            """
            
            self.driver.execute_script(script)
            self.logger.debug("反检测脚本执行完成")
            
        except Exception as e:
            self.logger.warning(f"反检测脚本执行失败: {str(e)}")
    
    def _load_cookies(self):
        """
        加载Cookie到浏览器
        """
        try:
            # 先访问主域名以设置Cookie域
            self.driver.get(self.config.BASE_URL)
            time.sleep(2)
            
            # 加载保存的Cookie
            cookies = self.cookie_manager.get_cookies_for_domain(self.config.BASE_URL)
            
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    self.logger.warning(f"添加Cookie失败: {cookie.get('name', 'unknown')}, 错误: {str(e)}")
            
            if cookies:
                self.logger.info(f"加载了 {len(cookies)} 个Cookie")
            
        except Exception as e:
            self.logger.warning(f"加载Cookie失败: {str(e)}")
    
    def navigate_to(self, url: str) -> bool:
        """
        导航到指定URL
        
        Args:
            url (str): 目标URL
            
        Returns:
            bool: 导航成功返回True，失败返回False
        """
        if not self.driver:
            self.logger.error("浏览器未启动")
            return False
        
        try:
            start_time = time.time()
            self.logger.info(f"导航到: {url}")
            
            self.driver.get(url)
            self.page_loads += 1
            
            # 等待页面加载
            self._wait_for_page_load()
            
            # 随机等待
            self._random_wait(1, 3)
            
            duration = time.time() - start_time
            self.logger.info(f"页面加载完成: {url}, 耗时: {duration:.2f}s")
            
            # 保存Cookie
            self._save_cookies()
            
            return True
            
        except TimeoutException:
            self.logger.error(f"页面加载超时: {url}")
            return False
        except Exception as e:
            self.logger.error(f"导航失败: {url}, 错误: {str(e)}")
            return False
    
    def _wait_for_page_load(self, timeout: int = 30):
        """
        等待页面加载完成
        
        Args:
            timeout (int): 超时时间（秒）
        """
        try:
            # 等待document.readyState为complete
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # 等待jQuery加载完成（如果存在）
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda driver: driver.execute_script("return typeof jQuery !== 'undefined' && jQuery.active == 0")
                )
            except:
                pass  # jQuery可能不存在
            
        except TimeoutException:
            self.logger.warning("页面加载等待超时")
    
    def _random_wait(self, min_seconds: float = 1, max_seconds: float = 3):
        """
        随机等待
        
        Args:
            min_seconds (float): 最小等待时间
            max_seconds (float): 最大等待时间
        """
        wait_time = random.uniform(min_seconds, max_seconds)
        time.sleep(wait_time)
    
    def find_element(self, by: By, value: str, timeout: int = 10) -> Optional[Any]:
        """
        查找元素
        
        Args:
            by (By): 定位方式
            value (str): 定位值
            timeout (int): 超时时间
            
        Returns:
            Optional[WebElement]: 找到的元素，失败返回None
        """
        if not self.driver:
            self.logger.error("浏览器未启动")
            return None
        
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, value)))
            return element
        except TimeoutException:
            self.logger.warning(f"元素查找超时: {by}={value}")
            return None
        except Exception as e:
            self.logger.error(f"元素查找失败: {by}={value}, 错误: {str(e)}")
            return None
    
    def find_elements(self, by: By, value: str) -> List[Any]:
        """
        查找多个元素
        
        Args:
            by (By): 定位方式
            value (str): 定位值
            
        Returns:
            List[WebElement]: 找到的元素列表
        """
        if not self.driver:
            self.logger.error("浏览器未启动")
            return []
        
        try:
            elements = self.driver.find_elements(by, value)
            return elements
        except Exception as e:
            self.logger.error(f"元素查找失败: {by}={value}, 错误: {str(e)}")
            return []
    
    def click_element(self, element) -> bool:
        """
        点击元素
        
        Args:
            element: 要点击的元素
            
        Returns:
            bool: 点击成功返回True，失败返回False
        """
        try:
            # 滚动到元素可见
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            self._random_wait(0.5, 1.5)
            
            # 等待元素可点击
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(element))
            
            # 点击元素
            element.click()
            self.element_interactions += 1
            
            self._random_wait(1, 2)
            return True
            
        except Exception as e:
            self.logger.error(f"点击元素失败: {str(e)}")
            return False
    
    def input_text(self, element, text: str) -> bool:
        """
        在元素中输入文本
        
        Args:
            element: 输入元素
            text (str): 要输入的文本
            
        Returns:
            bool: 输入成功返回True，失败返回False
        """
        try:
            # 清空现有内容
            element.clear()
            self._random_wait(0.5, 1)
            
            # 模拟人工输入
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            self.element_interactions += 1
            self._random_wait(0.5, 1.5)
            return True
            
        except Exception as e:
            self.logger.error(f"文本输入失败: {str(e)}")
            return False
    
    def execute_script(self, script: str, *args) -> Any:
        """
        执行JavaScript脚本
        
        Args:
            script (str): JavaScript代码
            *args: 脚本参数
            
        Returns:
            Any: 脚本执行结果
        """
        if not self.driver:
            self.logger.error("浏览器未启动")
            return None
        
        try:
            result = self.driver.execute_script(script, *args)
            self.js_executions += 1
            return result
        except Exception as e:
            self.logger.error(f"脚本执行失败: {str(e)}")
            return None
    
    def get_page_source(self) -> Optional[str]:
        """
        获取页面源码
        
        Returns:
            Optional[str]: 页面源码，失败返回None
        """
        if not self.driver:
            self.logger.error("浏览器未启动")
            return None
        
        try:
            return self.driver.page_source
        except Exception as e:
            self.logger.error(f"获取页面源码失败: {str(e)}")
            return None
    
    def take_screenshot(self, file_path: str) -> bool:
        """
        截取页面截图
        
        Args:
            file_path (str): 截图保存路径
            
        Returns:
            bool: 截图成功返回True，失败返回False
        """
        if not self.driver:
            self.logger.error("浏览器未启动")
            return False
        
        try:
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            success = self.driver.save_screenshot(file_path)
            if success:
                self.logger.info(f"截图保存成功: {file_path}")
            else:
                self.logger.error(f"截图保存失败: {file_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"截图失败: {str(e)}")
            return False
    
    def _save_cookies(self):
        """
        保存当前Cookie
        """
        try:
            if self.driver:
                cookies = self.driver.get_cookies()
                if cookies:
                    # 转换为requests格式并保存
                    import requests
                    session = requests.Session()
                    
                    for cookie in cookies:
                        session.cookies.set(
                            name=cookie['name'],
                            value=cookie['value'],
                            domain=cookie.get('domain'),
                            path=cookie.get('path', '/'),
                            secure=cookie.get('secure', False)
                        )
                    
                    user_agent = self.driver.execute_script("return navigator.userAgent;")
                    self.cookie_manager.save_cookies(session, user_agent)
                    
        except Exception as e:
            self.logger.warning(f"保存Cookie失败: {str(e)}")
    
    def search_drugs(self, keyword: str) -> bool:
        """
        搜索药品
        
        Args:
            keyword (str): 搜索关键词
            
        Returns:
            bool: 搜索成功返回True，失败返回False
        """
        try:
            # 构建搜索URL
            search_url = self.config.get_search_url(keyword)
            
            # 导航到搜索页面
            if not self.navigate_to(search_url):
                return False
            
            # 等待搜索结果加载
            self._wait_for_page_load()
            
            self.logger.info(f"药品搜索完成: {keyword}")
            return True
            
        except Exception as e:
            self.logger.error(f"药品搜索失败: {keyword}, 错误: {str(e)}")
            return False
    
    def get_browser_stats(self) -> Dict[str, Any]:
        """
        获取浏览器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            'browser_type': self.browser_type,
            'headless': self.headless,
            'page_loads': self.page_loads,
            'element_interactions': self.element_interactions,
            'js_executions': self.js_executions,
            'current_url': None,
            'window_size': None,
            'cookies_count': 0
        }
        
        if self.driver:
            try:
                stats['current_url'] = self.driver.current_url
                stats['window_size'] = self.driver.get_window_size()
                stats['cookies_count'] = len(self.driver.get_cookies())
            except:
                pass
        
        return stats
    
    def close_browser(self):
        """
        关闭浏览器
        
        清理资源，关闭浏览器实例
        """
        try:
            if self.driver:
                # 保存最终Cookie
                self._save_cookies()
                
                # 关闭浏览器
                self.driver.quit()
                self.driver = None
                self.wait = None
                
                self.logger.info("浏览器已关闭")
                
        except Exception as e:
            self.logger.error(f"关闭浏览器失败: {str(e)}")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close_browser()