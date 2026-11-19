---
type: API
title: torchair.ops.npu_print：GE 图内异步打印与展示量
description: 说明 Tensor 参数、摘要和详细输出，明确异步顺序、额外开销及 dtype 限制。
tags:
- task.lookup
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ops/npu_print.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/tensor_print.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ops/npu_print.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/tensor_print.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ops/_print_ops.py
  role: implementation
created_at: '2026-11-09T02:51:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# torchair.ops.npu_print：GE 图内异步打印与展示量

## 版本与范围

依据 TorchAir 固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`。该提交属于 ascend_26_0_pt28 的固定来源组合；不是所有历史或主线版本的通用契约。发布部分选取A2/A3；主线A2/A3与950的限定范围见后文，不回推发布版。

## 接口

`torchair.ops.npu_print(*args,summarize_size=3,tensor_detail=False)` 不返回结果，参数中至少包含一个 Tensor，其他可为 str/bool/float/int 等。仅 GE 图模式，用于观察图内运行数据而避免普通 Python print 引起 graph break。

summarize_size 默认 3，对每维展示开头/末尾元素；-1 打印全部。tensor_detail=True 另打印 shape/dtype。Complex 不支持打印 value；uint16/uint32/uint64 的支持要求 PyTorch≥2.3，其他类型按来源列表核对。

## 顺序和诊断成本

打印是异步的，只保证图内打印的执行顺序，不保证与图外 Python print 的屏显先后。它消耗额外 Device 内存和时间，来源建议数据展示量控制在 KB 级以下；全量大 Tensor 可能导致 OOM 或超时。

先缩小到目标节点和最少元素，检查输出与正常执行；关闭打印后再测性能。不要把异步屏显次序用作跨 Host/Device 的精确时序证据。


## 验证边界

分别核对实际软件版本、配置生效日志/图结构、输出与存储语义，再比较同输入的稳态耗时。本文为固定文档和静态接口审阅，没有执行上游代码、NPU 数值或性能实验。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 主线校验与GE打印路径

固定主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的本节文档/实现已核对，主线总览覆盖A2/A3与950PR/950DT；发布 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013` 的A2/A3条件仍独立保留，不回推发布版950或两仓主线配套。

主线API与特性页保留同一GE约束。summarize_size只支持正整数或-1，0和<-1会报错；某一维长度≤2*summarize_size时该维完整展示，其余维仍可摘要。tensor_detail必须bool，至少一个Tensor，其他位置参数仅str/bool/float/int；不能传任意字典/列表供其递归打印。

文档的Tensor列表为有符号int8/16/32/64、uint8/16/32/64、float16/32/64、BF16与bool，uint16/32/64需PyTorch≥2.3；Complex value不支持，不由模型本身支持Complex就推导打印支持。主线GE Converter将BF16值转FP32供显示，tensor_detail的dtype文字来自原输入；打印格式不等于内部存储类型已改变。

GE路径使用StringFormat/PrintV2；Eager注册的CPU/PrivateUse1实现则detach并转CPU生成文本，不能把它当作相同的Device异步打印路径。接口登记了FX副作用，Meta无输出不表示可以删除。观察完成后关闭打印再测性能，不用屏显或摘要文本证明逐位数值一致。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ops/npu_print.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/tensor_print.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ops/npu_print.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/tensor_print.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ops/_print_ops.py)（implementation）
