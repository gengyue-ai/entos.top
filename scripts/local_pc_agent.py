# local_pc_agent.py — Remote PC Agent 主程序
# 打包：pyinstaller --onefile --windowed --name "RemotePCAgent" local_pc_agent.py
import os, sys, json, subprocess, asyncio, threading, webbrowser, uuid, time, shutil
from pathlib import Path

APP_NAME = "Remote PC Agent"
VERSION = "1.0.0"
MCP_PORT = 8767
GUI_PORT = 18767
DATA_DIR = Path.home() / ".remote-pc-agent"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ─── MCP Server ───
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from mcp.server.sse import SseServerTransport

mcp = Server("remote-pc-agent")

@mcp.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(name="scan_files", description="Scan directory",
             inputSchema={"type":"object","properties":{"path":{"type":"string"},"pattern":{"type":"string"}},"required":["path"]}),
        Tool(name="run_shell", description="Run command",
             inputSchema={"type":"object","properties":{"command":{"type":"string"}},"required":["command"]}),
        Tool(name="run_blender", description="Render Blender script",
             inputSchema={"type":"object","properties":{"script_path":{"type":"string"},"output_path":{"type":"string"}},"required":["script_path","output_path"]}),
        Tool(name="get_status", description="Agent status",
             inputSchema={"type":"object","properties":{}}),
    ]

@mcp.call_tool()
async def call_tool(name: str, args: dict) -> list:
    if name == "scan_files":
        fs = [str(f) for f in Path(args["path"]).rglob(f"*{args.get('pattern','')}") if f.is_file()]
        return [TextContent(type="text", text=json.dumps(fs[:200], ensure_ascii=False))]
    elif name == "run_shell":
        r = subprocess.run(args["command"], shell=True, capture_output=True, text=True, timeout=600)
        return [TextContent(type="text", text=f"OK:{r.stdout[:3000]}\nERR:{r.stderr[:1000]}")]
    elif name == "run_blender":
        b = shutil.which("blender") or "D:\\Program Files\\Blender\\blender.exe"
        r = subprocess.run(f'"{b}" -b -P "{args["script_path"]}"', shell=True, capture_output=True, text=True, timeout=3600)
        return [TextContent(type="text", text=f"OK:{r.stdout[:2000]}\nERR:{r.stderr[:1000]}")]
    elif name == "get_status":
        return [TextContent(type="text", text=json.dumps({
            "version":VERSION,"blender":bool(shutil.which("blender")),"ffmpeg":bool(shutil.which("ffmpeg"))}))]
    return [TextContent(type="text", text=f"Unknown: {name}")]

