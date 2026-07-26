# DriveGuard Lab v1.0

DriveGuard Lab 是一个面向智能驾驶危险场景的可重复仿真与碰撞风险研究平台。v1.0
聚焦一维纵向前车急刹场景，通过确定性点车辆模型研究 Gap、TTC、THW、理论制动距离、
风险等级，以及 No Assist、Warning Only 和基线 AEB 三种策略。

当前仓库是 **v1.0 发布候选**。它适合教学、软件实验和可重复研究，不是功能安全认证
产品，不得用于控制真实车辆，也不应把默认阈值解释为行业标准或安全保证。

## 能做什么

- 配置并运行 No Assist、Warning Only 或基线 AEB 单策略仿真；
- 使用同一物理参数执行三策略评估，不生成主观排名或综合安全分数；
- 使用六个标准回归场景作为实验预设；
- 查看碰撞、最小 Gap/TTC、策略触发和干预时长摘要；
- 逐帧播放结果、跳转事件并检查速度、Gap、制动距离、TTC 和 THW 曲线；
- 通过同步 FastAPI 端点执行仿真与回归套件；
- 可选使用隔离的 headless SUMO 1.27.1 回放和原生探针实验。

## 环境要求

| 组件 | v1.0 支持范围 |
| --- | --- |
| Python | 3.11 或更高；发布候选验证 3.11 与 3.14 |
| Node.js | 24.x |
| npm | 11.x |
| 浏览器 | 支持现代 ES2022、SVG 和 `requestAnimationFrame` 的桌面浏览器 |
| SUMO | 可选，固定为 headless Eclipse SUMO 1.27.1 |

## 安装

在 PowerShell 中进入仓库根目录：

```powershell
cd "F:\workspace\Project8-DriveGuard Lab\driveguard-lab"

cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"

cd ..\frontend
npm.cmd ci
```

如果需要 SUMO 实验，将后端安装命令改为：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,sumo]"
```

## 启动 Dashboard

打开两个 PowerShell 窗口。

终端一：

```powershell
cd "F:\workspace\Project8-DriveGuard Lab\driveguard-lab\backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

终端二：

```powershell
cd "F:\workspace\Project8-DriveGuard Lab\driveguard-lab\frontend"
npm.cmd run dev
```

浏览器打开 `http://localhost:5173`。后端健康检查位于
`http://127.0.0.1:8000/health`，交互式 API 文档位于
`http://127.0.0.1:8000/docs`。

## 第一次实验

1. 在“标准场景预设”中选择“AEB 避免碰撞”。
2. 保持“单策略仿真”和“AEB”，点击“运行单策略仿真”。
3. 查看摘要中的碰撞结果、最小间距和 AEB 触发时间。
4. 使用播放、前后帧、事件跳转和曲线联动检查完整离散结果。
5. 切换到“三策略评估”，用完全相同的物理配置比较三种策略原始结果。

表单中的物理量均使用 SI 单位。更完整的操作和结果解释见
[`docs/user-guide.md`](docs/user-guide.md)。

## 固定公网网址

仓库提供一个生产容器：构建时生成 Dashboard，运行时由同一个 FastAPI 服务在根路径
托管静态页面和 `/api/v1`，因此公网只需要一个 HTTPS 域名。`render.yaml` 可在 Render
上创建新加坡区域的公开 Web Service，并使用 `/health` 作为健康检查。

完整的部署、平台限制、自定义域名和更新步骤见
[`docs/public-deployment.md`](docs/public-deployment.md)。创建实际公网服务仍需要一个可由
Render 读取的 Git 仓库和用户自己的 Render 账号；仓库不包含部署凭据。

## 验证

确定性基础门禁不依赖 SUMO：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

严格 SUMO 门禁会在运行时缺失时失败而不是跳过：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-sumo.ps1
```

完整发布候选检查还会验证版本、许可证、文档链接、后端 wheel/sdist 和干净安装：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\release-check.ps1
```

## 文档

从 [`docs/index.md`](docs/index.md) 开始浏览用户指南、模型语义、API、策略、播放、SUMO
和发布验证文档。v1.0 已知边界与实证环境记录在
[`docs/release-readiness.md`](docs/release-readiness.md)。

## 目录

```text
driveguard-lab/
├── backend/       # FastAPI、领域/仿真核心和后端测试
├── contracts/     # 前后端共同验证的 API v1 JSON 样本
├── docs/          # 用户、模型、接口和发布文档
├── frontend/      # React/Vite Dashboard
├── scripts/       # 基础、SUMO 和发布候选验证入口
├── Dockerfile     # Dashboard + API 单域名生产镜像
├── render.yaml    # Render 公网服务 Blueprint
├── LICENSE
├── CHANGELOG.md
└── THIRD_PARTY_NOTICES.md
```

## 明确不包含

v1.0 不包含 ACC、多车道或横向运动、传感器/感知模型、随机噪声、结果持久化与导出、
数据库、WebSocket、实时流、CARLA、OpenSCENARIO、真实车辆接口或功能安全认证。SUMO
适配器只是隔离实验工具，不替代内部仿真器，也不接入 Dashboard 或 API。

## 许可证

项目源代码采用 [Apache License 2.0](LICENSE)。第三方和可选依赖说明见
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。
