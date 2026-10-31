---
type: Guide
title: DeepSeek-V4 Flash A3 当前续训练入口与优化案例
description: 当前 Flash A3 配置函数、EP128/FSDP128、Muon/Swap、MTP 默认值、HF 检查点和显式 override；区分来源报告的吞吐案例。
tags:
- task.implementation
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/examples/deepseek_v4/deepseek_v4_flash_cpt_4k_a3.sh
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/scripts/run_train_multinodes.sh
  role: supporting
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v4/config_registry.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/llm_pretrain/deepseekv4/README.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-10-29T15:39:14Z'
platforms:
- a3
---

# DeepSeek-V4 TorchTitan-NPU + AutoFuse 极简续训练（Flash 64 卡 / Pro 192 卡 A3）

## Summary

DeepSeek-V4 在昇腾 A3 上做**续训练（CPT）**。当前 Recipes 优化报告记录的案例包含两个规格：**DeepSeek-V4-Flash**（285B / 43 层，最小 **8 机 64 卡 A3** = 128 die）与 **DeepSeek-V4-Pro**（61 层，最小 **24 机 192 卡 A3** = 384 die）。整套方案围绕三条主线——「**极简并行**」（纯 FSDP + 大 EP，舍弃 TP/PP）、「**自动融合**」（torch.compile + Ascend C AutoFuse 训练入图）、「**定制算子**」（针对 DSA / mHC 稀疏结构的 SAS / SASG / LI / SLIG 融合算子）。4K 序列 BF16 + MTP1 训练下，Flash 在 A3 SuperPods 64 卡集群上吞吐从初始 397 tokens/p/s 提升到 **1100 tokens/p/s**，其中定制融合算子与 AutoFuse 分别贡献约 90% 与 30% 的吞吐增益。该实践对应的推理部署见跨域页 [deepseek-v4](../../../inference/concepts/models/deepseek_v4.md)。

整体软件栈自顶向下为 TorchTitan → TorchTitan-NPU 插件 → TorchInductor → CANN AutoFuse：

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v4/Architecture.png" width="62%"></p>
<p align="center"><sub>图：四层软件架构——TorchTitan 提供 FSDP 等 PyTorch Native 并行，TorchTitan-NPU 插件做昇腾通信/算子适配，Inductor 继承 torch.compile 图捕获，AutoFuse 作 Ascend C Codegen 后端（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·引言）</sub></p>

## 当前 Flash A3 训练入口

