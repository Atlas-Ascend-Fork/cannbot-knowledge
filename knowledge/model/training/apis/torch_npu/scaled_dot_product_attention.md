---
type: API
title: PyTorch SDPA：NPU 掩码语义与融合路径选择
description: 说明原生 SDPA 的四维规格、布尔与加性掩码、MATH 控制、版本重载及 950DT 入图限制。并含 _transform_bias_rescale_qkv 探测失败整对 CPU 往返。
tags:
- task.lookup
- topic.attention
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn-functional.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/graph_supported_apis.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScaledDotProductAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/Version.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ScaledDotProductAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NativeMultiHeadAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NativeMultiHeadAttentionKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedSdpChoiceKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/TransfromBiasRescaleQKVKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/TransfromBiasRescaleQKVKernelNpuOpApi.cpp
  role: implementation
created_at: '2026-11-09T08:07:39Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# PyTorch SDPA：NPU 掩码语义与融合路径选择

## 版本与范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的PyTorch2.14逐API清单，产品为A2/A3训练系列、950DT；同提交2.7.1、2.9至2.13各版本页也列这三类产品和相应限制。这些是同一固定来源中的分版本文档，不构成主线与ascend_26_0_pt28配套证明，也不扩大950PR范围。实现核对OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`，未证明这两个主线快照已配套运行。

## 接口与规格

Schema为PyTorch≥2.5列下式重载，2.1..2.4重载没有enable_gqa；不能将内部源码注释中的版本名称替代Schema范围。

```text
torch.nn.functional.scaled_dot_product_attention(query, key, value, attn_mask=None, dropout_p=0.0, is_causal=False, *, scale=None, enable_gqa=False) -> Tensor
```

产品页限定同dtype的FP16/BF16/FP32、四维[B,N,L/S,E]；包装还要求相同设备。B∈[1,2048]，Q长度L、KV长度S∈[1,512K]，E∈[1,512]且Value的Ev=E，Q头数与KV头数比例是1..256的整数。内部融合分支的宽松条件不扩展公开产品规格。

scale=None按1/sqrt(E)计算，显式scale按模型定义传入；返回最终注意力结果，不能把内部FusionAttention的统计量元组当作SDPA返回协议。enable_gqa只在相应重载存在，是否与头数、选中实现一致须核对实际包，不能只凭该参数推断已复制或分片KV。

## mask极性与类型

BOOL mask的True表示允许参与，False表示遮蔽。融合路径先logical_not转为底层“True排除”的mask，数学路径将False填负无穷；手动调用[专用融合注意力](npu_fusion_attention.md)时不能直接沿用未经转换的布尔mask。

清单列[ B,1,L,S ]、[ B,N,L,S ]、[1,1,L,S]、[L,S]等，以及可广播的BOOL mask；实现只对已知可广播的2..4维形状预expand，其他形状交底层检查。广播写法不代表后续掩码转换必定零分配，应检查真实峰值及处理规模。

is_causal=True时必须attn_mask=None。参数说明将融合限制写为BOOL，但同页差异说明与实现允许同query dtype的浮点加性mask，它会走数学组合路径；其他mask dtype直接报错。浮点mask的值有加性偏置含义，不能仅为命中融合就强转bool或无条件取反，否则会改变结果。

## 融合选择与兼容模式

BOOL/None、四维及其他规格满足时，包装优先尝试训练FA路径；no_grad或requires_grad=False本身不保证选中后面的FIA分支。新重载中小于950的FA分支调用npu_fusion_attention_v3，950调用npu_fusion_attention；旧重载使用另一调用签名，不能按单一Kernel名覆盖全部版本。

FP32的任一Q/K/V尾轴不是4的倍数时会直接走数学路径。同dtype加性mask同样不能进入这两个BOOL/None融合分支。数学回退是NPU上的组合实现，不等同于转CPU，也不能用禁止CPU fallback开关证明命中了融合。

use_compatible_impl(True)后，包装在MATH启用且FLASH禁用时强制数学路径，任一尾维>256也会强制数学路径；未开启兼容模式时，不能仅凭SDPA后端上下文就认定这一包装遵循相同选择。该兼容标志在每个C++重载中以static首次读取，应在首次调用前设置；同进程后来改开关不保证已初始化重载改变行为。

融合路径以keep_prob=1-dropout_p下传；NPU的DSA随机算法与CUDA不同，不能用相同seed期待dropout逐元素一致。做跨实现精度对照时分开验证无dropout计算和随机统计。

## 图模式与验收

固定原生入图页另明确：950DT在列出的2.7.1、2.9、2.10、2.11、2.12、2.13、2.14不支持原生SDPA入图。Eager产品页支持不覆盖这个图模式限制；2.8未列，不能自行推定支持或不支持。专用FA接口需按各自卡片核对，不能由原生SDPA限制推出所有Attention接口不可成图。

验证先对齐布尔/加性mask、因果对齐、head比例和scale，检查实际Kernel与数学回退，再比较同输入的稳态耗时和峰值内存。本卡仅固定文档与实现静态审阅，未运行NPU、dropout、梯度或性能测试。

