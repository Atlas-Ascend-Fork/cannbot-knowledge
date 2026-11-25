---
{
  "type": "Runbook",
  "title": "CANN 9.1.0-beta.1 SuperKernel 仍强制 >2 real stream 限制：combine_v2 融入 shared_expert_x 引入第三条流触发 E40021 编译失败",
  "description": "模型/任务：hy3_preview（295B MoE，80 层，1 shared expert + 192 routed experts top-8）ge_graph decode（batch=16，input 1024，max_new_tokens=64），16 die（A3，moe_ep=16，attn_tp=4/dp=4，dense_tp=4），BF16。",
  "tags": [
    "task.testing",
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

# CANN 9.1.0-beta.1 SuperKernel 仍强制 >2 real stream 限制：combine_v2 融入 shared_expert_x 引入第三条流触发 E40021 编译失败

## 适用场景

- 平台范围依据：source 0 seq 24、source 0 seq 163、source 0 seq 164的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 模型/任务：hy3_preview（295B MoE，80 层，1 shared expert + 192 routed experts top-8）ge_graph decode（batch=16，input 1024，max_new_tokens=64），16 die（A3，moe_ep=16，attn_tp=4/dp=4，dense_tp=4），BF16，enable_superkernel=true + force_eplb=true。
- 平台：CANN 9.1.0-beta.1（<internal_build_path>），torch_npu，SuperKernel（super kernel）decode 图。
- 变更：Plan-E 把 shared expert 输出以 `shared_expert_x` 传入 `torch_npu.npu_moe_distribute_combine_v2`（dispatch/combine 均 shared_expert_num=1），由 combine 内部完成 routed+shared 合并，消除 79 层/step 的 Python `routed_output + shared_output` 加法。

## 触发与观测

Run 1（superkernel ON + shared_expert_x ON）在 `Try to compile model` 后约 4 分钟确定性编译失败（source 0 seq 164，tool_observed）：

```
[2026-07-03 21:36:01.251][model_worker.py:321] Try to compile model
[2026-07-03 21:40:09] [ERROR] [ascend910_93] ERROR: super kernel do not support more than 2 real stream, use 'options="stream-fusion=1"' to enable operators fusion on multi-stream, oplist: [{'bin_path': '<internal_build_path>', ..., 'stream_id': 1, ...}, ...]
```

配套（seq 166 agent 汇报的编译错误链）：`Compilation_Error(E40021): Failed to compile Op HcomAllReduce_2 → MoeDistributeDispatchV2 → GroupedMatmul → SwiGlu_2 → GroupedMatmul_1 → MoeDistributeCombineV2 → InplaceAddRmsNorm_3 → HcomAllGather_2`。

## 探针与操作

1. 探针运行（seq 163-164）：`bash infer.sh`（YAML custom_params enable_superkernel: True + 默认 enable_shared_expert_x=True，profiler=True，force_eplb=True）→ E40021。
2. 对照设计（seq 174-181）：W1b-B = superkernel OFF + shared_expert_x ON（判定无 SuperKernel 时 Plan-E 可行性与 52.79 ms/t 基线对比）、W1b-C = superkernel OFF + 无 sx。W1b-B 于 21:43:53 启动（seq 190），轨迹在其完成前截断（seq 196），无结果。
3. 历史对照（progress_history，seq 31）：CANN 8.5.0 曾因同一限制回退 shared_expert_x（F-5/S-5）；本次证明 9.1.0-beta.1 行为一致。

## 机制与判别

- 机制：shared expert 经 dense_tp 切分，其 `HcomAllReduce` 位于 stream 1；把 shared 融入 combine_v2 后，该 AllReduce 被拉入以 `HcomAllGather`（stream 1）结尾、经 `InplaceAddRmsNorm` 的 routed 融合链，SuperKernel 图内 real stream 数 >2，触发编译期硬限制（报错信息同时提示可用 `options="stream-fusion=1"` 开启多流算子融合，未在本轨迹验证）。
- 判别：错误在编译期确定复现（同配置与 CANN 8.5.0 历史记录同签名）；单变量归因于 shared_expert_x×SuperKernel 组合（去掉其一的理论对照 W1b-B/C 已启动未完成）。
- 未定：SuperKernel OFF 下 shared_expert_x 的性能净收益（W1b-B 结果缺失）；`stream-fusion=1` 是否可解除该限制未测试。

## 验证信号

- 编译失败原文（tool_observed，seq 164）：`ERROR: super kernel do not support more than 2 real stream ... oplist: [... hccl_ar_superkernel_bfloat16.o ... stream_id: 1 ...]`。
- InferenceConfig 运行时逐字（seq 164）：`exe_mode='ge_graph', enable_superkernel: True, enable_multi_streams: False, batch_size=16, moe_ep_size=16, force_eplb=True`。
- 单次确定性编译失败 + 历史版本（8.5.0）同签名记录；非概率性错误。

## 适用与失效边界

- 适用：CANN 9.1.0-beta.1 + SuperKernel + MoE combine_v2 shared_expert_x 融合（dense_tp shared expert 场景）的组合可行性判定——当前版本组合不可用，选型须二选一。
- 失效/不覆盖：非 SuperKernel 路径的 shared_expert_x（W1b-B 未出结果）；`stream-fusion=1` 选项；后续 CANN 版本可能解除该限制，需按版本复测。
- 停止条件：遇同签名 E40021 时应先关 SuperKernel 或移除 shared_expert_x，再排查其他编译问题。

## 附：断言存档

- CANN 9.1.0-beta.1 SuperKernel 仍强制 >2 real stream 限制：hy3_preview ge_graph decode 将 shared expert 以 shared_expert_x 融入 npu_moe_distribute_combine_v2 后，Try to compile 约 4 分钟确定性报 super kernel do not support more than 2 real stream（Compilation_Error E40021，含 hccl_ar_superkernel_bfloat16.o stream_id 1 oplist），与 CANN 8.5.0 回退史同签名。

```text
ERROR: super kernel do not support more than 2 real stream
Compilation_Error(E40021): Failed to compile Op
  HcomAllReduce_2 → MoeDistributeDispatchV2 → GroupedMatmul → SwiGlu_2 →
  GroupedMatmul_1 → MoeDistributeCombineV2 → InplaceAddRmsNorm_3 → HcomAllGather_2
```
