---
type: Guide
title: npugraph_ex 内存复用：图池、输入别名与输出保存
description: 说明三种复用模式的优先级，区分 user/mutated/参数输入和 clone_output 的覆盖问题。
tags:
- task.optimization
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/memory_reuse.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/memory_reuse.md
  role: constraint
created_at: '2026-11-09T02:14:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# npugraph_ex 内存复用：图池、输入别名与输出保存

## 版本与范围

依据发布子模块 7c6c754bed00c86ffaaa2a45cb7ac2724f058013，选择 A2/A3 推理，未做运行验证。

## 三种复用模式

use_graph_pool 接收 graph_pool_handle 创建的显式池，可供多个图使用；设置后自动关闭 reuse_graph_pool_in_same_fx，后者默认 True，用于同一 FX 图内不同 shape 的 aclgraph。clone_input 默认 True，可与前两种模式分别共存；跨 FX 图的输入复用还需显式共享池。

dynamic=True 能让多种 shape 在满足 Guards 时共用 FX 图，但不同 shape 仍可能分别捕获 aclgraph；不能把 FX 图数量当作捕获图数量。

## 输入类别与别名

clone_input 针对 user_inputs，不将 parameter/buffer 或 mutated_inputs（例如 KV Cache）统一克隆。mutated input 地址改变触发 Recapture，不能按普通特征输入的处理假定安全。关闭 clone_input 后，若新输入地址变化，框架可能把新数据复制到首次输入的旧存储以避免重捕获；代码其他位置仍引用旧 Tensor 时，会观察到数据被覆盖。

因此 clone_input=False 并不等于“完全没有拷贝”，也不保证输入对象的别名不受影响。权重、缓存与用户输入需要分别核对存储和生命周期。

## 输出保存

clone_output 默认 False。复用池后后续执行可覆盖先前输出，长时间保存结果应考虑设为 True 或按实际生命周期显式复制，并计算额外内存/拷贝成本。

## 验证

至少连续运行两次，保存第一次输出和原始输入的独立参考，再替换 user input、替换 KV Cache 地址、切换 shape，核对别名、数值、捕获次数与内存峰值。单次输出正确无法检验复用问题。

- [固定地址重放原则](../../../concepts/frameworks/npugraph_replay_address_contract.md)
- [捕获次数与调试选项](npugraph_ex_capture_controls.md)


## 主线明确的输出别名例外

固定主线文档明确：即使 clone_output=True，与输入存在别名关系的输出也不会被克隆，以保持输入输出引用一致性。因此该开关不能保证所有返回值均是独立快照；需要长期保留此类结果时，应在图外按实际语义显式保存独立副本，并核对原地更新。该说明是主线文档补充，不能仅凭发布页未写该句断言两个版本实现不同。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/memory_reuse.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/memory_reuse.md)（constraint）
