---
type: API
title: 前馈与专家前馈计算（torch_npu.npu_ffn）
description: torch_npu.npu_ffn：执行 FFN 或 MoE FFN；expert_tokens 的有无与编码决定分组路径。 `expert_tokens` 为空时是普通 FFN，非空时是 MoE FFN；专家分组编码仍须与实际参数版本和路由结果一致。 说明A2/A3两层FFN融合、专家列表互斥、GLU仅FP16高性能及量化/伪量化参数隔离。
tags:
- task.lookup
- topic.compute.composite
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_ffn.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_ffn.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FFNKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_ffn.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_ffn.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FFNKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_ffn.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_ffn.py
  role: example
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/ffn.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/ffn.py
  role: implementation
created_at: '2026-11-10T03:38:41Z'
updated_at: '2026-11-14T04:31:20Z'
platforms:
- a2
- a3
aliases:
- torch_npu.npu_ffn
- MoeFFN
---


# npu_ffn：专家分组、GLU门控与三类精度路径

## 固定版本与范围

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的产品页、Schema及同提交包装/Meta，未执行上游代码、图编译或设备实验。本文仅按公开A2/A3范围描述，具体差异不回推其他产品或历史版本。

## 接口与两层结构

```text
npu_ffn(x, weight1, weight2, activation, *, expert_tokens=None,
    expert_tokens_index=None, bias1=None, bias2=None,
    scale=None, offset=None, deq_scale1=None, deq_scale2=None,
    antiquant_scale1=None, antiquant_scale2=None,
    antiquant_offset1=None, antiquant_offset2=None,
    inner_precise=None, output_dtype=None) -> Tensor
```

非量化为activation(x@W1+b1)@W2+b2；伪量化先按(weight+offset)*scale反量化两份权重。量化路径的INT32 bias在相应反量化乘scale之前，不与浮点bias添加位置互换。产品表只A2/A3、推理，文档列图模式，不扩展到950。

x为rank2..8 ND，末维K1；无专家时W1=(K1,N1)、W2=(K2,N2)，有专家时增加E轴。输出沿用x前置维，末维为N2。需K1=N2，K1/K2<65536，token轴32字节对齐后小于INT32_MAX。

## 激活与专家分组

- gelu/fastgelu/relu/silu：N1=K2，支持专家或无专家，按对应类型分支选择高精度/性能与量化模式。
- geglu/swiglu/reglu：N1=2*K2，只支持**无专家、必选Tensor均FP16、inner_precise=1**；不能把普通SwiGLU接口的BF16支持带入此FFN融合路径。

expert_tokens和expert_tokens_index是Python整数列表（Schema int[]?），不是设备Tensor，长度最多256；C++禁止两者同时提供，并将后一种路径用tokens_index_flag区分。不能把“index”名称理解成任意token重排索引；有专家时所描述数据总数须与输入token数一致，不负责前置路由排序。

## 三类参数不能混放

|路径|输入/权重与bias|尺度、输出与精度|
|--|--|--|
|非量化|FP16或BF16，匹配对应浮点bias|不传量化或antiquant参数；BF16仅inner_precise=0，FP16可0/1|
|量化|x/W为INT8，bias为INT32|scale/offset FP32；输出FP16时deq_scale可INT64/UINT64/FP32，BF16输出需BF16 deq_scale；perchannel scale时FP16输出不列FP32 deq_scale|
|伪量化|FP16/BF16激活、INT8权重；FP16路径bias FP16，BF16路径bias FP32|两组antiquant scale/offset同激活dtype；不传量化scale/deq_scale|

deq_scale1/2 dtype须一致；有专家的通道尺度/bias需匹配(E,N1/N2)，普通路径去掉E轴。inner_precise=None包装默认0，量化/伪量化即使可传0/1也不据此承诺模式改变；output_dtype只量化生效、默认FP16，其他路径随x。

## 性能与验证

来源将GLU场景Vector耗时约30μs且占比超过10%作为融合尝试线索，不是任何小模型必然受益的保证。与同激活、同量化粒度和bias位置的两层参考比较，覆盖专家空组/总数与精度；再分开测编译和稳态，性能劣化时保留原组合实现。

## 发布对照、专家累计边界与输出推断

主线中英文与发布中文均只公开A2/A3推理图模式；文档附有单算子调用不扩充训练或950产品支持。两版C++均只检查x的rank及x末维等于weight1倒数第二维等局部条件，没有在此检查文档K1=N2，也未替调用方验证所有激活、专家长度、总token数和混合精度组合。

expert_tokens是各专家计数，expert_tokens_index是这些计数的累计终点；两版测试以np.cumsum构造后一列表。两种路径都要求按专家预分组的token顺序，不是每个token的专家ID，也不会自动执行MoE路由。C++以has_value判断互斥，即使同时显式传两个空列表也会拒绝；Meta没有这项检查，图形状推断成功不等于参数合法。

C++以deq_scale1是否提供决定是否选择量化输出dtype，而Meta以x是否INT8判定；对公开完整量化组合两者一致，非法混参可能分歧。这不是放宽三类参数隔离的依据。None精度默认0，非量化output_dtype不改变返回类型。两版GE转换器也保留专家列表互斥、INT64列表提升和tokens_index_flag；declare_supported的四个FP16例子只是一组声明，不替代公开类型和产品范围。

## 六项测试的证明范围

两版FFN测试各六项、只设A2门控，普通及伪量化覆盖FP16，INT8量化也只检查FP16输出。部分参考组合本身仍调用NPU算子，不是独立CPU参考；量化参考第二次INT32矩阵积先转FP16再反量化，也不能当作任意量化模式的通用黄金结果。

