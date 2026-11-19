---
type: Guide
title: OpPlugin框架适配：版本注册、结构化生成与示例缺口
description: 区分版本化Schema、前反向绑定、NZ路由、Meta和实现交付，保留自定义add示例的梯度与Schema差异。
tags:
- task.implementation
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_overview_opplugin.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_overview_opplugin.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_preparation_opplugin.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_preparation_opplugin.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_flow_opplugin.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_flow_opplugin.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_development_opplugin.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_development_opplugin.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/reference.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/reference.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_compile_opplugin.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_compile_opplugin.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/sample_call_opplugin.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/sample_call_opplugin.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/opplugin_adaptation_flow.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/opplugin_adaptation_flow.png
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/Version.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/CMakeLists.txt
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/CONTRIBUTING.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/CONTRIBUTING.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/README.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/README.zh.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/README.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/README_en.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/aclnn_extension/README.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/aclnn_extension/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/aclnn_extension/README_en.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/cpp_extension/README.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension/README_en.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/cpp_extension_asc/README.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_asc/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_asc/README_en.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/cpp_extension_base/README.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_base/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_base/README_en.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/cpp_extension_full/module/README.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_full/module/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_full/module/README_en.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/cpp_extension_full/torch_lib_impl/README.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_full/torch_lib_impl/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_full/torch_lib_impl/README_en.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/cpp_extension_pybind/README.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_pybind/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_pybind/README_en.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/cpp_extension_structured/README.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_structured/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_structured/README_en.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/framwork_cpp_extension/README.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/framwork_cpp_extension/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/framwork_cpp_extension/README_en.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/kernel_extension_aclgraph/pybind/README.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/kernel_extension_aclgraph/pybind/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/kernel_extension_aclgraph/pybind/README_en.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/kernel_extension_aclgraph/torch_library/README.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/kernel_extension_aclgraph/torch_library/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/kernel_extension_aclgraph/torch_library/README_en.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/README.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/aclnn_extension/gen.sh
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_structured/gen.sh
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/aclnn_extension/setup.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/aclnn_extension/npu_custom_derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/aclnn_extension/test/test_npu_fast_gelu_custom.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_full/torch_lib_impl/csrc/add_custom.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension/setup.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension/csrc/pybind11.asc
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/aclnn_extension/gen.sh
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/cpp_extension_full/torch_lib_impl/csrc/add_custom.cpp
  role: implementation
created_at: '2026-11-09T16:01:03Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# OpPlugin框架适配：版本注册、结构化生成与示例缺口

## 固定来源和草稿范围

全文审阅TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的两语言OpPlugin适配技术页及流程图。另读独立OpPlugin主线d84e9b1d6a558e5f27973cd4329f62968e46fdda的Version.h，以及CMake和兼容宏局部，以核对版本/回退措辞；不是证明这两个主线快照构成运行配套。

整体适配流程没有完整产品矩阵，样例还存在下述未闭合合同，本卡draft、platforms为空。950DT明确不支持aclop适配这一局部排除照录，不以它推导aclnn及所有自定义组合的全产品支持。这里处理框架插件与模型调用，不摄取Kernel/Host/Tiling生产工程，未编译安装或执行样例。

## 交付与选择顺序

先明确准确ATen Schema、语义和输入域，确认匹配CANN已有目标算子，再选择opapi/aclnn（推荐）或兼容所需aclops/aclop。固定父仓与子模块身份；文档clone master --recursive是示例获取方式，不能替代可复现版本锁定。

两语言流程图分别查看：准备→开发→编译验证，其中开发拆为YAML、执行适配、辅助交付；前反向和SymInt按实际需求可选。图中“适配成功/性能最优”是流程目标，不代表已通过或仅注册就最优。OpInterface.h/cpp、AclOpsInterface.h、OpApiInterface.h等是生成交付件，不把改生成文件代替改配置。

## YAML版本和NZ分发

