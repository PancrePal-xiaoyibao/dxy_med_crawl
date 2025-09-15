# 丁香园药物信息爬虫

一个功能强大的药物信息爬取工具，支持从丁香园网站获取药物详细信息，并提供多种数据处理和导出功能。

## 🚀 主要特性

- **智能内容提取**：集成Jina AI，自动清洗和结构化网页内容
- **多格式输出**：支持JSON、CSV、Excel等多种数据格式
- **智能反爬虫**：
  - 自动Cookie获取和更新
  - Cookie有效性检测和刷新
  - 智能延迟和User-Agent轮换
  - 请求失败自动重试机制
- **异步处理**：支持批量并发爬取，提高效率
- **数据优化**：针对RAG应用优化的数据结构和分块策略
- **完整日志**：详细的操作日志和性能监控
- **灵活配置**：支持环境变量和配置文件自定义

## 📋 系统要求

- Python 3.8+
- 操作系统: Windows/macOS/Linux
- 内存: 建议4GB以上
- 网络: 稳定的互联网连接

## 🛠️ 安装说明

### 1. 克隆项目

```bash
git clone <repository-url>
cd 丁香园pc助手说明书获取
```

### 2. 创建虚拟环境（推荐）

```bash
# 使用venv
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量（可选）

创建 `.env` 文件：

```bash
# 基础配置
BASE_URL=https://drugs.dxy.cn
JINA_BASE_URL=https://r.jina.ai

# 输出配置
OUTPUT_DIR=./output
LOGS_DIR=./logs
DATA_DIR=./data

# 请求配置
REQUEST_DELAY=1.0
MAX_RETRIES=3
TIMEOUT=30

# 反爬虫配置
USE_PROXY=false
ROTATE_USER_AGENT=true
RANDOM_DELAY=true
```

## 🎯 快速开始

### 基础用法

```bash
# 搜索单个药物
python src/main.py --drug "阿司匹林"

# 搜索多个药物
python src/main.py --drugs "阿司匹林,布洛芬,对乙酰氨基酚"

# 从文件读取药物列表
python src/main.py --file drugs.txt
```

### 高级用法

```bash
# 使用Jina AI处理
python src/main.py --drug "阿司匹林" --use-jina

# 指定输出格式
python src/main.py --drug "阿司匹林" --format json,csv,excel

# 异步批量爬取
python src/main.py --drugs "阿司匹林,布洛芬" --async --batch-size 5

# 详细日志输出
python src/main.py --drug "阿司匹林" --verbose

# 自定义输出目录
python src/main.py --drug "阿司匹林" --output ./my_output
```

## 📁 项目结构

```
丁香园pc助手说明书获取/
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── main.py            # 主程序入口
│   ├── modules/           # 核心模块
│   │   ├── __init__.py
│   │   ├── config.py      # 配置管理
│   │   ├── logger.py      # 日志管理
│   │   ├── network.py     # 网络请求
│   │   ├── parser.py      # 页面解析
│   │   ├── processor.py   # 数据处理
│   │   └── jina_processor.py  # Jina AI处理
│   └── utils/             # 工具函数
│       └── __init__.py
├── tests/                 # 测试文件
│   └── test_basic.py      # 基础功能测试
├── output/                # 输出目录
├── logs/                  # 日志目录
├── data/                  # 数据目录
├── requirements.txt       # 依赖包列表
├── .env.example          # 环境变量示例
└── README.md             # 说明文档
```

## 🔧 配置说明

### 环境变量配置

复制 `.env.example` 为 `.env` 并根据需要修改：

```bash
cp .env.example .env
```

### 主要配置项

#### 基础配置
- `BASE_URL`: 丁香园药物数据库基础URL
- `OUTPUT_DIR`: 数据输出目录
- `LOG_LEVEL`: 日志级别（DEBUG/INFO/WARNING/ERROR）

#### 网络和反爬虫配置
- `REQUEST_DELAY`: 请求间隔时间（秒）
- `MAX_RETRIES`: 最大重试次数
- `TIMEOUT`: 请求超时时间（秒）

#### Cookie管理配置
- `COOKIE_EXPIRE_HOURS`: Cookie过期时间（小时，默认24）
- `AUTO_REFRESH_COOKIES`: 自动刷新Cookie（true/false）
- `COOKIE_VALIDATION_ENABLED`: 启用Cookie验证（true/false）
- `COOKIE_RETRY_ATTEMPTS`: Cookie失效重试次数

#### Jina AI配置
- `JINA_API_KEY`: Jina AI API密钥（可选）
- `USE_JINA_AI`: 是否使用Jina AI处理（true/false）

## 📊 输出格式

### JSON格式

```json
{
  "name": "阿司匹林片",
  "specifications": ["100mg×30片/盒"],
  "manufacturer": "某某制药有限公司",
  "indications": "用于解热镇痛",
  "dosage": "口服，成人一次0.3-0.6g",
  "contraindications": "对本品过敏者禁用",
  "adverse_reactions": "可能出现胃肠道反应",
  "precautions": "孕妇及哺乳期妇女慎用",
  "drug_interactions": "与华法林合用需谨慎",
  "storage": "密封，在干燥处保存",
  "approval_number": "国药准字H12345678",
  "source_url": "https://drugs.dxy.cn/drug/123",
  "crawl_time": "2024-01-01T12:00:00",
  "processing_method": "standard"
}
```

### CSV格式

包含所有字段的表格格式，便于Excel打开和数据分析。

### Excel格式

多工作表Excel文件：
- `药物信息`: 主要药物数据
- `统计信息`: 爬取统计和汇总
- `错误日志`: 爬取过程中的错误记录

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
python tests/test_basic.py

# 使用pytest运行（如果安装了pytest）
pytest tests/ -v
```

