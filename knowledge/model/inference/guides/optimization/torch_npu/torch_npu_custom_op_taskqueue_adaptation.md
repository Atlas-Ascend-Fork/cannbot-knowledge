---
type: Guide
title: 自定义算子接入 TaskQueue：宏、回调与异步资源寿命
description: 区分 aclnn 标准宏与 RunOpApiV2 底层接入，说明流转换、值捕获和原始指针的前提。
tags:
- task.implementation
- topic.compilation
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/taskqueue/taskqueue_op_developer/standard_access.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/taskqueue/taskqueue_op_developer/lower_layer_access.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/taskqueue/taskqueue_op_developer/taskqueue_op_developer_overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/TASK_QUEUE_ENABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/taskqueue/taskqueue_op_developer/taskqueue_op_developer_overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/taskqueue/taskqueue_op_developer/standard_access.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/taskqueue/taskqueue_op_developer/lower_layer_access.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/taskqueue_op_developer_overview_fig_01.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/taskqueue_op_developer_overview_fig_01.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/release_notes.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/release_notes.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/pybind/README.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/pybind/README_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/torch_library/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/torch_library/README_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/pybind/csrc/add_custom.asc
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/pybind/csrc/trig_inplace_custom.asc
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/torch_library/csrc/add_custom.asc
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/torch_library/csrc/trig_inplace_custom.asc
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/pybind/csrc/pybind11.asc
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/pybind/test/add_aclgraph_test.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/pybind/test/trig_aclgraph_test.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/pybind/setup.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/torch_library/setup.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/torch_library/op_extension/_load.py
  role: implementation
created_at: '2026-11-09T02:56:52Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# 自定义算子接入 TaskQueue：宏、回调与异步资源寿命

## 版本与范围

