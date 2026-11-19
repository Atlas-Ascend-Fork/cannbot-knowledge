---
type: Guide
title: TorchNPU HCCL 通信域创建阶梯：RankTable、子域派生、流选择与合并收集
description: 从 ProcessGroupHCCL 两版源码记录通信域创建回退链、P2P 域命名、RootInfo 广播与版本一致性告警、通信流 id 入口及 coalescing 组提交语义。
tags:
- task.optimization
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.hpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/Init.cpp
  role: implementation
created_at: '2026-11-12T13:53:54Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# TorchNPU HCCL 通信域创建阶梯：RankTable、子域派生、流选择与合并收集

## 固定版本与范围

主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 与发布快照 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 的 `csrc/distributed/ProcessGroupHCCL.cpp`（8194/7132 行）。只读静态行段审阅，未运行进程组、未创建任何通信域。已有相邻卡的边界：域级 `hccl_config` 映射见 [Options 卡](torch_npu_hccl_pg_options.md)，Work 等待/内存生命周期见 [跨流内存复用卡](torch_npu_collective_memory_reuse.md)，RankTable 文档面与建链超时见 [RankTable 卡](torch_npu_ranktable_communication_init.md)，Scalable RootInfo 文档口径见 [RootInfo 卡](torch_npu_scalable_rootinfo.md)；本卡只补它们未映射的源码行为段。

## 创建回退阶梯与 group 括号

缓存未命中时 `createHCCLComm`（主线 :3272-3334）先结束再重启 `hcclActiveGroupCounter_` 层的 `hcclGroupStart/hcclGroupEnd`——两次都以 `OpCommand::RunOpApiV3("hcclGroupEnd"/"hcclGroupStart", ...)` 走 ACLNN 下发通道（:3289-3304），即建域动作对算子队列可见。随后按 devicesKey 建立 `hcclStreams_`、`hcclEvents_`、`rateCtrlEvents_`、`collectiveCnts_` 四组 per-key 缓存；P2P 域额外登记进 `p2pSendRecvKeys_[rank_]`（:3306-3331）。阶梯本身两级：`createHCCLCommEx` 失败回退 `createHCCLCommOrigin`（:3295-3297；发布版 :2832-2895 同构）。

`createHCCLCommEx`（主线 :3040-3093）：RANK_TABLE_FILE 为空或不可读、或 HCCL 运行时缺 `hcclCommInitClusterInfoConfig` 符号即返回 false 换原路；`HCCL_CONNECT_TIMEOUT<300` 时 WARN_ONCE 建链超时风险。仅全局域（`global_ranks_in_group` 为空）且 DEFAULT 型走 `createGlobalHcclComm(rankTableFile, rank, commConfig)`，失败同样回退；其余交给子域路径。发布版的子域创建内联在 Ex 尾部（:2637-2830），主线重构为独立 `createHCCLCommSub`。

## Origin：子域派生、Scalable 与 RootInfo

主线 `createHCCLCommOrigin`（:2945-3038）按序尝试三条路：先在 `ROOTINFO_SUBCOMM_ENABLE` 且非空 `global_ranks_in_group` 时调 `createHCCLCommSub(..., isOrigin=true)` 从缓存的全局域派生子域，成功即返回并 LOGW「内部实验特性、与 resume 模式不兼容」（:2953-2962）；再对 DEFAULT 型读 `TORCH_HCCL_RANKS_PER_ROOT`，大于 0 且 A2/A3 SoC 且 `numRanks>ranksPerRoot` 时用向上取整的根数走 `createHCCLCommScalable`（:2965-2981）；最后才是 rank 0（或单 P2P 的 p2pRank 0）`hcclGetRootInfo` + `broadcastMasterID` + 每设备 `HCCLComm::create_config`（DEFAULT 校验 commConfig 或用 `createHcclCommConfigWithOptions` 造默认配置；P2P 固定 numRanks=2、rank=p2pRank，注释明确 P2P 不设 hcclCommName，:2983-3037）。发布版 Origin（:2574-2635）没有子域派生与 Scalable 两个分支，直接 RootInfo。

## 子域派生与 P2P 域命名

`createHCCLCommSub`（主线 :3095-3213）从 `global_`（首个全局 ProcessGroupHCCL，构造时登记）取全局域：非 Origin 路径 `getHcclCommByDevices`（必要时新建），Origin 路径只查缓存 `getHcclCommByDevicesFromCache`，拿不到都返回 false 回退。子域 id 是 `hash(group_id)`（P2P 用 `hash(devicesKey)`）。P2P 子域命名 `group{group_id}_p2p_{lowRank}_{highRank}`：只在调用方已设 hcclCommName 时覆写该字段，hcclUdi 仅在非 Origin 且已设时覆写（:3164-3183）——即从 Options/Python 传入的 commName/Udi 在 P2P 派生域上会被框架重命名，自定义名不保留。`createSubHcclComm` 以全局域 + ranks 数组 + 子域 id 创建，返回 null 即回退。P2P_HCCL_BUFFSIZE 只在 commConfig==nullptr 时经 `config.hcclBufferSize` 进入子域（:3140-3147）。

## RootInfo 广播与版本一致性告警