| 配置 | 固定文档含义及边界 |
| --- | --- |
| official/custom | 分别声明原生ATen和自定义接口，func保留名称、overload、参数、返回及别名/mutation |
| acl_op/op_api | 分别配置两条实现路线的PyTorch版本，缺省字段不能按另一条路线补齐 |
| all_version、[vX, newest] | 当前代码支持列表/版本范围；文档示例只列v2.1至v2.10，不是所有未来版本支持证明 |
| exposed | 商用公开接口的版本声明，通常只配置前向，不等于所有私有反向都公开 |
| internal_format_opapi | NZ输入默认走acl_op，显式白名单才允许转到op_api；不能从普通ND支持推出NZ支持 |
| symint | 在official/custom外同时声明SymInt路线，底层实现另有_symint后缀和相应类型 |
| gen_opapi | 在语义已对齐且除输出申请无额外适配逻辑时选择结构化生成 |

std.correction的旧/新参数不同须按版本分别声明，不能把int/Scalar、可选和默认值差异合成一个Schema。SymInt例子最终调用asIntArrayRefUnchecked，出现SymInt签名不证明底层完整保留任意符号维；实际lowering/运行约束另核。

VERSION_BETWEEN是编译期的PyTorch版本区间，不是NPU硬件型号区间。独立OpPlugin快照CMake从TORCH_VERSION的major/minor生成CURRENT_VERSION=VxRy；Version.h以V2R1..V2R16和闭区间比较定义宏。定义V2R16或VERSION_NEWEST不等于已经承诺运行PyTorch2.16；旧文档例子的V1R11/V2R0在该头文件未定义，不能原样当本快照完整编译配方。参考页将它称作NPU硬件版本的表述应按此源码层次纠正。

## 前反向和结构化生成分别适配

原生算子已有上游自动微分绑定仍需插件前/反向实现；自定义算子在derivatives.yaml按name与参数定义梯度表达式、不可微参数和output_differentiability，并用version区分版本。result、grads、保存的中间结果需对应真实生成规则；仅前向可执行不证明自动求导绑定正确。

结构化生成仅用于aclnn：gen_opapi.out或out0/out1配置shape、dtype及可选name；out变体的输出名须与Schema一致，inplace不另配out。size/dtype可引用输入、表达式或专用推导函数；out无需变shape或dtype检查时相应项可省略。name当前只支持与某输入同名；exec指定aclnn调用与参数顺序，只有参数顺序已一致时才可只写aclnn名。structured_inherit从out变体复用相同配置，不代替语义、别名与布局校验。

手写aclnn适配放op_api命名空间/KernelNpuOpApi文件，aclop放acl_op/KernelNpu文件。普通、out与inplace分别保持API合同：out先检查shape/dtype等；旧aclop非连续输出示例用连续临时Tensor执行再回写，inplace复用out路径，不能将直调nocheck函数当任意布局均安全。950DT仍不支持这条aclop路线。

## 回退宏不保证任意失败都回退CPU

OpPlugin DO_COMPATIBILITY 完整宏：静态查询aclnn执行与GetWorkspaceSize符号，任一缺失且设备为AclnnOnly时直接报不支持；其他情况告警并return调用点传入的originCallExpression。替代表达式可能是aclop或框架实现，不是统一CPU回退；符号存在后的参数、dtype或执行错误也不是该宏的自动回退条件。COMMON变体在该宏内没有AclnnOnly拒绝分支，不能忽略宏名差异。

参考页列EXEC_NPU_CMD、OPS_ERROR、FLOP_COUNT及apply_tensor/apply_tensor_without_format/check_tensor等辅助层：分配输出、校验、调用、错误格式化和理论FLOP计数各有职责。copy_scalar_to_device/binary_op_check示例标为参考逻辑，不当作完整稳定签名；check_tensor的概述也不保证错误dtype都能自动转好。TaskQueue的EXEC_NPU_CMD_EXT和低层回调另见[异步接入指南](torch_npu_custom_op_taskqueue_adaptation.md)，不能仅因名称相近互换。

## 自定义add示例不能直接推广

文档明确例子为PyTorch2.7.1/v2.7，前向计算x+alpha*y；但反向仅接收grad，复制后返回同一个result两次，derivatives绑定也没有传alpha或输入shape。由该数学定义可知，非默认alpha时y的梯度需要相应缩放，广播时还需恢复到各输入shape；当前片段没有这些信息，不能证明一般情况下正确。两个返回还共享同一Tensor，不假定它们是独立存储。

