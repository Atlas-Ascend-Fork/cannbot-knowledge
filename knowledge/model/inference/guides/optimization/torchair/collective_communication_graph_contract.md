---
type: Guide
title: 集合通信入图：GE 支持范围、Send/Recv 与稳定拓扑
description: 在 Eager 通信成立后核对 GE 集合通信 Converter，说明 Send/Recv 的组成员和 StableRDFS、动态 shape
  边界。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/communication_graph.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/communication_graph.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/patch_for_hcom.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/graph_failed_cases.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/（beta）torch_npu-distributed-all_gather_into_tensor_uneven.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/torch_npu-distributed-reduce_scatter_tensor_uneven.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/torchair/patch_for_hcom.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/communication_graph.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/communication_graph.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_send_recv.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_send_recv.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py
  role: implementation
created_at: '2026-11-08T11:58:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# GE 集合通信入图

## 前提和范围

先在 Eager 验证通信组、设备、rank、数据和调用顺序。固定主线的 GE 后端默认集成相应 Converter，支持 all_gather、all_gather_into_tensor、all_reduce、all_to_all、all_to_all_single、broadcast、reduce_scatter_tensor、send/recv 及文档列出的 uneven 接口。

图支持清单只表明这份来源的接口支持，仍需核对具体 overload、参数及软件配套，不能推导任何通信组合均可成图。

## Send/Recv 专项检查

Send 与 Recv 成对使用；dynamic=True 时不同 shape 可产生不同 FX 图。未传 group 的 GE 路线须有适当默认组；显式 group 只包含参与通信节点。图中存在多个 Send/Recv 时，来源要求 StableRDFS 稳定遍历顺序。

torch_npu.distributed.reduce_scatter_tensor_uneven 不支持 PRODUCT 归约。组参数、shape 和 rank 顺序的错误应先按通信合同处理，不能直接归因于图优化。

## 验证

逐项确认 Eager、图节点和多 rank 结果；分开记录捕获/编译耗时与通信计算重叠。出现问题时恢复 Eager 通信，保留各 rank 的顺序、组和 shape 证据。本文对应固定主线，未进行多卡测试。

## 版本入口

- [软件栈来源与适用性](../../../concepts/frameworks/ascend_software_stack_baselines.md)：来源快照、部署配套和实际运行验证分别核对。

## npugraph_ex 发布版与旧补丁

固定发布子模块 7c6c754bed00c86ffaaa2a45cb7ac2724f058013 的 A2/A3 npugraph_ex 默认集成所列集合通信入图，包括 all_gather、all_gather_into_tensor、all_reduce、all_to_all、all_to_all_single、broadcast、reduce_scatter_tensor、两种 uneven 及 send/recv；前提仍是所有算子先能 Eager 执行。不同 shape 的 Send/Recv 可能产生不同 FX 图。

该页中的默认组、StableRDFS 说明明确写的是 max-autotune，不能直接重标为所有捕获后端的统一配置。另一个 patch_for_hcom() API 针对 PyTorch2.1 补齐原生部分通信支持，不能当作 PyTorch2.8 或所有新版本的必要初始化步骤。

融合/拓扑优化后仍要检查跨 rank 通信顺序，见[GE 调度与控制依赖](ge_scheduling_and_static_partition.md)。

## 发布版 AllGather 输出形状案例

固定发布子模块的 A2/A3 案例中，PyTorch 期望三维输出而 GE HcomAllGather 产生二维拼接结果，错误直到下游 Transpose 检查 perm 才暴露。需要按该接口的真实 output_size 在 Converter 中恢复规格，不能推广为所有 AllGather 都无条件 Reshape。

- [比较通信前后 Meta 与 GE shape](ge_shape_dtype_failure_diagnosis.md)

## 入图清单不替代独立接口的产品范围

固定 OpPlugin 主线的两个 uneven 产品页列 A2/950DT 与 Atlas 推理产品，但未列 A3，且限定单机。与本卡通用后端入图清单应分层阅读：列表中的接口名不能独自证明在本卡全部产品、所有拓扑上均可调用；未列产品也不是绝对不支持的证明。