固定 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`，A2/A3；这些文档不是所有历史版本都有相同头文件和宏的证明。仅审阅异步接入契约，没有生产或执行完整 Device Kernel。

## 选择接入层

最终调用 aclnn 时优先 EXEC_NPU_CMD_EXT，宏托管 stream 获取、参数转换、值捕获和 RunOpApiV2 入队，开发者不要再另取 aclrtStream 干扰其顺序。仅获取 NPUStream 对象用于查属性不触发清空。

Ascend C launch 或非 aclnn CANN 接口走 OpCommand::RunOpApiV2(op_name,func,sync=False)，func 为 std::function<int()>、0 表示成功；op_name 用于观测，超过 99 字节会截断。sync=True 会增加当前流同步，不作为默认异步性能配置。

## 顺序与生命周期

底层路线用 current NPUStream 的 stream(false) 获取句柄，并将真实 launch 放入入队的 lambda。仅使用 stream(false) 却绕过队列直接 launch 会越过尚未下发任务；若选择直接执行路线，则先清空且之后不能又穿插入队。

lambda 晚于调用线程执行，不捕获栈变量引用。小值按值捕获，自定义元数据可用 shared_ptr 托管；aclTensor 包装结构须在回调内完成使用与销毁，销毁包装不等于释放其引用的设备内存。

标准宏按值捕获 Tensor；底层指南为减少引用延长，建议按值捕获 data_ptr，但安全性依赖 TorchNPU 内存池和同流保序前提。不能推广到外部分配器、跨流访问或任意提早释放，shared_ptr 仅托管元数据也不会取得裸设备指针的所有权。

## 核验

在相同流和实际分配器下核对多次调用、异步返回、回调报错和资源释放，比较 Host 下发是否出现额外清空。TaskQueue Level2 与 aclgraph 的互斥及 workspace 池约束仍单独适用，不因完成宏接入就推定任意模式组合可用。

- [TaskQueue 下发级别](torch_npu_taskqueue_delivery.md)
- [图适配与命名空间](../../integration/torchair/custom_operator_graph_contract.md)

## 完整接入说明和路径图的边界

两语言路径图分别查看，按最终调用的接口选择：aclnn走标准宏，非aclnn或Ascend C launch走底层回调；不是仅凭算子名称或编译来源选择。RunOpApiV2的sync参数是下发后同步当前流；不是回调按引用捕获栈变量也安全的保证。

标准宏托管Tensor按值捕获，底层示例为减轻延长引用而捕获data_ptr，两者不可机械互换。shared_ptr托管自定义Host元数据不取得裸设备指针所有权；关闭缓存、外部分配器或跨流情形仍需独立生命周期与依赖证据。aclTensor可在回调内创建，也可外部创建后捕获包装指针，但实际使用及销毁都必须覆盖延迟执行阶段。

示例aclnnAdd实参、Ascend C launch及uint32长度只是接入示意，不构成完整可编译算子签名或任意Tensor的shape/dtype/长度校验器。这里只摄取框架下发接口和资源契约，没有扩为Kernel/Host/Tiling生产工程，也没有执行或编译示例。

## 26.1发布修复项同时涉及流和资源配套

同提交26.1发布说明将GDN自定义适配问题描述为aclnn_extension未传stream、顺序/同步异常，根因及方案又指出EXEC_NPU_CMD_V1_EXT/V2_EXT内存/workspace申请释放须与标准宏一致。这是来源的已解决报告，未经本卡复现，也不能简化成只改stream或只清workspace。

实际接入仍核对队列保序、捕获、分配器及异步资源寿命；不将来源“修复后整网精度正常”登记为本仓verified。本卡既有A2/A3范围保持逐接入文档口径，不因发布说明提到950DT扩大所有宏组合。

## TorchAir双接入示例的队列顺序、注册与边界

TorchAir固定主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的Pybind和torch.library双语示例明确A2/A3，前提torch至少2.6、npugraph_ex另需TorchNPU产品至少7.3，示例CANN toolkit/ops至少8.5；不把这些最低条件当已固定三组件的配套矩阵。示例固定ND的8×2048，Add用int、Trig用float32，不证明广播、任意stride、storage offset或其他dtype可用。

| 源码方式 | 顺序含义 |
| --- | --- |
| 1：直接将NPUStream对象传launch | 隐式转原始句柄时清Host队列；获取对象本身不清队列 |
| 2/8：stream(true)或stream()后直调 | 先清已入队的Host下发；不是Device计算全部完成 |
| 3：stream(false)+RunOpApiV2内launch | 无额外清队列，真实launch按队列顺序执行 |
| 4：stream(false)直接launch | 不清也不入队，可能越过先前尚未下发操作 |
| 5：队列lambda内使用会隐式清队列的NPUStream对象 | 队内任务等待队列清空，形成循环等待风险 |
| 6：stream(true)再入队 | 当前示例可保序，但有额外清队列成本，不是默认最优 |
| 7：清队列后zeros_like入队、随后直调自定义Kernel | 新的初始化仍可能在Kernel之后下发，不能用先前一次flush覆盖后续入队 |

README将TaskQueue称Device队列，实际这些接口控制Host异步下发；图中自定义add排在mul_1之前只是来源历史trace，本文没有复现。源码当前公开绑定/注册的是无后缀方式1，其余2..8是不同函数的教学对照，并没有自动遍历全部方式。不要把“存在八个函数”当八种路线都已通过设备测试。

Pybind先将run_add_custom/run_trig_custom暴露Python，再用torch.library DEF注册schema、PrivateUse1实现和Meta。torch_library路线在C++用TORCH_LIBRARY_FRAGMENT/IMPL注册并load_library；README中Add的m.def引号写坏，实际C++schema字符串正确。Trig将out_sin标Tensor(a!)、out_cos标Tensor(b!)并返回新tan，不能漏掉这两个输入的变更合同；Meta empty_like(x)只适合此固定例的输出约定，不扩为广播/类型提升实现。

Pybind Host示例以storage().data取得底层基址，而torch_library对应代码使用mutable_data_ptr；前者没有显式纳入非零storage offset，不将二者在任意view上视为等价。长度以uint32累乘、固定blockDim和未展示完整shape/dtype校验都属于示例限制，不作为生产算子完整验证器。这里只读取框架注册和Host下发区域，Device算子体不在本卡范围。

两setup默认bisheng、--npu-arch=dav-2201、C++20，并从当前torch取_GLIBCXX_USE_CXX11_ABI及依赖目录；这是例子构建目标，不由A2/A3标题保证任意目标架构参数通用。torch_library加载器按glob取首个custom_ops_lib*.so，缺失报错，不能据文件名判断旧库/多库/ABI匹配。

测试分别展示手工NPUGraph、make_graphed_callables、npugraph_ex和单算子；手工重放先copy_进静态地址，Trig还检查sin/cos的副作用。npugraph_ex样例fullgraph=True/dynamic=True仅固定输入，不证明任意动态shape都可复用一张图；所谓cpuout实际调用torch.add/sin/cos的输入仍为NPU Tensor，不据变量名记为独立CPU真值。所有构建、库加载和设备测试均未执行。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/taskqueue/taskqueue_op_developer/standard_access.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/taskqueue/taskqueue_op_developer/lower_layer_access.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/operator_dispatch/taskqueue/taskqueue_op_developer/taskqueue_op_developer_overview.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/op_execution/TASK_QUEUE_ENABLE.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/taskqueue/taskqueue_op_developer/taskqueue_op_developer_overview.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/taskqueue/taskqueue_op_developer/standard_access.md)（constraint）

- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/operator_dispatch/taskqueue/taskqueue_op_developer/lower_layer_access.md)（constraint）

- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/taskqueue_op_developer_overview_fig_01.png)（constraint）

- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/taskqueue_op_developer_overview_fig_01.png)（constraint）

- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/release_notes.md)（primary）

- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/release_notes.md)（constraint）

- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/pybind/README.md)（primary）

- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/pybind/README_en.md)（constraint）

- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/torch_library/README.md)（constraint）

- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/torch_library/README_en.md)（constraint）

- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/pybind/csrc/add_custom.asc)（implementation）

- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/pybind/csrc/trig_inplace_custom.asc)（implementation）

- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/torch_library/csrc/add_custom.asc)（implementation）

- [固定来源 19](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/torch_library/csrc/trig_inplace_custom.asc)（implementation）

- [固定来源 20](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/pybind/csrc/pybind11.asc)（implementation）

- [固定来源 21](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/pybind/test/add_aclgraph_test.py)（implementation）

- [固定来源 22](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/pybind/test/trig_aclgraph_test.py)（implementation）

- [固定来源 23](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/pybind/setup.py)（implementation）

- [固定来源 24](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/torch_library/setup.py)（implementation）

- [固定来源 25](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/examples/_kernel_extension_aclgraph/torch_library/op_extension/_load.py)（implementation）
