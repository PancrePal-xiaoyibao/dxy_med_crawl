# Chunk处理逻辑说明

## 概述

本项目实现了智能的RAG（Retrieval-Augmented Generation）预处理功能，通过添加chunk边界标记来优化文档分割，提高向量检索的准确性。

## 核心功能

### 1. 智能分块策略

- **语义完整性保证**：确保相关内容在同一个chunk中
- **主题边界识别**：根据标题和关键词自动识别章节边界
- **大小控制**：动态调整chunk大小，避免过长或过短的分块

### 2. 分块标记系统

#### 文档结构标记
```markdown
====== 文档开始 ======
[文档内容]
====== 文档结束 ======
```

#### Chunk边界标记
```markdown
[内容块1]

[CHUNK_BOUNDARY]

[内容块2]
```

### 3. 关键词识别

系统会自动识别以下类型的分段关键词：

- **Markdown标题**：`#`, `##`, `###`
- **药品信息章节**：基本信息、成分、适应症、用法用量
- **安全信息**：不良反应、禁忌、注意事项
- **药理信息**：药理毒理、药代动力学
- **其他信息**：贮藏、包装、生产企业

## 处理流程

### 1. 文档预处理

```python
def apply_rag_preprocessing(content: str) -> str:
    """
    应用RAG预处理规则
    
    功能:
    - 智能添加chunk切分标记
    - 基于语义完整性进行分割
    
    参数:
        content: 原始内容
        
    返回:
        str: 预处理后的内容
    """
```

### 2. 分块参数配置

- **最大chunk大小**：800字符
- **最小chunk大小**：200字符
- **强制分割阈值**：超过最大大小且行数>5时强制分割

### 3. 处理规则

1. **主题分段优先**：遇到新的主题关键词时创建新chunk
2. **大小控制**：超过最大大小时强制分割
3. **内容完整性**：保持原始内容不变，仅添加标记
4. **边界清晰**：每个chunk边界都有明确的`[CHUNK_BOUNDARY]`标记

## 使用示例

### 原始文件处理

```bash
# 处理单个文件
python process_rag_file.py
```

### 批量处理

```python
from src.modules.processor import DataExporter

# 初始化处理器
exporter = DataExporter(config, logger)

# 生成RAG优化文件
optimized_file = exporter._generate_rag_optimized_file(original_file)
```

## 输出结果

### 文件命名规则

- **原始文件**：`药品名称.md`
- **优化文件**：`药品名称_optimized.md`

### 统计信息

处理完成后会显示：
- 原始文件大小
- 优化后文件大小
- 生成的chunk数量
- Chunk大小分布

## 质量保证

### 1. 内容完整性
- ✅ 保持原始内容100%不变
- ✅ 仅添加格式标记和边界标识
- ✅ 支持各种文档格式和编码

### 2. 分块质量
- ✅ 语义完整性保证
- ✅ 主题边界清晰
- ✅ 大小分布合理
- ✅ 检索友好的结构

### 3. 兼容性
- ✅ 支持中英文混合内容
- ✅ 兼容Markdown格式
- ✅ 适配各种RAG系统

## 配置参数

在`config.py`中可以调整以下参数：

```python
# RAG优化配置
RAG_CHUNK_SIZE: int = 500  # 每个chunk的字符数
RAG_CHUNK_OVERLAP: int = 50  # chunk重叠字符数
RAG_ADD_LINE_NUMBERS: bool = True  # 是否添加行号
RAG_ADD_CHUNK_MARKERS: bool = True  # 是否添加chunk标记
```

## 技术特点

1. **智能识别**：基于关键词和语义结构自动分段
2. **动态调整**：根据内容长度动态调整chunk大小
3. **边界清晰**：明确的标记系统便于后续处理
4. **质量保证**：保持原始内容完整性
5. **高效处理**：优化的算法确保处理速度

## LLM集成优化

### 多LLM提供商集成

可以结合多种LLM（本地Ollama、智谱GLM等）来进一步提高chunk处理的准确性：

#### Ollama本地LLM

