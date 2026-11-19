---
type: Guide
title: 发布快照原生Tensor与torch清单：dtype、形状和空白项
description: 保留发布API总表的四类型泛化限制及where、topk、sum差异，不套用主线逐参数支持表。
tags:
- task.lookup
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/docs/api/torch_npu_apis.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.md
  role: constraint
created_at: '2026-11-09T17:27:10Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 发布快照原生Tensor与torch清单：dtype、形状和空白项

## 来源与版本缺口

依据PyTorch/TorchNPU发布快照f3ecfe4a7ef7395754da7ca2e35661a7132b519b内docs/api/torch_npu_apis.md。它位于锁定发布源码内，但页面没有逐项的PyTorch小版本、CANN/包post、产品或参数支持矩阵，不能仅由父提交推为26.0/PT2.8所有组合的运行保证；本卡保留draft、platforms为空，待独立版本/硬件证据消解。

原表Y表示该文件声称兼容，仍须看限制；兼容性留空明确表示尚未验证。空白不是显式不支持，Y也不是本知识库新增verified或完整模型验收。类、方法、原地形式和同名函数逐行消费，不按父类、别名、相邻项或主线其他版本补全；这里没有执行/导入上游、编译、启动进程或设备实验。

## 先看限制定位到哪一层

该文件对许多torch函数和Tensor方法只写接口级“仅FP16、FP32、INT64、BOOL”，没有区分input/self、索引、权重、输出或标量参数。它既不是这些类型任意混搭的笛卡尔积，也不证明转换方法不能产生其他类型；例如Tensor.bfloat16、double等处于该泛化分组，不能据此推导BF16/FP64输出行为。不能把主线2.7.1/2.9..2.14的逐参数表回填到这份发布快照清单。

| 入口 | 本文件独立限制 |
| --- | --- |
| torch.ones/ones_like/squeeze/square/sub/tan/tanh/argmax/median/searchsorted | FP16、FP32、INT64，未列BOOL |
| Tensor.argmax/median/square/sub/sub_/tan/tanh/zero_ | 同三类型；不能自动给所有同名原地形式相同结论 |
| torch.acosh/arccosh/cosh/sinh/sqrt/xlogy/std/var/kthvalue | FP16、FP32 |
| 对应Tensor.cosh/acosh/arccosh/sinh/sqrt/xlogy及已列原地形式、std/var/kthvalue | FP16、FP32；按本表实有方法名消费 |
| torch.where、Tensor.where | 四类型，另写不支持8维shape；没有说明8维以外任意秩都支持 |
| torch.topk、Tensor.topk | 四类型，明确不支持sorted=False；不扩大成所有排序参数均受限 |
| torch.sum | 四类型，明确不支持dtype参数；Tensor.sum没有这句，不能交叉补齐 |

## 有Y、留空与名称不完整的边界

torch.tensor/as_tensor/asarray/from_numpy/frombuffer、RNG状态工具、save/load、类型探测、线程工具及torch.compile列Y但无局部限制；这不能推出所有外部数据零拷贝、反序列化可信或compile后端均可用。torch.rand/randn/randint的主入口留空，相应*_like却有Y与类型限制，两者仍按行分开。

Tensor.to/view/reshape、常见数学与索引条目有Y，不保证任意布局下无拷贝、别名关系或原地更新安全。Tensor.new_tensor、device、shape、requires_grad、record_stream、resize_等留空，不能由Tensor类本身Y覆盖。表还含没有完整限定名的to、torch.to、view、to_sparse条目，保持其名称证据不足，不擅自解析为某个正式重载。

torch.dtype/device/layout列Y，memory_format留空；finfo/iinfo及Named Tensors的names/rename/rename_/refine_names/align_as/align_to/flatten列Y。属性、格式、具名Tensor与真实算子布局支持是不同层次，不由这些条目宣布任意模型布局兼容。

## 所属表的证据范围

| 表 | Y条目 | 留空条目 | 有限制条目 |
| --- | --- | --- | --- |
| torch | 282 | 204 | 216 |
| torch.Tensor | 366 | 167 | 324 |
| Tensor Attributes | 3 | 1 | 0 |
| Type Info | 2 | 0 | 0 |
| Named Tensors | 8 | 0 | 0 |

计数是该页目录记录数量，不是运行通过率；未给局部参数/默认值/组合条件时保持未知。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/docs/api/torch_npu_apis.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.md)（constraint）
