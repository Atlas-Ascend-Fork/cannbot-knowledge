---
type: Concept
title: vLLM Ascend 输入元数据：请求索引、位置、块表与 slot mapping
description: 按中英文输入示例区分每请求数量与token总数、词表ID/扁平索引/物理块和KV slot，用两轮chunked prefill校验元数据量纲，保留padding与专用路径边界。 补充MRv1持久字段、DCP请求排序、拒绝后异步重建、MTP slot与builder最终化合同。
tags:
- task.design
- topic.attention
- topic.kv_cache
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/developer_guide/Design_Documents/ModelRunner_prepare_inputs.md
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/locale/zh_CN/LC_MESSAGES/developer_guide/Design_Documents/ModelRunner_prepare_inputs.po
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/npu_input_batch.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/dcp_utils.py
  role: implementation
created_at: '2026-10-29T09:34:19Z'
updated_at: '2026-11-03T05:13:17Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
aliases:
- NPUInputBatch
- DCPManager
- DCPSpecDecodeMTPInputs
- DCPAsyncSpecDecodeRebuildResult
---

# vLLM Ascend 输入元数据：请求索引、位置、块表与 slot mapping

## 范围与三个层次

以下是 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 输入准备设计中的逻辑关系，不是所有 Runner 的同名字段或内存布局承诺。普通整数位置示例不能替代 M-RoPE、CP 或图 padding 的专用路径。

token 级字段按本轮调度 token 排列，如 input_ids、positions、slot_mapping；请求级字段按活动请求排列，如已计算 token 数和 seq_lens；query_start_loc 是请求边界前缀和，因此比请求数多一个元素。系统级 Token IDs table 保存各请求的 token，block table 保存逻辑块到物理块的映射。token 数、请求数与最大单请求调度长度不能互换。

## 从调度数量到输入

设每请求本轮调度数量为 n_r，已计算数量为 c_r，则普通位置为 `c_r + [0, ..., n_r-1]`。展开请求索引 r 后，以该请求在 token table 的行基址加位置选取输入。`query_start_loc = prefix_sum([0, n_0, ...])`，普通 seq_lens 为 `c_r+n_r`，max_query_len 是 n_r 的最大值。

设计文档的 chunked-prefill 例子中，未在第一轮调度完的 prompt 留到下一轮；已经进入 Decode 的请求同时携带新采样 token。请求处于同一 batch 不意味着处于同一阶段。先核对 request order，再比较每个 token 的输入、位置和对应元数据。

## 分页写入关系

设逻辑 block size 为 B，token 位置为 p，则逻辑块号是 `p // B`，块内偏移是 `p % B`。由请求的 block table 查物理块号 b，得到普通分页路径的 `slot = b*B + p%B`。它表示 KV 写入的物理 slot，不是输入 token ID，也不是 token table 的线性索引。

例如 B=2、物理块号为7、块内偏移为1时，slot 为15；不能因请求是第几项就推导其物理块号。设计文档部分图表的 T_x_y 标注与请求号有笔误，摄取保留计算关系，不把占位标签当作真实输入值。

## 适配检查与边界

检查扁平 token 总数等于调度数量之和，query_start_loc 单调且末项覆盖本轮有效 token；逐请求核对已计算量、seq_lens、位置和已分配块。空请求、请求重排、抢占重算、共享缓存和投机 token 需沿各自状态链验证，不能只核对 shape。

图捕获使用的 padded 数量与真实数量可能不同；CP 会改变本地位置和缓存写入；M-RoPE 位置也不是普通一维整数序列。将本卡公式推广到这些路径前，读取对应实现与元数据契约。设计例子的 mask 大小和 block 0 占位规则也不是所有后端通用 API。

## Evidence

输入准备文档给出两轮混合/分块示例及元数据层次；平台源码表明后端按模型与场景选择。本次没有以真实请求运行验证，数学关系不代替实现和数值验收。


## 平台证据待补

输入准备设计解释逻辑元数据，没有整项接口的平台矩阵；platform.py的通用后端选路不能证明该示例布局在四类设备的实际实现范围。据此撤回原平台枚举，保持draft/空平台；这是证据不足，不能解读为这些平台不支持。

标准非因果Attention还需将causal与mask的消费协议一起核对，不能因位置/长度公式正确就保留上三角遮挡；见[双向mask诊断](../../runbooks/precision/vllm_ascend_noncausal_mask_contract.md)。


## 中文输入准备示例与量纲核对

ModelRunner_prepare_inputs.po的87条有效译文均匹配当前英文，但原英文也含示例标签/量纲歧义。`Token IDs`/`Input IDs`是词表编号，`token indices`是取token table的扁平索引，`device block number`是物理块编号；都不是同一个值，也不单独等于原始字节地址。slot mapping用于对应token的KV写入位置，不按文档“存Token ID”的措辞把词表编号写进KV缓存。

