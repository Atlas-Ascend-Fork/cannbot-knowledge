---
type: API
title: npu_nsa_* 稀疏注意力算子组：压缩注意力出 topk 与选择注意力的训练/推理入口
description: 汇总 torch_npu 侧 8 个 npu_nsa_* schema 的调用链、固定注入参数、输出分配与自动微分接线，区分训练 TND 链与推理分页链，保留长度列表与块对齐边界。
tags:
- task.lookup
- topic.attention
- topic.kv_cache
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_nsa_compress.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_nsa_compress_grad.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_nsa_compress_infer.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_nsa_compress_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_nsa_compress_attention_infer.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_nsa_select_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_nsa_select_attention_grad.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_nsa_select_attention_infer.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.h
  role: implementation
created_at: '2026-11-12T04:21:27Z'
updated_at: '2026-11-14T01:59:28Z'
platforms: []
---

# npu_nsa_* 稀疏注意力算子组：压缩注意力出 topk 与选择注意力的训练/推理入口

## 版本与范围

本卡依据 OpPlugin 主线候选固定提交与同代发布提交，两 pin 中该组相关实现为注释剔除后 token 等价（仅排版差异）。该组 8 个 schema 全部经 `op_plugin_functions.yaml` 的 `gen_opapi` 登记生成，执行落到 aclnnNsa* 设备算子；OpPlugin 仓库没有对应官方 API 文档页，schema 与默认值以 yaml 登记为准。主线候选的软件配套尚未确认，不能据此推定任一发布组合支持这组接口或下列参数。

## 算子族与调用链

原生稀疏注意力（NSA）按"压缩 → 选块 → 稀疏计算"三段组织，torch_npu 层共 8 个入口：

| 入口 | 段 | aclnn 执行入口 | gen_opapi 固定注入 |
|---|---|---|---|
| npu_nsa_compress | 压缩（训练/预填充） | aclnnNsaCompress | `layout="TND"`、`actual_seq_len_type=0` |
| npu_nsa_compress_infer（.cache 变体） | 压缩（解码，增量写缓存） | aclnnNsaCompressWithCache | `layout="TND"`、`actual_seq_len_type=1` |
| npu_nsa_compress_attention | 压缩注意力 + 选块（训练/预填充） | aclnnNsaCompressAttention | `layout="TND"`、`sparse_mode=1` |
| npu_nsa_compress_attention_infer | 同上（解码分页） | aclnnNsaCompressAttentionInfer | `sparse_mode=0`、layout 由参数透传（默认 TND） |
| npu_nsa_select_attention | 选择注意力（训练/预填充） | aclnnNsaSelectedAttention | `layout="TND"`、`sparse_mode=2` |
| npu_nsa_select_attention_infer | 选择注意力（解码分页） | aclnnNsaSelectedAttentionInfer | `sparse_mode=0`、layout 由参数透传（默认 BSND） |
| npu_nsa_compress_grad | 压缩反向 | aclnnNsaCompressGrad | `layout="TND"` |
| npu_nsa_select_attention_grad | 选择注意力反向 | aclnnNsaSelectedAttentionGrad | `layout="TND"`、`sparse_mode=2` |

训练链输入按 TND 变长打包：query `(total_q, head_num, Dq)`，key/value 为压缩后的 `(total_cmp_kv, head_num, D)`；推理链额外引入 `block_table`、`slot_mapping` 与 `page_block_size` 分页缓存。所有 8 个入口 yaml 标注 `op_api: all_version`。

`npu_nsa_compress_attention` 的输出由 host 侧直接分配：`attention_out` 形如 `(query.size(0), query.size(1), value.size(2))`（dtype 同 query），`topk_indices_out` 为 `(query.size(0), key.size(1), select_block_count)` 的 INT32，`softmax_max_out`/`softmax_sum_out` 为 `(query.size(0), query.size(1), 8)` 的 FP32。推理变体的输出尺寸由 `KernelNpuOutputSize.cpp` 的四个推导函数给出，且布局检查在推导内完成：

