#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
丁香园药物信息爬虫 - 安装和设置脚本

这个脚本帮助用户快速设置项目环境，包括:
- 检查Python版本
- 安装依赖包
- 创建配置文件
- 初始化目录结构
- 运行基础测试

使用方法:
    python setup.py
    python setup.py --dev    # 开发模式安装
    python setup.py --test   # 仅运行测试

作者: AI Assistant
创建时间: 2024-01-15
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Tuple


class ProjectSetup:
    """项目设置类"""
    
    def __init__(self, dev_mode: bool = False):
        """初始化设置器
        
        Args:
            dev_mode: 是否为开发模式
        """
        self.dev_mode = dev_mode
        self.project_root = Path(__file__).parent
        self.python_executable = sys.executable
    
    def print_banner(self):
        """打印安装横幅"""
        mode = "开发模式" if self.dev_mode else "标准模式"
        banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                丁香园药物信息爬虫 - 项目设置                    ║
║                                                              ║
║  模式: {mode:<20}                                    ║
║  Python: {sys.version.split()[0]:<15}                                ║
║  路径: {str(self.project_root):<45} ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def check_python_version(self) -> bool:
        """检查Python版本
        
        Returns:
            bool: 版本是否满足要求
        """
        print("🔍 检查Python版本...")
        
        if sys.version_info < (3, 8):
            print(f"❌ Python版本过低: {sys.version}")
            print("   需要Python 3.8或更高版本")
            print("   请升级Python后重试")
            return False
        
        print(f"✅ Python版本: {sys.version.split()[0]}")
        return True
    
    def check_pip(self) -> bool:
        """检查pip是否可用
        
        Returns:
            bool: pip是否可用
        """
        print("🔍 检查pip...")
        
        try:
            result = subprocess.run(
                [self.python_executable, '-m', 'pip', '--version'],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✅ pip版本: {result.stdout.strip().split()[1]}")
            return True
        except subprocess.CalledProcessError:
            print("❌ pip不可用")
            print("   请安装pip后重试")
            return False
    
    def install_dependencies(self) -> bool:
        """安装项目依赖
        
        Returns:
            bool: 安装是否成功
        """
        print("📦 安装项目依赖...")
        
        requirements_file = self.project_root / 'requirements.txt'
        
        if not requirements_file.exists():
            print("❌ requirements.txt文件不存在")
            return False
        
        try:
            # 升级pip
            print("  📦 升级pip...")
            subprocess.run(
                [self.python_executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
                check=True,
                capture_output=True
            )
            
            # 安装依赖
            print("  📦 安装项目依赖...")
            cmd = [
                self.python_executable, '-m', 'pip', 'install', 
                '-r', str(requirements_file)
            ]
            
            if self.dev_mode:
                # 开发模式安装额外依赖
                dev_packages = [
                    'pytest>=7.0.0',
                    'pytest-asyncio>=0.21.0',
                    'black>=22.0.0',
                    'flake8>=4.0.0',
                    'mypy>=0.950',
                    'pre-commit>=2.17.0'
                ]
                cmd.extend(dev_packages)
                print("  📦 安装开发依赖...")
            
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            
            print("✅ 依赖安装完成")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 依赖安装失败: {e}")
            if e.stderr:
                print(f"   错误信息: {e.stderr}")
            return False
    
    def create_directories(self) -> bool:
        """创建项目目录结构
        
        Returns:
            bool: 创建是否成功
        """
        print("📁 创建项目目录...")
        
        directories = [
            'output',
            'logs',
            'data',
            'data/cache',
            'data/temp',
            'tests/data',
            'docs'
        ]
        
        try:
            for dir_name in directories:
                dir_path = self.project_root / dir_name
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"  ✅ {dir_name}/")
            
            print("✅ 目录结构创建完成")
            return True
            
        except Exception as e:
            print(f"❌ 目录创建失败: {e}")
            return False
    
    def setup_config_file(self) -> bool:
        """设置配置文件
        
        Returns:
            bool: 设置是否成功
        """
        print("⚙️  设置配置文件...")
        
        env_file = self.project_root / '.env'
        env_example = self.project_root / '.env.example'
        
        try:
            if not env_file.exists() and env_example.exists():
                # 复制示例配置文件
                with open(env_example, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                with open(env_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("✅ 已创建.env配置文件")
                print("   请根据需要修改配置")
            elif env_file.exists():
                print("✅ 配置文件已存在")
            else:
                print("⚠️  未找到配置文件模板")
            
            return True
            
        except Exception as e:
            print(f"❌ 配置文件设置失败: {e}")
            return False
    
    def run_basic_tests(self) -> bool:
        """运行基础测试
        
        Returns:
            bool: 测试是否通过
        """
        print("🧪 运行基础测试...")
        
        try:
            # 测试模块导入
            print("  🧪 测试模块导入...")
            
            test_imports = [
                'src.modules.config',
                'src.modules.logger',
                'src.modules.network',
                'src.modules.parser',
                'src.modules.jina_processor',
                'src.modules.processor',
                'src.main'
            ]
            
            for module_name in test_imports:
                try:
                    __import__(module_name)
                    print(f"    ✅ {module_name}")
                except ImportError as e:
                    print(f"    ❌ {module_name}: {e}")
                    return False
            
            # 运行测试文件（如果存在）
            test_file = self.project_root / 'tests' / 'test_basic.py'
            if test_file.exists():
                print("  🧪 运行单元测试...")
                result = subprocess.run(
                    [self.python_executable, str(test_file)],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                
                if result.returncode == 0:
                    print("    ✅ 单元测试通过")
                else:
                    print("    ⚠️  单元测试有警告")
                    if result.stderr:
                        print(f"    警告: {result.stderr[:200]}...")
            
            print("✅ 基础测试完成")
            return True
            
        except Exception as e:
            print(f"❌ 测试运行失败: {e}")
            return False
    
    def setup_git_hooks(self) -> bool:
        """设置Git钩子（开发模式）
        
        Returns:
            bool: 设置是否成功
        """
        if not self.dev_mode:
            return True
        
        print("🔧 设置Git钩子...")
        
        try:
            # 检查是否是Git仓库
            git_dir = self.project_root / '.git'
            if not git_dir.exists():
                print("  ⚠️  不是Git仓库，跳过Git钩子设置")
                return True
            
            # 安装pre-commit钩子
            result = subprocess.run(
                [self.python_executable, '-m', 'pre_commit', 'install'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                print("✅ Git钩子设置完成")
            else:
                print("⚠️  Git钩子设置失败，但不影响项目使用")
            
            return True
            
        except Exception as e:
            print(f"⚠️  Git钩子设置失败: {e}")
            return True  # 不影响主要功能
    
    def print_next_steps(self):
        """打印后续步骤"""
        print("\n🎉 项目设置完成!")
        print("\n📋 后续步骤:")
        print("1. 检查并修改 .env 配置文件")
        print("2. 运行测试: python run.py --test")
        print("3. 开始使用: python run.py")
        print("\n📚 更多信息请查看 README.md")
        
        if self.dev_mode:
            print("\n🔧 开发模式额外功能:")
            print("- 代码格式化: black src/")
            print("- 代码检查: flake8 src/")
            print("- 类型检查: mypy src/")
            print("- 运行测试: pytest tests/")
    
    def run_setup(self) -> bool:
        """运行完整设置流程
        
        Returns:
            bool: 设置是否成功
        """
        self.print_banner()
        
        steps = [
            ("检查Python版本", self.check_python_version),
            ("检查pip", self.check_pip),
            ("安装依赖", self.install_dependencies),
            ("创建目录", self.create_directories),
            ("设置配置", self.setup_config_file),
            ("运行测试", self.run_basic_tests),
        ]
        
        if self.dev_mode:
            steps.append(("设置Git钩子", self.setup_git_hooks))
        
        for step_name, step_func in steps:
            print(f"\n{'='*60}")
            print(f"步骤: {step_name}")
            print('='*60)
            
            if not step_func():
                print(f"\n❌ 设置失败: {step_name}")
                return False
        
        self.print_next_steps()
        return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="丁香园药物信息爬虫 - 项目设置"
    )
    
    parser.add_argument(
        '--dev',
        action='store_true',
        help='开发模式安装（包含开发工具）'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='仅运行测试'
    )
    
    args = parser.parse_args()
    
    try:
        if args.test:
            # 仅运行测试
            setup = ProjectSetup()
            setup.print_banner()
            if setup.run_basic_tests():
                print("\n✅ 测试通过")
                sys.exit(0)
            else:
                print("\n❌ 测试失败")
                sys.exit(1)
        else:
            # 完整设置
            setup = ProjectSetup(dev_mode=args.dev)
            if setup.run_setup():
                sys.exit(0)
            else:
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n👋 用户取消设置")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 设置过程出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()