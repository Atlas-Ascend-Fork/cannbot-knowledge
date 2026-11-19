---
type: Guide
title: GE基础构图：Const存储、自动提升与属性上下文
description: 区分Data/Cast描述、Const原始Storage与逻辑视图、有限自动提升、异常嵌套状态和诊断PythonCode的边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py
  role: implementation
created_at: '2026-11-10T12:57:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE基础构图：Const存储、自动提升与属性上下文

## 固定版本与范围

全文核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的ge/_ge_graph.py。此前只覆盖局部函数的两份文件在本次补齐全文；本卡限定Python图描述与调用合同，不替代原生执行器、kernel和完整设备能力。产品矩阵未知，保持draft与空平台；未导入上游、构造/反序列化图、生成或执行代码、读设备数据或做性能实验。

## Data与Cast只先建立图描述

Data先追加节点、写index及转换后的Proto dtype、layout和device_type；placement只允许NPU/CPU。shape给定则写维度，否则写[-2]，不能按这个列表长度就当作已知一维Tensor。复制输出描述到input_desc，再登记索引；异常时没有回滚此前追加节点。

Cast先加dependencies控制边，再接x与其描述，dst_type原值写属性，只先创建命名输出Tensor，没有在该函数填完所有输出dtype/shape。Tensor缓存和最终Meta/Infer结果要分别看，不能把图上Cast节点存在当作设备已经转换或所有目标类型支持。

get_invalid_desc缓存UNDEFINED Proto描述并标_is_unfed_optional；调用方通常CopyFrom，不把可选空槽当真实Tensor输入。bytes及二维列表转换工具只做限定容器/编码装配，不提供完整值域或底层原型验证。

## Const保存底层存储，不是任意view的逻辑拷贝保证

Const拒绝GE Tensor。dtype省略时Torch Tensor按自身类型，其他值经array_default_f32和NumPy推导；Python float默认FP32、空list默认INT32，已有ndarray直接保留而不是套用所有Python默认。目标类型经ge_type_to_torch_type取得，非Torch值构造Torch Tensor，不同dtype再to。

随后写v.untyped_storage()到字节流，同时描述shape取v.shape，layout=ND；这里没有先统一contiguous或按storage_offset截取逻辑元素。对于非连续、偏移或大底层Storage的视图，不能仅凭逻辑shape认为字节只包含该视图需要的元素；这是静态存储路径，未运行反例或读设备内容。

_torch_tensor_to_ge_const另在no_dispatch下把非CPU Tensor显式cpu再调Const，直接Const没有完全相同的前置流程。两条入口不混用，也不以None dtype推导所有低位类型都可序列化。

readable控制_readable_value保存原值repr，真实value.data与可读字符串不同；repr受对象显示规则影响，且关闭readable时不能由诊断PythonCode认定可无损重建。Const返回的Tensor仍按通用构造器先保存未设置的Meta/dtype缓存，后续Meta及推导负责补齐，见[Tensor元数据](torchair_ge_tensor_dtype_metadata.md)。

## 自动Const提升范围有限

auto_convert_to_tensor用inspect.signature.bind取得args/kwargs，没有在这里apply_defaults；再按inputs_dynamic/inputs_optional展平、提升和重组。动态输入必须list/tuple且非optional，各项最终须GE Tensor；普通可选None可保留，TT_INDEX_NUMBER可先把非Tensor转INT64 Const。

已有GE Tensor不做通用公共类型推断；_get_promoted_dtype只收集限定浮点/整数集合。Python float/int输入只在相应已有类型集合不超过一种时按该类型建Const，否则拒绝；Torch Tensor走显式常量入口。NumPy取首元素后的分支也不是全部复杂Python值、复数或任意容器的通用提升算法。

没有动态参数说明时直接返回bundle_inputs；绑定后缺省/关键字参数位置、动态列表展平及实际原型数量仍需核对。它与Converter中显式dtype_promote到Meta输出类型不是同一套策略。

## 嵌套计数与attr_scope不是事务恢复

包装器调用前增加线程局部auto_convert_nesting，正常返回再减少，最外层追加诊断PythonCode；异常路线没有finally减少计数，不能由正常路径概括失败后状态必已复原。

attr_scope在进入时设置extral_node_attrs，finally清空为{}，不恢复先前嵌套值。_set_extral_node_attrs只处理Tensor或扁平list/tuple，序列元素非Tensor断言；其他输出类型的分支只是构造ValueError而没有raise。不能宣称任意嵌套/Mapping输出均带相同属性或会统一拒绝。

## PythonCode与结构化Ascend IR参数

parse_inputs/parse_kwargs主要生成可读表达，Const输入依赖_readable_value，字符串只是加引号而非完整序列化，输出容器只处理限定深度。add_python_code及format_python_code用于诊断记录，不证明复制文本能在独立进程恢复全部输入、属性与数值。

torch_args_to_ge_args两版都存在，主线主要改用集中错误消息。它按ge_inputs/ge_attrs的迭代顺序要求args总数相等，required必须Tensor、optional为Tensor或None、dynamic先只要求list/tuple；动态项的完整元素验证还在后续装配层。属性None跳过，vt_tag查构造器；torch.dtype属性转换成图API GE类型，这与回调Schema标量的c10数值域不同。

核对每层实际dtype域、可选槽、Meta、底层存储、Const提升和失败后的线程状态，再验证图编译、布局与精度；本次未执行这些实验。

- [IR装配和可选项](torchair_ge_ir_assembly_compatibility.md)
- [辅助层显式类型提升](torchair_ge_metadata_support_helpers.md)
- [Schema回调标量类型域](torchair_ge_callback_schema_codegen.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py)（implementation）
