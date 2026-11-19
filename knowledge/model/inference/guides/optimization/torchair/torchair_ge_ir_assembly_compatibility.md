---
type: Guide
title: GE IR装配：可选项省略、输出层级与兼容查询
description: 解释两版compat_ir的输入属性装配、IrDef可选项筛选、动态输出返回结构、缓存查询范围和失败后的图状态。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/compat_ir.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/compat_ir.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/utils_tools/utils_tools.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/utils_tools/utils_tools.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/core/torchair.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/core/torchair.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/core/npu_wrapper.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/core/npu_wrapper.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/cann_ir_ability/cann_ir_ability.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/cann_ir_ability/cann_ir_ability.cpp
  role: implementation
created_at: '2026-11-10T10:43:14Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE IR装配：可选项省略、输出层级与兼容查询

## 固定版本与范围

全文核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的compat_ir.py，两版AST相同。本卡限定Python IR装配及兼容性查询入口，不替代底层CANN查询、InferShape或kernel实现；产品矩阵未知，保持draft与空平台，未导入上游或调用原生扩展。

## 输入、属性与控制依赖分别装配

_assemble_inputs要求None或dict，按dict顺序追加：GE Tensor复制desc并以输入名重命名；None写空输入边及invalid desc；list/tuple逐项要求GE Tensor，动态名字拼为name0、name1等。列表不是一个打包Tensor，也没有自动Cast、广播、跨设备搬运或任意嵌套容器转换。

_assemble_attrs要求每个值为ge.attr._Attr实例，再merge_to属性；普通Python标量没有在此自动变为类型化属性。_assemble_dependencies只要求None或list，逐项追加dependency.controller，没有完整同图、类型、环或运行完成检查。图控制边不是已经发生的host barrier或跨rank同步。

## 输出层级由描述决定

_assemble_outputs对None或空list/tuple返回None；每个字符串建立一个Tensor输出，二元(str,int)描述建立动态输出列表并依序命名。多个顶层描述返回tuple，只有一个顶层描述则返回其本身，所以单个动态输出描述会返回list；不是所有多输出都返回扁平tuple。

这里检查二元组字段类型，但没有单独要求动态数量非负，也未检查所有输出名字唯一、实际shape和dtype。数量和名称符合Python装配格式不等于底层原型、Meta和设备输出均匹配。

## 有无IrDef会改变可选输入与默认属性处理

IrDef链式记录必选/可选/动态输入、必选/可选属性和输出及support_dtype等描述；本模块没有逐一用这些字段完成全Schema或dtype校验。attr方法登记可选默认值，required_attr登记必选属性；不能由“已声明必选”推导调用时缺失一定在此被完整拦截。

ge_op在ir=None时直接_custom_op，因此输入None会保留空边/invalid desc，也不走本模块的is_cann_compat分支。提供ir时先过滤值为None的输入，再收集实际出现且在IrDef可选名单中的输入名；属性中等于默认值的可选项被删掉，只把实际非默认可选属性名交兼容性查询。两条路线不能共用“None永远保留占位边”或“所有调用都已检查兼容”的结论。

is_cann_compat以optype和两个名称tuple调用_torchair.check_cann_compat，返回非空错误文本时AssertionError；lru_cache(maxsize=4096)缓存相同参数查询。这里查询的是算子和已用可选输入/属性名称，不包含每个实际Tensor的shape、dtype、值域与真实执行结果，不能把空错误文本当作任意输入的完整支持矩阵。

## 图写入不是原子验证

_custom_op先get_default_ge_graph().op.add并设置type及唯一name，再依次装输入、依赖、属性和输出。装配中抛异常时本函数没有删除已追加节点；兼容检查通过也不保证后面的字段校验全部成功。排查时应区分查询失败、装配失败、推导失败和设备执行失败。

核对准确IrDef、可选项是否实际传入、默认属性是否被省略、输入顺序、动态输出层级和依赖边，再验证Meta、CANN原型及实际执行。本次仅静态审阅，没有生成模型图或设备实验。

- [GE构图对象与控制边](ge_converter_tensor_and_control_edges.md)
- [自动符号规则](torchair_ge_symbolic_inference.md)
- [Converter注册与自动映射](torchair_ge_registration_prims_lowering.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/compat_ir.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/compat_ir.py)（implementation）


## 原生绑定上的CANN兼容探针：check_cann_compat与CheckAclnnAvaliable

