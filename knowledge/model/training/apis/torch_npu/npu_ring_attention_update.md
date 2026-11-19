---
type: API
title: npu_ring_attention_update：分步Attention与Softmax统计合并
description: 说明SBH/TND输入、FP32八槽统计、长度校验、V2调用与仓内参考测试的适用边界。
tags:
- task.lookup
- topic.attention
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RingAttentionUpdateKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_ring_attention_update.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-11T07:27:39Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# npu_ring_attention_update：分步Attention与Softmax统计合并

## 固定来源与接口

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的完整Host包装、完整小型参考测试及有界Meta/Schema。Schema的op_api与exposed均为 `[v2.7,newest]`；这不是任意PyTorch/CANN组合已经配套的证明。固定发布快照 `dedc316708372c9a8bfde4527abd2a94b74840f5` 的同名CPP和测试精确路径Git树均无条目，Schema未出现同名符号，只记录固定路径差异。

```text
torch_npu.npu_ring_attention_update(
    prev_attn_out, prev_softmax_max, prev_softmax_sum,
    cur_attn_out, cur_softmax_max, cur_softmax_sum,
    *, actual_seq_qlen=None, input_layout="SBH", input_softmax_layout=""
) -> (attn_out, softmax_max, softmax_sum)
```

它接收已经取得的前一块与当前块attention及softmax max/sum，没有在本地实现跨rank通信。它与接收LSE/输出列表的 [npu_attention_update](../../../inference/apis/torch_npu/npu_attention_update.md) 使用不同状态表示和接口，不可只凭同属Attention合并直接互换。

## 布局、类型与本地校验

| 输入 | 本地明确约束 |
| --- | --- |
| 两个attention | 都为3维，shape/dtype相同；仅FP16、FP32、BF16。SBH和TND均在此以3维Tensor表示。 |
| 四个softmax统计 | shape全部相同，均FP32，最后一轴必须为8；SBH时rank4，TND时rank3。 |
| input_layout | 仅大小写精确的SBH或TND。 |
| input_softmax_layout | 仅空字符串、SBH或TND；此枚举检查不等于任意交叉布局组合已验证。 |
| actual_seq_qlen | TND必须存在且defined；只要可选Tensor存在且defined就要求INT64，SBH也遵循这条dtype检查。 |

包装没有在这里完整核验统计量各前导轴与attention的映射、head_dim整除关系、所有Tensor同设备、连续性、长度Tensor的rank/单调性/终值或每段长度。缺少这些检查不是放宽底层输入约束的证据，也不能把SBH/TND字符串校验当作完整布局认证。

Host通过prev_attn_out、prev_softmax_max、prev_softmax_sum分别 `apply_tensor_without_format` 分配三个输出，调用 `aclnnRingAttentionUpdateV2`。ABI按六个前/当前Tensor、actual_seq_qlen、两个布局字符串、三个输出的顺序下传；可选长度缺省时转成未定义Tensor。包装不修改输入来复用输出缓冲，也没有在本地实现数学备用分支或失败后重试。是否存在下层工作区、额外转换或特定Kernel支持，本卡没有执行证明。

## 稳定合并公式与参考范围

仓内CPU参考先把两组attention及统计slot0转FP32。记两组max为mₚ、m꜀，sum为sₚ、s꜀：

```text
m = max(mₚ, m꜀)
a = exp(mₚ - m), b = exp(m꜀ - m)
s = sₚ*a + s꜀*b
out = prev_attn_out*(sₚ*a/s) + cur_attn_out*(s꜀*b/s)
```

SBH参考从统计的N维推得head_num，将 `[S,B,H]` reshape为 `[S,B,N,D]` 并重排权重；TND直接广播最后一轴。最终attention转回原dtype，m/s各重复到末轴8个槽并contiguous。因此测试只构造8个相同槽，不覆盖统计各槽不一致的行为。参考没有给分母加epsilon，也没有专门处理两组max均为负无穷或sum为0，不能自行推定这些退化输入的设备策略。

## Meta描述和测试不能扩展运行支持

有界Meta函数重复布局、shape、dtype、rank、末轴8和TND长度存在性检查，返回三个与前一组对应Tensor同shape/dtype的 `device='meta'` empty_like。Python可选长度检查使用is not None，C++另判断defined；Meta没有执行aclnn或通信，形状可推导不代表编译、反向或设备运行已验证。

完整测试只包含两种小尺寸：SBH的S=4、B=2、N=2、D=16；TND的T=5、N=2、D=64，长度为INT64 `[2,5]`。两者循环FP16/FP32/BF16，设备筛选装饰器列Ascend910B、Ascend910_93、Ascend950；本卡不据装饰器添加已验证平台。随机max/sum带正偏置，三输出均以prec16=0.005与CPU参考比较，但没有本卡执行结果。

TND参考计算不消费actual_seq_qlen，不能用该数值对照证明多种长度分段、非法长度拒绝或非平凡padding语义。没有梯度、原地别名、跨rank、性能、大规模、空输入或图捕获实验；input_softmax_layout只覆盖SBH缺省空串和TND显式TND，没有完整交叉组合。

## 与上下文并行调用链的边界

已固定的 [TorchNPU上下文并行状态指南](../../guides/torch_npu_context_parallel_ring_softmax_state.md) 说明BNSD到SBH转换、FP32统计、callable探测及逐步缓存。该消费者选择op或Python合并发生在closure构造时，不是算子失败后重试。这里补的是被调OpPlugin入口，两个仓库固定提交尚未作设备配套验证；TND入口存在也不扩大该CP消费者当前只接BNSD的边界。

## Evidence

- [RingAttentionUpdateKernelNpuOpApi.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RingAttentionUpdateKernelNpuOpApi.cpp)（primary）：1–167；完整本地文件。
- [test_npu_ring_attention_update.py](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_ring_attention_update.py)（example）：1–135；完整本地文件。
- [_meta_registrations.py](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）：6245–6315；仅此有界完整函数或Schema。
- [op_plugin_functions.yaml](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：5890–5892；仅此有界完整函数或Schema。
