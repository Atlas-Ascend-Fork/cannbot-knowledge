---
type: API
title: 增量注意力（torch_npu.npu_incre_flash_attention）
description: torch_npu.npu_incre_flash_attention：基于当前 Query 和历史 KV 计算增量注意力。 区分A2/310P的增量注意力、分页KV和量化合同，核对发布/主线图转换与950明确拒绝边界。
tags:
- task.lookup
- topic.attention
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_incre_flash_attention.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_incre_flash_attention.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/flash_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_incre_flash_attention.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_incre_flash_attention.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_incre_flash_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_incre_flash_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_incre_flash_attention.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_incre_flash_attention.py
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/flash_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
created_at: '2026-11-10T03:38:44Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- 310p
aliases:
- torch_npu.npu_incre_flash_attention
- IncreFlashAttention
---


# npu_incre_flash_attention：增量注意力与分页 KV 条件

## 版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 完整产品页，本卡覆盖A2和310P推理；该页未列A3/950。TorchAir主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` Converter显式拒绝950。不能用统一FIA或其他FA接口的产品范围补齐此入口。

## 接口与输出

```text
npu_incre_flash_attention(Tensor query, Tensor key, Tensor value, *, Tensor? padding_mask=None, Tensor? atten_mask=None, Tensor? pse_shift=None, SymInt[]? actual_seq_lengths=None, Tensor? antiquant_scale=None, Tensor? antiquant_offset=None, Tensor? block_table=None, Tensor? dequant_scale1=None, Tensor? quant_scale1=None, Tensor? dequant_scale2=None, Tensor? quant_scale2=None, Tensor? quant_offset2=None, Tensor? kv_padding_size=None, int num_heads=1, float scale_value=1.0, str input_layout="BSH", int num_key_value_heads=0, int block_size=0, int inner_precise=1) -> Tensor
```

公开Python入口为torch_npu.npu_incre_flash_attention，前三项按序，其余关键字。A2的query为FP16/BF16 ND，key/value支持FP16/BF16/INT8且shape一致；310P按下表另行限定，三者rank一致。BSH为三维，BNSD/BSND为四维；输出shape同query。非量化输出dtype同query，传quant_scale2后输出INT8，不能把无输出量化的参考直接用于量化结果。

num_heads默认1，num_key_value_heads默认0表示同query；显式KV头数须整除query头数，比例≤64。A2页面上限B≤65535、N≤256、S≤262144、D≤512，不表示这些上限可以任意组合且都具备性能收益。

## 长度、掩码与量化组

actual_seq_lengths是各batch有效KV长度的Python整数列表（Schema为SymInt[]），长度B或1；不是累计前缀，也不是公开Tensor长度输入。padding_mask预留不用；atten_mask为BOOL/INT8/UINT8，1排除、0参与。pse_shift与query同dtype，D需16对齐。inner_precise默认1为高性能，0为高精度；scale_value默认1，模型需要1/sqrt(D)时应显式传入。

反量化scale/offset按KV布局：BNSD为[2,N,1,D]、BSH为[2,H]、BSND为[2,N,D]，dtype按产品FP16/BF16。dequant_scale1/quant_scale1/dequant_scale2分别用于BMM1后反量化、BMM2前量化、BMM2后反量化，不可与输出量化随意混配。三输入全INT8不支持；FP16输入转INT8输出需quant_scale2、可选quant_offset2，前三个中间量化因子必须None。quant_scale2/offset2支持FP32/BF16的pertensor/perchannel，offset可省略，不因传了offset就自行假定scale已满足。

## 分页与左padding

page attention需有效INT32二维block_table及每batch actual_seq_lengths。表行为batch，列覆盖所需逻辑块；有效值是[0,blocknum)物理块编号。KV可按[blocknum,Nkv,block_size,D]或[blocknum,block_size,H]连续存储，前者要求query BNSD；后者H超过64K受硬件限制。FP16/BF16 KV的block_size需16对齐，INT8需32对齐；128/256是页面常见值，不是固定默认。

blocknum需满足页面存储容量条件，表列覆盖最长请求所需块；长度不是block_size整数倍时必须覆盖尾部块，不能把文档除法描述照抄为截断分配。分页对吞吐和单token时延的影响应分别测量，不能只写“提高性能”。

kv_padding_size为INT64 Tensor，需同时有actual_seq_lengths才启用左padding。有效区间为[Smax-padding-length,Smax-padding)，负padding按0，页面说明起/终点小于0时输出全0；缺任一参数按右padding。

## 图与版本边界

页面列图模式并给单算子示例；TorchAir主线Converter把key/value各包装成单元素列表并构造GE IncreFlashAttention，不把它推广成公开Tensor[]输入。Meta按quant_scale2决定INT8输出的分支不验证全部产品限制。发布页的独立差异及测试边界见下文。


## 验证边界

按实际软件栈验证目标shape、dtype、mask语义和输出，再比较稳态性能。本次只做固定文档与实现的静态审阅，未执行上游代码或NPU数值/性能测试。