`broadcastMasterID`（主线 :2387-2453；发布版 :2270-2330 同构）：普通域用递增 `hcclCommCounter_` 作 store key，单 P2P 域直接用 devicesKey；rank 0 `store_->set` RootInfo 字节串，非 0 rank `store_->get` 失败时报「可能是 rank 0 应用崩溃或网络问题」。额外写/读 `version_key`：内容为 `PYTORCH_NPU_VERSION` 宏串 + `__DATE__`，非 0 rank 比对不一致时 TORCH_NPU_WARN「PTA version mismatch」——混版本组网的分布式作业会得到该告警而非报错。所有 key 同时登记进 `TCPStoreKeyList_`；`_delete_tcpstore_key`（Init.cpp :379 绑定）删除 key "0" 与全部已登记 key，容忍并发删除异常（:1541-1560）。

## 通信流 id 的三个入口

`getCollStreamId(device)`（主线 :3357-3367）按设备键从 `hcclStreams_` 取，未命中时从流池新建：高优先条件是 `options_->is_high_priority_stream` 或 cvar `TORCH_HCCL_HIGH_PRIORITY`（`c10d::getCvarBool`）。`getP2PStreamId(device, peer, is_batched)`（:3369-3388）batched=1 用设备键、否则用 `getKeySendRecv(rank_, peer)`，未命中返回 -1 并以 INFO 级打印全部现存键与目标键——负值是诊断信号不是错误。`getStreamId(p2p, peer)`（:3336-3355）按当前设备取键，仅当 rootinfo-config 符号存在且 `P2P_HCCL_BUFFSIZE != 0` 时 P2P 才切到 sendrecv 键；三者在 Init.cpp :392-401 暴露为 `get_coll_stream_id/get_p2p_stream_id/_get_stream_id`。发布版有 `getP2PStreamId`（:2919-2940）与 `getStreamId`（:2897-2917），无 `getCollStreamId`。

## 合并收集：groupStart/End 与延迟 P2P 私有格式回拷

`startCoalescing`（主线 :6845-6857）重置合并状态并把设备推断为 `groupRanks()[getRank()]` 对应设备——子进程组也能正确取设备——随后 `groupStart()`。`endCoalescing(optype)`（:6859-6929）无实际收集时只 groupEnd 并复位；有收集则以同一个 comm/device 建 Work，记录 desync 起始事件后 `groupEnd()` 提交整组 HCCL 算子，再补做延迟的 P2P 私有格式回拷：合并模式下 recv 跳过收尾回调，框架把「用户私有格式张量 ↔ 基础格式缓冲」对暂存进 `coalescedP2PFormatCasts_`（recv :7436-7443），在 groupEnd 之后按通信流顺序 `recordStream` + `copy_` 回写（:6899-6908）。流捕获状态下不 enqueue Work（:6877-6879）；future 以空张量列表立即完成。`_group_start/_group_end` 亦单独暴露给 Python（Init.cpp :460-461）。`getSequenceNumberForGroup` 只返回内部 `seq_`，`setSequenceNumberForGroup` 为空实现（:1384-1388）——不能把它当 c10d 调试序列号语义使用。两版均有该组函数（发布版 :6038-6137、:1204-1207）。

## Work 超时的主线独有行为与发布差异

主线 `assignTimeoutToWork`（:3538-3549）在三个集合通信入口把 `options_->timeout` 加上活跃的 ephemeral 增量写入 Work 的 `opTimeout_`，并用 `ephemeralTimeoutActive_/ephemeralTimeoutInflight_` 记账增量归属；`_add_ephemeral_timeout`（Init.cpp :456-459 绑定，:2099-2103 实现）累加临时超时；`_set_default_timeout` 绑定 `setTimeout` 只改 options 不改已入队 Work。发布版没有 assignTimeoutToWork/addEphemeralTimeout/`mem_allocator` 属性与 getCollStreamId；`_window_register_and_exchange`/`_get_window_mem` 两版都有。

## 暴露给 Python 的 NPU 扩展入口

Init.cpp :363-466 的 ProcessGroupHCCL 绑定面（两版共有）：`get_hccl_comm`、`_set_hccl_comm_name`、`resume_hccl_comm`、`_set_switch_nic_comm`（hcclCommWorkingDevNicSet 存在性受检）、`abort_hccl_comm`、`_delete_tcpstore_key`、`set_watchdog_status`、`clear_workmeta_list`、`get_hccl_comm_name`（kwarg `init_comm`）、流 id 三入口与窗口两入口。abort 会销毁全部缓存通信域但**不**从缓存摘除，注释说明这是防止部分 rank 失败后其余 rank 重建域导致 hcclCommInitRank 挂死（:1390-1433）。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp)（primary）：主线行段 :1347-1381、:1384-1388、:1390-1433、:1541-1560、:2099-2103、:2387-2453、:2945-3213、:3272-3334、:3336-3388、:3533-3549、:6845-6941、:7436-7443。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp)（primary）：发布侧行段 :1204-1207、:2270-2330、:2574-2635、:2637-2700、:2832-2917、:2919-2940、:6038-6137；负向证据：全文件无 createHCCLCommSub/createHCCLCommScalable/assignTimeoutToWork/addEphemeralTimeout/getCollStreamId/registerMemPool/getMemAllocator。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.hpp)（implementation）：:782-789、:914-922。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/Init.cpp)（implementation）：:363-466。
