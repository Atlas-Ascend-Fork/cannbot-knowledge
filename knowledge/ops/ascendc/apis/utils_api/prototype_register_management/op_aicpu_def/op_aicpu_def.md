---
type: API
title: OpAICPUDef
description: OpAICPUDef算子定义接口索引。
tags: [task.lookup, topic.implementation.operator_registration]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/prototype_register_management/OpAICPUDef/OpAICPUDef.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# OpAICPUDef

OpAICPUDef 用于定义算子在 AICPU 上的执行属性，包括引擎类型（Engine）、分片标志（FlagPartial）、计算开销（ComputeCost）、异步执行标志（FlagAsync）、Kernel 库与 SO 路径（OpkernelLib、KernelSo）、入口函数名（FunctionName）和扩展配置（ExtendCfgInfo）。用于 AICore 无法覆盖的场景下的算子下沉到 AICPU 执行。

<!-- cannbot:related:start -->
## 相关

- [AICPU launcher 缺 OP_ATTR_NAMES 编译错](../../../../runbooks/compilation/aicpu_launcher_op_attr_names.md)（`exemplifies`）：《AICPU launcher 缺 OP_ATTR_NAMES 编译错》的任务是“无属性 regbase 算子的 ADD_TO_LAUNCHER_LIST_AICPU 调用若照搬 AICORE 写法省略 OP_ATTR_NAMES()，AICPU 宏会把第二个形参位（op::FVector<std::string>&，属性名向量）错绑到 OP_INPUT(...)，触发引用类型不匹配编译错。判别=build.sh --pkg 编译期报 invalid initialization of reference of type 'op::FVector<std::basic_string<char> >&' from expression of type 'op::OpInput<...>'，定位行紧随算子名后缺 OP_ATTR_NAMES()。AICORE 变体无该形参位，省略合法，二者宏签名不可互换。”。《OpAICPUDef》具体提供“OpAICPUDef算子定义接口索引。”，它直接用于AICPU launcher 的 OP_ATTR_NAMES 形参、属性定义和 AICPU 原型。
- [KernelSo](kernel_so.md)（`related`）：《KernelSo》说明配置AICPU算子实现文件编译生成的动态库文件的名称。；《OpAICPUDef》说明OpAICPUDef算子定义接口索引。。二者在KernelSo、FunctionName、OpkernelLib和UserDefined共同确定AICPU实现动态库及入口符号的注册合同上存在可执行的直接衔接。
- [UserDefined](user_defined.md)（`related`）：《UserDefined》说明配置该算子是否为用户自定义算子，AICPU自定义算子的userDefined仅支持配置为“True”，若开发者没有配置的情况下，该参数会被默认设置为“True”。；《OpAICPUDef》说明OpAICPUDef算子定义接口索引。。二者在UserDefined是AICPU注册属性，与KernelSo、FunctionName、OpkernelLib、OpAICPUDef及编译/launcher合同共同生效上存在可执行的直接衔接。
- [AICPU（OpDef）](../op_def/aicpu.md)（`same_topic`）：“AICPU（OpDef）”处理设置AI CPU的配置信息：包括算子输入输出的名称、支持的数据类型、数据格式等信息。；“OpAICPUDef”明确OpAICPUDef算子定义接口索引。。实质衔接：AICPU() 的返回值就是 OpAICPUDef；后续配置由该对象承载，其他成员归属交给 part_of。
- [ComputeCost](compute_cost.md)（`same_topic`）：ComputeCost 与《OpAICPUDef》的实质衔接是：两张 ComputeCost 都要求固定值 100，但分别属于 OpAICPUDef 与 OpHostCPUDef；类定义决定该预留属性挂载在哪类 CPU kernel 注册上。
- [ExtendCfgInfo](extend_cfg_info.md)（`same_topic`）：ExtendCfgInfo 与《OpAICPUDef》的实质衔接是：ExtendCfgInfo 属于 OpAICPUDef 的扩展键值配置，AICPU 编译材料与 launcher 属性缺失故障说明该配置进入生成和加载阶段的位置。
- [FlagAsync](flag_async.md)（`same_topic`）：FlagAsync 与《OpAICPUDef》的实质衔接是：FlagAsync 是 OpAICPUDef 的预留注册属性且必须固定 false；HostCPU 同名字段、FlagPartial 和类定义用于避免把它误解为运行时异步同步开关。
- [FunctionName](function_name.md)（`same_topic`）：FunctionName 与《OpAICPUDef》的实质衔接是：FunctionName 在 OpAICPUDef 中指定 RunCpuKernel，OpHostCPUDef 对应方法及 Engine/OpkernelLib 决定该入口由哪个运行引擎和库加载。
- [OpkernelLib](opkernel_lib.md)（`same_topic`）：OpkernelLib 与《OpAICPUDef》的实质衔接是：OpkernelLib 在 OpAICPUDef 固定 CUSTAICPUKernel，必须与 KernelSo、Engine、FunctionName 和 AICPU OpDef/launcher 生成链一致。
<!-- cannbot:related:end -->
