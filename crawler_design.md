# 丁香园PC助手药品说明书爬虫设计文档

## 项目概述

### 目标
开发一个Python爬虫脚本，用于自动化获取丁香园PC助手网站的药品说明书信息，并进行RAG格式优化处理。

### 核心功能
1. 模拟浏览器操作，绕过反爬机制
2. 搜索指定药品关键词
3. 获取搜索结果列表
4. 提取药品详情页面的说明书内容
5. 保存为结构化markdown格式
6. 进行RAG格式优化处理

## 技术架构设计

### 核心技术栈
- **Python 3.8+**
- **Selenium WebDriver** - 模拟浏览器操作
- **requests + requests-html** - HTTP请求处理
- **Jina AI API** - 网页内容智能处理（新增）
- **BeautifulSoup4** - HTML解析
- **fake-useragent** - 用户代理轮换
- **time/random** - 请求间隔控制
- **logging** - 日志记录
- **json** - 数据序列化
- **re** - 正则表达式处理

### 反爬策略分析与应对

#### 1. 检测到的反爬机制
- **复杂的Cookie验证**：包含多个加密Cookie字段
- **User-Agent检测**：需要真实浏览器标识
- **请求频率限制**：过快请求会被封禁
- **JavaScript动态加载**：页面内容通过JS渲染
- **Session管理**：需要维持登录状态

#### 2. 应对策略
- **Jina AI优先策略**：使用r.jina.ai直接获取清洁内容（推荐）
- **浏览器模拟**：使用Selenium + Chrome无头模式（备选）
- **智能Cookie管理**：
  - 自动获取和保存Cookie
  - Cookie有效性检测和自动更新
  - 支持多账户Cookie轮换
  - Cookie过期自动刷新机制
- **请求间隔**：随机延迟2-5秒
- **User-Agent轮换**：使用真实浏览器UA池
- **代理IP轮换**：避免IP封禁（可选）
- **异常重试**：网络异常自动重试机制
- **会话保持**：维持长期有效的会话状态

## 系统架构

```
丁香园爬虫系统
├── 配置管理模块 (config.py)
├── 网络请求模块 (network.py)
├── 页面解析模块 (parser.py)
├── 数据处理模块 (processor.py)
├── 文件管理模块 (file_manager.py)
├── 日志管理模块 (logger.py)
├── 主控制器 (main.py)
└── 工具函数 (utils.py)
```

## Jina AI集成方案

### Jina AI处理流程
```python
class JinaProcessor:
    """
    Jina AI网页内容处理器
    功能：将药品详情页URL转换为清洁的markdown内容
    """
    
    def __init__(self, config):
        self.jina_url = config.JINA_API_URL
        self.timeout = config.JINA_TIMEOUT
        
    def process_url(self, drug_detail_url):
        """
        使用Jina AI处理药品详情页
        参数：drug_detail_url - 药品详情页URL
        返回：处理后的markdown内容
        异常：网络异常时返回None，触发降级策略
        """
        jina_request_url = f"{self.jina_url}{drug_detail_url}"
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        }
        
        try:
            response = requests.post(
                jina_request_url,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Jina AI返回状态码: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Jina AI处理失败: {str(e)}")
            return None
```

### Jina AI优势分析
1. **绕过反爬机制**：无需处理复杂的Cookie和JS渲染
2. **内容质量高**：自动提取主要内容，过滤广告和无关信息
3. **处理速度快**：无需启动浏览器，减少资源消耗
4. **格式标准化**：直接输出markdown格式，便于后续处理
5. **稳定性好**：减少因网站反爬升级导致的失败

### 降级策略
当Jina AI处理失败时，自动切换到传统Selenium爬虫方式：
```python
def get_drug_content(self, drug_url):
    # 优先尝试Jina AI
    if self.config.USE_JINA_FIRST:
        jina_content = self.jina_processor.process_url(drug_url)
        if jina_content:
            logger.info("使用Jina AI成功获取内容")
            return jina_content
        else:
            logger.warning("Jina AI失败，降级到传统爬虫")
    
    # 降级到传统爬虫方式
    return self.browser_crawler.get_content(drug_url)
```

## 详细模块设计

### 1. 配置管理模块 (config.py)
```python
class Config:
    # 基础配置
    BASE_URL = "https://newdrugs.dxy.cn"
    SEARCH_URL = "/pc/search"
    DRUG_DETAIL_URL = "/pc/drug"
    
    # Jina AI配置（新增）
    JINA_API_URL = "https://r.jina.ai/"
    USE_JINA_FIRST = True  # 优先使用Jina AI处理
    JINA_TIMEOUT = 30
    
    # 反爬配置
    REQUEST_DELAY = (2, 5)  # 请求间隔范围
    MAX_RETRIES = 3
    TIMEOUT = 30
    
    # 浏览器配置
    CHROME_OPTIONS = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled"
    ]
```

### 2. 网络请求模块 (network.py)
- **BrowserManager类**：管理Selenium WebDriver
- **RequestManager类**：处理HTTP请求
- **JinaProcessor类**：使用Jina AI处理网页内容
- **CookieManager类**：Cookie持久化管理
- **ProxyManager类**：代理IP管理（可选）
- **搜索关键词编码处理类**： 要把搜索关键词改为URL编码

### 3. 页面解析模块 (parser.py)
- **SearchResultParser类**：解析搜索结果页面
- **DrugDetailParser类**：解析药品详情页面
- **ContentExtractor类**：提取说明书内容

