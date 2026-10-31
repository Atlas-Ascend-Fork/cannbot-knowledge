---
type: Guide
title: DeepSeek-V4 A3与950部署及优化验收流程
description: 更新 V4 当前环境与六类启动配置，串联 CacheEntry/CP 状态写回、原生 MTP、950 低时延 TP 和 DSpark 验证。
tags:
- task.implementation
- topic.model_serving
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_inference_guide.md
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modules/attention_data.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modules/compressor.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_950/deepseek_v4_flash_rank_16_16ep.yaml
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_950/deepseek_v4_flash_rank_4_1bs_low_latency_tp_dspark.yaml
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_950/deepseek_v4_flash_rank_4_4ep_dspark.yaml
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_a3/deepseek_v4_flash_rank_128_128ep_128cp_w8a8.yaml
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_a3/deepseek_v4_flash_rank_128_128ep_w8a8.yaml
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_a3/deepseek_v4_flash_rank_16_16ep_w8a8_platform.yaml
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_a3/deepseek_v4_pd/decode.yaml
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_a3/deepseek_v4_pd/prefill.yaml
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_a3/deepseek_v4_pro_rank_64_64ep_w4a8.yaml
  role: implementation
created_at: '2026-10-21T09:02:44Z'
updated_at: '2026-10-29T15:20:09Z'
platforms:
- a3
- '950'
---

# DeepSeek-V4 A3与950部署及优化验收流程

## 目标、输入与产物

本流程面向 当前锁定的 cann-recipes-infer 提交 的 DeepSeek-V4 Flash/Pro，分别核对 Atlas A3 与 950PR/DT 路径。输入为具体平台/部署形态、权重规格与量化、卡数、序列和目标；输出为配置快照、正确性与计时记录、缓存/通信检查和回退记录。本次没有执行模型，机制见[模型总览](../../concepts/models/deepseek_v4.md)。

## 1. 先分开平台与权重路径

A3 整数量化条件由[INT8/INT4 机制](../../concepts/quantization/int8_int4_hybrid.md)维护，950 浮点混合条件由[FP8/MXFP4 机制](../../concepts/quantization/hybrid_mxfp8_mxfp4.md)维护。原生混合权重与转换后的权重不是同一路径；按固定 README 核对是否只转换 config 或还需转换权重。不要把混合格式写成量化 Scope 的 OR。

固定 README 对原生 Hybrid FP8-MXFP4 要求转换 `config.json`，该脚本会覆盖原配置，运行前备份。其他量化场景按各自转换路径核对参数和输出，本 Guide 不执行转换或覆盖用户权重。

## 2. 核对运行配置与环境

按固定 README 选 `config/ci_a3` 或 `config/ci_950`、设置实际权重路径、IP 与 CANN 路径，再指定 `YAML_FILE_NAME`。来源配置默认使用 `npugraph_ex`；其他后端的可用性仍须按对应版本检查。

固定 README 的一站式 A3 8 卡环境只支持 Flash，使用 `ci_a3/deepseek_v4_flash_rank_16_16ep_w8a8_platform.yaml`，并要求 `enable_limit_core=False`；它与 Atlas A3 Pod 的控核配置不能相互覆盖。平台范围不是卡数、die 数和算力规格完全相同的证明。

按来源在模型目录、各节点同步执行 `bash infer.sh`，保存有效配置、版本、输入和输出。完整依赖、启动与最小部署单元以固定 README 为准，不把部署示例环境直接当作 benchmark 的测量环境。

当前 A3 README 使用 CANN9.2/PT2.9、HDK25.5.1；950 示例为 x86、CANN9.2 weekly 与 PT2.9/torch_npu2.9 对应开发包。按 README 固定镜像和 requirements 配套，不把其他模型的 CANN9/PT2.8 环境混用。

