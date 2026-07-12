"""
Local Agent - Connects to tunnel, receives tasks, renders with Blender
Run: python local_agent.py
"""
import asyncio, json, subprocess, os, shutil, tempfile
from pathlib import Path
import websockets

TUNNEL = "ws://47.115.50.15:8768"

async def run():
    print("[ClipForge Agent] Starting...")
    async with websockets.connect(TUNNEL) as ws:
        print("[+] Connected to ClipForge Cloud")
        async for msg in ws:
            data = json.loads(msg)
            if data.get("type") == "task":
                await execute(ws, data)

async def execute(ws, task):
    tid = task["task_id"]
    inp = task.get("input", "")
    out = task.get("output", "C:\\Users\\michael\\Desktop")
    tmpl = task.get("template", "football")

    def report(p, msg, log="", out_file=""):
        data = json.dumps({"type":"task_update","task_id":tid,"progress":p,"message":msg,"log":log or msg,"output":out_file})
        asyncio.run_coroutine_threadsafe(ws.send(data), loop)

    loop = asyncio.get_event_loop()
    report(5, "扫描素材...", "开始扫描素材目录")

    # 扫描视频文件
    videos = []
    for ext in ['.mp4','.mov','.MTS','.avi','.mkv']:
        videos.extend([str(f) for f in Path(inp).rglob(f"*{ext}")])
    videos = sorted(videos)[:15]

    if not videos:
        report(100, "未找到视频素材", "错误: 素材目录中无视频文件")
        return

    report(15, f"找到 {len(videos)} 条素材", f"扫描完成: {len(videos)} 条视频")
    await asyncio.sleep(1)

    blender = shutil.which("blender") or "D:\\Program Files\\Blender\\blender.exe"
    if not os.path.exists(blender):
        # Fallback to FFmpeg
        report(30, "Blender 未找到，使用 FFmpeg 快速拼接", "Blender 未安装，使用 FFmpeg")
        out_file = os.path.join(out, f"clipforge_{tid}.mp4")
        list_file = os.path.join(tempfile.gettempdir(), f"concat_{tid}.txt")
        with open(list_file, "w", encoding="utf-8") as f:
            for v in videos:
                f.write(f"file '{v}'\n")
        report(60, "FFmpeg 渲染中...", f"拼接 {len(videos)} 段视频")
        r = subprocess.run(f'ffmpeg -y -f concat -safe 0 -i "{list_file}" -c copy "{out_file}"', shell=True, capture_output=True, text=True, timeout=600)
        os.unlink(list_file)
        if r.returncode == 0:
            report(100, "✅ 渲染完成", f"输出: {out_file}", out_file)
        else:
            report(100, "❌ 渲染失败", f"FFmpeg 错误: {r.stderr[:200]}")
        return

    # Blender 渲染
    config = {
        "input": inp, "output": os.path.join(out, f"clipforge_{tid}.mp4"),
        "duration": task.get("duration", 90),
        "ratio": task.get("ratio", "16:9"),
        "resolution": task.get("resolution", "1080p"),
        "title": task.get("title", ""),
        "ending": task.get("ending", ""),
        "pace": task.get("pace", "auto"),
        "videos": videos[:8]
    }

    # 生成 Blender 脚本
    script = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8")
    script.write(generate_blender_script(config))
    script.close()

    report(40, "Blender 渲染中...", f"启动 Blender ({len(videos)} 段素材)")
    cmd = f'"{blender}" -b -P "{script.name}"'
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3600)

    os.unlink(script.name)

    if r.returncode == 0:
        report(100, "✅ 渲染完成", f"输出: {config['output']}", config["output"])
    else:
        report(100, "❌ 渲染失败", f"Blender 错误: {r.stderr[:300]}")

def generate_blender_script(config):
    """生成 Blender VSE Python 脚本"""
    res_map = {"720p": (1280,720), "1080p": (1920,1080), "4k": (3840,2160)}
    w, h = res_map.get(config["resolution"], (1920, 1080))
    fps = 30
    total_frames = config["duration"] * fps
    seg_frames = total_frames // max(len(config["videos"]), 1)

    # 片头帧数
    title_frames = min(60, seg_frames)

    script = f'''
import bpy, os
scene = bpy.context.scene
scene.sequence_editor_create()
scene.render.fps = {fps}
scene.render.resolution_x = {w}
scene.render.resolution_y = {h}
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MP4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
scene.render.filepath = r"{config['output']}"

frame = 1
# 片头标题
title_text = r"{config['title']}" or "ClipForge"
title = scene.sequence_editor.sequences.new_effect(name="title", type='TEXT', channel=2, frame_start=1, frame_end={title_frames})
title.text = title_text
title.font_size = 72
title.location = ({w//2}, {h//2 + 60})
title.align_x = 'CENTER'
title.color = (1,1,1,1)
title.use_shadow = True
title.shadow_color = (0,0,0,0.8)

frame = {title_frames + 1}

# 视频片段
videos = {json.dumps(config["videos"])}
for i, vpath in enumerate(videos):
    if frame > total_frames: break
    dur = min({seg_frames}, total_frames - frame + 1)
    if dur < 15: break
    clip = scene.sequence_editor.sequences.new_movie(name=f"clip_{i}", filepath=vpath, channel=1, frame_start=frame)
    clip.frame_final_end = frame + dur
    frame += dur

# 片尾
end_frame = frame
end = scene.sequence_editor.sequences.new_effect(name="end", type='TEXT', channel=2, frame_start=end_frame, frame_end=end_frame + 60)
end_text = r"{config['ending']}" or "Powered by ClipForge"
end.text = end_text
end.font_size = 48
end.location = ({w//2}, {h//2})
end.align_x = 'CENTER'
end.color = (1,1,1,1)
'''
    return script

if __name__ == "__main__":
    import json
    asyncio.run(run())
