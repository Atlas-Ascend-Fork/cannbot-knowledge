---
type: Runbook
title: MoE dispatch/combine 算子报错或大 batch 失败：HCCL 通信 buffer 不足，须按模型显式放大 HCCL_BUFFSIZE
description: MoE dispatch/combine 算子报错或大 batch 失败：HCCL 通信 buffer 不足，须按模型显式放大 HCCL_BUFFSIZE。昇腾多卡 EP 推理下，MoE 的 npu_moe_distribute_dispatch_v2（报错日志里显示为 MoeDistributeDispatchV2）启动即报算子错误，或大 batch 时失败；日志常见关键字 HCCL_BUFFSIZE is too SMALL, ..., NEEDED_HCCL_BUFFSIZE..., HCCL_BUFFSIZE=200MB。切到 eager 模式同一算子仍报错——不是图模式独有，是 EP dispatch 通信层的问题。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.parallelism
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/160
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/421
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/issues/4051
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:33:02Z'
platforms:
- a3
---

# MoE dispatch/combine 算子报错或大 batch 失败：HCCL 通信 buffer 不足，须按模型显式放大 HCCL_BUFFSIZE

## 信号（现象）

昇腾多卡 [EP](../../concepts/parallelism/expert_parallel.md) 推理下，MoE 的 [`npu_moe_distribute_dispatch_v2`](../../concepts/techniques/moe_dispatch_combine_v2.md)（报错日志里显示为 `MoeDistributeDispatchV2`）启动即报算子错误，或大 batch 时失败；日志常见关键字 `HCCL_BUFFSIZE is too SMALL, ..., NEEDED_HCCL_BUFFSIZE..., HCCL_BUFFSIZE=200MB`。切到 eager 模式同一算子仍报错——**不是图模式独有**，是 EP dispatch 通信层的问题。

同一签名在**算子 tiling 阶段**也会以链式失败出现：`MoeDistributeDispatchV2 do tiling failed, ret is -1`，其上是 A3 tiling 实现 `MoeDistributeDispatchA3TilingFuncImpl`（`moe_distribute_dispatch_v2_tiling.cc`）打印的 `HCCL_BUFFSIZE is too SMALL, ...`，其下一路 `NnopbaseExecutorDoTiling` / `NnopbaseExecutorTilingAndUpdateBinInfo` / `NnopbaseExecutorMatchCache` / `NnopbaseRunForWorkspace` Check failed、进程 EZ9999 崩溃。这条 tiling 校验会在**启动期的显存探测**（`profile_run` → `_dummy_run` → dummy 前向）就触发——即真正推理前的空跑就崩，不必等到稳态解码。因此「刚起服务、模型还没进 token 就报 HCCL_BUFFSIZE too SMALL」也属同一根因。

## 触发条件

MoE EP dispatch/combine 走 HCCL all-to-all，通信 buffer（RDMA 窗口）大小由 `HCCL_BUFFSIZE` 控制，默认 **200MB**。当一步 dispatch 的流量超过该 buffer（专家数多、batch 大时更易），算子报错。

## 根因

默认 HCCL buffer 对 MoE 全量 dispatch/combine 太小。所需 buffer 随「路由专家总数 / 每卡专家数 / batch」增长——仓内注释自报某满配 671B 级 MoE 需约 479MB。注意实现细节：`ProcessGroupHCCL` 的 `hccl_config["hccl_buffer_size"]` 不直接读环境变量，是 executor 显式读取 `HCCL_BUFFSIZE`（`int(os.environ.get("HCCL_BUFFSIZE", 200))`）后注入 `options`，所以 launch 脚本里的 `export HCCL_BUFFSIZE=...` 才对 `moe_ep_group` 生效。

算子自身把所需缓冲量以**显式公式**打印在 `HCCL_BUFFSIZE is too SMALL` 日志里，可据此对自身 workload 换算（缓冲需同时容纳 dispatch 与 combine，故末尾 `*2`）：

```
NEEDED_HCCL_BUFFSIZE = (maxBs * tokenNeedSizeDispatch * ep_worldsize * localMoeExpertNum
                        + maxBs * tokenNeedSizeCombine * (k + sharedExpertNum)) * 2
```

其中 `maxBs`=最大 batch、`tokenNeedSizeDispatch/Combine`=单 token 分发/聚合字节数、`ep_worldsize`=EP world size、`localMoeExpertNum`=每卡本地专家数、`k`=top-k、`sharedExpertNum`=shared-expert 数。可见所需缓冲主要被 `ep_worldsize × localMoeExpertNum × maxBs` 一项撑大——**EP 规模大、每卡专家多、batch 大**的 MoE 尤其容易超出默认 200MB。该公式是通用换算依据，不是某模型专属。

## 修法

两条，按能不能改代码选：

- **快修（部署侧）**：调大 `HCCL_BUFFSIZE` 并**所有 Rank 保持一致**。观测实例里 `export HCCL_BUFFSIZE=205`（仅略高于默认 200）即让 eager 恢复正常——具体值取该配置实际需求量，不外推为通用阈值。
- **根治（代码侧）**：不依赖 shell 级 export，代码内按 yaml + HF config 计算 buffer 并传给 `init_comm_group` 的 `hccl_buffer_size`。参考实现 `calc_moe_hccl_buffer_size(runner_settings, hf_config, ...)` 内读 `total_experts = get_global_routed_expert_num(config)`（取 `n_routed_experts`，无则回落 `num_experts`，都无则 `raise AttributeError`）、`experts_per_rank = total_experts // moe_ep_size` 推算窗口。

## 参考实现及其约束

