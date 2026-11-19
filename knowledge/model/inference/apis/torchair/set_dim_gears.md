---
type: API
title: set_dim_gears：GE 动态 shape 分档的维度与档位限制
description: 设置输入 Tensor 的动态维度档位，说明 dynamic=True、非私有格式、档位数量和 0/1 边界。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/inference/set_dim_gears.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/dynamic_gears_merge_policy.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/inference/set_dim_gears.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_gear_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/__init__.py
  role: implementation
created_at: '2026-11-08T11:58:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# GE 动态维度分档

## 接口

```python
torchair.inference.set_dim_gears(t, dim_gears)
```

t 是待分档输入 Tensor；dim_gears 为维度索引到整数列表或元组的字典。接口没有返回值。它为 GE 整图优化设置已知档位，不负责给输入 padding 或把任意 shape 自动归档。

## 必须同时满足的条件

- 与 `torch.compile(dynamic=True)` 配合；接口只符号化指定 Tensor 的维度，其他 scalar 的符号化仍依赖 Dynamo。
- 参与分档的 Tensor 不使用 FRACTAL_NZ、NC1HWC0 等私有格式。
- 总档位数量不超过 100，档位值不含 0 或 1；这两个值不能按普通动态维度处理。
- 实际 shape 必须在档位中，否则可在编译或执行阶段报错；同一个 Tensor 不能重复设置不一致的档位。
- 只用于 GE 整图优化；不能同时配置 Dynamo 导图或 RefData 类型转换功能。

## 验证

在首次执行、编译读取档位之前设置；后续不必重复设置。覆盖每个计划档位及 0、1、越档输入，核对报错和重编译行为；不能直接复用到 npugraph_ex。适用边界来自固定主线文档，未运行分档实验。

## 版本入口

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)：来源快照、部署配套和实际运行验证分别核对。

## 发布接口与主线校验细节

发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013` 的A2/A3接口页与主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 保留相同GE整图、dynamic=True、私有格式禁用和档位范围要求。主线总览的950支持不能回推发布版；本节仅对照固定页及主线实现，未执行档位编译。

主线set_dim_gears还要求维度索引为[0,rank-1]内整数，不能直接使用常见负轴-1；每维档位列表/元组的条目数为2..100，每个条目为整数。局部代码仅显式排除值0，但公开文档同时排除0/1，不能因1可通过这一步就当作支持；也不能把单个静态值包装成一条gear列表来规避动态条件。

zip要求所有参与组合的档位列表长度相同；product形成笛卡尔积，生成选项时去重后总组合数≤100。列表条目数与最终唯一组合数是两项检查，不能只限制单维≤100。生成的ge.dynamicDims按输入/维度信息构造并去重，展示顺序不是业务档位身份。

存在分档输入时，guard_gears_shape对未设置gear的Tensor或其未分档维度使用guard_int具体化；分档维度则检查当前值属于枚举集合，不是允许最小/最大值之间所有整数。因此dynamic=True不表示其他Tensor维度必然仍全部泛化，越档失败也不由自动padding修复。

主线/发布分档特性页的示例有torch.compile调用省略dynamic=True，约束段却明确要求它；实际接入应显式满足dynamic=True和fullgraph，不把示例省略作为豁免。组合的算子关系与FA值依赖仍见[分档与静态下沉](../../guides/optimization/torchair/torchair_ge_dynamic_shapes_and_fa_tiling.md)。

## Evidence

- [docs/zh/ascend_ir/api/inference/set_dim_gears.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/inference/set_dim_gears.md)（primary）
- [docs/zh/overview.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）
- [动态分档的组合约束](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/dynamic_gears_merge_policy.md)（constraint）

- [发布版 zip/product 组合和 FA 下沉定位](../../guides/optimization/torchair/torchair_ge_dynamic_shapes_and_fa_tiling.md)

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/inference/set_dim_gears.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/_gear_utils.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/inference/__init__.py)（implementation）
