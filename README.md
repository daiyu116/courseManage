**项目功能介绍**
    
    本系统是一套面向教育培训机构的综合管理平台，涵盖从排课调度、学员管理到费用统计的全流程业务。功能模块按授权方式分为两类： 默认授权即开即用， 高级授权需在"系统授权管理"中激活后方可使用。

**默认授权 基础功能**
        📚 科目与排课
            科目管理：科目代码/名称维护、批量导入
            手动排课：按导师/班级/教室/科目灵活排课，冲突自动检测
            排课状态跟踪：待上课、已完训、延期、取消
            学员考勤：出席/请假/缺席签到，缺席自动标记待补课
            日历视图与表格视图双模式展示课程安排
            约束条件管理：硬性约束（导师/学员/班级/教室时间约束）与软性约束
            节假日管理：假期维护与批量导入，排课自动避开节假日
        👨‍🏫 导师与学员
            导师管理：信息维护、科目关联、在职/离职状态
            学员管理：档案维护、班级归属、多维度筛选与搜索
            班级管理：班级信息、学员分配、试听/正式课标记
            教室管理：教室代码/名称/位置/容量维护
            请假管理：导师/学员请假记录、请假后排课自动规避
            导师可见性控制：开启后导师仅可见自己相关的科目、班级与排课
        ⚙️ 系统管理
            用户管理：多角色权限（超级管理员/系统管理员/课程管理员/系统审计员）
            导师角色授权：费用管理导师、成绩管理导师、评价管理导师、运营管理导师
            LDAP统一认证：支持LDAP/AD域账号登录，角色自动映射
            开放注册：限时开放用户自助注册（3天自动关闭）
            登录超时配置：自定义Token过期时间（5分钟~30天）
            密码重置：用户自助申请、管理员审核重置
            邮箱通知：SMTP邮件向课程安排关联的导师/学员发送课程安排提醒和课程变更提醒
            系统日志：操作日志记录、日志归档备份与清除
            站点信息：机构名称/LOGO/官网/二维码等全局参数配置
        📋 排课管理
            手动排课：灵活创建课程安排
            排课查询：按条件筛选查看排课记录
            请假/调课：便捷处理临时变动
**高级授权 增强功能**
        🧠 智能算法排课
            遗传算法：适合大规模排课场景，全局搜索较优解
            回溯算法：精确搜索最优解，适合中小规模
            混合算法：结合两者优点，推荐使用
            排课预览：生成结果可逐条选择、编辑后再保存
        💰 费用管理
            学员课费项管理：新增/编辑课费项，关联科目与班级
            缴费记录：支持多种缴费途径，优惠金额管理
            退费管理：退费流程、退费途径与退费说明
            收费提醒：自动提醒待缴费项
            课费报表导出
        📈 学员成绩管理
            成绩录入：单条/批量添加学员成绩
            成绩变化追踪：对比历次成绩变化趋势
            成绩比例趋势图：ECharts可视化展示历次成绩变化
            多维度对比：按科目、班级、学员筛选分析
        📊 学员评价管理
            评价模板管理：按科目类型自定义评价维度与权重
            综合能力画像：支持"学习态度/知识掌握/实践能力/创新思维/协作素养"五维或"德智体美劳"五维模型
            单科能力画像：学科专属评价维度（如语言类听说读写、数学类逻辑推理等）
            评价周期管理：按学期（上学期秋季/下学期春季）灵活记录
            雷达图可视化：ECharts五维/多维雷达图直观展示学员能力结构
            评价管理导师：独立授权评价管理权限，精细控制访问范围
        💬 微信通知管理
            企业微信群机器人Webhook通知
            课程安排提醒：新建、更新、完训、延期、取消等信息向导师信息群/班级信息群分别推送
            综合管理通知：费用管理等信息推送
        🤖 智能指令管理
            自然语言指令解析：一句话完成添加科目/导师/学员/排课/请假等操作
            双模式解析：规则解析（内置）与AI大模型解析（须配置大模型API KEY）（Deepseek/千问/OpenAI/自定义）
            指令示例管理：自定义智能指令，同时内置示例库，支持批量AI/正则对比测试
        📺 运营大屏
            KPI看板：收入/转化率/学员数/导师数/课次/出勤率等核心指标
            可视化图表：科目分布、导师工作量、收入相关图表分析（可一键隐藏）、月度趋势等
            试听转化漏斗、导师效能排行
            全屏模式展示，支持导出图片
        🔮 全站快捷按钮
            桌面端悬浮快捷入口，一键直达智能指令、排课、新建等常用功能
            可拖拽定位，自动吸附边缘
        🗄️ 数据库管理
            手动备份：一键导出SQL备份文件
            自动备份：定时备份（每小时/每天/每周），自动清理旧备份
            数据库恢复：从备份文件还原
            备份文件管理：列表查看、下载、删除

**🧑‍💻 客户部署指南（完整版 无docker环境）**

**一  前提条件（两种方式通用）**

    Linux（Ubuntu/Debian）：
        **bash**
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

