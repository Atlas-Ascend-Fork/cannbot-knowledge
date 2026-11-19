---
type: Guide
title: Foreach执行：分批、Scalar准备与Host设备复制
description: 聚合Copy/Add/Mul/Sqrt的fast与慢路线、V1标量物化和V2分块，并明确批量Host设备复制的dtype、连续性和同步边界。
tags:
- task.optimization
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ForeachCopyKernelOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ForeachAddKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ForeachMulScalarKernelOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ForeachSqrtKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/ScalarOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/ForeachConstants.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ForeachCopyKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ForeachAddKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ForeachMulScalarKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ForeachSqrtKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/ScalarOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/ForeachConstants.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
created_at: '2026-11-11T11:07:50Z'
updated_at: '2026-11-11T11:07:50Z'
platforms: []
---

# Foreach执行：分批、Scalar准备与Host/设备复制

Foreach接口不保证一次设备调用：本地会按入口和原地/函数式拆分Tensor列表；符号、SoC和类型条件还决定批量执行、V1 Scalar设备物化、batch memcpy或ATen慢路径。下面聚合_foreach_copy_、add List/ScalarList、mul Scalar和sqrt；不扩到其余Foreach重载或已单列的[AMP unscale](torch_npu_native_amp_unscale_execution.md)。

## 算术路线与批大小

| 入口/gate | 行为 | 可见准备成本 |
|---|---|---|
| Add List、Mul Scalar的SoC门失败 | 直接调用对应ATen slow | 不进入本地V2申请和分块 |
| V2符号兼容检查失败 | 转本文件V1 | V1另检查CheckJitDisable与fast route，必要时再slow |
| V1 fast通过 | 把alpha/scalar变设备Tensor，调用旧ACLNN | functional还逐个申请输出；原地把输入列表作输出 |
| V2 fast通过 | 直接传Scalar并拆块 | 避开V1那次copy_scalar_to_device调用，仍有输出申请/分批 |
| Sqrt fast不成立，或has_integral_tensor(...,true) | ATen slow | 不是把整数输入静默cast后沿同一快速路径执行 |

SoC门用函数局部static缓存`(GetSocVersion()>=Ascend910B1 && GetSocVersion()<Ascend310B1) || GetSocVersion()>Ascend310B4`。Add/Mul V2路线不再调用V1的CheckJitDisable；V1 fast要求它和can_use_fast_route都通过。Mul V1另明确仅接受Half/Float/Int，其他类型在该分支TORCH_CHECK；Add V1没有照抄同一dtype断言。

Add ScalarList与Sqrt先做自己的DO_COMPATIBILITY，再做SoC/限制/fast检查；ScalarList fast调用can_use_fast_route(...,true)。源码中“default slow path for now”注释不能盖过下面实际存在的fast与执行分支。这里的ATen slow可能是逐Tensor设备操作，不等于本地已经显式转CPU。

| 所选执行 | functional每块上限 | inplace每块上限 |
|---|---:|---:|
| Add List V2 | 16 | 24 |
| Add ScalarList | 24 | 48 |
| Mul Scalar V2 | 24 | 48 |
| Sqrt | 24 | 48 |
| Copy ACLNN | — | 48（只有inplace入口） |

列表超过上限时先执行完整块，再执行非零余数块；不能由Foreach一个Python入口推导一次SDK调用。functional快路由按第一个Tensor的dtype，为列表中每个Tensor分别申请输出，并非申请一个共同平坦buffer；原地路线直接传输入列表作为结果，不执行同样的输出申请。

## V1设备Scalar与V2标量适配

Add List V1把alpha、Mul Scalar V1把scalar通过copy_scalar_to_device转换为设备Tensor，dtype和设备取列表第一个Tensor；该helper的具体pinned复制机制见[动态选择与标量执行](torch_npu_dynamic_selection_sync_and_where_scalar_execution.md)，这里不重复其来源资格。Add V1使用aclnnForeachAddList，Mul V1使用aclnnForeachMulScalar。

相应V2 helper调用adaptToDouble，再传Scalar给aclnnForeachAddListV2/aclnnForeachMulScalarV2：第一个Tensor为浮点、Scalar符合isIntegralType条件时，以scalar.toDouble()重新组成Scalar，其余保留原Scalar。主线isIntegralType(scalar.type(),false)，发布未显式传第二个实参；不把函数名解释成所有Scalar或所有Tensor均转Double，默认Bool判定按所配ATen头另核。ScalarList Add直接传每段Scalar列表，没有逐项调用此helper。

这些成本差异不足以证明任意混合类型、溢出或浮点精度等价；V1/V2实际选择和对应fast限制须连同调用参数固定。

## Copy先按设备与dtype决定分组

两版_foreach_copy_先做aclnnForeachCopy兼容检查和check_foreach_api_restrictions。should_group选择第一个非空列表的首Tensor作参照；该入口传入(src,self)，通常以首源为准。两列表对象设备都与参照相同且存在dtype差异才返回true；任意设备不同直接false，两表都空也false。true时按**源dtype**建立unordered_map，每组同时保留原src[i]/self[i]配对，分别交process_tensor_list_batch；这不是按目标dtype分组，也不保证各组全局执行顺序。

Copy的SoC ND门与上面相同，batch门则为`(>=Ascend910B1 && <Ascend310B1) || >Ascend910_9391`，两个静态布尔不能混用。主线快速资格是ND门、源类型helper，以及`can_use_fast_route || check_cross_dtype_supported`都通过；发布没有后一个跨dtype替代门，只用can_use_fast_route。

