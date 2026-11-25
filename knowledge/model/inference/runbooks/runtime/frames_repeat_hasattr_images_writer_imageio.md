---
{
  "type": "Runbook",
  "title": "MiniMax-H3 FL2VA 推理产物 mp4 无声：save_output 音视频分立 + [0,1] 帧值域被 [-1,1] 公式压缩致偏亮",
  "description": "Ascend NPU（本次实际型号未记录）上以 cann-recipes-infer 版 MiniMax-H3（diffusers `MiniMaxH3ModularPipeline`，FL2VA 变体，768×1280/129 帧/50 步/32kHz 立体声）跑端到端推理，产物为 `fl2va_output.mp4`（无声音）+ `fl2va_output.wav` 两个文件。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": []
}
---

# MiniMax-H3 FL2VA 推理产物 mp4 无声：save_output 音视频分立 + [0,1] 帧值域被 [-1,1] 公式压缩致偏亮

## 适用场景

- README中的A2/A3仅为样例支持列表，不代表本次运行设备已定位。

Ascend NPU（本次实际型号未记录）上以 cann-recipes-infer 版 MiniMax-H3（diffusers `MiniMaxH3ModularPipeline`，FL2VA 变体，768×1280/129 帧/50 步/32kHz 立体声）跑端到端推理，产物为 `fl2va_output.mp4`（无声音）+ `fl2va_output.wav` 两个文件，需确认正确形态并修复输出管线时适用。

## 触发与观测