样例Schema的x/y、关键字Scalar alpha与公开Schema JSON里的self/other、普通float alpha不一致，文档签名也不同；需统一真实Schema、C++参数、生成器和公开声明，不能用名字相似通过一致性验收。说明文字把Python前缀写op-api，JSON实际写op_api，也应按真实配置格式核验。

Meta示例计算广播表达式再empty_like并固定self.dtype；它没有单独证明混合dtype提升、任意广播、stride/别名和运行实现一致。npu_transpose的permute/empty_like示例同样只说明注册方法，不据“视图/连续”的描述推导所有输入的共享存储合同。

测试只比较默认alpha同shape前向，并直接调用反向接口检查grad；没有通过output.backward验证derivatives绑定，也没有非默认alpha/广播/双重梯度/别名测试。历史“2 tests OK、1.199s”只属于来源输出；不是本卡执行结果或足以推广的正确性证据。allow_internal_format=False和jit_compile=False也是该样例配置，不代表所有模型必须如此。

## 辅助交付与验收

新增接口同时更新文档模板、publicAPI白名单、Schema清单及Meta注册；文件存在不等于接口在目标版本暴露。FX/compile的FakeTensor规格要与Eager一致，图后端还需要对应转换/函数化/捕获条件，见[图接入指南](../../integration/torchair/custom_operator_graph_contract.md)。

文档的reshape UT覆盖FP16/FP32及两种零维长度输入，属于测试设计示例，不证明任意接口已有边界覆盖。实际验收应覆盖真实输入域、非法参数、out/inplace、自动求导和图模式；按来源避免在TorchNPU源码根目录运行造成torch_npu._C遮蔽。编译成功、UT输出、Meta通过和端到端性能分别采证，本文未执行这些步骤。

## OpPlugin本仓版本、代码生成与弃用入口的补充

继续全文审阅OpPlugin发布快照dedc316708372c9a8bfde4527abd2a94b74840f5及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda的根说明、config与扩展示例。这里仍是独立固定来源，不证明该OpPlugin主线与前述PyTorch主线配套。主线明确third_party/op-plugin代码随TorchNPU集成进入torch_npu包，使用既有算子无需单独OpPlugin安装包；另行打包的aclnn_extension/cpp_extension是扩展示例，和重建torch_npu wheel区分。

发布根README以7.3/7.2/7.1/7.0、6.0及rc、5.0及rc分支映射对应TorchNPU产品列举历史组合，master例子为2.7.1；主线改由父仓配套/支持表管理。分支名、根页API“基于2.9/2.8/2.7.1/2.6”摘要与具体API支持不是同一精度，按准确gitlink及独立API页消费；不能在同一行里任取版本组成新基线。构建入口见[源码构建](../../bringup/torch_npu/torch_npu_source_build_and_linkage.md)。

本仓config示例all_version发布列v1.11、v2.0至v2.12，主线再列v2.13；它比前述父仓教程更长，但仍只是该文档列举，不等于真实生成器、编译宏和所有算子已支持每个版本。acl_op/op_api允许显式列表或闭区间，newest依当前列表解析；两个版本Schema不同就分别写func，不以同名覆盖旧签名。

普通/out/inplace、输出shape/dtype/name、exec顺序及structured_inherit遵循前文的结构化合同。gen_opapi.new_params还可配置派生局部变量再传exec，变量可见不证明额外语义自动正确；推导函数分别落KernelNpuOutputSize.h/KernelNpuOutputDtype.h。ACLOP示例声明contiguous_result却调用contigTensor，是文档片段变量缺口，不能原样当可编译实现，也不能把连续输出临时回写省掉。

deprecated.yaml的name须含overload（如npu_broadcast.out），replace可给迁移入口；生成TORCH_WARN_ONCE时却以不含overload的基本名显示。没有replace只是废弃警告，不自动生成等价替代，也不由warn-once推定接口已删除。out重载与普通入口的迁移仍分别核对。

贡献页把接口、yaml、前反向、实现和测试列为交付，并建议逐dtype泛化100至200例、正反向分别测试。这是来源开发验收目标，不是当前所有API已拥有这些测试或已通过；仓库治理、CLA、PR模板和pre-commit安装命令不作为模型优化技术卡或本工作区执行指令。

