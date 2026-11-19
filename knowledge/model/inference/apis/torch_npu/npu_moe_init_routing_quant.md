---
type: API
title: npu_moe_init_routing_quant：INT8路由融合的五返回与容量
description: 记录独立路由量化入口的1024默认容量、INT32统计、动态尺度与无效输出，避免与routing_v2四返回混用。
tags:
- task.implementation
- topic.mixture_of_experts
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeInitRoutingQuantKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeInitRoutingQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_moe_init_routing_quant.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_moe_init_routing_quant.py
  role: example
created_at: '2026-11-10T11:33:00Z'
updated_at: '2026-11-14T01:59:28Z'
platforms: []
---

# npu_moe_init_routing_quant：INT8路由融合的五返回与容量

## 固定版本与接口范围

本卡依据OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`与发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的C++包装和Schema，补齐路由与INT8量化融合入口。两个快照的所述检查、分配和ACLNN参数一致；发布来源组合为ascend_26_0_pt28，主线配套未知。未取得覆盖整张接口的产品支持合同，保持draft与空平台；测试的Ascend910B装饰器不作为完整设备矩阵。

```text
npu_moe_init_routing_quant(x, expert_idx, *, scale=None, offset=None,
  active_num=1024, expert_capacity=0, expert_num=256, drop_pad_mode=0,
  expert_tokens_num_mode=0, expert_tokens_before_capacity_flag=False,
  quant_mode=1)
  -> (expanded_x, expanded_row_idx, expert_token_cumsum_or_count,
      expert_tokens_before_capacity, expanded_scale)