```python
# 示例：使用Ollama优化chunk分割
import requests
import json

def optimize_chunk_with_llm(text_chunk, context=""):
    """
    使用Ollama本地LLM优化chunk分割点
    
    Args:
        text_chunk (str): 待优化的文本块
        context (str): 上下文信息
    
    Returns:
        dict: 优化建议和分割点
    """
    prompt = f"""
    请分析以下医药说明书文本，建议最佳的分割点：
    
    文本内容：{text_chunk}
    上下文：{context}
    
    请返回JSON格式的分割建议，包括：
    1. 建议的分割点位置
    2. 分割理由
    3. 语义完整性评分
    """
    
    response = requests.post('http://host.docker.internal:11434/api/generate', 
                            json={
                                'model': 'qwen3:1.7b',  # 或 nomic-embed-text:latest
                                'prompt': prompt,
                                'stream': False
                            })
    
    return json.loads(response.json()['response'])

#### GLM4.5集成

```python
# 示例：使用智谱GLM4.5优化chunk分割
import requests
import json

def optimize_chunk_with_glm(text_chunk, context="", api_key=""):
    """
    使用智谱GLM4.5优化chunk分割点
    
    Args:
        text_chunk (str): 待优化的文本块
        context (str): 上下文信息
        api_key (str): 智谱AI API密钥
    
    Returns:
        dict: 优化建议和分割点
    
    Raises:
        requests.RequestException: API请求异常
        json.JSONDecodeError: JSON解析异常
    """
    prompt = f"""
    请分析以下医药说明书文本，建议最佳的分割点：
    
    文本内容：{text_chunk}
    上下文：{context}
    
    请返回JSON格式的分割建议，包括：
    1. 建议的分割点位置
    2. 分割理由
    3. 语义完整性评分（1-10分）
    4. 专业术语保护建议
    """
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': 'glm-4-plus',
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ],
        'temperature': 0.1,
        'max_tokens': 1000
    }
    
    response = requests.post(
        'https://open.bigmodel.cn/api/paas/v4/chat/completions',
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        content = result['choices'][0]['message']['content']
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # 如果返回的不是标准JSON，进行简单解析
            return {'raw_response': content, 'status': 'needs_parsing'}
    else:
        raise requests.RequestException(f'GLM API请求失败: {response.status_code}')
 ```

### LLM增强功能

- **语义边界识别**：LLM可以更准确地识别语义完整的分割点
- **专业术语处理**：针对医药专业术语进行智能分组
- **上下文保持**：确保重要信息不被分割破坏
- **质量评估**：对分割结果进行智能评分和优化建议

### 配置示例

```python
# config.py 中添加LLM配置
 # Ollama配置
  OLLAMA_CONFIG = {
      'enabled': True,
      'provider': 'ollama',
      'model': 'qwen3:1.7b',  # 可选: qwen3:1.7b, nomic-embed-text:latest
      'endpoint': 'http://host.docker.internal:11434',
      'chunk_optimization': True,
      'semantic_scoring': True
  }
  
  # GLM4.5配置
  GLM_CONFIG = {
      'enabled': True,
      'provider': 'zhipu',
      'model': 'glm-4.5-airx',  # 或 glm-4.5-plus, glm-4.5-air, glm-4.5-flash
      'api_key': 'your_zhipu_api_key_here',
      'endpoint': 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
      'temperature': 0.1,
      'max_tokens': 1000,
      'chunk_optimization': True,
      'semantic_scoring': True
  }
  
  # 统一LLM配置
  LLM_CONFIG = {
      'primary_provider': 'ollama',  # 主要使用的LLM提供商
      'fallback_provider': 'zhipu',  # 备用LLM提供商
      'ollama': OLLAMA_CONFIG,
      'zhipu': GLM_CONFIG
  }
```

## 使用策略建议

### 推荐配置：特定情况使用LLM

基于性能、成本和准确性的综合考虑，建议采用**智能触发策略**：

```python
# 推荐的LLM使用策略
LLM_CONFIG = {
    'enabled': True,
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
    }
}
```

### 复杂度判断规则

系统通过以下算法自动判断内容复杂度：

```python
def assess_content_complexity(text_chunk):
    """
    评估文本块的复杂度
    
    Args:
        text_chunk (str): 待评估的文本块
    
    Returns:
        dict: 包含复杂度评分和触发条件的字典
    """
    complexity_score = 0
    triggers = []
    
    # 1. 医学术语密度检测
    medical_terms = ['适应症', '禁忌症', '不良反应', '药代动力学', '临床试验', 
                    '给药方法', '注意事项', '药物相互作用', '毒理学']
    medical_density = sum(1 for term in medical_terms if term in text_chunk) / len(medical_terms)
    if medical_density > 0.3:
        complexity_score += 30
        triggers.append('medical_terms')
    
    # 2. 表格结构检测
    table_indicators = ['|', '┌', '├', '└', '┬', '┼', '┴']
    if any(indicator in text_chunk for indicator in table_indicators):
        complexity_score += 25
        triggers.append('table_processing')
    
    # 3. 数值密度检测
    import re
    numbers = re.findall(r'\d+(?:\.\d+)?(?:%|mg|ml|g|kg|次|天|小时|分钟)', text_chunk)
    if len(numbers) > 5:
        complexity_score += 20
        triggers.append('numerical_data')
    
    # 4. 句子复杂度检测
    sentences = text_chunk.split('。')
    avg_sentence_length = sum(len(s) for s in sentences) / len(sentences) if sentences else 0
    if avg_sentence_length > 50:
        complexity_score += 15
        triggers.append('complex_sentences')
    
    # 5. 特殊符号和格式检测
    special_chars = ['®', '™', '©', '±', '≥', '≤', '→', '↑', '↓']
    if any(char in text_chunk for char in special_chars):
        complexity_score += 10
        triggers.append('special_formatting')
    
    # 6. 边界模糊性检测
    boundary_keywords = ['另外', '此外', '同时', '然而', '但是', '因此', '所以']
    boundary_count = sum(1 for keyword in boundary_keywords if keyword in text_chunk)
    if boundary_count > 2:
        complexity_score += 15
        triggers.append('ambiguous_boundaries')
    
    return {
        'complexity_score': complexity_score,
        'is_complex': complexity_score >= 50,  # 阈值：50分
        'triggers': triggers,
        'recommendation': 'llm' if complexity_score >= 50 else 'rule_based'
    }

