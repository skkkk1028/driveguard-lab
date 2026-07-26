# 固定公网部署

## 目标架构

生产构建使用单一 HTTPS 域名：

```text
浏览器 https://<service>.onrender.com/
                  │
                  ├── /、/assets/*       React Dashboard
                  ├── /api/v1/*          FastAPI 仿真接口
                  ├── /health            健康检查
                  └── /docs              Swagger UI
```

`Dockerfile` 先使用 Node 24 和 `npm ci` 生成 Vite 静态文件，再使用 Python 3.14
安装后端。最终镜像只包含 Python 运行时、后端包和生产静态文件，并以非 root 用户
`10001` 运行。生产前端默认使用当前页面的同源 `/api/v1`，不会访问 localhost。

本地开发仍使用 Vite `http://localhost:5173` 和 FastAPI
`http://127.0.0.1:8000` 两个进程。

## 部署到 Render

仓库当前没有远端。首次部署需要：

1. 将完整仓库提交并推送到 GitHub、GitLab 或 Bitbucket。不要提交 `.venv`、
   `node_modules`、`dist` 或任何访问令牌。
2. 注册或登录 [Render](https://render.com/)，在 Dashboard 选择 **New →
   Blueprint**。
3. 授权 Render 只读取目标仓库，选择仓库根目录的 `render.yaml`。
4. 检查服务名、`Singapore` 区域和实例类型，然后创建 Blueprint。
5. 等待容器构建、`/health` 检查和首次部署完成。Render 会分配类似
   `https://driveguard-lab-xxxx.onrender.com` 的固定 HTTPS 地址。
6. 依次检查公网 `/`、`/health`、`/docs`，再从手机或另一网络运行一个仿真。

Blueprint 使用 `autoDeployTrigger: checksPass`。后续提交只有在 GitHub Actions
通过后才会自动部署；CI 会构建容器并检查 Dashboard、健康接口和 OpenAPI 版本。

## 免费实例与持续在线

`render.yaml` 默认选择 `free`，避免在没有明确授权时产生费用。根据 Render 当前
官方说明，免费 Web Service 在连续 15 分钟没有入站流量后会休眠；下一次访问会唤醒，
可能等待约一分钟。免费实例适合演示和研究预览，但不等于始终在线的生产服务。

若要求每次打开都立即响应，应在 Render 服务设置中升级为付费实例。不要在 Blueprint
中直接改成付费计划并同步，除非账号所有者已确认费用和预算。

## 自定义固定域名

Render 分配的 `onrender.com` 子域名本身是固定公开网址。如果拥有域名，可以在服务的
**Settings → Custom Domains** 添加例如 `lab.example.com`，按页面给出的记录修改 DNS。
Render 会为验证成功的域名签发和续期 TLS 证书。域名购买、DNS 账号及可能适用的地区
备案要求不属于本仓库，必须由域名和部署账号所有者处理。

## 运行边界

- 当前服务无数据库和用户账户，刷新或重启不会丢失服务器端实验记录，因为结果从未
  持久化；需要保存时应由使用者自行记录响应。
- API 对单请求最多允许 10,000 个推进区间，但公开服务没有认证、配额、分布式限流、
  WAF 规则或服务等级保证。公开传播前应关注云平台用量和日志。
- `render.yaml` 不安装可选 SUMO；公网 Dashboard 始终使用内部确定性仿真器。
- 平台是教学与研究工具，不是安全认证系统或真实车辆控制服务。
- 中国大陆及其他网络环境对境外托管域名的可达性不能由本项目保证，应从目标网络实际
  测试；如迁移到其他容器平台，镜像只要求平台把外部端口转发到 `$PORT`。

官方参考：

- [Render Web Services](https://render.com/docs/web-services)
- [Render Blueprint specification](https://render.com/docs/blueprint-spec)
- [Render free service limits](https://render.com/docs/free)
- [Render custom domains](https://render.com/docs/custom-domains)
