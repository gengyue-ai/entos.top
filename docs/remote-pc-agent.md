# Remote PC Agent — 企业级本地电脑远程控制方案

## 一、产品定位

一套即装即用的远程 PC 控制方案。任何公司下载一个脚本，双击运行，云端 AI 即可远程操控该公司电脑（执行命令、读写文件、运行 Blender 渲染等）。

**不需要在服务器装任何软件，不需要开放防火墙端口。**

## 二、核心架构

```
云端 Hermes（AI 大脑）
    ↕ MCP 协议（HTTP + SSE）
cloudflared 隧道（免费、加密、无需注册）
    ↕
客户电脑
┌─────────────────────────────────────┐
│  一个 Python 脚本 = 整个 MCP Server  │
│    ├── run_shell      — 执行命令    │
│    ├── scan_files     — 扫描文件    │
│    ├── run_blender    — 后台渲染    │
│    ├── read/write     — 读写文件    │
│    ├── get_system_info— 系统信息    │
│    └── 可无限扩展                  │
└─────────────────────────────────────┘
```

## 三、部署流程

### 3.1 客户电脑（3 步，5 分钟）

**第 1 步：装 Python 依赖**
```
pip install mcp uvicorn starlette
```

**第 2 步：下载脚本**
```
https://entos.top/scripts/remote-pc-agent.py.txt
```
重命名为 `remote-pc-agent.py`

**第 3 步：启动**
```
python remote-pc-agent.py
```

你会看到：
```
==================================================
  Remote PC Agent - MCP Server (HTTP/SSE)
  Port: 8767
  SSE:  http://localhost:8767/sse
  Health: http://localhost:8767/health
==================================================

  To expose to internet, run in another terminal:
  cloudflared tunnel --url http://localhost:8767
```

**保持这个窗口不要关。**

**第 4 步：暴露到公网（可选）**

如果需要从云端访问，新开一个 cmd 窗口运行：

```
cloudflared tunnel --url http://localhost:8767
```

会显示一个 `https://xxxxx.trycloudflare.com` 的地址，把这个地址发给云端管理员配置即可。

### 3.2 云端配置

在 Hermes 配置文件中添加 MCP Server：

```yaml
mcp_servers:
  customer-pc:
    url: https://xxxxx.trycloudflare.com/sse
    transport: sse
```

配置后，云端即可调用该电脑的全部工具。

## 四、工具清单

| 工具名 | 参数 | 功能 |
|--------|------|------|
| `run_shell` | command | 执行任意 CMD/PowerShell 命令 |
| `scan_files` | path, pattern | 扫描目录文件（支持后缀过滤） |
| `write_file` | path, content | 创建或覆盖文件 |
| `read_file` | path | 读取文件内容 |
| `list_dir` | path | 列出目录内容（含文件大小） |
| `run_blender` | script_path, output_path | 后台运行 Blender 渲染视频 |
| `get_system_info` | (无) | 获取系统信息（OS / CPU / 内存 / 磁盘） |

## 五、可扩展设计

这个 MCP Server 的核心代码不到 100 行。扩展新工具只需加一个函数：

```python
@server.list_tools()
async def list_tools():
    return [
        # ... 已有工具 ...
        Tool(name="your_new_tool", description="你的新工具功能",
             inputSchema={"type":"object","properties":{...},"required":[...]}),
    ]
```

可扩展的方向：
- AI 修图（调用 PicWish / Remove.bg API）
- AI 配音（调用 Edge TTS）
- Photoshop 自动化（PS 脚本）
- 浏览器自动化（Selenium/Playwright）
- 本地模型推理（Ollama API）

## 六、对比：frp vs cloudflared

| 维度 | frp | cloudflared |
|------|-----|-------------|
| **服务端安装** | 需要（阿里云装 frps） | ❌ 不需要 |
| **客户端操作** | 下载 frpc + 配 toml 文件 | 下载一个 exe，一行命令 |
| **安全性** | Token 认证 | Cloudflare 加密通道 |
| **国内可用** | ✅ 稳定 | ⚠️ 偶尔被墙但可重连 |
| **是否免费** | ✅ 免费 | ✅ 免费（不需要注册） |
| **适合作产品** | ❌ 每家公司要配服务端 | ✅ 客户零配置 |

## 七、安全说明

- MCP Server 默认监听 `127.0.0.1`（仅本地可访问）
- cloudflared 只暴露 HTTP 端口，不暴露文件系统
- 所有命令记录日志，可审计追溯
- 素材数据不离开客户电脑，只传输分析结果

## 八、产品化路线

| 阶段 | 内容 | 时间 |
|------|------|------|
| **MVP** | 单 Python 脚本，客户手动启动 | 今天 |
| **V2** | PyInstaller 打包成 exe，双击即运行 | 1 天 |
| **V3** | 注册为 Windows 服务，开机自启 | 2 天 |
| **V4** | Web 管理面板，可视化监控多台 PC | 1 周 |
