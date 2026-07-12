"""
Blender 混剪模板 — 足球赛事宣传片
云端生成此脚本，客户端执行 blender -b -P this_script.py
素材路径和输出路径通过命令行参数传入
"""
import bpy, sys, json, os

# 解析参数
argv = sys.argv[sys.argv.index("--") + 1:]
CONFIG = json.loads(argv[0]) if argv else {}
MATERIAL_DIR = CONFIG.get("input", "")
OUTPUT_PATH = CONFIG.get("output", "")
MUSIC_PATH = CONFIG.get("music", "")

# 清空序列编辑器
bpy.ops.sequencer.delete_all_sequences()
scene = bpy.context.scene
scene.sequence_editor_create()
scene.render.fps = 30
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MP4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'HIGH'

# 扫描素材
import glob
videos = sorted(glob.glob(os.path.join(MATERIAL_DIR, "*.mp4"))) + \
         sorted(glob.glob(os.path.join(MATERIAL_DIR, "*.mov")))
videos = videos[:12]  # 最多12段

frame = 1  # 当前帧位置

# 片头标题（2秒）
text = scene.sequence_editor.sequences.new_effect(
    name="title", type='TEXT', channel=2,
    frame_start=1, frame_end=60)
text.text = "连南市长杯足球赛"
text.font_size = 72
text.location = (960, 600)
text.align_x = 'CENTER'
text.color = (1, 1, 1, 1)
text.shadow_color = (0, 0, 0, 0.8)
text.shadow_angle = 0
text.use_shadow = True

subtitle = scene.sequence_editor.sequences.new_effect(
    name="subtitle", type='TEXT', channel=3,
    frame_start=1, frame_end=60)
subtitle.text = "Liannan Mayor's Cup Football Tournament"
subtitle.font_size = 36
subtitle.location = (960, 520)
subtitle.align_x = 'CENTER'
subtitle.color = (1, 1, 0, 1)

frame = 61

# 拼接每段视频（每段3-4秒）
for i, v in enumerate(videos):
    duration = 90  # 3秒 @30fps
    clip = scene.sequence_editor.sequences.new_movie(
        name=f"clip_{i}", filepath=v,
        channel=1, frame_start=frame)
    clip.frame_final_end = frame + duration

    # 文件名作为小标签
    name_text = scene.sequence_editor.sequences.new_effect(
        name=f"label_{i}", type='TEXT', channel=2,
        frame_start=frame, frame_end=frame + duration)
    name_text.text = os.path.splitext(os.path.basename(v))[0]
    name_text.font_size = 24
    name_text.location = (960, 80)
    name_text.align_x = 'CENTER'
    name_text.color = (1, 1, 1, 1)

    frame += duration

# 结尾字幕（3秒）
end = scene.sequence_editor.sequences.new_effect(
    name="end_title", type='TEXT', channel=2,
    frame_start=frame, frame_end=frame + 90)
end.text = "连南足球 · 永不止步"
end.font_size = 60
end.location = (960, 540)
end.align_x = 'CENTER'
end.color = (1, 1, 1, 1)

# 输出
if OUTPUT_PATH:
    scene.render.filepath = OUTPUT_PATH

print(f"Rendering {frame + 90} frames to {OUTPUT_PATH}")