没有由这些测试证明BF16输出、GLU门控、高精度0、bias、rank大于2、256专家上限或任意空专家布局。发布测试与主线只有空白差异，不重复算作新增功能覆盖。本文保留源测试能说明的分组和调用语义，未执行上游或设备测试。

## 包装层的完整局部检查与18实参

两版完整FFN包装的形状检查是x秩在2..8，以及x末维等于weight1倒数第二维；并没有在此比较x末维与weight2末维。后者不能因文档的K1=N2约束被写成本地已检查。weight1/2的dim值虽先读取，EXPERT_WEIGHT_DIM=3、NO_EXPERT_WEIGHT_DIM=2、MAX_EXPERT_NUM=256也有声明，但这些变量/常量没有在本函数参与专家/权重秩检查；公开约束仍须满足，不能拿未用常量证明已经校验。

activation直接取string_view.data并const_cast为char*，这里没有激活名枚举或字符串重建。十个Optional Tensor分别用value_or(undefined Tensor)：bias1/2、scale/offset、deq_scale1/2、antiquant_scale1/2和antiquant_offset1/2；本地不会为缺失参数生成数值scale或bias。输出申请先复制x形状，把末维替换为weight2末维；仅deq_scale1.has_value时改用output_dtype或默认Half，否则用x dtype。此分支看Optional存在性，不是x是否INT8，也不要求该Optional中的Tensor已defined。

expert两列表都缺失时传空IntArrayRef，任一存在才检查互斥；优先选择expert_tokens，否则expert_tokens_index，tokens_index_flag单独按后一Optional的has_value确定。inner_precise缺省取0。apply_tensor_without_format不构成对激活、dtype、专家总量、完整GLU组合或所有weight2维度的验证。

传给aclnnFFNV2的18项依次为x、weight1、weight2、expert_tokens_real、bias1、bias2、scale、offset、deq_scale1、deq_scale2、antiquant_scale1、antiquant_scale2、antiquant_offset1、antiquant_offset2、activation_ptr、inner_precise_val、tokens_index_flag、result。两版完整非注释token与所有注释相同；本地没有另一个依据精度选择不同aclnnFFN版本的分支，不把inner_precise参数出现当成实际性能收益。

## 完整测试helper的量化和分组口径

两版整个test_npu_ffn.py的AST相同，全部原始差异仅空白。silu helper为x×sigmoid(x)；calc_ffn先在antiquant_scale1存在时按两权重各自offset/scale广播，在scale存在的另一分支才转INT32。量化参考首个matmul先乘deq_scale1再转FP16，激活后乘scale加offset、round/clamp[-128,127]并转INT32；第二个INT32 matmul先转FP16再乘deq_scale2。参考只实现relu/gelu/silu，其他激活不在这里给出结果，不把这个helper推广为全部公开激活的通用golden。

deq_scale_generate从FP32 0.01..0.05随机值取位表示，以0xFFFFE000清低13位来模拟高19位，再把这些uint32位填入高32位为0的uint64容器；不是把浮点值直接数值cast为整数。custom_op_exec再将该容器转int64 NumPy后构造传入Tensor，公开编码和真实接口类型必须一起核对。

supported_op_exec仅在expert_tokens列表为真时按计数split并逐专家调用参考、再cat；空列表走未分组分支，不等于已验证任意空专家布局。custom_op_exec三分支均显式inner_precise=1，量化分支把输入/权重/尺度移到NPU并构造反量化Tensor；普通/伪量化参考也可能已经在NPU，不能称为全独立CPU验证。

六项测试均标Ascend910B。普通/伪量化/量化使用8192×320和320×2560→2560×320；两个专家测试用340 token、16专家、5120→2560→5120以及固定计数列表，累计索引由np.cumsum得到。每项写有x与clone及输出的0.001比较，并未分别断言所有权重/尺度都未改变。量化两例只比较FP16默认与显式FP16输出，没有BF16/GLU/高精度0或边界失败分支测试结果；本次不执行这些测试。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 前馈与专家前馈计算：torch_npu.npu_ffn

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

执行 FFN 或 MoE FFN；expert_tokens 的有无与编码决定分组路径。

### 输入、输出与行为

`expert_tokens` 为空时是普通 FFN，非空时是 MoE FFN；专家分组编码仍须与实际参数版本和路由结果一致。

### 文档签名

```text
torch_npu.npu_ffn(x, weight1, weight2, activation, *, expert_tokens=None, expert_tokens_index=None, bias1=None, bias2=None, scale=None, offset=None, deq_scale1=None, deq_scale2=None, antiquant_scale1=None, antiquant_scale2=None, antiquant_offset1=None, antiquant_offset2=None, inner_precise=None, output_dtype=None) -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_ffn.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_ffn.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FFNKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_ffn.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_ffn.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FFNKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_ffn.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_ffn.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/ffn.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/ffn.py)（implementation）

## 完整实现与测试证据

- [d84e9b1 FFNKernelNpuOpApi.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FFNKernelNpuOpApi.cpp)（implementation）：完整本地文件1–109。
- [d84e9b1 test_npu_ffn.py](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_ffn.py)（example）：完整本地文件1–257。
- [dedc316 FFNKernelNpuOpApi.cpp](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FFNKernelNpuOpApi.cpp)（implementation）：完整本地文件1–76。
- [dedc316 test_npu_ffn.py](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_ffn.py)（example）：完整本地文件1–257。