| 当前配置文件（config 下） | world / CP / batch | 投机配置 |
| --- | --- | --- |
| ci_a3/deepseek_v4_flash_rank_128_128ep_w8a8.yaml | 128 / 1 / 256 | next_n=1 |
| ci_a3/deepseek_v4_flash_rank_128_128ep_128cp_w8a8.yaml | 128 / 128 / 256，cp_mini_batch=1 | next_n=1 |
| ci_a3/deepseek_v4_pro_rank_64_64ep_w4a8.yaml | 64 / 1 / 256，o_proj TP16 | next_n=1 |
| ci_950/deepseek_v4_flash_rank_16_16ep.yaml | 16 / 1 / 16 | next_n=3 |
| ci_950/deepseek_v4_flash_rank_4_4ep_dspark.yaml | 4 / 1 / 4 | DSpark width5 |
| ci_950/deepseek_v4_flash_rank_4_1bs_low_latency_tp_dspark.yaml | 4 / 1 / 1 | DSpark width7 |

A3 的 world_size 统计与双 die 芯片对应，不能把 world128 当作128张物理卡。配置是启动样例，不等同于性能表的完整测量命令。当前 V4 仅允许 eager/npugraph_ex；eager 拒绝 cache_compile/SuperKernel，enable_limit_core 需要多流、与 PyPTO 互斥。V4 的 enable_pypto 仍只接受 A3，不能由编程框架跨代际能力推断整网支持。

## 3. 并行与 MTP 的集成检查

### Prefill 并行（长序列 CP + zigzag）

长序列 Prefill 内存与 TTFT 压力大，故 Attention 选 **Context Parallel（CP）** 而非 DP，多 rank 分摊计算/访存。LI 用 `causal_mask`，越靠后的 Context Chunk 访存/计算越重，故沿用 V3.2 的 `zig_zag` 切分将首尾序列块放同一 rank 做负载均衡。见 [context-parallel](../../concepts/parallelism/context_parallel.md)、[zigzag-cp](../../concepts/parallelism/zigzag_cp.md)。

切分需同时考虑滑窗与压缩：SWA 层每个 chunk 需前序 `win_size=128` 的 KV；HCA / CSA 层若前序 chunk 序列 **128 对齐**则无需向后传额外 token（CSA Compressor 另需前序 4 个 token 做 Overlap）。Attention 模块引入两次 CP 通信：MQA 起始用全局 `all_gather` 取各 rank 末尾 128 token（按 `receive_idx` 裁切，`chunk_0` 不取）；Compressor 后对 Compress Cache 做 CP 域 `all_gather`（zigzag 场景需顺序重排）供 LI/SAS 使用。

**进一步通信优化**（源 §并行策略 › Prefill 并行策略末段，CSA 为例，源附图 `prefill_cp_allgather_cache2`）：由于两个 Compressor 存在并行空间，且 CSA 的 Compressor 仅需 4 个 Overlap token 信息，因此可将 **Window Attention 所需数据**与 **Compressor 所需数据分别进行通信**，实现计算通信掩盖，且冗余计算的数据量也较少。Compressor 后同样需要对 Compressed Cache 做 CP 域 `all_gather` 通信。

### Decode 并行（DP + EP + LM_head TP）

Decode 参考 DeepSeek-R1 / V3.2 方案：Attention 用 **Data Parallel（DP）**、MoE 用 **Expert Parallel（EP）**、LM_head 用 **Tensor Parallel（TP）**。Output Projection 中 `o_a_proj` 权重大、访存重，低时延场景可**选择性对其做 TP 切分**，经 `all_to_all` + `reduce_scatter` 实现 DP↔TP 转换。见 [data-parallel](../../concepts/parallelism/data_parallel.md)、[expert-parallel](../../concepts/parallelism/expert_parallel.md)、[tensor-parallel](../../concepts/parallelism/tensor_parallel.md)。

### 950 低时延 TP

`low_latency_tp=True` 要求 attn_tp_size=world_size>1、cp_size=1，o_proj/moe/embed/lmhead TP 也等于 world；attention heads 和 o_groups 必须可整除 TP。每 rank 保留全部专家的 TP 分片，路由后专家输出 all_reduce，不走普通 EP Dispatch/Combine。开启稀疏 grouplist 时依赖带 KEY_VALUE 空专家修复的算子包；共享专家侧流必须在 finalize 前等待，避免未完成输出被读取。它与普通 DP/EP 并行是不同配置路径。