- [原生接口入图名单的产品脚注](../../../inference/concepts/frameworks/torchair_backend_boundaries.md)
- [CPU回退与兼容实现](../../../inference/guides/optimization/torch_npu/torch_npu_cpu_fallback_and_compatible_impl.md)
- [软件栈版本与来源身份](../../../inference/concepts/frameworks/ascend_software_stack_baselines.md)

## 固定实现的分支条件与掩码成本

以下细节来自OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的完整Host包装；发布快照 `dedc316708372c9a8bfde4527abd2a94b74840f5` 的差异单列于后。公开产品页的规格与平台限制继续适用，内部条件不是新的产品支持承诺。

前置校验只要求Q/K/V同dtype、同device且各rank≥2；有显式mask时还校验mask为BOOL或query dtype，并拒绝query/key为NestedTensor。主线新重载在这一步即拒绝 `is_causal=True` 与显式mask并用；旧重载未传此标志，其融合mask转换另有同样拒绝检查，数学分支如何处理仍取决于被调实现。

| 分支 | 本地选择条件及顺序 |
| --- | --- |
| FA | 在前述主线FP32提前数学回退和force_math之后，要求未force_math、BOOL/None mask、Q/K/V各rank4、FP16/BF16/FP32；Q/K头数各≤2048、Q尾维≤512、Q头数为K头数的正整数倍，以及SoC枚举≥Ascend910B1。 |
| FIA | 位于FA的 `else if`，同样要求未force_math，并要求Q/K/V均不需梯度、各rank4、Q四轴非零、FP16/BF16且Q尾维为16的倍数；有mask时BOOL且末两轴等于Sq、Skv；Q/K的B和D相同、K/V四轴全相同；B≤65536、Q/K头数各≤256、D≤512，K头数非零且Q/K头数整比≤64，SoC枚举≥Ascend910B1。 |
| 数学组合 | 未满足前面条件时将BOOL转为加性mask，调用 `_scaled_dot_product_attention_math` 并取结果0；新重载将enable_gqa传给数学实现。 |

这些条件是代码的实际先后顺序，不是独立后端选择菜单。FA条件没有在取模前单独保护K头数为零，也没有完整验证Q/K/V每个相容轴，不能把“未显式拦截”解释成支持空头或任意形状。正常正维形状下，FIA的较严谓词还会满足前面的FA候选条件，因此仅关闭梯度并不能让这个包装直接选中FIA；本地也没有捕获FA执行错误后再尝试FIA的流程。

主线mask预处理按右对齐判断2..4维能否广播到 `[B,N,Sq,Skv]`：每轴必须为1或目标值。精确 `[Sq,Skv]`，以及末两轴精确且前两轴为 `[B,N]`、`[B,1]` 或 `[1,1]` 的4维mask直接保留；其他已知可广播形状expand到完整四维，无法证明可广播的形状原样交下游。随后BOOL取反可能产生新Tensor，不能把expand视图当作整条路径无内存成本。

两版融合因果mask都由包装新建2048×2048 BOOL ones再取上三角，不是按当前Sq/Skv直接裁剪用户mask。FA以BNSD、Q头数、默认或显式scale、keep_prob=1-dropout_p下传；pre_tokens=2147483647，因果时next_tokens=0、sparse_mode=2，否则next_tokens=2147483647、sparse_mode=0。PSE、padding和实际序列长度等可选输入在这里为空。主线FA的inner_precise在非因果、Sq>1且原始mask存在时为2，其余为0；它不是按是否需梯度决定。

FIA代码若进入分支，在Sq=1时先把局部is_causal置false；Sq>1且非因果时inner_precise=2，其余0，再处理mask。它把Q/K头数分别传入，布局和token窗口同上，量化、页表、padding、实际长度等可选输入均为空，末尾相关模式为四个0和false。不要把专用FIA完整接口的量化、分页或其他优化能力反推为原生SDPA已在此开启。两类融合都只返回元组第0项，enable_gqa未作为独立参数传给融合调用；是否满足分组头规格仍须依据形状和实际下层实现。

## 发布快照不能直接沿用主线优化结论

固定发布快照的SDPA同样有无enable_gqa与带enable_gqa两个重载，FA/FIA主要候选条件、布局、窗口和返回第0项的原则相同，但有以下实质差异：

- 没有主线的FP32尾维非4倍数提前数学回退，也没有CheckCompatibleImpl、MATH/FLASH上下文或尾维>256强制数学分支。本卡前述兼容模式控制只描述已审主线，不能据此推定发布快照也服从该控制。
- 没有主线的可广播mask预expand。进入FA候选分支后，显式mask若既非2维也非4维，直接走数学组合；因此发布版3维BOOL mask不会像主线那样在这里预展开后继续FA。其他2/4维形状不在包装内完整校验后两轴，最终合法性由下层决定。
- 发布版两个重载的FA inner_precise均固定0，主线按非因果/Sq/mask选择2的逻辑不能外推。发布版FIA保留上述Sq=1局部取消因果及inner_precise条件，但没有预expand。
- 发布版新重载的前置validate没有is_causal参数；融合mask转换仍拒绝因果与显式mask并用，但不能据此声称所有数学路径都在同一前置位置拒绝。

