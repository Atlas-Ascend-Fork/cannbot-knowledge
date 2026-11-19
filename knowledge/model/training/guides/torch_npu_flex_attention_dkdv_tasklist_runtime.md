---
type: Guide
title: FlexAttention dK/dV 任务列表：选择、元数据缓存与拆分内存
description: 补齐显式 bwd_dkdv 分派的静态门槛、负载启发式、版本计数缓存及FP32 partial/reduce成本。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention_tasklist.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention_dispatch.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/select_algorithm.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/wrapper.py
  role: implementation
created_at: '2026-11-10T11:54:20Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FlexAttention dK/dV 任务列表：选择、元数据缓存与拆分内存

## 固定范围与明确可达路径

本卡按 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 lowering、tasklist helper和复合dispatch定向审阅。只对明确设置 `flexattention_dispatch_strategy="bwd_dkdv"` 后附着到候选、由dispatch plan及codegen消费的路径作结论；候选最终被选中仍须核对产物。

没有运行设备、导入上游、验证稀疏梯度或测量收益。发布固定快照缺少上述主线路径，不回推发布能力，整卡 `draft`、空平台。文档开关与本实现的差异见[开关卡](flex_attention_backward_tasklist.md)，反向其他路线见[反向分路与输出](torch_npu_flex_attention_backward_routes_and_gradients.md)。

## 先满足静态与资源条件，再谈运行期选用

lowering先要求mask-out、没有所检查的动态维度，并通过tasklist reduce的UB容量筛选；源码用 `3*BLOCK_N1*max(QK_HEAD_DIM,V_HEAD_DIM)*4 <= floor(UB大小*4/5)` 保留候选。没有安全候选时关闭该图tasklist codegen，不是把tile或结果截断到UB。

局部资格函数还要求Bq/Bkv/sparse_z/sparse_hq均为Python int，Bq=Bkv=sparse_z=1、sparse_hq=1，BLOCK_N1>0且SPARSE_KV_BLOCK_SIZE可整除它，两份Q方向block count元数据连续且INT32，累加为FP32。C++ wrapper和AOT被兼容检查拒绝；显式复合plan还声明Python-only上下文能力。

不满足条件时，显式plan带回退原因并回primary dK/dV。满足这些条件也不保证最终启用任务列表：运行期另计算负载。所读资格与错误回退不能当作完整元数据合法性或设备支持验证。

## 运行期启发式看工作权重，而非只有稀疏率

helper把 `q_num_blks+full_q_num_blks` 展平，detach后转CPU INT64并tolist。因此首次构造或缓存失效有元数据传输/Host调度成本，不是纯设备端分派。

令 total_base=batch_size*Hkv*num_kv_blocks、total_weight=Hkv*sum(weights)、mean=total_weight/total_base。非空、正任务数和正权重等前提成立后，代码仅在下列任一情况返回tasklist：

- 按launch_programs分轮有非零尾部，完整轮数不超过2，尾部占比小于1/2。
- 任务数恰好整除launch_programs，且max(weights)/mean大于1.5。

这些是固定实现的经验判据，不是负载最优性或性能保证。其他形态会使用primary；完全空或零权重也不由本helper强制走tasklist。

构建列表时跳过零权重KV块；超过目标负载的块拆成若干subtasks，按KV head分组、权重降序并放入当前最轻的bin。它不仅把图切成固定大小分片，也不是按真实测得kernel时间动态调度。

## 缓存依赖Tensor身份与版本计数

缓存挂在 `q_num_blks._npu_dkdv_tasklist_cache` 上。key含batch/head/block数、sparse_kv_multiple、launch_programs和device；entry另要求full_q_num_blks为同一个对象，两份元数据的 `_version` 都匹配。结果包括“不采用tasklist”的否定结果，而非只缓存已生成列表。

捕获不到版本计数时不写入这条缓存；本卡没有把inference tensor等缺版本对象当成可无条件复用。正常版本计数变化会使旧entry失配，但不能由此推导任意外部存储写入都受追踪；通过绕开版本机制改变内容时，需重新核对缓存生命周期。

entry会保留full-count对象和生成的设备任务Tensor引用，寿命随所持有的count对象/缓存而延长。这是运行期元数据缓存，不是编译产物持久缓存或模型权重缓存。

## 有拆分时，部分梯度缓冲可能很大

任务列表命中后再看split_bases是否非空：有拆分时，为dK和dV分别分配 `[max_sub,*完整累加输出shape]` 的FP32 partial，按显式storage stride安排并清零；并非只给少数重块按局部元素分配。

之后执行tasklist kernel，再由reduce kernel合并拆分输出。没有拆分则将partial引用指向原dK/dV，走tasklist_no_split并跳过reduce；未采用tasklist则直接primary。评估显存时需计入两份partial的完整shape、stride间距、max_sub和清零成本，不能仅按有效任务条目数量估算。

复合dispatch验证三种variant的参数、输出和mutation契约；reduce不能重置已经累加的输出。不能为减少清零或一次launch而删掉这些语义。生成wrapper最后del相关临时对象不等于驱动立即释放全部显存，仍受allocator与设备执行顺序约束。

lowering另保留legacy runtime-renderer对象和wrapper方法；本卡没有据这些定义的存在证明默认配置一定执行同一动态分支，也不以文档默认1代替产物核对。对比时区分资格回退、启发式否决、缓存命中、有拆分和无拆分，再验证梯度和稳态耗时。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention_tasklist.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/flex_attention_dispatch.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/select_algorithm.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/wrapper.py)（implementation）