```

这是独立的五返回入口；[npu_moe_init_routing_v2](npu_moe_init_routing_v2.md)为四返回、统计参数名和默认值也不同。不能仅改函数名后按旧位置取scale，或把本接口quant_mode=0解释为非量化。两版包装均调用`aclnnMoeInitRoutingQuantV2`，该ACLNN名中的V2不把它变成同名Python routing_v2接口，也不构成最小CANN版本证明。

## 输入检查与模式边界

包装要求x和expert_idx均为二维，首轴相同。令x为[B,H]、expert_idx为[B,K]，局部校验仅允许drop_pad_mode=0/1、quant_mode=0/1和expert_tokens_num_mode=0..2。测试参考使用0为静态INT8量化、1为动态INT8量化；两者expanded_x均分配INT8，本入口没有保持浮点输出的非量化分支。

scale/offset缺省被替换为未定义Tensor交给ACLNN。包装没有完整检查其shape、dtype、非零尺度，也未逐项检查expert ID域、输入dtype、expert_num/capacity正值和计数溢出；本卡不把这些未检查条件扩为合法输入。需要与目标ACLNN合同及下游专家GMM核对，不因Python接受参数就猜测所有广播与类型组合。

## 容量与每项输出的消费

active_num默认1024，调用方若省略且B*K>1024，局部输出分配即进入截断容量，不能默认认为处理全部路由。drop_pad_mode=0时，active_num>0分配R=min(B*K,active_num)，非正值分配R=B*K；这是包装分配规则，不是负数值域的完整公开保证。drop_pad_mode=1时R=expert_num*expert_capacity，数据为三维[E,C,H]，active_num不参与这一步分配。

| 输出槽 | 包装形状与类型 | 生效条件及边界 |
| --- | --- | --- |
| expanded_x | dropless/active为[R,H]，drop/pad为[E,C,H]；INT8 | 静态和动态模式均量化，分配容量不是有效token数量。 |
| expanded_row_idx | [B*K]，沿expert_idx的options | active截断不缩短此映射缓冲；不要用expanded_x行数强行reshape映射。 |
| expert_token_cumsum_or_count | [E]，INT32 | 仅drop_pad_mode=0且统计mode>0时分配，否则C++为未定义Tensor；不继承routing_v2的INT64统计。 |
| expert_tokens_before_capacity | [E]，INT32 | 仅drop_pad_mode=1且flag=True时分配，否则未定义。 |
| expanded_scale | [R]，FP32 | 仅quant_mode=1分配；静态mode0为未定义Tensor，不是返回了一组单位尺度。 |

包装只限定统计mode值0..2，没有在本函数解释1与2的全部统计语义。选定测试在mode2把第三项与独立专家count参考比较；mode1不在这些数值用例中。不要根据字段名自动把两种模式都按cumsum消费。恢复token必须与本入口实际映射方向、有效前缀及容量策略配套，不与Dispatch V2的assist_info_for_combine互换。

## 测试参考与缺口

已静态阅读主线测试的参考、调用和两个用例：B=4/H=1024/K=8/E=32，drop_pad_mode=0、active_num=0、统计mode2，覆盖浮点输入的静态和动态INT8。静态有单元素scale/offset；动态用例令二者None。第四项返回被测试helper丢弃，没有drop/pad或active_num=1024截断的数值验收。

CPU参考按expert_idx的token优先展平做稳定排序，动态无scale分支用每行absmax/127形成反量化尺度；这个参考没有完整处理零幅值和空有效区。扩展到有expert平滑scale时还需留意测试把传入NPU的scale截为[:1]，不能据此认证全[E,H]分支。比较前helper还将有效count之后的expanded_x/scale改成0，因而测试不证明后端原始尾部已清零。INT8结果差先以INT8数组计算绝对值，有溢出敏感性，不把宽松差值检查当作全值域误差认证。

本次未运行测试或新增verified。模型接入应显式确定active容量，分别验证静态/动态、统计模式、空专家、截断、drop/pad、映射方向与有效尺度；用非均匀输入接真实GMM及恢复路径验数值，再比较融合前后的完整阶段耗时和峰值内存。融合可能省去独立量化与重排中间结果，但实际收益未测量。

## 完整测试参考中的映射与量化顺序

两版251行测试原始字节相同。CPU helper先统计expert_range内路由数，将低于expert_start的ID替换为INT32最大值，再以稳定排序排列展平的expert_idx；它没有对高于等于expert_end的ID做同样替换，不能将该参考推广为任意无效ID处理合同。drop_mode=0时参考映射是**原路由槽→排序后的有效位置**，初值为-1，只对有效前缀回填；helper的drop_mode=1分支返回排序下标，但现有两个测试方法都只取mode0，不能把未运行的参考分支当作后端drop/pad证明。

静态参考先将x、scale和offset转FP16，取排序对应token，乘scale第一行、可选加offset第一行，然后rint、裁剪到[-128,127]并转INT8；其浮点输入覆盖FP16、FP32和BF16，但静态参考内部仍经过FP16。动态参考将输入转FP32，可选先按专家行乘平滑scale，再以每行absmax/127归一化并round到INT8；现有动态方法只选scale/offset均None，没有验证这个有scale分支。参考末尾补零、bincount与实际NPU尾部人工清零是不同步骤。

两个测试均以[B,H,K]=[4,1024,8]、expert_range=[0,32]构造随机专家ID；generator也写有INT8输入分支，但两个方法的dtype列表均只含上述三种浮点输入。它们分别比较INT8 expanded_x、映射和INT32 count，动态额外比较scale；BF16比较helper分支及任意expert_range、空专家总集合和drop_mode=1并未由此得到验收。完整包装16项ACLNN参数次序为x/expert_idx/scale/offset、active/capacity/expert_num、drop/statistics/before-capacity/quant属性，最后顺序写五个返回缓冲；不在本地重算排序、直方图或量化数学。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeInitRoutingQuantKernelNpuOpApi.cpp)（primary）

- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeInitRoutingQuantKernelNpuOpApi.cpp)（implementation）

- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_moe_init_routing_quant.py)（example）

## 精确审阅范围

- [MoeInitRoutingQuantKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MoeInitRoutingQuantKernelNpuOpApi.cpp)（primary）：1–151；完整本地文件。
- [MoeInitRoutingQuantKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MoeInitRoutingQuantKernelNpuOpApi.cpp)（implementation）：1–105；完整本地文件。
- [test_npu_moe_init_routing_quant.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_moe_init_routing_quant.py)（example）：1–251；完整本地文件。
- [test_npu_moe_init_routing_quant.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_moe_init_routing_quant.py)（example）：1–251；完整本地文件。
