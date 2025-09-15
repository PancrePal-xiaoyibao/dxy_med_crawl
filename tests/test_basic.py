#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础功能测试脚本

测试各个模块的基本功能，确保系统正常运行。

作者: AI Assistant
创建时间: 2024
版本: 1.0.0
"""

import sys
import os
import unittest
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.modules.config import Config
from src.modules.logger import LogManager
from src.modules.network import NetworkManager
from src.modules.parser import PageParser
from src.modules.processor import DataProcessor
from src.modules.jina_processor import JinaProcessor


class TestConfig(unittest.TestCase):
    """配置管理模块测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config = Config()
    
    def test_config_initialization(self):
        """测试配置初始化"""
        self.assertIsNotNone(self.config)
        self.assertIsInstance(self.config.base_url, str)
        self.assertIsInstance(self.config.jina_base_url, str)
        self.assertIsInstance(self.config.output_dir, str)
    
    def test_get_full_url(self):
        """测试URL构建"""
        path = "/test"
        full_url = self.config.get_full_url(path)
        self.assertTrue(full_url.startswith("http"))
        self.assertIn(path, full_url)
    
    def test_get_output_path(self):
        """测试输出路径构建"""
        filename = "test.json"
        output_path = self.config.get_output_path(filename)
        self.assertTrue(output_path.endswith(filename))


class TestLogger(unittest.TestCase):
    """日志管理模块测试"""
    
    def setUp(self):
        """测试前准备"""
        self.log_manager = LogManager("test_logger")
    
    def test_logger_initialization(self):
        """测试日志器初始化"""
        self.assertIsNotNone(self.log_manager)
        self.assertIsNotNone(self.log_manager.logger)
    
    def test_logging_methods(self):
        """测试日志记录方法"""
        # 测试各种日志级别
        self.log_manager.info("测试信息日志")
        self.log_manager.warning("测试警告日志")
        self.log_manager.error("测试错误日志")
        self.log_manager.debug("测试调试日志")
        
        # 如果没有异常抛出，则测试通过
        self.assertTrue(True)
    
    def test_performance_logging(self):
        """测试性能日志"""
        perf_logger = self.log_manager.get_performance_logger()
        self.assertIsNotNone(perf_logger)
        
        # 测试性能记录
        perf_logger.log_request("test_url", 200, 0.5, 1024)
        self.assertTrue(True)