补读两 pin 的原生绑定层后，本卡把“兼容查询”从 Python 装配入口延伸到 `_torchair` 原生模块上的两个导出函数，前文 compat_ir.py 装配合同保持不变。两者都在 `PYBIND11_MODULE(_torchair, m)` 内注册，且是仅源码可见的入口：两 pin 的 docs 目录对这两个探针名 rg 零命中，没有文档承诺。

`_torchair.check_cann_compat` 的原生实现在 `torchair/cann_ir_ability/cann_ir_ability.cpp`（两 pin 各 56 行全文核对；注册于 npu_wrapper.cpp，主线 81 行、发布 78 行）。它先 `ge::OperatorFactory::IsExistOp(optype)`，查不到即返回“maybe you need upgrade cann version”；再 `CreateOperator` 后用 `GetAllIrAttrNamesAndTypes` 收集属性名集合，用 `UpdateInputDesc` 试探可选输入、用集合成员资格判断可选属性，全部通过返回空串，否则拼出带“please upgrade cann version”的错误文本。发布快照第 45 行为“unsupport optional input”、主线修为“unsupported optional input”，除该词与 include 顺序外两 pin 去注释去空白归一化比较等价——判定逻辑相同、错误文案措辞不同。它只回答算子与已用可选名称的存在性，不校验 shape/dtype/值域，也不执行算子；Python 侧 lru_cache 缓存的是 optype 与名称元组，与这里每次重查的语义不能混同。

`_torchair.CheckAclnnAvaliable` 是 ACLNN 符号可用性探针（`torchair/utils_tools/utils_tools.cpp`，主线 61 行、发布 66 行全文核对，除大括号排版外归一化逐字节等价）。函数内 `static` 局部变量只执行一次 `dlopen("libopapi.so", RTLD_LAZY)`——首次失败同样被缓存，进程内不再重试；句柄非空时每次调用 `dlsym` 查询传入的 aclnn 符号名，命中返回 true，否则 false。绑定链为 npu_wrapper.cpp:43 注册 → torchair.cpp:283–285 `TorchNpuGraphBase::CheckAclnnAvaliable` 先 `gil_scoped_release` 再转发，两 pin 相同。它只回答“当前 libopapi.so 是否导出该符号”，不是对 shape/dtype/设备合法性、性能或执行成功的试运行。

实际门槛与动作：要判断“本机 CANN 是否带某个 aclnn 符号或某个 GE 算子可选输入”，可用这两个探针做符号级确认；若首次 dlopen 失败（例如 libopapi.so 不在进程库路径），探针结论在该进程内不会随环境修复自动更新，须重启进程再测。两个探针的 Python 消费状态不同：`check_cann_compat` 在两 pin 都有 Python 调用方——compat_ir.py 的 `is_cann_compat`（主线 258–260 行、发布 236–238 行，即前文提供 IrDef 的 ge_op 路径所用的兼容查询入口）经 lru_cache 包装调用 `_torchair.check_cann_compat`，不能宣称编译器缺少 GE 兼容检查；仅 `CheckAclnnAvaliable` 在两 pin 的 python/ 范围内没有 Python 调用方——导出 API 无内部消费者不构成把该版本边界排除出知识的理由，但也不能据此宣称 TorchAir 编译流程已在内部用它做 ACLNN 降级。本节为固定两 pin 的静态源码观察，未在设备上运行探针。

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/utils_tools/utils_tools.cpp)（implementation）：1–61 完整读取。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/utils_tools/utils_tools.cpp)（implementation）：1–66 完整读取（末行无换行符，wc -l 计 65）。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/core/torchair.cpp)（implementation）：275–290 定向窗口（283–285 为 GIL 释放后转发）。
- [新增来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/core/torchair.cpp)（implementation）：275–290 定向窗口。
- [新增来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/core/npu_wrapper.cpp)（implementation）：1–46、70–90 定向窗口（28 行 PYBIND11_MODULE、43 行与 81 行注册）。
- [新增来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/core/npu_wrapper.cpp)（implementation）：28–46、60–90 定向窗口（43 行与 78 行注册）。
- [新增来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/cann_ir_ability/cann_ir_ability.cpp)（implementation）：1–56 完整读取。
- [新增来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/cann_ir_ability/cann_ir_ability.cpp)（implementation）：1–56 完整读取。
