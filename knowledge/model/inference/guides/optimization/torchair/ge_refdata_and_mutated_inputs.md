---
type: Guide
title: GE RefData：原地输入、在线开关与离线默认
description: 区分 RefData 与固定输入地址，说明在线/离线配置和动态分档互斥。
tags:
- task.optimization
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/ref_data.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/frozen_parameter.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/dynamic_gears_merge_policy.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/ref_data.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/graph_pass.py
  role: implementation
created_at: '2026-11-09T02:48:45Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# GE RefData：原地输入、在线开关与离线默认

## 版本与范围

依据 TorchAir 固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`。该提交属于 ascend_26_0_pt28 的固定来源组合；不是所有历史或主线版本的通用契约。发布部分选取 A2/A3；主线 A2/A3 与950的限定范围见下节，不回推发布版。

## 选择依据

输入会被 Assign/ScatterUpdate 等 Ref 类算子改写时，RefData 转换可减少重复拷贝。它描述 GE 对输入 mutation 的处理，不等于权重地址固定，也不自动保证 KV Cache 重分配后旧图仍安全。

在线 torch.compile 默认关闭，通过 config.experimental_config.enable_ref_data=True 开启；离线 dynamo_export 路线默认已开启。不能因离线默认开启就推定在线默认相同。

## 组合与核验

GE 动态分档明确不支持同时配置 RefData，因此先在不分档路径确认实际原地更新，再选择适合的执行方式。检查源图 mutation、转换日志和执行后输入内容；单次返回值相同不证明原地语义保留。

固定地址优化与 RefData 是不同开关。Parameter 或 mark_static_address 只适合真实地址稳定的输入，内容更新、别名和地址变化分别检查。

- [动态分档条件](../../../apis/torchair/set_dim_gears.md)
- [固定输入地址](../../../optimizations/rules/frozen_parameter_address_contract.md)


## 验证边界

分别核对实际软件版本、配置生效日志/图结构、输出与存储语义，再比较同输入的稳态耗时。本文为固定文档和静态接口审阅，没有执行上游代码、NPU 数值或性能实验。

- [软件栈来源与适用性](../../../concepts/frameworks/ascend_software_stack_baselines.md)

## 主线转换与日志方向

固定主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的本节对应文档已与发布 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013` 逐页对照；主线总览声明A2/A3与950PR/950DT，未在这些接口页另列产品排除。950仅属于主线证据，不回推发布配套，也不证明两仓主线组合已兼容。

主线特性页仍区分离线dynamo_export默认开启与在线enable_ref_data默认False；只适用于GE。示例日志写“Replace ...:RefData with ...:Data”，不能据字符串顺序断言转换方向相反：主线replace_data_to_refdata遍历Data，按ref_input_idx找到需要改写的输入，设置_origin_data_name后把op.type改为RefData，并更新引用名称。应以转换后的图节点、索引和实际输入写回判断，而不是从旧日志措辞还原算法。

实现生成名称时包含shape、stride、storage_offset和输入对象身份，并检查图内重名；名称存在并不证明任意别名或重新分配都满足契约。仍分别核对mutation、最终图、布局和存储变化，不能把RefData当作永久地址保证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/ref_data.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/frozen_parameter.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/dynamic_gears_merge_policy.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/ref_data.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/graph_pass.py)（implementation）
