---
type: Guide
title: vLLM Ascend CPU 权重卸载：NZ 缓冲重绑定与图捕获限制
description: 区分 CPU 参数卸载和 MoE 设备内预取，核对 prefetch 工厂、NZ 检测时机、共享 buffer 键冲突、重绑定和 eager 回退。
aliases:
- AscendPrefetchOffloader
- mark_prefetch_offload_nz_weight
- _format_static_buffers_for_nz
tags:
- task.implementation
- task.debugging
- topic.data_movement
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_executor/offloader/base.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_executor/offloader/prefetch.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/model_executor/offloader/__init__.py
  role: implementation
created_at: '2026-11-03T04:57:14Z'
updated_at: '2026-11-03T04:57:14Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend CPU 权重卸载：NZ 缓冲重绑定与图捕获限制

## 入口与适用边界

固定 Main ceac1a2 的 offloader 包三个文件提供框架合同；未运行 CPU/NPU 传输、量化或图捕获。工厂仅在 offload_backend 精确等于 prefetch 时构造 AscendPrefetchOffloader，并传入 group_size、num_in_group、prefetch_step、offload_params，mode 固定 cpu；无配置或其他 backend 返回 NoopOffloader。新增 backend 名称不会自动启用卸载。包 __all__ 只导出工厂与该类。

这条路径把 CPU 参数按层预取到静态设备缓冲，与[MoE 权重预取案例](../../optimizations/cases/vllm_moe_weight_prefetch_token_gate.md)的设备内权重提示、token 门限及比例不同，不能交叉套用默认值或收益。本卡只说明 Ascend 扩展；Native PrefetchOffloader 的完整调度和内存预算不由这三个文件证明。

## NZ 标记与静态 buffer 身份

参数仅在设备类型为 npu 且 get_npu_format 返回 FRACTAL_NZ 时被识别，查询异常返回 False。模块在 quant_method.process_weights_after_loading 完成后扫描参数并打标，且同一 quant_method 对象仅包装一次；量化/格式转换尚未执行时提前判断 CPU storage 的格式会丢失信息。ParamInfo 扩展 use_nz_buffer，键仍由 name、shape、stride、dtype 等继承信息确定。

同一静态 buffer key 同时要求 NZ 和非 NZ 会抛 ValueError，不能让后一个参数静默覆盖布局。npu_format_cast 返回新 tensor，因此仅替换 pool 的 buffers 不足以修复已经绑定的参数；实现进一步按 slot 找新缓冲，重设 _gpu_buffer 与 param.data，然后重新发起前 min(prefetch_step,模块数) 个 onload。若只检查 pool 中的格式却没有核对参数实际地址，NZ-only GMM 仍可能读取旧 ND 存储。

## 捕获门禁与初始化顺序

post_init 先执行 Native 初始化、收集全部 ParamInfo；没有实际 offload 模块即返回。若存在 NZ 参数且 enforce_eager 为假，直接抛 RuntimeError：此固定栈的 ND pinned CPU→NZ copy 需要 aclop 转换，不能在 ACL graph capture 中执行。源码给出的回退是 enforce_eager=True 或 additional_config 的 weight_nz_mode=0，仍需确认该模型支持相应非 NZ 路径。

该门禁由配置决定，不探测未来 CANN/torch_npu 是否已经增加支持；不能把固定版本错误说明扩展为永久硬件限制，也不能承诺任意版本关闭 NZ 都数值等价。首次 onload 顺序必须在重绑定后，避免初始化期间填充旧缓冲。

## 全局替换、异常与 Agent 验收

wrap_modules 暂时替换 Native 模块的 _ModuleOffloader 类，调用父实现后在 finally 恢复；单次异常会恢复符号，但源码没有对并发构造提供锁。不要据此声称多模型并行初始化安全。参数标记、quant_method 包装和 pool 复用均需遵守模型生命周期。

适配验收至少分别检查 Noop/真实 prefetch、NZ/ND 同键冲突、量化后标记、param.data 与 pool 同一 slot 的地址/格式、首批预取、跨层复用、eager 数值与峰值内存。测量加载时间、传输重叠和推理时延时固定工作负载；静态 buffer 存在不证明搬运已经重叠或性能有收益。