主线跨dtype helper要求名为9.1.0的CANN版本判断为true、两列表长度相同，逐对仅允许Float→Half/BFloat16或Half/BFloat16→Float。该判断helper缓存IsGteCANNVersion("9.1.0","CANN")结果；源类型helper中Long/Double/Bool的额外门缓存"8.1.RC1"判断。版本parser与真实安装探测不在本节展开。

源类型helper还明确列Char/Byte/BFloat16/Float/Half、Int、Short。其最前两支原文是`sizeof(src[0])==4`与`sizeof(src[0])==2`，并有QInt32/Int/Short条件：这是C++对象sizeof表达式，**不是element_size()**，不能把它改述成对全部4字节/2字节元素类型的支持矩阵。helper只看src[0]，完整列表限制还依赖前面的ATen检查及分组/fast判定。

## batch memcpy门与同步位置

快速ACLNN资格失败时，才尝试batch memcpy：需batch SoC门、与non_blocking对应的MemcpyBatchAsync/MemcpyBatch符号存在、设备helper通过。主线还额外要求两列表所有Tensor都is_contiguous()；发布没有这两个本地连续检查，不能回填主线限制，也不能反推发布任意stride都可正确raw copy。

设备helper要求列表等长且非空、各目标保持首目标device.type，各源保持首源device.type，PrivateUse1一侧索引保持一致；non_blocking为true时还比较该NPU索引与GetDevice返回的当前索引。源/目标device.type相同则拒绝，因此D2D不会由这个helper选batch路线。代码在此未逐项检查dtype或字节长度相等，不将其函数名中的dtype解释成已经验证了转换条件。

| 已选Copy路线 | 实际行为 |
|---|---|
| ACLNN | src/dst按48拆块，调用aclnnForeachCopy；主线最后传split(...,true)，发布传原non_blocking，但exec_npu_cmd_copy都没有把该实参传给SDK |
| batch且non_blocking=true | 取当前流，交LaunchBatchAsyncCopyTask并检查返回码 |
| batch且non_blocking=false | 先请求当前流同步，再调用AclrtMemcpyBatch并检查返回码 |
| batch门也失败 | 日志后调用ATen foreach_tensor_copy_list_kernel_slow_，透传原non_blocking |

因此non_blocking在batch与慢路线仍有实际作用，不能因ACLNN helper未使用它就概括成整个API忽略该参数；也不能由true就推导所有路径没有Host等待。

memcpyBatch取各Tensor data_ptr，分别以numel()*element_size()计算源/目标长度，构建逐项attrsIndexes及Host/Device位置，清零rsv字段。它没有在此先cast Tensor dtype；raw字节搬运不是任意跨dtype数值复制的证明。指针/数组到队列的持有、异步生命周期和底层属性验证另按队列实现核对，不由本函数局部Tensor变量保证全部存储长期有效。

同步失败时先执行专门错误宏/打印，再根据resume模式warning或AT_ERROR；不能将resume文案理解成前面宏必然不会抛。同步batch的failIdx初始化后作为输出指针传入，局部没有另读该索引恢复某个子项。

## 来源与模型定位

OpPlugin固定主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`。所列Add/Mul/Sqrt Schema为op_api all_version，Copy为[v2.1,newest]；主线另外在Mul Scalar inplace、Sqrt两重载列dvm，发布没有这些声明。本卡只覆盖精确重载，不从标签扩展DVM内部执行或产品支持。

定位优化器/权重列表操作时，记录列表长度、每组dtype/设备、inplace、alpha/scalar类型、JIT/SoC/CANN门及non_blocking；核对V1物化Scalar、V2分块、逐个结果申请、batch同步与慢路线，再比较数值、别名及端到端耗时。本卡仅静态审阅，未运行ATen、查库、设备、复制或性能测试，未知平台保持draft、空平台，没有verified。

## Evidence

- [ForeachCopyKernelOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ForeachCopyKernelOpApi.cpp)（primary）：1–329。
- [ForeachAddKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ForeachAddKernelNpuOpApi.cpp)（primary）：1–205。
- [ForeachMulScalarKernelOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ForeachMulScalarKernelOpApi.cpp)（primary）：1–135。
- [ForeachSqrtKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ForeachSqrtKernelNpuOpApi.cpp)（primary）：1–85。
- [OpUtils.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）：460–466、504–508。
- [ScalarOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/ScalarOpApi.cpp)（implementation）：23–31。
- [ForeachConstants.h d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/ForeachConstants.h)（implementation）：19–19。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：225–226、231–235、241–242、295–296、381–382、390–392、442–448。
- [ForeachCopyKernelOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ForeachCopyKernelOpApi.cpp)（implementation）：1–285。
- [ForeachAddKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ForeachAddKernelNpuOpApi.cpp)（implementation）：1–215。
- [ForeachMulScalarKernelOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ForeachMulScalarKernelOpApi.cpp)（implementation）：1–137。
- [ForeachSqrtKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ForeachSqrtKernelNpuOpApi.cpp)（implementation）：1–91。
- [OpUtils.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）：416–422。
- [ScalarOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/ScalarOpApi.cpp)（implementation）：23–32。
- [ForeachConstants.h dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/ForeachConstants.h)（implementation）：19–19。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：225–226、231–235、240–241、291–292、375–376、384–385、435–439。
