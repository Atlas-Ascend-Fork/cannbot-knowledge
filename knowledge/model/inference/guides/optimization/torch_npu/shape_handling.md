---
type: Guide
title: ShapeHandling配置与恢复：文档合同和源码差异
description: 记录分档参数、batch/sequence差别及包装和绑定不一致，保留为待确认草稿。
tags:
- task.lookup
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/dynamicshape/shapehandling.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/overview/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_dynamo.py
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_torch/npu_shape_handling.cpp
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_torch/npu_shape_handling.h
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_package/shape_handling.cpp
  role: constraint
created_at: '2026-11-09T15:23:53Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# ShapeHandling配置与恢复：文档合同和源码差异

## 固定范围与草稿原因

依据TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的内置文档、NPUShapeHandling Python类、配置/调用局部以及三份C++定义/绑定。手册总览约束950DT，元数据保留950组但不扩大PR。文档和当前源码在若干关键调用与恢复处不一致，故status为draft，不提供已经可运行的调用配方，也不把静态推断当设备复现。

Python层NPUShapeHandling位于torch_npu.utils._dynamo，是继承_C._NPUShapeHandling的内部包装；此处不是承诺稳定公开命名空间。没有读取整个_dynamo.py或其他后端的全部接线，没有导入、构造或执行。

## 文档的options与规则字段

| 字段 | 文档默认及含义 |
| --- | --- |
| enable_shape_handling | bool，默认False，启用时设True |
| shape_handling_configs | list[dict]，文档默认None、启用时要求给出规则，最多BATCHSIZE与SEQLEN两种类型 |
| shape_handling_dict | 默认None，自定义预处理/后处理集合 |
| type | 必填BATCHSIZE或SEQLEN，不能重复同一类型 |
| dimensions | int或整数列表；batch默认[0]，sequence按规则推导，支持各输入不同序列维 |
| indices | 默认[]，运行时推导可处理Tensor的索引，不等于无条件处理所有任意rank对象 |
| value | 数字，默认0.0的pad值，不保证对模型数学语义中性 |
| gears | 默认[]；非空显式档位优先于min/max/policy |
| min_size/max_size/policy | 默认1/1024/TIMES；min/max生成只支持TIMES，CUSTOM应提供gears |

shape_handling_dict的短键trans_pre_fn/trans_post_fn/re_pre_fn/re_post_fn分别映射构造器transform_pre_fn/transform_post_fn/recover_pre_fn/recover_post_fn。文档推荐输入转Tensor列表、分组后还原多组args/kwargs、输出转Tensor组再恢复最终结构；不把长构造器参数名直接当短字典键。

## 档位选择与batch/sequence的不同操作

已读C++FindClosestGear选择不小于当前大小的最近档；文档“padding到最近上一个档位”措辞不能解释成向下缩小输入。TIMES生成保留min/max端点，中间补2的幂，因此非幂边界也会出现，并非全部档位必为2的幂。要求min≥1、min≤max；每类最多64档，batch档1..8192、sequence档1..1310720，显式gear排序并检查唯一性。

默认batch策略检查所选Tensor同维大小一致，超过最大档先按最大档split，最后一组再向上pad；Recover按内部记录裁掉batch padding并沿该维拼接。默认sequence策略只pad，超过最大档直接TORCH_CHECK报错；NPUShapeHandling::Recover没有独立sequence裁剪，不能把文档“超过max自动分割”或“恢复原shape”无差别套给sequence输出。双类型时先sequence处理再batch切分。

索引/维度必须在真实输入范围内、非负；batch索引排序后检查重复。sequence用索引排序映射维度，但去重在原始indices的相邻比较上执行，不能据此宣称所有乱序重复都会被拒绝。部分所选索引之后还有未选Tensor时，遍历中访问m_indices[pos]缺少末尾pos范围保护，是需要重点核验的静态边界，不提供已安全工作的部分选择示例。

## Python包装与绑定的可见不一致

1. 配置get_config_copy补的shape_handling_configs默认是[]，不是文档None；构造器在None/空列表时反而延迟创建默认batch规则，所以“开启必须显式给规则”与包装层行为不同。
2. 文档称BATCHSIZE多维列表只用首元素，_validate_configs却先把它改为整数，紧接着又要求list/tuple，静态路径会落入类型错误分支；不要据文档把多元素列表当已验证输入。
3. Python transform/recover分别以tensors=和tensor_groups=调用super，所读pybind绑定的两个关键字都叫inputs。保留这处调用合同不一致，未执行确认实际安装二进制是否相同或异常文本。
4. 自定义pre后只提供默认post时，默认post需要的indices/leaves/spec只在默认pre分支赋值；recover也有相同配对问题。不能从参数单独可选推定任意混搭均已接通。
5. 所读_patch_dynamo_context门控只认包装链中的compiler_name=inductor，直接Module/类调用在该局部包装中另有早退；文档给npugraphs组合例子，但不能只据该例认定这里已处理所有backend/Module。其他接线未全审，不作端到端绝对不支持结论。

## 内部对象和验证边界

绑定提供BATCHSIZE/SEQLEN、TIMES/CUSTOM枚举，initialize有显式gears和min/max/policy两个重载，transform返回分组Tensor，recover恢复列表；可注册非空batch/sequence策略替换默认，已初始化时复制其现有配置。BS策略有Transform/Recover，Seq只有Transform，默认sequence无对等恢复方法不是遗漏一个文档示例即可补齐。

内部pack_op_info记录为64位：op4、index16、原size36、dimension8位，范围在编码处检查，unpack为对应层次；旧OP_MASK等宏被标弃用。这是当前内部记录布局，不是可跨版本持久化的外部Schema。Python默认flatten/unflatten仅替换结构中的Tensor叶、保留其他叶，输出恢复采用最后一组的结构元数据，不证明任意不同组结构均可安全合并。

验证需固定真实构建、规则、padding数学语义、拆分独立性、输出裁剪及结构，并核对绑定与回调接线后再运行。分档减少编译或捕获次数不替代正确性；当前源码差异未消除前不将文档片段当作生产支持承诺。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/dynamicshape/shapehandling.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/overview/overview.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/utils/_dynamo.py)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_torch/npu_shape_handling.cpp)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_torch/npu_shape_handling.h)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/inductor/aoti_package/shape_handling.cpp)（constraint）