**二  客户有 两种部署方式，根据需求选择：**

              部署方式一：生产部署（推荐） |    部署方式二：开发/本地构建部署
    配置文件| docker-compose.deploy.yml   |    docker-compose.yml
    镜像来源| 从 GHCR 拉取预构建镜像       |	  本地从源码构建镜像
    需要源码| ❌ 不需要                   |    ✅ 需要完整仓库
    构建时间| 无（直接拉取）	              |    约 5-10 分钟
    适用场景| 正式部署、客户使用           |	   二次开发、调试
    安全性  | 高（无源码暴露）             |    低（源码可见）
 
**部署方式一：生产部署（拉取预构建镜像）**

    步骤 1：创建部署目录并下载文件
        **bash**
          mkdir coursemanage && cd coursemanage
        下载 2 个文件：
        # Linux 下载
        **bash**
          curl -O https://raw.githubusercontent.com/daiyu116/courseManage/main/docker-compose.deploy.yml
          curl -O https://raw.githubusercontent.com/daiyu116/courseManage/main/.env.example
        
        # Windows 下载
        **powershell**
          Invoke-WebRequest -Uri https://raw.githubusercontent.com/daiyu116/courseManage/main/docker-compose.deploy.yml -OutFile docker-compose.deploy.yml
          Invoke-WebRequest -Uri https://raw.githubusercontent.com/daiyu116/courseManage/main/.env.example -OutFile .env.example

    步骤 2：配置环境变量
        **bash**
        # 复制模板
        cp .env.example .env
        # 编辑配置
        nano .env    # Linux
        notepad .env # Windows
        
        **必须修改（★）的项：**
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
          **bash**
          docker compose -f docker-compose.deploy.yml up -d
          首次启动会自动拉取镜像（约 2-5 分钟），成功输出：
              ✔ Network coursemanage_default   Created
              ✔ Container coursemanage-db      Started
              ✔ Container coursemanage-backend Started
              ✔ Container coursemanage-frontend Started
      
      步骤 4：访问系统
          浏览器打开 http://服务器IP:18080 **端口修改为您自定义端口**

      步骤 5：验证
          **bash**
          # 查看容器状态（应全部 Up）
          docker compose -f docker-compose.deploy.yml ps
          
          # 查看后端日志
          docker compose -f docker-compose.deploy.yml logs backend
          
          # 查看前端日志
          docker compose -f docker-compose.deploy.yml logs frontend

**部署方式二：开发/本地构建部署**

      步骤 1：克隆完整仓库
          **bash**
          git clone https://github.com/daiyu116/courseManage.git
          cd courseManage
      
      步骤 2：配置环境变量
          **bash**
          cp .env.example .env
          nano .env    # 修改 POSTGRES_PASSWORD 和 SECRET_KEY（同方式一）
          
      步骤 3：构建并启动
          **bash**
          docker compose up -d --build
          首次启动需要从源码构建镜像（约 5-10 分钟），成功输出：
              ✔ Network coursemanage_default   Created
              ✔ Container coursemanage-db      Started
              ✔ Container coursemanage-backend Started
              ✔ Container coursemanage-frontend Started
      步骤 4：访问系统
          浏览器打开 http://服务器IP:18080 **端口修改为您自定义端口**
      
      步骤 5：验证
          **bash**
          docker compose ps
          docker compose logs backend
          docker compose logs frontend

**两种方式对比：**

      方式一（生产部署）：
          下载2个文件 → 改.env → docker compose -f docker-compose.deploy.yml up -d → 访问
          ✅ 简单快速  ✅ 无源码暴露  ✅ 适合客户
      
      方式二（本地构建）：
          git clone → 改.env → docker compose up -d --build → 访问
          ✅ 可二次开发  ✅ 可调试  ⚠️ 源码可见

