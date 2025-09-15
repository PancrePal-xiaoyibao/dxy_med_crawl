# -*- coding: utf-8 -*-
"""
日志管理模块

功能：
- 统一的日志记录接口
- 支持文件和控制台输出
- 日志轮转和压缩
- 不同级别的日志过滤
- 性能监控日志

作者：AI Assistant
创建时间：2025-01-15
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import functools
import time

from .config import config


class TimerContext:
    """
    计时器上下文管理器
    
    功能：
    - 实现with语句的计时功能
    - 自动记录代码块执行时间
    
    参数：
    - performance_logger: 性能日志器实例
    - name: 计时器名称
    
    返回值：无
    异常：无
    """
    
    def __init__(self, performance_logger, name: str):
        self.performance_logger = performance_logger
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        execution_time = end_time - self.start_time
        
        # 更新统计信息
        if self.name not in self.performance_logger.stats:
            self.performance_logger.stats[self.name] = {
                'total_calls': 0,
                'total_time': 0,
                'success_calls': 0,
                'failed_calls': 0
            }
        
        self.performance_logger.stats[self.name]['total_calls'] += 1
        self.performance_logger.stats[self.name]['total_time'] += execution_time
        
        if exc_type is None:
            self.performance_logger.stats[self.name]['success_calls'] += 1
        else:
            self.performance_logger.stats[self.name]['failed_calls'] += 1
        
        # 记录执行时间
        avg_time = self.performance_logger.stats[self.name]['total_time'] / self.performance_logger.stats[self.name]['total_calls']
        self.performance_logger.logger.debug(
            f"代码块 {self.name} 执行时间: {execution_time:.3f}s, "
            f"平均时间: {avg_time:.3f}s, "
            f"调用次数: {self.performance_logger.stats[self.name]['total_calls']}"
        )


class ColoredFormatter(logging.Formatter):
    """
    彩色日志格式化器
    
    功能：
    - 为不同级别的日志添加颜色
    - 提高控制台日志可读性
    
    参数：
    - fmt: 日志格式字符串
    - datefmt: 日期格式字符串
    
    返回值：格式化器实例
    异常：无
    """
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'        # 重置
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录
        
        功能：为日志记录添加颜色代码
        
        参数：
        - record: 日志记录对象
        
        返回值：格式化后的日志字符串
        异常：无
        """
        # 获取原始格式化结果
        log_message = super().format(record)
        
        # 添加颜色
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        return f"{color}{log_message}{reset}"


class PerformanceLogger:
    """
    性能监控日志器
    
    功能：
    - 记录函数执行时间
    - 监控系统性能
    - 统计调用次数
    
    参数：
    - logger: 日志器实例
    
    返回值：性能日志器实例
    异常：无
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.stats: Dict[str, Dict[str, Any]] = {}
    
    def log_execution_time(self, func_name: str = None):
        """
        记录函数执行时间的装饰器
        
        功能：
        - 自动记录函数执行时间
        - 统计调用次数和平均时间
        
        参数：
        - func_name: 函数名称（可选）
        
        返回值：装饰器函数
        异常：无
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                name = func_name or f"{func.__module__}.{func.__name__}"
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    success = True
                except Exception as e:
                    self.logger.error(f"函数 {name} 执行失败: {e}")
                    success = False
                    raise
                finally:
                    end_time = time.time()
                    execution_time = end_time - start_time
                    
                    # 更新统计信息
                    if name not in self.stats:
                        self.stats[name] = {
                            'total_calls': 0,
                            'total_time': 0,
                            'success_calls': 0,
                            'failed_calls': 0
                        }
                    
                    self.stats[name]['total_calls'] += 1
                    self.stats[name]['total_time'] += execution_time
                    
                    if success:
                        self.stats[name]['success_calls'] += 1
                    else:
                        self.stats[name]['failed_calls'] += 1
                    
                    # 记录执行时间
                    avg_time = self.stats[name]['total_time'] / self.stats[name]['total_calls']
                    self.logger.debug(
                        f"函数 {name} 执行时间: {execution_time:.3f}s, "
                        f"平均时间: {avg_time:.3f}s, "
                        f"调用次数: {self.stats[name]['total_calls']}"
                    )
                
                return result
            return wrapper
        return decorator
    
    def timer(self, name: str):
        """
        计时器上下文管理器
        
        功能：
        - 提供with语句的计时功能
        - 自动记录代码块执行时间
        
        参数：
        - name: 计时器名称
        
        返回值：计时器上下文管理器
        异常：无
        """
        return TimerContext(self, name)
    
    def get_performance_report(self) -> str:
        """
        获取性能报告
        
        功能：生成详细的性能统计报告
        
        参数：无
        返回值：性能报告字符串
        异常：无
        """
        if not self.stats:
            return "暂无性能统计数据"
        
        report = ["\n=== 性能统计报告 ==="]
        
        for func_name, stats in self.stats.items():
            avg_time = stats['total_time'] / stats['total_calls']
            success_rate = stats['success_calls'] / stats['total_calls'] * 100
            
            report.append(f"\n函数: {func_name}")
            report.append(f"  总调用次数: {stats['total_calls']}")
            report.append(f"  成功次数: {stats['success_calls']}")
            report.append(f"  失败次数: {stats['failed_calls']}")
            report.append(f"  成功率: {success_rate:.1f}%")
            report.append(f"  总执行时间: {stats['total_time']:.3f}s")
            report.append(f"  平均执行时间: {avg_time:.3f}s")
        
        return "\n".join(report)


