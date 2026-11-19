---
type: API
title: RoPE 二维平面旋转位置编码（torch_npu.npu_rotary_mul）
description: torch_npu.npu_rotary_mul：RoPE 二维平面旋转位置编码。执行Rotary Position Embedding (RoPE) 旋转位置编码，通过对输入特征进行二维平面旋转注入位置信息。 区分A2/A3与950模式、广播、矩阵、梯度dtype和图转换，说明兼容回退可能丢失参数。
tags:
- task.lookup
- topic.attention
- topic.model_serving
status: stable
sources:
- resource: https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_rotary_mul.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md
  role: supporting
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_rotary_mul.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/davinci-magihuman/inference/model/dit/dit_module.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_rotary_mul.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_rotary_mul.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RotaryMulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RotaryMulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RotaryMulBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RotaryMulBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RotaryMulKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RotaryMulKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rotary_mul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rotary_mul_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/npu_fx_passes/joint_graph_passes/npu_rotary_mul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rotary_mul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rotary_mul_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/npu_fx_passes/joint_graph_passes/npu_rotary_mul.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/check_platform.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py
  role: implementation
created_at: '2026-11-10T03:38:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
aliases:
- torch_npu.npu_rotary_mul
---


# npu_rotary_mul：四种旋转、旧入口与图模式差异

## 版本与范围

发布A2/A3约束依据ascend_26_0_pt28固定组合；主线新增950PR及DT按独立固定快照描述，其软件组合尚未确认。Eager、旧ACL及图转换的模式、dtype与回退分别限定。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_rotary_mul(input, r1, r2, rotary_mode='half', rotate=None) -> Tensor
```

计算 input*r1+rotate(input)*r2，返回同 shape/dtype 的 Tensor。half 把尾维分为两半后拼接 (-后半,前半)；interleave 按奇偶对旋转。可选 rotate 提供二维变换矩阵，其数值和排列必须与模型 RoPE 约定一致。

## 参数与组合限制

- input/r1/r2 支持三维或四维 FP16/BF16/FP32，具体路径还有更窄限制。A2/A3 的 jit_compile=False：D<896 且为偶数，cos/sin 数值在 [-1,1]。
- half 路线 B,N<1000；若计算 cos/sin 反向，B*N≤1024。BNSD 的 r1/r2 可为 11SD/B1SD/BNSD，BSND 可为 1S1D/BS1D/BSND，SBND 可为 S11D/SB1D/SBND，TND 可为 T1D/TND。
- interleave 路线 B*N<1000，r1/r2 分别只支持上述布局的共享形式 11SD、1S1D、S11D 或 T1D，不能套用 half 的全部广播形态。
- jit_compile=True 的来源范围确认 A2：仅 half、四维、D=128，B/N≤1000，广播轴总数据量≤1024；本卡不扩展该路径到 A3。
- 传 rotate 不支持反向。训练可能保留 input，r1/r2 不求梯度时也可能比小算子组合占更多显存；BNSD half 的 D 未按 32 Bytes 对齐可能退化，融合不保证收益。

## 验证与模型关联

按模型采用的旋转约定对比输出，区分 half/interleave 与布局广播；需要训练时同时检查梯度、保留内存和 rotate 的禁用边界。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/davinci-magihuman/inference/model/dit/dit_module.py#L174)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)


## 主线950新模式与广播名单

主线中英文增加950PR及DT、FakeTensor，以及quarter和interleave-half。quarter把末维分成x1/x2/x3/x4，旋转项为concat(-x2,x1,-x4,x3)；interleave-half先把原输入偶/奇位置拼成p=concat(x_even,x_odd)，再用h=concat(-x_odd,x_even)，结果为p*r1+h*r2。后者连第一乘项的排列也变化，不能当成普通interleave或只替换rotate函数。

950的D≤1024，half/interleave/interleave-half按2整除，quarter按4整除；四维输入用(B,S,N,D)表述时，r1与r2的shape完全相同且只能从(1,1,1,D)、(B,S,N,D)、(B,1,N,D)、(B,S,1,D)、(1,1,N,D)、(1,S,1,D)、(B,1,1,D)中选，不能扩成全部NumPy式广播组合。input为空时输出为空且豁免这些shape限制。一般参数及950样例仍有三维输入，而该详细广播段以四维说明；不自行补造三维所有布局的名单。主线中文确认ND与非连续输入，英文省略这句话不等于否定。

950不支持显式rotate，须None或省略；主线包装在950及以上明确拒绝已定义的rotate，发布包装没有同一检查不构成产品支持。公开图调用示例仅标950PR及DT，属于使用说明，不是本仓已执行torch.compile的记录。

## 旧运行库、混合dtype与梯度

两固定包装在缺aclnnRotaryPositionEmbedding时退到ACL旧实现，在旧SoC也走该路线；旧实现只接受half，使用四维尾轴，且没有消费rotate。即使存在V1但没有V2，ACLNN V1调用也不传rotate。因此显式矩阵不能以“有兼容回退”为由宣称保留语义。950跳过了最初的两模式检查，但共享get_rotary_mode只定义half/interleave/quarter/interleave-half到0/1/2/3，其他字符串无默认返回，不代表可以传任意模式。

ACLNN正向在r1/r2与input的dtype不同时先转为input dtype；反向还把grad转为input dtype，dx按grad shape、dcos/dsin按各系数shape分配，但三者均用input的dtype。Meta反向也给系数梯度input dtype，不能保证保持原系数dtype。实际x仅在r1或r2任一个需要梯度时下传，否则传未定义Tensor；这不消除公开训练前向可能保留input的内存代价。

derivatives.yaml把self/r1/r2交给不带rotate参数的反向，并将rotate标为non_differentiable；不能由注册存在推定显式矩阵正向有受支持的反向。旧ACL反向的need_backward条件却是r1和r2都需要梯度，和ACLNN下传x的OR条件不同，不能机械把两条分支等同。旧ACL在D不被64整除或广播轴乘积超过1024时改用小算子组合；这只是实现分支，不扩大公开的shape上限。

公开构造get_interleave_matrix将两个互换位置都设为+1。按文档给出的右乘x@rotate公式，这是交换相邻元素，单独看不能产生标准(-奇,偶)的符号，故不把该样例矩阵当作通用数值金标准；仍按模型旋转约定核对，未运行或修改上游示例。

## 图转换与自动融合的独立限制

两个固定TorchAir正向转换器相同：is_arch35分支支持四种模式，调用GE RotaryPositionEmbedding但不传rotate；非该分支且rotate非None时只允许half/interleave并传矩阵；其余情况调用GE RotaryMul，完全没有传rotary_mode。因此非该分支的interleave且rotate=None不能据Eager能力假定图语义相同。平台辅助函数按设备名称判断：发布含Ascend910_95/Ascend950，主线还含Ascend350；通用分支名称不构成新增硬件产品契约。

图反向在is_arch35分支调用GE RotaryPositionEmbeddingGrad并传四模式；其他分支要求self/r1/r2四维，所有检查shape都是静态整数，末维被64整除且广播轴乘积≤1024。动态shape、不满足对齐或广播限制会拒绝，没有Eager旧ACL的小算子回退，也不传mode给旧RotaryMulGrad。need_backward是Converter附加的默认True参数，不能由此保证自动匹配Eager梯度掩码。

两个joint_graph_passes/npu_rotary_mul.py只匹配q*cos+rotate_half(q)*sin并替换为默认npu_rotary_mul；训练图与推理图均注册，没有torch_npu环境则跳过初始化。它们没有展示interleave、quarter或任意矩阵的自动匹配，计数器增长也不是性能获益。公开BNSD half非32 Bytes对齐可能退化、融合训练可能增加保存显存的提醒继续适用。以上均为固定源代码静态结论。

## 已有 OpPlugin 7.3.0 文档与版本边界

### RoPE 二维平面旋转位置编码：torch_npu.npu_rotary_mul

以下保留目标分支原有 API 卡的技术内容，固定来源为 OpPlugin 7.3.0 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`。本节的签名、默认值和产品支持仅适用于该文档版本；不与上文发布来源或主线候选的参数、平台范围交叉组合。实际部署仍需核对所安装 build，未进行设备运行验证。

