---
type: "Runbook"
title: "L2 读写端口独立并行 HBM 总线串行共享"
description: "Ascend950 L2 的 MTE2 读端口与 MTE3 写端口独立并行（吞吐可相加），HBM 总线被读写共享串行仲裁；并发读写带宽应按总数据量与实际并发时间算，不能把单路带宽相加当并发带宽。"
tags: ["task.lookup", "topic.architecture", "topic.data_movement.memory_access", "topic.performance.analysis"]
status: stable
sources: []
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# L2 读写端口独立并行 HBM 总线串行共享

## 现象

在 Ascend950PR 上测并发读写带宽（`test/concurrent_rw/probe_rw.asc`，同 kernel 内同时发 MTE2 读 + MTE3 写）。用 NPU event 测并发 kernel 实际时间得到并发带宽；再用 msprof 分别采纯读 MTE2 时间与纯写 MTE3 时间，把读带宽 + 写带宽相加，得到一个"两路相加"的值。两者差异巨大：

- L2 hit：相加相对 NPU event 实测并发带宽高估约 12%。
- HBM：相加相对 NPU event 实测并发带宽高估约 2.1 倍。

根因是 L2 与 HBM 的读写通路并行与串行模型不同。

## 适用场景

- 工程形态：Kernel 直调（ops-direct-invoke）并发读写带宽探针，msprof `ai_core_metrics` 单管道计时 + NPU event 并发计时。
- API 路径：`DataCopy`（MTE2 读 / MTE3 写）；msprof `ai_core_metrics` 取 MTE2/MTE3 时间；`aclrtCreateEvent`/`aclrtSynchronizeStream`（NPU event 并发计时）。
- 验证过的平台与 CANN 版本：Ascend950PR；CANN 9.1.0。
- 适用粒度：platform_wide（所有在 950 上设计并发读写 kernel、或解释并发读写带宽数据的 kernel）。
- 路线优先级：recommended_fastpath（并发带宽用 NPU event 实测并发时间 + 总数据量算；用单路 msprof MTE2/MTE3 时间分别核算只用于验证各路是否独立达标，不作为并发总带宽）。
- 不适用或未验证场景：msprof 对双管道（MTE2+MTE3 同时用）并发 kernel 不生成 `ai_core_metrics`，无法分别取并发场景下的 MTE2/MTE3 时间——本环境工具限制，未验证；950DT 未验证。

## 根因

950 L2 Cache 的读端口（MTE2）与写端口（MTE3）是独立端口，可真正并行——两管道执行时间重叠，并发场景下实际总时间约等于 max(MTE2 时间, MTE3 时间)，两路吞吐可相加；但"读带宽+写带宽"用的是各自独立场景的时间，相加会高估（因分子两倍、分母用各自独立时间，相当于把重叠的并行时间当成了不重叠）。HBM 总线被读写共享、串行仲裁——两管道执行时间不重叠（互斥），实际总时间约等于 MTE2 时间 + MTE3 时间；但"读带宽+写带宽"把各自独立场景的带宽相加，分母用了独立场景的时间，相当于把串行的两路当成各自独立的满带宽，会近 2 倍高估。

## 判别方法

触发（tool_observed）：并发读写 kernel 的"读带宽 + 写带宽"（用纯读 msprof MTE2 + 纯写 msprof MTE3 时间分别算）远超 NPU event 实测并发带宽——L2 场景高估约 12%，HBM 场景高估约 2.1 倍。

探针：① 跑纯读 kernel，msprof 取 MTE2 时间，算读带宽；② 跑纯写 kernel，msprof 取 MTE3 时间，算写带宽；③ 跑并发读写 kernel，NPU event 取并发实际时间，算并发带宽；④ 比较（读带宽 + 写带宽）与并发带宽的比值。

观测（tool_observed）：L2 场景下"读带宽+写带宽"相对 NPU event 实测并发带宽高估约 12%；HBM 场景下高估约 2.1 倍；纯读 L2 带宽与纯写 L2 带宽接近（均接近单向 L2 上限）。

