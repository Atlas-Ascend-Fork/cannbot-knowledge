---
{
  "type": "Runbook",
  "title": "MoE 推理 prefill 阶段 EP all-to-all 通信暴露与约 45% 层内同步气泡的诊断（Hy3-preview, 16-die Atlas A3, bf16, ge_graph）",
  "description": "模型：Hy3-preview（Tencent Hy，295B MoE Transformer，Dense L0 + 79 层 Sparse MoE with Shared Expert，GQA），bf16 非量化。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---

# MoE 推理 prefill 阶段 EP all-to-all 通信暴露与约 45% 层内同步气泡的诊断（Hy3-preview, 16-die Atlas A3, bf16, ge_graph）

## 适用场景

- 平台范围依据：source 0 seq 1、source 0 seq 19、source 0 seq 27的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 模型：Hy3-preview（Tencent Hy，295B MoE Transformer，Dense L0 + 79 层 Sparse MoE with Shared Expert，GQA），bf16 非量化。
- 部署：16 die Atlas A3（910C，单 die 64GB），ge_graph 执行（MC2 dispatch/combine + GMM + SuperKernel），EP 并行下每 rank 12 专家。
- 工作负载：prefill 2048 输入 token × batch 4（8192 token），框架内置 profiler 采集 rank0 kernel_details.csv（Level1+PipeUtilization，47 列）。
- 目标：定位 prefill 单步时间结构，判断通信/计算/气泡占比。轨迹内为纯 CPU 解析，未执行新卡上运行。

## 触发与观测

触发：SOTA-approach round0 baseline 剖析，prefill 单步（Step Id 0，5358 kept ops）eager 执行，计算集中单流 s46，通信算子（hcom_*）在 N/A 流。

逐字观测（source 0 seq 74，工具统计输出）：

```text
=== comm ops (count, sum_us) ===
  158    100900.0us  hcom_alltoallv_
   79     64603.7us  hcom_alltoall_
   82     16374.9us  hcom_allReduce_
   80      8333.0us  hcom_reduceScatter_
   81      3755.7us  hcom_allGather_

PREFILL step window = 507.7ms
s46 compute busy = 74.6ms
comm (N/A) busy = 194.0ms
```

组件归并（source 0 seq 98）：MoE 226.3ms（84.3% step_wall 268.6ms）、GQA 25.6ms（9.5%）；其中 EP a2a（alltoallv 100.9 + alltoall meta 64.6）= 165.5ms = 61.6% step_wall。通信忙时 194.0ms 约为计算忙时 74.6ms 的 2.6 倍。

## 探针与操作

逐 MoE 层重叠/气泡探针（source 0 seq 106 执行）：以每层 MoeGatingTopK 为层锚点（79 个，取相邻 78 区间），统计层 span、层内通信（N/A 流）与层内计算（s46）时长中位数。

逐字输出（source 0 seq 107）：

```text
MoE layer (n=78):
  median span        = 5827.5us
  median comm-in-layer= 2285.5us
  median comp-in-layer= 934.9us
  comm/span ratio     = 39%
  comp/span ratio     = 16%
  sum(comm+comp)/span = 55% (>100% => overlap; <100 => bubble)
  total 78 MoE layer span = 460.2ms
```

## 机制与判别

- 主结论：prefill 首要瓶颈是 EP all-to-all 通信暴露 + 同步气泡，而非算子计算（通信 61.6% step_wall vs 计算 27.8%）。
- 逐层 sum(comm+comp)/span = 55% < 100%，层内通信与计算未重叠，45% 为等待/同步气泡；Agent 归因于数据依赖串行链：alltoall_meta（hcom_alltoall_）强制同步 → dispatch alltoallv → GMM（source 0 seq 108，agent_narrative，未单独实验隔离）。
- 可区分解释：并非计算受限（s46 busy 仅 74.6ms）也不是全步纯串行（>1ms 大间隙仅 28.3ms，多为头尾 warmup，source 0 seq 104）——气泡分散在各层的路由/分发/计算/合并同步点。
- 测量陷阱：对 N/A 流与计算流做时间轴 union 曾得出 overlap=0.0ms（source 0 seq 101）；随后发现通信 collective summary 时间戳可能与计算流不同时间线，该绝对零重叠不可靠（source 0 seq 105，agent 推断），应以逐层比例法为准。

## 验证信号

- tool_observed（rank0 kernel_details.csv 单步统计，本轨迹单次观测）：通信/计算忙时、逐层 span/comm/comp 中位数、组件归并比如上；均为该 workload 单次 profiling，无 baseline/candidate 对照，不构成通用加速结论。
- 优化方向（micro-batch 流水线隐藏通信、减少同步 barrier）为基于该结构的建议，轨迹内未实施验证。

## 适用与失效边界

- 仅覆盖 Hy3-preview 295B bf16、16-die A3、ge_graph、EP（12 expert/rank）、2048×batch4 prefill 的单步 rank0 视角；其他 batch/seq、TP/EP 配比、量化形态需重测。
- 逐层锚点法依赖 MoeGatingTopK 每层一次的算子签名；换执行模式（如 decode 的 SuperKernel 聚合）后签名不同。
- union-overlap 零重叠结论在本数据上不可信（时间戳时间线疑义），复现者应使用逐层比例法并核对 collective summary 时间戳。
- 45% 气泡的同步链归因是未验证推断；验证需在拆分 alltoall_meta 或开启 comm/compute 重叠后复测。

## 附：断言存档

- Hy3-preview（295B MoE，bf16，16-die Atlas A3，ge_graph+MC2+GMM，2048 tok × batch4）prefill 单步中 MoE 模块占 step_wall 268.6ms 的 84.3%，其中 EP all-to-all 通信（hcom_alltoallv_ 158 次 100.9ms + hcom_alltoall_ 79 次 64.6ms）合计 165.5ms（61.6% step_wall），而计算流 s46 busy 仅 74.6ms；通信是 prefill 首要瓶颈，不是算子计算。