def make_mcp():
    sse = SseServerTransport("/mcp/messages/")
    async def sse_handler(request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as s:
            opts = NotificationOptions(tools_changed=False, resources_changed=False, prompts_changed=False)
            caps = mcp.get_capabilities(notification_options=opts, experimental_capabilities={})
            await mcp.run(s[0], s[1], InitializationOptions(server_name="agent", server_version=VERSION, capabilities=caps))
    return Starlette(routes=[Route("/sse", sse_handler), Mount("/mcp/messages/", sse.handle_post_message)])

# ─── Web GUI ───
GUI = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>Remote PC Agent</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:sans-serif;background:#f8fafc;color:#0f172a;padding:40px 24px;max-width:700px;margin:0 auto}
h1{font-size:22px;margin-bottom:24px}
.card{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:20px;margin-bottom:16px}
label{font-size:13px;font-weight:600;display:block;margin-bottom:6px}
input,select{width:100%;padding:10px;border:1px solid #e2e8f0;border-radius:6px;font-size:14px;margin-bottom:12px}
.btn{width:100%;padding:14px;background:#2563eb;color:#fff;border:none;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer}
.btn:disabled{opacity:.5}
.bar{height:8px;background:#e2e8f0;border-radius:4px;overflow:hidden;margin:12px 0}
.fill{height:100%;background:#2563eb;width:0%}
.log{background:#0f172a;color:#e2e8f0;border-radius:8px;padding:16px;font-size:12px;font-family:monospace;height:150px;overflow-y:auto;margin-top:12px;white-space:pre-wrap}
</style>
</head>
<body>
<h1>⚡ Remote PC Agent</h1>
<div class="card">
  <label>素材目录</label>
  <input id="inputPath" placeholder="F:\\连南项目\\彬">
  <label>输出目录</label>
  <input id="outputPath" value="C:\\Users\\michael\\Desktop">
  <label>任务</label>
  <select id="taskSelect">
    <option>足球赛事宣传片混剪</option>
    <option>探店短视频</option>
    <option>活动精华集锦</option>
  </select>
  <button class="btn" id="startBtn" onclick="start()">▶ 开始</button>
  <div class="bar"><div class="fill" id="fill"></div></div>
  <div style="font-size:12px;color:#64748b" id="statusText">就绪</div>
  <div class="log" id="logBox">等待开始...</div>
</div>
<script>
async function start(){
  const btn=document.getElementById('startBtn');btn.disabled=true;btn.textContent='运行中...';
  const r=await fetch('/api/task',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({input:document.getElementById('inputPath').value,output:document.getElementById('outputPath').value})});
  const d=await r.json();
  if(d.error){log('错误: '+d.error);btn.disabled=false;btn.textContent='▶ 开始';return}
  const tid=d.task_id;
  const iv=setInterval(async()=>{
    const pr=await fetch('/api/progress/'+tid);const pd=await pr.json();
    document.getElementById('fill').style.width=pd.progress+'%';
    document.getElementById('statusText').textContent=pd.message;
    if(pd.log)log(pd.log);
    if(pd.progress>=100){clearInterval(iv);btn.textContent='✅ 完成';btn.disabled=false}
  },2000);
}
function log(m){const b=document.getElementById('logBox');b.textContent+=(b.textContent?'\\n':'')+'['+new Date().toLocaleTimeString()+'] '+m;b.scrollTop=b.scrollHeight}
</script>
</body>
</html>"""

# ─── Local API ───
def run_task(task_id, input_path, output_path):
    def update(p, msg, log_msg="", out=""):
        Path(DATA_DIR / f"{task_id}.json").write_text(json.dumps({"progress":p,"message":msg,"log":log_msg,"output":out}))
    update(5, "启动中", "任务已创建")
    time.sleep(1)
    files = list(Path(input_path).glob("*.mp4")) + list(Path(input_path).glob("*.mov")) + list(Path(input_path).glob("*.MTS"))
    update(20, f"找到 {len(files)} 条素材", f"扫描: {len(files)} 条视频")
    if not files: update(100, "未找到素材", "错误: 无视频文件"); return
    list_file = DATA_DIR / f"concat_{task_id}.txt"
    out_file = Path(output_path) / f"output_{task_id}.mp4"
    with open(list_file, "w") as f:
        for v in files[:15]: f.write(f"file '{v}'\n")
    update(50, "拼接中...", f"FFmpeg 拼接 {min(len(files),15)} 段")
    r = subprocess.run(f'ffmpeg -y -f concat -safe 0 -i "{list_file}" -c copy "{out_file}"', shell=True, capture_output=True, text=True, timeout=600)
    list_file.unlink(missing_ok=True)
    if r.returncode == 0: update(100, "✅ 完成", f"输出: {out_file}", str(out_file))
    else: update(100, "❌ 失败", f"FFmpeg 错误: {r.stderr[:200]}", "")

def make_gui():
    from starlette.responses import Response
    routes = [
        Route("/", endpoint=lambda r: Response(GUI, media_type="text/html")),
        Route("/api/task", endpoint=api_task, methods=["POST"]),
        Route("/api/progress/{tid}", endpoint=api_progress),
    ]
    return Starlette(routes=routes)

async def api_task(request):
    body = await request.json()
    inp, out = body.get("input",""), body.get("output","")
    if not inp or not Path(inp).is_dir(): return Response(json.dumps({"error":"目录不存在"}), media_type="application/json")
    tid = uuid.uuid4().hex[:8]
    Path(DATA_DIR / f"{tid}.json").write_text(json.dumps({"progress":0,"message":"初始化","log":"","output":""}))
    threading.Thread(target=run_task, args=(tid, inp, out), daemon=True).start()
    return Response(json.dumps({"task_id":tid}), media_type="application/json")

async def api_progress(request):
    tid = request.path_params["tid"]
    f = DATA_DIR / f"{tid}.json"
    return Response(f.read_text() if f.exists() else json.dumps({"progress":0,"message":"未找到"}), media_type="application/json")

# ─── Main ───
def main():
    import uvicorn
    threading.Thread(target=lambda: uvicorn.run(make_mcp(), host="127.0.0.1", port=MCP_PORT, log_level="warning"), daemon=True).start()
    print(f"\n{APP_NAME} v{VERSION}")
    print(f"MCP:  http://localhost:{MCP_PORT}/sse")
    print(f"GUI:  http://localhost:{GUI_PORT}")
    webbrowser.open(f"http://localhost:{GUI_PORT}")
    uvicorn.run(make_gui(), host="127.0.0.1", port=GUI_PORT, log_level="warning")

if __name__ == "__main__":
    main()