两轮玩具示例取max_model_len=12、block size=2，第一轮只调度10个prompt token，第二轮两个短请求已decode、长请求继续chunked prefill：

| 量 | 第一轮 | 第二轮 |
| --- | --- | --- |
| 每请求调度数量 | [3,2,5] | [1,1,3] |
| 已计算数量 | [0,0,0] | [3,2,5] |
| 有效token总数 / 请求数 | 10 / 3 | 5 / 3 |
| query_start_loc | [0,3,5,10] | [0,1,2,5] |
| seq_lens | [3,2,5] | [4,3,8] |
| max_query_len | 5 | 3 |
| token indices | [0,1,2,12,13,24,25,26,27,28] | [3,14,29,30,31] |
| slot mapping | [2,3,4,6,7,8,9,10,11,12] | [5,14,13,16,17] |

原文将[3,2,5]也标作number of tokens时，应区分该每请求数量列表与其和10，不把列表直接喂给实际backend的scalar字段。请求顺序、request index与输入token展开必须相同；T_3_y是该第三行的占位标签笔误，不增加第四个请求。位置的除block size在此是整数块索引关系，不是浮点除法。

文档的int32、block_0未使用、mask 5×5或5×8属于这个解释示例，不构成所有Runner、attention、padding或多模态的dtype/空块/掩码接口。token table与block table的理想矩形也不证明实际内存连续或storage所有权。实际Q/KV长度、padding与投机修正按[DSpark长度诊断](../../runbooks/precision/vllm_ascend_dspark_query_kv_length_mismatch.md)等对应路径核对，不能照抄普通示例覆盖M-RoPE/CP或乐观元数据。本批没有生成或执行真实tensor。


## MRv1持久InputBatch与DCP真实长度

整文件AST投影核对同提交 NPUInputBatch(258原始行)、DCPManager(697原始行)的全部程序语句，注释/docstring未作逐字完整阅读。NPUInputBatch自行初始化继承字段而非调用父构造，包含req_id/index、Host token表、num_tokens/no_spec/prompt/computed、采样参数、LoRA mapping、生成器、logits processor、pooling与异步copy状态；升级Native新增字段不由继承自动补齐。大token IDs与is_token_ids表显式pin_memory=False，其他Host镜像按参数pin，不能把整个InputBatch当一份pinned连续内存。

MultiGroupBlockTable同时接收manager/kernel块大小、interleave、KV groups与spec预算；kernel列表为嵌套形式时只取每组首项，调用方须保证这项确为选中kernel粒度。sampling metadata在构造时生成，prev_req_id_to_index、sampled IDs及copy-ready event初始为None；请求重排/移除的更新协议仍在父类，不能只改GPU Tensor而留Host映射。

DCP decode分类同时要求有context、本轮query<=1+构造spec预算、已完成prompt；PD recompute例外允许computed=prompt-1。它按mask求decode数，却对scheduled前num_decode_reqs项求token和，因此调用方必须先保证decode请求排在前缀，不能只传任意混合顺序。device local seq_lens与CPU local镜像都按真实DCP rank/interleave计算，CPU必须来自有效镜像；padding请求长度置0。

MTP slot输入分清完整请求边界、实际接受数和追加query容量：由原sample index求拒绝数，slot_index=请求起点+请求号×(K-1)+接受数-1。额外draft位置按构造decode_threshold-2扩展，实际本批K不一定等构造预算；动态K需沿caller核对。slot表目前从group0取，不能将这个helper自动推广到任意独立多KV group。

## 异步DCP重建与builder最终化

异步重建要有前批mapping、valid_sampled_count且存在decode。纯decode、无prompt embeds/多模态且有prev_positions时走device位置与slot重建；否则等valid-count Host拷贝事件，以拒绝数校正optimistic CPU长度，再重取token table、复制input IDs并调用准备函数。返回值分开rebuilt与positions_ready_on_device，不能仅用一个布尔判断位置镜像都已同步。

generate_dcp_mtp_input保存完整query_start_loc与async rebuild快照，再按每请求追加预算生成slot；多项签名参数在实现中del掉，并不消费其承诺的语义，不能靠同名参数假定有额外修正。非SFA drafting要求metadata已被backend builder归入decode且带cp_seq_len或cp_history_seq_len，本helper不再重新计算覆盖；SFA则更新dcp_context的当前rank长度并把padding尾清0。legacy非MLA路径额外构造CPU全rank local lengths，不能把其二维字段与只当前rank向量互换。

验证请求重排/新增、prompt边界、PD重算、dynamic K、拒绝、Host copy事件与每组slot，分别比较CPU镜像、device真值和capture padding。本节没有运行上游，源码选路不代替分布式一致性或吞吐验收。