## 扩展接入方式、Meta与自动求导分别判断

| 示例 | 已说明的接入层与局限 |
| --- | --- |
| cpp_extension_base | schema+PrivateUse1前向+load_library；注释写“前反向”不表示已经绑定自动求导 |
| cpp_extension_full/module | 再注册Meta/反向，由调用者的Python autograd.Function.apply连接前反向 |
| cpp_extension_full/torch_lib_impl | C++ autograd.Function，加AutogradPrivateUse1/AutogradMeta注册，和普通设备实现分层 |
| cpp_extension_structured | YAML生成前向/反向实现，文档明确不自动绑定前反向；可在Python补绑定 |
| cpp_extension_pybind | 直接Pybind导出，接口形态灵活；不由导出本身取得Dispatcher/Meta/compile或梯度注册 |
| cpp_extension_asc | Ascend C直调经TORCH_LIBRARY_FRAGMENT/IMPL接入，包含Meta及原地Trig合同 |
| aclnn_extension | 单独生成并打包aclnn适配，代码生成步骤与前反向绑定不能混同 |
| framwork_cpp_extension | 历史Eager注册之外，另为TorchAir GE定义FX converter |

基础/完整Add都分配empty_like(self)、alpha固定1，Meta也只empty_like(self)。这些例子没有完整广播、类型提升、输出layout及两个输入设备一致性校验，不能提升为torch.add通用规格。OptionalDeviceGuard选self的设备，不会自动校验other或让不同设备输入变成合法跨卡运算；多卡必须核对实际设备及流，不能只添加guard就称跨device访问正确。

Python完整例保存x/y但反向只把grad_output传给自定义backward；C++完整例在Function.forward用AutoDispatchBelowADInplaceOrView后redispatch，在backward调独立反向接口，避免把自动求导注册递归回自身。两固定版本完整C++文件均有对应NPU与Meta Function。名称注册存在不表示更高阶梯度、所有训练路径或Meta别名已验证。

两完整Add反向直接result=grad并返回{result,result}，不是注释所称“创建输出内存”；两个返回还引用同一Tensor，Meta则返回同一empty_like结果两次。缺少输入shape，不能恢复广播输入梯度；前向alpha固定1也不能推广成可变alpha梯度配方。只看两个返回形状相同不证明二者有独立存储或所有alias合同均被Schema表达。

加载例多按glob选择首个匹配so，缺失报错，版本/ABI/多个旧库仍需核对。PrivateUse1/AutogradPrivateUse1与旧XLA/AutogradXLA的注释是历史适配说明，不是当前包改DispatchKey字符串即可兼容旧版本。README里的Ran xx tests/OK是占位输出，不记录为本地通过。

## aclnn_extension文档与实际生成脚本的差异

双语README称gen.sh可收第二个derivatives参数、列六个模块并含gen_autograd；实际两固定版本gen.sh只把$1作为算子YAML，derivatives文件名固定npu_custom_derivatives.yaml，非空判断总会尝试生成derivatives，末尾只有gen_backend_stubs，没有文档第六步gen_autograd。主线cpp_extension_structured/gen.sh与这个文件逐字节相同，也不能据“目录含derivatives”就认定自动求导已绑定。

实际固定derivatives.yaml内容为backward:[]。所读FastGelu测试仅float32、(3,16,32)、输入0至100，比较自定义NPU前向与已有torch.ops.npu.npu_fast_gelu后转CPU结果；没有独立CPU数学参考或output.backward验收。YAML中出现_backward函数仅表明其可生成独立调用，不是自动反向已经接线。

实际生成顺序为版本化op_plugin_functions→derivatives→接口/路由→structured实现→backend stubs；产出目录/源配置和安装环境必须一致。脚本用PATH的python读版本，后续用python3执行模块，setup.py又用sys.executable读版本，不自动保证三个名字指向同一个解释器。脚本没有set -e，前一步失败不能仅凭最后一步退出码判定全部成功；必须保留每阶段错误和实际生成物。