- `npu_nsa_compress_attention_infer`：layout 仅接受 TND/BSND；TND 输出 `(T, N, head_size_vo)`，BSND 输出 `(B, S, N, head_size_vo)`；topk 输出 TND `(T, key_value_head_num, select_block_count)`、BSND `(B, S, key_value_head_num, select_block_count)`。该入口的输出与 topk 两个推导函数都先无条件 TORCH_CHECK `key_value_head_num > 0`；其中输出推导函数再以它相除计算 head_size_vo，topk 推导只用它组成输出形状。
- `npu_nsa_select_attention_infer`：layout 接受 BSH/BSND/TND；BSH 输出 `(B, S, head_num*key_head_dim)`，TND 输出 `(T, N, key_head_dim)`，BSND 输出 `(B, S, N, Dv)`。`key_value_head_num > 0` 的守卫只有 BSH 分支执行；TND 分支没有该守卫，直接以 `value.size(2) / key_value_head_num` 相除推 key_head_dim，非正值会直接进入除法，其合法性由调用方自证；BSND 分支直接取 `value.size(3)`，不做该除法。

## 长度列表与块语义

- 各 `actual_seq_*` 列表是按样本顺序的累计长度（等价 cu_seqlens 前缀和）。官方用例同时出现带首 0（`[0, 5, 49]`）与不带首 0（`[1384, 2633]`）两种写法，host 推导按差分逐样本处理：首项 0 产生一个空样本，空样本与长度不足 `compress_block_size` 的样本都被跳过、不产生压缩块。`compress_stride > 0` 的 TORCH_CHECK 只在某个样本长度达到 `compress_block_size` 时才执行，不是无条件 host 校验——全部样本都过短时，非法 stride 不会被该检查拦截。
- `npu_nsa_compress`：每个样本内按 `compress_stride` 滑窗（窗长 `compress_block_size`），输出 `(压缩块数, N, D)`，每块为 `sum(窗内输入 × weight)`。weight 形如 `(compress_block_size, N)`，在窗维广播。注意 schema 里 `actual_seq_len` 虽标 Optional，但 gen_opapi 固定注入 `actual_seq_len_type=0`，host 推导对该分支执行 `actual_seq_len.value()`：不传该列表是缺失 Optional 访问的 host 侧失败（具体失败形态未验证），实际必填。
- `npu_nsa_compress_attention`：先用压缩 KV 做稠密注意力，再把 softmax 概率按 `select_block_size / compress_stride` 与 `compress_block_size / compress_stride` 的块结构聚合成块重要性（GQA 组内对组头求和），随后降序稳定排序取前 `select_block_count` 个块索引。`topk_mask` 命中位置在官方 golden 中以大值填充，等效于强制入选；返回 `(attention_out, topk_indices, softmax_max, softmax_sum)` 四元组。解码端（`_infer`）golden 的固定规则是：块 0 与最后两个块必选，其余从中间块按重要性取满。
- `npu_nsa_select_attention`：按 `topk_indices` gather 对应 KV 块后做稠密 softmax 与 PV；golden 要求 key/value 的序列维能被 `select_block_size` 整除（非对齐直接抛错），并按 GQA（`G = N1/N2`）分组计算；softmax_max/sum 广播成 8 列 FP32 返回。
- `npu_nsa_select_attention_infer`：`topk_indices` 中以 `-1` 表示无效槽位（golden 遇 `-1` 停止收集）；块经 `block_table` 分页定位后按 `page_block_size` 拼接。
- `npu_nsa_compress_infer`（.cache）：仅当当前样本满足 `(实际KV长 - compress_block_size) % compress_stride == 0` 时，把尾部长度为 `compress_block_size` 的滑窗加权和写入 `cache[slot_mapping[b]]`，实现解码期压缩 KV 缓存的增量更新；窗口可跨 `block_table` 相邻两页拼接。

