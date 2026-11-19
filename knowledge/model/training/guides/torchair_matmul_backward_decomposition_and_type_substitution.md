---
type: Guide
title: Matmul训练分解：梯度布局、mask与类型替换
description: 说明matmul梯度的rank分支与contiguous成本、mask前置准备及类型替换参数缺口。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/__init__.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/__init__.py
  role: implementation
created_at: '2026-11-12T02:09:46Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Matmul训练分解：梯度布局、mask与类型替换

两版register_matmul_backward_decomp以py_impl修改指定dispatch key：to.other/type_as使用AutogradPrivateUse1，matmul_backward使用CompositeImplicitAutograd并套out_wrapper。add_npu_patch安装这些规则，和[GE算子降低](../../inference/guides/optimization/torchair/torchair_ge_matmul_lowering.md)的图节点转换分开。本文静态读取本地公式，没有执行训练或注册。

| self/other rank | 梯度构造与可见准备 |
| --- | --- |
| 1/1 | 按mask分别用other*grad、self*grad |
| 2/1 | unsqueeze后mm构造grad_self；self转置与grad的mm后squeeze构造grad_other |
| 1/2 | grad与other转置mm；self与grad的外积mm |
| self>=3，other为1/2 | grad整理成2D（有contiguous）；self梯度mm后view回原shape，other梯度需self.contiguous().view后mm |
| self为1/2，other>=3 | grad或其转置展成2D；other转置/contiguous/view参与self梯度；other梯度mm后view/transpose |
| 其余 | 分别matmul(grad,other转置)、matmul(self转置,grad) |

mask只控制所请求的梯度赋值，未请求项保持None。混合高低rank分支的部分contiguous/view准备在mask判断之前；关闭某个梯度不等于所有对应前置准备都消失。最终普通matmul分支没有在本地显式sum_to_size或按广播batch做梯度归约，不能把公式存在当成所有广播布局均已数值验证。

to.other的替换只执行self.to(other.dtype)，不消费other设备，也不使用non_blocking/copy/memory_format形参；type_as同样只取other.dtype。实际设备语义需结合该dispatch入口，不能按原算子名补回这里没转发的参数。

默认decomposition表另只在本地添加npu_define.allgather，以及版本对象与'2.3.1'比较满足时的_c10d_functional.all_to_all_single，外部通信分解见[GE通信合同](../../inference/guides/optimization/torchair/torchair_ge_collective_lowering.md)。本地未强制将版本对象转普通str，比较语义不能仅凭右侧字符串断言为字典序。调用方表与后续patch优先级按[FX编译管线](../../inference/guides/optimization/torchair/torchair_fx_compiler_pipeline.md)核对；注册本身修改的是共享dispatcher状态，不是单图私有规则。

## 实现来源

- [固定实现1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/__init__.py)：1–22、286–381、454–478。
- [固定实现2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/__init__.py)：1–22、282–376、444–464。
