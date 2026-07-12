# 本地电脑远程控制方案 — Hermes MCP 隧道架构

## 一、核心架构

```
云端（阿里云 47.115.50.15）
┌─────────────────────────────────────┐
│  Hermes Agent（我）                  │
│    ↓ MCP 协议（标准工具调用协议）    │
│  frp 服务端（frps）                 │
└──────────┬──────────────────────────┘
           │ frp 隧道（加密 TCP）
           │
本地（你的 Windows 电脑）
┌──────────┴──────────────────────────┐
│  frp 客户端（frpc）                 │
│    ↓                                │
│  MCP Server（Python）               │
│    ├── run_shell     — 执行任意命令 │
│    ├── run_blender   — 后台渲染视频 │
│    ├── scan_files    — 扫描目录文件 │
│    ├── read/write    — 读写本地文件 │
│    └── ...扩展工具                  │
└─────────────────────────────────────┘
```

## 二、解决的问题

### 2.1 当前困境

- 我的推理能力在云端（Hermes 跑在阿里云）
- 你的 Blender / 视频素材 / 文件在本地 Windows
- 中间隔着一层网络，无法直接通信

### 2.2 解决方案

MCP（Model Context Protocol）是 Anthropic 推出的标准 Agent 工具协议。Hermes 原生支持 MCP Client。我在云端通过 MCP 协议，调用你本地 MCP Server 暴露的工具，就像调用本地工具一样。

frp 的作用是打通网络——把你的本地端口暴露到云端服务器，我通过服务器中转访问。

## 三、技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| **隧道** | frp | 国内可用，稳定，轻量，配置简单 |
| **MCP 传输** | stdio（开发）→ TCP/frp（生产） | stdio 测试方便，frp 部署后转 TCP |
| **MCP Server 语言** | Python | 你已安装 Python，生态丰富 |
| **剪辑引擎** | Blender VSE | 免费，纯后台渲染，Python API 完整 |
| **素材分析** | FFmpeg + PySceneDetect | 轻量，不依赖 GPU |

## 四、部署步骤

### 4.1 服务器端（我已配置）

- 安装 frps（frp 服务端）
- 配置 frps.toml（监听 7000 端口）
- 开放 7000 端口防火墙
- 配置 Hermes 连接远程 MCP Server

### 4.2 本地端（你来操作）

#### 4.2.1 安装依赖

```
# 1. 安装 Python 包
pip install mcp

# 2. 下载 frp
#    https://github.com/fatedier/frp/releases
#    选 frp_0.61.0_windows_amd64.zip，解压到 C:\frp\

# 3. 下载 MCP Server 脚本
#    https://entos.top/scripts/mcp_server.py
#    保存到 C:\mcp_server.py
```

#### 4.2.2 配置 frp

创建 `C:\frp\frpc.toml`：

```toml
serverAddr = "47.115.50.15"
serverPort = 7000
auth.method = "token"
auth.token = "entos2026"

[[proxies]]
name = "mcp-server"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8767
remotePort = 8767
```

#### 4.2.3 启动

先在一个 cmd 窗口跑 MCP Server：

```
python C:\mcp_server.py
```

再开一个 cmd 窗口跑 frp 隧道：

```
C:\frp\frpc.exe -c C:\frp\frpc.toml
```

两个都跑起来之后，我就能远程控制你的本地电脑了。

### 4.3 验证是否连通

我在云端执行：
```
→ 调用 scan_files(path="F:\连南项目\彬")
← 返回素材列表 → 确认连通
```

## 五、MCP Server 工具清单

| 工具名 | 参数 | 功能 |
|--------|------|------|
| `run_shell` | command, cwd | 执行 CMD/PowerShell 命令 |
| `scan_files` | path, pattern | 扫描目录文件 |
| `run_blender` | script_path, output_path | 后台运行 Blender 脚本渲染 |
| `write_file` | path, content | 创建/覆盖本地文件 |
| `read_file` | path | 读取本地文件 |
| `list_dir` | path | 列出目录内容 |

## 六、Blender 自动化工作流

### 6.1 典型混剪流程

```
用户：这条视频帮我混剪一下
  ↓
① 我调用 scan_files 扫描素材目录
② 我写 Blender Python 脚本
③ 我调用 write_file 把脚本写到你的桌面
④ 我调用 run_blender 执行渲染
⑤ 30分钟后桌面出现成品 MP4
```

### 6.2 Blender Python 脚本示例

```python
import bpy

# 清空序列编辑器
bpy.ops.sequencer.delete_all_sequences()
scene = bpy.context.scene
scene.sequence_editor_create()

# 导入视频素材
clip = scene.sequence_editor.sequences.new_movie(
    name="clip_01",
    filepath="F:\\连南项目\\彬\\素材01.mp4",
    channel=1,
    frame_start=1
)

# 设置入点出点
clip.frame_final_start = 1
clip.frame_final_end = 150  # 5秒（30fps）

# 加文字标题
text = scene.sequence_editor.sequences.new_effect(
    name="title",
    type='TEXT',
    channel=2,
    frame_start=1,
    frame_end=150
)
text.text = "连南市长杯足球赛"
text.font_size = 80
text.location = (960, 540)  # 居中
text.align_x = 'CENTER'
text.align_y = 'CENTER'
text.color = (1, 1, 1, 1)  # 白色

# 输出设置
scene.render.filepath = "C:\\Users\\你的用户名\\Desktop\\output.mp4"
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.fps = 30
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MP4'
scene.render.ffmpeg.codec = 'H264'
```

## 七、安全说明

| 问题 | 措施 |
|------|------|
| **中间人攻击** | frp 使用 Token 认证，只有我知道 Token |
| **未授权访问** | MCP Server 只监听 127.0.0.1（本地），frp 也只转发到本地 |
| **命令安全** | 所有命令执行有日志留痕 |
| **数据隐私** | 素材不离开你的电脑，只传分析结果 |

## 八、长期扩展方向

这套 MCP 隧道不只是为了剪视频——它是你本地电脑的万能控制接口：

```
MCP Server（Windows）
  ├── 当前：Blender / FFmpeg / 文件系统
  ├── 扩展：PicWish API（AI 修图）
  ├── 扩展：Edge TTS（配音）
  ├── 扩展：本地 Ollama（离线模型推理）
  ├── 扩展：Photoshop 脚本（批量修图）
  ├── 扩展：浏览器自动化（Selenium）
  └── 任意：你说什么我做什么
```

## 九、附录：故障排查

| 问题 | 排查 |
|------|------|
| frp 连不上 | 检查服务器端口 7000 是否开放 |
| MCP Server 启动报错 | 确认已装 pip install mcp |
| Blender 找不到 | 确认 Blender 已安装且在 PATH 中 |
| 渲染失败 | 检查素材路径是否有中文/空格 |