这只是两个固定仓内包装的差异，不证明任意PyTorch/CANN/驱动版本已配套，也未执行实际注意力、梯度或设备性能测量。

## 相邻原生入口不能证明实际融合或CPU执行

主线 `_fused_sdp_choice` 的Schema登记为 `[v2.7,newest]`；其实现忽略Q/K/V、mask、dropout、因果、scale和enable_gqa，始终返回源码常量 `SDPBackend::overrideable = 4`。这个返回值不能证明选中了FA/FIA、完成了参数校验或成功执行Kernel。发布快照的同一路径Git树中没有该CPP，Schema也未出现同名条目；这里只记录精确入口缺失，不推断整个发布软件栈没有其他选择实现。

两版 `_native_multi_head_attention` 包装逐字节相同，Schema为all_version，接收Q/K/V、embed_dim、num_head、QKV及投影weight/bias、可选mask、need_weights、average_attn_weights、mask_type共13项，原样委托 `at::native::native_multi_head_attention_cpu` 并返回二Tensor元组。包装本身没有显式 `.cpu()`、设备拷贝或单独的投影/注意力运算；本卡未核对取外部ATen被调实现，不能仅凭函数名认定实际全部在CPU执行，也不能把它当作直接调用本卡SDPA融合包装的证明。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn-functional.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn-functional.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn-functional.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn-functional.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn-functional.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn-functional.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn-functional.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/graph_supported_apis.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScaledDotProductAttentionKernelNpuOpApi.cpp)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/Version.h)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/__init__.py)（implementation）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn-functional.md)（constraint）

## 完整与有界实现来源

- [ScaledDotProductAttentionKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ScaledDotProductAttentionKernelNpuOpApi.cpp)（implementation）：1–385；完整本地文件。
- [ScaledDotProductAttentionKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ScaledDotProductAttentionKernelNpuOpApi.cpp)（implementation）：1–319；完整本地文件。
- [NativeMultiHeadAttentionKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/NativeMultiHeadAttentionKernelNpuOpApi.cpp)（implementation）：1–42；完整本地文件。
- [NativeMultiHeadAttentionKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/NativeMultiHeadAttentionKernelNpuOpApi.cpp)（implementation）：1–42；完整本地文件。
- [FusedSdpChoiceKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FusedSdpChoiceKernelNpuOpApi.cpp)（implementation）：1–37；完整本地文件。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：3783–3785、4484–4492；仅所列Schema片段。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：3678–3680、4360–4365；仅所列Schema片段。

- [TransfromBiasRescaleQKVKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/TransfromBiasRescaleQKVKernelNpuOpApi.cpp)（implementation）：1–75；完整本地文件。
- [TransfromBiasRescaleQKVKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/TransfromBiasRescaleQKVKernelNpuOpApi.cpp)（implementation）：1–75；完整本地文件，与主线去空白字符流相同。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：5223–5224；仅所列Schema片段。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：5056–5057；仅所列Schema片段。

## _transform_bias_rescale_qkv：aclnn 探测失败时的整对 CPU 往返

aten::_transform_bias_rescale_qkv 是 SDPA 数学组合路径内部的 QKV 变换入口（登记 op_api all_version，主线 5223–5224、发布 5056–5057；无 acl_op 旧路径条目）。主线与发布两版本 包装（TransfromBiasRescaleQKVKernelNpuOpApi.cpp，各 75 行，去空白字符流相同）不走 DO_COMPATIBILITY，而是 `check_aclnn_kernel_available("aclnnTransformBiasRescaleQkv")` 符号探测，结果存函数级 `static const bool`：首次调用一次判定，同进程后续调用不再重新探测。

| 路径 | 实际门槛与动作 |
| --- | --- |
| 探测失败 | `TORCH_NPU_WARN_ONCE`（原文：operator 当前不被 NPU 后端支持、将回退 CPU 运行、建议升级 CANN 版本）后，qkv 与 qkv_bias **整对 `.cpu()`**，调 ATen CPU 实现 `at::_transform_bias_rescale_qkv`，q/k/v 三个结果逐个 `.to(qkv.device())` 回传 |
| 探测成功 | host 检查 `num_head != 0`、`D = qkv_bias.size(0)/3` 整除 num_head（两条 TORCH_CHECK/VALUE 原文文案），按 `[B, num_head, T, D/num_head]` 以 qkv dtype 申请三份 apply_tensor_without_format，单次 `aclnnTransformBiasRescaleQkv(qkv, qkv_bias, num_heads, q, k, v)` |

源码注释自述 NPU 暂不支持 Nested Tensor、相关逻辑未加入。本节与前节『相邻原生入口不能证明实际融合或CPU执行』口径互补：`_native_multi_head_attention` 只是委托 ATen、不能证明 CPU 执行，而本入口在探测失败时是**显式**的整对 CPU 往返。探测失败在哪些 CANN/SoC 组合上实际发生、往返的耗时与同步代价，均不在静态源内；未做设备验证。static 探测也意味着同进程内 CANN 环境变化不会重新判定。
