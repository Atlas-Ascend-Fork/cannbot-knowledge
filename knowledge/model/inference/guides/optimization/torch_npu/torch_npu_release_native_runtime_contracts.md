---
type: Guide
title: 发布快照运行工具：CUDA映射、AMP、Storage与后端
description: 限定CUDA到NPU映射短名单、custom_fwd空白及存储/后端查询与执行的不同证据。
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

# 发布快照运行工具：CUDA映射、AMP、Storage与后端

## 来源与版本缺口

依据PyTorch/TorchNPU发布快照f3ecfe4a7ef7395754da7ca2e35661a7132b519b内docs/api/torch_npu_apis.md。它位于锁定发布源码内，但页面没有逐项的PyTorch小版本、CANN/包post、产品或参数支持矩阵，不能仅由父提交推为26.0/PT2.8所有组合的运行保证；本卡保留draft、platforms为空，待独立版本/硬件证据消解。

原表Y表示该文件声称兼容，仍须看限制；兼容性留空明确表示尚未验证。空白不是显式不支持，Y也不是本知识库新增verified或完整模型验收。类、方法、原地形式和同名函数逐行消费，不按父类、别名、相邻项或主线其他版本补全；这里没有执行/导入上游、编译、启动进程或设备实验。

## 替换前缀的说明受逐行映射约束

页面文字称torch.cuda.xxx改为torch.npu.xxx，但表只有45个Y映射；current_stream/default_stream/synchronize、Stream.query/record_event/synchronize/wait_event、Event.record/synchronize、CUDAGraph及capture/replay、memory_snapshot/PluggableAllocator等57行留空且没有NPU映射。不能据总述补出所有接口，未映射也不直接等于实现缺失。

set_device示例注释仍写torch.npu.set_device("cuda:0")，这是页面保留的字符串，不作为NPU设备类型正确示例。设备、同步、RNG、显存计数、分配器与流/事件逐项核对；同名Y既不保证具体产品支持Peer Access，也不改变跨流寿命/异步等待要求。

AMP表对torch.cuda.amp.autocast/custom_bwd/GradScaler及列出的scale/unscale_/step/update和状态/增长因子方法有Y及NPU映射，custom_fwd留空。torch.autocast行映射栏为“-”，torch.cpu.amp.autocast映射为自身，不造出同一torch.npu别名；也不由GradScaler列Y推定BF16需要/适配任何scaling策略。

## 后端查询、RNG和存储分别消费

backends中多项CUDA SDP/TF32、cuDNN/CPU库与MPS查询标Y，不表明CUDA/cuDNN/MPS计算已在NPU可执行；部分减精度开关、cuFFT缓存、cudnn.version/benchmark_limit与opt_einsum策略留空。表没有这些开关在NPU的语义、默认或精度保证。

random六个种子/状态入口和futures十个Future/回调/等待条目、overrides九个协议工具及__config__.show/parallel_info列Y；torch.cpu六行均留空。CPU/NPU RNG、全设备状态、进程与异步完成仍是不同协议，Future.wait的Y不自动证明任意NPU流已同步。

TypedStorage/UntypedStorage与常见标量Storage、部分转换/分配/共享查询列Y；bfloat16、complex、量化Storage及部分dtype/device属性、share_memory_等留空。TypedStorage.from_buffer/from_file有Y，UntypedStorage相同方法留空，不交叉继承；pin_memory/is_pinned的Y不承诺任意数据通路零拷贝或并行搬运收益。

## 所属表的证据范围

| 表 | Y条目 | 留空条目 | 有限制条目 |
| --- | --- | --- | --- |
| torch.cuda | 45 | 57 | 0 |
| torch.cuda.amp | 19 | 1 | 0 |
| torch.backends | 25 | 11 | 0 |
| torch.futures | 10 | 0 | 0 |
| torch.overrides | 9 | 0 | 0 |
| torch.cpu | 0 | 6 | 0 |
| torch.random | 6 | 0 | 0 |
| torch.Storage | 67 | 49 | 0 |
| torch.__config__ | 2 | 0 | 0 |

计数是该页目录记录数量，不是运行通过率；未给局部参数/默认值/组合条件时保持未知。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/docs/api/torch_npu_apis.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.md)（constraint）
