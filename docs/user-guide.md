# DriveGuard Lab v1.0 用户指南

## 1. 使用边界

DriveGuard Lab 用确定性一维点车辆模型研究前车急刹场景。所有物理输入使用 SI 单位，
相同输入产生相同输出。平台不模拟方向盘、多车道、传感器、道路参与者行为或真实车辆
执行器，不提供安全认证结论。

默认风险阈值和基线 AEB 只是项目内启发式实验配置，不是行业标准。碰撞、Warning 和
AEB 触发时间都是保留帧上的离散观测时刻，不推断步长内部的精确发生时间。

## 2. 安装和启动

准备 Python 3.11 或 3.14、Node.js 24 和 npm 11。在仓库根目录执行：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"

cd ..\frontend
npm.cmd ci
```

分别启动后端和前端：

```powershell
# 终端一
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

# 终端二
cd frontend
npm.cmd run dev
```

打开 `http://localhost:5173`。如果页面显示 API unavailable，先访问
`http://127.0.0.1:8000/health`；正常响应为
`{"status":"ok","service":"driveguard-api"}`。

## 3. 配置场景

“标准场景预设”只复制物理配置，不会改变当前运行模式或单策略选择：

| 预设 | 主要用途 |
| --- | --- |
| 稳定跟车 | 无干预、无碰撞的稳定基线 |
| 仅谨慎风险 | 到达 Caution 但不触发 Warning/AEB |
| 告警但不改变运动 | 检查 Warning 与 No Assist 轨迹一致性 |
| AEB 避免碰撞 | No Assist 碰撞而 AEB 避免碰撞 |
| AEB 无法避免碰撞 | AEB 延迟但不能消除碰撞 |
| 初始紧急与边界步长 | 初始 Emergency、内部制动边界和缩短末步 |

主要输入包括自车/前车初速度、初始 Gap、前车制动起点与减速度、自车反应时间与最大
制动减速度、固定仿真步长和最大时长。自定义阈值启用后必须完整填写五个有限正值，且
满足 `Emergency TTC < Danger TTC < Caution TTC` 和
`Danger THW < Caution THW`。

一次策略最多 10,000 个推进区间。表单会进行前置校验，后端仍会独立执行权威校验。

## 4. 运行和解释结果

### 单策略仿真

选择 No Assist、Warning Only 或 AEB 后点击“运行单策略仿真”。

- No Assist：自车不施加辅助加速度。
- Warning Only：Danger/Emergency 帧产生 Warning，但不改变任何车辆运动。
- AEB：Danger 使用最大制动幅值的 50%，Emergency 使用 100%；当前帧动作作用于下一个
  仿真区间，没有额外执行延迟或动作锁存。

### 三策略评估

“三策略评估”使用同一组物理参数和风险阈值，固定按 No Assist、Warning Only、AEB
运行。差值均为 AEB 减 No Assist。平台只报告碰撞、Gap、触发、末速度和干预时长等
原始量，不选择“最佳策略”。

### 摘要和播放

- `Gap = lead.position_m - ego.position_m`，`Gap <= 0` 是内部点车辆碰撞状态。
- TTC 只在自车相对接近前车时适用；不适用显示为空，接触/重叠显示 `0`。
- THW 在自车静止时不适用。
- 图表坐标是展示值，文本物理量保持 API 原始数值，不进行 UI 舍入。
- 道路动画采用固定地面坐标范围，自车和前车都按 API 返回的绝对 `position_m`
  移动；单次运行使用该轨迹的范围，三策略评估使用三条轨迹的共同范围，播放和策略
  切换期间比例保持不变。
- 道路图中的圆点是点车辆参考位置，示意车身分别向接触点外侧延伸：`Gap > 0`
  时分离、`Gap = 0` 时接触、`Gap < 0` 时重叠；车身图形不代表真实车辆尺寸。
- 播放只选择后端保留帧，不插值运动，也不推断步内碰撞时间。
- 评估播放使用三策略帧时间并集；已提前结束的策略保持在末帧。

## 5. API

Swagger UI 位于 `http://127.0.0.1:8000/docs`。主要端点为：

- `POST /api/v1/simulations`
- `POST /api/v1/evaluations`
- `GET /api/v1/regression-scenarios`
- `POST /api/v1/regression-suites`

详细请求、错误信封和资源限制见 [FastAPI simulation API](simulation-api.md)。应用版本
显示为 `1.0.0`，响应中的 `schema_version` 仍为 `1.0`。

## 6. 可选 SUMO 实验

安装额外依赖并检查受支持运行时：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -e ".[dev,sumo]"
.\.venv\Scripts\python.exe -m app.adapters.sumo doctor
```

运行回放或原生探针：

```powershell
.\.venv\Scripts\python.exe -m app.adapters.sumo replay `
  --scenario-id aeb_avoids_collision --strategy aeb

.\.venv\Scripts\python.exe -m app.adapters.sumo probe `
  --scenario-id initial_emergency_and_boundaries --strategy aeb
```

回放验证 TraCI 生命周期和坐标映射；原生探针只报告两个模拟器的确定性差异，不声称
任何一方更准确。SUMO 的物理碰撞与 DriveGuard 的点车辆碰撞必须分开解释。详见
[SUMO adapter exploration](sumo-adapter-exploration.md)。

## 7. 常见问题

- **端口被占用**：后端或前端启动输出会说明冲突；停止占用进程或显式选择新端口，并
  同步设置 `VITE_API_BASE_URL` 和允许的开发来源。
- **预设无法加载**：Dashboard 仍允许手工配置；确认后端健康检查和浏览器控制台。
- **收到 `response_contract_error`**：当前后端成功响应与 Dashboard v1 契约不兼容；
  不要绕过校验，应统一前后端版本。
- **SUMO 测试被跳过**：基础验证故意排除 SUMO；使用 `scripts/verify-sumo.ps1` 获得
  fail-closed 的严格结果。
- **结果与真实车辆不同**：这是简化模型的预期限制，不应据此标定或控制真实车辆。
