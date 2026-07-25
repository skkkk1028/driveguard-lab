# DriveGuard Lab

DriveGuard Lab 是一个面向智能驾驶危险场景的可重复仿真与碰撞风险研究平台。

## 当前开发状态

阶段 1 至阶段 11 已完成工程基线、领域数据契约、基础运动与风险计算，No Assist、
Warning Only 和基线 AEB 的确定性运行，以及三策略评估和六个标准回归场景。评估结果
包含碰撞、间距、触发和干预指标，但不生成主观策略排名。上述能力现已通过版本化
FastAPI 端点提供；前端仿真功能尚未实现。

## v1.0 目标范围

v1.0 计划通过项目内部的一维确定性纵向仿真引擎，研究前车急刹场景中的 TTC、
THW、制动距离、碰撞风险和 AEB 控制策略。当前已完成核心领域功能和标准策略评估，
后续阶段将增加网页配置、播放和可视化。

## 技术栈

- 后端：Python 3.11+、FastAPI、Uvicorn、pytest、Ruff、mypy
- 前端：React、TypeScript、Vite、npm、Vitest、React Testing Library、ESLint

## 目录结构

```text
driveguard-lab/
├── backend/       # FastAPI 应用、后端测试和 Python 工具配置
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

健康检查地址为 `http://127.0.0.1:8000/health`，交互式 API 文档地址为
`http://127.0.0.1:8000/docs`。阶段 11 API 的请求、响应和限制见
[`docs/simulation-api.md`](docs/simulation-api.md)。

## 前端安装与运行

需要 Node.js 和 npm：

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

如果系统允许执行 `npm.ps1`，也可以使用 `npm` 替代 `npm.cmd`。项目不会要求修改
PowerShell 的全局执行策略。

## 测试与验证

准备好 `backend/.venv` 和 `frontend/node_modules` 后，在仓库根目录执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

也可以分别执行：

```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy app tests
.\.venv\Scripts\python.exe -m pytest

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
帧时刻。现有 API 可运行单策略仿真、三策略评估和标准回归套件。尚无 ACC 控制、
前端仿真功能、图表、数据库、WebSocket、SUMO、
CARLA、TraCI 或 OpenSCENARIO 集成。

## 许可证

开源许可证尚未确定，本阶段不自动添加许可证文件。
