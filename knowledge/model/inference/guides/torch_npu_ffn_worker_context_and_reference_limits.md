---
type: Guide
title: FFN Worker上下文：测试打包、缓冲持有与参考验收边界
description: 补齐FFN Worker测试的packed上下文、偏移与设备地址、随机参考及仅断言y的范围，复用既有八返回和调度隔离合同。
tags:
- task.implementation
- topic.mixture_of_experts
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FfnWorkerBatchingKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FfnWorkerSchedulerKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_ffn_worker_batching.py
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_ffn_worker_schedule.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FfnWorkerBatchingKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FfnWorkerSchedulerKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_ffn_worker_batching.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_ffn_worker_schedule.py
  role: example
created_at: '2026-11-11T06:47:34Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FFN Worker上下文：测试打包、缓冲持有与参考验收边界

## 固定来源与适用范围

本卡完整阅读OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`的FFN Batching/Scheduler包装及两份测试，对照发布`dedc316708372c9a8bfde4527abd2a94b74840f5`。两对C++完整非注释token相同，仅主线多namespace尾注；两份测试完整AST相同，全部原文差异仅行尾空白。发布配套为ascend_26_0_pt28，主线配套未知；整卡保持draft、空平台，没有导入测试、启动进程池、生成文件、分配设备窗口或执行调度。

包装的输入检查、八返回容量/类型、Y/H的C++ int窄化、非下划线调度器先copy副本，以及GE的TensorMove隔离，复用[工作调度与八返回合同](optimization/torchair/torchair_ge_worker_scheduler_lowering.md)。本卡补的是**固定测试自己的上下文布局和验收缺口**，不是厂商公开二进制ABI；不能把测试结构体或十六进制占位地址当作任意版本可直接使用的上下文。

## Packed结构与token大小是两种对齐

Batching测试所有ctypes结构体用_pack_=1。按源码字段宽度计算，CommonArea=128字节、ControlArea=128、AttentionArea=128、FfnArea=256，另有384字节reserve，ScheduleContext合计1024字节。这里的字节数来自字段布局，不代表整体指针自动按512字节对齐。

| 测试结构 | 所保存信息 |
| --- | --- |
| CommonArea | session/micro-batch数量、batch大小、selected_expert_num、expert_num、两方向token字节大小及schedule_mode |
| ControlArea | run_flag与三个uint64等待缓冲字段，含保留区 |
| AttentionArea | token_info/data缓冲及大小、micro_batch_id |
| FfnArea | token_info/data、polling_index，layer/session/micro-batch/expert ID缓冲及大小、out_num |
| DataDesc | INT32 flag、layer_id及BS*K_plus_1个INT32专家ID |

选定全局参数为A=4、M=1、BS=54、K_plus_1=9、H=7168、expert_num=2、out_num=A、tokenDtype=2、need_schedule=1、cur_micro_batch_id=0、无效概率0。输入token为INT8[H]，后跟FP32 quant_scale及padding，HS按ceil((H+4)/512)*512得到7680字节。浮点分支使用uint16容器存FP16位，HS=2H；它没有在此为BF16写另一套数值生成逻辑。DataDesc在该参数下为(2+54*9)*4=1952字节；512规则针对token记录容量，不是所有描述符或Tensor首地址的通用对齐保证。

## 文件偏移和设备地址不能混用

generate_input_func先写common/control/attention与FFN字段，将FFN各数据块按顺序拼到schedule_context.bin；初始buf字段是**相对文件起点的字节偏移**，size是字节数。read_schedule_context按这些偏移切片，offset或size为0则返回None，按size//element_size构造数组；没有在本地完成任意损坏文件的完整范围/长度验证。

测试随后把token_info、token_data和ID数组分别转Tensor再搬NPU，保存在tensor_buffers字典中；正式调用前把对应FFN字段改成这些设备Tensor的data_ptr和字节长度，再将1024字节ctx复制成INT8 Tensor上NPU。文件偏移、Host ctypes地址和设备data_ptr是不同阶段的值。字典保留独立缓冲引用，不能只留下整数地址就推定Tensor仍存活或所有异步消费已完成。

control/attention填入的0x1000等字段是本测试的占位值，后面的改写只针对列出的FFN缓冲；部分layer缓冲也没有建立独立数据块。这里只观察该示例构造，不从这些数字推导完整调度等待协议或真实地址有效性。ffn_data_parts是全局列表，生成前没有清空；tensor_buffers.clear只清另一份字典，不能将重复调用视为完全重新构造、无旧段累积的无状态函数。

## 生成器和读取helper不证明输入全域

两组token生成均使用multiprocessing.Pool(cpu_count())，chunksize至少1000；这是测试Host准备工作，没有证明融合算子速度。INT8值随机取[-10,10)，scale取[0.1,2.0)，padding清零；FP16分支取[-1,1)。token_info的flag由micro-batch位置产生，expert ID实际随机域硬编码0/1；layer_id没有在生成函数单独赋值。无效值helper默认用214748364，最多替换1512项，但当前概率为0；另一个无替换helper的extreme_val形参并未消费。

convert_ctypes_to_torch先要求ctypes.Array，仅映射c_int32/c_float/c_uint8/c_int64，其他类型报错。它根据ctype选择dtype，**忽略expected_dtype形参**；from_address/frombuffer后调用clone，最终返回独立Tensor副本，不能只看“零拷贝”注释评价其成本或生命周期。INT8/FP16参考也通过NumPy.copy建立可写数组；量化scale按FP32读取，而非把随token储存的4字节解释成INT8数值。

## Batching参考排序不等于全部八输出已验收

calc_expect_func从文件读取token_data并恢复[A,M,BS,K_plus_1,H]。need_schedule=1时按AM_idx%M选定当前micro-batch的expert IDs；无调度分支则取直接expert_ids_buf。展平expert IDs稳定排序，按session_ids、当前micro_batch、batch与topK槽收集数据；token_ids参考为batch索引、expert_offsets为topK槽，动态尺度按相同token索引收集。

参考将ID>=1e6计入masked_count并算actual_token_num，但没有因此截断所收集的y；group_list又用unique_experts<=1e6过滤，阈值等号的处理也不同。它把unique专家ID和count直接写到[expert_num,2]整列，没有普遍处理任意缺失专家/空结果。micro_batch_ids参考直接取单个当前元素，没有独立构造包装所分配的[Y]返回缓冲；开头按FP16创建的零y随后又被gather结果覆盖，不能据这一临时分配改写真实输出dtype。上述均是测试helper的静态边界，不能反推后端算法同样如此。

唯一Ascend910B方法生成文件与缓冲，调用npu_ffn_worker_batching(...,token_dtype=2,need_schedule=1,layer_num=0)，显式synchronize后**只assertRtolEqual(y_cpu,y_npu)**。group_list、session_ids、micro_batch_ids、token_ids、expert_offsets、dynamic_scale和actual_token_num虽然被接收，却没有在本方法逐项断言；实际Y=4*54*9=1944的容量也不能替代有效token数。它没有验证FP16/BF16、need_schedule=0、空专家、无效ID、层切换或重复生成路径，本次没有运行该方法。

## Scheduler测试的窗口与skip范围

另一份55行测试在模块顶层就写有200MiB INT8 NPU窗口分配和_afd.create_schedule_context_holder调用，取holder的上下文Tensor；这是源码中实际存在的导入副作用，本次没有导入它。参数为2个Attention worker、3个micro-batch、batch6、topK8、hidden7168、expert288、schedule_mode=0。它按每session每micro-batch的(8+batch*topK*4)字节前缀建立INT32视图并全部置1，没有在本文件验证这些字段对应的完整跨worker可见性/完成协议。

两个Ascend910B方法均unittest.skip，理由为等待CANN支持。带下划线方法意图检查输入上下文改变；非下划线方法意图检查原输入不变而返回副本不同，sync_group_size均2。它们不证明实际调度完成、数据窗口保持正确、无死锁、execute_mode全域或跨卡收益，skip也不是发布软件整体缺能力的证据。接入模型时应单独核对真实上下文生产者、缓冲所有权、有效长度和全部八项输出，再测Attention/FFN完整链路；本卡没有设备、数值或性能验证及新增verified。

## Evidence

- [FfnWorkerBatchingKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FfnWorkerBatchingKernelNpuOpApi.cpp)（implementation）：完整本地文件1–99。
- [FfnWorkerSchedulerKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/FfnWorkerSchedulerKernelNpuOpApi.cpp)（implementation）：完整本地文件1–19。
- [test_npu_ffn_worker_batching.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_ffn_worker_batching.py)（primary）：完整本地文件1–636。
- [test_ffn_worker_schedule.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_ffn_worker_schedule.py)（example）：完整本地文件1–55。
- [FfnWorkerBatchingKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FfnWorkerBatchingKernelNpuOpApi.cpp)（implementation）：完整本地文件1–77。
- [FfnWorkerSchedulerKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/FfnWorkerSchedulerKernelNpuOpApi.cpp)（implementation）：完整本地文件1–20。
- [test_npu_ffn_worker_batching.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_ffn_worker_batching.py)（example）：完整本地文件1–636。
- [test_ffn_worker_schedule.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_ffn_worker_schedule.py)（example）：完整本地文件1–55。
