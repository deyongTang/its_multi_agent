# GitHub Actions 自动部署指南

本文档介绍如何使用 GitHub Actions 实现 ITS Knowledge 知识库平台的自动化部署。

## 目录

- [部署架构](#部署架构)
- [前置准备](#前置准备)
- [配置步骤](#配置步骤)
- [使用方法](#使用方法)
- [故障排查](#故障排查)

---

## 部署架构

### 工作流程

```
开发者推送代码到 main 分支
    ↓
GitHub Actions 自动触发
    ↓
通过 SSH 连接到远程服务器
    ↓
拉取最新代码
    ↓
构建 Docker 镜像
    ↓
重启服务
    ↓
健康检查
    ↓
部署完成
```

### 触发条件

- **自动触发**: 当 `backend/knowledge/` 目录下的文件发生变化并推送到 `main` 分支时
- **手动触发**: 在 GitHub Actions 页面手动触发工作流

---

## 前置准备

### 1. 服务器准备

在远程服务器上完成以下准备工作：

```bash
# 1. 安装 Docker 和 Docker Compose
# (参考 DEPLOYMENT.md 中的安装指南)

# 2. 创建项目目录
sudo mkdir -p /opt/its_knowledge
cd /opt/its_knowledge

# 3. 克隆项目
git clone https://github.com/deyongTang/its_multi_agent.git .

# 4. 配置环境变量
cd backend/knowledge
cp .env.example .env
vim .env  # 配置必填项

# 5. 首次手动部署
./deploy.sh
```

### 2. 生成 SSH 密钥

在本地机器生成 SSH 密钥对：

```bash
# 生成新的 SSH 密钥（如果还没有）
ssh-keygen -t rsa -b 4096 -C "github-actions" -f ~/.ssh/github_actions_key

# 查看公钥
cat ~/.ssh/github_actions_key.pub

# 查看私钥（稍后需要添加到 GitHub Secrets）
cat ~/.ssh/github_actions_key
```

### 3. 配置服务器 SSH 访问

将公钥添加到服务器：

```bash
# 在远程服务器上执行
mkdir -p ~/.ssh
echo "your-public-key-content" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

测试 SSH 连接：

```bash
# 在本地测试
ssh -i ~/.ssh/github_actions_key user@your-server-ip
```

---

## 配置步骤

### 步骤 1: 配置 GitHub Secrets

在 GitHub 仓库中配置敏感信息：

1. 打开仓库：https://github.com/deyongTang/its_multi_agent
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret** 添加以下密钥：

| Secret 名称 | 说明 | 示例值 |
|------------|------|--------|
| `SERVER_HOST` | 服务器 IP | `123.456.789.0` |
| `SERVER_USER` | SSH 用户名 | `root` |
| `SERVER_SSH_KEY` | SSH 私钥 | 完整私钥内容 |
| `SERVER_PORT` | SSH 端口 | `22` |

### 步骤 2: 推送代码触发部署

```bash
# 提交并推送代码
git add .
git commit -m "Update knowledge platform"
git push origin main
```

---

## 使用方法

### 自动部署

当你推送代码到 `main` 分支时，GitHub Actions 会自动触发部署。

### 手动部署

1. 打开 GitHub 仓库
2. 点击 **Actions** 标签
3. 选择 **Deploy Knowledge Platform** 工作流
4. 点击 **Run workflow** → **Run workflow**

### 查看部署日志

1. 进入 **Actions** 页面
2. 点击最新的工作流运行
3. 查看详细日志

---

## 故障排查

### 1. SSH 连接失败

**错误**: `Permission denied (publickey)`

**解决方案**:
- 检查 `SERVER_SSH_KEY` 是否正确
- 确认公钥已添加到服务器 `~/.ssh/authorized_keys`
- 检查服务器 SSH 配置

### 2. Docker 构建失败

**解决方案**:
```bash
# SSH 到服务器手动检查
ssh user@server-ip
cd /opt/its_knowledge/backend/knowledge
docker compose logs
```

### 3. 服务未启动

**解决方案**:
- 检查 `.env` 文件配置
- 查看容器日志：`docker compose logs -f`
- 检查端口占用：`lsof -i :8001`

---

## 最佳实践

1. **首次部署手动完成** - 确保环境配置正确
2. **定期备份数据** - 备份 `chroma_kb` 和 `.env`
3. **监控部署状态** - 关注 GitHub Actions 通知
4. **测试后再推送** - 本地测试通过后再推送到 main

---

## 相关文档

- [完整部署文档](DEPLOYMENT.md)
- [项目架构说明](../../CLAUDE.md)
- [GitHub 仓库](https://github.com/deyongTang/its_multi_agent)
