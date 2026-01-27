# JWT 认证功能使用说明

## 功能概述

为 ITS 知识库平台后端系统添加了完整的 JWT (JSON Web Token) 认证功能,实现用户注册、登录、Token 刷新和接口权限保护。

## 架构设计

### 1. 认证流程

```
用户注册 → 用户登录 → 获取 Token → 访问受保护接口 → Token 过期 → 刷新 Token
```

### 2. Token 类型

- **Access Token**: 有效期 30 分钟,用于访问受保护的 API 接口
- **Refresh Token**: 有效期 7 天,用于刷新 Access Token

### 3. 目录结构

```
backend/knowledge/
├── config/
│   └── settings.py                    # JWT 配置 (密钥、过期时间)
├── schemas/
│   └── schema.py                      # 用户认证相关数据模型
├── utils/
│   └── security.py                    # 密码加密、JWT 生成/验证
├── data_access/
│   └── user_repository.py             # 用户数据访问层
├── business_logic/
│   └── auth_service.py                # 用户认证业务逻辑
├── infrastructure/
│   └── auth_dependencies.py           # JWT 认证依赖项
├── api/
│   ├── auth_routes.py                 # 认证 API 路由
│   └── routers.py                     # 知识库 API (已添加认证保护)
└── scripts/
    ├── init_users_table.sql           # 用户表 SQL 脚本
    └── init_users_db.py               # 数据库初始化脚本
```

## 安装步骤

### 1. 安装依赖包

```bash
cd backend/knowledge
pip install -r requirements.txt
```

新增的依赖包:
- `PyJWT`: JWT Token 生成和验证
- `passlib[bcrypt]`: 密码加密 (bcrypt 算法)
- `email-validator`: 邮箱格式验证

### 2. 配置环境变量

在 `backend/knowledge/.env` 文件中添加 JWT 配置:

```env
# JWT 认证配置
JWT_SECRET_KEY=your-secret-key-change-in-production-please-use-a-strong-random-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

**重要**: 生产环境请使用强随机密钥!

### 3. 初始化数据库

运行数据库初始化脚本创建用户表:

```bash
cd backend/knowledge
python scripts/init_users_db.py
```

或者手动执行 SQL:

```bash
mysql -u root -p its_knowledge < scripts/init_users_table.sql
```

### 4. 启动服务

```bash
cd backend/knowledge
python api/main.py
```

服务运行在 `http://127.0.0.1:8001`

## API 接口说明

### 认证接口 (无需 Token)

#### 1. 用户注册

**接口**: `POST /auth/register`

**请求体**:
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123"
}
```

**响应**:
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "is_active": true,
  "created_at": "2026-01-27T10:00:00"
}
```

#### 2. 用户登录

**接口**: `POST /auth/login`

**请求体**:
```json
{
  "username": "testuser",
  "password": "password123"
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 3. 刷新 Token

**接口**: `POST /auth/refresh`

**请求体**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 受保护接口 (需要 Token)

#### 4. 获取当前用户信息

**接口**: `GET /auth/me`

**请求头**:
```
Authorization: Bearer <access_token>
```

**响应**:
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "is_active": true,
  "created_at": "2026-01-27T10:00:00"
}
```

#### 5. 上传文档到知识库

**接口**: `POST /upload`

**请求头**:
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**请求体**: 文件上传 (form-data)

#### 6. 查询知识库

**接口**: `POST /query`

**请求头**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**请求体**:
```json
{
  "question": "如何重置密码?"
}
```

## 使用示例

### Python 示例

```python
import requests

BASE_URL = "http://127.0.0.1:8001"

# 1. 注册用户
register_data = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
}
response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
print(response.json())

# 2. 登录获取 Token
login_data = {
    "username": "testuser",
    "password": "password123"
}
response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
tokens = response.json()
access_token = tokens["access_token"]

# 3. 使用 Token 访问受保护接口
headers = {
    "Authorization": f"Bearer {access_token}"
}
response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
print(response.json())

# 4. 查询知识库
query_data = {"question": "如何重置密码?"}
response = requests.post(f"{BASE_URL}/query", json=query_data, headers=headers)
print(response.text)
```

### cURL 示例

```bash
# 1. 注册用户
curl -X POST http://127.0.0.1:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}'

# 2. 登录获取 Token
curl -X POST http://127.0.0.1:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'

# 3. 使用 Token 访问受保护接口
curl -X GET http://127.0.0.1:8001/auth/me \
  -H "Authorization: Bearer <your_access_token>"

# 4. 查询知识库
curl -X POST http://127.0.0.1:8001/query \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"question":"如何重置密码?"}'
```

## 安全特性

### 1. 密码安全
- 使用 bcrypt 算法进行密码哈希
- 密码不以明文存储
- 密码验证使用常量时间比较

### 2. Token 安全
- JWT 使用 HS256 算法签名
- Token 包含过期时间 (exp)
- Access Token 短期有效 (30 分钟)
- Refresh Token 长期有效 (7 天)

### 3. 接口保护
- 所有知识库操作接口需要认证
- Token 验证失败返回 401 Unauthorized
- 用户被禁用返回 403 Forbidden

## 常见问题

### Q1: Token 过期怎么办?

使用 Refresh Token 刷新 Access Token:

```python
refresh_data = {"refresh_token": refresh_token}
response = requests.post(f"{BASE_URL}/auth/refresh", json=refresh_data)
new_tokens = response.json()
```

### Q2: 如何修改 Token 过期时间?

修改 `.env` 文件中的配置:

```env
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60  # 改为 60 分钟
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30    # 改为 30 天
```

### Q3: 忘记密码怎么办?

目前系统未实现密码重置功能。可以直接在数据库中更新用户密码:

```python
from utils.security import hash_password

new_password_hash = hash_password("new_password")
# 然后在数据库中更新 hashed_password 字段
```

### Q4: 如何禁用用户?

在数据库中将用户的 `is_active` 字段设置为 0:

```sql
UPDATE users SET is_active = 0 WHERE username = 'testuser';
```

## 测试建议

### 1. 使用 FastAPI 自动文档

访问 `http://127.0.0.1:8001/docs` 查看 Swagger UI 文档,可以直接在浏览器中测试所有接口。

### 2. 使用 Postman

1. 创建一个 Collection
2. 添加环境变量 `access_token`
3. 在登录接口的 Tests 中自动保存 Token:
   ```javascript
   pm.environment.set("access_token", pm.response.json().access_token);
   ```
4. 在其他接口的 Authorization 中使用 `{{access_token}}`

## 后续优化建议

1. **密码重置功能**: 添加邮箱验证和密码重置流程
2. **Token 黑名单**: 实现 Token 撤销机制 (使用 Redis)
3. **多因素认证**: 添加 2FA 支持
4. **OAuth 集成**: 支持第三方登录 (Google, GitHub 等)
5. **用户权限管理**: 实现基于角色的访问控制 (RBAC)
6. **登录日志**: 记录用户登录历史和异常登录检测

## 技术支持

如有问题,请查看:
- FastAPI 文档: https://fastapi.tiangolo.com/
- PyJWT 文档: https://pyjwt.readthedocs.io/
- Passlib 文档: https://passlib.readthedocs.io/