setup.py扫描生成的torch_npu/csrc/aten与op_plugin源码，排除部分主汇总/Everything文件以免重复定义，采用CppExtension/BuildExtension、C++17和当前major.minor生成CURRENT_VERSION宏；额外显式宏可覆盖，不能从文件存在推定语义配套。它把导数路径拼为op-plugin/config，但gen.sh产在op_plugin/config，ACNN_EXTENSION_PATH/SWITCH拼写也不同于gen.sh的ACLNN_EXTENSION_*；这些不能擅自视作自动别名，须按消费者及真实生成物排查，不直接断言所有构建必失败。

独立包install_requires精确torch去本地后缀的版本字符串，未同时锁定TorchNPU/CANN；wheel名不是完整依赖锁。文档混用npu_fast_gelu.yaml/npu_custom.yaml，以及torch_npu.npu_fast_gelu_custom/torch.ops.npu.npu_fast_gelu_custom，实际注册名和包导入应从配置/生成物确认。不要在样例同名源码根运行造成导入遮蔽；本文未生成、构建、安装或导入该包。

## Ascend C直调示例的版本、顺序与目标架构

OpPlugin普通cpp_extension发布页的Host示例用stream(true)+RunOpApiV2；主线改为五种可保序方式对照，并在实际pybind11.asc只公开方式3（stream(false)+RunOpApiV2）。**这里的方式4/5编号不能套用TorchAir八种对照的错误方式4/5**。真实launch放入队列并保持资源寿命，清Host队列不等于Device计算已结束，见[TaskQueue指南](torch_npu_custom_op_taskqueue_adaptation.md)。

普通cpp_extension/setup.py通过npu-smi info取首个可解析芯片名，包含950映射dav-3510、包含910映射dav-2201，其他情况报错。该字符串探测没有为全部可见设备分别选架构，不证明异构多卡或全部产品均可运行；C++17、当前torch ABI和依赖目录与TorchAir另一个示例的C++20/固定dav-2201分开。USE_NINJA=1只在此setup以精确字符串1选择，不是所有示例共享的布尔控制。

独立cpp_extension_asc示例给Add int/Trig float、ND、8×2048，Trig会修改out_sin/out_cos并返回新tan，schema中(a!)/(b!)不能丢。Meta empty_like只说明该例输出，不能补广播与混合dtype。发布包/命名空间误写cpp_extension_acs，主线改asc；调用章节却仍cd cpp_extension_base，不能按目录片段判断当前测试目标。主线外链CANN9.2与安装页的CANN9.1镜像分别保留，不拼成一套已配套环境。

kernel_extension_aclgraph双语示例独立明确A2/A3训练/推理产品，torch至少2.6、npugraph_ex需TorchNPU产品至少7.3、CANN toolkit/ops至少8.5；只用于该组示例，不给本卡其他扩展补硬件矩阵。它比较NPUGraph、make_graphed_callables和npugraph_ex三条路径，Meta/FakeTensor通过不代表三条任意动态shape都可捕获；发布torch_library README的schema引号错误在主线修正，不据它造另一API。实际架构、ops包与toolkit安装路径仍须对应。

## 历史GE converter示例和公开范围

framwork_cpp_extension保留PyTorch2.1/Python3.9样例身份，英文文首外链却指社区2.13文档，不将链接版本覆盖样例版本。它按REG_OP AddCustom的x/y输入和z输出注册torch.ops.myops.add_custom.default的GE converter，精确端口名/输出名与目标CANN算子定义一致才可使用；Pybind/Meta/自动求导与converter不是互相替代项。

发布片段缺typing.Any导入，主线补齐；示例运行路径仍指外部samples/CppExtensionInvocation，不是当前仓相对目录。外部算子工程必须已安装其实际Kernel/原型，仅复制custom_op转换片段不提供后端实现。本文只摄取框架调用及模型优化条件，Ascend C设备实现、外链Kernel工程、全部torchnpugen实现与设备测试尚未因此完成。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_overview_opplugin.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_overview_opplugin.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_preparation_opplugin.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_preparation_opplugin.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_flow_opplugin.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_flow_opplugin.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_development_opplugin.md)（primary）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_development_opplugin.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/reference.md)（primary）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/reference.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_compile_opplugin.md)（primary）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/adaptation_compile_opplugin.md)（constraint）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/sample_call_opplugin.md)（primary）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/custom_operator_adaptation/opplugin_operator_adaptation/sample_call_opplugin.md)（constraint）
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/opplugin_adaptation_flow.png)（constraint）
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/opplugin_adaptation_flow.png)（constraint）
- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/Version.h)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/CMakeLists.txt)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/op_api_common.h)（implementation）

