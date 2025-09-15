# -*- coding: utf-8 -*-
"""
配置管理模块

功能：
- 管理系统全局配置
- 提供配置参数访问接口
- 支持环境变量覆盖
- 配置验证和默认值处理

作者：AI Assistant
创建时间：2025-01-15
"""

import os
from typing import List, Tuple, Optional
from pathlib import Path


class Config:
    """
    系统配置类
    
    功能：
    - 集中管理所有配置参数
    - 支持环境变量覆盖
    - 提供配置验证
    
    参数：无
    返回值：配置实例
    异常：配置验证失败时抛出ValueError
    """
    
    # ==================== 基础配置 ====================
    # 丁香园网站配置
    BASE_URL: str = "https://newdrugs.dxy.cn"
    SEARCH_URL: str = "/pc/search"
    DRUG_DETAIL_URL: str = "/pc/drug"
    
    # ==================== Jina AI配置 ====================
    # Jina AI服务配置（新增重要功能）
    JINA_API_URL: str = "https://r.jina.ai/"
    USE_JINA_FIRST: bool = True  # 优先使用Jina AI处理
    JINA_TIMEOUT: int = 30  # Jina AI请求超时时间
    JINA_MAX_RETRIES: int = 2  # Jina AI最大重试次数
    
    # ==================== 反爬配置 ====================
    # 请求控制配置
    REQUEST_DELAY: Tuple[int, int] = (2, 5)  # 请求间隔范围（秒）
    MAX_RETRIES: int = 3  # 最大重试次数
    TIMEOUT: int = 30  # 请求超时时间
    
    # Cookie管理配置
    COOKIE_EXPIRE_HOURS: int = 24  # Cookie过期时间（小时）
    AUTO_REFRESH_COOKIES: bool = True  # 自动刷新Cookie
    COOKIE_VALIDATION_ENABLED: bool = True  # 启用Cookie验证
    COOKIE_RETRY_ATTEMPTS: int = 2  # Cookie重试次数
    COOKIE_FILE: str = "data/cookies.json"  # Cookie文件路径
    
    # User-Agent池
    USER_AGENTS: List[str] = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
    ]
    
    # ==================== 浏览器配置 ====================
    # Chrome浏览器选项
    CHROME_OPTIONS: List[str] = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled",
        "--disable-extensions",
        "--disable-plugins",
        "--disable-images",  # 禁用图片加载，提高速度
        "--disable-javascript",  # 可选：禁用JS（如果不影响内容获取）
        "--headless",  # 无头模式
        "--window-size=1920,1080"
    ]
    
    # WebDriver配置
    WEBDRIVER_TIMEOUT: int = 30
    PAGE_LOAD_TIMEOUT: int = 30
    IMPLICIT_WAIT: int = 10
    
    # ==================== 目录配置 ====================
    # 项目根目录
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    
    # 各种目录路径
    OUTPUT_DIR: Path = PROJECT_ROOT / "output"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    DATA_DIR: Path = PROJECT_ROOT / "data"
    CACHE_DIR: Path = PROJECT_ROOT / "cache"
    
    # 独立目录配置
    USE_INDEPENDENT_DIRS: bool = True  # 是否使用独立目录
    CURRENT_SESSION_DIR: Optional[Path] = None  # 当前会话目录
    
    # 文件命名配置
    OUTPUT_FILENAME_TEMPLATE: str = "{drug_name}_{timestamp}.md"
    RAG_FILENAME_TEMPLATE: str = "{drug_name}_rag_{timestamp}.md"
    
    # ==================== 日志配置 ====================
    # 日志级别配置
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    
    # 日志文件配置
    LOG_FILE_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_FILE_BACKUP_COUNT: int = 5
    
    # ==================== RAG优化配置 ====================
    # RAG处理配置
    RAG_CHUNK_SIZE: int = 500  # 每个chunk的字符数
    RAG_CHUNK_OVERLAP: int = 50  # chunk重叠字符数
    RAG_ADD_LINE_NUMBERS: bool = True  # 是否添加行号
    RAG_ADD_CHUNK_MARKERS: bool = True  # 是否添加chunk标记
    
    # ==================== LLM集成配置 ====================
    # Ollama配置
    OLLAMA_CONFIG: dict = {
        'enabled': True,
        'provider': 'ollama',
        'model': 'qwen3:1.7b',  # 可选: qwen3:1.7b, nomic-embed-text:latest
        'embed_model': 'nomic-embed-text:latest',  # 嵌入模型
        'endpoint': 'http://localhost:11434',  # macOS本地环境使用localhost
        'chunk_optimization': True,
        'semantic_scoring': True,
        'timeout': 30,
        'max_retries': 2
    }
    
    # GLM4.5配置
    GLM_CONFIG: dict = {
        'enabled': True,
        'provider': 'zhipu',
        'model': 'glm-4.5-airx',  # 或 glm-4.5-plus, glm-4.5-air, glm-4.5-flash
        'api_key': os.getenv('GLM_API_KEY', ''),
        'endpoint': 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
        'temperature': 0.1,
        'max_tokens': 1000,
        'chunk_optimization': True,
        'semantic_scoring': True,
        'timeout': 30,
        'max_retries': 2
    }
    
    # 统一LLM配置
    LLM_CONFIG: dict = {
        'enabled': True,
        'primary_provider': 'ollama',  # 主要使用的LLM提供商
        'fallback_provider': 'zhipu',  # 备用LLM提供商
        'trigger_conditions': {
            'complex_content': True,      # 复杂内容自动触发
            'medical_terms': True,       # 医学术语密集时触发
            'table_processing': True,    # 表格处理时触发
            'ambiguous_boundaries': True # 边界模糊时触发
        },
        'fallback_mode': 'rule_based',   # LLM失败时回退到规则
        'cost_control': {
            'max_tokens_per_chunk': 2000,
            'daily_limit': 100000
        },
        'complexity_threshold': 50  # 复杂度阈值
    }
    
    # 内容提取配置
    EXTRACT_SECTIONS: List[str] = [
        "成份", "性状", "适应症", "规格", "用法用量", 
        "不良反应", "禁忌", "注意事项", "孕妇及哺乳期妇女用药",
        "儿童用药", "老年用药", "药物相互作用", "药物过量",
        "药理毒理", "药代动力学", "贮藏", "包装", "有效期",
        "执行标准", "批准文号", "生产企业"
    ]
    
    # ==================== 性能配置 ====================
    # 并发控制
    MAX_CONCURRENT_REQUESTS: int = 3
    MAX_WORKERS: int = 4
    
    # 缓存配置
    ENABLE_CACHE: bool = True
    CACHE_EXPIRE_HOURS: int = 24
    
    # 内存管理
    MAX_MEMORY_USAGE_MB: int = 512
    
    def __init__(self):
        """
        初始化配置
        
        功能：
        - 创建必要的目录
        - 从环境变量加载配置
        - 验证配置参数
        
        参数：无
        返回值：无
        异常：目录创建失败或配置验证失败时抛出异常
        """
        # 设置实例属性
        self.cookie_file = self.COOKIE_FILE
        self.cookie_expire_hours = self.COOKIE_EXPIRE_HOURS
        self.auto_refresh_cookies = self.AUTO_REFRESH_COOKIES
        self.cookie_validation_enabled = self.COOKIE_VALIDATION_ENABLED
        self.cookie_retry_attempts = self.COOKIE_RETRY_ATTEMPTS
        
        self._load_from_env()
        self._create_directories()
        self._validate_config()
        
        # 初始化独立目录
        if self.USE_INDEPENDENT_DIRS:
            self._create_session_directory()
    
    def _create_session_directory(self) -> None:
        """
        创建独立的会话目录
        
        功能：
        - 生成格式为yymmdd+序号的目录名
        - 确保目录唯一性
        - 更新当前会话目录路径
        
        参数：无
        返回值：无
        异常：目录创建失败时抛出OSError
        """
        import datetime
        
        # 生成日期前缀（yymmdd格式）
        today = datetime.datetime.now()
        date_prefix = today.strftime("%y%m%d")
        
        # 查找当天已存在的目录，确定序号
        base_output_dir = self.PROJECT_ROOT / "output"
        base_output_dir.mkdir(exist_ok=True)
        
        sequence = 1
        while True:
            dir_name = f"{date_prefix}{sequence:02d}"
            session_dir = base_output_dir / dir_name
            
            if not session_dir.exists():
                break
            sequence += 1
            
            # 防止无限循环
            if sequence > 99:
                raise OSError(f"当天目录数量已达上限（99个）")
        
        # 创建会话目录
        try:
            session_dir.mkdir(parents=True, exist_ok=True)
            self.CURRENT_SESSION_DIR = session_dir
            print(f"📁 创建会话目录: {session_dir}")
        except OSError as e:
            raise OSError(f"无法创建会话目录 {session_dir}: {e}")
    
    def _load_from_env(self) -> None:
        """
        从环境变量加载配置
        
        功能：
        - 支持通过环境变量覆盖默认配置
        - 自动类型转换
        
        参数：无
        返回值：无
        异常：类型转换失败时记录警告
        """
        # 基础URL配置
        self.BASE_URL = os.getenv('DXY_BASE_URL', self.BASE_URL)
        
        # Jina AI配置
        self.JINA_API_URL = os.getenv('JINA_API_URL', self.JINA_API_URL)
        self.USE_JINA_FIRST = os.getenv('USE_JINA_FIRST', str(self.USE_JINA_FIRST)).lower() == 'true'
        
        # 超时配置
        try:
            self.TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', str(self.TIMEOUT)))
            self.JINA_TIMEOUT = int(os.getenv('JINA_TIMEOUT', str(self.JINA_TIMEOUT)))
        except ValueError:
            pass  # 使用默认值
        
        # 日志级别
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', self.LOG_LEVEL).upper()
        
        # Cookie管理配置
        try:
            self.cookie_expire_hours = int(os.getenv('COOKIE_EXPIRE_HOURS', str(self.cookie_expire_hours)))
            self.cookie_retry_attempts = int(os.getenv('COOKIE_RETRY_ATTEMPTS', str(self.cookie_retry_attempts)))
        except ValueError:
            pass  # 使用默认值
            
        self.auto_refresh_cookies = os.getenv('AUTO_REFRESH_COOKIES', str(self.auto_refresh_cookies)).lower() == 'true'
        self.cookie_validation_enabled = os.getenv('COOKIE_VALIDATION_ENABLED', str(self.cookie_validation_enabled)).lower() == 'true'
        self.cookie_file = os.getenv('COOKIE_FILE', self.cookie_file)
    
    def _create_directories(self) -> None:
        """
        创建必要的目录
        
        功能：
        - 创建输出、日志、数据、缓存目录
        - 确保目录权限正确
        
        参数：无
        返回值：无
        异常：目录创建失败时抛出OSError
        """
        directories = [
            self.OUTPUT_DIR,
            self.LOGS_DIR,
            self.DATA_DIR,
            self.CACHE_DIR
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise OSError(f"无法创建目录 {directory}: {e}")
    
    def _validate_config(self) -> None:
        """
        验证配置参数
        
        功能：
        - 检查必要参数是否存在
        - 验证参数值的合理性
        - 检查URL格式
        
        参数：无
        返回值：无
        异常：配置验证失败时抛出ValueError
        """
        # 验证URL格式
        if not self.BASE_URL.startswith(('http://', 'https://')):
            raise ValueError(f"无效的BASE_URL: {self.BASE_URL}")
        
        if not self.JINA_API_URL.startswith(('http://', 'https://')):
            raise ValueError(f"无效的JINA_API_URL: {self.JINA_API_URL}")
        
        # 验证超时时间
        if self.TIMEOUT <= 0 or self.JINA_TIMEOUT <= 0:
            raise ValueError("超时时间必须大于0")
        
        # 验证重试次数
        if self.MAX_RETRIES < 0 or self.JINA_MAX_RETRIES < 0:
            raise ValueError("重试次数不能为负数")
        
        # 验证请求间隔
        if len(self.REQUEST_DELAY) != 2 or self.REQUEST_DELAY[0] > self.REQUEST_DELAY[1]:
            raise ValueError("请求间隔配置无效")
    
    def get_full_search_url(self) -> str:
        """
        获取完整的搜索URL
        
        功能：拼接基础URL和搜索路径
        
        参数：无
        返回值：完整的搜索URL
        异常：无
        """
        return f"{self.BASE_URL.rstrip('/')}{self.SEARCH_URL}"
    
    def get_search_url(self, keyword: str = None) -> str:
        """
        获取搜索URL
        
        功能：
        - 构建带关键词的搜索URL
        - 对中文关键词进行URL编码
        - 提供向后兼容性
        
        参数：
        - keyword (str, optional): 搜索关键词
        
        返回值：完整的搜索URL字符串
        异常：无
        """
        from urllib.parse import quote
        
        base_url = self.get_full_search_url()
        if keyword:
            # 对中文关键词进行URL编码
            encoded_keyword = quote(keyword, safe='')
            return f"{base_url}?keyword={encoded_keyword}"
        return base_url
    
    def get_full_drug_url(self, drug_id: str) -> str:
        """
        获取完整的药品详情URL
        
        功能：根据药品ID生成完整的详情页URL
        
        参数：
        - drug_id: 药品ID
        
        返回值：完整的药品详情URL
        异常：无
        """
        return f"{self.BASE_URL.rstrip('/')}{self.DRUG_DETAIL_URL}/{drug_id}"
    
    def get_jina_url(self, target_url: str) -> str:
        """
        获取Jina AI处理URL
        
        功能：将目标URL转换为Jina AI处理URL
        
        参数：
        - target_url: 目标网页URL
        
        返回值：Jina AI处理URL
        异常：无
        """
        return f"{self.JINA_API_URL.rstrip('/')}/{target_url}"
    
    def get_output_filepath(self, drug_name: str, is_rag: bool = False) -> Path:
        """
        获取输出文件路径
        
        功能：根据药品名称和类型生成输出文件路径
        
        参数：
        - drug_name: 药品名称
        - is_rag: 是否为RAG格式文件
        
        返回值：输出文件路径
        异常：无
        """
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 清理文件名中的非法字符
        safe_drug_name = "".join(c for c in drug_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_drug_name = safe_drug_name.replace(' ', '_')
        
        if is_rag:
            filename = self.RAG_FILENAME_TEMPLATE.format(
                drug_name=safe_drug_name,
                timestamp=timestamp
            )
        else:
            filename = self.OUTPUT_FILENAME_TEMPLATE.format(
                drug_name=safe_drug_name,
                timestamp=timestamp
            )
        
        # 使用独立目录或默认目录
        if self.USE_INDEPENDENT_DIRS and self.CURRENT_SESSION_DIR:
            return self.CURRENT_SESSION_DIR / filename
        else:
            return self.OUTPUT_DIR / filename
    
    def __str__(self) -> str:
        """
        配置信息字符串表示
        
        功能：返回主要配置信息的字符串表示
        
        参数：无
        返回值：配置信息字符串
        异常：无
        """
        return f"""丁香园爬虫配置:
- 基础URL: {self.BASE_URL}
- Jina AI: {self.JINA_API_URL} (启用: {self.USE_JINA_FIRST})
- 超时时间: {self.TIMEOUT}s
- 请求间隔: {self.REQUEST_DELAY}s
- 输出目录: {self.OUTPUT_DIR}
- 日志级别: {self.LOG_LEVEL}"""


# 全局配置实例
config = Config()


if __name__ == "__main__":
    # 配置测试
    print("配置加载测试:")
    print(config)
    print(f"\n搜索URL: {config.get_full_search_url()}")
    print(f"药品URL示例: {config.get_full_drug_url('12345')}")
    print(f"Jina URL示例: {config.get_jina_url('https://example.com')}")