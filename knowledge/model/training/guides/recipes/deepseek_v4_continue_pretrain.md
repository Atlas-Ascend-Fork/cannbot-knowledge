---
type: Guide
title: DeepSeek-V4 TorchTitan-NPU + AutoFuse 极简续训练（Flash 64 卡 / Pro 192 卡 A3）
description: DeepSeek-V4 在昇腾 A3 上做续训练（CPT）。CANN 在 torchtitan-npu v0.2.2-dev 分支上为两个规格做了快速训练支持：DeepSeek-V4-Flash（285B / 43 层，最小 8 机 64 卡 A3 = 128 die）与 DeepSeek-V4-Pro（61 层，最小 24 机 192 卡 A3 = 384 die）。整套方案围绕三条主线——「极简并行」（纯 FSDP + 大 EP，舍弃 TP/PP）、「自动融合」（torch.compile + Ascend C AutoFuse 训练入图）、「定制算子」（针对 DSA / mHC 稀疏结构的 SAS / SASG / LI / SLIG 融合算子）。4K 序列 BF16 + MTP1 训练下，Flash 在 A3 SuperPods 64 卡集群上吞吐从初始 397 tokens/p/s 提升到 1100 tokens/p/s，其中定制融合算子与 AutoFuse 分别贡献约 90% 与 30% 的吞吐增益。该实践对应的推理部署见跨域页 deepseek-v4。
tags:
- task.implementation
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-09-03T13:55:44Z'
platforms:
- a3
---

# DeepSeek-V4 TorchTitan-NPU + AutoFuse 极简续训练（Flash 64 卡 / Pro 192 卡 A3）

## Summary

DeepSeek-V4 在昇腾 A3 上做**续训练（CPT）**。CANN 在 `torchtitan-npu` `v0.2.2-dev` 分支上为两个规格做了快速训练支持：**DeepSeek-V4-Flash**（285B / 43 层，最小 **8 机 64 卡 A3** = 128 die）与 **DeepSeek-V4-Pro**（61 层，最小 **24 机 192 卡 A3** = 384 die）。整套方案围绕三条主线——「**极简并行**」（纯 FSDP + 大 EP，舍弃 TP/PP）、「**自动融合**」（torch.compile + Ascend C AutoFuse 训练入图）、「**定制算子**」（针对 DSA / mHC 稀疏结构的 SAS / SASG / LI / SLIG 融合算子）。4K 序列 BF16 + MTP1 训练下，Flash 在 A3 SuperPods 64 卡集群上吞吐从初始 397 tokens/p/s 提升到 **1100 tokens/p/s**，其中定制融合算子与 AutoFuse 分别贡献约 90% 与 30% 的吞吐增益。该实践对应的推理部署见跨域页 [deepseek-v4](../../../inference/concepts/models/deepseek_v4.md)。

整体软件栈自顶向下为 TorchTitan → TorchTitan-NPU 插件 → TorchInductor → CANN AutoFuse：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v4/Architecture.png" width="62%"></p>
<p align="center"><sub>图：四层软件架构——TorchTitan 提供 FSDP 等 PyTorch Native 并行，TorchTitan-NPU 插件做昇腾通信/算子适配，Inductor 继承 torch.compile 图捕获，AutoFuse 作 Ascend C Codegen 后端（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·引言）</sub></p>

## 训练配置（两规格真实并行度）

软硬件基线（README）：Atlas A3 系列、Ascend HDK 25.5.2、CANN 9.0.0、镜像 `dsv4_train_torchtitan:cann9.0.0_v3.0`、`torchtitan-npu` `v0.2.2-dev` 分支。两规格 4K 序列、`local_batch_size=1`、`num_mtp_modules=1`、AdamW（`lr=1e-5`）、`activation_checkpoint.mode="full"`、`compile.enable=true`（`components=["model","loss"]`），均配置 `swap_optimizer=true`，用 SwapOptimizer 把优化器状态卸载到主机内存降设备内存（机制见下文 §内存卸载 / SwapOptimizer）。注：SwapOptimizer 与 Virtual Optimizer 是两套互斥的优化器显存方案（`optimizer_selector.py` 显式 `raise ValueError("Cannot enable both virtual_optimizer and swap_optimizer at the same time.")`），本实践两份主力 4k 配置用的是前者。