## 训练反向

`derivatives.yaml` 为三个前向入口自动接线，但路径并不对称：

- `npu_nsa_compress` → `npu_nsa_compress_grad`，返回 `(grad_input, grad_weight)`；
- `npu_nsa_select_attention` → `npu_nsa_select_attention_grad`，需要把前向返回的 `attention_out`、`softmax_max`、`softmax_sum`（golden 约定取每行第 0 列）与 `topk_indices` 一并回传，梯度按块 scatter-add 回 key/value，dq/dk 再乘 `scale_value`；
- `npu_nsa_compress_attention` 的 q/k/v 梯度不走 nsa 专用 grad，而是改接 `npu_fusion_attention_grad`（TND、`sparse_mode=1`，复用前向 `result0/2/3` 与 `actual_seq_qlen`、`actual_cmp_seq_kvlen`）。这意味着压缩注意力的反向在数值上按稠密 FA 语义回传，其稀疏性只体现在 topk 索引输出上；两个 grad 入口本身也可脱离 autograd 单独调用。

## 触发门槛与收益

适配 NSA（压缩注意力 + topk 选择）类稀疏注意力模型时，该组是 torch_npu 层的成组入口：预填充走训练链（compress → compress_attention → select_attention），解码走分页链（compress_infer 维护压缩缓存，compress_attention_infer 出 topk，select_attention_infer 完成稀疏计算）。收益边界：只有 selected-attention 段的计算量与中间激活随选中块数而非全序列增长；全量 KV 存储、压缩计算与块重要性打分仍随序列长度增长。本卡未做显存/吞吐实测，不提供量化收益承诺。设备算子层的 Host/Launcher/Route/Kernel 实现见 [NsaCompress](../../../../ops/ascendc/operators/aclnn/transformer/attention/nsa_compress.md)、[NsaCompressAttentionInfer](../../../../ops/ascendc/operators/aclnn/transformer/attention/nsa_compress_attention_infer.md)、[NsaSelectedAttention](../../../../ops/ascendc/operators/aclnn/transformer/attention/nsa_selected_attention.md)与[NsaSelectedAttentionInfer](../../../../ops/ascendc/operators/aclnn/transformer/attention/nsa_selected_attention_infer.md)；训练反向复用的稠密 FA 梯度入口见 [npu_fusion_attention_v3](../../../training/apis/torch_npu/npu_fusion_attention_v3.md)。

## 失效边界

- 官方用例 8 件中 7 件带 `@unittest.skip("Skipping due to outdated CANN version…")`（仅 `test_npu_nsa_select_attention` 活跃），全部标注 `SupportedDevices(['Ascend910B'])`；本卡未做任何运行验证，数值行为以用例 golden 为参考描述，平台支持未知。
- `test_npu_nsa_compress_infer` 的 golden 内部以未绑定名调用 `get_last_kv`（潜在缺陷），且该用例处于 skip 状态，其解码增量语义不能视为已验证。
- 两个 torchair 固定版本（主线与发布）的 ge_converter 定向搜索没有 `npu_nsa_*` 条目：这组入口在所查版本的 GE 图捕获中无 converter，走 torchair 路径时需要自行处理；该否定性观察不外推其它图执行路径。
- 训练链与推理链的块参数（`compress_block_size`、`compress_stride`、`select_block_size`、`select_block_count`、`page_block_size`）必须与 KV 分页布局一致，`select_block_count` 需不超过实际可选块数；topk 索引跨链复用时注意训练链 topk 维度取 `key.size(1)`（head 维）而推理链取 `key_value_head_num`。
- 与[稀疏共享 KV 注意力概念](../../concepts/kernels/sparse_attn_sharedkv.md)（SAS/SASG，五阶段 CV 流水实现）不是同一算子族：那是 Ascend C 概念层的另一稀疏注意力家族，不要混用入口与结论。
