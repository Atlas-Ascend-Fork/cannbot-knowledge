---
{
  "type": "Runbook",
  "title": "TND 布局 FA v2 host list `actual_seq_lengths_list_q` 在 batch>1 必须为 cumulative",
  "description": "npugraph_ex 适配中为 FA v2 新增 host list 长度字段后，batch>1（packed decode，eager 回退路径）传 `actual_seq_lengths_list_q=[1]*B` 会触发 FA tiling 校验失败：`The last element(1) of actualSeqLengthsQ is not equal to the T(3) of query`（actual_seq_len_checker.cpp:275）并伴随大块显存分配失败。TND 布局要求该 list 为 cumulative 且末元素等于 query 的 T，正确写法是 `list(range(1, batch_size + 1))`；修复后 batch=1 图 + batch=3 packed eager 逐请求 token 一致，multibatch 校验 PASS。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-03T12:00:00Z",
  "platforms": [
    "950"
  ]
}
---

# TND 布局 FA v2 host list `actual_seq_lengths_list_q` 在 batch>1 必须为 cumulative

## 适用场景

- 模型/框架：Hunyuan-A13B-Instruct-FP8，Paged KV + `torch.ops.npu.npu_fused_infer_attention_score_v2`（`input_layout="TND"`、`sparse_mode=3`）；npugraph_ex 图模式适配中为 FA 长度新增 host `List[int]` 传参（`ForwardMetaData.actual_seq_lengths_list_q/kv`）。
- 平台/版本：Ascend950PR_9589 单卡；CANN 9.1.0；torch 2.12.0+cpu / torch_npu 2.12.0。
- 目标与工作负载：batch=1 走 npugraph_ex 图、batch>1 packed 走 eager 回退的混合路径（`reviewer_multibatch_check`：3 条不等长 prompt，batch=1 solo 与 batch=3 packed 逐请求比对贪心 token）。

## 触发与观测

- 触发：npugraph_ex 适配初版在 decode 循环中对所有 batch 传 `actual_seq_lengths_list_q=[1] * batch_size`（batch=1 时恰好正确），batch=3 packed（eager 回退路径）立即失败。
- 故障：batch=3 packed decode（eager 回退路径）传 `actual_seq_lengths_list_q=[1] * batch_size` 触发 FA tiling 校验失败 `The last element(1) of actualSeqLengthsQ is not equal to the T(3) of query. The last element of actualSeqLengthsQ must be equal to the T of query when the layout of query is TND.`（actual_seq_len_checker.cpp:275），并伴随 805306368 bytes 显存分配失败，multibatch 校验 rc=1。
- 观测原文（失败关键行，`torch.OutOfMemoryError ... aclnnFusedInferAttentionScoreV5 failed, error code is 207001` 之后）：

```
The last element(1) of actualSeqLengthsQ is not equal to the T(3) of query. The last element of actualSeqLengthsQ must be equal to the T of query when the layout of query is TND.[FUNC:CheckActualSeqLenQTNDLastData][FILE:actual_seq_len_checker.cpp][LINE:275]
```

注意表层错误是 `OutOfMemoryError` / `Resource_Error_Insufficient_Device_Memory`（workspace 分配失败），真因在其后的 tiling 校验信息——只看 OOM 会误判为显存不足。

## 探针与操作

错误写法（before，`runner_hunyuan_a13b_fp8.py` decode 循环初版）：

```
                actual_seq_lengths_list_q=[1] * batch_size,
                actual_seq_lengths_list_kv=kv_lens_step_list,
```

正确写法（after，最终态）：

```
277:                 # TND query lengths are cumulative ([1, 2, ..., B] for Decode).
278:                 actual_seq_lengths_list_q=list(range(1, batch_size + 1)),
279:                 actual_seq_lengths_list_kv=kv_lens_step_list,
```

复现/校验命令：`tools/_envrun.sh tools/reviewer_multibatch_check.py`（batch=1 solo 三条 + batch=3 packed 一轮，逐请求贪心 token 比对）。

失败路线（不可采用）：`[1] * batch_size`（非 cumulative，末元素 != T）；把 OOM 当显存问题去清缓存/减 batch 无效。

## 机制与判别

- TND 布局下 query 的 T 等于 packed 总 token 数（decode 时 = B）；`actual_seq_qlen` 是 cumulative 查询长度表，FA 算子校验其**末元素必须等于 T**。batch=1 时 `[1]` 恰好同时满足"TND cumulative 且末元素=1"两种语义，掩盖了错误；batch=3 时 `[1,1,1]` 末元素 1 != T=3 被校验拒绝。
- 与 kv 侧的区别：decode 的 `actual_seq_lengths_list_kv` 是 direct（每请求各自 KV 长度），保持 `kv_lens_step_list` 即可；只有 q 侧要求 cumulative。
- 可区分解释分支：a) q 长度表语义错（成立）；b) 显存不足（被证伪：同一 batch=3 负载修一行后 PASS，显存占用不变量级）；c) FA host list 与 eager 路径不兼容（被证伪：该错误发生在 eager 回退路径，Tensor/list 均走同一 tiling 校验）。
- 未验证推断：BNSD/BSH 布局下该 list 的语义未实测。

## 验证信号

均在本机（Ascend950PR_9589 单卡、CANN 9.1.0）实测，证据等级：脚本退出码 + 日志比对。

- 失败：`reviewer_multibatch_check.py` rc=1，batch=3 段报上述 tiling/OOM 错误（实施者事件 276/280）。
- 修复：改为 `actual_seq_lengths_list_q=list(range(1, batch_size + 1))`（TND cumulative，末元素 == B == query 的 T）后，batch=1 图模式 + batch=3 packed eager 回退逐请求 greedy token 一致，`reviewer_multibatch_check` RESULT: PASS（rc=0）。（`[check] req0/req1/req2 match=True`，`RESULT: PASS`）
- 单次观测（一轮 multibatch 校验），未做多轮统计。

## 适用与失效边界

- 适用：FA v2 TND 布局下一切构造 `actual_seq_qlen`（list 或 Tensor cumsum 形式）的调用方；eager 与 npugraph_ex host-list 路径同此约束。
- 失效/风险：batch=1 的测试无法暴露该错误（`[1]` 恰好双语义重合）；必须用 batch>1 packed 用例回归。
- 若改用其它 `input_layout`（BSH/BNSD），cumulative 语义未在轨迹内验证，需按算子文档重核。
- 停止/回退条件：出现 `CheckActualSeqLenQTNDLastData` 校验失败即定位到 q 长度表构造，不要按 OOM 处理。