| 规格 | 层数 | 卡数 / die | config toml | 真实并行度 `[parallelism]` | GBS |
|---|---|---|---|---|---|
| **V4-Flash** | 43 | 8 机 64 卡 / 128 die | `deepseek_v4_285b_43layers_4k_128die.toml` | TP1 / PP1 / EP64 / etp1 / CP1，DP-shard=-1（FSDP 填满） | 1024 |
| **V4-Pro** | 61 | 24 机 192 卡 / 384 die | `deepseek_v4_pro_61layers_4k_384die.toml` | TP1 / PP1 / EP192 / etp1 / CP1，DP-shard=-1（FSDP 填满） | 384 |

```toml
# torchtitan_npu/models/deepseek_v4/train_configs/deepseek_v4_285b_43layers_4k_128die.toml
[model]
name = "deepseek_v4"
flavor = "285B_debug_43_layers"
converters = ["npu_rms_norm", "npu_permute", "npu_gmm", "npu_rope", "deepseek_v4_sfa", "npu_mhc_pre"]
[training]
global_batch_size = 1024
local_batch_size = 1
seq_len = 4096
num_mtp_modules = 1
[parallelism]
data_parallel_shard_degree = -1          # FSDP 分片度自动填满剩余 die
tensor_parallel_degree = 1               # 不切 TP
pipeline_parallel_degree = 1             # 不切 PP
expert_parallel_degree = 64              # 大 EP（路由专家沿 die 切）
expert_tensor_parallel_degree = 1        # 不开 ETP（TP extend EP）
context_parallel_degree = 1              # 4K 序列无需 CP
```

> ⚠️ 规格说明：技术报告「极简切分」表以 **per-die** 视角写作 FSDP128 + EP128（64 卡 = 128 die），而仓库随附的 4K 训练 toml 取 `expert_parallel_degree=64`（per-card EP，框架内再展开到 die）。两者描述同一份切分，并列保留以忠实于来源。同仓另有 `deepseek_v4_285b_43layers_64k_128die.toml` 把长序列改为 `EP64 + CP16`——CP 仅在长序列开启，且 V4 仅当 `deepseek_v4_sfa` 融合 kernel 使能时才支持 CP（见 `parallelize.py` 的断言）。

**真实拉起命令**（README·启动训练）——所有参与节点同时执行，靠 `CONFIG_FILE` 选规格，节点 IP / 网卡在 `run_train_multinodes.sh` 内按环境改：

```shell
# DeepSeek-V4-Flash 多机 CPT
CONFIG_FILE=./torchtitan_npu/models/deepseek_v4/train_configs/deepseek_v4_285b_43layers_4k_128die.toml \
bash scripts/run_train_multinodes.sh

# DeepSeek-V4-Pro 多机 CPT
CONFIG_FILE=./torchtitan_npu/models/deepseek_v4/train_configs/deepseek_v4_pro_61layers_4k_384die.toml \
bash scripts/run_train_multinodes.sh
```

