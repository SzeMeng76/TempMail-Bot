<h1 align="center">TempMail 💌</h1>

<p align="center">
  <a href="https://github.com/bisnuray/TempMail-Bot/stargazers"><img src="https://img.shields.io/github/stars/bisnuray/TempMail-Bot?color=blue&style=flat" alt="GitHub Repo stars"></a>
  <a href="https://github.com/bisnuray/TempMail-Bot/issues"><img src="https://img.shields.io/github/issues/bisnuray/TempMail-Bot" alt="GitHub issues"></a>
  <a href="https://github.com/bisnuray/TempMail-Bot/pulls"><img src="https://img.shields.io/github/issues-pr/bisnuray/TempMail-Bot" alt="GitHub pull requests"></a>
  <a href="https://github.com/bisnuray/TempMail-Bot/graphs/contributors"><img src="https://img.shields.io/github/contributors/bisnuray/TempMail-Bot?style=flat" alt="GitHub contributors"></a>
  <a href="https://github.com/bisnuray/TempMail-Bot/network/members"><img src="https://img.shields.io/github/forks/bisnuray/TempMail-Bot?style=flat" alt="GitHub forks"></a>
</p>

<p align="center">
  <em>基于 mail.tm 的临时邮箱工具，包含 Telegram 机器人和网页两种使用方式。</em>
</p>
<hr>

## 项目结构

```
.
├── tempmail.py, config.py        # Telegram 机器人（Pyrogram）
├── Dockerfile                    # bot 镜像
├── frontend/                     # 网页前端（React + Vite），纯客户端直连 mail.tm API
│   └── Dockerfile                # web 镜像（多阶段构建，最终由 nginx 提供静态文件）
├── docker-compose.yaml           # 同时拉起 bot 和 web 两个容器
└── .github/workflows/            # CI：分别构建并推送 bot / web 两个多架构镜像到 GHCR
```

bot 和网页各自独立打包成镜像，互不依赖，都是直接调用 [mail.tm](https://mail.tm) 的公共 API。

## 功能

### Telegram 机器人

- `/tmail` - 随机生成一个临时邮箱和密码
- `/tmail [用户名]:[密码]` - 使用指定的用户名和密码生成邮箱
- `/cmail [邮箱令牌]` - 使用令牌查看最近的 10 封邮件
- 通过按钮直接在 Telegram 内查看邮件详情

### 网页前端

- 打开即自动生成一个临时邮箱，地址+密码保存在浏览器本地，刷新页面不丢失
- 收件箱每 10 秒自动刷新，支持手动刷新、复制地址、换一个、恢复已有邮箱
- 点击邮件查看详情（HTML/纯文本内容）
- 纯静态页面，不依赖任何自建后端或数据库

## 部署

### 方式一：Docker Compose（推荐）

1. 复制环境变量文件并填入你的 Telegram 配置：

   ```bash
   cp .env.example .env
   ```

   编辑 `.env`：

   ```env
   API_ID=你的API_ID
   API_HASH=你的API_HASH
   BOT_TOKEN=你的BOT_TOKEN
   ```

   - `API_ID` / `API_HASH`：在 [my.telegram.org](https://my.telegram.org) 创建应用获取
   - `BOT_TOKEN`：从 [@BotFather](https://t.me/BotFather) 获取

2. 拉起服务：

   ```bash
   docker compose up -d
   ```

   默认会启动两个容器：

   | 服务 | 说明 | 端口 |
   |---|---|---|
   | `tempmail-bot` | Telegram 机器人 | - |
   | `tempmail-web` | 网页前端 | `8080` |

   网页启动后访问 `http://<你的服务器IP>:8080` 即可使用。

   `docker-compose.yaml` 默认从 GHCR 拉取已构建好的镜像（`ghcr.io/szemeng76/tempmail-bot` / `tempmail-web`）。如果想本地构建，把对应服务的 `image:` 换成：

   ```yaml
   build: .          # tempmail-bot
   build: ./frontend # tempmail-web
   ```

3. 查看日志 / 停止服务：

   ```bash
   docker compose logs -f
   docker compose down
   ```

   机器人的登录 session 会持久化在 `./sessions` 目录，容器重启不需要重新登录。

### 方式二：本地直接运行机器人

```bash
git clone https://github.com/bisnuray/TempMail-Bot
cd TempMail-Bot
pip install -r requirements.txt
```

编辑 `config.py` 或设置环境变量 `API_ID` / `API_HASH` / `BOT_TOKEN`，然后运行：

```bash
python tempmail.py
```

### 方式三：本地开发网页前端

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173`。构建生产版本用 `npm run build`，产物在 `frontend/dist`。

## CI / 镜像构建

`.github/workflows/docker-build.yml` 会在 push 到 `main`、打 `v*` tag 或手动触发时，分别为 `tempmail-bot` 和 `tempmail-web` 构建 `linux/amd64` + `linux/arm64` 双架构镜像，合并成多架构 manifest 后推送到 GitHub Container Registry：

- `ghcr.io/<owner>/tempmail-bot`
- `ghcr.io/<owner>/tempmail-web`

## 注意事项

✨ 生成邮箱后会拿到一个邮箱令牌（token），该令牌可用于查看这个临时邮箱收到的邮件，请妥善保管，不要泄露给他人。mail.tm 的公共接口限流为每个 IP 每秒 8 次请求（8 QPS）。

## 作者

- Name: Bisnu Ray
- Telegram: [@itsSmartDev](https://t.me/itsSmartDev)

Feel free to reach out if you have any questions or feedback.