- [软件栈版本与来源身份](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 发布与主线的产品交集

完整来源为OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda的中英文页及发布dedc316708372c9a8bfde4527abd2a94b74840f5中文页；两版均列A2和Atlas推理系列加速卡（310P）。发布属于ascend_26_0_pt28；主线软件栈单独配套，不能只因参数相似便认证跨版本组合。

|产品|公开dtype与参数边界|轴上限|
|--|--|--|
|A2|Q为FP16/BF16，K/V为FP16/BF16/INT8；PSE与Q同dtype；输出量化scale/offset为FP32/BF16|B≤65535、N≤256、S≤262144、D≤512|
|310P|Q为FP16，K列FP16/BF16/INT8但V只列FP16/INT8；PSE只能None；antiquant尺度/偏移FP16；不支持quant_scale2/offset2，三个中间BMM尺度暂不用|B≤256、N≤256、S≤65536、D≤512|

310P单项K支持BF16不能推广成Q/K/V都BF16；主线通用分页段列BF16也不能绕过产品专门限制。三输入全INT8明确不支持。A3未公开确认；950不只产品页缺失，两版C++及两个TorchAir转换器都明确拒绝。

主线公式将发布简写query*key修成query@key^T，文档atten_mask公式仍写数值加法，但公开参数为1遮蔽、0参与的布尔/整数mask；不能把BOOL直接数值加到logit当作等价CPU参考。padding_mask是预留项，C++后端调用未使用它。

## 版本补充与量化合同

主线补齐GQA解释及QKV布局含义，实际num_heads是query头数、num_key_value_heads为0时同Q，否则须整除且比值≤64；actual_seq_lengths表示逐batch真实KV长度，非累计前缀，与训练Fusion Attention的actual_seq_qlen/kvlen不同。

发布分页段称吞吐提高但“性能下降”，主线明确代价可能是单token解码时延增加；两者都不是实测普遍提速承诺。主线补二维表[batch,maxBlockNumPerSeq]、逻辑块到物理块映射及物理索引范围[0,blocknum)，发布段虽少了部分文字，也不意味着发布允许越界映射。使用ceil(length/block_size)覆盖尾块，不按文档“除法”截断容量。

block_size是每物理块token容量，英文参数段误作head count不能照搬。浮点KV需16对齐、INT8 KV需32对齐；主线写128/256等常用值，默认仍0，不可当分页默认已有效。KV布局[BNSD页]与BSH页的吞吐/时延需分别验证，缓存内容、表和实际长度应同步维护。

quant_scale2存在才把输出推成INT8，quant_offset2只是可选偏移；Meta与C++均按scale是否存在分配，不因为offset单独非空就提供合法输出量化保证。QINT8时包装/Meta还能分配FP16输出，但公开产品合同及全INT8禁用仍适用，不能按分配成功扩展QINT8能力。

两版C++均把单个K/V Tensor封装为TensorList，调用aclnnIncreFlashAttentionV4；公开API仍只接单Tensor K/V，不因此接收任意多个cache块列表。主线仅比发布增加空input_layout检查，两个固定实现均未在此包装完整复验分页、dtype和量化组合，需后端配套验证。

## 图转换与GE的边界

两版TorchAir分别固定92e1e967bd35ebc37a442b4a969730bf3cf77a3c及7c6c754bed00c86ffaaa2a45cb7ac2724f058013。转换器语义相同：拒绝950，将K/V变为单元素列表，将非空actual_seq_lengths提升为INT64 Tensor，再传给GE IncreFlashAttention。转换器类型注解容纳Tensor是内部表示，不扩大Python Schema的SymInt[]长度输入。

Converter转发公开num_key_value_heads默认0，而生成GE函数自身默认1；从低层GE直接调用时不能照抄公开默认并省略属性。生成IR注释还列Q FP32/INT8、mask浮点、dequant_scale1/2为UINT64、antiquant为FP16，与公开API当前产品/dtype段不完全一致；实际转换器仅显式转换长度，未将所有尺度/掩码重解释成另一种存储。不能以陈旧IR枚举扩充公开支持，也不能把普通cast视为打包反量化因子的等价变换。

主线把图示例的TORCHDYNAMO_VERBOSE/TORCH_LOGS从普通Python局部赋值改为os.environ，才会作为环境变量影响日志。两个版本图示例只打印图与单算子结果，没有相等断言；示例中的日志、随机输出和torch.compile调用不是本次运行记录，更不代表310P图执行已验证。

## 测试与验收范围

主线custom/base测试全文52/59行，发布两文件逐字节相同。每文件一个910B方法，均为FP16、B1/N32、Q S1/KV S2048、D128，转BSH调用；参考MatMul/Softmax/MatMul也在NPU执行，不能称独立CPU golden。两个方法均有输出近似断言，但没有310P/BF16/GQA/INT8输出/反量化/分页/左padding/图转换测试。

本次只做静态来源核对，未执行上游或设备测试，无新增verified。应用时按目标产品分别验证图/Eager一致性、真实长度和分页边界、左padding有效区间及实际使用的量化组合；性能同时报告吞吐、单token时延和缓存占用，不能用宽产品表代替这些验收。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 增量注意力：torch_npu.npu_incre_flash_attention

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

基于当前 Query 和历史 KV 计算增量注意力。

### 文档签名

```text
torch_npu.npu_incre_flash_attention(query, key, value, *, padding_mask=None, pse_shift=None, atten_mask=None, actual_seq_lengths=None, dequant_scale1=None, quant_scale1=None, dequant_scale2=None, quant_scale2=None, quant_offset2=None, antiquant_scale=None, antiquant_offset=None, block_table=None, kv_padding_size=None, num_heads=1, scale_value=1.0, input_layout="BSH", num_key_value_heads=0, block_size=0, inner_precise=1) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_incre_flash_attention.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_incre_flash_attention.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/flash_attention.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_incre_flash_attention.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_incre_flash_attention.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_incre_flash_attention.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_incre_flash_attention.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FlashAttentionKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_incre_flash_attention.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_incre_flash_attention.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/flash_attention.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）
