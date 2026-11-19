---
type: API
title: npu_batch_gather_matmul：LoRA参数与实际返回边界
description: 说明LoRA矩阵乘的校验、ACLNN输出缓冲与self返回差异，以及测试未证明的非原地语义。
tags:
- task.lookup
- topic.compute.composite
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BatchGatherMatmulKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BatchGatherMatmulKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_batch_gather_matmul.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_batch_gather_matmul.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-11T07:42:59Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# npu_batch_gather_matmul：LoRA参数与实际返回边界

依据OpPlugin主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 和固定发布快照 `dedc316708372c9a8bfde4527abd2a94b74840f5` 的两版完整Host包装与小型测试。两CPP本地逻辑相同、仅格式及namespace尾注差异；两测试逐字节同一。没有执行设备、LoRA或精度实验，测试设备装饰器不作为已验证平台。

## 接口与校验

```text
torch_npu.npu_batch_gather_matmul(self, x, weight_b, indices,
    weight_a=None, layer_idx=0, scale=1e-3, y_offset=0,
    y_slice_size=-1) -> Tensor
torch_npu.npu_batch_gather_matmul_(self, x, weight_b, indices,
    weight_a=None, layer_idx=0, scale=1e-3, y_offset=0,
    y_slice_size=-1) -> Tensor
```

两版Schema均登记op_api all_version；只有下划线版本明确为self声明可写别名并返回同别名。Host两入口都检查self/y与x为2维、weight_b为4维、indices为1维且长度等于self第0轴。weight_a虽然传入检查函数却未在其中使用；这里没有完整检查dtype、device、weight_a形状、indices内容、layer_idx范围、offset/切片越界或矩阵收缩轴。

y_slice_size=-1时改为self.size(1)，不在本地扣除y_offset。命令按self、x、weight_b、indices、weight_a、layer_idx、scale、y_offset、y_slice_size及输出下传 `aclnnAddLora`，不能凭名字交换A/B权重。

## 无下划线入口不能按常规函数式语义推定

无下划线版本先以self分配独立result，把result作为ACLNN输出，但C++最后明确 `return self`，没有返回该result。下划线版本直接把self作为ACLNN输出并返回self引用。这是固定源码中可直接观察的输出缓冲/返回对象区别，不能把无下划线版自动视为“返回新计算结果且self不变”。

底层命令是否另外修改输入、返回值实际数据及不同运行环境行为，本卡没有执行或读取aclnn实现确认；这里不将静态差异写成已复现故障，也不自行修正上游合同。接入模型时需要核对self调用前后数据、返回对象及结果缓冲实际语义。

## 仓内参考与测试隔离边界

完整参考在权重首轴追加一组FP16零权重，按indices与layer_idx取两组权重并转置，执行两次bmm、乘scale后加y。参考形参有y_offset/y_slice_size，但其计算未消费这两个参数，不能据此覆盖局部切片写入；零权重额外槽也未由下面的随机索引范围覆盖。

两方法都仅用Ascend310P筛选装饰器、FP16、layer0、scale2、offset0和slice128。无下划线方法的y为(1,128)、x为(1,16)，indices来自randint(0,1)因而只有0；调用设备入口后忽略其返回值，直接将y与先算的参考比较。它测试的是调用后y的数据，不能证明设备返回的新result或标准非原地合同。

下划线方法y/x均(10,128)，indices来自0..1并比较y_out；两例weight_a均非None，weight_b为(2,1,128,16)，未覆盖默认scale0.001、默认None权重、多layer、非法/零权重哨兵索引、真实局部切片、不同dtype、其他产品或图模式。未运行测试。

## 与GE转换的边界

既有 [GE矩阵乘转换指南](../../guides/optimization/torchair/torchair_ge_matmul_lowering.md) 已记录此default重载转AddLora时的weightA/weightB映射及默认属性；这里按当前SHA复用该合同，不重审或重绑已完成转换器。GE转换存在不能消解Eager包装中result与self返回的差异，也不能认证原地关系、设备支持或实际收益。

## Evidence

- [BatchGatherMatmulKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/BatchGatherMatmulKernelNpuOpApi.cpp)（primary）：1–79；完整本地文件。
- [BatchGatherMatmulKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/BatchGatherMatmulKernelNpuOpApi.cpp)（implementation）：1–79；完整本地文件。
- [test_npu_batch_gather_matmul.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_batch_gather_matmul.py)（example）：1–57；完整本地文件。
- [test_npu_batch_gather_matmul.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_batch_gather_matmul.py)（example）：1–57；完整本地文件。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：5965–5970；仅所列Schema或关键完整函数。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：5716–5721；仅所列Schema或关键完整函数。
