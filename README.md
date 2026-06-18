🧑‍💻 客户部署指南（完整版）
客户有 两种部署方式，根据需求选择：

方式一：生产部署（推荐）	方式二：开发/本地构建部署
配置文件	docker-compose.deploy.yml	docker-compose.yml
镜像来源	从 GHCR 拉取预构建镜像	本地从源码构建镜像
需要源码	❌ 不需要	✅ 需要完整仓库
构建时间	无（直接拉取）	约 5-10 分钟
适用场景	正式部署、客户使用	二次开发、调试
安全性	高（无源码暴露）	低（源码可见）
前提条件（两种方式通用）
Linux（Ubuntu/Debian）：


bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# 退出终端重新登录
docker --version
docker compose version
Windows：

下载安装 Docker Desktop
安装后重启电脑
打开 PowerShell 验证：docker --version
方式一：生产部署（拉取预构建镜像）
步骤 1：创建部署目录并下载文件

bash
mkdir coursemanage && cd coursemanage
下载 2 个文件：


bash
# Linux
curl -O https://raw.githubusercontent.com/daiyu116/courseManage/main/docker-compose.deploy.yml
curl -O https://raw.githubusercontent.com/daiyu116/courseManage/main/.env.example

powershell
# Windows PowerShell
Invoke-WebRequest -Uri https://raw.githubusercontent.com/daiyu116/courseManage/main/docker-compose.deploy.yml -OutFile docker-compose.deploy.yml
Invoke-WebRequest -Uri https://raw.githubusercontent.com/daiyu116/courseManage/main/.env.example -OutFile .env.example
步骤 2：配置环境变量

bash
# 复制模板
cp .env.example .env

# 编辑配置
nano .env    # Linux
notepad .env # Windows
必须修改（★）的项：

参数	说明	怎么改
★ POSTGRES_PASSWORD	数据库密码	改成强密码。Linux 执行 tr -dc A-Za-z0-9 </dev/urandom | head -c 24 生成
★ SECRET_KEY	应用密钥	执行 openssl rand -hex 32 生成，粘贴进去
可选修改的项：

参数	默认值	何时需要改
FRONTEND_PORT	18080	想换前端访问端口时
BACKEND_PORT	35000	想换后端 API 端口时
DOCKER_SUBNET	172.18.16.0/24	与宿主机网络冲突时
POSTGRES_USER	cadbuser	想换数据库用户名时
POSTGRES_DB	cadb	想换数据库名时
UVICORN_WORKERS	4	建议设为 CPU 核心数
ALLOWED_ORIGINS	localhost:18080	服务器有域名时改为 https://yourdomain.com
步骤 3：启动服务

bash
docker compose -f docker-compose.deploy.yml up -d
首次启动会自动拉取镜像（约 2-5 分钟），成功输出：


plainText
✔ Network coursemanage_default   Created
✔ Container coursemanage-db      Started
✔ Container coursemanage-backend Started
✔ Container coursemanage-frontend Started
步骤 4：访问系统
浏览器打开 http://服务器IP:18080

步骤 5：验证

bash
# 查看容器状态（应全部 Up）
docker compose -f docker-compose.deploy.yml ps

# 查看后端日志
docker compose -f docker-compose.deploy.yml logs backend

# 查看前端日志
docker compose -f docker-compose.deploy.yml logs frontend
方式二：开发/本地构建部署
步骤 1：克隆完整仓库

bash
git clone https://github.com/daiyu116/courseManage.git
cd courseManage
步骤 2：配置环境变量

bash
cp .env.example .env
nano .env    # 修改 POSTGRES_PASSWORD 和 SECRET_KEY（同方式一）
步骤 3：构建并启动

bash
docker compose up -d --build
首次启动需要从源码构建镜像（约 5-10 分钟），成功输出：


plainText
✔ Network coursemanage_default   Created
✔ Container coursemanage-db      Started
✔ Container coursemanage-backend Started
✔ Container coursemanage-frontend Started
步骤 4：访问系统
浏览器打开 http://服务器IP:18080

步骤 5：验证

bash
docker compose ps
docker compose logs backend
docker compose logs frontend
两种方式对比

plainText
方式一（生产部署）：
  下载2个文件 → 改.env → docker compose -f docker-compose.deploy.yml up -d → 访问
  ✅ 简单快速  ✅ 无源码暴露  ✅ 适合客户

方式二（本地构建）：
  git clone → 改.env → docker compose up -d --build → 访问
  ✅ 可二次开发  ✅ 可调试  ⚠️ 源码可见
常用运维命令（两种方式通用）

bash
# ===== 停止 / 重启 =====
# 生产部署
docker compose -f docker-compose.deploy.yml down
docker compose -f docker-compose.deploy.yml restart

# 本地构建
docker compose down
docker compose restart

# ===== 更新版本 =====
# 生产部署（拉取最新镜像）
docker compose -f docker-compose.deploy.yml pull
docker compose -f docker-compose.deploy.yml up -d

# 本地构建（重新构建镜像）
docker compose up -d --build

# ===== 查看日志 =====
# 生产部署
docker compose -f docker-compose.deploy.yml logs -f backend
docker compose -f docker-compose.deploy.yml logs -f frontend

# 本地构建
docker compose logs -f backend
docker compose logs -f frontend

# ===== 数据库操作 =====
# 进入数据库
docker exec -it coursemanage-db psql -U cadbuser -d cadb

# 备份数据库
docker exec coursemanage-db pg_dump -U cadbuser cadb > backup_$(date +%Y%m%d).sql

# 恢复数据库
cat backup_20260618.sql | docker exec -i coursemanage-db psql -U cadbuser -d cadb

# ===== 清理 =====
# 停止并删除所有容器和数据卷（⚠️ 会删除数据库数据）
docker compose -f docker-compose.deploy.yml down -v
