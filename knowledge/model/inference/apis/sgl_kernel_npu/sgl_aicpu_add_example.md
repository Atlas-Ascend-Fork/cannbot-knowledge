---
type: API
title: SGLang AICPU AddExample的输入与独立存储合同
description: 说明add_example的FP32/INT32、同shape连续ND、无广播、输出独立存储和aicpu无回退分发，保留整数溢出未验证边界。
tags:
- task.implementation
- topic.implementation.api_layer.aicpu_api
- topic.memory
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/examples/add_example.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/examples/add_example.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/operators/examples/test_add_example.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/utils/accuracy.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/examples/add_example/torch_adapter.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/examples/add_example/op_host/aclnn_sgl_add_example.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/examples/add_example/op_host/aclnn_sgl_add_example.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/examples/add_example/op_kernel_aicpu/add_example_aicpu.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/examples/add_example/op_kernel_aicpu/add_example_aicpu.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/examples/add_example/op_kernel_aicpu/add_example.json
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/examples/add_example/CMakeLists.txt
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/aclnn_torch_adapter/aclnn_runtime.h
  role: implementation
created_at: '2026-11-08T11:06:19Z'
updated_at: '2026-11-09T12:44:59Z'
platforms:
- a2
- a3
- '950'
---

# SGLang AICPU AddExample的输入与独立存储合同

## 接口、平台和选择

```python
from sgl_kernel_npu.operators.examples import add_example
add_example(x1, x2, *, impl="auto")
```

固定文档声明aicpu与torch_native支持arch22（A2/A3）和arch35（旧称A5，即950）。auto与aicpu是同一入口，不构成两个独立实现。调用原生路径前，需安装与架构匹配且由--ops选择add_example的wheel；缺绑定报错，不自动回退。AICPU构建说明要求CANN 9.2.0及对应HCC/AICPU开发环境。

## 张量与副作用

输入必须为同NPU、相同shape及dtype的非空Tensor，仅FP32或INT32；连续且存储格式为ND。公开包装检查这些条件，不广播、不静默转换格式或类型。结果逐元素相加，返回同shape/dtype/device的连续ND新Tensor，输入不变，结果与任一输入不共享存储。

原生入口是`torch.ops.npu.sgl_add_example`，reference是独立`torch.add`，同样经过公开输入合同。该示例展示AICPU接入，不是性能基准；整数溢出尚未验证，不从INT32类型推导溢出规则。

## 验证入口与边界

上游`tests/python/operators/examples/test_add_example.py`仅定义 shape=(2,) 的 FP32/INT32 两种实现数值比较；共用 accuracy 工具检查输出 shape/dtype/device 与数值，没有存储身份断言或 shape 不等、空输入、非连续、非 ND 拒绝用例。上述输入拒绝条件来自公开包装源码的静态检查；存储独立性与异常分支需另补验证，不能当作已有测试覆盖。本卡蒸馏公开API及实际适配/CPU入口，不进行完整样例工程的编译验收。本次未执行编译、真机、数值或性能测试。

## 真实ACLNN入口与异步所有权

该示例自供的两段式接口是`aclnnSglAddExampleGetWorkspaceSize`与`aclnnSglAddExample`，不是普通`aclnnAdd`或其他教程的`aclnnAddExample`。第一阶段接收x1/x2及调用方已分配的y；空指针返回`ACLNN_ERR_PARAM_NULLPTR`，dtype/shape/连续ND/空输入不符返回`ACLNN_ERR_PARAM_INVALID`，创建executor失败有独立错误码。校验后把AICPU任务加入launcher，返回实际executor workspace大小。原生ACLNN层不替调用方分配y，亦未检查y与输入的存储重叠；独立输出保证来自Torch adapter的新分配，不能向下推广为原生pair自动拒绝alias。

Torch adapter重复输入检查，用输入device的`DeviceGuard`分配连续ND输出；动态符号只从本扩展相对路径下的vendor `libcust_opapi.so`加载，`RTLD_LOCAL`且保持handle存活，避免依赖进程全局同名库。descriptor用Tensor实际data_ptr作为基址、offset0并携带sizes/strides，因此连续子视图的storage_offset已体现在data_ptr，不应再叠加一次偏移。

query失败在提交执行前抛错；workspace先检查能放入int64元素数，再按字节Tensor分配。adapter获取guard设备的current stream，对x1/x2/y/workspace分别`record_stream`；OpCommand闭包按值捕获这些Tensor、三个shared descriptor及executor指针。捕获保护Host排队期间的对象，record_stream保护异步设备消费；不能把局部workspace变量离开作用域直接解释为已悬空。execute用workspaceSize决定是否传nullptr，返回错误会抛出；实际排队、完成及executor销毁细节由匹配OpCommand/ACLNN运行时负责，本源码没有额外同步。

## AICPU接线与弱下层检查

CMake将本项注册为`EXECUTION_UNIT AICPU`、OpType `SglAddExample`，支持2201/3510，并显式绑定Torch adapter、手写ACLNN文件、CPU源及JSON。JSON指定`DNN_VM_AICPU`、`RunCpuKernel`及`libsgl_kernel_npu_aicpu.so`；其中workspaceSize字符串100不能替代query返回的实际executor workspace，也不能据flagAsync=False断言Python调用已同步完成。

CPU Compute按input0 dtype分派float/int32，检查输入输出对象及数据指针后，以input0的NumElements做线性`y[i]=x0[i]+x1[i]`；没有广播、分块并行或Cube/Vector计算路径。它不重复完整shape/dtype匹配，依赖上层合同；CPU体对空输入可早返成功，但公开Python与ACLNN query已拒绝空输入，这不是公开支持扩展。int32加法没有饱和、溢出检测或显式无符号取模处理，不能承诺wraparound规则。AICPU框架装载/线程与内存协议仍属于外部依赖；本卡不以CPU源码存在或构建登记冒充运行通过。
