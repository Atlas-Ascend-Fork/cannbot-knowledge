---
type: Guide
title: 对象gather的准备成本：尺寸同步、填充与HCCL路线
description: 跟踪对象collective的padding、Host标量、allgather准备和版本目的rank差异。
tags:
- task.implementation
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/distributed_c10d.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/distributed_c10d.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/distributed_patches.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py
  role: implementation
created_at: '2026-11-12T01:59:30Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# 对象gather的准备成本：尺寸同步、填充与HCCL路线

固定TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`和发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的_gather/_gather_object。本地补丁将torch.distributed及其distributed_c10d下的两个API指向这组实现；主线通过注册的distributed补丁表/赋值helper完成，发布在_apply_distributed_methods_patch内直接赋值。这里只读本地方法和接线，没有执行通信、对象转换或设备操作；上游对象编解码和HCCL内部另计。

## gather到一个rank，可能仍在每个rank准备全部输出

| 本地条件 | 路线与准备 |
| --- | --- |
| 非NPU Tensor | 调用相应ProcessGroup.gather；子组把global dst转为group-local rootRank。 |
| NPU且兼容路线成立 | 获取NPU backend并调用gather，只有目的rank传输出列表。主线还按设备名字符串区间限制兼容路线；发布没有这层设备名筛选。 |
| NPU其余路线 | 先broadcast_object_list发送目的rank各输出shape；没有gather_list的rank为每个shape执行torch.empty(...).npu()，再调用backend.allgather。 |
| async_op=False | 最后work.wait后返回None；True仅返回Work，前面的检查、对象广播和输出申请仍先发生。 |

主线的兼容设备名检查使用字符串`>=/<=`：Ascend910B1..Ascend910B4_1或Ascend910_9362..Ascend910_9392；它是本地代码门槛，不是从设备能力数值推导的矩阵。发布仅看are_compatible_impl_enabled返回值。主线NPU兼容子组还将global dst转为组内root；发布对应NPU兼容分支直接传原dst，不能把两个快照的子组语义视为完全相同。

默认NPU路线的警告“HCCL doesn't support gather”描述此实现为何选allgather，不等于当前整个库和全部设备永久没有gather能力。`.npu()`明确请求迁移前一步torch.empty创建的Tensor；没有指定device的empty也不能在这里当成已在目标NPU上零成本申请。目的rank只有既有列表，非目的rank仍可能持有world_size份输出，故“结果只在一个rank可见”不代表其他rank没有接收/内存成本。

## 对象协议有独立的尺寸collective和Host标量消费

_gather_object先检查目的rank的输出列表，取_object_coll_device，再调用外部_object_to_tensor取得payload与local_size。随后每个rank：

1. 创建world_size个Long尺寸槽并all_gather local_size。
2. 对这些单元素Tensor取max，再`.item()`/int得到max_object_size。若槽在NPU，这里需要Host可用的标量，不是纯设备端异步控制；本地未显式调用全设备synchronize，不能把它等同于该更强语义。
3. input_tensor.resize_(max_object_size)，将各rank的payload统一到最大字节长度。这个表达式没有按每个rank真实长度消除padding，也没有本地清零新尾部。
4. 目的rank申请world_size×max_object_size个uint8，并切成不重叠view作为输出；调用本地_gather且不传async_op，因此其最终wait不会被跳过。
5. 只有目的rank按原尺寸调用外部_tensor_to_object写object_gather_list；其他rank返回。

若第4步进入默认NPU allgather路线，还会执行上一节的shape对象广播，非目的rank也申请全套payload输出。对象尺寸偏斜大时，padding、额外接收、Host标量消费和转换可能比实际元数据内容大很多；本地没有从本协议自动改成按各rank长度的变长传输。上游_object_to_tensor/_tensor_to_object、设备选择和序列化格式没有在本组展开，不据其名称补造所有对象都零拷贝或固定发生某种CPU/NPU往返的结论。

## 目的rank与版本门槛

| 主线新增条件 | 行为 |
| --- | --- |
| dst与group_dst都省略 | global dst=0。 |
| 两者同时给出 | 在非成员早返之前抛ValueError。 |
| 仅group_dst | 无group时取default组，再get_global_rank转成global dst交_gather。 |
| weights_only=True且CURRENT_VERSION<(2,14) | 先抛RuntimeError，不静默改用旧对象协议。 |
| CURRENT_VERSION>=(2,14) | 把weights_only传给两端对象转换helper；旧分支不传该参数。 |

发布签名只有dst=0/group，没有group_dst或weights_only。主线“传给helper”不等于本地已经实现或证明所有对象格式与安全策略；对应上游消费者仍须匹配实际PyTorch版本。

调优时把对象控制面与模型Tensor collective分开观察：保留组大小、真实/最大payload字节数、目的rank转换、有效兼容模式、输出申请和Host等待位置。支持清单见[原生collective约束](torch_npu_native_collective_constraints.md)，异步Work与存储寿命见[通信内存复用](torch_npu_collective_memory_reuse.md)。

## 固定实现来源

- [distributed_c10d.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/distributed_c10d.py)（primary）：15–43、46–48、138–344。
- [distributed_c10d.py f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/distributed_c10d.py)（implementation）：103–197、200–254。
- [distributed_patches.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/distributed_patches.py)（implementation）：29–43、59–73、88–96、135–151。
- [__init__.py f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py)（implementation）：191–198。
