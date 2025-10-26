# 部署指南 - 将应用部署到云端

本指南将帮助您将 A股指数分析系统部署到云端，使其可以在线访问。

## 方案选择

我们推荐使用 **Render.com** 免费部署方案：
- ✅ 免费托管 Python Web 应用
- ✅ 自动从 GitHub 部署
- ✅ 提供 HTTPS 域名
- ✅ 自动重启和健康检查
- ✅ 支持环境变量配置

## 部署步骤

### 第一步：准备 GitHub 仓库

1. **创建 GitHub 仓库**（如果还没有）
   ```bash
   # 在 GitHub 上创建新仓库，例如：stock-index-analysis
   ```

2. **推送代码到 GitHub**
   ```bash
   # 初始化 git（如果还没有）
   git init

   # 添加所有文件
   git add .

   # 创建提交
   git commit -m "Initial commit: A股指数分析系统"

   # 添加远程仓库（替换为你的 GitHub 用户名和仓库名）
   git remote add origin https://github.com/YOUR_USERNAME/stock-index-analysis.git

   # 推送到 GitHub
   git branch -M main
   git push -u origin main
   ```

### 第二步：在 Render 上部署

1. **注册 Render 账号**
   - 访问 https://render.com
   - 使用 GitHub 账号登录（推荐）

2. **创建新的 Web Service**
   - 点击 "New +" 按钮
   - 选择 "Web Service"
   - 连接你的 GitHub 仓库
   - 选择 `stock-index-analysis` 仓库

3. **配置部署设置**

   **基本设置：**
   - Name: `stock-index-api`（或你喜欢的名字）
   - Region: `Singapore`（选择离你最近的区域）
   - Branch: `main`
   - Runtime: `Python 3`

   **构建设置：**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`

   **计划：**
   - 选择 `Free` 计划

4. **配置环境变量**

   在 "Environment Variables" 部分添加以下变量：

   ```
   APP_NAME=A股指数分析系统
   APP_VERSION=1.0.0
   DEBUG=False
   HOST=0.0.0.0
   DATABASE_URL=sqlite:///./data/stock_index.db
   DATA_SOURCE=akshare
   DATA_UPDATE_INTERVAL=5
   LOG_LEVEL=INFO
   LOG_FILE=./logs/app.log
   ```

5. **点击 "Create Web Service"**

   Render 将自动：
   - 克隆你的代码
   - 安装依赖
   - 启动应用
   - 提供一个公开的 URL

### 第三步：访问你的应用

部署完成后，你会得到一个类似这样的 URL：
```
https://stock-index-api.onrender.com
```

你可以访问：
- **API 文档**: https://stock-index-api.onrender.com/docs
- **Web 界面**: https://stock-index-api.onrender.com
- **实时行情**: https://stock-index-api.onrender.com/api/realtime/sh000001

## 重要提示

### 免费计划限制

Render 免费计划有以下限制：
- ⚠️ 15分钟无活动后会自动休眠
- ⚠️ 首次访问需要等待 30-60 秒唤醒
- ⚠️ 每月 750 小时免费运行时间
- ⚠️ 共享 CPU 和内存资源

### 数据持久化问题

⚠️ **重要**: Render 免费计划的文件系统是临时的，重启后数据会丢失。

**解决方案：**

1. **使用外部数据库**（推荐）
   - 使用 Render 的 PostgreSQL 数据库（免费）
   - 或使用 MongoDB Atlas（免费）

2. **使用云存储**
   - 将数据存储到 AWS S3 或阿里云 OSS

3. **接受数据丢失**
   - 如果只是演示用途，可以接受每次重启后重新获取数据

### Redis 缓存

免费计划不包含 Redis，但应用会自动禁用缓存功能，不影响核心功能。

## 自动部署

配置完成后，每次推送代码到 GitHub 的 `main` 分支，Render 会自动重新部署：

```bash
git add .
git commit -m "更新功能"
git push origin main
```

## 监控和日志

在 Render 控制台可以：
- 查看实时日志
- 监控 CPU 和内存使用
- 查看部署历史
- 手动重启服务

## 自定义域名（可选）

如果你有自己的域名，可以在 Render 设置中添加：
1. 进入 Service 设置
2. 点击 "Custom Domain"
3. 添加你的域名
4. 按照提示配置 DNS

## 升级到付费计划

如果需要更好的性能和稳定性，可以升级到付费计划：
- **Starter**: $7/月 - 不会休眠，更多资源
- **Standard**: $25/月 - 更高性能，自动扩展

## 其他部署选项

### 1. Heroku
- 类似 Render，但免费计划已取消
- 需要付费 $5/月起

### 2. Railway
- 提供 $5 免费额度
- 超出后按使用量付费

### 3. Vercel + Serverless
- 适合前端 + API
- 需要改造为 Serverless 架构

### 4. 自己的服务器
- 阿里云、腾讯云等
- 需要自己配置和维护

## 故障排查

### 部署失败

1. **检查日志**
   - 在 Render 控制台查看构建日志
   - 查找错误信息

2. **常见问题**
   - 依赖安装失败：检查 `requirements.txt`
   - 启动命令错误：检查 `Start Command`
   - 端口配置错误：确保使用 `$PORT` 环境变量

### 应用无法访问

1. **检查服务状态**
   - 确认服务正在运行
   - 查看是否有错误日志

2. **检查环境变量**
   - 确认所有必需的环境变量已设置

3. **检查数据源**
   - AkShare 可能需要网络访问
   - 某些数据源可能被限制

## 性能优化建议

1. **使用 CDN**
   - 静态文件使用 CDN 加速

2. **启用缓存**
   - 使用 Redis 云服务（如 Redis Labs）

3. **数据库优化**
   - 使用 PostgreSQL 替代 SQLite
   - 添加适当的索引

4. **异步处理**
   - 数据获取使用后台任务
   - 避免阻塞主线程

## 安全建议

1. **环境变量**
   - 不要在代码中硬编码敏感信息
   - 使用 Render 的环境变量功能

2. **API 限流**
   - 添加请求频率限制
   - 防止滥用

3. **HTTPS**
   - Render 自动提供 HTTPS
   - 确保所有请求使用 HTTPS

## 成本估算

**免费方案：**
- Render Web Service: $0
- 总计: $0/月

**推荐付费方案：**
- Render Starter: $7/月
- PostgreSQL: $7/月（可选）
- Redis: $5/月（可选）
- 总计: $7-19/月

## 获取帮助

- Render 文档: https://render.com/docs
- Render 社区: https://community.render.com
- 项目 Issues: 在 GitHub 仓库提交问题

## 下一步

部署成功后，你可以：
1. 分享你的应用 URL 给其他人
2. 在 README 中添加在线演示链接
3. 监控应用性能和使用情况
4. 根据需要优化和扩展功能

祝部署顺利！🚀
