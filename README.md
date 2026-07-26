# DriveGuard Lab

DriveGuard Lab 是一个面向智能驾驶危险场景的可重复仿真与碰撞风险研究平台。

## 当前开发状态

阶段 1 至阶段 15 已完成工程基线、领域数据契约、基础运动与风险计算，No Assist、
Warning Only 和基线 AEB 的确定性运行，以及三策略评估和六个标准回归场景。评估结果
包含碰撞、间距、触发和干预指标，但不生成主观策略排名。上述能力现已通过版本化
FastAPI 端点提供；中文 Dashboard 已支持配置并运行单策略仿真或三策略评估、查看
紧凑摘要，并对完整结果进行逐帧播放、事件跳转和联动 SVG 曲线检查。阶段 14 还提供
隔离、可选的 SUMO 回放与原生探针实验适配器；它不改变 API、Dashboard 或内部仿真器。
阶段 15 增加成功响应运行时校验、共享 API 契约样本、完整回归不变量和明确分离的基础/
SUMO 验证门禁，但不改变 API 或领域 schema `1.0`。

## v1.0 目标范围

v1.0 计划通过项目内部的一维确定性纵向仿真引擎，研究前车急刹场景中的 TTC、
THW、制动距离、碰撞风险和 AEB 控制策略。当前已完成核心领域功能、标准策略评估、
仿真 API、网页配置工作流、离散逐帧播放和结果可视化。

## 技术栈

- 后端：Python 3.11+、FastAPI、Uvicorn、pytest、Ruff、mypy（可选 Eclipse SUMO）
- 前端：React、TypeScript、Vite、npm、Vitest、React Testing Library、ESLint

## 目录结构

```text
driveguard-lab/
├── backend/       # FastAPI 应用、后端测试和 Python 工具配置
├── contracts/     # 后端生成且由前后端共同验证的 API v1 样本
├── frontend/      # React/Vite 应用和前端测试
├── docs/          # 架构边界与开发路线图
├── scripts/       # 本地验证脚本
├── .editorconfig
├── .gitignore
├── AGENTS.md
└── README.md
```

## 后端安装与运行

需要 Python 3.11 或更高版本。在仓库根目录使用 PowerShell：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

如需执行阶段 14 的 headless SUMO 实验，再安装可选依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,sumo]"
.\.venv\Scripts\python.exe -m app.adapters.sumo doctor
```

详细安装、CLI 和建模边界见 [`docs/sumo-adapter-exploration.md`](docs/sumo-adapter-exploration.md)。

健康检查地址为 `http://127.0.0.1:8000/health`，交互式 API 文档地址为
`http://127.0.0.1:8000/docs`。阶段 11 API 的请求、响应和限制见
[`docs/simulation-api.md`](docs/simulation-api.md)。

## 前端安装与运行

需要 Node.js 和 npm，并先按上一节启动后端：

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Dashboard 默认请求 `http://127.0.0.1:8000`。如需使用其他后端地址，可在
`frontend/.env.local` 中设置 `VITE_API_BASE_URL`。标准回归场景在本阶段只作为配置
预设，不会从页面运行完整回归套件。详细工作流见
[`docs/dashboard-workflow.md`](docs/dashboard-workflow.md)，播放语义见
[`docs/simulation-playback.md`](docs/simulation-playback.md)。

如果系统允许执行 `npm.ps1`，也可以使用 `npm` 替代 `npm.cmd`。项目不会要求修改
PowerShell 的全局执行策略。

## 测试与验证

准备好 `backend/.venv` 和 `frontend/node_modules` 后，在仓库根目录执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

该命令执行可重复的基础门禁并明确排除可选 SUMO。安装受支持的 headless SUMO 1.27.1
后，再执行严格 SUMO 验证；运行时缺失会直接失败而不是跳过：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-sumo.ps1
```

也可以分别执行：

```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy app tests
.\.venv\Scripts\python.exe -m pytest -m "not sumo"

cd ..\frontend
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test
npm.cmd run build
```

## 安全声明

本项目仅用于软件学习与仿真实验，不得用于控制真实车辆。项目未经过功能安全认证，
也不构成自动驾驶或真实车辆控制产品。

## 尚未实现

当前已有简化的运动推进、风险指标和分类、点车辆碰撞状态，三种策略完整运行器，以及
可序列化的跨策略评估和标准回归套件。碰撞、首次 Warning 和首次 AEB 时间均为离散
帧时刻。现有 API 可运行单策略仿真、三策略评估和标准回归套件；Dashboard 可配置
和运行前两类操作，并展示摘要、离散帧播放、当前策略事件以及联动 SVG 图表。尚无
ACC 控制、结果持久化或导出、实时流式仿真、数据库、WebSocket、CARLA 或
OpenSCENARIO 集成。TraCI 仅存在于隔离的可选 SUMO 实验适配器中。

## 许可证

开源许可证尚未确定，本阶段不自动添加许可证文件。
