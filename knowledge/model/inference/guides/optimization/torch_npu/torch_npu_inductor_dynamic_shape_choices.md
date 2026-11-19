---
type: Guide
title: Inductor动态形状：符号化、输入分档与分组调优
description: 区分编译图复用、padding/split和Kernel候选复用，保留分档实现的待确认边界。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/dynamicshape/shapehandling.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/dynamicshape/symbolic.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/overview/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/compilation_backend/inductor.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/torch_compile/compilation_backend/inductor.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/torch_compile/overview.md
  role: constraint
created_at: '2026-11-09T15:23:53Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# Inductor动态形状：符号化、输入分档与分组调优

## 固定来源与三种复用层次

依据TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf内部形状文档及总览的950DT范围，不扩展其他产品/版本；分组开关的PR/DT范围按独立页核对。仅静态审阅，未编译或运行模型。

| 方法 | 改变哪一层 | 需要核对 |
| --- | --- | --- |
| Symbolic | 用SymInt/SymFloat表示未知维，尽量复用编译图 | guard、算子lowering、运行时shape和重编译 |
| ShapeHandling | 将输入pad/split到有限档位，图/捕获复用 | 数学等价、独立拆分、输出恢复及当前实现差异 |
| Grouped autotune | 同一动态Kernel按特征分桶，复用代表shape选出的launcher | 单动态轴、模板/访问签名、预算及实际shape性能 |

同名bucket不是同一对象：输入分档改变被模型计算的数据形状，分组autotune通常选择Kernel配置；两者均不等于删除所有Guard或允许重放不同地址的静态图。

## dynamic参数与示例的限度

dynamic=False以静态shape编译，True尝试符号化处理未知维，None由框架自动判断。True旨在减少重编译，不保证任何形状变化都只编一次；静态/自动也不是每个模型均已最优。文档例子混有未定义model_fn、测试只打印说明等片段，不当作已经实测的编译次数。

可根据固定输入、变化范围和运行开销对比，符号化可能增加运行时开销，复杂模型/回调仍受支持度限制。调试例子用torch._dynamo.export打印graph_module.code，只是查看图，不代表NPU运行或完整导出部署能力已验证。

## 分档与捕获前处理

文档示例用BATCHSIZE/SEQLEN，最多两类规则；TIMES或显式gears、Tensor维度/索引及四个自定义转换回调见[分档接口草稿](shape_handling.md)。源文中的4次到2次编译/捕获表只是示意，不是所有业务输入的上界或本次结果；当前Python/C++接线、sequence超档/恢复等存在差异，必须先核对真实版本。

分档说明还给npugraphs后端示例并建议dynamic=False，在捕获前处理到固定档位。固定shape只是捕获的一项前提，不解除地址、依赖、状态和生命周期要求；当前所读局部门控与该示例存在张力，不据文字推荐未经验证的组合。padding值和slice/concat恢复应保持模型数学语义，不能对跨batch/序列交互运算机械拆分。

## 分组Autotune

Symbolic页当前仅一个动态轴的pointwise/reduction/persistent_reduction Kernel可分组，从numel提取特征并用代表shape选config，运行时bucketize并材料化block；访问签名/代表不可构造或显存预算超限回普通调优。AOT/CppWrapper落盘支持不是MegaCache已打包CppWrapper的证明，见[CostModel与分组指南](torch_npu_inductor_costmodel_and_shape_groups.md)。

分别测首次图编译、档位padding/拆分、mask/数据准备、调优预算和业务shape稳态。代表shape最快、编译数减少与真实模型端到端收益是不同证据，保留关闭优化的同负载对照。

## reduce-overhead的Tree复用层次

同提交中英文用户页将Inductor reduce-overhead描述为NPUGraph Tree：缓存多个捕获版本，按输入形状路由，并管理分段子图内存。它与符号化编译共用FX图、ShapeHandling改变输入档位、grouped autotune选Kernel配置是不同层次；“最匹配”措辞不证明可以把不兼容shape直接送入任意静态图。

用户页称dynamic shape会触发重编译，应按“可能增加重编译开销”理解，不推定每次shape变化必重编译，也不据dynamic=True保证一次编译全覆盖。optimizer step通常不入图是该用户页的实践描述，无法据此否定其他已专门适配的编译训练方案。Tree缓存、内存复用、地址和具体算子仍受各自限制；本卡950DT内部特性的范围不因通用用户页扩大。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/dynamicshape/shapehandling.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/dynamicshape/symbolic.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/overview/overview.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/compilation_backend/inductor.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/torch_compile/compilation_backend/inductor.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/overview.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/torch_compile/overview.md)（constraint）
