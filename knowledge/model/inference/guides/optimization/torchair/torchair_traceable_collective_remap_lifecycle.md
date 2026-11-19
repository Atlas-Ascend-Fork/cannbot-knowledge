---
type: Guide
title: 通信跟踪映射：导入副作用与AllGather布局适配
description: 区分导入时remap表调整和旧手动补丁，记录两版覆盖策略、concat/stack回拷与uneven局部失败。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/adjust_traceable_collective_remaps.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/adjust_traceable_collective_remaps.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/__init__.py
  role: implementation
created_at: '2026-11-10T14:08:40Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 通信跟踪映射：导入副作用与AllGather布局适配

## 与手动patch_for_hcom是两条入口

本卡绑定TorchAir主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`与发布`7c6c754bed00c86ffaaa2a45cb7ac2724f058013`。两版包__init__都会调用adjust_traceable_collective_remaps；它在版本条件满足时修改torch功能化通信的进程级remap字典并挂载辅助函数，不要求用户先手动调用patch_for_hcom。

这与[旧补丁的全局distributed函数替换](collective_communication_graph_contract.md)不同，也不把[GE通信转换](torchair_ge_collective_lowering.md)的具体group/rank/count约束重复为新支持矩阵。整卡平台未知，保持draft、空平台；未导入TorchAir、创建组或运行通信。

## AllGather条目的版本差异

函数直接比较`torch.__version__ >= '2.3.1'`；实际比较语义依赖版本对象，不仅据右侧字符串断言字典序或未来版本能力。进入分支后，用从distributed_c10d导入的函数对象作为key：

| 条目 | 发布快照 | 主线 |
| --- | --- | --- |
| _all_gather_base、all_gather_into_tensor | update覆盖为all_gather_tensor_inplace_fixed | 仅key不存在时新增，已有上游/其它注册保留 |
| all_to_all、broadcast、send、recv | update为NPU跟踪patch | 仍update覆盖相应条目 |

主线保留已有AllGather remap，但随后仍把`all_gather_tensor_inplace_fixed`等属性设置在torch.distributed._functional_collectives命名空间。因此看到该属性存在，不证明remap表最终使用的也是这份helper；需同时核对原始函数对象key对应的value。该注册表、公开distributed函数和某张FX/GE图的执行是三个不同层次。

这条主线增量是保留已有AllGather选择，不是把全部通信重映射变成“仅注册一次”。重复调用仍可重写其它条目/属性，导入成功也不认证实际安装包的所有tracing消费者与通信协议。

## AllGather结果先按concat，再尝试stack

两版all_gather_tensor_inplace_fixed函数AST相同：async_op=True立即ValueError；group未给或为假值时选WORLD，仍为None则报错。随后调用功能化all_gather_tensor(input,gather_dim,group,tag)。

若结果shape恰与output_tensor一致，直接copy_回输出并返回该Tensor。否则以`input_tensor.shape[0]`作为分段长度，固定沿dim=0 split结果，再沿dim=0 stack；只有新shape与目标完全一致才copy_并返回，否则ValueError。它没有仅reshape到任意同numel输出，也不是返回Work句柄。

签名中的gather_dim不等于任意非零轴stack布局都受此回退支持：这条stack变换固定dim=0。函数也没有在此建立全部标量、空首轴、分组大小或dtype的合法性验证。成功shape分支仍不证明异步重叠、rank顺序、通信完成或完整算子支持；最后的copy_应计入集成成本。

## uneven扩展失败只保留局部结果

两版还在try中导入torch_npu的all_gather_into_tensor_uneven/reduce_scatter_tensor_uneven及对应patch，再update字典并挂载属性；仅捕获ImportError，主线pass、发布return。缺少这一扩展时，不会回滚此前已写入的普通通信条目或属性；其它异常没有在该except统一吞掉。

相应uneven计数、GE映射和Eager依赖仍复用既有通信卡，不以此导入分支扩展产品支持。排查通信入图或AllGather输出shape时，分别保存实际Torch版本、被调用函数对象、remap value、目标输出shape及是否async；不能为了探测是否可用就执行全局补丁或把注册成功当设备验证。本次没有运行tracing、通信或性能实验，未新增verified。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/adjust_traceable_collective_remaps.py)（primary）：定向范围1–103。
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/adjust_traceable_collective_remaps.py)（implementation）：定向范围1–85。
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/__init__.py)（implementation）：定向范围31–37, 46–56。
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/__init__.py)（implementation）：定向范围20–20, 44–44。
