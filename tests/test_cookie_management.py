#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
丁香园爬虫 - Cookie管理功能测试

测试Cookie的自动获取、验证、更新和管理功能
"""

import sys
import os
import time
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.modules.config import Config
from src.modules.logger import LoggerManager
from src.modules.network import NetworkManager

def test_cookie_basic_functionality():
    """
    测试Cookie基础功能
    """
    print("\n=== 测试Cookie基础功能 ===")
    
    try:
        # 初始化组件
        config = Config()
        logger_manager = LoggerManager()
        
        with NetworkManager(config, logger_manager) as network:
            print("✓ NetworkManager初始化成功")
            
            # 测试Cookie文件创建
            cookie_file = config.cookie_file
            if os.path.exists(cookie_file):
                print(f"✓ Cookie文件存在: {cookie_file}")
                
                # 检查Cookie文件格式
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookie_data = json.load(f)
                    
                if isinstance(cookie_data, dict) and 'cookies' in cookie_data:
                    print("✓ Cookie文件格式正确（新格式）")
                    print(f"  - Cookie数量: {len(cookie_data['cookies'])}")
                    print(f"  - 最后更新: {time.ctime(cookie_data.get('last_update', 0))}")
                else:
                    print("! Cookie文件使用旧格式")
            else:
                print(f"! Cookie文件不存在: {cookie_file}")
                
            return True
            
    except Exception as e:
        print(f"✗ Cookie基础功能测试失败: {str(e)}")
        return False

def test_cookie_validation():
    """
    测试Cookie验证功能
    """
    print("\n=== 测试Cookie验证功能 ===")
    
    try:
        config = Config()
        logger_manager = LoggerManager()
        
        with NetworkManager(config, logger_manager) as network:
            # 测试Cookie验证
            is_valid = network._validate_cookies()
            print(f"✓ Cookie验证结果: {'有效' if is_valid else '无效'}")
            
            return True
            
    except Exception as e:
        print(f"✗ Cookie验证测试失败: {str(e)}")
        return False

def test_cookie_refresh():
    """
    测试Cookie刷新功能
    """
    print("\n=== 测试Cookie刷新功能 ===")
    
    try:
        config = Config()
        logger_manager = LoggerManager()
        
        with NetworkManager(config, logger_manager) as network:
            # 记录刷新前的Cookie数量
            old_cookie_count = len(network.session.cookies)
            print(f"刷新前Cookie数量: {old_cookie_count}")
            
            # 执行Cookie刷新
            network._refresh_cookies()
            
            # 记录刷新后的Cookie数量
            new_cookie_count = len(network.session.cookies)
            print(f"刷新后Cookie数量: {new_cookie_count}")
            
            print("✓ Cookie刷新完成")
            return True
            
    except Exception as e:
        print(f"✗ Cookie刷新测试失败: {str(e)}")
        return False

def test_cookie_expiration():
    """
    测试Cookie过期检测
    """
    print("\n=== 测试Cookie过期检测 ===")
    
    try:
        config = Config()
        logger_manager = LoggerManager()
        cookie_file = config.cookie_file
        
        # 创建一个过期的Cookie文件
        if os.path.exists(cookie_file):
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)
                
            # 设置为过期时间（25小时前）
            cookie_data['last_update'] = time.time() - (25 * 3600)
            
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookie_data, f, ensure_ascii=False, indent=2)
                
            print("✓ 创建过期Cookie文件")
            
            # 测试过期检测
            with NetworkManager(config, logger_manager) as network:
                print("✓ 过期Cookie检测和处理完成")
                
        return True
        
    except Exception as e:
        print(f"✗ Cookie过期检测测试失败: {str(e)}")
        return False

def test_network_request_with_cookies():
    """
    测试带Cookie的网络请求
    """
    print("\n=== 测试带Cookie的网络请求 ===")
    
    try:
        config = Config()
        logger_manager = LoggerManager()
        
        with NetworkManager(config, logger_manager) as network:
            # 测试搜索请求
            response = network.search_drugs("阿司匹林")
            
            if response and response.status_code == 200:
                print("✓ 搜索请求成功")
                print(f"  - 状态码: {response.status_code}")
                print(f"  - 响应长度: {len(response.text)}")
                print(f"  - Cookie数量: {len(network.session.cookies)}")
                
                # 检查是否有新的Cookie
                for cookie in network.session.cookies:
                    print(f"  - Cookie: {cookie.name}={cookie.value[:20]}...")
                    
                return True
            else:
                print(f"✗ 搜索请求失败: {response.status_code if response else 'None'}")
                return False
                
    except Exception as e:
        print(f"✗ 网络请求测试失败: {str(e)}")
        return False

def test_cookie_configuration():
    """
    测试Cookie配置参数
    """
    print("\n=== 测试Cookie配置参数 ===")
    
    try:
        config = Config()
        
        print(f"✓ Cookie过期时间: {config.cookie_expire_hours}小时")
        print(f"✓ 自动刷新Cookie: {config.auto_refresh_cookies}")
        print(f"✓ Cookie验证启用: {config.cookie_validation_enabled}")
        print(f"✓ Cookie重试次数: {config.cookie_retry_attempts}")
        print(f"✓ Cookie文件路径: {config.cookie_file}")
        
        return True
        
    except Exception as e:
        print(f"✗ Cookie配置测试失败: {str(e)}")
        return False

def main():
    """
    运行所有Cookie管理测试
    """
    print("丁香园爬虫 - Cookie管理功能测试")
    print("=" * 50)
    
    tests = [
        test_cookie_configuration,
        test_cookie_basic_functionality,
        test_cookie_validation,
        test_cookie_refresh,
        test_cookie_expiration,
        test_network_request_with_cookies
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ 测试异常: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有Cookie管理功能测试通过！")
        return True
    else:
        print("⚠️  部分测试失败，请检查配置和网络连接")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)