- 触发（source 0 seq 1，用户报告）：result 目录下 `.mp4 文件没有声音`，询问是否应为单文件含声。
- 产物观测（source 0 seq 13）：`results/` 下 `fl2va_output.mp4`（12986364B）与 `fl2va_output.wav`（752044B）并存。
- 参照系观测（source 0 seq 70/79，任务检视 + 开源仓检索）：仓库内 hunyuan-video/sana-video 均为纯视频、不生成音频；wan2.2-i2v 定义了 ffmpeg `merge_video_audio` 辅助函数但推理链路未调用；原始开源 MiniMax-H3 仓库不含任何 save/mux 代码；diffusers `MiniMaxH3ModularPipeline`（decoders.py）把 `videos`/`audio`/`sampling_rate` 作为独立输出返回；参考 API 脚本（scripts/readme/*.sh）最终都从服务端下载单个含音频 mp4。

## 探针与操作

- 读 diffusers `export_utils.py`（seq 124）：存在 `encode_video()`（export_utils.py:303），PyAV 后端，可将视频帧 + 音频 tensor mux 进单个 mp4；Cosmos pipeline 的 `Cosmos3ExportStep` 是既有模式：有音频用 `encode_video`、无音频用 `export_to_video`。
- 读 `postprocess_video`/`postprocess`（seq 138/143，inspect.getsource）：pipeline 输出的 `videos` 为 `[1, F, C, H, W]`、值域 [0,1]，`audio` 为 `[1, 2, num_samples]`。

## 机制与判别

- 根因一（无声）：`save_output`（infer_minimax_h3.py:203-251）用 `imageio.get_writer(output_path, fps=fps, codec="libx264", ...)` 只写视频流，音频经 soundfile 单独写 `.wav`，两者从不合并——与"统一生成 32kHz 立体声音频视频"的产品形态不符。
- 根因二（值域，顺带发现）：帧转换 `frames = (frames.clamp(-1, 1) * 127.5 + 127.5).byte()` 假设输入是 [-1,1]；而 pipeline 输出实测为 [0,1]，该公式把 [0,1] 映射到 [127.5, 255]，丢失下半动态范围导致画面整体偏亮。判别依据是 diffusers 输出值域（源码级确认，非视觉复测）。
- 修复（source 0 seq 153，before/after 全文见「探针与操作」小节）：有音频时改走 `diffusers.utils.encode_video(frames, fps=fps, audio=audio_data, audio_sample_rate=sampling_rate, output_path=...)`；无音频保留 imageio 路径；帧转换改为 `(frames.clamp(0, 1) * 255).round().to(torch.uint8)`；wav 仍单独保留不破坏既有产物。

## 验证信号

- 本地 PyAV 容器级测试（source 0 seq 172/173，tool_observed）：4 帧合成视频 + `randn(2, 32000)` 双声道音频经 `encode_video` 写 mp4 后 `av.open` 检查输出：`Video streams: 1 / Audio streams: 1 / Audio codec: aac / Audio sample rate: 32000 / Audio channels: 2 / Test passed`。
- `ast.parse` 语法通过（seq 159）。
- 端到端 FL2VA 推理复跑与画面观感（偏亮修复效果）未在本轨迹执行。

## 适用与失效边界

- `encode_video` 模式依赖 diffusers ≥ 该版本（0.40.0.dev0，本机 15.1.0 PyAV）；低版本 diffusers 无该函数时需退回 ffmpeg mux。
- 值域结论绑定 `MiniMaxH3ModularPipeline` 的 [0,1] 输出约定；若上游改为 [-1,1] 输出（部分视频模型如此），`clamp(-1,1)*127.5+127.5` 才是正确公式——移植时必须先核对 pipeline 输出值域再选转换式。
- 音画同步（帧率 vs 采样率时长对齐）未在本轨迹显式验证，仅由 encode_video 的单容器写入隐含。

## 附：断言存档

- cann-recipes-infer 版 MiniMax-H3 FL2VA 推理产物 mp4 无声的根因：infer_minimax_h3.py 的 save_output 用 imageio.get_writer(codec="libx264") 只写视频流、音频经 soundfile 单独写 .wav，从不合并；而 diffusers MiniMaxH3ModularPipeline 把 videos([1,F,C,H,W], 值域[0,1]) 与 audio([1,2,num_samples]) 作为独立输出返回，原始开源仓库不含保存逻辑，参考 API 脚本均从服务端下载单个含音频 mp4。修复：有音频时改用 diffusers.utils.encode_video（PyAV 后端，export_utils.py:303，Cosmos pipeline 同款模式）将帧+音频 mux 为单个 AAC 立体声 mp4，无音频保留 imageio 路径。本地 PyAV 容器级验证通过：合成 4 帧 + randn(2,32000) 双声道经 encode_video 后 av.open 检出 Video streams:1 / Audio streams:1 / codec:aac / 32000Hz / 2ch；端到端推理复跑未执行。

```text
            frames = (frames.clamp(-1, 1) * 127.5 + 127.5).byte().numpy()
            if frames.ndim == 3 and frames.shape[-1] == 1:
                frames = np.repeat(frames, 3, axis=-1)
        elif hasattr(frames, 'images'):
            frames = [np.array(img) for img in frames.images]
        writer = imageio.get_writer(output_path, fps=fps, codec="libx264",
                                    quality=8, macro_block_size=1)
```

```text
            frames = (frames.clamp(0, 1) * 255).round().to(torch.uint8)
        elif hasattr(frames, 'images'):
            frames = torch.from_numpy(
                np.stack([np.array(img) for img in frames.images])
            )

        if audio is not None:
            from diffusers.utils import encode_video

            audio_data = audio
            if isinstance(audio_data, torch.Tensor):
                audio_data = audio_data.cpu().float()
            if audio_data.ndim == 3:
                audio_data = audio_data[0]
            if audio_data.ndim == 1:
                audio_data = audio_data.reshape(1, -1).expand(2, -1)

            encode_video(
                frames,
                fps=fps,
                audio=audio_data,
                audio_sample_rate=sampling_rate,
                output_path=output_path,
            )
```

```text
Video streams: 1
Audio streams: 1
Audio codec: aac
Audio sample rate: 32000
Audio channels: 2
Test passed: mp4 contains both video and audio
```
