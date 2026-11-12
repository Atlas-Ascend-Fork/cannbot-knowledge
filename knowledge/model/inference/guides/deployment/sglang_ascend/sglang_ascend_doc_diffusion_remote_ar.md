---
type: Guide
title: SGLang Diffusion GLM-Image远程AR：HCCL端口与调用成本
description: 说明SRT按完整AR生成发送HTTP、启动连接检查、A3共卡双服务端口隔离及T2I能力边界。
tags:
- task.implementation
- topic.diffusion
- topic.multimodal
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/docs/docs/sglang-diffusion/models_with_ar.mdx
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/runtime/pipelines_core/stages/model_specific_stages/glm_image.py
  role: implementation
created_at: '2026-11-08T12:33:44Z'
updated_at: '2026-11-09T04:31:21Z'
platforms:
- a3
---

# SGLang Diffusion GLM-Image远程AR：HCCL端口与调用成本

## 选择本地或远程AR

GLM-Image默认bundled Transformers支持T2I/I2I/V2I；外部SRT AR当前只支持T2I。Qwen Image Layered与LongCat使用进程内native Qwen2.5-VL，是不同路径。文档把 --srt-encoder-url 外部模式描述为每个 AR step 一次 HTTP；同提交 GLM-Image 实现却把完整 max_new_tokens 放入一次 /generate 请求，批量路径同样一次提交整批并取回完整 output_ids。因此 HTTP 调用粒度应按一次完整 AR 生成或批量生成核对，不能据文档逐 token 往返推导网络成本。来源仍建议同机或低延迟局域网，并按负载提高 encoder-timeout 和 connection-timeout；启动会检查远端连接，离线即停止。

## A3共享设备的隔离

来源A3示例为2物理卡/4设备，两服务分别设置HCCL_IF_BASE_PORT、HCCL_HOST_SOCKET_PORT_RANGE和HCCL_NPU_SOCKET_PORT_RANGE：一组23000段、另一组24000段，不能只改HTTP端口而保留冲突的HCCL范围。AR用TP4、mem-fraction0.4、decode graph bs1；Diffusion为num-gpus4/SP4，另开Cache-DiT及request warmup。两者共用设备需合计权重/激活与通信buffer容量。

## 证据与验收

示例输出33.82秒排除warmup，仅为1920×1088、50步和指定缓存配置的来源单次记录，不能外推为无缓存或所有GLM请求。先验证AR URL、模型/processor对应、HCCL端口无冲突，再对照本地后端验证T2I输出和超时；记录AR往返与DiT/VAE分别耗时。本次未启动服务或测量。

## 配套知识

[GLM NPU多输出实现](../../integration/sglang_ascend/sglang_ascend_diffusion_glm_multioutput.md)；[GLM分离拓扑](sglang_ascend_doc_diffusion_disaggregation.md)。
