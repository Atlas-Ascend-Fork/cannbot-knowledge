---
type: Guide
title: 推荐模型推理基准：固定批次、同步时延与数据前提
description: 区分DCNv2/DIN/ETA/MMOE示例的数据、compile模式和重复单批推理计时，避免把输出文件当质量或全链路吞吐验收。
tags:
- task.optimization
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/inference/README.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/inference/DCNv2/dcnv2.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/inference/DIN/din.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/inference/ETA/eta.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/inference/MMOE/mmoe.py
  role: implementation
created_at: '2026-11-09T17:03:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 推荐模型推理基准：固定批次、同步时延与数据前提

## 固定来源与范围

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的inference README、DCNv2/DIN完整脚本及ETA/MMOE的配置/推理局部。未给完整产品/软件配套矩阵，故draft、platforms为空，不将“支持NPU”泛称映射为所有A2/A3/950；未运行、读取数据集或加载模型输出。

## 数据和模型不是统一的一套输入

DCNv2脚本读取CTR_Algorithm/data/data.csv并做类别编码/固定随机拆分；DIN实际读amazon-books-100k.txt及AmazonBookPreprocess，不是README对两者统一写的data.csv。外部CTR_Algorithm仓未固定在本基线，不能据clone命令复现完整模型实现。

ETA/MMOE要求Ali-CCP的预处理HDF5分片和spec等数据；README把预处理委托外部RecSDK，不把这些外部流程视为已摄入。data_dir默认./aliccp/aliccp_out/，源码部分以字符串拼接test/...，改路径须核对分隔符。ETA使用glob结果的第二个分片切片[1:2]，不是完整数据集；两者DataLoader示例batch4096、10worker、prefetch100，不是最优服务配置或所有环境都能负担的推荐值。

## 计时到底覆盖哪部分

四个示例都先从DataLoader取一个batch、迁移至设备，再反复运行这个固定批次；预热一次后每轮model.eval/no_grad前向并显式同步，再记录耗时，丢弃前10轮求平均。它测的是固定输入的同步模型调用，不含持续读取/预处理/H2D流量、排队、动态批处理和完整服务请求，也不是整个验证集的吞吐或业务精度评估。

DCNv2/DIN脚本示例batch32、默认200轮，用time.time；ETA/MMOE默认100轮、用perf_counter。ETA/MMOE不因参数说明保留train/eval字样就变成训练基准。固定轮数与批大小、输入shape/dtype、实际设备、精度及计时器要同时记录，不能直接对比这些不同任务的毫秒数。

四脚本设备探测优先CUDA，再尝试NPU，NPU路径设置MLIR环境；CLI的enable_compile不是一个NPU后端选择器。DCNv2/DIN/ETA使用dynamic=False，MMOE另设reduce-overhead；请求静态捕获仍需实际模式/shape/地址和算子支持。ETA还把输入int64 Tensor转int32，该输入约束不能套到其他脚本；MLIR版本/弃用边界独立核对。

## 结果与Profiler的证据边界

DCNv2/DIN在计时前保存首批输出到带模式的.pt，但没有在脚本中加载训练权重、对照eager/compile全输出或计算质量指标；两脚本也未显式固定模型初始化随机种子。ETA/MMOE设置2024种子，但种子不替代跨运行状态/数据一致性。输出文件存在不证明本次模式正确或模型质量通过，本文不读取或反序列化这些文件。

Profiler采用wait0/warmup=start/active=end-start+1，计时循环内进行step，采集会改变时间；测正常时延应另保留关闭采集的对照。CPU fallback分支与辅助函数对torch.npu属性的假设没有构成完整CPU可运行合同。README建议先应用DCNv2 patch、ARM执行unix2dos，是示例准备提示，不提供未经核对的全树转换/改源码操作。

- [版本基线](../../concepts/frameworks/ascend_software_stack_baselines.md)
- [计时与采集开销](torch_npu/torch_npu_profiler_measurement_overhead.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/inference/README.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/inference/DCNv2/dcnv2.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/inference/DIN/din.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/inference/ETA/eta.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/benchmarks/inference/MMOE/mmoe.py)（implementation）
