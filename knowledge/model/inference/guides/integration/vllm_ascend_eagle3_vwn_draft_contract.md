---
type: Guide
title: vLLM Ascend Eagle3 VWN 草稿接入：分组宽网络、隐状态与词表映射
description: 沿 VWN 草稿构造和 forward 核对 m/r 分组、第一层 QKV、宽残差、三个辅助隐状态、草稿量化与词表偏移；对照独立 Native 的继承接口、权重加载和 parallel drafting，保留硬件及版本待验证边界。
aliases:
- Eagle3 VWN
- PreVwnLayerV1
- VwnLlamaDecoderLayer
- VwnLlamaModel
- Eagle3VwnLlamaForCausalLM
- norm_before_fc
tags:
- task.implementation
- task.debugging
- topic.speculative_decoding
- topic.model_adaptation
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/models/llama_eagle3_vwn.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/spec_decode/test_speculators_vwn_eagle3.py
  role: evidence
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/model_executor/models/llama_eagle3.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.github/vllm-main-verified.commit
  role: constraint
created_at: '2026-10-31T21:29:10Z'
updated_at: '2026-10-31T21:37:10Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Eagle3 VWN 草稿接入：分组宽网络、隐状态与词表映射

## 接入任务、版本和证据范围

Eagle3 VWN 在普通 Eagle3 的输入 embedding 与 target 隐状态之间加入分组宽网络。移植时必须保持实际 token 行数、宽残差和反馈状态，不能只把草稿架构名注册成功就认定接入完成。本卡主来源是 Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2 的 llama_eagle3_vwn.py 全文 257 行，类入口为 Eagle3VwnLlamaForCausalLM；同时阅读其 CPU UT 全文 418 行，以及独立 Native llama_eagle3.py 全文 470 行。

Main 配对 Native 为 544f182d9f0c9bfe8bd7645525951d5e3692a542，独立参考 Native 为 5df63a7203cdb9328d824a27b682e77c7b9928be。下面区分直接覆写和继承行为，不把这两个 Native 身份混成已通过 ABI 验证的组合。整项 VWN 适配的硬件与实际 checkpoint 范围没有独立闭合，保持 draft/空平台；注册表列出模型不构成 A2、A3、950 或其他硬件的运行证明。

投机方法选择见[草稿方法指南](../optimization/vllm_ascend_speculative_method_selection.md)，不同模型的二元状态协议见[MTP 隐状态诊断](../../runbooks/precision/vllm_ascend_mtp_hidden_state_contract.md)。这些共同约束不能代替 VWN 自己的宽度和权重合同。

## PreVwnLayerV1：先融合，再按 m 分组升维

