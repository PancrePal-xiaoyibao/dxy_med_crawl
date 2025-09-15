#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
丁香园药物信息爬虫 - 快速启动脚本

这个脚本提供了一个简单的命令行界面来运行爬虫程序。
支持多种运行模式和配置选项。

使用方法:
    python run.py                    # 交互式模式
    python run.py --drug "阿司匹林"    # 直接搜索单个药物
    python run.py --file drugs.txt   # 从文件批量搜索
    python run.py --test             # 测试模式

作者: AI Assistant
创建时间: 2024-01-15
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path
from typing import List, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.main import DrugCrawler
    from src.modules.config import Config
    from src.modules.logger import LoggerManager
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("请确保已安装所有依赖: pip install -r requirements.txt")
    sys.exit(1)


class QuickStart:
    """快速启动类"""
    
    def __init__(self):
        """初始化快速启动器"""
        self.config = Config()
        self.logger = LoggerManager().get_logger("QuickStart")
        self.crawler = None
    
    def print_banner(self):
        """打印程序横幅"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    丁香园药物信息爬虫                           ║
║                  DXY Drug Information Crawler                ║
║                                                              ║
║  功能特性:                                                    ║
║  • 智能药物信息爬取                                            ║
║  • Jina AI 内容处理                                           ║
║  • 多格式数据导出                                              ║
║  • RAG 优化支持                                               ║
║  • 反爬虫机制                                                 ║
║                                                              ║
║  版本: v1.0.0                                                ║
║  作者: AI Assistant                                          ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def check_environment(self) -> bool:
        """检查运行环境"""
        print("🔍 检查运行环境...")
        
        # 检查Python版本
        if sys.version_info < (3, 8):
            print("❌ Python版本过低，需要Python 3.8+")
            return False
        print(f"✅ Python版本: {sys.version.split()[0]}")
        
        # 检查必要的目录
        required_dirs = ['src', 'src/modules', 'src/utils']
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                print(f"❌ 缺少必要目录: {dir_path}")
                return False
        print("✅ 项目结构完整")
        
        # 检查配置文件
        if not Path('.env').exists() and not Path('.env.example').exists():
            print("⚠️  未找到配置文件，将使用默认配置")
        else:
            print("✅ 配置文件存在")
        
        # 创建必要目录
        self.config._create_directories()
        print("✅ 输出目录已准备")
        
        return True
    
    def get_drug_list_from_file(self, file_path: str) -> List[str]:
        """从文件读取药物列表"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                drugs = [line.strip() for line in f if line.strip()]
            return drugs
        except FileNotFoundError:
            print(f"❌ 文件不存在: {file_path}")
            return []
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return []
    
    def interactive_mode(self):
        """交互式模式"""
        print("\n🎯 进入交互式模式")
        print("请选择运行模式:")
        print("1. 搜索单个药物")
        print("2. 批量搜索药物")
        print("3. 从文件导入药物列表")
        print("4. 测试模式")
        print("0. 退出")
        
        while True:
            try:
                choice = input("\n请输入选项 (0-4): ").strip()
                
                if choice == '0':
                    print("👋 再见!")
                    return
                elif choice == '1':
                    drug_name = input("请输入药物名称: ").strip()
                    if drug_name:
                        asyncio.run(self.run_single_drug(drug_name))
                    break
                elif choice == '2':
                    drugs_input = input("请输入药物名称（用逗号分隔）: ").strip()
                    if drugs_input:
                        drugs = [d.strip() for d in drugs_input.split(',') if d.strip()]
                        asyncio.run(self.run_multiple_drugs(drugs))
                    break
                elif choice == '3':
                    file_path = input("请输入文件路径: ").strip()
                    if file_path:
                        drugs = self.get_drug_list_from_file(file_path)
                        if drugs:
                            asyncio.run(self.run_multiple_drugs(drugs))
                    break
                elif choice == '4':
                    asyncio.run(self.run_test_mode())
                    break
                else:
                    print("❌ 无效选项，请重新输入")
            except KeyboardInterrupt:
                print("\n👋 用户取消操作")
                return
            except Exception as e:
                print(f"❌ 发生错误: {e}")
                return
    
    async def run_single_drug(self, drug_name: str):
        """运行单个药物搜索"""
        print(f"\n🔍 开始搜索药物: {drug_name}")
        
        try:
            if not self.crawler:
                self.crawler = DrugCrawler(self.config)
            
            results = await self.crawler.search_and_crawl_drug(drug_name)
            
            if results:
                print(f"✅ 成功获取药物信息")
                
                # 导出数据
                output_files = self.crawler.export_results(
                    [results], 
                    'json'
                )
                if output_files:
                    print(f"📁 数据已保存到: {output_files[0]}")
                    for file_path in output_files[1:]:
                        print(f"📁 额外文件: {file_path}")
            else:
                print("❌ 未找到相关药物信息")
                
        except Exception as e:
            self.logger.error(f"搜索药物失败: {e}")
            print(f"❌ 搜索失败: {e}")
    
    async def run_multiple_drugs(self, drugs: List[str]):
        """运行多个药物搜索"""
        print(f"\n🔍 开始批量搜索 {len(drugs)} 个药物")
        
        try:
            if not self.crawler:
                self.crawler = DrugCrawler(self.config)
            
            all_results = []
            
            for i, drug_name in enumerate(drugs, 1):
                print(f"\n[{i}/{len(drugs)}] 搜索: {drug_name}")
                
                try:
                    results = await self.crawler.search_and_crawl_drug(drug_name)
                    if results:
                        all_results.append(results)
                        print(f"  ✅ 获取药物信息")
                    else:
                        print(f"  ⚠️  未找到信息")
                except Exception as e:
                    print(f"  ❌ 搜索失败: {e}")
                    continue
            
            if all_results:
                print(f"\n✅ 总共获取 {len(all_results)} 条药物信息")
                
                # 导出数据
                output_file = await self.crawler.export_data(
                    all_results, 
                    "batch_drugs_info"
                )
                print(f"📁 数据已保存到: {output_file}")
            else:
                print("❌ 未获取到任何药物信息")
                
        except Exception as e:
            self.logger.error(f"批量搜索失败: {e}")
            print(f"❌ 批量搜索失败: {e}")
    
    async def run_test_mode(self):
        """运行测试模式"""
        print("\n🧪 进入测试模式")
        
        test_drugs = ["阿司匹林", "布洛芬", "对乙酰氨基酚"]
        
        print(f"将测试搜索以下药物: {', '.join(test_drugs)}")
        
        # 设置测试配置
        original_delay = self.config.request_delay
        self.config.request_delay = 0.5  # 测试模式使用较短延迟
        
        try:
            await self.run_multiple_drugs(test_drugs[:2])  # 只测试前2个
        finally:
            self.config.request_delay = original_delay
        
        print("\n🧪 测试模式完成")
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """
使用方法:
    python run.py [选项]

选项:
    --drug DRUG_NAME     搜索指定药物
    --file FILE_PATH     从文件批量搜索药物
    --test              运行测试模式
    --jina              启用Jina AI处理
    --format FORMAT     输出格式 (json,csv,excel)
    --output DIR        输出目录
    --help              显示此帮助信息

示例:
    python run.py --drug "阿司匹林"
    python run.py --file drugs.txt --format json,csv
    python run.py --test --jina
    
配置文件:
    复制 .env.example 为 .env 并修改配置
        """
        print(help_text)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="丁香园药物信息爬虫",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--drug', 
        type=str, 
        help='搜索指定药物'
    )
    parser.add_argument(
        '--file', 
        type=str, 
        help='从文件批量搜索药物'
    )
    parser.add_argument(
        '--test', 
        action='store_true', 
        help='运行测试模式'
    )
    parser.add_argument(
        '--jina', 
        action='store_true', 
        help='启用Jina AI处理'
    )
    parser.add_argument(
        '--format', 
        type=str, 
        default='json,csv',
        help='输出格式 (json,csv,excel)'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        help='输出目录'
    )
    
    args = parser.parse_args()
    
    # 创建快速启动器
    quick_start = QuickStart()
    
    # 显示横幅
    quick_start.print_banner()
    
    # 检查环境
    if not quick_start.check_environment():
        sys.exit(1)
    
    # 应用命令行参数
    if args.jina:
        quick_start.config.use_jina_by_default = True
        print("✅ 已启用Jina AI处理")
    
    if args.output:
        quick_start.config.OUTPUT_DIR = Path(args.output)
        print(f"✅ 输出目录设置为: {args.output}")
    
    if args.format:
        quick_start.config.default_output_format = args.format.split(',')
        print(f"✅ 输出格式设置为: {args.format}")
    
    try:
        # 根据参数运行不同模式
        if args.drug:
            # 单个药物搜索
            asyncio.run(quick_start.run_single_drug(args.drug))
        elif args.file:
            # 文件批量搜索
            drugs = quick_start.get_drug_list_from_file(args.file)
            if drugs:
                asyncio.run(quick_start.run_multiple_drugs(drugs))
            else:
                print("❌ 无法从文件读取药物列表")
        elif args.test:
            # 测试模式
            asyncio.run(quick_start.run_test_mode())
        else:
            # 交互式模式
            quick_start.interactive_mode()
    
    except KeyboardInterrupt:
        print("\n👋 用户取消操作")
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        sys.exit(1)
    
    print("\n🎉 程序运行完成!")


if __name__ == "__main__":
    main()