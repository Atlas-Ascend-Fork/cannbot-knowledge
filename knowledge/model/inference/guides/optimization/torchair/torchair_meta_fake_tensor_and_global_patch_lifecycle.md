---
type: Guide
title: 编译前Meta补丁：打包mask、空统计与全局FakeTensor规则
description: 说明NPU编译Meta的打包mask与空统计、Div dtype补丁及全局一次安装的状态边界。
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

# 编译前Meta补丁：打包mask、空统计与全局FakeTensor规则

两版TorchAir的add_npu_patch先安装本地Meta/分解与FakeTensor规则，再按配置处理joint Pass。改动作用于进程共享表和函数引用，非每个模型的私有副本。固定主线92e1e967与发布7c6c754b在所列局部行为一致；本卡只静态读取，不执行patch或FakeTensor。

| Meta项 | 本地输出 |
| --- | --- |
| native_dropout，train真且p!=0 | 输出empty_like；mask字节数为输入numel向上对齐128后除8，dtype=uint8，同设备 |
| native_dropout，其他条件 | 原输入对象加ones_like(bool) mask；不在此验证p范围 |
| native_dropout_backward | empty_like(grad_output)，不消费mask/scale内容做数值计算 |
| _native_batch_norm_legit_no_training | 调用在模块加载时保存的原分解函数，随后把save_mean/save_rstd都替换为input.new_zeros((0,)) |

dropout计算numel使用无初始值的reduce(operator.mul, shape)，所以空shape的标量输入有局部异常路径，不能把打包公式直接推广为所有rank。BN的空统计是Meta合同，不是对设备统计值的数值验证。

注册helper对OpOverload直接登记，对packet遍历其全部overloads；同一键重复登记报错。npu_patch_meta逐项写全局decomposition_table（avoid_fallback名单除外），删除Meta py_kernel再py_impl注册，并替换FakeTensor的torch_decomp_decompositions查询函数：本地表命中返回True，其余交保存的原函数。该查询带lru_cache；异常前已修改的其他项没有统一回滚。

## Div快速Meta规则与一次性安装

fast-op私有接口导入触发ImportError时，本地Div补丁直接跳过。可用时，它保存make_fast_binary_impl(refs_div)的实现，新函数先取得其结果；若Tensor操作数全属于int8/uint8/int16/int32/int64，且参数中出现int/SymInt，则把结果.to(torch.float)。非Tensor参数不会使“所有Tensor均整数”变假；这里也不是设备Tensor的真实cast。

全局get_fast_op_impls被替换成lru_cache函数，第一次调用先触发原函数，再给aten.div.Tensor安装新实现并返回共享FAST_OP_IMPLEMENTATIONS。缓存存在不等于每次调用都重新安装。

add_npu_patch带run_once：只在整个函数成功返回后has_run=True；失败后可再次进入，先前已发生的全局修改不会由装饰器撤销。成功后换config或decomposition参数仍不会自动重跑；可手动把has_run设False重置，装饰器没有线程锁。既有joint共享表清理见[Attention/RMSNorm替换](torchair_joint_attention_rmsnorm_replacement_contract.md)。

## 实现来源

- [固定实现1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/__init__.py)：1–154、408–462。
- [固定实现2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/__init__.py)：1–152、403–452。
