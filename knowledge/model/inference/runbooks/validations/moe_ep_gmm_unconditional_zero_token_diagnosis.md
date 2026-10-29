---
type: Runbook
title: 纯 EP MoE decode 中 GMM 无条件执行（0 token 也跑）：profiling 里某卡缺 GMM 不能用「该卡没分到 token」解释，用 expert_token_num 诊断
description: 纯 EP MoE decode 中 GMM 无条件执行（0 token 也跑）：profiling 里某卡缺 GMM 不能用「该卡没分到 token」解释，用 expert_token_num 诊断。采集昇腾纯 EP（moe_ep_size>1 / moe_tp_size==1）MoE decode 的 profiling，发现某卡没有 GroupedMatmul(gmm) 算子、其余卡有（各卡 gmm 非对称）。直觉会把它当作「该卡专家没分到 token → 不跑 gmm」的正常负载不均现象——这个直觉是错的。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/120
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-09-03T13:55:44Z'
platforms:
- agnostic
---

# 纯 EP MoE decode 中 GMM 无条件执行（0 token 也跑）：profiling 里某卡缺 GMM 不能用「该卡没分到 token」解释，用 expert_token_num 诊断

## 信号（现象）

采集昇腾纯 [EP](../../concepts/parallelism/expert_parallel.md)（`moe_ep_size>1` / `moe_tp_size==1`）MoE decode 的 profiling，发现**某卡没有 GroupedMatmul(gmm) 算子、其余卡有**（各卡 gmm 非对称）。直觉会把它当作「该卡专家没分到 token → 不跑 gmm」的正常负载不均现象——**这个直觉是错的**。

## 根因 / 算子行为事实

纯 EP 下每卡只持全部专家的一个分片，各卡本步收到的 token 数随路由分布波动、可为 0。但 **gmm 的调用与该卡是否收到 token 无关**——decode 路径 dispatch 出 `expert_token_num` 后直接喂给专家 GroupedMatmul，**没有任何 `expert_token_num.sum()>0` 守卫**：

```python
output = torch_npu.npu_moe_distribute_dispatch_v2(**dispatch_args)
expand_x, dynamic_scale, expand_idx, expert_token_num, ep_recv_counts, tp_recv_counts = output[:6]
# 无条件调用，无 token 计数分支
gmm_args = {"x": expand_x, "expert_tokens": expert_token_num, "group_list_type": 1}
if "a8" in self.gmm_quant_mode:
    gmm_args.update({"pertoken_scale": dynamic_scale})
hidden_states_ordered_by_experts = self.experts(**gmm_args)   # FusedMoEGMM → npu_grouped_matmul
```

`FusedMoEGMM` 内部同样无 token 计数分支——`expert_token_num` 全 0 时 gmm 仍执行（处理空 group）。**故正常情况下每卡每步都应出现 gmm 算子；缺 gmm 是异常信号（需另查配置/图/采集差异），不是「该卡没 token」的自然结果。**

## 诊断手段

在 **eager 模式**下打印 `npu_moe_distribute_dispatch_v2` 输出 tuple 的第 4 项 `expert_token_num`（`output[:6][3]`），它是**该卡上每个专家本步收到的 token 数**（DeepSeek-V4 shmem 指南记 `expert_token_nums_out`=「每个专家收到的token个数」，全库 MoE 建模文件解包位置一致）。据此确认目标卡是否真的收到极少/0 token、各专家分布是否异常——但**即使确认 0 token，也不改变「gmm 仍应被调用」这一结论**。

## 边界 / 关联

参考现象取自 LongCat-Flash 系 4 卡 EP decode；原始现象的根因（0 卡为何缺 gmm）在上游 Issue 中尚未查明。上述算子行为事实与诊断判据可跨 MoE 模型复用。dispatch 出 `expert_token_num` 后走的 [MC2 dispatch/combine](../../concepts/techniques/moe_dispatch_combine_v2.md) 路径见其概念页；「各卡专家负载」的理想均衡口径测量见 [perfect-eplb-profiling-upper-bound](../../optimizations/rules/perfect_eplb_profiling_upper_bound.md)。

## Evidence

- decode 路径 `self.experts(**gmm_args)` 在 dispatch 后无条件调用（无 token 计数守卫）、`FusedMoEGMM.forward` → `npu_grouped_matmul` 无零 token 分支、`expert_token_num` 为 dispatch 输出第 4 项：diff/code 事实 @2c45117d。溯源下探 [cann-recipes-infer-issue-120-question-longcat-4p](https://gitcode.com/cann/cann-recipes-infer/issues/120)。
- 「eager 打印 expert_token_num 确认各专家 token 数」「即使 0 卡专家没 token，gmm 也会被调用」：维护者确认（官方 issue 讨论区答复，与代码互相印证）。