class LoggerManager:
    """
    日志管理器
    
    功能：
    - 创建和配置日志器
    - 管理日志文件轮转
    - 提供统一的日志接口
    
    参数：无
    返回值：日志管理器实例
    异常：日志配置失败时抛出异常
    """
    
    def __init__(self):
        self.loggers: Dict[str, logging.Logger] = {}
        self.performance_logger: Optional[PerformanceLogger] = None
        self._setup_root_logger()
    
    def _setup_root_logger(self) -> None:
        """
        设置根日志器
        
        功能：
        - 配置根日志器的基本设置
        - 设置日志级别和格式
        
        参数：无
        返回值：无
        异常：日志配置失败时抛出异常
        """
        # 设置根日志器级别
        logging.root.setLevel(getattr(logging, config.LOG_LEVEL))
        
        # 清除现有处理器
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        获取日志器实例
        
        功能：
        - 创建或获取指定名称的日志器
        - 自动配置处理器和格式化器
        
        参数：
        - name: 日志器名称
        
        返回值：配置好的日志器实例
        异常：日志器创建失败时抛出异常
        """
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, config.LOG_LEVEL))
        
        # 防止重复添加处理器
        if not logger.handlers:
            self._add_console_handler(logger)
            self._add_file_handler(logger)
        
        self.loggers[name] = logger
        return logger
    
    def _add_console_handler(self, logger: logging.Logger) -> None:
        """
        添加控制台处理器
        
        功能：
        - 配置控制台输出
        - 添加彩色格式化
        
        参数：
        - logger: 日志器实例
        
        返回值：无
        异常：无
        """
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, config.LOG_LEVEL))
        
        # 使用彩色格式化器
        console_formatter = ColoredFormatter(
            fmt=config.LOG_FORMAT,
            datefmt=config.LOG_DATE_FORMAT
        )
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(console_handler)
    
    def _add_file_handler(self, logger: logging.Logger) -> None:
        """
        添加文件处理器
        
        功能：
        - 配置文件输出
        - 设置日志轮转
        
        参数：
        - logger: 日志器实例
        
        返回值：无
        异常：文件处理器创建失败时抛出异常
        """
        # 创建日志文件路径
        log_file = config.LOGS_DIR / f"{logger.name}.log"
        
        # 使用轮转文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=config.LOG_FILE_MAX_SIZE,
            backupCount=config.LOG_FILE_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别
        
        # 文件格式化器（不需要颜色）
        file_formatter = logging.Formatter(
            fmt=config.LOG_FORMAT,
            datefmt=config.LOG_DATE_FORMAT
        )
        file_handler.setFormatter(file_formatter)
        
        logger.addHandler(file_handler)
    
    def get_performance_logger(self, logger_name: str = "performance") -> PerformanceLogger:
        """
        获取性能日志器
        
        功能：
        - 创建性能监控日志器
        - 提供性能统计功能
        
        参数：
        - logger_name: 日志器名称
        
        返回值：性能日志器实例
        异常：无
        """
        if self.performance_logger is None:
            logger = self.get_logger(logger_name)
            self.performance_logger = PerformanceLogger(logger)
        
        return self.performance_logger
    
    def log_system_info(self) -> None:
        """
        记录系统信息
        
        功能：
        - 记录系统环境信息
        - 记录配置信息
        - 记录启动时间
        
        参数：无
        返回值：无
        异常：无
        """
        logger = self.get_logger("system")
        
        logger.info("=== 丁香园爬虫系统启动 ===")
        logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Python版本: {sys.version}")
        logger.info(f"工作目录: {os.getcwd()}")
        logger.info(f"配置信息: {config}")
        logger.info("=== 系统信息记录完成 ===")
    
    def shutdown(self) -> None:
        """
        关闭日志管理器
        
        功能：
        - 输出性能报告
        - 关闭所有处理器
        - 清理资源
        
        参数：无
        返回值：无
        异常：无
        """
        # 输出性能报告
        if self.performance_logger:
            logger = self.get_logger("system")
            report = self.performance_logger.get_performance_report()
            logger.info(report)
        
        # 关闭所有日志器的处理器
        for logger in self.loggers.values():
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
        
        # 清理缓存
        self.loggers.clear()
        self.performance_logger = None


# 全局日志管理器实例
logger_manager = LoggerManager()

# 便捷函数
def get_logger(name: str) -> logging.Logger:
    """
    获取日志器的便捷函数
    
    功能：提供简单的日志器获取接口
    
    参数：
    - name: 日志器名称
    
    返回值：日志器实例
    异常：无
    """
    return logger_manager.get_logger(name)


def get_performance_logger() -> PerformanceLogger:
    """
    获取性能日志器的便捷函数
    
    功能：提供简单的性能日志器获取接口
    
    参数：无
    返回值：性能日志器实例
    异常：无
    """
    return logger_manager.get_performance_logger()


def log_execution_time(func_name: str = None):
    """
    记录执行时间的装饰器便捷函数
    
    功能：提供简单的性能监控装饰器
    
    参数：
    - func_name: 函数名称（可选）
    
    返回值：装饰器函数
    异常：无
    """
    perf_logger = get_performance_logger()
    return perf_logger.log_execution_time(func_name)


if __name__ == "__main__":
    # 日志系统测试
    logger_manager.log_system_info()
    
    # 测试不同级别的日志
    test_logger = get_logger("test")
    test_logger.debug("这是调试信息")
    test_logger.info("这是普通信息")
    test_logger.warning("这是警告信息")
    test_logger.error("这是错误信息")
    test_logger.critical("这是严重错误信息")
    
    # 测试性能日志
    @log_execution_time("测试函数")
    def test_function():
        import time
        time.sleep(0.1)
        return "测试完成"
    
    result = test_function()
    test_logger.info(f"函数返回: {result}")
    
    # 输出性能报告
    perf_logger = get_performance_logger()
    print(perf_logger.get_performance_report())
    
    # 关闭日志管理器
    logger_manager.shutdown()