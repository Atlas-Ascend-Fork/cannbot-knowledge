---
type: Guide
title: vLLM Ascend CP 拓扑：PCP 与 DCP 的 rank 复用及缓存传输
description: 按中文资料核对 CP 的 PCP/DCP 拓扑、num_key_value_heads 与 GQA 独立/叠加条件，区分 1P1D 节点、整模型的
  EP 与 TP 模块及 TTFT、TPOT 初始排队口径。
tags:
- task.implementation
- topic.parallelism
- topic.kv_cache
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/context_parallel.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/context_parallel.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/user_guide/feature_guide/context_parallel.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/context_parallel.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ascend_config.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/features/long_sequence_context_parallel_single_node.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/tutorials/features/long_sequence_context_parallel_multi_node.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/tutorials/features/ray.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/cp/overview.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/cp/head-tail-style.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/cp/device_world.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/cp/chunkedprefill.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/cp/pcp-prefill.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/cp/pcp-decode.png
  role: supporting
created_at: '2026-10-29T09:40:13Z'
updated_at: '2026-11-03T01:29:41Z'
platforms:
- a2
- a3
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend CP 拓扑：PCP 与 DCP 的 rank 复用及缓存传输

## 范围和拓扑产物

来源对 A2/A3/950 的 MLA/GQA/SFA DCP 给出支持矩阵，PCP 标为实验。先记录 attention backend、TP、PCP、DCP、DP、PP、物理 ranks 和 connector；不能把后端逐项支持当成任意功能组合。

PCP 新增 ranks，world_size_with_pcp=PCP×original_world_size，分摊长 Prefill token。DCP 复用 PCP/TP ranks，分摊历史 KV，不进一步增加 world size。PCP=1 的 DCP 与 PCP>1 的叠加拓扑适用不同公式。

## 先分场景验证尺寸

| 场景 | 固定指南约束 |
| --- | --- |
| PCP=1，MLA DCP | TP>=DCP 且 TP%DCP=0 |
| PCP=1，稀疏 SFA DCP | DCP=TP |
| PCP=1，GQA DCP | TP//num_kv_heads>=DCP 且该商可被 DCP 整除 |
| PCP>1，MLA/SFA | DCP=PCP 或 DCP=PCP×TP |
| PCP>1，GQA | 仅 DCP=PCP |

例如 MLA/SFA TP2+PCP2+DCP4 可成立；GQA 不能沿用。KV transfer/pooling 时 cp_kv_cache_interleave_size 应等于实际 block_size，不盲抄默认128。

## 关键组合和失效边界

PD 仅 P 端开 PCP，D 端 PCP=1。PCP+PP 使用受支持模型的 MooncakeConnectorV2；V1/Hybrid 与 PCP 时不支持 PP，Hybrid 也不支持 DCP。PCP pooling 仅 AscendStoreConnector 非 layerwise。PCP 不支持 FULL，但其他图模式仍要按 backend 验证；encoder-decoder、LoRA、adaptive verification 不支持，动态 draft 长度在验证范围外。

PCP 下 target 用配置拓扑，draft 每个 PCP rank 复制、逻辑 PCP=1；方法按 backend 选择 MTP/Eagle3/DSpark，不给 draft 再扩大 PCP。embedding/LM-head 的 PCP 权重分片默认开；SFA/DSA 特定 O-proj 分片默认开但不适配时告警降级，且与同模块 fine-grained TP 冲突。

## 验收与回退

先 eager、无投机/传输验证 token、位置、KV 布局和精度，再分别加图及 connector；记录实际降级，比较 TTFT、decode 吞吐、缓存容量和通信。多模态位置风险另见[PCP 位置诊断](../../runbooks/precision/pcp_multimodal_noncontiguous_position.md)。拓扑错误、KV 不一致或精度失败时撤回新增维度。本次没有运行多卡测试。


## 进入实现前固定元数据契约

新backend需分别核对全局request、本地query和汇聚KV的顺序；PCP head-tail的恢复映射必须在logits/draft消费前完成。当前虚拟块只乘DCP，不再乘PCP；不能把旧版SFA指南的公式带入此commit。主KV分片与indexer复制也不是同一内存缩放。映射公式、rank顺序、空分片和LSE合并见[当前CP机制](../../concepts/frameworks/vllm_ascend_cp_cache_mapping.md)。


## 中文拓扑资料与当前配置分别裁决

用户context_parallel.po的56条有效译文有44条匹配当前英文、12条差异，设计PO另有11条差异。当前英文移除PCP仅MRv2、旧DSA-CP独立小节和迁移文字；同时DSpark的PCP方法说明补入SFA。文档移除Runner限定不单独证明每个Runner都可运行，仍沿目标模型和实际选路验收。

所读AscendConfig局部代码仍显式拒绝enable_dsa_cp与PCP>1同开，并拒enable_dsa_cp与use_v2_model_runner同开。不能因当前CP指南不再介绍旧DSA-CP就声称配置键已删除，也不能把它改名PCP或跳过验证。旧迁移TP=N/PCP=1改TP=1/PCP=N在其假设下可保留模型worker数量，却不证明权重分片、量化、图、通信或性能等价。