**🖥️ 在已经具备docker的NAS设备上面如何部署**

    **方式一：SSH 命令行部署（推荐）**
          步骤 1：开启 SSH
              a.浏览器打开 NAS 管理页面（如 http://192.168.1.100)
              b.进入 设置 → 终端与SNMP → 开启 SSH
              c.记下 SSH 端口（默认 22）
          步骤 2：SSH 登录 NAS
              **bash**
              # 从电脑终端登录（用户名和密码是 NAS 的管理员账号）
              ssh 你的NAS用户名@NAS的IP地址:SSH端口
              # 例如：
              ssh admin@192.168.1.100:2222
          步骤 3：确认 Docker 可用
              **bash**
              docker --version
              docker compose version
              应输出类似：
              Docker version 27.x.x
              Docker Compose version v2.x.x
          步骤 4：创建部署目录
              **bash**
              # 在 NAS 的共享存储路径下创建（绿联默认共享路径为 /volume1）
              sudo mkdir -p /volume1/docker/coursemanage
              cd /volume1/docker/coursemanage
              ⚠️ 如果 /volume1 不存在，执行 ls /volume* 查看实际路径，可能是 /volume2 或其他。
          步骤 5：下载部署文件
              **bash**
              # 下载 docker-compose 配置
              curl -O https://raw.githubusercontent.com/daiyu116/courseManage/main/docker-compose.deploy.yml
              # 下载环境变量模板
              curl -O https://raw.githubusercontent.com/daiyu116/courseManage/main/.env.example
              如果 NAS 无法访问 GitHub（国内网络问题），可以用 Gitee 镜像：
              **bash**
              curl -O https://gitee.com/daiyu116/courseManage/raw/main/docker-compose.deploy.yml
              curl -O https://gitee.com/daiyu116/courseManage/raw/main/.env.example
          步骤 6：配置环境变量
              **bash**
              # 复制模板
              cp .env.example .env
              # 编辑配置
              vi .env
              **必须修改的项：**
                  # ★ 改成强密码（不要用默认值！）
                  POSTGRES_PASSWORD=aB3dE7fG9hJ2kL5mN8pQ1rS （不要使用@等连接符号）
                  
                  # ★ 改成随机密钥（在 NAS 上执行 openssl rand -hex 32 生成）
                  SECRET_KEY=**把生成的密钥粘贴到这里**
                  
                  # ★ 改成 NAS 的实际 IP 或域名 +本项目端口
                  ALLOWED_ORIGINS=http://192.168.1.100:18080
                  
                  # NAS 一般 4 核 CPU，设为 2-4
                  UVICORN_WORKERS=2
                  
                  # 如果 18080 端口被 NAS 其他服务占用，改为其他端口
                  FRONTEND_PORT=18080
                  
                  # 如果 35000 端口被占用
                  BACKEND_PORT=35000
          步骤 7：启动服务
              **bash**
              docker compose -f docker-compose.deploy.yml up -d
              首次启动拉取镜像约 3-5 分钟，成功输出：
                  ✔ Network coursemanage_default   Created
                  ✔ Container coursemanage-db      Started
                  ✔ Container coursemanage-backend Started
                  ✔ Container coursemanage-frontend Started
          步骤 8：访问系统
              浏览器打开：
              http://NAS的IP:18080 **端口修改为您自定义端口**
              例如：http://192.168.1.100:18080
          
          步骤 9：验证
              **bash**
              # 查看容器状态
              docker compose -f docker-compose.deploy.yml ps
              
              # 查看后端日志
              docker compose -f docker-compose.deploy.yml logs backend
    
    **方式二：NAS Docker图形界面部署**
          
          步骤 1：下载部署文件
              在电脑上下载这两个文件：
              
              https://raw.githubusercontent.com/daiyu116/courseManage/main/docker-compose.deploy.yml
              https://raw.githubusercontent.com/daiyu116/courseManage/main/.env.example
          步骤 2：编辑 .env 文件
              在电脑上用记事本打开 .env.example，按照方式一步骤6 修改配置环境变量参数, 修改后另存为 .env：
          步骤 3：上传文件到 NAS
              a.打开 NAS 文件管理器
              b.进入共享文件夹（如 Docker 或 docker）
              c.创建 coursemanage 文件夹
              d.将 docker-compose.deploy.yml 和 .env 上传到该文件夹
          步骤 4：在 Docker 管理器中部署
              a.打开 NAS 管理页面 → Docker 管理器
              b.找到 "项目" 或 "Compose" 功能
              c.点击 "创建"：
                项目名称：coursemanage
                路径：选择刚才上传文件的 coursemanage 文件夹
                compose 文件：会自动识别 docker-compose.deploy.yml
              d.点击 "启动" 或 "部署"
          步骤 5：访问系统
              浏览器打开 http://NAS的IP:18080 **端口修改为您自定义端口**

**常用运维命令（几种方式通用）**

      **bash**
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
      
**NAS 常见问题排查**

    问题                |   原因	                                     |   解决方法
    无法拉取镜像        |   国内网络无法访问 GHCR                      |   配置 Docker 镜像加速器，或用 Gitee 镜像源
    端口被占用	NAS       |  其他服务占用了 18080 或 35000	修改         |   .env 中的 FRONTEND_PORT 和 BACKEND_PORT
    子网冲突            | 	  NAS 已有 Docker 网络使用 172.18.16.0/24   |	 修改 .env 中的 DOCKER_SUBNET，如改为 172.28.16.0/24
    容器启动后立即退出   | 	.env 中密码/密钥未修改                    |	 检查 POSTGRES_PASSWORD 和 SECRET_KEY 是否已改
    页面打不开          | 	  防火墙阻止了端口                          |	 NAS 设置中开放 18080 端口
    
**配置 Docker 镜像加速器（如果拉取 GHCR 镜像超时）：**

    **bash**
    # 编辑 Docker 配置
        sudo mkdir -p /etc/docker
        sudo tee /etc/docker/daemon.json <<'EOF'
        {
          "registry-mirrors": [
            "https://docker.1ms.run",
            "https://docker.xuanyuan.me"
          ]
        }
        EOF
    # 重启 Docker
        sudo systemctl restart docker
    注意：加速器主要加速 Docker Hub，GHCR 可能仍需科学上网。如果实在无法拉取，可以联系供应商提供离线镜像包。
