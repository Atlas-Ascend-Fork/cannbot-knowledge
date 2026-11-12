---
type: Optimization
title: SGLang 昇腾 VLM 预处理的八维 reshape 与调度争用
description: 说明 Qwen、GLM4.6V、MiniMax M3 图像/视频 patch 抽取、Transformers 补丁和 fast processor
  设备选择。
tags:
- task.optimization
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/modules/qwen_vl_processor.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/modules/glm46v_processor.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/modules/minimax_m3_processor.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/multimodal/processors/base_processor.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/multimodal/processors/ernie45_vl.py
  role: supporting
created_at: '2026-11-08T12:20:03Z'
updated_at: '2026-11-08T12:20:03Z'
platforms: []
---

# SGLang 昇腾 VLM 预处理的八维 reshape 与调度争用

## 场景与 patch 排列

部分 Transformers VLM patch extraction 会创建十维中间张量，超过此 NPU 适配所针对的八维限制。共同的 transform_patches_to_flatten 将时间并入 batch，先 reshape/permute 为最多八维，再恢复 `[B,grid_t*grid_h*grid_w,patch_features]`，保持 temporal/channel/spatial merge 的逻辑顺序。

图像和视频先按 shape 分组 resize，再重排回原顺序并 rescale/normalize；resize factor=patch_size*merge_size，需核对 temporal padding 和 grid_thw 与真实 patch 数一致。Qwen 使用显式尺寸调用 TorchvisionBackend.resize，规避不同 Transformers 版本的 Qwen resize override 差异；Qwen 视频尾帧按 `-T%temporal_patch_size` 补齐。MiniMax 另限制最大长宽比 200，使用其 min/max pixels；不能把默认 temporal 参数下的 padding 公式任意推广。

## 安装点与设备边界

base processor 对 MiniMaxVLProcessor 给实际 image/video processor 类型打幂等 patch；Glm46VProcessor 安装专门 wrapper；其他路径安装 Qwen wrapper。Glm4vProcessor 保留未设置设备的特例。fast preprocessing 在 NPU 上被视为与 scheduler 争用同一加速器，增加 worker 不等于 CPU 预处理并行收益。ERNIE45 不在 NPU 强塞 device=cuda，并在关闭 CUDA IPC 时把 feature tensors 移回 CPU。

验证多图/视频顺序、不同分辨率、尾帧、grid 数和 patch byte order，与未受维数限制的 reference 比较。代价包含 grouping、reorder 和设备争用；关闭 fast processor/重建 processor 可回退，不能仅移除 reshape 保留错误排列。本次未执行 Transformers 或测量加速。