- [固定来源 20](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/CONTRIBUTING.md)（primary）

- [固定来源 21](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/CONTRIBUTING.md)（constraint）

- [固定来源 22](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/README.md)（primary）

- [固定来源 23](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/README.md)（constraint）

- [固定来源 24](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/README.zh.md)（primary）

- [固定来源 25](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/README.md)（primary）

- [固定来源 26](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/README.md)（constraint）

- [固定来源 27](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/README_en.md)（primary）

- [固定来源 28](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/aclnn_extension/README.md)（primary）

- [固定来源 29](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/aclnn_extension/README.md)（constraint）

- [固定来源 30](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/aclnn_extension/README_en.md)（primary）

- [固定来源 31](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/cpp_extension/README.md)（primary）

- [固定来源 32](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension/README.md)（constraint）

- [固定来源 33](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension/README_en.md)（primary）

- [固定来源 34](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/cpp_extension_asc/README.md)（primary）

- [固定来源 35](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_asc/README.md)（constraint）

- [固定来源 36](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_asc/README_en.md)（primary）

- [固定来源 37](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/cpp_extension_base/README.md)（primary）

- [固定来源 38](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_base/README.md)（constraint）

- [固定来源 39](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_base/README_en.md)（primary）

- [固定来源 40](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/cpp_extension_full/module/README.md)（primary）

- [固定来源 41](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_full/module/README.md)（constraint）

- [固定来源 42](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_full/module/README_en.md)（primary）

- [固定来源 43](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/cpp_extension_full/torch_lib_impl/README.md)（primary）

- [固定来源 44](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_full/torch_lib_impl/README.md)（constraint）

- [固定来源 45](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_full/torch_lib_impl/README_en.md)（primary）

- [固定来源 46](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/cpp_extension_pybind/README.md)（primary）

- [固定来源 47](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_pybind/README.md)（constraint）

- [固定来源 48](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_pybind/README_en.md)（primary）

- [固定来源 49](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/cpp_extension_structured/README.md)（primary）

- [固定来源 50](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_structured/README.md)（constraint）

- [固定来源 51](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_structured/README_en.md)（primary）

- [固定来源 52](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/framwork_cpp_extension/README.md)（primary）

- [固定来源 53](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/framwork_cpp_extension/README.md)（constraint）

- [固定来源 54](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/framwork_cpp_extension/README_en.md)（primary）

- [固定来源 55](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/kernel_extension_aclgraph/pybind/README.md)（primary）

- [固定来源 56](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/kernel_extension_aclgraph/pybind/README.md)（constraint）

- [固定来源 57](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/kernel_extension_aclgraph/pybind/README_en.md)（primary）

- [固定来源 58](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/kernel_extension_aclgraph/torch_library/README.md)（primary）

- [固定来源 59](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/kernel_extension_aclgraph/torch_library/README.md)（constraint）

- [固定来源 60](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/kernel_extension_aclgraph/torch_library/README_en.md)（primary）

- [固定来源 61](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/README.md)（primary）

- [固定来源 62](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/README.md)（constraint）

- [固定来源 63](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/aclnn_extension/gen.sh)（implementation）

- [固定来源 64](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_structured/gen.sh)（implementation）

- [固定来源 65](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/aclnn_extension/setup.py)（implementation）

- [固定来源 66](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/aclnn_extension/npu_custom_derivatives.yaml)（implementation）

- [固定来源 67](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/aclnn_extension/test/test_npu_fast_gelu_custom.py)（implementation）

- [固定来源 68](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension_full/torch_lib_impl/csrc/add_custom.cpp)（implementation）

- [固定来源 69](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension/setup.py)（implementation）

- [固定来源 70](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/examples/cpp_extension/csrc/pybind11.asc)（implementation）

- [固定来源 71](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/aclnn_extension/gen.sh)（implementation）

- [固定来源 72](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/examples/cpp_extension_full/torch_lib_impl/csrc/add_custom.cpp)（implementation）
