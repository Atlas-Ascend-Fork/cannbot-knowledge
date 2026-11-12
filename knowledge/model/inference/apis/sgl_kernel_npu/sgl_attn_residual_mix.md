---
type: API
title: SGL注意力残差快照的归一化打分与softmax混合
description: 说明 attn_res_mix_fused 的有效bank前缀、原值加权、不做末尾RMSNorm和空输入别名。
tags:
- task.implementation
- topic.attention
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/hyper_conn/attn_res_mix_fused.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/hyper_conn/attn_residual_mix.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/operators/hyper_conn/test_attn_residual_mix.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/kimi_k3/attn_residual.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-10T07:03:17Z'
platforms:
- a2
- a3
- '950'
aliases:
- attn_res_mix_fused
---

# SGL注意力残差快照的归一化打分与softmax混合

## 调用入口

```python
from sgl_kernel_npu.operators.hyper_conn import attn_res_mix_fused

def attn_res_mix_fused(
    prefix_sum,
    bank,
    num_valid_blocks,
    combined_weight,
    variance_epsilon,
    *,
    impl="auto",
):
    ...
```

## 计算边界

对每token，取bank的前B个快照与prefix_sum当前前缀组成B+1行；各行做RMS归一化后与combined_weight点积形成score，再行间softmax，以原始行值加权求和。输出到最终RMSNorm之前，不增加残差，也不写快照。combined_weight由调用方预先把score归一化权重与score投影逐元素相乘。

prefix_sum `[N,H]`，bank `[N,C,H]`，combined_weight `[H]`，同设备strided FP16/BF16/FP32，dtype可各不相同。0<=B=num_valid_blocks<=C，N可0，H>0；variance_epsilon有限正数。未使用的bank后缀不读取，可含NaN或未初始化值；参与的输入按有限数使用。

## 输出与布局

非空输出是同设备prefix_sum.dtype的新 `[N,H]` Tensor；N=0时直接返回prefix_sum本身且不启动kernel。B=0时仍执行FP32 RMS评分和softmax；只有评分及softmax可定义、无溢出的路径才有值等于prefix_sum的恒等结论，输入有限本身不足以保证（如H=2、prefix=[1,1]、FP32 weight=[3e38,3e38]会使score归约溢出）。非空仍分配新Tensor；这是源码条件分析，未做NPU数值复现。

Triton 在 N>0 时要求输入位于 NPU、prefix/bank末维stride1、weight stride1；N=0 仍检查 shape/dtype/同设备等基本元信息，但在设备类型与这些 stride 检查前返回原 prefix_sum，可为 CPU 或末维 stride=2 的空视图。token及bank行stride可不同；H通过二次幂补齐和mask处理，均方仍除真实H，支持7168等非二次幂尾部。auto选择triton，不自动失败回退；Triton按上述空/非空顺序检查元信息，torch_native仅作假定合法输入的数学参考。

## 验证信号

参考独立FP32计算后转回输入类型。覆盖B=0、bank无效后缀含NaN、非连续但末维连续视图和N=0别名；比较只关注有效快照。误把归一化行值参与加权或额外执行输出RMSNorm都会改变接口语义。

## 固定来源与验证状态

- [hyper_conn/attn_res_mix_fused.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/hyper_conn/attn_res_mix_fused.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。


## 旧Kimi-K3入口与新接口的可复用域

旧kimi_k3.attn_residual.mix_fused具有相同“RMS打分→softmax→原行值加权”数学，在N>0、H为可编译二次幂、末维连续且所有公开输入条件满足时可按该数学接入。它不是新Host/Device的全域别名：旧kernel直接tl.arange(0,H)且所有hidden load/store无mask，新kernel则BLOCK_H=nextPower2(H)、hidden_mask并仍按真实H求均方；因此新接口对7168等非二次幂的支持不能倒推旧实现。

旧Host先解包prefix的二维shape，N=0立即返回prefix，甚至早于检查B是否落在bank容量；非空只检查0<=B<=bank.shape[1]，未有新版对三Tensor rank/dtype/shape/同device、正H、epsilon有限正值以及非空NPU/末维stride1的完整guard。旧kernel用显式token/bank行stride，但hidden维按连续地址假定；不把Host没拒绝解释为宽域已支持。

两实现均按vector core持久切token，每program负责ceil(N/cores)个连续token，先逐B个bank行和prefix行计算FP32 score，再用最大值平移softmax，第二遍重读原值加权，最终转prefix.dtype写新输出。只保留NB=nextPower2(B+1)个逻辑score/probability与hidden向量，避免GM score矩阵物化；N/B显式do_not_specialize、H/EPS/NB和core数为constexpr，multibuffer=True。编译后的物理UB字节/并发临时未由此源码给出。

旧utils.triton_utils与新implementation/triton/utils中的get_device_properties核心相同，但属于两个模块的独立无参数@cache，首次读取current NPU的core数后不按device index作key。切设备/不同实现模块的缓存生命周期不能按一个全局device感知cache理解。此处只补旧可见实现与失败边界，保留前文新公开合同和平台范围，不声明旧入口已获同样平台验收。
