# AI Chat - 智能对话助手

基于 Vue 3 + FastAPI + Supabase + OpenRouter 的 AI 聊天应用，部署在 Vercel 免费平台上。

## 技术架构

- **前端**: Vue 3 + Vite（现代深色主题 UI）
- **后端**: Python FastAPI（Vercel Serverless Function）
- **数据库**: Supabase（聊天记录存储）
- **AI 模型**: OpenRouter (qwen3-coder:free)
- **部署**: Vercel 免费版

## 项目结构

```
├── api/                    # 后端 (Vercel Serverless)
│   └── index.py            # FastAPI 主入口
├── src/                    # 前端 (Vue 3)
│   ├── main.js             # 入口文件
│   ├── App.vue             # 根组件
│   ├── components/         # UI 组件
│   │   ├── Sidebar.vue     # 侧边栏（对话列表）
│   │   ├── ChatView.vue    # 聊天主视图
│   │   ├── MessageList.vue # 消息列表
│   │   ├── MessageBubble.vue # 消息气泡
│   │   └── ChatInput.vue   # 输入框
│   ├── services/           # API 服务
│   │   └── api.js          # 后端通信 & Markdown 渲染
│   └── assets/
│       └── style.css       # 全局样式
├── supabase/
│   └── migration.sql       # 数据库建表脚本
├── vercel.json             # Vercel 部署配置
├── vite.config.js          # Vite 构建配置
└── package.json            # 前端依赖
```

## 本地开发

### 1. 克隆项目并安装依赖

```bash
# 安装前端依赖
npm install

# 安装后端依赖（本地开发用）
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入你的配置：

```bash
cp .env.example .env
```

需要配置：
- `OPENROUTER_API_KEY` - OpenRouter API 密钥
- `SUPABASE_URL` - Supabase 项目 URL
- `SUPABASE_KEY` - Supabase Anon Key

### 3. 设置 Supabase 数据库

1. 在 [Supabase](https://supabase.com) 创建项目
2. 进入 SQL Editor，执行 `supabase/migration.sql` 中的 SQL
3. 复制项目 URL 和 Anon Key 到 `.env`

### 4. 启动开发服务器

```bash
# 终端 1: 启动后端
uvicorn api.index:app --reload --port 8000

# 终端 2: 启动前端
npm run dev
```

访问 http://localhost:5173

## 部署到 Vercel

### 1. 推送代码到 GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push -u origin main
```

### 2. 在 Vercel 中部署

1. 访问 [Vercel](https://vercel.com)，导入你的 GitHub 仓库
2. 配置环境变量：
   - `OPENROUTER_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SITE_URL`（可选，你的网站 URL）
   - `SITE_NAME`（可选，你的网站名称）
3. 点击 Deploy

### 3. Vercel 免费版限制

- Serverless Function 执行时间: 最大 10s（Hobby）/ 60s（Pro）
- 每月 Serverless Function 调用次数: 100,000
- 带宽: 100 GB/月
- 构建时间: 6,000 分钟/月

## 功能特性

- 流式输出（SSE），AI 回复逐字显示
- 多会话管理（侧边栏切换对话）
- 本地存储聊天记录
- Supabase 云端同步（可选）
- Markdown 渲染（代码高亮、列表等）
- 响应式设计，支持移动端
- 现代深色主题 UI
