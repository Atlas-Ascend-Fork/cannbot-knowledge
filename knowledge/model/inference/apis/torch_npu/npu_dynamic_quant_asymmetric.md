---
type: API
title: 动态非对称量化（torch_npu.npu_dynamic_quant_asymmetric）
description: torch_npu.npu_dynamic_quant_asymmetric：按输入范围同时计算量化值、scale 与 offset，支持 token、tensor 以及按专家分组的量化。 说明 A2/A3 pertoken 与950额外粒度、累计边界必须覆盖所有token，以及INT4与hifloat8物理容器。
tags:
- task.lookup
- topic.compute.quantization
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_dynamic_quant_asymmetric.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_quant_asymmetric.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_quant_asymmetric.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dynamic_quant_asymmetric.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DynamicQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DynamicQuantKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_dynamic_quant_asymmetric.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_dynamic_quant_asymmetric.py
  role: example
created_at: '2026-11-10T03:38:41Z'
updated_at: '2026-11-14T04:31:20Z'
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_dynamic_quant_asymmetric
---


# npu_dynamic_quant_asymmetric：零点、粒度与完整分组

## 版本和支持范围

依据 OpPlugin 固定主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`，按产品表和具体参数分支使用，不回推发布基线，不从单页类型名单推导任意混合组合。未执行上游代码、设备算子或图编译。

## 接口与非对称量化

```text
npu_dynamic_quant_asymmetric(input, *, smooth_scales=None,
    group_index=None, dst_type=None, quant_mode='pertoken',
    dst_type_max=0.0) -> (y, scale, offset)
