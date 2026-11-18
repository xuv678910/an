# 全球金融与财政每日简报（GitHub Actions 云端版）

本目录用于在 **GitHub Actions** 云端自动运行每日金融与财政简报，**无需本地电脑开机**，每个工作日（周一至周五）北京时间早上 **9:00**（UTC `01:00`）自动检索全球最新资讯并发送至您的 Gmail 邮箱。

## 部署步骤（约 3 分钟）

### 第 1 步：获取 Gemini API Key
1. 登录 [Google AI Studio](https://aistudio.google.com/apikey)。
2. 点击 **Create API key**，生成并复制您的 API Key。

### 第 2 步：创建 GitHub 私有仓库并上传代码
1. 在 GitHub 上新建一个 **Private（私有）** 仓库（例如 `daily-finance-briefing`）。
2. 将本目录（`d:\Google\daily-finance-cloud`）下的所有文件（**注意包含 `.github/workflows/daily-briefing.yml` 隐藏目录**）推送到该仓库的默认分支。

### 第 3 步：配置仓库 Secrets（密钥）
进入 GitHub 仓库页面 → **Settings** → 左侧 **Secrets and variables** → **Actions** → 点击 **New repository secret**，依次添加以下 4 个必需密钥：

| Name | Value 说明 |
| :--- | :--- |
| `GEMINI_API_KEY` | 第 1 步获取的 Gemini API Key |
| `SENDER_EMAIL` | 发件人邮箱（如 `xuv.678910@gmail.com`） |
| `RECIPIENT_EMAIL` | 收件人邮箱（如 `xuv.678910@gmail.com`） |
| `SMTP_PASSWORD` | 您的 16 位 Gmail 应用专用密码（去掉空格） |

> （可选）如果您改用 QQ/163 邮箱发信，可额外添加 `SMTP_SERVER` 和 `SMTP_PORT` 两个 Secret；若不添加，默认使用 `smtp.gmail.com` 和 `465`。

### 第 4 步：立即手动测试一次
1. 打开 GitHub 仓库顶部的 **Actions** 标签页。
2. 左侧选择 **Daily Global Finance Briefing**。
3. 点击右侧的 **Run workflow** → **Run workflow**，等待约 30 秒，您的 Gmail 就会收到一封云端生成的简报！

> **提示**：GitHub Actions 的定时任务在整点高峰期可能会有几分钟至十几分钟的调度延迟，属于正常现象。
