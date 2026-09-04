---
type: Runbook
title: aclgraph 图捕获报 Alloc sq cq fail / 207005 / EL0006：档位过多耗尽每卡 SQ/CQ 流资源
description: '昇腾 NPU 以 aclgraph 图模式跑 Qwen3-MoE（tp/dp/ep）在图捕获阶段报 [SqCqManage]Alloc sq cq fail / AclmdlRICaptureBegin error code 207005 / EL0006 The resources are insufficient / Failed to apply for memory 的失败签名。报错栈落在 torch_npu 的 capture_begin → AclmdlRICaptureBegin / rtStreamBeginCapture。文案像 HBM 显存不足或抢卡，但 TraceBack 顶端真实失败点是 [SqCqManage]Alloc sq cq fail（对连续 stream_id 各申请 SQ/CQ 都失败），即流的 SQ/CQ（Submit Queue / Complete Queue）队列资源分配失败，非显存耗尽。根因：NPU 每卡 SQ/CQ 流资源有限预算，aclgraph 每个捕获档位（capture size / gear）× 每个通信进程组 × 层数都占用 stream 并各申请一对 SQ/CQ，档位越多、进程组越多、层数越大越易把 per-device SQ/CQ 申满；A3 比 A2 更易触发。修法：调小 vllm-ascend 的 cuda-capture-sizes（减少图捕获档位），用维护者经验公式估上限——A3: num_capture_sizes=(1920-pg_num*40)/(num_hidden_layer+1)/(1+pg_num*2)，A2: num_capture_sizes=1920/(num_hidden_layer+1)/(1+pg_num*1)，pg_num 为通信进程组数、num_hidden_layer 为隐藏层数。cuda-capture-sizes 与公式常数是 vllm-ascend 实现落点，但档位×进程组×层数占 stream 撞 SQ/CQ 预算的根因与减少档位的修法方向可迁移到任意 aclgraph 下 tp/dp/ep 图模式 MoE。关联 npu-graph-mode 与 atlas-a3 静态概念页。'
tags:
- task.debugging
- topic.graph_execution
- topic.memory
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/issues/2410
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:33:02Z'
platforms:
- a2
- a3
---

# aclgraph 图捕获报 Alloc sq cq fail / 207005 / EL0006：档位过多耗尽每卡 SQ/CQ 流资源

## 信号（现象）

启动即在 aclgraph 图捕获阶段抛错，报错栈落在 torch_npu 的 `capture_begin`：

```
File ".../torch_npu/npu/graphs.py", line 210, in capture_begin
  super().capture_begin(pool=pool, capture_error_mode=capture_error_mode)
RuntimeError: capture_begin:...:156 NPU function error:
  c10_npu::acl::AclmdlRICaptureBegin(capture_stream_, capture_mode), error code is 207005
[ERROR] ... ERR00100 PTA call acl api failed
[Error]: Failed to apply for memory.
        Check the remaining storage space in the hardware environment.
EL0006: ... The resources are insufficient.
        Solution: Close applications not in use.
        TraceBack (most recent call last):
        [SqCqManage]Alloc sq cq fail, stream_id=1984, retCode=0x7020023.[FUNC:AllocStreamSqCq][FILE:stream_sqcq_manage.cc][LINE:78]
        [SqCqManage]Alloc sq cq fail, stream_id=1984, retCode=0x7020023.[FUNC:Setup][FILE:stream.cc][LINE:655]
        rtStreamBeginCapture execute failed, reason=[driver error:resource alloc fail]...
        begin capture stream failed, runtime result = 207005...
        [SqCqManage]Alloc sq cq fail, stream_id=1985, ...
```

可逐项核对的关键点：错误码是 **207005**（`AclmdlRICaptureBegin` / `rtStreamBeginCapture` 失败）、`EL0006 The resources are insufficient`，TraceBack 顶端反复出现 **`[SqCqManage]Alloc sq cq fail`**（对多个连续 `stream_id` 各申请一次都失败）。

**错误文案易致误判**：`Failed to apply for memory` / `Check the remaining storage space` / `resources insufficient` 读起来像 HBM 显存不足或被其他进程抢占，但真实失败点是 TraceBack 最顶端的 `[SqCqManage]Alloc sq cq fail`——**流的 SQ/CQ（Submit Queue / Complete Queue）队列资源分配失败**，不是显存耗尽。据错误文案去释放显存或关闭其他进程，排查方向即偏离根因。

## 触发条件

- 图模式为 **aclgraph**（torch_npu 图捕获路径 `AclmdlRICaptureBegin`），而非 GE / torchair 静态图。
- 开启多路并行（如 tp/dp/ep），存在**多个通信进程组**（每组各自占用 stream）。
- 图捕获**档位数偏多**（vllm-ascend 的 `cuda-capture-sizes` 配了较多 gear）。
- 模型层数偏大（经验公式含 `num_hidden_layer` 项，隐含每层再乘一份占用；系由公式反推，非机制散文明证）。
- **昇腾 A3 更易触发**：同等层数 / 进程组下 A3 能容纳的档位数少于 A2（见下方公式）。

