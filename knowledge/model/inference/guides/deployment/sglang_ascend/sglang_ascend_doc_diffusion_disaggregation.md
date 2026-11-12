---
type: Guide
title: SGLang Diffusion昇腾分离部署：传输构建与GLM token派发
description: 区分Mooncake Ascend Direct环境和GLM-Image不搬latent的14去噪worker拓扑，保留不同数据面的边界。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/hardware-platforms/ascend-npus/diffusion/disaggregation.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/sglang-diffusion/disaggregation.mdx
  role: constraint
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/disaggregation/orchestrator.py
  role: implementation
created_at: '2026-11-08T12:33:45Z'
updated_at: '2026-11-09T04:30:20Z'
platforms: []
---

# SGLang Diffusion昇腾分离部署：传输构建与GLM token派发

## 先分清数据面

Ascend专页要求先完成NPU安装，再按Mooncake v0.3.10.post2构建并启用USE_ASCEND_DIRECT，安装wheel并使.so目录可被动态加载器找到。页面给出的Python3.11.14 site-packages只是该环境示例，不能覆盖新版安装的Python版本或直接复制到其他环境。本次没有执行依赖安装、cmake或编译。

通用disaggregation还包含GLM-Image特殊模式，仅接受单个字符串文本 prompt 的 T2I 请求，`image_path` 必须为 None；单请求传多个 prompt 或图像输入会被拒绝。head批量执行AR，把prior tokens派发给denoiser；每个worker本地执行prompt/glyph、DiT和VAE，不传latent/embedding。它不同于通用encoder→denoiser→decoder张量传输，不能用一个拓扑的通信收益证明另一条。

## 来源GLM拓扑

16可见设备中0–1给外部AR TP2，2–15是14个独立batch1、单设备Cache-DiT denoiser，关闭DiT offload并选FA。每worker scheduler/master端口独立；head只配置denoiser-urls与SRT URL，故意省encoder/decoder URLs，dynamic batching上限28。任一worker退出时示例脚本清理同组worker，不能只保留失联的URL继续验收。

确认worker端点可达、实际AR/denoiser设备与端口不冲突，再用单文本、无图像输入的请求验证token派发与结果归属，逐步提高跨请求动态合批；动态合批不代表单请求可以传多个 prompt。通用页的H200同机RDMA像素一致测试不属于Ascend证据；本次没有跨进程、跨机或性能测量，芯片范围未知。
