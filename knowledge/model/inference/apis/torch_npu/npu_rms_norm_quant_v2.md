---
type: API
title: npu_rms_norm_quant_v2：scale 方向、打包与 rstd 有效性
description: 说明 950 单算子 RMSNorm 量化的 div_mode、可选参数、INT4 打包以及 requires_grad=False 的占位输出。
tags:
- task.lookup
- topic.compute.normalization
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_rms_norm_quant_v2.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RmsNormQuantKernelOpApiV2.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_rms_norm_quant_v2.md
  role: constraint
created_at: '2026-11-09T06:17:11Z'
updated_at: '2026-11-09T22:10:09Z'
platforms:
- '950'
---

# npu_rms_norm_quant_v2：scale 方向、打包与 rstd 有效性

## 版本与范围

依据 OpPlugin 固定主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的接口产品页及同提交 Schema，仅描述下列产品和参数路径，不回推到发布快照。文档支持、来源配套和设备验证分别核对。

## Schema 与计算顺序

```text
npu_rms_norm_quant_v2(x, gamma, scale, *, offset=None, beta=None,
    epsilon=1e-6, div_mode=True, dst_dtype=None) -> (y, rstd)
```

文档原型省略offset/beta的默认值，但同提交Schema明确二者为Optional Tensor、默认None。先RMSNorm乘gamma并加可选beta；div_mode=True按quant_in/scale+offset量化，False按quant_in*scale+offset，不能沿用旧接口的固定乘法方向。

x为1..8维ND，FP16/BF16/FP32，支持非连续、不支持空；gamma为(D,)或(1,D)，D=x尾维，dtype同x，beta与gamma同shape/dtype。scale为一维单元素且不为0。文档混合dtype矩阵允许：低精度x配同dtype scale及同dtype/INT8 offset；FP32 x配FP32 scale/offset；低精度x配FP32 scale及INT32或FP32 offset。不要把参数列表中各自允许的dtype做任意笛卡尔积。

dst_dtype默认None即INT8，可选quint4x2、float8_e4m3fn/e5m2、hifloat8。quint4x2实际以INT32承载8个INT4，y尾维为x的1/8；x尾维须被8整除，gamma/beta尾维需为偶数。其他输出通常同x形状。

## 训练中间量与模式限制

rstd有效时为FP32，norm维保留1。单算子根据**x.requires_grad**决定是否写出；False时返回shape=[0]空Tensor作无效占位，不要按正常rstd消费。文档明确仅单算子调用，训练/推理均列支持；不能据返回两个Tensor推定TorchAir模式也可用。

- [发布版固定乘法 scale 的旧接口](npu_rms_norm_quant.md)


## 核验

按同一计算顺序、激活模式和量化参数建立参考，检查输出数量、dtype、shape与别名；训练还需验证反向及保存的中间值。再比较正常负载的稳态时间和内存。本次未执行算子、图编译或设备性能测试。

## rstd 的 Meta 描述不能代替运行有效性

同提交C++明确用x.requires_grad()决定是否分配有效rstd，与产品页一致；Meta则始终分配尾维为1的FP32规格，没有复现无梯度时shape=[0]的分支。因此不能用Meta的非空shape证明Eager返回有效数据，也不借此突破本卡仅单算子模式的限制。

## 完整双语与底层V3契约

主线中英文只确认950PR及DT；训练/推理、仅单算子均按公开页，Meta存在不扩成图支持。公开原型把offset/beta列在*后但未写默认值，同提交schema才明确默认None；应按上文schema调用，不把Optional位置张量变成必填关键字。

C++此Python v2接口实际调用aclnnRmsNormQuantV3，不能把Python版本号或其他接口的ACLNN V2当作兼容性等价项。仅x.requires_grad决定有效FP32 rstd，否则明确分配[0]；只让gamma/beta需要梯度不改变此条件。Meta始终分配非空统计规格，不作Eager有效性证明。

INT4打包仍只明确quint4x2，N必须被8整除，实际INT32尾维N/8；NZ只见内部打包分配而非公开ND以外的支持承诺。FP8/HiFloat8不打包缩轴，HiFloat8用UINT8容器，不能把物理字节按普通整数恢复。静态scale的一维单元素、非零和整行dtype组合约束与旧接口分开；div_mode默认True，迁移旧乘法scale参数时不能仅替换函数名。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-npu_rms_norm_quant_v2.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RmsNormQuantKernelOpApiV2.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-npu_rms_norm_quant_v2.md)（constraint）