当前PCP基础表按MLA/GQA/SFA/DSA/DSA V4.1分别列出MTP/Eagle3/DSpark、MLAPO、图、PD及非layerwise池化的组合。SFA也列DSpark，不把旧摘要漏项当当前不支持；FULL不支持仍不能解释成PIECEWISE/FULL_AND_PIECEWISE/FULL_DECODE_ONLY任一组合全已通过。目标用PCP、每rank draft逻辑PCP=1，与draft是否支持DCP分开取证。

enable_pcp_embedding_lmhead_weight_sharding默认行为、enable_pcp_o_proj_weight_sharding在SFA/DSA特定投影的降级warning，与同模块fine-grained TP互斥应按最终有效值判断。无query的rank仍须参加必需通信；PCP+DCP复制短prefill和decode query的路径不能沿用PCP-only round-robin owner假设。

cp_kv_cache_interleave_size声明默认1、SFA有效按block_size处理、KV transfer要求显式等于实际block_size是不同层次；128只是该指南示例的block-size值。Standalone与stacked DCP约束不要混用，rank逻辑顺序、slot和三图边界见[CP缓存机制](../../concepts/frameworks/vllm_ascend_cp_cache_mapping.md)。源码与译文检查不当多卡/NPU或Agent结果，未执行外部RFC/脚本。


## 两份历史长序列教程不能代替当前CP矩阵

long_sequence_context_parallel_single_node.po的35条与long_sequence_context_parallel_multi_node.po的44条同名英文均已不存在。完整阅读后作为历史recipe线索，与当前CP用户指南逐项对照，不恢复成当前可执行命令。单机页是Qwen3-235B-A22B W8A8、Atlas800 A3 64G×16的PD共置例；多机页是DeepSeek-V3.1 W8A8、三物理机组成一个跨机P实例加一个D实例的1P1D例。逻辑P/D实例数、物理节点数、NPU设备/die与实际worker数分别记录。

多机旧页的“A3支持、A2未来支持”不能覆盖当前DCP的A2/A3/950 MLA/GQA/SFA矩阵；PCP依旧标实验，不能反向按DCP表承诺全部PCP组合。旧例选择D端不启DCP是考虑其通信/小算子代价的workload选择，不是DCP功能禁令。

历史单机给TP可整除DCP及TP//KV-head上限，多机给TP可整除DCP且DCP<=TP；这些不能用于所有backend或PCP叠加。当前PCP=1时GQA另需(TP//num_key_value_heads)%DCP=0；PCP>1时GQA只DCP=PCP，而MLA/SFA可DCP=PCP或PCP×TP。先选分支，再算物理world，不能将TP×PCP再乘DCP。

## 历史参数、权重与指标的保留边界

旧RoPE段仅列v0.12前rope_scaling与v0.12的hf-overrides/rope_parameters，不能当v0.32或任意模型128k开关。旧DeepSeek例要求把config.json的torch_dtype由float16改bfloat16，也不表示权重字节已转换、量化元数据已匹配或精度已验收；先固定实际checkpoint和模型解析路径。

旧说明“纯EP或纯TP”不能被解释成整模型不能同时配置TP和EP：当前[Ray示例](../deployment/vllm_ascend_ray_multinode_bootstrap.md)并列--tensor-parallel-size和--enable-expert-parallel。具体MoE权重切分、expert group和attention/非MoE TP分别核对，不用旧一句话推全部算子组。

旧waiting同时计入TTFT/TPOT的说明须按所用benchmark公式核对，记录initial queue、TTFT、inter-token gap、输出token数；不凭概括预测TPOT收益。util×HBM-peak也只是旧简化解释，不代替目标版本的权重、activation/profile、图和实际KV分配审计。max-num-seqs×DP>=concurrency是减少排队的一种负载选择，不是正确性硬约束或吞吐单调定律。

历史17.36s/20.7s的AISBench TTFT、128k部署和benchmark输出均是来源参考，缺同一模型/负载/版本配对时不可比较为CP加速比，更不是本次NPU结果。Flashcomm1、recompute_scheduler_enable、图capture sizes及quantization旧参数按各自当前指南与最终配置核对；不自动照搬或下载/修改权重。

旧kv_port到kv_port+num_chips与engine_id唯一的简写不足以推出当前connector端口范围、是否含末端或TCP不冲突；用实际connector版本/拓扑核算。当前PCP只P端、D PCP1、非layerwise池化与interleave=实际block_size条件保持，本批未分配端口、改环境或做多机验收。

## CP图示的顺序与版本边界

固定源码保留的六张CP图用于拆开逻辑维度和数据流：head-tail示意将早/晚token组合分配以平衡因果attention负载，而缓存图采用交错slot；Q恢复顺序与KV存放顺序不能混成一张连续有效区。PCP增加的分组与TP内复用的DCP子组分别核算，不把图中所有维度相乘当物理world size。

Prefill图分别画出当前KV在PCP组汇聚、MLA压缩KV与GQA head分工；chunked-prefill图还区分当前贡献与历史KV贡献，最后按O/LSE合并。Decode图给出DCP AllGather、局部attention、DCP All2All、PCP AllGather和correct_attn的示意链。它们帮助检查通信域、结果head轴和LSE归属，不证明每个backend均采用同一实现或性能更优。

图片使用TP6/PCP2/DCP3等示例记号，与本卡当前PCP叠加约束的写法不同；其中local子组、配置因子与旧版本布局必须先对应，不能直接当可执行CLI。图没有解除现有backend、图、connector与draft门禁；实际slot/restore/shape仍沿当前源码合同核对。本次仅阅读图示，没有运行多卡。