使用 uneven 路径时先按独立 API 的产品、单机、分割及返回值契约核对，再验证目标后端实际入图。两仓主线并非已经确认的发布配套。

- [非等长 Gather 的限定范围](../../../../training/apis/torch_npu/all_gather_into_tensor_uneven.md)
- [非等长 ReduceScatter 的限定范围](../../../../training/apis/torch_npu/reduce_scatter_tensor_uneven.md)
- [变长 All-to-All 的计数矩阵](../../../../training/apis/torch_npu/all_to_all_vc.md)

## 主线旧补丁仍会修改进程全局函数

主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的patch_for_hcom页仍定位为PyTorch2.1兼容入口。__init__.py中即使进入“2.3.1及以上无需调用”的Warning分支，也没有立即return；后续仍安装DeepSpeed补丁并替换torch.distributed.all_reduce、all_gather、all_gather_into_tensor、broadcast、all_to_all_single、all_to_all。不能把Warning当作函数已经变成no-op，或在未知新版本上反复调用它作为通用初始化。

源码直接比较torch.__version__与"2.3.1"，实际排序依赖版本对象的比较实现；仅凭表达式不判断为纯字符串或版本误判。旧分支中还可能替换torch_npu.distributed的uneven接口。这里是进程内函数替换，不是只给某一张图添加标记，也不能据补丁存在推定训练、异步通信和所有overload均已支持。当前已纳入支持的后端路径先按清单接入，不自动补做旧补丁。

## 主线npugraph_ex清单与后端配置边界

主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的npugraph_ex通信页列11个入口：all_gather、all_gather_into_tensor、all_reduce、all_to_all、all_to_all_single、broadcast、reduce_scatter_tensor、两个uneven及send/recv。仍要求脚本中所有算子先可Eager执行；send/recv成对，dynamic=True时不同shape可产生不同FX图，不能用一个捕获实例假定覆盖所有通信尺寸。

主线已删除发布页夹带的max-autotune默认组/StableRDFS说明，约束段写“无”。这表示该页没有新增专门条目，不免除通信API自己的dtype、group、rank/形状、同步/异步和产品限制；GE稳定拓扑配置也不能作为npugraph_ex的统一必填项。普通torch.compile(..., backend="npugraph_ex", fullgraph=True, dynamic=False)示例仅说明入口，不能证明11个API的任意overload及所有多卡组合均已验证。

该清单对当前框架范围的950仍需与每个独立算子产品表求交集；uneven的A3/单机边界继续按前文限定。本次未初始化通信组、发送数据或捕获通信图。

## 版本比较表达式的证据限度

完整复查该主线__init__.py，两个条件直接比较torch.__version__与"2.3.1"，未在此处强制str转换。排序语义取决于实际版本对象的比较实现；不能只因右操作数为字符串就认定按纯字符串排序，更不能据此断言2.10等版本分支错误。Warning后继续替换全局通信函数的控制流事实仍成立，版本表达式和全局副作用分开核对。本次未导入torch或执行补丁。

## Evidence

