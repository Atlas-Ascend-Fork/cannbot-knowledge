---
type: Guide
title: 批量P2P的派发与Work列表：版本门槛和子组rank
description: 对照两版P2P的coalescing/backend批派发、Work数量、组内rank及debug包装门槛。
tags:
- task.implementation
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/distributed_c10d.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/distributed_c10d.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/distributed_patches.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py
  role: implementation
created_at: '2026-11-12T02:15:11Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# 批量P2P的派发与Work列表：版本门槛和子组rank

固定TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的_batch_isend_irecv。两版本地补丁将torch.distributed及distributed_c10d的batch_isend_irecv指向此函数；外层补丁加载协议与后端通信实现未展开。仅静态审阅，没有执行进程组、设备或P2P。

## 第一项决定派发，批大小不等于Work数量

函数先取p2p_op_list[0].group和tensor.device，之后才可能进入_check_p2p_op_list；空列表没有在此先正常返回。不能把这个入口当成先完整统一校验、再无副作用发起所有请求的事务。

| 首Tensor/分支 | 实际调用 | 返回 |
| --- | --- | --- |
| CUDA | coalescing_manager内逐条以位置参数传tensor/peer/group/tag | cm.works |
| NPU coalescing门槛成立 | 先_check_p2p_op_list，再manager内逐条传tensor、group、tag和group_dst或group_src | cm.works |
| NPU其余路线 | 收集op.__name__、Tensor及转换后的rank列表，一次backend.batch_isend_irecv | 只含一个后端Work的列表 |
| 其他device类型 | 逐条调用原op，收集真值Work；注释称兼容Gloo | reqs列表 |

没有在这些本地路线把数值Tensor转CPU计算。其他device分支也不是把任意NPU不支持算子自动回退CPU。NPU batch路线只逐项检查tensor.device.type为npu，没有在本地完整再校验每项device index、group和op是否合法；实际后端仍有自己的限制。

NPU coalescing的peer_kwarg通过`op.op is isend`的对象身份选择group_dst，否则group_src，值用op.group_peer。batch路线则使用peer：首项group为None时取default组并保留global peer；显式group时逐个get_group_rank转换。batch调用没有另传逐项tag，不能套用coalescing路线的所有参数透传行为。调用方应按实际返回Work列表等待，而不是假定列表长度总等于P2P操作数。

## 版本门槛与debug包装

| 条件 | 主线 | 发布 |
| --- | --- | --- |
| CANN门槛 | 导入时调用_is_gte_cann_version('9.0.0')，捕获其bool结果；helper委托_C比较 | 导入时取cann_version，入口直接执行与'9.0.0'的比较，没有用主线bool helper |
| 普通ProcessGroup的设备名门槛 | Ascend910B1..Ascend910B4_1或Ascend910_9362..Ascend910_9392 | 第一段相同，第二段上界为Ascend910_9391 |
| FakeProcessGroup backend | 直接使coalescing条件成立，不再受上述版本/设备名与ProcessGroup类型的and门槛限制 | 没有同一特例 |
| batch backend是_ProcessGroupWrapper | 解一层wrapped_pg后调用batch方法 | 没有这层unwrap |

设备名区间是普通字符串比较，不是完整产品能力矩阵。主线在Fake判定前也已取设备名/backend，不能把Fake特例推成这里完全不访问设备状态。CANN结果在导入时保存，之后不是每个调用重新探测；发布表达式与主线委托的版本比较也不能不加核对地视为相同规则。

unwrap的源码注释关联TORCH_DISTRIBUTED_DEBUG=DETAIL和ProcessGroupWrapper缺少batch方法；本地实际只解一层，没有递归剥离任意嵌套包装的协议。coalescing与单次batch都依赖首项建立的backend/组选择，修改列表或组映射后需按实际调用链核对。

这组函数返回异步工作列表，没有在末尾统一wait，但设备/后端选择、rank转换、检查和逐项派发等Host工作已经发生，不能把async_ops=True解释成没有Host成本。与对象收集的padding和尺寸同步区分见[对象gather](torch_npu_gather_object_padding_and_hccl_routing.md)。已覆盖的非等长collective包装继续引用[reduce_scatter_tensor_uneven](../apis/torch_npu/reduce_scatter_tensor_uneven.md)及[all_gather_into_tensor_uneven](../apis/torch_npu/all_gather_into_tensor_uneven.md)，本卡不重复它们的产品或split协议。

## 固定实现来源

- [distributed_c10d.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/distributed/distributed_c10d.py)（primary）：11–14、48–50、58–135。
- [distributed_c10d.py f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/distributed/distributed_c10d.py)（implementation）：27–27、44–46、49–100。
- [utils.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/utils.py)（implementation）：51–62。
- [distributed_patches.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/distributed_patches.py)（implementation）：19–27、59–73、88–96、135–151。
- [__init__.py f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/__init__.py)（implementation）：191–194。