class TestNetworkManager(unittest.TestCase):
    """网络请求模块测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config = Config()
        self.network = NetworkManager(self.config)
    
    def test_network_initialization(self):
        """测试网络管理器初始化"""
        self.assertIsNotNone(self.network)
        self.assertIsNotNone(self.network.session)
    
    def test_user_agent_rotation(self):
        """测试User-Agent轮换"""
        ua1 = self.network._get_random_user_agent()
        ua2 = self.network._get_random_user_agent()
        
        # User-Agent应该是字符串
        self.assertIsInstance(ua1, str)
        self.assertIsInstance(ua2, str)
        self.assertTrue(len(ua1) > 0)
        self.assertTrue(len(ua2) > 0)
    
    def test_rate_limiting(self):
        """测试请求频率控制"""
        import time
        start_time = time.time()
        
        # 连续两次调用应该有延迟
        self.network._apply_rate_limit()
        self.network._apply_rate_limit()
        
        elapsed = time.time() - start_time
        # 应该有一定的延迟（至少0.5秒）
        self.assertGreaterEqual(elapsed, 0.5)


class TestPageParser(unittest.TestCase):
    """页面解析模块测试"""
    
    def setUp(self):
        """测试前准备"""
        self.parser = PageParser()
    
    def test_parser_initialization(self):
        """测试解析器初始化"""
        self.assertIsNotNone(self.parser)
    
    def test_clean_text(self):
        """测试文本清理功能"""
        dirty_text = "  测试文本\n\t  带有空格  \r\n  "
        clean_text = self.parser._clean_text(dirty_text)
        
        self.assertEqual(clean_text, "测试文本 带有空格")
    
    def test_parse_search_results_with_sample_html(self):
        """测试搜索结果解析（使用示例HTML）"""
        sample_html = """
        <html>
        <body>
            <div class="drug-card">
                <h3><a href="/drug/123">测试药物</a></h3>
                <p>药物描述</p>
            </div>
        </body>
        </html>
        """
        
        results = self.parser.parse_search_results(sample_html, "测试")
        
        # 结果应该是列表
        self.assertIsInstance(results, list)


class TestDataProcessor(unittest.TestCase):
    """数据处理模块测试"""
    
    def setUp(self):
        """测试前准备"""
        self.processor = DataProcessor()
    
    def test_processor_initialization(self):
        """测试处理器初始化"""
        self.assertIsNotNone(self.processor)
    
    def test_clean_drug_name(self):
        """测试药物名称清理"""
        dirty_name = "  阿司匹林片（规格：100mg）  "
        clean_name = self.processor._clean_drug_name(dirty_name)
        
        self.assertEqual(clean_name, "阿司匹林片")
    
    def test_extract_specifications(self):
        """测试规格提取"""
        text = "规格：100mg×30片/盒"
        specs = self.processor._extract_specifications(text)
        
        self.assertIsInstance(specs, list)
        if specs:
            self.assertIn("100mg", specs[0])


class TestJinaProcessor(unittest.TestCase):
    """Jina AI处理模块测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config = Config()
        self.jina_processor = JinaProcessor(self.config)
    
    def test_jina_initialization(self):
        """测试Jina处理器初始化"""
        self.assertIsNotNone(self.jina_processor)
        self.assertIsNotNone(self.jina_processor.config)
    
    def test_build_jina_url(self):
        """测试Jina URL构建"""
        original_url = "https://example.com/drug/123"
        jina_url = self.jina_processor._build_jina_url(original_url)
        
        self.assertTrue(jina_url.startswith("https://r.jina.ai/"))
        self.assertIn(original_url, jina_url)
    
    def test_extract_drug_info_from_text(self):
        """测试从文本提取药物信息"""
        sample_text = """
        药品名称：阿司匹林片
        规格：100mg×30片/盒
        生产厂家：某某制药有限公司
        适应症：用于解热镇痛
        """
        
        drug_info = self.jina_processor._extract_drug_info_from_text(sample_text)
        
        self.assertIsInstance(drug_info, dict)
        self.assertIn("name", drug_info)
        self.assertIn("specifications", drug_info)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config = Config()
        self.log_manager = LogManager("integration_test")
        self.network = NetworkManager(self.config)
        self.parser = PageParser()
        self.processor = DataProcessor()
        self.jina_processor = JinaProcessor(self.config)
    
    def test_all_modules_initialization(self):
        """测试所有模块初始化"""
        self.assertIsNotNone(self.config)
        self.assertIsNotNone(self.log_manager)
        self.assertIsNotNone(self.network)
        self.assertIsNotNone(self.parser)
        self.assertIsNotNone(self.processor)
        self.assertIsNotNone(self.jina_processor)
    
    def test_config_integration(self):
        """测试配置集成"""
        # 测试配置是否正确传递给各个模块
        self.assertEqual(self.network.config, self.config)
        self.assertEqual(self.jina_processor.config, self.config)
    
    def test_directory_creation(self):
        """测试目录创建"""
        # 测试输出目录是否存在
        output_dir = Path(self.config.output_dir)
        self.assertTrue(output_dir.exists())
        
        # 测试日志目录是否存在
        logs_dir = Path(self.config.logs_dir)
        self.assertTrue(logs_dir.exists())


class TestAsyncFunctions(unittest.TestCase):
    """异步功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config = Config()
        self.network = NetworkManager(self.config)
    
    def test_async_session_creation(self):
        """测试异步会话创建"""
        async def test_session():
            async_session = self.network._create_async_session()
            self.assertIsNotNone(async_session)
            await async_session.close()
        
        # 运行异步测试
        asyncio.run(test_session())


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestConfig,
        TestLogger,
        TestNetworkManager,
        TestPageParser,
        TestDataProcessor,
        TestJinaProcessor,
        TestIntegration,
        TestAsyncFunctions
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 返回测试结果
    return result.wasSuccessful()


if __name__ == "__main__":
    print("开始运行基础功能测试...")
    print("=" * 50)
    
    success = run_tests()
    
    print("=" * 50)
    if success:
        print("✅ 所有测试通过！")
        sys.exit(0)
    else:
        print("❌ 部分测试失败！")
        sys.exit(1)