当前 TorchTitan-NPU 使用配置函数和分层 CLI，旧 train_configs/*.toml、CONFIG_FILE、deepseek_v4_sfa/npu_mhc_pre converter 已移除。Recipes README 中仍有旧分支及 TOML 命令，不能与当前源码混用；以下以当前实际存在的 Flash A3 wrapper 为准。

```bash
TORCHINDUCTOR_NPU_BACKEND=ascendc \
NODE_IPS=<所有节点的逗号分隔IP> \
HF_ASSETS_PATH=/path/to/DeepSeekV4_tokenizer \
CKPT_INIT_LOAD_PATH=/path/to/initial_hf_checkpoint \
CKPT_SAVE_LOAD_PATH=/path/to/output \
bash examples/deepseek_v4/deepseek_v4_flash_cpt_4k_a3.sh \
  --training.steps 5
```

在所有参与节点使用同一 NODE_IPS 顺序，按实际网卡设置 Network_Interface/LOCAL_HOST。示例默认 8 节点、每节点 16 个逻辑进程；进程数与物理卡数不同，启动前按设备映射核对。它选择模块 torchtitan_npu.models.deepseek_v4、配置 deepseek_v4_flash，TP1/PP1/EP128/CP1/DP_SHARD128，DP_REPLICATE=world/(128×CP)。不能把旧 Flash EP64、旧 Pro TOML 或旧卡/die 计数自动套到此配置。

当前 wrapper 默认序列4096、MBS1、GBS1024、100步、per_doc_alignment=128×CP；编译启用 model/inductor，默认 Muon lr=1e-5，并选择 swap_optimizer override。它未显式请求 MTP；配置函数 num_mtp_layers 默认0，旧报告的 MTP1 不是当前命令默认值。

算子通过显式 override 选择 RMSNorm、LI、SMLA、MHC Pre/Post 和 token dispatcher，RoPE 另有当前 override。USE_GOLDEN=1 使用模型参考注意力组合，不关闭全部训练功能。需要 loss 编译时追加 --compile.components model loss。

检查点默认 enable+load-only，initial-load-in-hf：已有输出目录中的有效 step-* 优先恢复，冷启动时应使用新目录。load-only 不会保存新检查点；需保存时显式关闭 load-only，并配置保存周期。Tokenizer 路径与初始权重路径各自独立。

多机 launcher 当前默认 TASK_QUEUE_ENABLE=2、STREAMS_PER_DEVICE=32、MULTI_STREAM_MEMORY_RESERVE=1、NGPU=8（该 wrapper 覆盖为16），并导出默认 AscendC 后端。启动前核对实际最终配置，不使用旧环境变量表。

## 以下优化案例的适用范围

下文图示和数值来自当前 Recipes 仍保留的优化报告，描述 A3 64 卡、BF16、4K、MTP1 的特定实验。它们不等于上述当前 Muon/MTP0 配置的复测结果，也不证明当前 Pro 完整训练已验证。不同阶段的增益百分比不能相加。当前实现细节以相应知识卡和本页最新源代码为准。

## 极简分布式并行：纯 FSDP + 大 EP

MoE 大模型里 EP 切分摊薄了路由专家权重，但注意力、共享专家、词嵌入/词表投影等**非专家参数**仍需切分；本实践直接舍弃 TP/PP，用 **纯 FSDP + 大 EP** 兜住非专家参数。下表是 Flash 的内存瓶颈转换（主权重+梯度按混合精度各 4 字节算）：EP 切分后非专家内存占比从 2.8% 飙到 80% 成为新瓶颈，而叠加 FSDP128 后非专家权重+梯度被均分到全部 die，从 59.5GB 压到 **0.465GB**，几乎清零——TorchTitan 初始化后单卡权重内存仅约 8~9GB（约等于 EP 切后的路由专家权重）。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v4/FSDP-vs-TP-PP.png" width="58%"></p>
<p align="center"><sub>图：FSDP vs TP/PP——FSDP 通信不依赖当前层中间结果，可下发到独立通信流与计算异步并发，借 A3 超节点高带宽被计算完全掩盖；TP/PP 通信与关键路径耦合无法掩盖（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·FSDP+EP 极简切分优势）</sub></p>

FSDP 的易用性优势在 DSA 结构上尤为关键：V4 继承 V3.2 的 DSA，其 **Indexer 在前向与 Loss 计算时都要沿 head 维度做 ReduceSum**，该语义决定了无法直接沿 head 切 TP——强行切就得额外引入 AllGather 才能保证 ReduceSum 正确。FSDP 对参数无差异分片 + 异步 AllGather，做到模型结构无感的权重切分，适配上仅一行 `fully_shard`。这套切分机制与 V3.2 的最小化切分共享原理，原理细节与 EP/etp 装配代码下放到 → [fsdp](../../concepts/parallelism/fsdp.md)，FSDP2 零冗余二次分片与 A3 预取掩盖见 [fsdp](../../concepts/parallelism/fsdp.md)。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v4/Indexer-TP.png" width="50%"></p>
<p align="center"><sub>图：DSA Indexer 沿 head 维度 ReduceSum，语义上拒绝 TP head 切分——这是选 FSDP 而非 TP 的硬约束（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·易用性优势）</sub></p>

代码层（`parallelize.py` 的 `apply_moe_ep_tp`）在 `tp_mesh is None or etp_mesh is None` 时对 `moe.experts` 直接用 `ExpertParallel()` 沿 `ep_mesh` 切，即 **TP extend EP**（不开 ETP）；`parallelize_deepseek_v4` 末尾对 `fsdp_enabled or ep_enabled` 调 `apply_fsdp`，路由专家与非专家分别走 `efsdp` / `fsdp` mesh 做二次分片。

### 双通信域 overlap 修复

FSDP128 + EP128 时 FSDP 域与 EP 域均等于全局默认通信域、PyTorch 为二者分配**同一个 ProcessGroup**，FSDP 的 AllGather/ReduceScatter 与 EP 的 AllToAll 被迫串行、暴露到 MoE 关键路径；V4 在初始化阶段对 EP 通信域独立标注，使两域各持 ProcessGroup 在不同 HCCL 流并发，MoE 层通信等待 **10ms → ~3ms、+1.1%** 性能（该固定报告计划后续向 PyTorch/TorchTitan 上游反馈）。该 bug 本质属 FSDP+EP 切分机制——共享 ProcessGroup 的 bug 推导与独立标注修复（bug / bugfix 两图）详见 → [fsdp](../../concepts/parallelism/fsdp.md) §双通信域 overlap。

### 优化报告的 SwapOptimizer 机制与配置差异

FSDP2 原生方案里 AdamW 的两个 FP32 动量在前反向期间仍驻留设备。固定优化报告介绍了参考 MindSpeed 思路实现的 SwapOptimizer；该机制说明不代表本卡两份 （当前来源） TOML 已启用它：把已被 FSDP 切到单卡的优化器状态进一步卸载到主机内存，仅在权重更新阶段按需换入，并以参数为粒度做「加载—更新—卸载」切片流水重叠。常驻内存从 FSDP 的 16 字节/参数（权重4+梯度4+优化器8）压到 **8 字节/参数**（仅权重+梯度），近乎减半。上述字节数是报告对 Swap 路径的参数化估算，不是这两份 Virtual 配置的独立显存测量。机制细节 → [swap-optimizer](../../concepts/techniques/swap_optimizer.md)。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v4/Swap-optimizer.png" width="58%"></p>
<p align="center"><sub>图：SwapOptimizer 以参数为粒度切片流水，将串行的加载/更新/卸载重叠执行，降低优化器更新阶段内存峰值（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·内存卸载优化）</sub></p>

## torch.compile + AutoFuse 训练入图

MoE/多模态架构里动态、细粒度的小算子组合成为主流——以 DeepSeek 的 **mHC** 为例，其把 HC 拆成 HcRes / HcPre / HcPost 三段、用双随机矩阵与 Sigmoid 门控保障数学性质，实现上依赖大量细碎 PyTorch op，手写融合 kernel 已跟不上模型迭代速度。torch.compile 捕获 FX 图交 Inductor 做垂直/水平融合；但 NPU 与 GPU 内存架构/计算范式本质不同，CANN 的 **AutoFuse** 在继承 Inductor 流程基础上实现了目标为 Ascend C 的 Schedule & Codegen 后端，把计算图自动映射为高效 NPU 指令。

本训练场景**不开 TP**，各算子计算量本身大、融合后 Kernel Launch 占比极低，静态图无收益空间，故采用**动态图 Eager 模式执行编译后的算子图**（仍需满足动态图捕获与后端 shape 约束），已可取得融合主要收益。报告阶段列出的覆盖率不作为当前编译器覆盖率；当前启用方式使用两级 backend 和 compile 配置。训练入图与推理 AutoFuse 的差异（训练侧重 Vector 算子自动融合 / Eager 执行）→ [autofuse-train](../../concepts/techniques/autofuse_train.md)。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v4/AutoFuse.png" width="60%"></p>
<p align="center"><sub>图：AutoFuse 在 Inductor 之上注入架构感知的融合/调度/展开策略，将计算图优化转为 NPU 高效指令序列（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·torch.compile + AutoFuse）</sub></p>

使能 AutoFuse 后整网吞吐收益 **31.8%**，主要来自 AIV 算子融合与 Host-Bound 缓解（Free Time 减少）。典型融合算子收益（净收益时间 s）：

| 融合后算子 | Count | 优化核心 | 净收益 |
|---|---|---|---|
| `autofused_mul_sum` 系列 | 10,232 | 带宽优化：Mul 结果不写回内存，片上直接规约 | 5.5s |
| 基础逐元素融合 (Mul/Add/Div) | ~20 万 | 访存收敛：合并独立乘加除，减少内存访问次数 | 5s |
| `autofused_add_div_expand_mul_pow` | 1,584 | 指令加速：高延迟 Pow 指令化、计算掩盖访存 | 1.6s |
| BroadcastTo 隐式化 | ~3.3 万 | 隐式广播：Stride 逻辑变换消除物理拷贝 | 2.2s |
| `autofused_npu_dtype_cast` 系列 | 14,832 | 调度简化：吸收数万次类型转换、降下发频率 | 0.7s |

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v4/AutoFuse-gain.png" width="60%"></p>
<p align="center"><sub>图：AutoFuse 收益拆解——收益主要来自 AIV 算子融合与 Host-Bound 缓解（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·AutoFuse 收益分析）</sub></p>

## 高性能融合算子

针对 V4 的稀疏注意力核心结构，开发了 4 个训练场景 Ascend C 算子（`converters` 经 `deepseek_v4_sfa` / `npu_mhc_pre` 注入）：

- **LightningIndexer (LI)**：一系列操作得到每 token 的 Top-k 位置索引，供 SAS 作输入；3 阶段 C0(Cube QK+ReLU) / V1(向量计算) / V2(二次分核 Topk)，设计一次 Preload C 提升 C/V 流水并行。推理侧同名算子 → [lightning-indexer](../../../inference/concepts/kernels/lightning_indexer.md)。
- **SparseAttnSharedkv (SAS)**：完成 MQA 形态的稀疏 Attention，按 `cmp_ratio` 支持 SWA / CFA / SCFA 三种；5 阶段 V0(Gather)/C1(QK)/V1(onlineSoftmax+sinks)/C2(PV)/V2(rescale)，Preload 一轮 V0+C1 错开依赖达成 CV 流水并行。正向算子原理与跨域对照 → [sparse-attn-sharedkv](../../../inference/concepts/kernels/sparse_attn_sharedkv.md)。
- **SparseAttnSharedkvGrad (SASG)**：SAS 反向，5 阶段 Gather / Cube12 / Process / Cube345 / Scatter，Preload 一次 Gather+Cube12 达成 CV 流水并行 → [sasg](../../concepts/kernels/sasg.md)。
- **SparseLightningIndexerGradKLLoss (SLIG)**：LI 的 Loss 计算内存开销达序列长度平方级（需算 Main Attention score），SLIG 把 Main Attention score 计算、LI 反向、KL Loss 计算三者融合以省中间内存；5 阶段 V0 / C1 / V1(KLLoss+dW) / C2(dQ) / V2(ScatterAdd dK)，V0 两次 Preload + PingPong 掩盖 C1/C2 → [slig](../../concepts/kernels/slig.md)。

mHC 结构（HcPre/HcPost）的推理侧实现与本页 `npu_mhc_pre` converter 对照 → [mhc-hcpre-hcpost](../../../inference/concepts/kernels/mhc_hcpre_hcpost.md)。

## Benchmark（A3 SuperPods 64 卡）

Flash 在 A3 64 卡上吞吐 **397 → 1100 tokens/p/s**，定制融合算子贡献约 90%、AutoFuse 约 30%。优化后单步耗时构成：计算占绝对主导 **84.68%**（CUBE 27.89% + FA 19.77% + VEC 37.01%），通信 EP 9.56% + FSDP 2.98% = 12.53%，FREE 仅 2.79%，**MFU 28.78%**。Vector 类算子占近 40%，是下一步重计算/AutoFuse 扩面的优化重点。

<p align="center"><img src="https://raw.gitcode.com/cann/cann-recipes-train/raw/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/figures/deepseek_v4/Total-gain.png" width="60%"></p>
<p align="center"><sub>图：端到端吞吐 397→1100 tokens/p/s 提升瀑布，融合算子 +90%、AutoFuse +30%（<a href="https://gitcode.com/cann/cann-recipes-train/blob/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md">DeepSeek-V4 优化文档</a>·A3 SuperPods 64 卡性能结果）</sub></p>

当前主线已经包含 Muon、A5 低精度、MTP 与新 CP 配置，不再将报告的未来展望作为当前待实现功能清单。精度和吞吐应在实际选定配置上重新验证，本次未执行硬件训练。

## Evidence

- [deepseek_v4_flash_cpt_4k_a3.sh](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/examples/deepseek_v4/deepseek_v4_flash_cpt_4k_a3.sh)（primary）
- [run_train_multinodes.sh](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/scripts/run_train_multinodes.sh)（supporting）
- [config_registry.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v4/config_registry.py)（supporting）
- [deepseek-v4_torchtitan_npu_autofuse.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/docs/llm_pretrain/deepseek-v4_torchtitan_npu_autofuse.md)（supporting）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-train/532c60c5a3fd8ac84c207ab29be241a88b6eb6ba/llm_pretrain/deepseekv4/README.md)（supporting）

## Links

- [FSDP 与 EP](../../concepts/parallelism/fsdp.md)
- [训练 AutoFuse](../../concepts/techniques/autofuse_train.md)
- [当前 SMLA](../../concepts/kernels/smla.md)
- [Swap 优化器](../../concepts/techniques/swap_optimizer.md)
- [MTP 配置](../../concepts/modules/deepseek_v32_mtp_train.md)
- [Muon](../../concepts/techniques/muon_optimizer.md)
- [检查点](../../concepts/techniques/checkpoint_dcp_hf.md)
