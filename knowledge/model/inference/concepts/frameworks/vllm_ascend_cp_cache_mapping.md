---
type: Concept
title: vLLM Ascend CP：虚拟块、请求布局与分片 Attention 合并
description: 依据CP中文设计与原图，解释0 or 1当前写入与历史缓存的区别，区分sparse和request块表范围，核对交织rank、indexer复制与LSE合并。 补充strided ND MLA局部行读取的device长度、8行尾tile与TND输出布局边界。
tags:
- task.design
- topic.parallelism
- topic.kv_cache
- topic.attention
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/context_parallel.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/context_parallel.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/context_parallel.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/cp/blocktable.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/cp/dcp-prefill.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/assets/cp/dcp-decode.png
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/paged_mla_cache_read.py
  role: implementation
created_at: '2026-10-29T11:00:26Z'
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
      parallelism:
        all_of:
        - cp
updated_at: '2026-11-03T05:09:40Z'
aliases:
- try_load_strided_mla_cache
- load_mla_cache_rows_by_slots
---

# vLLM Ascend CP：虚拟块、请求布局与分片 Attention 合并


## 范围与版本

本卡面向固定 ceac1a2b 的 MLA/GQA/SFA CP 实现；平台来自配套功能指南的 A2/A3/950 功能矩阵，各 backend 和组合须遵守[拓扑指南](../../guides/integration/vllm_ascend_context_parallel_topology.md)。它与[通用 CP 概念](../parallelism/context_parallel.md)中的 SGLang 路径不同，也不能覆盖[旧版 SFA 跨组汇聚](../../guides/integration/sfa_dsa_cp_cross_group_kv_allgather.md)所固定的历史实现。

## rank 与虚拟块

worker 数为 DP×PP×PCP×TP，DCP 复用已有 rank。有效物理块大小 B、DCP 大小 d、interleave I 下，虚拟块容纳 B×d 个 token，PCP 不再乘入虚拟块大小。token x 的虚拟块编号为 x//(B×d)，块内偏移为 x%(B×d)；连续 I 个 token 为一交织单元，该单元序号对 d 取余得到 owner DCP rank。B 必须被 I 整除。

设计默认 I=1；SFA 要核对有效块大小，KV transfer/pooling 要显式 I=B，不能把某个启动脚本中的128当通用默认。TP2、PCP2 的网格若两行为[0,1]、[2,3]，PCP组为[0,2]与[1,3]；叠加完整DCP组的顺序为[0,2,1,3]，通信元数据必须使用真实组内顺序。

## 三种顺序分别维护

PCP 的 head-tail 切分将输入补齐为2×PCP个 chunk，rank r 取第r与第(2×PCP-1-r)块，保存原始位置和恢复映射以平衡因果 Attention。短 prefill 在 PCP+DCP 下可复制，不能假定每个请求必然被均分成非空片。

全局请求顺序、本地 query 顺序、汇聚后的 KV 顺序不同。AscendPCPAttentionContext 的 restore maps 应贯穿 attention 和输出恢复；hidden states 在 logits/draft 消费前恢复。DCPMetadataBuilderMixin 与 DCPImplMixin 复用 v1 builder 的基础真值，避免重新实现请求分类、padding 或 mask 后产生另一套语义。

## Decode 和稀疏缓存

PCP>1、DCP=1 时 decode 请求轮转分配 owner，完整 verify query 留在 owner，其他 rank 仍参与必需 collective 和 KV 同步；不能因本地 query 为空就退出全组通信。叠加 PCP+DCP 时 query 复制到组内，主 KV 按本地分片求 partial attention。

若分片输出为 O_j、log-sum-exp 为 L_j，先 m=max(L_j)，再以 exp(L_j-m) 加权并归一合并 O_j，不能直接平均局部输出。空分片的 LSE 与输出中性处理见[现有精度诊断](../../runbooks/precision/cp_dcp_online_softmax_merge_mask_out_not_only_lse.md)。

GLM-5.2 SFA 等路径中 indexer KV 复制而主 KV 分片；global topk 索引需映射到本地物理块。prefill/mixed 在 cache write 后汇聚有效紧凑块，decode 用 query/局部 attention/LSE 合并。indexer 内存不会按主 KV 的 DCP 分片比例缩小。