### MTP

V4 沿用原生 Multi-Token Prediction（[mtp-speculative-decoding](../../concepts/techniques/mtp_speculative_decoding.md)）。Main Model 针对 Window KV 与 Compressor 的 `kv_state`/`score_state` 设计 **Ring Buffer**（`block_table` + `slot_mapping` 复用少数 Cache 块），其余 KV Cache 按压缩后最大长度申请；MTP 场景沿用 LI / SAS 内置的**梯形掩码**，确保待验证 token 的压缩 Cache 不参与主模型 token 计算。**MTP Spec Model 仅使用 Window Attention（SWA）**，原生 MTP 的多个 Draft Step 复用其声明的模型权重与 CacheEntry。MTP 在 SWA/HCA/LI 上 Cache 搬运量与非 MTP 几乎一致，自然提升计算访存比；CSA 的 FA 极端下搬运量为非 MTP 的 `next_n+1` 倍。来源提出高吞吐场景尝试 MTP1、低时延场景尝试 MTP3；这是固定实践的选择，不是按目标自动启用的规则，需要测量实际接受率、时延和输出。

#### Main Model 额外 Cache 定量（源 §MTP › Main Model 方案）

若某 MTP Token 校验不被接受，需在下一 Step 重新推导，故须为 Compressor 的 `kv_state`/`score_state` 额外缓存。结合 Ring Buffer，只需**提前申请更大 Buffer** 即可自然实现该额外缓存动作。需缓存的 Cache 以 `compress_ratio` 个 token 为一组统计，组数公式为：

$$
\mathrm{num\_ratio\_group} = (1 \ \mathrm{if} \ \mathrm{next\_n} == 0 \ \mathrm{else}\ 2) + \mathrm{overlap}
$$

其中 `overlap` 在 CSA 等于 1、在 HCA 等于 0。`num_ratio_group` 里预留了**余数 token** 和**可能需要重新压缩的前序 token**。每个 Batch 需要的 Cache Block 个数为：

$$
\mathrm{ceil}(\mathrm{num\_ratio\_group} \times \mathrm{ratio} \ / \ \mathrm{block\_size})
$$

MTP 的通用取舍与计时见[MTP 机制](../../concepts/techniques/mtp_speculative_decoding.md)和[计时规则](../../optimizations/rules/mtp_decode_timing_two_metric_split.md)；o_proj 的通用取舍见[局部 TP 规则](../../optimizations/rules/local_tp_memory_heavy_projections.md)。这些入口不替代上述 V4 特有的滑窗、压缩和缓存前提。

### 当前缓存申请与 CP 写回

模型 get_cache_info 声明各层 SlidingWindow/FullAttention CacheEntry，框架按 manager_key 分配并通过 setter 绑定。Compressor 的 state/score 在同一 FP32 state tensor；C4A 的 SFA/LI 各有 state，不能沿用旧 CacheData 的 None 占位结构。

离线 CP Prefill 使用临时全长压缩缓存与逐层 state_cache_by_layer；前后段计算、all_gather、ZigZag 重排后，仅有效 Decode 归属 rank 写回持久缓存。C128A state 写目标末块，C4A 按有序 block ids 映射；warmup 不写回。上述 Ring Buffer 公式解释算法余量，实际预算按当前管理器/CacheEntry、量化记录与临时空间核算，不能仅用公式替代框架申请。

### DSpark

当前 V4 DSpark 与原生 MTP 的配置、拒绝采样、缓存和 PD 状态传输见[专用流程](deepseek_v4_dspark.md)。V4 DSpark 明确拒绝 CP>1；通用 Worker 的 CP 行序修复不表示这个具体模型支持 CP。A3 PD 配置位于 ci_a3/deepseek_v4_pd，P/D 均 width5、CP1，需保持量化与 attention TP 匹配。

## 4. 多流数据依赖检查

V4 借助 CANN 软件栈的算子控核与多流并行能力，对跨算子无数据依赖的计算流做细粒度并行掩盖（[multi-stream](../../concepts/techniques/multi_stream.md)）。

