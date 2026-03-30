# 小智数字助手（Xiaozhi Digital Assistant）

AI 驱动的数字助手，基于阿里通义千问模型，提供智能对话和内容生成能力。

## 项目结构

```
├── backend/                 # FastAPI 后端应用
│   ├── main.py              # FastAPI 主应用
│   ├── config.py            # 配置管理
│   ├── llm_wrapper.py       # 通义千问 LLM 封装
│   ├── llm_service.py       # LLM 服务示例
│   ├── requirements.txt      # Python 依赖
│   ├── .env.example         # 环境变量模板
│   └── .gitignore           # Git 忽略文件
│
├── frontend/                # React 前端应用
│   ├── src/
│   │   ├── main.jsx         # 入口文件
│   │   ├── App.jsx          # 主应用组件
│   │   ├── index.css        # 全局样式
│   │   └── components/      # React 组件
│   │       ├── ChatWindow.jsx
│   │       ├── Header.jsx
│   │       ├── MessageBubble.jsx
│   │       ├── InputBox.jsx
│   │       └── index.js
│   ├── index.html           # HTML 入口
│   ├── package.json         # Node 依赖
│   ├── vite.config.js       # Vite 配置
│   ├── tailwind.config.js   # Tailwind CSS 配置
│   ├── postcss.config.js    # PostCSS 配置
│   ├── .gitignore           # Git 忽略文件
│   └── .env.example         # 环境变量模板
│
└── README.md                # 项目文档
```

## 快速开始

### 1. 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 DASHSCOPE_API_KEY

# 启动服务
python main.py
# 或
uvicorn main:app --reload
```

后端 API 文档: http://localhost:8000/docs

### 2. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建
npm run build

# 预览
npm run preview
```

前端应用: http://localhost:5173

## 第一阶段任务

### Task 1.1: FastAPI 后端初始化 ✅
- ✅ 初始化 FastAPI 环境
- ✅ 配置环境变量（API_KEY）
- ✅ 设置 CORS 中间件
- ✅ 创建健康检查端点

文件:
- `backend/main.py` - FastAPI 主应用
- `backend/config.py` - 配置管理
- `backend/requirements.txt` - 依赖管理
- `backend/.env.example` - 环境变量模板

### Task 1.2: 通义千问 LLM 集成 ✅
- ✅ 封装 Tongyi LLM 调用类
- ✅ 支持单轮对话和多轮对话
- ✅ 集成 LangChain Community
- ✅ 实现对话历史管理

文件:
- `backend/llm_wrapper.py` - LLM 封装类
- `backend/llm_service.py` - 集成示例

### Task 1.3: React 前端脚手架 ✅
- ✅ 初始化 React + Vite 项目
- ✅ 集成 Tailwind CSS
- ✅ 创建聊天界面组件
- ✅ 配置 API 代理

文件:
- `frontend/src/App.jsx` - 主应用
- `frontend/src/components/` - UI 组件
- `frontend/index.html` - HTML 入口
- `frontend/package.json` - 依赖管理
- `frontend/vite.config.js` - Vite 配置
- `frontend/tailwind.config.js` - Tailwind 配置

## API 端点

### 健康检查
```
GET /health
```

### 聊天
```
POST /chat
Content-Type: application/json

{
  "message": "你好",
  "conversation_id": "optional",
  "temperature": 0.7,
  "max_tokens": null
}

Response:
{
  "response": "你好！...",
  "conversation_id": "xxx",
  "tokens_used": 50
}
```

## 技术栈

### 后端
- **框架**: FastAPI
- **服务器**: Uvicorn
- **LLM**: LangChain + Tongyi (阿里通义千问)
- **配置管理**: Pydantic Settings

### 前端
- **框架**: React 18
- **构建工具**: Vite
- **样式**: Tailwind CSS
- **HTTP 客户端**: Axios

## 环境变量

### 后端 (.env)
```
DASHSCOPE_API_KEY=your_api_key_here
DEBUG=True
API_HOST=0.0.0.0
API_PORT=8000
```

## 下一步

第二阶段：核心功能扩展
- 多种对话模式（翻译、代码生成等）
- 对话上下文管理和持久化
- 用户认证系统
- 对话历史导出

## 许可证

MIT