验收要分别保存 global/local query 长度、position、slot mapping、block table、restore map、topk 与 collective 顺序，并对无本地 query、非整块、跨 chunk 与 speculative verify 做 eager 对照。本次未运行分布式或精度测试。


## 中文CP设计与三个图示的边界

设计context_parallel.po的71条有效译文有60条msgid匹配当前英文，11条有差异。旧local_block_index在当前改名interleave_index，原式是交织单元序号，不能把它当本rank物理block编号；owner仍按该序号对DCP大小取余。旧MRv2-only PCP、独立DSA-CP说明及相关文件标签不完整反映当前英文，删除叙述不等于已验证所有Runner/路径。

blocktable.png画四个逻辑DCP rank：token interleave=1时tok0/1/2/3分属rank0/1/2/3；block interleave=4时tok0–3归rank0，tok4–7归rank1，之后按组轮转。这是交织粒度示意，不证明实际block size、物理拓扑或world-rank顺序；TP×PCP完整组的[0,2,1,3]仍须按真实映射处理。

只有owner写当前token，非owner和padding使用PAD_SLOT_ID=-1跳过KV写入；不能把通用玩具输入示例的block0占位规则搬到该路径。PCP不额外乘入虚拟块大小，模型worker数量也不等于所有控制/辅助进程数量。

dcp-prefill.png区分MLA历史KV all-gather/reorg与GQA Q-head all-gather/local attention，并分别通过query/history的输出和LSE合并。dcp-decode.png明确TP=6、DCP=3、Q seq=1；其中KV Cache“0 or 1”描述本step的新写入，不是历史缓存容量。单query图不证明多token因果、SFA、PCP堆叠或任意GQA head组合；独立SFA DCP要求DCP=TP，不能照图配TP6/DCP3。

当前SFA prefill/mixed叙述是当前层写入后按request block table引用的KV块压紧并all-gather，旧译文说“sparse block table”；不能据旧词把传输量估成只搬indexer最终top-k。Indexer复制与主SFA KV分片依然是两种布局。图中workspace与请求标签不作为实际分配大小、collective trace或性能依据。

三张原图按原始分辨率阅读，未重绘或修改；图示、公式、backend方法与真机结果分层留证。本次没有运行collective、attention、图或Device测试。


## 0 or 1是当前写入量，不是历史缓存长度

DCP解码图以Q seq=1为前提：单个新token只由owner写入，其他逻辑rank本步不写，因此标注KV Cache(0 or 1,h/tp)。历史缓存仍由请求seq_lens、分片所有权、实际block table与分配决定，不能据本步0写入宣告缓存为空、释放历史块或跳过所需collective。这个图示的单query前提也不覆盖所有混batch或多token验证。

## sparse和request块表的传输范围

旧中文设计的sparse block table表示“稀疏块表”措辞，当前英文对应request block table，即当前请求块表。SFA prefill/mixed在当前层写入后压紧这些请求块表引用的KV块并all-gather；这不同于仅将indexer最终选择的top-k作为传输清单。Decode则将复制indexer产生的global索引映射到本地KV。估算传输字节还须核对实际块数、dtype、物理stride和布局，不把旧词或一张流程图当实际通信量。


## strided ND MLA读取的局部实现边界

同提交 device/paged_mla_cache_read.py 全文给出选择性读取路径：仅4D、单物理head、K/V前三维一致、FP16/BF16且同dtype、NPU、至少一项非连续，以及NPU格式0/2才尝试；NZ/其他布局返回False交原读者。进入后严格核metadata/output的维度、同device、seq_offset长度与正block size，不兼容则ValueError，不能把False和异常都当无条件继续。

读取长度必须是本地每请求device行数，不能传CPU全局累计端点。按seq_lens repeat_interleave生成请求号，减累计起点得请求内位置，再加可选offset；从本请求block table取物理块，slot=physical_block×block_size+位置余数。num_tokens需与长度总和及输出形状配对，表内位置/物理ID合法性仍由调用者保证。

copy_pcp_kv_cache每tile最多8行，尾tile以首slot重复补齐后裁掉padding，避免来源注释所述A3部分尾tile问题；负slot的安全行为是被调用kernel约定，本文件未完成其Device证明。K/V packed结果的split view有跨两组件的行stride，所以最终copy到原TND输出，不能把split view直接当连续消费者输入。空输出返回成功，不因此取消其他CP collective。本节无NPU/MTE复现，原CP平台声明不扩展为该局部reader的全硬件数值认证。