解释（interpretation，端口级并行度为推断）：L2 两端口独立并行，各自时间重叠，相加高估；HBM 总线串行共享，各自时间不重叠但相加用了独立场景带宽，近 2 倍高估。并发带宽只能用 NPU event 实测并发时间 + 总数据量算；单路相加只用于验证各路是否独立达标。

## 验证信号

- L2 并发读写"读带宽+写带宽"相对 NPU event 实测并发带宽高估约 12%（来源平台:Ascend950；证据等级:tool_observed）
- HBM 并发读写"读带宽+写带宽"相对 NPU event 实测并发带宽高估约 2.1 倍（来源平台:Ascend950；证据等级:tool_observed）
- 纯读 L2 带宽与纯写 L2 带宽接近，均接近单向 L2 上限（来源平台:Ascend950；证据等级:tool_observed）

## 失效边界

- 950 / CANN 9.1.0 实测。
- msprof 无法对双管道并发 kernel 取 `ai_core_metrics`，"并发场景下 MTE2/MTE3 实际重叠时间"未直接量测（当前用纯读 + 纯写 msprof 时间相加近似），未验证。
- 950DT 未验证，推断可迁移（同代 L2/HBM 微架构）。

## 坏实践

- 把"纯读 msprof MTE2 带宽 + 纯写 msprof MTE3 带宽"当成并发读写总带宽报——L2 会高估、HBM 会近 2 倍高估，虚高达标率无物理意义。

<!-- cannbot:related:start -->
## 相关

