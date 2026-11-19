---
type: API
title: register_fx_node_ge_converter：按准确 overload 注册 GE 转换
description: 以装饰器为准确的 torch.ops 节点注册 Ascend Converter，并区分 Meta 推导与 GE 转换。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/torchair/register_fx_node_ge_converter.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/custom_op_graph/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/register_fx_node_ge_converter.md
  role: constraint
created_at: '2026-11-08T11:58:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 注册 FX 节点的 GE Converter

以下仅示意注册形式，转换函数需按准确 Schema 实现：

```python
@torchair.register_fx_node_ge_converter(torch.ops.npu.my_op.default)
def converter(x, y, z, attr1, attr2):
    raise NotImplementedError("按该算子实现 Ascend IR 转换")
```

接口接收待转换的准确算子对象，返回供转换函数使用的装饰器，不是可单独执行算子的运行 API。相同短名的不同 overload 必须分别核对 Schema、参数顺序与输出结构。

Converter 将 FX 算子映射为 Ascend IR；Meta 推导则向 PyTorch 描述 shape、dtype 和内存关系，两者互不替代。原地算子还涉及别名、mutation 与函数化。注册动作应在模型编译前执行，实际覆盖必须由 FX 图中的准确节点确认。

验证顺序为 Eager 输出、Meta/符号推导、GE 构图、真实执行与输出比较。Converter 缺失不能通过只补 Meta 来解决。本文为固定主线接口说明，没有编译或运行自定义算子。

## 版本入口

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)：来源快照、部署配套和实际运行验证分别核对。

## Evidence

- [docs/zh/ascend_ir/api/torchair/register_fx_node_ge_converter.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/torchair/register_fx_node_ge_converter.md)（primary）
- [docs/zh/custom_op_graph/overview.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/custom_op_graph/overview.md)（constraint）
- [docs/zh/overview.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [完整页复核来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/register_fx_node_ge_converter.md)（constraint）