- **cann-recipes-infer（代码内计算，根治向）**：`calc_moe_hccl_buffer_size(runner_settings, hf_config, ...)` 从 yaml + HF config 算 buffer 并传给 `init_comm_group` 的 `hccl_buffer_size`，内部 `total_experts = get_global_routed_expert_num(config)`（取 `n_routed_experts`，无则回落 `num_experts`，都无则 `raise AttributeError`）、`experts_per_rank = total_experts // moe_ep_size`。这是不依赖 shell export 的算路。约束：该函数是该仓的参考实现，其取字段回落链绑定该仓 config 约定，不是算子层要求。
- **vLLM + vllm-ascend（部署侧 export，快修向）**：该栈无 linked PR / 代码内计算路径，同一失败签名靠 `export HCCL_BUFFSIZE=<足够大>` 绕过。观测配置 `Qwen3-Next-80B-A3B-Instruct`（MoE，`localMoeExpertNum=128`、`k=10`、`sharedExpertNum=0`），`tensor_parallel_size=4` / `enable_expert_parallel=True`（EP world size=4）/ `enforce_eager=True`，CANN toolkit 8.3.RC1；算子按上面公式算出 `NEEDED_HCCL_BUFFSIZE=294MB` > 默认 `200MB` 而在 `profile_run` dummy 前向即 tiling 失败。维护者给的解法 `export HCCL_BUFFSIZE=1024`（远大于 294MB、一次性覆盖），校验通过后 tiling 不再失败。约束：`1024` 是作者取的一个足够大值、非精确阈值——按公式算自身 workload 的 NEEDED 再留余量即可；数字忠于该 CANN 版本 + 该 config，不外推为「所有 MoE 都需 1024」。这条也证实该失败签名**跨框架**（cann-recipes-infer 与 vLLM/vllm-ascend 都命中），是 EP dispatch 通信层的公共问题、非某框架 bug。

## 关联

- 该显式 buffer 后来归位到独立的 `moe_ep_group_mc2` 域（只给 MC2 路径放大、普通 EP 域回落默认），见 [mc2-dedicated-comm-domain](../../optimizations/experience/rules/mc2_dedicated_comm_domain.md)。
- 多个 MoE 模型 README 记录同一「HCCL_BUFFSIZE is too SMALL」失败签名——这是跨 MoE 模型可复用的失败签名、非一次性 changelog。

## Evidence

- 维护者给出 `export HCCL_BUFFSIZE=205`、报告者复现确认 eager 随后可跑：维护者确认 + 报告者复现；默认 200MB 由 executor 转发注入、LongCat decode EP 走 dispatch_v2/combine_v2 并提示检查 HCCL_BUFFSIZE：diff/doc 事实 @2c45117。溯源下探 [cann-recipes-infer-issue-160-bug-report-longcat](https://gitcode.com/cann/cann-recipes-infer/issues/160)。
- 默认 200MB 不足、`calc_moe_hccl_buffer_size` → `hccl_buffer_size` 传参链、某 R1 级配置报需约 479MB：diff 事实 @d4b8eb61；200MB/479MB 数字为仓内注释自报、无独立复测。溯源下探 [cann-recipes-infer-pr-421-refactor-mc2-use-independent-communication-group](https://gitcode.com/cann/cann-recipes-infer/merge_requests/421)。
- vLLM/vllm-ascend 上 Qwen3-Next-80B-A3B EP 推理，`profile_run` dummy 前向即 `MoeDistributeDispatchV2 do tiling failed, ret is -1`：报错字符串、`NEEDED_HCCL_BUFFSIZE` 公式与各参数（`maxBs=64/h=2048/epWorldSize=4/localMoeExpertNum=128/k=10/sharedExpertNum=0`）、`294MB` vs `200MB` 均来自 issue 正文中 CANN 算子（`MoeDistributeDispatchA3TilingFuncImpl`, `moe_distribute_dispatch_v2_tiling.cc:941`）自身打印的 EZ9999 日志，非报告人推测；修法 `export HCCL_BUFFSIZE=1024` 由 COLLABORATOR 维护者答复给出、issue closed COMPLETED = 维护者确认；无 linked PR / diff。溯源下探 [vllm-ascend-issue-4051-bug-qwen3-next-ep-inference-failure](https://github.com/vllm-project/vllm-ascend/issues/4051)。

<!-- cannbot:related:start -->
## 相关

- [MoE Dispatch/Combine V2（一体化融合算子）](../../concepts/techniques/moe_dispatch_combine_v2.md)（`related`）：`torch_npu.npu_moe_distribute_dispatch_v2` / `npu_moe_distribute_combine_v2`（仓内文档亦称 **MC2** 路由）是把 MoE 专家并行（［expert-parallel］(../parallelism/expert_parallel.md)）的整条 All-to-All 路由链路收敛为**两个一体化融合算子**：；MoE EP dispatch/combine 走 HCCL all-to-all，通信 buffer（RDMA 窗口）大小由 `HCCL_BUFFSIZE` 控制，默认 **200MB**。当一步 dispatch 的流量超过该 buffer（专家数多、batch 大时更易），算子报错。。概念卡定义两个融合算子的 EP All-to-All，Runbook给出其 HCCL buffer 不足时的启动期信号、容量公式和调参动作。
- [多机集合通信 HCCL_BUFFSIZE too SMALL —— 调大且各 rank 一致](hccl_buffsize_too_small.md)（`same_topic`）：默认 HCCL buffer 对 MoE 全量 dispatch/combine 太小。；根因即环境变量 `HCCL_BUFFSIZE` 设定的通信缓冲区偏小、不满足 `NEEDED_HCCL_BUFFSIZE`。两卡都定位同一通信缓冲不足，MoE 卡补充 dispatch/combine 需求公式与注入路径，通用卡给出多机 rank 一致的处置边界。
<!-- cannbot:related:end -->