令 hs=hidden_size，m=vwn_m（缺省 1），r=vwn_r（缺省 1），wd=int(hs*r)。PreVwnLayerV1 分别用 input_layernorm 和 hidden_norm 对 embeds/hidden_states 做 RMSNorm，沿最后维拼为 2*hs，经 fc 投影回 hs；随后 view(-1,hs//m)，用共享 upward 从 hs//m 投到 wd//m，再 view(-1,wd)。

这里的分组发生在特征维，共享同一组线性权重；中间的第一维通常是 token 行数乘 m。它不是把 token 分给 m 张卡，也不是 tensor parallel world size。若 m、hs、wd 的关系不满足分组整除，某些 batch 的总 numel 恰好可 view 也不保证 token 行数仍正确。接入层应检查 m 为正整数、wd 为正、hs 与 wd 均能整除 m，并验证每阶段实际行数。

r 先乘后转 int，不能按理想实数比例推导宽度而忽略截断。源码没有完整的非正 m/r、非法 dtype 或任意输入 rank 校验。_linear 使用 ReplicatedLinear、bias=False、return_bias=False，params_dtype 取传入 vllm_config.model_config.dtype；量化配置另走草稿专用入口，不意味着 target 与 draft 的所有 dtype 自动独立。

## VwnLlamaDecoderLayer：第一层的窄 QKV 与两段宽残差

父类 Eagle3 第一层原本使用 2*hs 的 QKV 输入。VWN 在 layer_idx==0 时重新建立 QKVParallelLinear，输入宽度恢复 hs，保留 head_dim、总 query/KV heads、attention_bias 和草稿 quant_config。VWN 先在 PreVwnLayerV1 融合输入，所以不能再套父类第一层的 embedding 拼接路径。

第一层 forward 的顺序为：

1. pre_vwn_layer 形成 wd 宽特征；downward_and_forgot 把每个 wd//m 分组投到 (hs+wd)//m，重排后拆出 hs 宽 hidden 与 wd 宽 res。
2. hidden 经 pre_attention_layernorm 与 self_attn；结果按组 upward_after_attn 升到 wd，并与前面的 res 相加。
3. downward_and_forgot_after_attn 再拆 hidden/res；hidden 经 post_attention_layernorm、MLP、upward_after_mlp，再与新的 res 相加。
4. 最后 downward 按组降到 hs，返回 hidden_states 与传入 residual。

VWN 的宽 res 是函数局部张量，不等于父类贯穿普通 decoder 的 residual 参数。固定实现只在 layer_idx==0 执行上述计算；其余层直接返回输入 hidden_states/residual。构造函数仍按 num_hidden_layers 建立多个层，不能由“列表有 N 层”推导执行了 N 次 VWN，也不能凭此自行补造后续层算法。

## 层名偏移、辅助状态与量化配置

VwnLlamaModel 从 speculative_config.draft_model_config.hf_config 取配置。层名称使用 i+start_layer_id，但传给 decoder 的局部 layer_idx 仍是 i。主类用 target model_config.get_num_layers(parallel_config) 得到 n，保存 target_layer_count，并以 start_layer_id=n 构造模型。独立 Native 使用 get_total_num_hidden_layers()；在 PP 等情形下需核对实际 API 语义，不能把这两个调用自动视为相同的全局层数。

use_aux_hidden_state 从 eagle_config 的同名键取得，缺省 True。启用时，fc 输入为 target_hidden_size*3（属性存在时）或 hs*3，num_aux_hidden_states 固定 3，再投到 hs。Main 的 norm_before_fc 读取顶层配置；启用时用单个 RMSNorm 归一化整段拼接向量。Main 显式令 fc_norm=None。

独立 Native 可从配置或辅助层列表决定辅助状态数，还支持各 chunk 独立的 fc_norm，并优先解释 eagle_config 中的 norm_before_fc。父类具备这些选项，不证明 Main 重建的构造函数也实现了它们。若 target 实际提供的辅助层数或 hidden width 发生变化，先核对拼接来源和 FC 权重形状，不截断/补零掩盖差异。

VWN decoder 的 get_quant_config 继承草稿专用 get_draft_quant_config，VwnLlamaModel 和 LM head 也调用该入口。它与 params_dtype 的选择是不同问题；加载时分别记录 target/draft 的 quant_config、Linear 实例、参数 dtype 与 prefix。具体量化 scheme 的内部实现不在本卡源码范围内。

## forward、combine_hidden_states 与二元输出

VwnLlamaModel.forward 在未传 input_embeds 时调用 embed_input_ids，逐层传入同一输入 embedding 与当前 hidden_states，最后返回 `self.norm(hidden_states,residual), hidden_states`。固定 VWN 路径中的 residual 保持传入的 None，UT 检查 postnorm/prenorm 两个结果的形状；这不是完整数值一致性证明。

独立 Native forward 还检查 embedding 与 hidden_states 的末维相等，并可按 norm_output 选择辅助输出。Main 覆写不等于保留了所有父类 guard 和选项。接入 proposer/runner 时应确认第一项用于 logits、第二项如何参与下一步草稿反馈，不能交换两项或把最终归一化重复施加给递归状态。

combine_hidden_states 在关闭 aux 时原样返回；否则按 norm_before_fc 做整体归一化，可选 fc_norm 分支逐 chunk 处理后再调用 FC。Main 默认 fc_norm 为 None，因此该分支不是构造后自然启用。辅助状态数、每个 chunk 的宽度、norm 顺序及实际 FC 输入需要一起验证。

## 草稿词表：偏移映射与未加载状态

draft_vocab_size 为 None 时回退 vocab_size，LM head 与 LogitsProcessor 使用草稿词表大小，并保留 logit_scale。Main 总是创建长度为 draft_vocab_size 的非梯度 long 参数 draft_id_to_target_id，初值全零；独立 Native 则只在草稿词表与 target 词表大小不同时创建映射。

compute_logits 先得到草稿 logits，令 base=arange(draft_vocab_size)、targets=base+draft_id_to_target_id，新建 `[rows,vocab_size]` 且全为 -inf 的张量，然后把草稿 logits 写入 targets。该参数保存的是偏移，不是可直接使用的绝对 target ID。若映射为 None，才走词表宽度断言后直接返回的分支。

需要验证 offset 的加载、长度、dtype、device、targets 范围与重复目标。源码没有为所有越界或重复映射提供专用 guard；不能把高级索引对负值的行为当作正确映射，也不能从构造时全零推导 checkpoint 的真实映射已经加载。未被映射的位置保留 -inf，并不是任意较大 target 词表都能由草稿直接完整生成。

## 继承 loader、prefix 与 parallel drafting

Main 没有覆写 load_weights，继承独立 Native 所示的处理链：跳过 t2d，将 d2t 名称替换为 draft_id_to_target_id，普通非 lm_head 权重加 model. 前缀；mask_hidden 在 parallel drafting 开启时直接 view(1,-1) 并复制，关闭时告警跳过。开启 parallel drafting 却没有 mask_hidden 会报 ValueError。loader 还根据缺失的 embedding、映射和关闭的 aux/norm 配置构造忽略项。

该流程调用 process_eagle_weight、AutoWeightsLoader 和 WeightsMapper；本卡只闭合所读调用与名称处理，没有完整阅读这些共享 helper，不声称所有 checkpoint 异常都会由它们正确恢复。Native LlamaModel 自身还把 midlayer 映到 layers.0，并合并 q/k/v、gate/up。Main 的 model prefix 固定为 model，而 LM head 使用传入 prefix；外层非空 prefix、层号偏移和 checkpoint 原始键必须逐项对照。

parallel_drafting 开启时，Main 注册非 persistent 的 mask_hidden，宽度为 `(3 if use_aux_hidden_state else 1)*hs`。如果 FC 输入另取 target_hidden_size*3，这两个宽度并非由同一个表达式推导。检查实际权重和 proposer 传值，不能用当前 UT 默认配置替代不同 target/draft hidden size 的覆盖。

## 验证次序、回退与 Evidence

先固定模型/依赖提交、草稿配置、实际模块类型、m/r、hs/wd、辅助层与词表映射。依次核对分组线性形状、第一层 QKV、宽残差、非零 layer_idx 行为、二元输出、FC 与 mask 宽度，再检查完整 checkpoint 的加载清单和 logits 的目标索引。随后在授权环境中验证 target/draft 联合状态推进、接受率、任务精度、PP/TP、graph/eager 和性能；单独的 shape 成功不能替代这些验证。

UT 用 CPU 实现替换 NPU RMSNorm/add-norm，用 passthrough 替换 attention 和 MLP，mock TP1/Ascend 配置；覆盖 m/r、第一层 QKV、单层 forward、embedding 等形状。它未提供完整词表映射、缺权重、多层 VWN、实际 attention/MLP 或设备图执行的验收。本次只读测试源文件，没有运行这些测试。

出现偏差时保留原 checkpoint、加载名称、各阶段 shape/dtype 与版本，回退到已配对验证的草稿和 proposer 配置。不要靠丢弃辅助状态、默认零映射或把多个 decoder 层改成同一模板消除报错。本次未执行上游导入、权重加载、编译、模型、NPU、精度、性能或 Agent A/B，未填写 verified 事件。
