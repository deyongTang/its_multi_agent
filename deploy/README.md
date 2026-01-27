# 知识库平台前端部署指南

> 后端已部署，仅部署前端到 Nginx

## 一键部署（2 步搞定）

### 步骤 1：本地构建前端

```bash
cd deploy
chmod +x build.sh
./build.sh
```

构建完成后会生成 `front/knowlege_platform_ui/dist/` 目录。

---

### 步骤 2：上传并配置服务器

#### 2.1 上传前端文件

```bash
# 上传构建产物到服务器
scp -r front/knowlege_platform_ui/dist/* user@server:/var/www/knowledge_platform/

# 上传 Nginx 配置文件
scp deploy/nginx.conf user@server:/tmp/
```

#### 2.2 配置 Nginx

登录服务器后执行：

```bash
# 复制配置文件
sudo mv /tmp/nginx.conf /etc/nginx/sites-available/knowledge-platform

# 启用配置
sudo ln -s /etc/nginx/sites-available/knowledge-platform /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

---

## 访问系统

打开浏览器访问: `http://服务器IP`

前端会自动通过 Nginx 代理到后端 `http://localhost:8001`

---

## 架构说明

```
用户浏览器
    ↓
Nginx (80端口) ← 前端静态文件
    ↓
/api/* 请求代理到 → 后端 (localhost:8001)
```

---

## 常用命令

```bash
# 重启 Nginx
sudo systemctl restart nginx

# 查看 Nginx 状态
sudo systemctl status nginx

# 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log

# 测试 Nginx 配置
sudo nginx -t
```

---

## 故障排查

### 前端页面无法访问

1. 检查 Nginx 是否运行
```bash
sudo systemctl status nginx
```

2. 检查文件是否上传成功
```bash
ls -la /var/www/knowledge_platform/
```

3. 查看 Nginx 错误日志
```bash
sudo tail -f /var/log/nginx/error.log
```

### API 调用失败

1. 检查后端是否运行
```bash
curl http://localhost:8001/api/health
```

2. 检查浏览器控制台网络请求
   - 打开浏览器开发者工具 (F12)
   - 查看 Network 标签页
   - 检查 API 请求是否返回 502/504 错误

3. 检查 Nginx 代理配置
```bash
sudo cat /etc/nginx/sites-available/knowledge-platform
```

### 文件上传失败

如果上传大文件失败，修改 Nginx 配置中的 `client_max_body_size`：

```nginx
location /api/ {
    client_max_body_size 200M;  # 改为更大的值
    ...
}
```

然后重启 Nginx：
```bash
sudo systemctl restart nginx
```