### 用途与语义

执行Rotary Position Embedding (RoPE) 旋转位置编码，通过对输入特征进行二维平面旋转注入位置信息。

### 文档签名

```text
torch_npu.npu_rotary_mul(input, r1, r2, rotary_mode='half') -> Tensor
```

上述为 op-plugin 7.3.0 文档的调用形状，来源固定到 `b3065ed3ed174b08b7ecfcc564c0c464fb91fd13`，不是本机已执行代码；具体 Python 重载以目标 torch_npu build 为准。

### 适用范围与约束

官方支持表明确列出 A2、A3。其他目标产品须另查该版本的支持表。

源表分组：正式接口。

### 选型与继续核对

通用接入检查、版本与生命周期边界见 [TorchNPU 接口选型](../../guides/integration/torch_npu_api_selection.md)。

### Evidence

- [固定官方接口文档](https://github.com/Ascend/op-plugin/blob/b3065ed3ed174b08b7ecfcc564c0c464fb91fd13/docs/context/torch_npu-npu_rotary_mul.md)（primary）
- [迁出表](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-fusion/references/torch_npu_API/torch_npu_list.md)（supporting）

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu/torch_npu-npu_rotary_mul.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_rotary_mul.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_rotary_mul.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RotaryMulKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RotaryMulKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RotaryMulBackwardKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RotaryMulBackwardKernelNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/RotaryMulKernelNpu.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/RotaryMulKernelNpu.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rotary_mul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rotary_mul_backward.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/npu_fx_passes/joint_graph_passes/npu_rotary_mul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rotary_mul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rotary_mul_backward.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/npu_fx_passes/joint_graph_passes/npu_rotary_mul.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/check_platform.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py)（implementation）
