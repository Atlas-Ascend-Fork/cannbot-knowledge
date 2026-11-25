---
{
  "type": "Runbook",
  "title": "64GB Atlas NPU 上 sr 双模型加载 OOM 与 CPU offload 两条路径的行为差异",
  "description": "daVinci-MagiHuman sr_540p/sr_1080p 超分辨率模式在 Atlas 910 单卡（npu-smi 显示 HBM 65536MB，运行时可用约 61.27GiB）上的部署：需同时驻留 base 模型与 SR 模型",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-20T14:17:05Z",
  "platforms": []
}
---

# 64GB Atlas NPU 上 sr 双模型加载 OOM 与 CPU offload 两条路径的行为差异

## 适用场景

daVinci-MagiHuman sr_540p/sr_1080p 超分辨率模式在 Atlas 910 单卡（npu-smi 显示 HBM 65536MB，运行时可用约 61.27GiB）上的部署：需同时驻留 base 模型与 SR 模型（各约 28.54GB，日志 `Load model successfully ... memory allocated: 28.54 GB`，source 0 seq 673）加 VAE 等组件。

## 触发与观测

- 触发：不开 offload 直接运行 sr_540p：`NPU out of memory. Tried to allocate 268.00 MiB / NPU 0; 61.27 GiB total capacity; 8.32 GiB already allocated`（source 0 seq 444 OOM 错误、seq 648 摘引，tool_observed）。
- 观测：`export CPU_OFFLOAD=true` 后同一脚本可完整运行（source 0 seq 487-490，tool_observed）。
- 自动阈值：代码仅在 `get_arch_memory() <= 48` 时自动启用部分 CPU 侧放置（VAE、文本编码器等），64GB 设备不自动，模型级 offload 依赖 `CPU_OFFLOAD` 环境变量（`inference/pipeline/video_generate.py` 行 179 `if env_is_true("CPU_OFFLOAD")`、行 216/221/235，source 0 seq 478 grep、seq 476 分析，tool_observed+源码读取）。
- Python 侧 CPUOffloadWrapper 路径下单次观测到设备不一致崩溃：`File "inference/model/dit/dit_module.py", line 246, in forward / proj = coords_xyz.unsqueeze(-1) * scales.unsqueeze(-1) * self.bands / RuntimeError: Expected all tensors to be on the same device. Expected NPU tensor, please check whether the input tensor device is correct.`（source 0 seq 678，tool_observed，伴随 ERR01002）。
- 对比公平性：sr_540p/sr_1080p 的 baseline 脚本本身已启用 offload（run_T2V.sh 定义 `export CPU_OFFLOAD=true` 与 `MAGI_COMPILER_OFFLOAD_ARGS`，source 0 seq 938 用户纠正、seq 949-950 读脚本确认）。sr_540p 强制 offload 运行相对其 baseline 的耗时差（139.276s vs 115.854s，+20.2%）在两侧 offload 配置确认一致后仍存在，但该次运行缓存激活状态未确认，归因未定（source 0 seq 496/958）。

## 探针与操作

- 内存探针：`npu-smi info`（本机返回 `3127 / 65536` HBM-Usage，source 0 seq 480）。
- offload 开关：运行脚本中 `export CPU_OFFLOAD="true"`（source 0 seq 488 编辑应用）。
- 残留进程清理后重跑可排除「上一进程占用导致 OOM」分支（source 0 seq 648 提到 8.32 GiB already allocated 的占用背景）。

## 机制与判别

- OOM 根因：双模型权重 + VAE 峰值超过单卡可用 HBM；阈值分支 `get_arch_memory() <= 48` 使 64GB 设备默认不启用自动 offload，与直觉（大内存更安全）相反的配置缺口在「双模型同驻」场景暴露。
- 设备不一致分支：CPUOffloadWrapper 将模型迁回 CPU 后，forward 中非参数张量（如 `self.bands`/coords 相关缓存张量）未随之迁至 NPU，触发混合设备乘法。该观测出现于 agent 自建脚本（含 FBCache 配置变更）的一次运行；baseline 脚本同 offload 环境可正常完成，具体触发差异未定位（unknown）。
- 未验证推断：`MAGI_COMPILER_OFFLOAD_ARGS`（编译器侧 offload 参数）与 `CPU_OFFLOAD`（Python 包装器）两条路径的性能与兼容性差异未做对照实验。

## 验证信号

- OOM 与 offload 后可运行：同一脚本两次运行对照（source 0 seq 444 vs seq 490，tool_observed）。
- 自动阈值与开关代码：源码 grep 证据（source 0 seq 478，static/source_read）。
- 设备不一致错误：单次观测（source 0 seq 678，tool_observed）。

## 适用与失效边界

适用于本仓库 CPUOffloadWrapper/get_arch_memory 结构与 64GB Ascend 910 单卡双模型场景。内存更充裕（如多卡 cp_size>1 或更大 HBM）时 OOM 分支不触发。做 sr 模式性能对比时必须先核对两侧脚本的 offload 配置（baseline 脚本默认已开），否则会把 offload 差异误读为优化收益/回退。CPUOffloadWrapper 路径遇混合设备 RuntimeError 时，回退方案是使用 baseline 脚本原生的 MAGI_COMPILER_OFFLOAD_ARGS 路径（本轨迹未对照验证）。

## 附：断言存档

- 64GB Ascend 910 单卡同时驻留 base+SR 双模型（各 28.54GB）加 VAE 超出可用 HBM（61.27GiB），sr_540p 不开 offload 运行报 NPU out of memory；export CPU_OFFLOAD=true 后同一脚本可完整运行。自动 CPU 侧放置仅在 get_arch_memory() <= 48 时启用，64GB 设备默认不自动开启模型级 offload（video_generate.py 行 179 env_is_true("CPU_OFFLOAD")、行 216/221/235 阈值分支）。

```text
Line 179:             if env_is_true("CPU_OFFLOAD"):
```
