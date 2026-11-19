---
type: Guide
title: 发布快照工具清单：Profiler、基准、数据与打包
description: 区分Profiler对象与方法、Callgrind统计与Timer及工具存在和模型性能验收。
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

# 发布快照工具清单：Profiler、基准、数据与打包

## 来源与版本缺口

依据PyTorch/TorchNPU发布快照f3ecfe4a7ef7395754da7ca2e35661a7132b519b内docs/api/torch_npu_apis.md。它位于锁定发布源码内，但页面没有逐项的PyTorch小版本、CANN/包post、产品或参数支持矩阵，不能仅由父提交推为26.0/PT2.8所有组合的运行保证；本卡保留draft、platforms为空，待独立版本/硬件证据消解。

原表Y表示该文件声称兼容，仍须看限制；兼容性留空明确表示尚未验证。空白不是显式不支持，Y也不是本知识库新增verified或完整模型验收。类、方法、原地形式和同名函数逐行消费，不按父类、别名、相邻项或主线其他版本补全；这里没有执行/导入上游、编译、启动进程或设备实验。

## Profiler与基准测试分别判断

Profiler profile/profile.step、ProfilerAction/ProfilerActivity、schedule/tensorboard_trace_handler有Y；_KinetoProfile及其metadata/events/key_averages/trace/stacks/memory timeline方法、ITT等留空。它们没有CUDA表那样明确的NPU映射栏，不能由名字直接推出torch_npu.profiler的所有同名方法可用或产物已采集。

benchmark.Timer、blocked_autorange/timeit、Measurement.merge/significant_figures留空，Timer.collect_callgrind、Measurement/CallgrindStats/FunctionCounts及所列统计方法有Y。CPU指令统计工具的Y不是NPU设备计时已同步或整模型时延已准确测量的证明；torch.testing三个比较/造Tensor入口的Y也不替代真实模型数值/梯度验收。

monitor的14项类/统计/事件处理有Y，Aggregation.name、Stat.count/name、Event.data/name/timestamp六个属性留空；TensorBoard19项SummaryWriter/记录/flush/close有Y。写出事件文件不等于已记录全部rank、设备、窗口或环境；torch._logging.set_logs留空。

## 数据、依赖和打包边界

DataLoader、Dataset/IterableDataset及常见组合、collate、Sampler/DistributedSampler等19项Y，StackDataset留空；没有给worker、pin_memory、随机分片/恢复或真实数据吞吐保证。DLPack两入口、mobile_optimizer及PrivateUse1/回溯相关utils入口留空，不因数据对象可创建就补全互操作路径。

CppExtension/CUDAExtension/BuildExtension/load_inline、include_paths、ABI/Ninja工具有Y，cpp_extension.load留空；CUDAExtension名字不构成NPU自定义算子编译配方。Hub7项、package38项及model_zoo.load_url有Y，但不固定远端版本、信任边界或二进制依赖，也不证明包产物能脱离环境运行。

CUDA memory history/_snapshot/_dump_snapshot三项留空，和Profiler时间线、NPU分配器OOM快照是不同观测，不从任一文件存在推导另一路径已可用。本次没有打开/反序列化产物、下载数据或执行分析工具。

## 所属表的证据范围

| 表 | Y条目 | 留空条目 | 有限制条目 |
| --- | --- | --- | --- |
| torch.hub | 7 | 0 | 0 |
| torch.monitor | 14 | 6 | 0 |
| torch.package | 38 | 0 | 0 |
| torch.profiler | 6 | 13 | 0 |
| torch._logging | 0 | 1 | 0 |
| torch.testing | 3 | 0 | 0 |
| torch.utils | 0 | 4 | 0 |
| torch.utils.benchmark | 11 | 5 | 0 |
| torch.utils.cpp_extension | 8 | 1 | 0 |
| torch.utils.data | 19 | 1 | 0 |
| torch.utils.dlpack | 0 | 2 | 0 |
| torch.utils.mobile_optimizer | 0 | 1 | 0 |
| torch.utils.model_zoo | 1 | 0 | 0 |
| torch.utils.tensorboard | 19 | 0 | 0 |
| Understanding CUDA Memory Usage | 0 | 3 | 0 |

计数是该页目录记录数量，不是运行通过率；未给局部参数/默认值/组合条件时保持未知。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/docs/api/torch_npu_apis.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/README.md)（constraint）
