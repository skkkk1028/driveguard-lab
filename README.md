# DriveGuard Lab

DriveGuard Lab 是一个面向智能驾驶危险场景的可重复仿真与碰撞风险研究平台。

## 当前开发状态

阶段 1 的工程基线、阶段 2 的领域数据契约和阶段 3 的确定性单车一维运动推进已经完成。
当前包含最小 FastAPI 健康接口、React 占位页面、纯 Python 领域契约，以及单车单时间步
的恒加速度状态推进。完整驾驶场景仍不能运行，风险指标、碰撞判断和 AEB 尚未实现。

## v1.0 目标范围

v1.0 计划通过项目内部的一维确定性纵向仿真引擎，研究前车急刹场景中的 TTC、
THW、制动距离、碰撞风险和 AEB 控制策略。上述领域功能将在后续阶段逐步设计和实现。

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

健康检查地址为 `http://127.0.0.1:8000/health`。

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

当前只有简化的单车单时间步运动推进，没有双车场景、仿真循环、TTC/THW 或制动距离
计算、碰撞风险判断、AEB/ACC 控制、场景运行接口、图表、数据库、WebSocket、SUMO、
CARLA、TraCI 或 OpenSCENARIO 集成。风险和控制字段仍只是未来结果的数据容器。

## 许可证

开源许可证尚未确定，本阶段不自动添加许可证文件。
