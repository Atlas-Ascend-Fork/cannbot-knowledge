---
type: Guide
title: SGLang Ascend分段图：静态shape捕获与弱引用输出
description: 说明piecewise NPU backend如何按符号维选择捕获shape、回退通用compiled graph、保持输入地址与输出生命周期。
tags:
- task.implementation
- topic.graph_execution
- topic.compilation
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/compilation/npu_piecewise_backend.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/compilation/backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_executor/runner_backend_utils/weak_ref_tensor.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_executor/runner_backend_utils/breakable_cuda_graph/breakable_cuda_graph.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/test/manual/ascend/test_npu_piecewise_graph_prefill.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_executor/cuda_graph_config.py
  role: implementation
created_at: '2026-11-08T12:08:01Z'
updated_at: '2026-11-09T04:32:21Z'
platforms: []
aliases:
- NPUPiecewiseBackend
- weak_ref_tensors
---

# SGLang Ascend分段图：静态shape捕获与弱引用输出

## Shape路由

本页仅说明固定快照保留源码的静态机制；当前 CLI 解析器明确拒绝已移除的 tc_piecewise，NPU prefill 支持表仅列 disabled，不能将本页当作可直接启用的部署流程。

NPUPiecewiseBackend继承共享piecewise流程，以首个符号输入的选定维解析runtime_shape。未配置捕获的shape直接运行general compiled graph；选中的静态shape先warmup一次，再用NPUGraph和共享pool捕获。不能把“启用piecewise”解释为每种动态batch都已捕获。

编译管理层按current_platform选择NPU backend；eager/inductor是此处接受的compiler选项。源码对磁盘缓存加载仍有TODO，不能宣称本版本已实现从持久cache恢复全部图。

## 捕获生命周期

第一段承担GC，后续段捕获临时将gc.collect和torch.npu.empty_cache替为no-op，以避免反复回收影响共享pool。最后一段保存weak ref输出，entry缓存也转weak_ref_tensors；非末段首次 capture 返回原始 output；末段在捕获中先转换为 weak_ref_tensors，首次返回的也是弱引用，不能据首次返回值推断拥有存储。后续 replay 返回 entry.output 的弱引用结构。

debug模式记录捕获前tensor data_ptr，并在replay断言地址一致。输入shape相等但重新绑定到另一存储仍可能违反捕获契约，应copy_持久输入而非随意换tensor。

## 验证与回退

先列出实际捕获shape，再检查段间input/output所有权与地址稳定性。覆盖未捕获shape通用回退、warmup→capture→多次replay以及上层保留输出后的生命周期；必要时启用指针断言。分段图增加各shape捕获时间和pool占用，未命中shape仍付compiled执行成本。本次未执行编译/捕获；具体硬件兼容与收益未确认。

## 调用依赖补充

NPU weak_ref_tensors来自torch_npu._C._weak_ref_tensor，包装只接受单tensor、list或tuple，其他类型抛ValueError。共享breakable工具对CPU tensor保留身份，空加速器tensor只保留同shape/stride元数据，非空tensor才转弱引用；这一辅助函数可在NPU导入，不代表整套torch.cuda.CUDAGraph分段实现已在NPU接通。分段pool use-count的CUDA论证不能直接替代NPU piecewise的运行生命周期验证。

## 补充调用与验证边界

manual定义Qwen2.5-7B、ascend attention和tc_piecewise prefill图，捕获token档位为range(128,4096,128)，实际最大3968；GSM8K问题1319、门槛0.84。另一个bench_one_batch测试断言prefill latency<0.045秒。该 manual 使用的 tc_piecewise 配置会被当前解析器拒绝；上述仅是保留测试的配置和判定阈值，本次未执行，不能写成该硬件已达到的结果。