### 4. 数据处理模块 (processor.py)
- **DataCleaner类**：数据清洗
- **MarkdownFormatter类**：Markdown格式化
- **RAGOptimizer类**：RAG格式优化

### 5. 文件管理模块 (file_manager.py)
- **FileManager类**：文件读写操作
- **PathManager类**：路径管理
- **BackupManager类**：数据备份

## 核心流程设计

### 核心流程设计

### 主要工作流程
```
1. 初始化配置和浏览器
2. 访问丁香园首页
3. 输入搜索关键词
4. 解析搜索结果页面
5. 遍历药品链接
6. 选择数据获取方式：
   a) Jina AI处理（推荐）- 直接获取清洁内容
   b) 传统爬虫方式 - 浏览器解析
7. 提取药品详情信息
8. 格式化为Markdown
9. RAG优化处理
10. 保存文件
11. 清理资源
```

### 错误处理机制
- **网络异常**：自动重试，记录日志
- **Jina AI失败**：自动降级到传统爬虫方式
- **解析异常**：跳过当前项目，继续处理
- **反爬检测**：更换策略，延长间隔
- **资源不足**：清理缓存，释放内存

## 数据结构设计

### 药品信息数据结构
```python
class DrugInfo:
    def __init__(self):
        self.name = ""           # 药品名称
        self.english_name = ""   # 英文名称
        self.drug_id = ""        # 药品ID
        self.approval_date = "" # 核准日期
        self.modify_date = ""    # 修改日期
        self.components = ""     # 成份
        self.indications = ""    # 适应症
        self.usage = ""          # 用法用量
        self.adverse_reactions = "" # 不良反应
        self.contraindications = "" # 禁忌
        self.precautions = ""    # 注意事项
        self.interactions = ""   # 药物相互作用
        self.pharmacology = ""   # 药理毒理
        self.pharmacokinetics = "" # 药代动力学
        self.storage = ""        # 贮藏
        self.packaging = ""      # 包装
        self.validity = ""       # 有效期
        self.manufacturer = ""   # 生产企业
```

## 输出格式
- 保存为markdown格式文件
- 文件名格式：药品名称_规格_时间戳.md
- 保持原有的结构和格式

## RAG embedding预处理要求
对于切分前的各种格式文档，进行预处理，从而提高chunk的准确且分。通过：
1. 增加行号如<1>,<2>
2. 增加chunk切分标记符号如"+","//"等
3. 根据主题和内容进行分段，插入分段提示"======"，进行主题段落区分

Rules: 不要修改文档内容，只进行格式整理，只允许修改chunk和符号，序号。输出前进行二次检查。处理文件添加后缀"_optimized"后，以markdown文件格式保存在同路径下。

## RAG优化处理规则

### 格式优化策略
1. **行号标记**：为每行添加`<1>`, `<2>`等标记
2. **分段标记**：添加`==chunk/start==`和`==chunk/end==`
3. **内容分块**：按主题和逻辑结构分段
4. **符号标记**：使用`+`, `//`等符号增强可读性

### 分块规则
- **药品基本信息**：名称、成份、规格等
- **适应症与用法**：适应症、用法用量
- **安全信息**：不良反应、禁忌、注意事项
- **药理信息**：药理毒理、药代动力学
- **其他信息**：贮藏、包装、生产企业等

## 日志与监控

### 日志级别
- **DEBUG**：详细调试信息
- **INFO**：一般操作信息
- **WARNING**：警告信息
- **ERROR**：错误信息
- **CRITICAL**：严重错误

### 监控指标
- 请求成功率
- 数据提取完整性
- 处理速度
- 错误类型统计

## 性能优化

### 优化策略
1. **并发控制**：合理控制并发数量
2. **缓存机制**：缓存已处理的数据
3. **增量更新**：只处理新增或变更的数据
4. **资源管理**：及时释放浏览器资源
5. **内存优化**：大文件分块处理

## 部署与运行

### 环境要求
- Python 3.8+
- Chrome浏览器
- ChromeDriver
- 稳定的网络连接

### 运行参数
```bash
python main.py --keyword "药品名称" --output "输出目录" --delay 3
```

## 风险评估与应对

### 主要风险
1. **反爬升级**：网站加强反爬机制
2. **法律风险**：数据使用合规性
3. **服务稳定性**：目标网站服务中断
4. **数据质量**：页面结构变化导致解析失败

### 应对措施
1. **持续监控**：定期检查爬虫运行状态
2. **策略更新**：及时调整反爬策略
3. **数据验证**：增加数据质量检查
4. **备用方案**：准备多种数据获取方式

## 开发计划

### 第一阶段：基础框架（1-2天）
- 搭建项目结构
- 实现基础配置管理
- 完成网络请求模块

### 第二阶段：核心功能（2-3天）
- 实现页面解析功能
- 完成数据提取逻辑
- 添加反爬策略

### 第三阶段：优化处理（1-2天）
- 实现RAG格式优化
- 完善错误处理
- 添加日志监控

### 第四阶段：测试完善（1天）
- 功能测试
- 性能优化
- 文档完善

## 注意事项

1. **合规使用**：确保数据使用符合相关法律法规
2. **频率控制**：避免对目标网站造成过大压力
3. **数据保护**：妥善保管获取的数据
4. **版本管理**：及时更新以适应网站变化
5. **异常处理**：完善的异常处理和恢复机制

---

**设计文档版本**：v1.0  
**创建日期**：2025年1月15日  
**最后更新**：2025年1月15日