`run_train_multinodes.sh` 内置 A3 训练关键环境变量（[`scripts/run_train_multinodes.sh`](https://gitcode.com/cann/torchtitan-npu/blob/87221a1beaa55314a1cdb73460346ba3cec0b475/scripts/run_train_multinodes.sh)）：`HCCL_CONNECT_TIMEOUT/HCCL_EXEC_TIMEOUT=7200`、`PYTORCH_NPU_ALLOC_CONF=expandable_segments:True`、`TASK_QUEUE_ENABLE=2`、`STREAMS_PER_DEVICE=32`、`MULTI_STREAM_MEMORY_RESERVE=1`、`NPUS_PER_NODE=16`；Pro 显存吃紧时改用 `max_split_size_mb:32,garbage_collection_threshold:0.6`。

**权重 BF16 转换**（README·模型权重准备）——HF 原始 FP8 权重经 `cann-recipes-train` 的 `convert_model.py` 转 BF16，输出目录须与 toml 的 `initial_load_path` 一致：

```shell
# cann-recipes-train/llm_pretrain/deepseekv4/utils/convert_model.py
python3 convert_model.py \
  --input_fp8_hf_path /data/models/DeepSeek-V4-Flash \
  --output_hf_path   /data/models/DeepSeek-V4-Flash-bf16 \
  --quant_type       bfloat16          # 另支持 w8a8-int / w4a8-mx
```

## 极简分布式并行：纯 FSDP + 大 EP

MoE 大模型里 EP 切分摊薄了路由专家权重，但注意力、共享专家、词嵌入/词表投影等**非专家参数**仍需切分；本实践直接舍弃 TP/PP，用 **纯 FSDP + 大 EP** 兜住非专家参数。下表是 Flash 的内存瓶颈转换（主权重+梯度按混合精度各 4 字节算）：EP 切分后非专家内存占比从 2.8% 飙到 80% 成为新瓶颈，而叠加 FSDP128 后非专家权重+梯度被均分到全部 die，从 59.5GB 压到 **0.465GB**，几乎清零——TorchTitan 初始化后单卡权重内存仅约 8~9GB（约等于 EP 切后的路由专家权重）。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v4/FSDP-vs-TP-PP.png" width="58%"></p>
<p align="center"><sub>图：FSDP vs TP/PP——FSDP 通信不依赖当前层中间结果，可下发到独立通信流与计算异步并发，借 A3 超节点高带宽被计算完全掩盖；TP/PP 通信与关键路径耦合无法掩盖（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·FSDP+EP 极简切分优势）</sub></p>

FSDP 的易用性优势在 DSA 结构上尤为关键：V4 继承 V3.2 的 DSA，其 **Indexer 在前向与 Loss 计算时都要沿 head 维度做 ReduceSum**，该语义决定了无法直接沿 head 切 TP——强行切就得额外引入 AllGather 才能保证 ReduceSum 正确。FSDP 对参数无差异分片 + 异步 AllGather，做到模型结构无感的权重切分，适配上仅一行 `fully_shard`。这套切分机制与 V3.2 的最小化切分共享原理，原理细节与 EP/etp 装配代码下放到 → [fsdp](../../concepts/parallelism/fsdp.md)，FSDP2 零冗余二次分片与 A3 预取掩盖见 [fsdp](../../concepts/parallelism/fsdp.md)。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v4/Indexer-TP.png" width="50%"></p>
<p align="center"><sub>图：DSA Indexer 沿 head 维度 ReduceSum，语义上拒绝 TP head 切分——这是选 FSDP 而非 TP 的硬约束（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·易用性优势）</sub></p>

代码层（`parallelize.py` 的 `apply_moe_ep_tp`）在 `tp_mesh is None or etp_mesh is None` 时对 `moe.experts` 直接用 `ExpertParallel()` 沿 `ep_mesh` 切，即 **TP extend EP**（不开 ETP）；`parallelize_deepseek_v4` 末尾对 `fsdp_enabled or ep_enabled` 调 `apply_fsdp`，路由专家与非专家分别走 `efsdp` / `fsdp` mesh 做二次分片。

### 双通信域 overlap 修复

FSDP128 + EP128 时 FSDP 域与 EP 域均等于全局默认通信域、PyTorch 为二者分配**同一个 ProcessGroup**，FSDP 的 AllGather/ReduceScatter 与 EP 的 AllToAll 被迫串行、暴露到 MoE 关键路径；V4 在初始化阶段对 EP 通信域独立标注，使两域各持 ProcessGroup 在不同 HCCL 流并发，MoE 层通信等待 **10ms → ~3ms、+1.1%** 性能（已反馈 PyTorch/TorchTitan 上游）。该 bug 本质属 FSDP+EP 切分机制——共享 ProcessGroup 的 bug 推导与独立标注修复（bug / bugfix 两图）详见 → [fsdp](../../concepts/parallelism/fsdp.md) §双通信域 overlap。

### 内存卸载 / SwapOptimizer

FSDP2 原生方案里 AdamW 的两个 FP32 动量在前反向期间仍驻留设备。作为 FSDP 的内存补充，本实践参考 MindSpeed 思路在 TorchTitan 中实现 SwapOptimizer：把已被 FSDP 切到单卡的优化器状态进一步卸载到主机内存，仅在权重更新阶段按需换入，并以参数为粒度做「加载—更新—卸载」切片流水重叠。常驻内存从 FSDP 的 16 字节/参数（权重4+梯度4+优化器8）压到 **8 字节/参数**（仅权重+梯度），近乎减半。机制细节 → [swap-optimizer](../../concepts/techniques/swap_optimizer.md)。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v4/Swap-optimizer.png" width="58%"></p>
<p align="center"><sub>图：SwapOptimizer 以参数为粒度切片流水，将串行的加载/更新/卸载重叠执行，降低优化器更新阶段内存峰值（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·内存卸载优化）</sub></p>

## torch.compile + AutoFuse 训练入图

MoE/多模态架构里动态、细粒度的小算子组合成为主流——以 DeepSeek 的 **mHC** 为例，其把 HC 拆成 HcRes / HcPre / HcPost 三段、用双随机矩阵与 Sigmoid 门控保障数学性质，实现上依赖大量细碎 PyTorch op，手写融合 kernel 已跟不上模型迭代速度。torch.compile 捕获 FX 图交 Inductor 做垂直/水平融合；但 NPU 与 GPU 内存架构/计算范式本质不同，CANN 的 **AutoFuse** 在继承 Inductor 流程基础上实现了目标为 Ascend C 的 Schedule & Codegen 后端，把计算图自动映射为高效 NPU 指令。

本训练场景**不开 TP**，各算子计算量本身大、融合后 Kernel Launch 占比极低，静态图无收益空间，故采用**动态图 Eager 模式执行编译后的算子图**（免处理动态 Shape 约束，更简洁），已可取得融合主要收益。AutoFuse 前端**仅加一行代码即可使能**，当前已支持 152 个 LoopIR 表达中的 46 个。训练入图与推理 AutoFuse 的差异（训练侧重 Vector 算子自动融合 / Eager 执行）→ [autofuse-train](../../concepts/techniques/autofuse_train.md)。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v4/AutoFuse.png" width="60%"></p>
<p align="center"><sub>图：AutoFuse 在 Inductor 之上注入架构感知的融合/调度/展开策略，将计算图优化转为 NPU 高效指令序列（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·torch.compile + AutoFuse）</sub></p>

使能 AutoFuse 后整网吞吐收益 **31.8%**，主要来自 AIV 算子融合与 Host-Bound 缓解（Free Time 减少）。典型融合算子收益（净收益时间 s）：

| 融合后算子 | Count | 优化核心 | 净收益 |
|---|---|---|---|
| `autofused_mul_sum` 系列 | 10,232 | 带宽优化：Mul 结果不写回内存，片上直接规约 | 5.5s |
| 基础逐元素融合 (Mul/Add/Div) | ~20 万 | 访存收敛：合并独立乘加除，减少内存访问次数 | 5s |
| `autofused_add_div_expand_mul_pow` | 1,584 | 指令加速：高延迟 Pow 指令化、计算掩盖访存 | 1.6s |
| BroadcastTo 隐式化 | ~3.3 万 | 隐式广播：Stride 逻辑变换消除物理拷贝 | 2.2s |
| `autofused_npu_dtype_cast` 系列 | 14,832 | 调度简化：吸收数万次类型转换、降下发频率 | 0.7s |

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v4/AutoFuse-gain.png" width="60%"></p>
<p align="center"><sub>图：AutoFuse 收益拆解——收益主要来自 AIV 算子融合与 Host-Bound 缓解（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·AutoFuse 收益分析）</sub></p>

## 高性能融合算子

针对 V4 的稀疏注意力核心结构，开发了 4 个训练场景 Ascend C 算子（`converters` 经 `deepseek_v4_sfa` / `npu_mhc_pre` 注入）：

- **LightningIndexer (LI)**：一系列操作得到每 token 的 Top-k 位置索引，供 SAS 作输入；3 阶段 C0(Cube QK+ReLU) / V1(向量计算) / V2(二次分核 Topk)，设计一次 Preload C 提升 C/V 流水并行。推理侧同名算子 → [lightning-indexer](../../../inference/concepts/kernels/lightning_indexer.md)。
- **SparseAttnSharedkv (SAS)**：完成 MQA 形态的稀疏 Attention，按 `cmp_ratio` 支持 SWA / CFA / SCFA 三种；5 阶段 V0(Gather)/C1(QK)/V1(onlineSoftmax+sinks)/C2(PV)/V2(rescale)，Preload 一轮 V0+C1 错开依赖达成 CV 流水并行。正向算子原理与跨域对照 → [sparse-attn-sharedkv](../../../inference/concepts/kernels/sparse_attn_sharedkv.md)。
- **SparseAttnSharedkvGrad (SASG)**：SAS 反向，5 阶段 Gather / Cube12 / Process / Cube345 / Scatter，Preload 一次 Gather+Cube12 达成 CV 流水并行 → [sasg](../../concepts/kernels/sasg.md)。
- **SparseLightningIndexerGradKLLoss (SLIG)**：LI 的 Loss 计算内存开销达序列长度平方级（需算 Main Attention score），SLIG 把 Main Attention score 计算、LI 反向、KL Loss 计算三者融合以省中间内存；5 阶段 V0 / C1 / V1(KLLoss+dW) / C2(dQ) / V2(ScatterAdd dK)，V0 两次 Preload + PingPong 掩盖 C1/C2 → [slig](../../concepts/kernels/slig.md)。

mHC 结构（HcPre/HcPost）的推理侧实现与本页 `npu_mhc_pre` converter 对照 → [mhc-hcpre-hcpost](../../../inference/concepts/kernels/mhc_hcpre_hcpost.md)。

## Benchmark（A3 SuperPods 64 卡）

Flash 在 A3 64 卡上吞吐 **397 → 1100 tokens/p/s**，定制融合算子贡献约 90%、AutoFuse 约 30%。优化后单步耗时构成：计算占绝对主导 **84.68%**（CUBE 27.89% + FA 19.77% + VEC 37.01%），通信 EP 9.56% + FSDP 2.98% = 12.53%，FREE 仅 2.79%，**MFU 28.78%**。Vector 类算子占近 40%，是下一步重计算/AutoFuse 扩面的优化重点。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/figures/deepseek_v4/Total-gain.png" width="60%"></p>
<p align="center"><sub>图：端到端吞吐 397→1100 tokens/p/s 提升瀑布，融合算子 +90%、AutoFuse +30%（<a href="https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·A3 SuperPods 64 卡性能结果）</sub></p>

上游 DeepSeek-V4 优化文档的未来展望（不属于上述性能结果对应的配置）：按需重计算避免对 Vector 算子冗余重计算；扩大 AutoFuse 覆盖；补齐 MC2 / EP 域通算并行；面向 950 支持 FP8、A8W4 与 MxFP8/MxFP4 低精度训练；集成 Muon 优化器。

## Evidence

- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md)（技术报告全文：极简并行 / 双通信域 / SwapOptimizer / AutoFuse 收益拆解 / LI·SAS·SASG·SLIG 算子 / Benchmark）
- [cann-recipes-train](https://gitcode.com/cann/cann-recipes-train/tree/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2) — [`llm_pretrain/deepseekv4/README.md`](https://gitcode.com/cann/cann-recipes-train/blob/d17909ef35e0eee1f5bc81189a12d2abebb0b4c2/llm_pretrain/deepseekv4/README.md)（Flash/Pro 双规格软硬件要求、源码/镜像/容器、数据集、`convert_model.py` BF16 转换、`run_train_multinodes.sh` + `CONFIG_FILE` 拉起命令）
- [`torchtitan_npu/models/deepseek_v4/train_configs/deepseek_v4_285b_43layers_4k_128die.toml`](https://gitcode.com/cann/torchtitan-npu/blob/3ad842122427e8ea8404ed3227caa91e138fb7b7/torchtitan_npu/models/deepseek_v4/train_configs/deepseek_v4_285b_43layers_4k_128die.toml) — Flash 真实并行度（TP1/PP1/EP64/etp1/CP1，DP-shard=-1，GBS1024，seq 4096，num_mtp_modules=1，`converters` 列表，`swap_optimizer=true`（与 `virtual_optimizer` 互斥），AC full，compile model+loss）
- [`torchtitan_npu/models/deepseek_v4/train_configs/deepseek_v4_pro_61layers_4k_384die.toml`](https://gitcode.com/cann/torchtitan-npu/blob/3ad842122427e8ea8404ed3227caa91e138fb7b7/torchtitan_npu/models/deepseek_v4/train_configs/deepseek_v4_pro_61layers_4k_384die.toml) — Pro 真实并行度（EP192，GBS=384，`moe_force_load_balance=true`，`swap_optimizer=true`）
- [`torchtitan_npu/models/deepseek_v4/train_configs/deepseek_v4_285b_43layers_64k_128die.toml`](https://gitcode.com/cann/torchtitan-npu/blob/3ad842122427e8ea8404ed3227caa91e138fb7b7/torchtitan_npu/models/deepseek_v4/train_configs/deepseek_v4_285b_43layers_64k_128die.toml) — 长序列 EP64 + CP16（CP 仅长序列开启）
- [`torchtitan_npu/models/deepseek_v4/parallelize.py`](https://gitcode.com/cann/torchtitan-npu/blob/3ad842122427e8ea8404ed3227caa91e138fb7b7/torchtitan_npu/models/deepseek_v4/parallelize.py) — `parallelize_deepseek_v4` 装配（TP→MoE-EP-TP→CP→AC→compile→FSDP）、`apply_moe_ep_tp` 的 TP-extend-EP（`ExpertParallel()`）、CP 仅当 `deepseek_v4_sfa` 使能、`apply_distributed_indexer_loss_tracking` 全局同步 indexer loss
- [`scripts/run_train_multinodes.sh`](https://gitcode.com/cann/torchtitan-npu/blob/87221a1beaa55314a1cdb73460346ba3cec0b475/scripts/run_train_multinodes.sh) — A3 训练环境变量（HCCL 超时、`expandable_segments`、`TASK_QUEUE_ENABLE=2`、`STREAMS_PER_DEVICE=32`、`NPUS_PER_NODE=16`）

## Links

- [fsdp](../../concepts/parallelism/fsdp.md)（极简切分原理与 EP/etp/FSDP 装配代码，本页并行的承重子页）
- [autofuse-train](../../concepts/techniques/autofuse_train.md)（AutoFuse 训练入图：Eager 执行、Vector 算子自动融合，本页 31.8% 收益来源）
- [sasg](../../concepts/kernels/sasg.md)（SAS 反向算子，本页 4 个定制算子之一）
- [slig](../../concepts/kernels/slig.md)（LI+KLLoss 融合反向算子，与 V3.2 同源、V4 复用）
- [swap-optimizer](../../concepts/techniques/swap_optimizer.md)（优化器状态主机内存卸载，本页 8 字节/参数内存的补充手段）
- [fsdp](../../concepts/parallelism/fsdp.md)（FSDP2 零冗余权重二次分片、A3 超节点预取掩盖）
- [torchtitan](../../concepts/frameworks/torchtitan.md)（承载框架：DTensor / ModelConverter / torch.compile 原生支持）
- [deepseek-v4](../../../inference/concepts/models/deepseek_v4.md)（跨域：同模型的推理部署，与本续训练侧对应）
- [sparse-attn-sharedkv](../../../inference/concepts/kernels/sparse_attn_sharedkv.md)（跨域：SAS 正向算子，本页训练侧 SAS/SASG 与之对照）
- [mhc-hcpre-hcpost](../../../inference/concepts/kernels/mhc_hcpre_hcpost.md)（跨域：mHC HcPre/HcPost 实现，本页 `npu_mhc_pre` converter 对应）
- [lightning-indexer](../../../inference/concepts/kernels/lightning_indexer.md)（跨域：LI 正向算子，训练侧 SLIG 是其反向）
- [atlas-a3](../../../inference/concepts/platforms/atlas_a3.md)（跨域：64/192 卡集群与高带宽支撑 FSDP 通信掩盖的硬件平台）
- [muon-optimizer](../../concepts/techniques/muon_optimizer.md)（V4 续训未来工作：集成 Muon 优化器）
- [training-debug-observability](../../concepts/techniques/training_debug_observability.md)（HCCL Flight Recorder / Profiling 调试可观测）
- [virtual-optimizer](../../concepts/techniques/virtual_optimizer.md)（与本页所用 SwapOptimizer 互斥的另一套优化器显存卸载方案，基于 Ascend 驱动虚拟内存、不改训练代码；本页两份 4k 主配置未启用）
- [smla](../../concepts/kernels/smla.md)（V4 稀疏 MLA 训练融合算子 npu_smla）
- [deepseek-v32-mtp-train](../../concepts/modules/deepseek_v32_mtp_train.md)（V4 续训 num_mtp_modules=1 的 MTP 训练）
- [mhc-train](../../concepts/kernels/mhc_train.md)（跨框架：MindSpeed-LLM 用 Triton-on-Ascend 实现的同结构 mHC 训练正反向算子，与本页 torchtitan-npu npu_mhc_pre converter 路径并列）

<!-- cannbot:related:start -->
## 相关

- [SASG（SparseAttnSharedkvGrad，DeepSeek-V4 SAS 训练反向算子）](../../concepts/kernels/sasg.md)（`related`）：“SASG 把 SAS 正向五阶段反传，主流程同样可分 **5 个阶段，依次为 Gather、Cube12、Process、Cube345、Scatter**：”与“- **SparseAttnSharedkvGrad (SASG)**：SAS 反向，5 阶段 Gather / Cube12 / Process / Cube345 / Scatter，Preload 一次 Gather+Cube12 达成 CV 流水并行 → ［sasg］(../../concepts/kernels/sasg.md)。”。kernel 卡展开 SASG 五阶段，续训练指南把同一五阶段算子列为 V4 定制训练组件。
- [SLIG（SparseLightningIndexerGradKLLoss，DSA 训练反向算子）](../../concepts/kernels/slig.md)（`related`）：「**定制算子**」（针对 DSA / mHC 稀疏结构的 SAS / SASG / LI / SLIG 融合算子）；真正的算子调用 `torch_npu.npu_sparse_lightning_indexer_grad_kl_loss`、三路梯度 + loss、`grad_output［0］` 缩放、loss tracker 记录，全部在 `backward`。；配方列出 SLIG，算子卡明确其反向下发与 KL loss 融合时机，直接补齐训练图实现。
- [训练入图：torch.compile + Inductor + AutoFuse（Bypass Triton → AutoFuse）](../../concepts/techniques/autofuse_train.md)（`related`）：DeepSeek-V4 通过 torch.compile + AutoFuse 训练入图，使能后 Flash 整网吞吐收益为 **31.8%**；复用该配置时需同时满足 AutoFuse 的入图约束。
<!-- cannbot:related:end -->