# 使用示例
def should_use_llm(text_chunk):
    """
    判断是否应该使用LLM处理
    
    Args:
        text_chunk (str): 文本块
    
    Returns:
        bool: 是否使用LLM
    """
    assessment = assess_content_complexity(text_chunk)
    return assessment['is_complex']
```

### 判断标准详解

| 判断维度 | 简单内容 | 复杂内容 | 权重 |
|----------|----------|----------|------|
| **医学术语密度** | <30% | ≥30% | 30分 |
| **表格结构** | 无表格 | 包含表格 | 25分 |
| **数值密度** | ≤5个数值 | >5个数值 | 20分 |
| **句子长度** | <50字/句 | ≥50字/句 | 15分 |
| **边界模糊性** | ≤2个转折词 | >2个转折词 | 15分 |
| **特殊格式** | 无特殊符号 | 包含特殊符号 | 10分 |

**总分阈值**：≥50分触发LLM处理

### 使用场景对比

| 场景 | 规则分割 | LLM辅助 | 推荐策略 |
|------|----------|---------|----------|
| 简单文档 | ✅ 快速高效 | ❌ 成本高 | 仅规则 |
| 医药说明书 | ⚠️ 可能不准确 | ✅ 语义准确 | **LLM辅助** |
| 表格内容 | ❌ 容易破坏 | ✅ 智能处理 | **LLM辅助** |
| 大批量处理 | ✅ 成本低 | ❌ 成本高 | 混合策略 |
| 实时处理 | ✅ 响应快 | ⚠️ 延迟高 | 仅规则 |

### 最佳实践

1. **默认策略**：启用规则分割 + 智能LLM触发
2. **成本控制**：设置token限制和每日配额
3. **质量保证**：LLM失败时自动回退到规则分割
4. **性能优化**：缓存LLM结果，避免重复调用

## 应用场景

- **知识库构建**：为RAG系统准备高质量的文档chunk
- **向量检索**：提高检索准确性和相关性
- **问答系统**：优化上下文理解和答案生成
- **文档分析**：支持大规模文档的智能分析
- **LLM辅助处理**：结合本地或云端LLM提升处理质量

---

*本文档说明了项目中chunk处理的核心逻辑和实现方式，为开发者提供了完整的技术参考。*