### 测试覆盖

- ✅ 配置管理模块
- ✅ 日志管理模块
- ✅ 网络请求模块
- ✅ 页面解析模块
- ✅ 数据处理模块
- ✅ Jina AI处理模块
- ✅ 集成测试
- ✅ 异步功能测试

## 🚨 注意事项

### 使用限制

1. **请遵守robots.txt**: 尊重网站的爬虫协议
2. **合理控制频率**: 避免对目标网站造成过大压力
3. **仅供学习研究**: 请勿用于商业用途
4. **数据准确性**: 爬取的数据仅供参考，请以官方信息为准

### 反爬虫策略

系统内置多种反爬虫机制：

- **User-Agent轮换**: 随机使用不同的浏览器标识
- **请求频率控制**: 自动控制请求间隔
- **随机延迟**: 增加请求时间的随机性
- **会话管理**: 维护Cookie和会话状态
- **错误重试**: 自动重试失败的请求

### 性能优化

- **异步爬取**: 支持并发请求提高效率
- **内存管理**: 及时释放不需要的数据
- **缓存机制**: 避免重复请求相同内容
- **批量处理**: 支持批量数据处理和导出

## 🔍 故障排除

### 常见问题

**Q: 安装依赖时出错**
A: 确保Python版本>=3.8，建议使用虚拟环境

**Q: 爬取失败或返回空数据**
A: 检查网络连接，确认目标网站可访问，适当增加请求延迟

**Q: 内存使用过高**
A: 减少批量大小，启用数据清理选项

**Q: Jina AI处理失败**
A: 检查网络连接，确认Jina AI服务可用

### 日志分析

系统会在 `logs/` 目录生成详细日志：

- `app.log`: 应用程序日志
- `performance.log`: 性能监控日志
- `error.log`: 错误日志

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements.txt

# 安装代码格式化工具
pip install black isort flake8

# 格式化代码
black src/
isort src/

# 代码检查
flake8 src/
```

### 提交规范

- 使用清晰的提交信息
- 确保代码通过所有测试
- 遵循现有的代码风格
- 添加必要的文档和注释

## 📄 许可证

本项目仅供学习和研究使用，请遵守相关法律法规和网站使用条款。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交Issue: [GitHub Issues]()
- 邮箱: [your-email@example.com]()

## 🙏 致谢

感谢以下开源项目的支持：

- [requests](https://requests.readthedocs.io/): HTTP请求库
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/): HTML解析库
- [aiohttp](https://aiohttp.readthedocs.io/): 异步HTTP客户端
- [pandas](https://pandas.pydata.org/): 数据处理库
- [Jina AI](https://jina.ai/): AI驱动的内容处理服务

---

**免责声明**: 本工具仅供学习和研究使用，使用者需自行承担使用风险，开发者不对任何损失负责。请遵守目标网站的使用条款和相关法律法规。# dxy_med_crawl
