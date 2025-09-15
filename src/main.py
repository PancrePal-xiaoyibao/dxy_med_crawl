#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
丁香园药物信息爬虫主控制器

主要功能：
- 药物搜索和信息爬取
- 多种数据获取策略
- 数据处理和RAG优化
- 批量处理和导出
- 错误处理和重试机制

作者: AI Assistant
版本: 1.0.0
使用方法:
    python main.py --drug "阿司匹林" --format json
    python main.py --batch drugs.txt --output ./results
"""

import sys
import argparse
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import time

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

# 导入模块
from src.modules.config import Config
from src.modules.logger import LoggerManager
from src.modules.network import NetworkManager
from src.modules.parser import PageParser
from src.modules.jina_processor import JinaProcessor
from src.modules.processor import DataProcessor, RAGOptimizer, DataExporter


class DrugCrawler:
    """
    药物信息爬虫主控制器
    
    功能:
    - 协调各个模块
    - 实现爬取流程
    - 处理错误和重试
    - 数据导出管理
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化爬虫控制器
        
        参数:
            config_path: 配置文件路径
        """
        # 初始化配置和日志
        self.config = Config()
        self.logger_manager = LoggerManager()
        self.logger = self.logger_manager.get_logger('drug_crawler')
        
        # 初始化各个模块
        self.network_manager = NetworkManager(self.config, self.logger_manager)
        self.page_parser = PageParser(self.config, self.logger_manager)
        self.jina_processor = JinaProcessor(self.config, self.logger_manager)
        self.data_processor = DataProcessor(self.config, self.logger_manager)
        self.rag_optimizer = RAGOptimizer(self.config, self.logger_manager)
        self.data_exporter = DataExporter(self.config, self.logger_manager)
        
        # 统计信息
        self.stats = {
            'total_searched': 0,
            'total_found': 0,
            'total_processed': 0,
            'total_exported': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
        self.logger.info("药物爬虫初始化完成")
    
    async def search_and_crawl_drug(self, drug_name: str, use_jina: bool = True, interactive: bool = False) -> Optional[Dict[str, Any]]:
        """
        搜索并爬取单个药物信息
        
        参数:
            drug_name: 药物名称
            use_jina: 是否优先使用Jina AI
            interactive: 是否启用交互式选择模式
            
        返回:
            Optional[Dict[str, Any]]: 处理后的药物信息
        """
        try:
            self.stats['total_searched'] += 1
            self.logger.info(f"开始搜索药物: {drug_name}")
            
            # 第一步：搜索药物
            search_results = self.network_manager.search_drug(drug_name)
            if not search_results:
                self.logger.warning(f"未找到药物: {drug_name}")
                return None
            
            # 第二步：解析搜索结果，获取详情页链接
            detail_links = self.page_parser.parse_search_results(search_results.text)
            if not detail_links:
                self.logger.warning(f"未找到药物详情链接: {drug_name}")
                return None
            
            self.stats['total_found'] += 1
            
            # 第三步：用户选择药物（如果启用交互模式且有多个选项）
            selected_links = detail_links
            if interactive and len(detail_links) > 1:
                selected_links = self._show_drug_selection(detail_links, drug_name)
                if not selected_links:
                    self.logger.info("用户取消选择")
                    return None
            
            # 第四步：获取药物详情信息
            drug_data = None
            
            # 如果是交互模式，只处理用户选择的药物；否则尝试前3个
            links_to_try = selected_links if interactive else detail_links[:3]
            
            # 如果是交互模式且用户选择了药物，直接使用Jina AI导出markdown
            if interactive and selected_links:
                try:
                    link_info = selected_links[0]  # 用户选择的药物
                    detail_url = link_info.get('url')
                    drug_title = link_info.get('name', drug_name)  # 使用name而不是title
                    
                    if detail_url:
                        # 直接使用Jina AI获取内容并保存为markdown
                        md_file_path = self.data_exporter.export_drug_from_url(detail_url, drug_title)
                        self.logger.info(f"成功导出markdown文件: {md_file_path}")
                        
                        # 返回简化的结果
                        return {
                            'drug_info': None,
                            'rag_data': None,
                            'raw_data': None,
                            'markdown_file': md_file_path,
                            'source_url': detail_url,
                            'drug_name': drug_title
                        }
                except Exception as e:
                    self.logger.error(f"直接导出markdown失败: {e}")
                    # 如果直接导出失败，继续使用传统方式
            
            for link_info in links_to_try:
                detail_url = link_info.get('url')
                if not detail_url:
                    continue
                
                self.logger.info(f"尝试获取药物详情: {detail_url}")
                
                # 策略1：优先使用Jina AI处理
                if use_jina and self.config.USE_JINA_FIRST:
                    try:
                        jina_data = self.jina_processor.process_url(detail_url)
                        if jina_data and self._validate_drug_data(jina_data):
                            drug_data = jina_data
                            drug_data['source_url'] = detail_url
                            drug_data['acquisition_method'] = 'jina_ai'
                            self.logger.info(f"Jina AI获取成功: {drug_name}")
                            break
                    except Exception as e:
                        self.logger.warning(f"Jina AI处理失败: {e}")
                
                # 策略2：传统网页爬取
                try:
                    detail_response = self.network_manager.get_drug_detail(detail_url)
                    if detail_response:
                        parsed_data = self.page_parser.parse_drug_detail(detail_response.text, detail_url)
                        if parsed_data and self._validate_drug_data(parsed_data):
                            drug_data = parsed_data
                            drug_data['source_url'] = detail_url
                            drug_data['acquisition_method'] = 'traditional_crawl'
                            self.logger.info(f"传统爬取成功: {drug_name}")
                            break
                except Exception as e:
                    self.logger.warning(f"传统爬取失败: {e}")
                
                # 如果是交互模式，只处理用户选择的药物，失败就停止
                if interactive:
                    break
            
            if not drug_data:
                self.logger.error(f"所有获取策略都失败: {drug_name}")
                self.stats['errors'] += 1
                return None
            
            # 第四步：数据处理和优化
            try:
                # 结构化处理
                drug_info = self.data_processor.process_drug_data(drug_data)
                
                # RAG优化
                rag_data = self.rag_optimizer.optimize_for_rag(drug_info)
                
                self.stats['total_processed'] += 1
                
                result = {
                    'drug_info': drug_info,
                    'rag_data': rag_data,
                    'raw_data': drug_data
                }
                
                self.logger.info(f"药物信息处理完成: {drug_name}")
                return result
                
            except Exception as e:
                self.logger.error(f"数据处理失败: {e}")
                self.stats['errors'] += 1
                return None
                
        except Exception as e:
            self.logger.error(f"爬取药物信息失败 {drug_name}: {e}")
            self.stats['errors'] += 1
            return None
    
    def _show_drug_selection(self, detail_links: List[Dict[str, Any]], drug_name: str) -> List[Dict[str, Any]]:
        """
        显示药物选择列表，让用户选择正确的药物
        
        参数:
            detail_links: 药物链接列表
            drug_name: 搜索的药物名称
            
        返回:
            List[Dict[str, Any]]: 用户选择的药物链接列表
        """
        print(f"\n找到 {len(detail_links)} 个与 '{drug_name}' 相关的药物:")
        print("-" * 60)
        
        for i, link_info in enumerate(detail_links, 1):
            name = link_info.get('name', '未知药物')
            description = link_info.get('description', '')
            manufacturer = link_info.get('manufacturer', '')
            
            print(f"{i}. {name}")
            if manufacturer:
                print(f"   生产厂家: {manufacturer}")
            if description:
                print(f"   描述: {description}")
            print()
        
        print("0. 取消选择")
        print("-" * 60)
        
        while True:
            try:
                choice = input(f"请选择要获取说明书的药物 (1-{len(detail_links)}, 0取消): ").strip()
                
                if choice == '0':
                    return []
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(detail_links):
                    selected_drug = detail_links[choice_num - 1]
                    print(f"\n已选择: {selected_drug.get('name', '未知药物')}")
                    return [selected_drug]
                else:
                    print(f"请输入有效的选项 (1-{len(detail_links)}, 0取消)")
                    
            except ValueError:
                print("请输入数字")
            except KeyboardInterrupt:
                print("\n用户取消操作")
                return []
    
    def _validate_drug_data(self, data: Dict[str, Any]) -> bool:
        """
        验证药物数据的有效性
        
        参数:
            data: 药物数据字典
            
        返回:
            bool: 数据是否有效
        """
        if not isinstance(data, dict):
            return False
        
        # 检查必要字段
        required_fields = ['药品名称', 'name', '名称']
        has_name = any(field in data and data[field] for field in required_fields)
        
        if not has_name:
            return False
        
        # 检查内容长度
        total_content_length = sum(
            len(str(value)) for value in data.values() 
            if isinstance(value, (str, int, float))
        )
        
        return total_content_length > 50  # 至少50个字符的内容
    
    async def batch_crawl(self, drug_names: List[str], 
                         max_concurrent: int = 3,
                         delay_between_requests: float = 1.0) -> List[Dict[str, Any]]:
        """
        批量爬取药物信息
        
        参数:
            drug_names: 药物名称列表
            max_concurrent: 最大并发数
            delay_between_requests: 请求间隔（秒）
            
        返回:
            List[Dict[str, Any]]: 处理结果列表
        """
        self.logger.info(f"开始批量爬取，共 {len(drug_names)} 个药物")
        results = []
        
        # 分批处理，控制并发
        for i in range(0, len(drug_names), max_concurrent):
            batch = drug_names[i:i + max_concurrent]
            
            # 并发处理当前批次
            tasks = []
            for drug_name in batch:
                task = self.search_and_crawl_drug(drug_name.strip())
                tasks.append(task)
            
            # 等待当前批次完成
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    self.logger.error(f"批量处理异常 {batch[j]}: {result}")
                    self.stats['errors'] += 1
                elif result:
                    results.append(result)
            
            # 请求间隔
            if i + max_concurrent < len(drug_names):
                await asyncio.sleep(delay_between_requests)
                
            self.logger.info(f"批次进度: {min(i + max_concurrent, len(drug_names))}/{len(drug_names)}")
        
        self.logger.info(f"批量爬取完成，成功处理 {len(results)} 个药物")
        return results
    
    def export_results(self, results: List[Dict[str, Any]], 
                      format_type: str = 'json',
                      output_dir: Optional[str] = None) -> List[str]:
        """
        导出爬取结果
        
        参数:
            results: 爬取结果列表
            format_type: 导出格式
            output_dir: 输出目录
            
        返回:
            List[str]: 导出文件路径列表
        """
        if output_dir:
            # 如果指定了输出目录，临时禁用独立目录功能
            original_use_independent = self.config.USE_INDEPENDENT_DIRS
            original_session_dir = self.config.CURRENT_SESSION_DIR
            
            self.config.USE_INDEPENDENT_DIRS = False
            self.config.OUTPUT_DIR = Path(output_dir)
            self.data_exporter = DataExporter(self.config, self.logger)
            
            # 恢复原始设置
            self.config.USE_INDEPENDENT_DIRS = original_use_independent
            self.config.CURRENT_SESSION_DIR = original_session_dir
        
        exported_files = []
        
        for result in results:
            try:
                # 检查是否是直接导出的markdown文件
                if result.get('markdown_file'):
                    exported_files.append(result['markdown_file'])
                    self.stats['total_exported'] += 1
                    self.logger.info(f"已导出markdown文件: {result['markdown_file']}")
                    continue
                
                drug_info = result.get('drug_info')
                if drug_info:
                    # 导出指定格式
                    file_path = self.data_exporter.export_drug_info(drug_info, format_type)
                    exported_files.append(file_path)
                    
                    # 同时导出markdown格式（如果不是markdown格式）
                    if format_type != 'md':
                        md_file_path = self.data_exporter.export_drug_info(drug_info, 'md')
                        exported_files.append(md_file_path)
                    
                    self.stats['total_exported'] += 1
            except Exception as e:
                self.logger.error(f"导出失败: {e}")
        
        # 导出汇总信息
        if results:
            try:
                self._export_summary(results, format_type)
            except Exception as e:
                self.logger.error(f"导出汇总信息失败: {e}")
        
        return exported_files
    
    def _export_summary(self, results: List[Dict[str, Any]], format_type: str):
        """
        导出汇总信息
        
        参数:
            results: 爬取结果列表
            format_type: 导出格式
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            summary_file = self.config.OUTPUT_DIR / f"summary_{timestamp}.{format_type}"
            
            summary_data = {
                'crawl_summary': self.stats,
                'total_drugs': len(results),
                'drugs': []
            }
            
            for result in results:
                drug_info = result.get('drug_info')
                if drug_info:
                    summary_data['drugs'].append({
                        'name': drug_info.name,
                        'generic_name': drug_info.generic_name,
                        'manufacturer': drug_info.manufacturer,
                        'quality_score': drug_info.data_quality_score,
                        'source_url': drug_info.source_url
                    })
            
            if format_type == 'json':
                with open(summary_file, 'w', encoding='utf-8') as f:
                    json.dump(summary_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"导出汇总信息: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"导出汇总信息失败: {e}")
    
    def print_stats(self):
        """
        打印统计信息
        """
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            duration_str = f"{duration:.2f}秒"
        else:
            duration_str = "未知"
        
        print("\n=== 爬取统计信息 ===")
        print(f"搜索药物数量: {self.stats['total_searched']}")
        print(f"找到药物数量: {self.stats['total_found']}")
        print(f"处理成功数量: {self.stats['total_processed']}")
        print(f"导出文件数量: {self.stats['total_exported']}")
        print(f"错误数量: {self.stats['errors']}")
        print(f"总耗时: {duration_str}")
        
        if self.stats['total_searched'] > 0:
            success_rate = (self.stats['total_processed'] / self.stats['total_searched']) * 100
            print(f"成功率: {success_rate:.1f}%")
    
    async def cleanup(self):
        """
        清理资源
        """
        try:
            self.network_manager.close()
            self.logger.info("资源清理完成")
        except Exception as e:
            self.logger.error(f"资源清理失败: {e}")


async def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='丁香园药物信息爬虫')
    parser.add_argument('--drug', '-d', type=str, help='单个药物名称')
    parser.add_argument('--batch', '-b', type=str, help='批量药物文件路径')
    parser.add_argument('--format', '-f', type=str, default='json', 
                       choices=['json', 'txt', 'md'], help='导出格式')
    parser.add_argument('--output', '-o', type=str, help='输出目录')
    parser.add_argument('--config', '-c', type=str, help='配置文件路径')
    parser.add_argument('--concurrent', type=int, default=3, help='最大并发数')
    parser.add_argument('--delay', type=float, default=1.0, help='请求间隔（秒）')
    parser.add_argument('--no-jina', action='store_true', help='禁用Jina AI')
    parser.add_argument('--interactive', '-i', action='store_true', help='启用交互式选择模式')
    
    args = parser.parse_args()
    
    if not args.drug and not args.batch:
        parser.print_help()
        return
    
    # 初始化爬虫
    crawler = DrugCrawler(args.config)
    crawler.stats['start_time'] = time.time()
    
    try:
        results = []
        
        if args.drug:
            # 单个药物爬取
            result = await crawler.search_and_crawl_drug(
                args.drug, 
                use_jina=not args.no_jina,
                interactive=args.interactive
            )
            if result:
                results.append(result)
        
        elif args.batch:
            # 批量药物爬取
            batch_file = Path(args.batch)
            if not batch_file.exists():
                print(f"错误: 批量文件不存在: {args.batch}")
                return
            
            with open(batch_file, 'r', encoding='utf-8') as f:
                drug_names = [line.strip() for line in f if line.strip()]
            
            if not drug_names:
                print(f"错误: 批量文件为空: {args.batch}")
                return
            
            results = await crawler.batch_crawl(
                drug_names, 
                max_concurrent=args.concurrent,
                delay_between_requests=args.delay
            )
        
        # 导出结果
        if results:
            exported_files = crawler.export_results(results, args.format, args.output)
            print(f"\n导出完成，共 {len(exported_files)} 个文件:")
            for file_path in exported_files:
                print(f"  {file_path}")
        else:
            print("\n未获取到任何药物信息")
        
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"\n程序异常: {e}")
        crawler.logger.error(f"程序异常: {e}")
    finally:
        crawler.stats['end_time'] = time.time()
        crawler.print_stats()
        await crawler.cleanup()


if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 运行主程序
    asyncio.run(main())