## 根因

NPU 每卡的 **SQ/CQ 流资源是有限预算**。aclgraph 捕获时，每个捕获档位（capture size / gear）× 每个通信进程组都要占用若干 stream，每条 stream 都要申请一对 SQ/CQ 队列。**档位越多、进程组越多，占用的 stream 越多**，越容易把 per-device SQ/CQ 预算申满；申满后下一个 `stream_id` 的 `AllocStreamSqCq` 返回失败，图捕获在 `capture_begin` 阶段整体报 207005。层数进入占用的机制系由下方经验公式（分母含 `num_hidden_layer`）反推，隐含每层再乘一份占用。

这是硬件固有的资源上界行为，与具体 rc 版本无关，可迁移到任意在 aclgraph 下跑 tp/dp/ep 图模式 MoE 的场景。

## 修法

调小图捕获档位数 —— vllm-ascend 里即减小 **`cuda-capture-sizes`**（配更少的 gear）。

估算「本平台 / 本模型能支持的最大档位数」的经验公式（`pg_num`=通信进程组数，`num_hidden_layer`=模型隐藏层数）：

```python
# pg_num: the number of process groups for communication
# num_hidden_layer: number of hidden layers of the model
num_capture_sizes = (1920 - pg_num * 40) / (num_hidden_layer + 1) / (1 + pg_num * 2)  # for A3
num_capture_sizes = (1920)              / (num_hidden_layer + 1) / (1 + pg_num * 1)  # for A2
```

用法：给定层数与进程组数，先用**对应平台**公式算出可支持的 `num_capture_sizes` 上限，再把 `cuda-capture-sizes` 配到该上限以内。A3 分母含额外的 `pg_num*40` 折扣与 `(1 + pg_num*2)` 因子，故同等层数 / 进程组下 **A3 容纳的档位数少于 A2**，与「A3 更易触发」一致。

除减少档位外，等价方向还有减少通信进程组数（公式分子含 `pg_num` 折扣，直接支撑）；理论上换用不逐档位占 stream 的图后端也可规避，但 source 未验证该路径。直接、可行动的抓手是把 `cuda-capture-sizes` 收敛到公式上限内。

## 参考实现及其约束

- 参考实现：vllm-ascend 的 aclgraph 图模式路径 + `cuda-capture-sizes` 参数（v0.9.1rc3 时期反馈），workload 为 Qwen3-MoE（tp/dp/ep）。`cuda-capture-sizes` 是 vllm-ascend 的开关名，具体参数名是该实现的落点。
- 上面的 A3/A2 经验公式（含 `1920` 常数、`pg_num*40` 折扣）是**该实现在 vllm-ascend 场景下给出的估算式**，不是 SQ/CQ 上界的通用理论表达；换框架 / 换 torch_npu 版本时公式常数可能变，但「档位 × 进程组 × 层数 三重占用 stream → 撞 per-card SQ/CQ 预算」这一根因与「aclgraph 下减少捕获档位」的修法方向可迁移。
- 静态概念背景：aclgraph 属于 [npu-graph-mode](../../concepts/techniques/npu_graph_mode.md) 图捕获路径的一种；平台差异细节见 [atlas-a3](../../concepts/platforms/atlas_a3.md)。

## 相关经验

- aclgraph 捕获的其他失败 / 守卫问题另见 [图模式多流跨流同步的失败签名](../runtime/graph_mode_multi_stream_sync_failures.md)。
- 图模式档位 / 输入签名与重复编译相关问题见 [graph-mode-stable-input-signature-recompile](../performance/graph_mode_stable_input_signature_recompile.md)。

## Evidence

- 来源为 vllm-ascend 该 FAQ 反馈帖，维护者（gh association=collaborator）给出根因（SQ/CQ 流资源耗尽，非显存）、修法（调小 `cuda-capture-sizes`）与 A3/A2 经验公式；报错栈顶端 `[SqCqManage]Alloc sq cq fail` 对应根因。issue 无 diff，据实层级为「维护者确认」。溯源下探 [vllm-ascend-issue-2410-v0-9-1rc3-faq-feedback](https://github.com/vllm-project/vllm-ascend/issues/2410)
- 源未给具体 before→after 数值，给出的是可行动修法（调小档位）与估档位上限的经验公式。

<!-- cannbot:related:start -->
## 相关

- [稳定图模式输入张量签名（shape/stride/dtype）避免 dynamo 重编译与缓存 miss](../performance/graph_mode_stable_input_signature_recompile.md)（`related`）：图模式档位 / 输入签名与重复编译相关问题见 ［graph-mode-stable-input-signature-recompile］(../performance/graph_mode_stable_input_signature_recompile.md)。；图模式按输入张量的 **shape + dtype + stride 签名** 缓存/守卫（guard）已编译图；decode 每步输入的 shape/dtype/stride 只要有一维不稳，dynamo 就把它当新形态触发重编译或 guard 失效。三类常见漂移：；排查 SQ/CQ 耗尽时，还需核对输入签名漂移是否触发重复编译。
<!-- cannbot:related:end -->