- [Matmul高阶API开启L2 Cache切分](../../guides/operator_practice/best_practices/matmul_tuning_cases/matmul_l2_cache_split.md)（`related`）：《L2 读写端口独立并行 HBM 总线串行共享》处理“Ascend950 L2 的 MTE2 读端口与 MTE3 写端口独立并行（吞吐可相加），HBM 总线被读写共享串行仲裁；并发读写带宽应按总数据量与实际并发时间算，不能把单路带宽相加当并发带宽。”。《Matmul高阶API开启L2 Cache切分》明确提供“本案例呈现了在Matmul计算过程中，输入和输出的数据总量超过L2 Cache大小时，通过L2 Cache数据切分对算子性能的提升效果。开启L2 Cache切分的完整样例请参考L2 Cache切分的算子样例。”，其参数、调用或验证步骤直接接入L2 读写路径的 cache 控制、带宽、端口争用和 fence 验证。
- [TQue MTE2→MTE3 缺 MTE3_MTE2 fence 致回读错位](../compilation/tque_mte2_mte3_mte3_mte2_fence.md)（`related`）：《L2 读写端口独立并行 HBM 总线串行共享》处理“Ascend950 L2 的 MTE2 读端口与 MTE3 写端口独立并行（吞吐可相加），HBM 总线被读写共享串行仲裁；并发读写带宽应按总数据量与实际并发时间算，不能把单路带宽相加当并发带宽。”。《TQue MTE2→MTE3 缺 MTE3_MTE2 fence 致回读错位》明确提供“rms_norm_rope_k_store_kv_cache Phase2 回读用 TQue<VECIN> 走 MTE2→MTE3 跨迭代复用同一 UB，下一轮 MTE2 覆盖 UB 时上一轮 MTE3 未读完形成 WAR，大数据(max_seq_len=65536) kv_a_out 前段错位、后段正确；判别靠 debug_full.py 逐 batch front/back match + 单核(blockDim=1)排除多核；根因为 TQue event 在该跨迭代路径不可靠且跨 Phase GM 可见性需 Host 同步。”，其参数、调用或验证步骤直接接入L2 读写路径的 cache 控制、带宽、端口争用和 fence 验证。
- [UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽](duplicate_ub_prefill_hurts_pure_write_bandwidth.md)（`related`）：《UB 预填充 Duplicate 引入 Vector 开销拖慢纯写带宽》的任务是“在纯写 HBM 带宽探针的 DataCopy(UB→GM) 前加 Duplicate<half> 预填充 UB，相对原版纯写带宽反而下降约 5%，因 Duplicate 占用 Vector 流水线与 MTE3 串行，不应作为写带宽优化手段。”。《L2 读写端口独立并行 HBM 总线串行共享》具体提供“Ascend950 L2 的 MTE2 读端口与 MTE3 写端口独立并行（吞吐可相加），HBM 总线被读写共享串行仲裁；并发读写带宽应按总数据量与实际并发时间算，不能把单路带宽相加当并发带宽。”，它直接用于纯写带宽中 Duplicate 占用 Vector 流水并与 MTE3 串行的验证。
- [探针末尾 MTE2_S/MTE3_S 同步不可由 stream sync 替代](../compilation/mte2_s_mte3_s_stream_sync.md)（`related`）：《L2 读写端口独立并行 HBM 总线串行共享》处理“Ascend950 L2 的 MTE2 读端口与 MTE3 写端口独立并行（吞吐可相加），HBM 总线被读写共享串行仲裁；并发读写带宽应按总数据量与实际并发时间算，不能把单路带宽相加当并发带宽。”。《探针末尾 MTE2_S/MTE3_S 同步不可由 stream sync 替代》明确提供“DMA 带宽探针 kernel 末尾须保留 PipeBarrier<PIPE_MTE2/MTE3> + MTE2_S/MTE3_S SetFlag/WaitFlag，确保 MTE 管线 DataCopy 完成后 Scalar 才退出；aclrtSynchronizeStream 不能替代该 in-kernel 同步，去掉后小数据量带宽虚高约 1%。”，其参数、调用或验证步骤直接接入L2 读写路径的 cache 控制、带宽、端口争用和 fence 验证。
- [设置合理的L2 CacheMode](../../guides/operator_practice/simd_operator_optimization/memory_access/l2_cache_mode_config.md)（`related`）：《L2 读写端口独立并行 HBM 总线串行共享》处理“Ascend950 L2 的 MTE2 读端口与 MTE3 写端口独立并行（吞吐可相加），HBM 总线被读写共享串行仲裁；并发读写带宽应按总数据量与实际并发时间算，不能把单路带宽相加当并发带宽。”。《设置合理的L2 CacheMode》明确提供“>该性能优化指导适用于如下产品型号：”，其参数、调用或验证步骤直接接入L2 读写路径的 cache 控制、带宽、端口争用和 fence 验证。
- [逐 rank 通信路径的 MTE2 主导诊断](rank_flag_mte2.md)（`related`）：《逐 rank 通信路径的 MTE2 主导诊断》处理“ReduceScatter 远程读采用逐 rank DataCopy 与同步时，msprof 显示 aiv_mte2_time 主导 T_comm；三段注释法可排除 vec/reduce，但现有证据未单独验证 flag 是带宽缺口的唯一原因。”。《L2 读写端口独立并行 HBM 总线串行共享》明确“Ascend950 L2 的 MTE2 读端口与 MTE3 写端口独立并行（吞吐可相加），HBM 总线被读写共享串行仲裁；并发读写带宽应按总数据量与实际并发时间算，不能把单路带宽相加当并发带宽。”，可直接用于核对ReduceScatter 逐 rank 搬运的 MTE2 计时、HBM 解释、同步必要性与成对 profile。
- [Ascend950 DataCopy 写回 L2 驱逐丢对角线](../precision/ascend950_datacopy_l2.md)（`same_topic`）：《L2 读写端口独立并行 HBM 总线串行共享》处理“Ascend950 L2 的 MTE2 读端口与 MTE3 写端口独立并行（吞吐可相加），HBM 总线被读写共享串行仲裁；并发读写带宽应按总数据量与实际并发时间算，不能把单路带宽相加当并发带宽。”。《Ascend950 DataCopy 写回 L2 驱逐丢对角线》明确提供“Ascend950 上 fill_diagonal_v2 dense path 用 DataCopy 批量写回整个 tile 到 GM 时写入经多核共享 L2 cache，64 核并行写入合计约 8MB 超出 L2 容量，后 32 核 dirty cache line 在末尾 DataCacheCleanAndInvalid 前被驱逐未刷回 GM，对角线位置丢失；判别方法为 dump 比对定位对角线 out==input 且分界线落核 31/32 与 4MB L2 临界点一致。”，其参数、调用或验证步骤直接接入L2 读写路径的 cache 控制、带宽、端口争用和 fence 验证。
<!-- cannbot:related:end -->
