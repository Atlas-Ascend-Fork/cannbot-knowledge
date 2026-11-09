---
type: Runbook
title: vLLM Ascend GDN卷积权重诊断：注册、重载回调与状态观察
description: 依据六个CPU测试场景诊断GDN packed卷积参数未刷新，核对LoRA base注册、meta占位、后处理重打包、地址和值及connector状态，保留真实加载边界。
aliases:
- GDN卷积权重诊断
- initialize_packed_conv_weight
- _PACKED_CONV_WEIGHT_NAME
- _get_packed_conv_weights
tags:
- task.debugging
- topic.precision
- topic.model_adaptation
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_gdn.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/ops/gdn.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_qwen3_5.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/ops/test_gdn_layerwise_kv.py
  role: evidence
created_at: '2026-10-31T11:26:02Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-31T11:33:30Z'
---

# vLLM Ascend GDN卷积权重诊断：注册、重载回调与状态观察

## 症状和主证据

GDN卷积checkpoint重载后输出未变、LoRA包装后找不到packed参数、meta参数没有落地，或connector看到旧state时，先检查注册位置、加载回调和消费顺序。主证据为固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2的test_gdn.py165行、6个CPU测试函数，ops/gdn.py和patch_qwen3_5.py解释机制。

本批只阅读源码与测试定义，未执行checkpoint、测试、torch.compile、NPU或在线换权重。没有复现一个真实设备故障，保持draft/空平台。Native loader、replace_parameter及配对ABI仍需按[框架版本](../../concepts/frameworks/vllm_ascend.md)核对。

## 六个场景与观察项

| 固定test函数 | 应保留的输入与断言 |
|---|---|
| test_packed_weight_is_registered_on_base_conv | 参数挂在conv base，shape为[W,D]、dtype匹配且不训练 |
| test_updated_packed_value_keeps_data_ptr | 两次后处理、源值改变，packed内容刷新且测试期望地址稳定 |
| test_packed_getter_resolves_lora_base_layer | LoRA.base_layer上的注册参数能由getter取得 |
| test_meta_weight_keeps_meta_placeholder | meta来源保持meta占位，data_ptr=0不是设备就绪 |
| test_layerwise_reload_repacks_updated_source_in_place | Native layerwise loader初始化/结束流程中的源与packed内容、地址 |
| test_head_first_conv_split_preserves_values_and_token_axis | TP1/2和不同head数，拆分视图保留值、token轴及storage |

测试用CPU Tensor和fake quant method表达期望，不能把定义或模拟loader当真实checkpoint重载成功。额外layerwise KV测试中的torch.compile/fullgraph同样未执行。

## 第一步：确认补丁实际安装的实现

patch_qwen3_5保存原Native GDN构造器。非GDN_COMPATIBILITY分支包装原init后调用initialize_packed_conv_weight，并替换forward/core/pack、将warmup置空；兼容分支选择_310p/ops/fla/gdn_310.py的core与state dtype，不走相同注册流程。

先记录实际类、profile、patch分支及conv对象是否已有LoRA wrapper，不对所有硬件重复安装相同hook。补丁文件的M-RoPE、完整attention和MTP分支不在此诊断范围；它们的存在不是本卡验收结果。

## 第二步：注册成功不代表内容已打包

_PACKED_CONV_WEIGHT_NAME为ascend_conv1d_weight；_get_base_conv1d解开LoRA.base_layer，注册在base conv而非attention或外层wrapper。参数为[W,D]、requires_grad=False，dtype来自model config、device来自源weight。

initialize_packed_conv_weight只先分配注册参数；没有quant_method或process_weights_after_loading时会在此返回，并不自动把当前source拷进去。不能仅凭named_parameters里出现名字就进入推理。meta来源在_pack_conv_weights中返回，保持placeholder，需要实际加载流程落地后重新确认。

_get_packed_conv_weights按base对象获取同一个注册参数；不要在attention上另挂一个常量副本绕过loader。

## 第三步：原始后处理在前，重打包在后

包装的process_weights_after_loading先调用原method，再_pack_conv_weights；后者把source[D,1,W] view后transpose为[W,D]，转换到packed的dtype/device并contiguous，再replace_parameter。

检查实际量化后source形状、回调绑定对象和执行次数。重载后应同时观察source值与packed值，而非只看shape或data_ptr。Native0.32分支显式prefer_copy=True，之后版本调用签名不同；地址稳定必须由实际版本验证。

这里是每次后处理刷新已注册参数的合同，与GLM KDA首次forward的lazy packed cache不同。[通用权重切换](../../guides/integration/vllm_ascend_weight_switch_contract.md)另管local/full视图和通信buffer，不能替代本回调。

## 第四步：重载后检查实际消费者

保存源/packed的参数身份、shape/dtype/device/stride、地址和小范围值对照；LoRA开启与关闭时都从base对象检查。测试证明的是设计期望，没有证明所有量化scheme和Native loader自动触发hook。

head-first conv输出沿head轴拆成q/k/v，再变成[1,T,H,D]视图；若源权重已更新而结果仍错，继续核head数量、TP切分、token轴和conv状态，不通过重复pack掩盖布局问题。GDN一般执行合同见[运行接入](../../guides/integration/vllm_ascend_gdn_runtime_dispatch_contract.md)。

## 第五步：权重新旧与KV状态新旧分开定位

_forward_core先wait connector并记录compute，再读取self.kv_cache；conv/SSM更新和输出合并后save。观察本步读到的cache对象、选中state行及save时值，不能把权重参数更新等同历史state已迁移。

test_connector_observes_updated_gdn_state_for_each_compiled_call定义CPU custom op和compile/fullgraph场景，fake conv/chunk推进state后由save检查；它没有验证真实NPU编译、DMA完成或PD传输。FLA strided-state fixture也替换kernel/gather/scatter，仅说明测试要保护选中行和未选行。

同文件的non-BF16 fixture用FP32但mock整个chunk；真实chunk入口明确拒绝FP32。确认了分派不等于确认了dtype可运行，不能据该fixture修成跨dtype承诺。

## 修复、回退与交付

按已定位的注册对象、加载回调、源布局或state生命周期恢复匹配实现；hook是否缺失要从实际调用链取证，不盲目重复包装。meta未落地、回调未完成、dtype/shape不满足或并发读者仍在用旧权重时，停止该新实例的推理，重建匹配权重与完整状态后验证基线。

实际验收需覆盖首次加载、连续两次重载、LoRA base wrapper、meta落地、目标量化scheme、TP/head布局、连续步状态，以及eager/graph和connector在途读者。每次记录模型/版本、源与packed值、回调顺序、参数/存储地址和输出参考。数值与状态正确后才比较打包时间、内存和端到端性能；本卡不声明热切换事务、并发安全或NPU收益。
