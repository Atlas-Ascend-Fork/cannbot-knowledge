---
type: Guide
title: 发布快照数学与量化清单：配置支持和执行缺口
description: 保留量化配置/Observer的Y与量化转换/算子空白，限定linalg和special短名单。
tags:
- task.optimization
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/docs/api/torch_npu_apis.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.md
  role: constraint
created_at: '2026-11-09T17:27:10Z'
updated_at: '2026-11-09T17:27:10Z'
platforms: []
---

# 发布快照数学与量化清单：配置支持和执行缺口

## 来源与版本缺口

依据PyTorch/TorchNPU发布快照f3ecfe4a7ef7395754da7ca2e35661a7132b519b内docs/api/torch_npu_apis.md。它位于锁定发布源码内，但页面没有逐项的PyTorch小版本、CANN/包post、产品或参数支持矩阵，不能仅由父提交推为26.0/PT2.8所有组合的运行保证；本卡保留draft、platforms为空，待独立版本/硬件证据消解。

原表Y表示该文件声称兼容，仍须看限制；兼容性留空明确表示尚未验证。空白不是显式不支持，Y也不是本知识库新增verified或完整模型验收。类、方法、原地形式和同名函数逐行消费，不按父类、别名、相邻项或主线其他版本补全；这里没有执行/导入上游、编译、启动进程或设备实验。

## 数学别名与命名空间不互相补齐

linalg仅norm有Y及四类型泛化限制，其他40行留空；special仅logsumexp/xlogy有同类Y和限制，其他36行留空。即使torch.logsumexp、torch.sqrt或Tensor方法存在Y，也不能据同名/等价关系给torch.special、linalg或别名自动填支持。

完整distributions表508项、FFT22项、signal.windows11项、nested3项和sparse26项均留空，含采样/分布属性、变换/约束、稀疏构造/求和/mm/softmax/格式检查等。表没有声明这些永远不可用，也没有提供设备/dtype、稀疏布局、随机状态与梯度合同；需要独立证据，不能将空白当已验证实现。

## 量化前端配置不代表INT8模型执行

271个量化条目中82个Y并泛写FP16、FP32、INT64、BOOL，集中于QConfigMapping、BackendConfig/BackendPatternConfig/DTypeConfig、部分FX custom config、Observer与Numeric Suite对象；同时也包括dynamic LSTM/GRU/RNNCell等少量条目。泛化dtype文案没有定位配置对象的Tensor参数或量化权重，不能推出只允许四类型、禁止INT8权重或支持任意量化组合。

quantize/quantize_dynamic/quantize_qat、prepare/convert、FX prepare/convert/fuse、FakeQuantize、qconfig预置、大量quantized/qat/动态Linear及Numeric Suite FX入口仍留空。Observer/配置类Y与其from_dict/默认工厂留空分别处理；能配置、收集统计、生成/加载权重、执行量化算子及验证模型精度不能合并成一个“量化已支持”。

本页没有OpPlugin自定义量化Matmul、低比特分组或融合attention的完整契约，不能用这些配置表替代已锁定自定义API的dtype/shape/硬件/版本限制。

## 所属表的证据范围

| 表 | Y条目 | 留空条目 | 有限制条目 |
| --- | --- | --- | --- |
| torch.distributions | 0 | 508 | 0 |
| torch.fft | 0 | 22 | 0 |
| torch.linalg | 1 | 40 | 1 |
| torch.signal | 0 | 11 | 0 |
| torch.special | 2 | 36 | 2 |
| Quantization | 82 | 189 | 82 |
| torch.nested | 0 | 3 | 0 |
| torch.sparse | 0 | 26 | 0 |

计数是该页目录记录数量，不是运行通过率；未给局部参数/默认值/组合条件时保持未知。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/docs/api/torch_npu_apis.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.md)（constraint）
