---
type: Guide
title: SGLang Ascend NPUGraph：捕获、长度重绑定与重放栅栏
description: 闭合按shape捕获的NPUGraph、共享pool、FIA主机长度更新和DFlash实时缓冲刷新，精确保留异步update/replay顺序。
tags:
- task.implementation
- topic.graph_execution
- topic.attention
- topic.speculative_decoding
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/graph_runner/npu_cudagraph_backend.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_dsv4_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_executor/input_buffers.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_executor/model_runner_components/cuda_graph_setup.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_executor/runner/prefill_cuda_graph_runner.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_executor/runner_backend/utils.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/model_executor/runner_utils/pool.py
  role: implementation
created_at: '2026-11-08T12:08:01Z'
updated_at: '2026-11-08T12:10:40Z'
platforms: []
aliases:
- NPUCudaGraphBackend
- NPUGraph.update
- ACLGraph
---

# SGLang Ascend NPUGraph：捕获、长度重绑定与重放栅栏

## 捕获与持有对象

`NPUCudaGraphBackend`每个ShapeKey保存一张torch.npu.NPUGraph和输出，复用graph pool；cache loc采用int32。capture可先torch.compile(fullgraph=True,dynamic=False,npugraph_ex)，两次warmup各有device同步和TP barrier，再执行post-warmup状态reset hook，避免warmup改变状态池后进入正式捕获。实际graph使用auto_dispatch_capture=True，可接memory saver adapter；supports_shared_read_events=False，不能继承CUDA共享读事件假设。

## 主机长度ABI

FIA不同变体的长度属性不同：ModelSlim/特定V2和多层draft extend使用actual_seq_kvlen；普通Eagle draft/extend使用actual_seq_lengths_kv；dense MLA DCP必须使用rank-local Host界限。属性名选择随runner和模型而变，不能统一字符串替换。

decode尽量用live CPU镜像并补padding0。DFlash优先采用forward_metadata已计算的列表；DFlash/DSpark镜像已包含verify块，不能再加captured_req_width。没有镜像会回到device.cpu()，不保证无D2H。Eagle draft为每个step构造一份字典，长度live+step+1；多层draft runner优先于普通decode类判断，缺实时CPU镜像时明确报错。

## 更新与重放顺序

单线程executor绑定正确NPU device，避免每轮新建线程。下一次rebind先synchronize上一轮fence，随后submit graph.update，在主线程调用graph.replay，再future.result，最后记录新fence。虽然docstring描述update须在设备消费前完成，源码并非先future.result再replay；本卡保留实际主机调用顺序，不把它改写成已串行等待的实现。

对不需host FIA更新的DSA/V4路线，可由attention元数据直接原地刷新；普通模型与spec runner按对应payload重绑定。cleanup先shutdown worker、等待fence，再释放graph/output/pool，不能在worker仍访问graph时清映射。

## DFlash批次刷新与验证

普通预计划路径主要copy input_ids、positions和mrope；DFlash单独重算raw batch、bucket与bs*width token数，刷新DP token buffer、num_token_non_padded、embeds、seq lens/CPU镜像、request slots及out_cache_loc，并清padding尾部后重新init元数据。否则相同shape下请求换号仍可能重放旧缓存地址。

建议测试同shape换请求、长度增长/缩短、bucket变化、多step draft、空DP rank和关闭图基线；同时观察Host fence等待、worker异常与device输出。graph减少发射开销但增加捕获显存、同步和更新工作；本次未执行捕获或性能测试，平台列表不从“NPU图”泛化。

## 调用依赖补充

decode backend resolver对device=npu明确返回NPUCudaGraphBackend，不能因用户配置了其他模式就推断有NPU breakable decode实现；prefill resolver是独立流程。通用prefill runner的cache loc在NPU使用int32，且当存在不能容忍idle的collective时，任意DP rank无token会回到eager；其captured attention metadata协议只对Breakable backend启用，不能从V4 decode图推导prefill全部复用。

ForwardInputBuffers.share_buffers在NPU因精度问题直接返回，跨runner的自动input buffer合并未启用；这与同一个NPU图runner内复用自己持久缓冲、或共享graph memory pool是三件不同的事。index-semantic字段如positions、mrope_positions、out_cache_loc、request和Mamba索引提供显式reset，stale内容不能视为无害padding。全局graph capture stream helper声明CUDA-only，NPU/XPU/CPU runner保留自身stream。setup中的“NPU graph”日志是捕获阶段标识，不证明已覆盖每个graph backend或已量得性能。
