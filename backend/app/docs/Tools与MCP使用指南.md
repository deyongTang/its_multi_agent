# Tools 与 MCP 使用指南

> 深入理解 OpenAI Agents SDK 中的两种工具集成方式

## 目录

- [1. 核心概念](#1-核心概念)
- [2. Tools（本地工具）详解](#2-tools本地工具详解)
- [3. MCP Servers（远程服务）详解](#3-mcp-servers远程服务详解)
- [4. 对比分析](#4-对比分析)
- [5. 使用场景指南](#5-使用场景指南)
- [6. 实战案例](#6-实战案例)
- [7. 最佳实践](#7-最佳实践)
- [8. 常见问题](#8-常见问题)

---

## 1. 核心概念

### 1.1 什么是 Tools？

**Tools（本地工具）** 是在你的 Python 进程中直接执行的函数，通过 `@function_tool` 装饰器注册给 Agent 使用。

```python
from agents import function_tool

@function_tool
def query_knowledge(question: str) -> str:
    """查询知识库"""
    # 这段代码在你的 Python 进程中执行
    response = requests.post(
        f"{KNOWLEDGE_BASE_URL}/query",
        json={"question": question}
    )
    return response.json()["answer"]
```

**核心特点**：
- ✅ 代码完全由你控制
- ✅ 在本地进程中执行
- ✅ 可以访问本地资源（数据库、文件系统）
- ✅ 调试方便（可以打断点）

### 1.2 什么是 MCP Servers？

**MCP Servers（Model Context Protocol Servers）** 是通过标准化协议连接的外部服务，提供远程能力。

```python
from infrastructure.tools.mcp.mcp_servers import search_mcp_client

# MCP 客户端连接到外部服务
search_mcp_client = MCPServerSse(
    name="search",
    url="https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse",
    params={"apiKey": settings.AL_BAILIAN_API_KEY}
)

# 注册到 Agent
agent = Agent(
    name="技术专家",
    mcp_servers=[search_mcp_client]
)
```

**核心特点**：
- ✅ 标准化协议（MCP）
- ✅ 在远程服务器执行
- ✅ 由第三方服务提供商维护
- ✅ 支持流式响应（SSE）

### 1.3 为什么需要两种方式？

**设计哲学**：
- **Tools** - 处理"内部逻辑"（你的业务、你的数据）
- **MCP** - 处理"外部能力"（第三方服务、实时数据）

**类比**：
- Tools 就像你的"内部员工"，完全听你指挥
- MCP 就像"外包服务"，你只需要调用接口

---

## 2. Tools（本地工具）详解

### 2.1 基本用法

**步骤 1：定义工具函数**

```python
from agents import function_tool
import requests

@function_tool
def query_knowledge(question: str) -> str:
    """
    查询私域知识库

    Args:
        question: 用户的问题

    Returns:
        知识库的回答
    """
    try:
        response = requests.post(
            f"{KNOWLEDGE_BASE_URL}/query",
            json={"question": question},
            timeout=10
        )
        return response.json()["answer"]
    except Exception as e:
        return f"知识库查询失败: {str(e)}"
```

**步骤 2：注册到 Agent**

```python
from agents import Agent

technical_agent = Agent(
    name="技术专家",
    instructions="你是一个技术维修专家...",
    tools=[query_knowledge]  # 注册工具
)
```

**步骤 3：Agent 自动调用**

```python
# Agent 会根据用户问题自动决定是否调用工具
result = await Runner.run(
    technical_agent,
    input="电脑蓝屏怎么办？"
)
# Agent 内部会调用 query_knowledge("电脑蓝屏怎么办？")
```

### 2.2 工具函数的要求

**必须满足的条件**：

1. **使用 `@function_tool` 装饰器**
2. **有清晰的 docstring**（LLM 会读取这个描述）
3. **参数类型注解**（帮助 LLM 理解参数）
4. **返回字符串**（LLM 只能理解文本）

**示例：完整的工具函数**

```python
@function_tool
def query_service_stations(
    city: str,
    keyword: str = ""
) -> str:
    """
    查询指定城市的服务站信息

    适用场景：
    - 用户询问"附近的维修点"
    - 用户询问"北京的小米之家"

    Args:
        city: 城市名称（如：北京、上海）
        keyword: 可选的关键词（如：小米之家、联想服务站）

    Returns:
        服务站列表的 JSON 字符串
    """
    # 实现逻辑...
    pass
```

### 2.3 Tools 的典型使用场景

#### 场景 1：查询本地数据库

```python
@function_tool
def query_service_stations(city: str) -> str:
    """查询指定城市的服务站"""
    from infrastructure.database import get_db_connection

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, address, phone FROM service_stations WHERE city = %s",
        (city,)
    )

    results = cursor.fetchall()
    cursor.close()

    if not results:
        return f"未找到 {city} 的服务站"

    # 格式化为 JSON 字符串
    stations = [
        {"name": r[0], "address": r[1], "phone": r[2]}
        for r in results
    ]
    return json.dumps(stations, ensure_ascii=False)
```

#### 场景 2：调用内部 API

```python
@function_tool
def query_knowledge(question: str) -> str:
    """查询私域知识库"""
    response = requests.post(
        f"{KNOWLEDGE_BASE_URL}/query",
        json={"question": question},
        headers={"Authorization": f"Bearer {API_TOKEN}"},
        timeout=10
    )

    if response.status_code == 200:
        return response.json()["answer"]
    else:
        return f"知识库查询失败: {response.status_code}"
```

#### 场景 3：文件操作

```python
@function_tool
def read_user_profile(user_id: str) -> str:
    """读取用户配置文件"""
    file_path = f"./user_profiles/{user_id}.json"

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return json.dumps(data, ensure_ascii=False)
    except FileNotFoundError:
        return f"用户 {user_id} 的配置文件不存在"
```

#### 场景 4：数据处理

```python
@function_tool
def calculate_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> str:
    """计算两个坐标点之间的距离（单位：公里）"""
    from math import radians, sin, cos, sqrt, atan2

    R = 6371  # 地球半径（公里）

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return f"{distance:.2f} 公里"
```

### 2.4 Tools 的优势

| 优势 | 说明 | 示例 |
|------|------|------|
| **完全控制** | 代码完全由你编写和维护 | 可以添加自定义日志、错误处理 |
| **无网络延迟** | 在本地进程执行 | 数据库查询通常 < 10ms |
| **易于调试** | 可以打断点、查看变量 | 使用 IDE 调试工具 |
| **访问本地资源** | 可以访问文件系统、数据库 | 读取配置文件、查询 MySQL |
| **灵活性高** | 可以实现任意复杂逻辑 | 多步骤数据处理、条件判断 |

### 2.5 Tools 的注意事项

**1. 避免长时间阻塞**

```python
# ❌ 不好的做法
@function_tool
def slow_operation(data: str) -> str:
    """耗时操作"""
    time.sleep(60)  # 阻塞 60 秒
    return "完成"

# ✅ 好的做法
@function_tool
def fast_operation(data: str) -> str:
    """快速操作"""
    # 使用异步或后台任务处理耗时操作
    task_id = submit_background_task(data)
    return f"任务已提交，ID: {task_id}"
```

**2. 统一错误处理**

```python
@function_tool
def query_database(query: str) -> str:
    """查询数据库"""
    try:
        # 数据库操作
        result = db.execute(query)
        return json.dumps(result)
    except Exception as e:
        logger.error(f"数据库查询失败: {str(e)}")
        return f"查询失败: {str(e)}"
```

**3. 返回格式化的字符串**

```python
# ❌ 不好的做法
@function_tool
def get_user_info(user_id: str) -> dict:
    """获取用户信息"""
    return {"name": "张三", "age": 30}  # 返回字典

# ✅ 好的做法
@function_tool
def get_user_info(user_id: str) -> str:
    """获取用户信息"""
    user = {"name": "张三", "age": 30}
    return json.dumps(user, ensure_ascii=False)  # 返回 JSON 字符串
```

---

## 3. MCP Servers（远程服务）详解

### 3.1 基本用法

**步骤 1：创建 MCP 客户端**

```python
from mcp import MCPServerSse
from config.settings import settings

# 创建搜索 MCP 客户端
search_mcp_client = MCPServerSse(
    name="search",
    url="https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse",
    params={
        "apiKey": settings.AL_BAILIAN_API_KEY
    }
)

# 创建百度地图 MCP 客户端
baidu_mcp_client = MCPServerSse(
    name="baidu_map",
    url="https://api.map.baidu.com/mcp/sse",
    params={
        "ak": settings.BAIDUMAP_AK
    }
)
```

**步骤 2：建立连接**

```python
# 在应用启动时建立连接
async def startup():
    await search_mcp_client.connect()
    await baidu_mcp_client.connect()
    print("MCP 连接建立完成")
```

**步骤 3：注册到 Agent**

```python
technical_agent = Agent(
    name="技术专家",
    instructions="你是一个技术专家...",
    mcp_servers=[search_mcp_client]  # 注册 MCP 服务
)
```

**步骤 4：Agent 自动调用**

```python
# Agent 会自动调用 MCP 提供的工具
result = await Runner.run(
    technical_agent,
    input="今天小米股价多少？"
)
# Agent 内部会通过 search_mcp_client 进行网络搜索
```

### 3.2 MCP 的典型使用场景

#### 场景 1：实时网络搜索

```python
# 搜索 MCP 客户端
search_mcp_client = MCPServerSse(
    name="search",
    url="https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse",
    params={"apiKey": settings.AL_BAILIAN_API_KEY}
)

# Agent 使用
technical_agent = Agent(
    name="技术专家",
    mcp_servers=[search_mcp_client]
)

# 用户问题："今天小米股价多少？"
# Agent 会自动调用 search_mcp_client 进行实时搜索
```

#### 场景 2：地图导航服务

```python
# 百度地图 MCP 客户端
baidu_mcp_client = MCPServerSse(
    name="baidu_map",
    url="https://api.map.baidu.com/mcp/sse",
    params={"ak": settings.BAIDUMAP_AK}
)

# Agent 使用
service_agent = Agent(
    name="服务站专家",
    mcp_servers=[baidu_mcp_client]
)

# 用户问题："怎么去颐和园？"
# Agent 会调用百度地图 MCP 进行路径规划
```

#### 场景 3：天气查询

```python
# 天气 MCP 客户端
weather_mcp_client = MCPServerSse(
    name="weather",
    url="https://api.weather.com/mcp/sse",
    params={"apiKey": settings.WEATHER_API_KEY}
)

# Agent 使用
assistant_agent = Agent(
    name="生活助手",
    mcp_servers=[weather_mcp_client]
)

# 用户问题："明天北京天气怎么样？"
# Agent 会调用天气 MCP 获取实时天气数据
```

### 3.3 MCP 的优势

| 优势 | 说明 | 示例 |
|------|------|------|
| **标准化协议** | 统一的接口规范 | 所有 MCP 服务都遵循相同协议 |
| **无需维护** | 服务商负责维护和更新 | API 变更不影响你的代码 |
| **实时数据** | 获取最新的外部信息 | 股价、天气、新闻 |
| **流式响应** | 支持 SSE 流式传输 | 实时返回搜索结果 |
| **易于扩展** | 添加新服务只需配置 | 无需修改核心代码 |

### 3.4 MCP 的注意事项

**1. 网络依赖**

```python
# MCP 依赖网络连接
# 需要在应用启动时建立连接
async def startup():
    try:
        await search_mcp_client.connect()
        logger.info("MCP 连接成功")
    except Exception as e:
        logger.error(f"MCP 连接失败: {str(e)}")
        # 应用可以继续运行，但 MCP 功能不可用
```

**2. API Key 管理**

```python
# 敏感信息应该从环境变量读取
search_mcp_client = MCPServerSse(
    name="search",
    url="https://api.example.com/mcp/sse",
    params={
        "apiKey": settings.API_KEY  # 从 .env 读取
    }
)
```

**3. 错误处理**

```python
# MCP 调用可能失败（网络问题、API 限流等）
# Agent 会自动处理错误，但你应该在日志中记录
try:
    await search_mcp_client.connect()
except ConnectionError as e:
    logger.error(f"MCP 连接失败: {str(e)}")
except TimeoutError as e:
    logger.error(f"MCP 连接超时: {str(e)}")
```

---

## 4. 对比分析

### 4.1 核心差异对比表

| 维度 | Tools（本地工具） | MCP Servers（远程服务） |
|------|------------------|------------------------|
| **执行位置** | 本地 Python 进程 | 远程服务器 |
| **代码控制** | 完全自主 | 依赖第三方 |
| **网络依赖** | 可选 | 必须 |
| **响应速度** | 快（< 10ms） | 慢（100-1000ms） |
| **维护成本** | 需要自己维护 | 服务商维护 |
| **调试难度** | 容易（可打断点） | 较难（只能看日志） |
| **数据来源** | 内部数据 | 外部数据 |
| **适用场景** | 业务逻辑、数据库查询 | 第三方服务、实时数据 |
| **成本** | 无额外成本 | 可能有 API 调用费用 |

### 4.2 性能对比

**Tools 性能特点**：
- ⚡ 响应时间：< 10ms（数据库查询）
- ⚡ 无网络延迟
- ⚡ 可以批量处理

**MCP 性能特点**：
- 🐌 响应时间：100-1000ms（网络延迟）
- 🐌 依赖外部服务稳定性
- 🐌 可能有 API 限流

### 4.3 成本对比

**Tools 成本**：
- ✅ 无额外费用
- ✅ 只消耗本地计算资源
- ❌ 需要开发和维护时间

**MCP 成本**：
- ❌ 可能有 API 调用费用
- ❌ 依赖外部服务可用性
- ✅ 无需开发和维护

---

## 5. 使用场景指南

### 5.1 决策树

```
用户需求
    ↓
是否需要实时外部数据？
    ├─ 是 → 使用 MCP
    │   └─ 示例：股价、天气、新闻
    │
    └─ 否 → 是否访问内部资源？
        ├─ 是 → 使用 Tools
        │   └─ 示例：数据库、文件、内部 API
        │
        └─ 否 → 是否需要复杂计算？
            ├─ 是 → 使用 Tools
            │   └─ 示例：数据处理、算法计算
            │
            └─ 否 → 直接让 LLM 回答
```

### 5.2 具体场景分类

#### 使用 Tools 的场景

| 场景类型 | 具体示例 | 原因 |
|---------|---------|------|
| **数据库查询** | 查询服务站、用户信息 | 内部数据，快速响应 |
| **文件操作** | 读取配置、日志分析 | 本地资源访问 |
| **内部 API** | 调用知识库、业务系统 | 私域服务，需要认证 |
| **数据处理** | 坐标转换、数据格式化 | 计算密集型任务 |
| **业务逻辑** | 订单处理、权限验证 | 复杂业务规则 |

#### 使用 MCP 的场景

| 场景类型 | 具体示例 | 原因 |
|---------|---------|------|
| **实时搜索** | 网络搜索、新闻查询 | 需要最新信息 |
| **地图服务** | 路径规划、位置查询 | 第三方专业服务 |
| **天气查询** | 实时天气、预报 | 实时外部数据 |
| **股价查询** | 实时股价、财经数据 | 金融数据服务 |
| **翻译服务** | 多语言翻译 | 专业 NLP 服务 |

### 5.3 混合使用策略

**最佳实践：优先本地，兜底远程**

```python
technical_agent = Agent(
    name="技术专家",
    instructions="""
    处理技术问题时：
    1. 优先查询私域知识库（query_knowledge）
    2. 如果知识库没有答案，再联网搜索（search_mcp_client）
    """,
    tools=[query_knowledge],           # 本地工具：快速
    mcp_servers=[search_mcp_client]    # 远程服务：兜底
)
```

**工作流程**：
```
用户问题："电脑蓝屏怎么办？"
    ↓
Agent 决策：先查私域知识库
    ↓
调用 query_knowledge (Tools)
    ↓
知识库返回：找到相关文档
    ↓
返回答案 ✅

---

用户问题："今天小米股价多少？"
    ↓
Agent 决策：知识库没有实时数据
    ↓
调用 search_mcp_client (MCP)
    ↓
搜索引擎返回：最新股价
    ↓
返回答案 ✅
```

---

## 6. 实战案例

### 6.1 案例 1：ITS 技术专家 Agent

**需求**：处理技术维修问题和实时资讯查询

**实现**：

```python
from agents import Agent, function_tool
from infrastructure.tools.mcp.mcp_servers import search_mcp_client

# 定义本地工具
@function_tool
def query_knowledge(question: str) -> str:
    """查询私域知识库"""
    response = requests.post(
        f"{KNOWLEDGE_BASE_URL}/query",
        json={"question": question}
    )
    return response.json()["answer"]

# 创建 Agent
technical_agent = Agent(
    name="技术专家",
    instructions="""
    你是一个技术维修专家。

    处理流程：
    1. 对于维修问题，优先查询私域知识库
    2. 对于实时资讯（股价、新闻），使用网络搜索
    """,
    tools=[query_knowledge],           # 本地工具
    mcp_servers=[search_mcp_client]    # 远程服务
)
```

**测试**：

```python
# 测试 1：维修问题（使用 Tools）
result = await Runner.run(
    technical_agent,
    input="电脑蓝屏怎么办？"
)
# Agent 调用 query_knowledge

# 测试 2：实时资讯（使用 MCP）
result = await Runner.run(
    technical_agent,
    input="今天小米股价多少？"
)
# Agent 调用 search_mcp_client
```

### 6.2 案例 2：服务站查询 Agent

**需求**：查询服务站并提供导航

**实现**：

```python
from agents import Agent, function_tool
from infrastructure.tools.mcp.mcp_servers import baidu_mcp_client

# 定义本地工具
@function_tool
def query_service_stations(city: str, keyword: str = "") -> str:
    """查询服务站数据库"""
    from infrastructure.database import get_db_connection

    conn = get_db_connection()
    cursor = conn.cursor()

    if keyword:
        sql = """
            SELECT name, address, phone, latitude, longitude
            FROM service_stations
            WHERE city = %s AND name LIKE %s
        """
        cursor.execute(sql, (city, f"%{keyword}%"))
    else:
        sql = """
            SELECT name, address, phone, latitude, longitude
            FROM service_stations
            WHERE city = %s
        """
        cursor.execute(sql, (city,))

    results = cursor.fetchall()
    cursor.close()

    stations = [
        {
            "name": r[0],
            "address": r[1],
            "phone": r[2],
            "latitude": r[3],
            "longitude": r[4]
        }
        for r in results
    ]

    return json.dumps(stations, ensure_ascii=False)

# 创建 Agent
service_agent = Agent(
    name="服务站专家",
    instructions="""
    你是一个服务站查询专家。

    处理流程：
    1. 查询服务站数据库（query_service_stations）
    2. 如果用户需要导航，使用百度地图 MCP
    """,
    tools=[query_service_stations],    # 本地工具：查数据库
    mcp_servers=[baidu_mcp_client]     # 远程服务：地图导航
)
```

**测试**：

```python
# 测试 1：查询服务站（使用 Tools）
result = await Runner.run(
    service_agent,
    input="北京有哪些小米之家？"
)
# Agent 调用 query_service_stations

# 测试 2：导航（使用 MCP）
result = await Runner.run(
    service_agent,
    input="怎么去最近的小米之家？"
)
# Agent 先调用 query_service_stations，再调用 baidu_mcp_client
```

---

## 7. 最佳实践

### 7.1 工具设计原则

**1. 单一职责原则**

```python
# ✅ 好的做法：每个工具只做一件事
@function_tool
def query_service_stations(city: str) -> str:
    """查询服务站"""
    # 只负责查询
    pass

@function_tool
def calculate_distance(lat1, lon1, lat2, lon2) -> str:
    """计算距离"""
    # 只负责计算
    pass

# ❌ 不好的做法：一个工具做太多事
@function_tool
def query_and_navigate(city: str, destination: str) -> str:
    """查询服务站并导航"""
    # 既查询又导航，职责不清晰
    pass
```

**2. 清晰的工具描述**

```python
# ✅ 好的做法：详细的 docstring
@function_tool
def query_knowledge(question: str) -> str:
    """
    查询私域知识库

    适用场景：
    - 用户询问技术维修问题
    - 用户询问产品使用方法

    Args:
        question: 用户的问题

    Returns:
        知识库的回答（JSON 格式）
    """
    pass

# ❌ 不好的做法：没有描述
@function_tool
def query(q: str) -> str:
    pass
```

**3. 统一的错误处理**

```python
@function_tool
def query_database(query: str) -> str:
    """查询数据库"""
    try:
        result = db.execute(query)
        return json.dumps(result, ensure_ascii=False)
    except DatabaseError as e:
        logger.error(f"数据库错误: {str(e)}")
        return f"查询失败: 数据库连接错误"
    except Exception as e:
        logger.error(f"未知错误: {str(e)}")
        return f"查询失败: {str(e)}"
```

### 7.2 MCP 管理最佳实践

#### 1. 连接管理

```python
# ✅ 好的做法：在应用启动时建立连接
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时建立连接
    await search_mcp_client.connect()
    await baidu_mcp_client.connect()
    logger.info("MCP 连接建立完成")

    yield  # 应用运行期间

    # 关闭时清理连接
    await search_mcp_client.cleanup()
    await baidu_mcp_client.cleanup()
    logger.info("MCP 连接清理完成")

app = FastAPI(lifespan=lifespan)
```

#### 2. 配置管理

```python
# ✅ 好的做法：从环境变量读取配置
from config.settings import settings

search_mcp_client = MCPServerSse(
    name="search",
    url=settings.DASHSCOPE_BASE_URL,
    params={"apiKey": settings.AL_BAILIAN_API_KEY}
)

# ❌ 不好的做法：硬编码 API Key
search_mcp_client = MCPServerSse(
    name="search",
    url="https://api.example.com/mcp/sse",
    params={"apiKey": "sk-hardcoded-key"}  # 不安全
)
```

#### 3. 错误处理

```python
# ✅ 好的做法：优雅处理 MCP 连接失败
async def mcp_connect():
    try:
        await search_mcp_client.connect()
        logger.info("搜索 MCP 连接成功")
    except Exception as e:
        logger.error(f"搜索 MCP 连接失败: {str(e)}")
        # 应用继续运行，但搜索功能不可用

    try:
        await baidu_mcp_client.connect()
        logger.info("地图 MCP 连接成功")
    except Exception as e:
        logger.error(f"地图 MCP 连接失败: {str(e)}")
        # 应用继续运行，但地图功能不可用
```

### 7.3 性能优化

#### 1. 工具响应时间优化

```python
# ✅ 好的做法：设置超时
@function_tool
def query_knowledge(question: str) -> str:
    """查询知识库"""
    try:
        response = requests.post(
            f"{KNOWLEDGE_BASE_URL}/query",
            json={"question": question},
            timeout=5  # 5 秒超时
        )
        return response.json()["answer"]
    except requests.Timeout:
        return "知识库查询超时，请稍后重试"
```

#### 2. 缓存策略

```python
# ✅ 好的做法：缓存频繁查询的结果
from functools import lru_cache

@lru_cache(maxsize=100)
def get_service_station_by_id(station_id: str) -> dict:
    """获取服务站信息（带缓存）"""
    # 查询数据库
    return station_info

@function_tool
def query_station_info(station_id: str) -> str:
    """查询服务站信息"""
    station = get_service_station_by_id(station_id)
    return json.dumps(station, ensure_ascii=False)
```

---

## 8. 常见问题

### 8.1 Tools 相关问题

#### Q1: 为什么工具函数必须返回字符串？

**A**: LLM 只能理解文本，所以工具函数必须返回字符串。如果需要返回结构化数据，使用 JSON 字符串。

```python
# ✅ 正确
@function_tool
def get_user(user_id: str) -> str:
    user = {"name": "张三", "age": 30}
    return json.dumps(user, ensure_ascii=False)

# ❌ 错误
@function_tool
def get_user(user_id: str) -> dict:
    return {"name": "张三", "age": 30}
```

#### Q2: 工具函数可以是异步的吗？

**A**: 可以！使用 `async def` 定义异步工具函数。

```python
@function_tool
async def query_knowledge(question: str) -> str:
    """异步查询知识库"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KNOWLEDGE_BASE_URL}/query",
            json={"question": question}
        )
        return response.json()["answer"]
```

#### Q3: 如何调试工具函数？

**A**: 可以直接调用工具函数进行测试。

```python
# 直接测试工具函数
result = query_knowledge("电脑蓝屏怎么办？")
print(result)

# 或者使用 pytest
def test_query_knowledge():
    result = query_knowledge("测试问题")
    assert "答案" in result
```

### 8.2 MCP 相关问题

#### Q1: MCP 连接失败怎么办？

**A**: 检查以下几点：

1. **网络连接**：确保可以访问 MCP 服务器
2. **API Key**：验证 API Key 是否有效
3. **URL 配置**：检查 MCP 服务器地址是否正确

```bash
# 测试网络连接
curl https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse

# 检查环境变量
echo $AL_BAILIAN_API_KEY
```

#### Q2: 如何知道 MCP 提供了哪些工具？

**A**: MCP 客户端连接后会自动发现可用工具。查看日志或使用调试模式。

```python
# 连接后查看可用工具
await search_mcp_client.connect()
tools = search_mcp_client.list_tools()
print(f"可用工具: {tools}")
```

#### Q3: MCP 调用很慢怎么办？

**A**: MCP 调用依赖网络，可能较慢。优化策略：

1. **优先使用本地工具**
2. **设置合理的超时时间**
3. **考虑缓存结果**

### 8.3 混合使用问题

#### Q1: Agent 如何决定使用 Tools 还是 MCP？

**A**: Agent 会根据工具的描述（docstring）自动决定。确保工具描述清晰。

```python
@function_tool
def query_knowledge(question: str) -> str:
    """
    查询私域知识库（适用于技术维修问题）
    """
    pass

# MCP 的描述由服务提供商定义
# Agent 会根据描述选择合适的工具
```

#### Q2: 可以同时调用多个工具吗？

**A**: 可以！Agent 会根据需要依次调用多个工具。

```python
# Agent 可能的执行流程：
# 1. 调用 query_service_stations（Tools）
# 2. 调用 baidu_mcp_client（MCP）
# 3. 综合结果返回给用户
```

---

## 9. 总结

### 9.1 核心要点

**Tools（本地工具）**：
- ✅ 用于内部逻辑和数据访问
- ✅ 响应快速，易于调试
- ✅ 完全可控，灵活性高
- ❌ 需要自己开发和维护

**MCP Servers（远程服务）**：
- ✅ 用于外部服务和实时数据
- ✅ 标准化协议，易于集成
- ✅ 无需维护，服务商负责
- ❌ 依赖网络，响应较慢

### 9.2 选择指南

| 场景 | 推荐方案 | 原因 |
|------|---------|------|
| 查询数据库 | Tools | 内部数据，快速响应 |
| 调用内部 API | Tools | 私域服务，需要认证 |
| 文件操作 | Tools | 本地资源访问 |
| 数据处理 | Tools | 计算密集型任务 |
| 实时搜索 | MCP | 需要最新信息 |
| 地图导航 | MCP | 第三方专业服务 |
| 天气查询 | MCP | 实时外部数据 |
| 股价查询 | MCP | 金融数据服务 |

### 9.3 最佳实践总结

1. **优先本地，兜底远程**：先用 Tools 查询内部数据，再用 MCP 获取外部信息
2. **清晰的工具描述**：详细的 docstring 帮助 Agent 正确选择工具
3. **统一错误处理**：所有工具都应该有完善的错误处理
4. **性能优化**：设置超时、使用缓存、避免阻塞
5. **安全配置**：API Key 从环境变量读取，不要硬编码

### 9.4 快速参考

**定义 Tools**：
```python
@function_tool
def tool_name(param: str) -> str:
    """工具描述"""
    return result
```

**创建 MCP 客户端**：
```python
mcp_client = MCPServerSse(
    name="service_name",
    url="https://api.example.com/mcp/sse",
    params={"apiKey": settings.API_KEY}
)
```

**注册到 Agent**：
```python
agent = Agent(
    name="Agent 名称",
    tools=[tool1, tool2],
    mcp_servers=[mcp_client1, mcp_client2]
)
```

---

**文档版本**：v1.0
**最后更新**：2026-01-26
**作者**：ITS 多智能体团队
