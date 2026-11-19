---
type: API
title: 逐 Token 对称动态量化（torch_npu.npu_dynamic_quant）
description: torch_npu.npu_dynamic_quant：逐 Token 对称动态量化。对输入的张量进行pertoken对称动态量化。 说明 INT8/INT4 打包、FP32 scale，以及平滑量化分组使用累计边界的约束。
tags:
- task.lookup
- topic.compute.quantization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_dynamic_quant.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_quant.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dynamic_quant.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DynamicQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DynamicQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_dynamic_quant.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_dynamic_quant.py
  role: example
created_at: '2026-11-10T03:38:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_dynamic_quant
---


# npu_dynamic_quant：逐 Token 量化与 MoE 累计分组

## 版本与范围

本文依据 `ascend_26_0_pt28` 发布来源组合中 OpPlugin 的固定提交；仅描述下列平台及参数路径。来源配套与实际部署验证分别核对。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_dynamic_quant(x, *, smooth_scales=None, group_index=None, dst_type=None) ->(Tensor, Tensor)
```

对每个 token 的末维做对称动态量化，返回 (y,scale)。默认 dst_type=None 按 INT8 处理；选择 quint4x2 时，实际 y 为 INT32 打包，每个元素承载 8 个 INT4，末维缩小 8 倍。scale 为 FP32，shape 为 x 去掉末维。

## 参数与组合限制

- x 为维数大于 1 的 FP16/BF16 ND Tensor，支持非连续；INT4 路径要求末维为 8 的倍数。
- 无 group_index 时，smooth_scales 必须是一维，长度等于 x 的末维。
- 有 group_index 时，它是一维 int32，长度等于二维 smooth_scales 的首维；smooth_scales 的末维等于 x 的末维。
- 这里 group_index 是严格递增的累计 token 边界，末项等于 x.numel()/x.shape[-1]，不是各组独立 token 数。不要沿用 npu_dequant_swiglu_quant 的 count 语义。

## 验证与模型关联

分别核对逐行量化误差、scale shape 和 INT4 解包；以多组不同 smooth 向量验证累计边界，覆盖边界误传为 count 的反例。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_r1/models/modeling_deepseek.py#L1248)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 主线新粒度、版本签名与产品范围

发布页签名只列x及三个可选参数；两固定schema却都已有quant_mode='pertoken'、dst_type_max=0.0，声明存在不等于发布页已确认全部新产品。主线中英文改名input，新增950PR及950DT；A2/A3仅默认pertoken，950另可perchannel/pertensor及FP8/HiFloat8，HiFloat8由UINT8承载。

scale为FP32：pertoken去末轴，perchannel去倒数第二轴而保留末轴，pertensor为(1,)；perchannel不是把所有前置维一并归约。无group时，前两种逐token/整体模式的smooth向量沿末轴，perchannel沿倒数第二轴；group_index存在则smooth必需、二维专家数1..1024，并仅pertoken。Eager的smooth dtype同input，图模式按文档和实际Converter另核对。dst_type_max仅950的HiFloat8取0..32768，0采用目标最大值。

## CANN回退和Meta不构成能力证明

两版按V3/V4符号探测选择实现；**两者都缺失时先返回V2，早于新参数校验，V2调用不会传quant_mode/dst_type_max**。非默认粒度路径还检查V3，非零dst_type_max要求V4。对称量化缺V2时的v0回退连group_index也未传底层。因此成功返回不能证明新增属性或分组已生效，也不能仅据文档签名推断旧CANN会可靠报错。

两版Meta在INT4+perchannel时把scale_shape再追加H/8，得到(...,H,H/8)，Eager则按输入原形状得到(...,S,H/8)；S与H不同时存在静态形状冲突。图组合不能仅凭Meta通过判为可用。两个固定TorchAir后端默认pertoken/max=0用GE DynamicQuant，其他粒度用GE DynamicQuantV2，并把逻辑INT4经Reshape/Bitcast打包为INT32；GE与ACLNN的V2/V3编号不能互作版本兼容表。

## 完整Host分配与版本选择合同

完整DynamicQuantKernelNpuOpApi.cpp同时实现对称、非对称和共享helper，非对称局部差异见[对应接口](npu_dynamic_quant_asymmetric.md)。get_output_tensor_wrapper只按input原形状和指定index准备y，scale_size形参没有用于这个计算。QUInt4x2分支要求该轴整除8并缩小8，申请Int Tensor且y_acltype=ACL_INT32；None申请Char/ACL_INT8；其他目标经GetAclDataType及convert_to_scalar_type申请。不能把物理INT32打包解释为普通INT32数值量化，具体可用目标类型仍受产品/运行库约束。

两种公开入口先检查rank>1；对称入口随后才做缺V2时的v0兼容。正常路径的scale为FP32，先保留除末两轴外前缀，perchannel补末轴H，其余先补倒数第二轴S，pertensor再替换为(1,)；y始终从input原形状做末轴打包，而非从scale形状重建。对称offset为缺省Optional；共享attr保存quant_mode字符串、is_symmetrical=True、物理目标dtype以及从double窄化的float dst_type_max。

V3/V4探测为函数static bool，选择顺序是：两者都不存在先回V2；否则非零dst_type_max需V4；否则非pertoken需V3，再在可用时选择V4；其余仍V2。因此不能仅因V4存在就省掉非默认模式的V3检查，默认模式也不自动用最高版本。本文件没有另行检查全部模式字符串、数值上界、smooth/group内容与公开产品组合。

V4宏实参依次为input、smooth、group、dst_type、is_symmetrical、quant_mode、dst_type_max、y、scale、offset；V3不带max，V2也不带symmetrical与quant_mode。声明的V1常量并未由当前select_version返回；switch default虽调用v0，却丢弃其返回tuple，不据该default推导已验证的新公开回退路径。真正对称v0用FP32去末轴scale，调用aclnnDynamicQuant时不带group_index，并返回新output/scale。

两版选择及分配结构一致，但字符串调用点不同：发布helper从attr.quant_mode的自有std::string取c_str，主线入口把原string_view.data经const_cast转char*交helper。这里只记录指针来源，不声称任意外部C++调用或字符串寿命已运行验证；底层转换/ACLNN函数也不因Host源码完整阅读而视为已核验。

## 完整对称测试的参考、分组与解包

完整test_npu_dynamic_quant.py两版AST与全部注释相同。参考将输入转FP32，按group累计边界逐片乘smooth，或无group时直接广播；末轴abs max除以127（INT8）或7（INT4）得到scale，round(x/scale)，再转int8或int32参考。代码只有Python ZeroDivisionError的catch，没有为Tensor零行/零scale明确定义额外结果或进行数值修复。

generate_input即使use_smooth=False也生成smooth；无平滑测试实际丢弃它。分组发生器从[0,row_num)随机取边界、排序、末项改row_num，因此可能含0与重复；参考对end≤start跳过。此处测试生成规则与公开“严格递增”约束不同，不能拿测试文字反向放宽产品合同，也不能说它覆盖了非法分组应报错的行为。perchannel发生器为倒二轴生成(S,1) smooth，调用时squeeze成S向量。

convert_int4_to_int8先把容器按uint8视图展平，再按每字节低/高nibble次序解包，用int8右移符号扩展后拼接；它不是数值cast或随机重排。前8项标Ascend910B，shape均[2,32,256]，组合FP16/BF16、INT8/INT4以及无smooth或64分组；y容差atol1/rtol0，scale为atol0/rtol1e-4。950一项只测试BF16 INT8 perchannel，y容差0.1/0.01、scale0.01/0.001。没有由这些测试证明pertensor、INT4 perchannel、FP8/HiFloat8、零scale或不整除8的错误分支，也没有本次运行结果。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 逐 Token 对称动态量化：torch_npu.npu_dynamic_quant

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

对输入的张量进行pertoken对称动态量化。

### 文档签名

```text
torch_npu.npu_dynamic_quant(x, *, smooth_scales=None, group_index=None, dst_type=None) ->(Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_dynamic_quant.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_quant.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dynamic_quant.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DynamicQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DynamicQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_quant.py)（implementation）

## 完整实现与测试证据

- [d84e9b1 DynamicQuantKernelNpuOpApi.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DynamicQuantKernelNpuOpApi.cpp)（implementation）：完整本地文件1–255。
- [d84e9b1 test_npu_dynamic_quant.py](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_dynamic_quant.py)（example）：完整本地文件1–213。
- [dedc316 DynamicQuantKernelNpuOpApi.cpp](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DynamicQuantKernelNpuOpApi.cpp)（implementation）：完整本地文件1–232。
- [dedc316 test_npu_dynamic_quant.py](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_dynamic_quant.py)（example）：完整本地文件1–213。