```

按目标最大/最小值与输入极值生成scale和offset，量化round(x/scale+offset)，不能沿用对称量化的零点0假设。input为rank>1的FP16/BF16 ND，可非连续。smooth在量化前乘输入；Eager中dtype同input，图模式文档允许不同，但仍需具体实现支持。

## 粒度与分组

非MoE smooth是一维尾轴H元素；MoE为(E,H)，E在1..1024，与INT32 group_index的一维长度一致。group_index是**严格递增累计边界**，范围[1,S]且末值必须等于S（前置维度乘积），不能用count或未覆盖尾部的列表；有group_index时仅pertoken。

A2/A3只按pertoken处理，不支持quant_mode和dst_type_max的额外配置。950可选pertoken/perchannel/pertensor；对应FP32 scale/offset形状分别为去末轴、去倒数第二轴而保留末轴、(1,)。950的dst_type_max只在hifloat8生效，范围0..32768，0用目标最大值。

## 输出与产品

默认INT8；A2/A3另可quint4x2，950另可FP8/hifloat8。INT4输入尾轴8对齐，y实际INT32、末维缩为1/8；hifloat8用UINT8承载，其余形状同input。仅推理，文档列单算子和TorchAir模式；可选参数必须用关键字。


## 验证

先核对计算顺序、分组语义、scale方向与真实存储形状，再比较量化/反量化数值；覆盖空组、尾块、非连续和打包解码的实际需要。分别测内存与稳态收益，本文只有静态证据。

## 发布粒度与主线约束分别保留

发布中文明确quant_mode可pertoken或pertensor；主线中英文却写A2/A3暂不支持该额外参数、默认pertoken，950PR及950DT才列三种粒度。保留这个版本差异，不把主线收窄文字覆盖旧发布，也不以旧页扩主线A2/A3。主线perchannel的统计形状去倒数第二轴，FP32 offset与scale同形，HiFloat8的UINT8承载及dst_type_max条件分别消费。

两固定实现共享动态量化的V3/V4选择：两者都缺失时先回V2，quant_mode/dst_type_max不会下传；其他路径才检查相应符号，不能保证所有不兼容配置都会在此层被拒绝。两版Meta的INT4+perchannel输出同样可能把S轴错推为H；与Eager原形状尾维缩8不同，未有运行验证。

主线smooth的非MoE说明仍写一维末轴，与新perchannel模式如何配合没有完整消歧；不直接从对称接口复制全部smooth形状支持。两个TorchAir Converter均用GE DynamicQuantV2(is_symmetrical=False)，INT4再做打包变形。所有公式都未为常量行、零scale和舍入边界给出完整数值定义，不能从round字样外推这些结果。

## 非对称入口的完整分配与共享调度边界

两版该入口先验input rank>1，按对称接口同一规则准备FP32 scale，同时申请同形FP32 offset；pertensor时两者都换成(1,)。y仍按原始input形状与末轴INT4打包处理，不按scale/offset形状重建。attr.is_symmetrical置False，double dst_type_max转float；shared helper V3/V4才显式带该bool，V2的实参不带它。V2实际语义及offset对后端的影响仍由对应运行库核验，不用参数个数推断数值实现。

本入口没有对称入口的DO_COMPATIBILITY(v0)调用，不能把对称缺V2的兼容路径套到这里。共享helper的完整版本选择、物理dst_type和switch default边界见[对称接口](npu_dynamic_quant.md)新增合同；两份固定CPP均完整读取。发布从attr自有string取c_str，主线从原string_view.data转char*，同样不提供任意C++字符串寿命的运行保证。

## 完整非对称测试不覆盖全部数值边界

test_npu_dynamic_quant_asymmetric.py两版整个AST及全部注释相同。参考先FP32和平滑，再按末轴max/min得到scale=(max-min)/255、offset=127-max/scale；INT4分支改用15与7。随后round(input/scale+offset)转int8，scale/offset去末轴并转FP32；offset本身不先round为整数。perchannel参考在倒数第二轴作max/min。仅捕获Python ZeroDivisionError没有定义Tensor常量行/零scale或饱和clamp的完整行为。

同对称测试，分组发生器只排序随机边界并覆盖末项，可能出现0或重复；参考跳过end≤start，不是公开严格递增约束的验证。use_smooth参数没有控制是否生成smooth，调用者决定是否丢弃；perchannel smooth从(S,1)在调用端squeeze。INT4按uint8视图低/高nibble及算术右移解包成有符号int8。

前8项标Ascend910B，仅[2,32,256]的FP16/BF16、INT8/INT4、无平滑或64分组，y容差atol1/rtol0，scale/offset为atol0/rtol1e-4；950一项仅BF16 INT8 perchannel，三输出均atol0.01/rtol0.001。它们没有覆盖pertensor、INT4 perchannel、FP8/HiFloat8、非连续或零行的完整结果；本次未执行，测试装饰也不新增产品支持或verified。

## 已有 OpPlugin 7.3.0 文档与版本边界

### 动态非对称量化：torch_npu.npu_dynamic_quant_asymmetric

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

按输入范围同时计算量化值、scale 与 offset，支持 token、tensor 以及按专家分组的量化。

### 文档签名

```text
torch_npu.npu_dynamic_quant_asymmetric(x, *, smooth_scales=None, group_index=None, dst_type=None, quant_mode="pertoken") -> (Tensor, Tensor, Tensor)
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

返回量化结果、scale 和 offset，不能当成只返回两项的对称量化接口。`quant_mode` 区分 pertoken 与 pertensor；MoE 的 group_index 为递增的组结束边界，最后一项等于输入行数。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_dynamic_quant_asymmetric.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_quant_asymmetric.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_dynamic_quant_asymmetric.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_dynamic_quant_asymmetric.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DynamicQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DynamicQuantKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_quant.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dynamic_quant.py)（implementation）

## 完整实现与测试证据

- [d84e9b1 DynamicQuantKernelNpuOpApi.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DynamicQuantKernelNpuOpApi.cpp)（implementation）：完整本地文件1–255。
- [d84e9b1 test_npu_dynamic_quant_asymmetric.py](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_dynamic_quant_asymmetric.py)（example）：完整本地文件1–224。
- [dedc316 DynamicQuantKernelNpuOpApi.cpp](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DynamicQuantKernelNpuOpApi.cpp)（implementation）：完整本地文件1–232。
- [dedc316 test_npu_dynamic_quant_asymmetric.py](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_dynamic_quant_asymmetric.py)（example）：完整本地文件1–224。