- [docs/zh/ascend_ir/features/basic/communication_graph.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/communication_graph.md)（primary）
- [docs/zh/overview.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [补充来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/communication_graph.md)（constraint）

- [补充来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/patch_for_hcom.md)（constraint）

- [补充来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [补充固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/graph_failed_cases.md)（constraint）

- [补充固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/（beta）torch_npu-distributed-all_gather_into_tensor_uneven.md)（constraint）

- [补充固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/distributed/torch_npu-distributed-reduce_scatter_tensor_uneven.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/torchair/patch_for_hcom.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/__init__.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/communication_graph.md)（constraint）

- [完整页复核来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/communication_graph.md)（constraint）
## send/recv 的安装路线、默认通信组与文档版本差

`features/basic/communication_graph.md` 表1把 11 个入口统一表述为「调用 torch.compile 默认已支持」。逐项配对该「默认」后，实际是两条不同的安装路线加一组运行期解析：

- 安装路线：9 个入口由 `patch_for_hcom` 直接替换 `torch.distributed.*`（all_reduce/all_gather/all_gather_into_tensor/broadcast/all_to_all_single/all_to_all 六个直接替换，两个 uneven 仅在 torch<2.3.1 且 torch_npu 已导入时替换；__init__.py 主线 63–105/发布 51–77 同构）。`send`/`recv` 不在 patch_for_hcom 内（两 pin `__init__.py` 无 send 字样），其补丁只在导入期的跟踪重映射中安装（legacy_send/legacy_recv 条目与 `_functional_collectives` 属性挂载，[通信跟踪映射](torchair_traceable_collective_remap_lifecycle.md)已载）——只调用 patch_for_hcom 不会安装 send/recv 补丁；反过来看，import torchair/npugraph_ex 已默认执行重映射。两条路线最终都落到 `npu_define._send/_recv` 转换器（[GE通信转换](torchair_ge_collective_lowering.md)已载，不重复）。
- 默认通信组：文档注意事项「不传入 group 参数时需要有默认通信组」的兑现位置在补丁函数内——tracing 时 group 为 None 即解析为 `c10d._world.default_pg`（hcom_send_recv.py send 主线 79/发布 79，recv 主线 156/发布 155），随后 `get_process_group_ranks(group)` 取 rank 列表；「group 应只包含参与通信的节点」是协议级要求，补丁与转换器层没有成员校验，错误成员在通信/运行层暴露。
- 版本差：发布版 communication_graph.md 删去了主线第 31 行「reduce_scatter_tensor_uneven 不支持 dist.ReduceOp.PRODUCT」约束（两版唯一实质差异）；本卡前文的 PRODUCT 结论来自主线文档侧，发布页未重申。uneven 实现侧两 pin 同构。
- StableRDFS 注意事项：`_process_send_recv` 只在 max-autotune 模式且 send/recv 节点数大于 1 时自动把用户配置改写为 StableRDFS 并 once 告警，其余编译模式提前返回、不自动设置（npu_fx_compiler.py 主线 925–960/发布 826–860 同构）；CANN≥8.6.0 不满足时仅 ERROR 日志、不中断编译。文档的「需要设置」在 max-autotune 外仍是手工义务，分支细节由[FX编译管线](torchair_fx_compiler_pipeline.md)承载。

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/__init__.py)（implementation）：窗口 44–77（adjust_traceable_collective_remaps 调用 44、patch_for_hcom 51–77）；主线 55–105 既有来源复读（直接替换块 82–88、uneven 条件块 92–105）。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_send_recv.py)（implementation）：1–163 全文（op define 与 Meta/PrivateUse1 11–50/90–113、converter 52–58/115–127、send/recv patch 68–90/145–163）。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/experimental/hcom_send_recv.py)（implementation）：1–162 全文（diff 仅 import 写法 13 与折行；default_pg 79/155、get_process_group_ranks 80/156 同构）。
- [新增来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（implementation）：窗口 925–960（`_process_send_recv`：hasattr 门 926–928、计数 930–935、CANN8.6.0 门 940–948、mode 门 950–951、StableRDFS 改写 952–960）。
- [新增来源 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py)（implementation）：窗口 826–860（同构）。
- 既有来源补读窗口：两 pin `docs/zh/ascend_ir/features/basic/communication_graph.md` 全文复读（表1 15–27、注意事项 29–33）；发布版经 diff 与主线逐行比对，唯一实质差异是主线第 31 行 PRODUCT 约束在发布版缺席。负向扫描（无截断 rg）：`npu_send_patch_dist`/`npu_recv_patch_dist` 安装点两 pin 各仅 `_utils/adjust_traceable_collective_remaps.py`；`python/torchair/__init__.py` 两 pin 均无 send 字样（rg -c 为 0）。全部静态读取，未 import/运行上游。