### Attention 多流并行

源 §多流并行优化 › Attention 多流并行（CSA 为例，源附图 `attn_multi_stream`）逐条列出 4 个并行点：

- **(a)** MLAProlog 模块中 Query 计算流与 KV 计算流有并行空间：`kv_proj`、`q_b_proj` 等 Matmul 用 **Cube 核**计算，与 `q_rms_norm` 等用 **Vector 核**计算的算子可并行；
- **(b)** `q_b_proj` 后的 `rms_norm` 和 `rope` 可与 LI 的 `li_q_b_proj` 并行计算；
- **(c)** CSA 时 LI 与 CSA Compressor 无数据依赖，可通过 **CV 控核**确保算子分配到合适的 Cube/Vector 核数，在多流并行时减少计算资源抢占对性能的影响，来源描述用于掩盖 CSA 的 Compressor；实际是否完全掩盖需检查时间线；
- **(d)** HCA 中没有 LI，可直接用 MLAProlog 计算掩盖**部分** Compressor。

### MoE 共享路由多流并行

源 §多流并行优化 › MoE 共享路由多流并行（源附图 `moe_multi_stream`）：MoE 模块中共享专家与路由专家存在**计算与计算、计算与通信**的并行机会。来源针对 **Int8 和 MXFP8 量化场景**实现专家多流，以路由专家为关键路径尝试掩盖共享专家计算。是否影响路由路径、是否形成有效重叠，需要在实际时间线上核对，不能从示意图认定收益。详见 [moe-multi-stream](../../concepts/techniques/moe_multi_stream.md)。

## 5. 验证与回退

固定平台、精度、并行与 prompt，对照关闭相关优化的基线检查 CP 分片/重建顺序、Window/Compress/Indexer Cache、MTP 接受与拒绝后的状态，以及多流事件与实际重叠。出现输出差异时先恢复匹配的配置与缓存，不能只看延时就判定优化成功。跨流验证方法见[多流实施流程](../optimization/multi_stream_optimization_workflow.md)。

性能观测分为[950DT](../../optimizations/benchmark_observations/deepseek_v4_950_source_benchmark.md)和[A3 Pod](../../optimizations/benchmark_observations/deepseek_v4_a3_source_benchmark.md)，按行核对 GBS、Chips、MTP 和量化，不能把来源的强制 EPLB 当作输出精度已经通过。保留来源未给的 warmup、重复和测量环境缺口；本次不增加 verified。

## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/README.md)（primary）
- [deepseek_v4_inference_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_inference_guide.md)（implementation）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py)（implementation）
- [attention_data.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modules/attention_data.py)（implementation）
- [compressor.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modules/compressor.py)（implementation）
- [deepseek_v4_flash_rank_16_16ep.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_950/deepseek_v4_flash_rank_16_16ep.yaml)（implementation）
- [deepseek_v4_flash_rank_4_1bs_low_latency_tp_dspark.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_950/deepseek_v4_flash_rank_4_1bs_low_latency_tp_dspark.yaml)（implementation）
- [deepseek_v4_flash_rank_4_4ep_dspark.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_950/deepseek_v4_flash_rank_4_4ep_dspark.yaml)（implementation）
- [deepseek_v4_flash_rank_128_128ep_128cp_w8a8.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_a3/deepseek_v4_flash_rank_128_128ep_128cp_w8a8.yaml)（implementation）
- [deepseek_v4_flash_rank_128_128ep_w8a8.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_a3/deepseek_v4_flash_rank_128_128ep_w8a8.yaml)（implementation）
- [deepseek_v4_flash_rank_16_16ep_w8a8_platform.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_a3/deepseek_v4_flash_rank_16_16ep_w8a8_platform.yaml)（implementation）
- [decode.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_a3/deepseek_v4_pd/decode.yaml)（implementation）
- [prefill.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_a3/deepseek_v4_pd/prefill.yaml)（implementation）
- [deepseek_v4_pro_rank_64_64ep_w4a8.yaml](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/config/ci_a3/deepseek_v4_pro_rank_64_64ep_w4a8.yaml)（implementation）
