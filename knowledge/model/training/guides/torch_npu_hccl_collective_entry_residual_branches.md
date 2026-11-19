---
type: Guide
title: ProcessGroupHCCL 剩余承重分支：ReduceOp 映射、集合通信前后钩子、字节对齐与心跳监控线程
description: 8194 行文件行为/分支映射后仍未入卡的承重面：getHcclReduceOp 的 AVG/PREMUL/bool 映射，allreduce 族仅取首张量与 bool 预转型、PREMUL 预乘、A5 整数 AVG 截断除，byte_alignment 的 950 免填充，getHcclCommConfig 的 CANN 8.2 确定性掩码，heartbeatMonitor 线程的 DumpPipe/全局 dump 信号协议。
tags:
- task.implementation
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp
  role: primary
created_at: '2026-11-12T17:14:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# ProcessGroupHCCL 剩余承重分支：ReduceOp 映射、集合通信前后钩子、字节对齐与心跳监控线程

## 固定版本与分支映射口径

主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 `ProcessGroupHCCL.cpp`（8194 行）按 SCOPE-2 以行为/分支映射定案：已核对主题段（创建阶梯[创建卡](torch_npu_hccl_comm_creation_ladder.md)、Work 等待/内存[跨流内存复用卡](torch_npu_collective_memory_reuse.md)、看门狗/状态落盘/NSLB/resume/NIC[健康卡](torch_npu_hccl_comm_health_watchdog_and_nic.md)、多流三态[跨流内存复用卡](torch_npu_collective_memory_reuse.md)、窗口注册三节[缓冲卡](torch_npu_communication_buffers_and_zero_copy.md)、hccl_config 映射[Options 卡](torch_npu_hccl_pg_options.md)、零拷贝启用阶梯与 window 互斥[缓冲卡](torch_npu_communication_buffers_and_zero_copy.md)、checkHcclComms 异步错误对照与恢复摘除[健康卡 runLoop 节]）不在本卡重述。本卡只收映射中此前零覆盖的承重分支。全部静态阅读，未运行任何通信。

## ReduceOp 到 HCCL 的映射（getHcclReduceOp :186-218）

- **AVG**：HCCL 不支持 ReduceOp::AVG，映射为 `HCCL_REDUCE_SUM`，PTA 以"先求和后除"模拟（注释原义）——除法发生在 collective 模板的 PostProcess（见下节）。
- **PREMUL_SUM**：映射 `HCCL_REDUCE_SUM`，但输入 dtype 必须 half/float/bfloat16/double（TORCH_CHECK，PREMUL_SUM 对整数形态直接报 TYPE）。
- **SUM+bool**：映射 `HCCL_REDUCE_MAX`——bool 以 uint8 表示，sum 会溢出，max 与 sum 在布尔域同为按位或（注释原义）。
- unsupportedOp 集合报 NOT_SUPPORT、未知 op 报 NOT_FOUND；AllGather/Broadcast 不做额外类型检查（:220 注释）。

## 集合通信入口的前/后钩子族（collective 模板消费者）

以 allreduce（:5178-5262）为样本、reduce 族（allreduce_coalesced/reduce/_reduce_oop/_reduce_scatter_base_uneven 等）同构复制（PREMUL/AVG 分支在本文件共 21 处）：

- **仅首张量参与**：`tensors_cp = {tensors[0]}`——多张量列表只做合法性检查，实际通信只取第 0 个（与逐 API 文档的"张量列表"表述需区分）。
- **PreProcess**：输入 bool/byte 时先 `_npu_dtype_cast(tensors[0], kInt)` 转 int32 通信；`PREMUL_SUM` 读 `NCCLPreMulSumSupplement->double_factor` 逐张量 `mul_` 预乘。
- **PostProcess**：`AVG` 逐张量 `div_(getSize())`；**A5（SoC≥950）且整数 dtype 用 `div_(size, "trunc")` 截断除**（浮点与非 A5 走普通除）；若发生过 bool/byte 预转型，PostProcess 末尾 `copy_` 回原 dtype 并对临时张量 `recordStream(hcclStreams[0])`。
- **每算子固定骨架**：`check_npu_tensors_different_devices` → OpHook `PreHook`（CheckOpHookEnable）→ lambda 内 `getHcclDataType`+`checkSupportedDataType`+`RECORD_FUNCTION`+mstx `MstxRange(DOMAIN_COMMUNICATION)`+`is_core_control_enabled() → UseStreamResInCurrentThread`+`hcclXxx` 经 `OpCommand::RunOpApiV3` 下发后置 `*is_dispatched = true`。collective 模板主体（:4460-4678）的多流三态/NSLB/silenceCheck(L_TRAIN)/perf_dump realpath 检查/核数缓存/syncStreams/workEnqueue 分归既有卡；gather/scatter（:6948/:7104）是同骨架加 root-rank 校验与非 root 空占位；batch_isend_irecv（:5262-5376）组装 `HcclSendRecvItem{SEND/RECV/SEND_RECV_RESERVED}` 数组走 `HcclBatchSendRecv`；alltoall（:7878-8194）按 `CheckCompatibleImpl() && IsCompatibleSoc() && !IsA5Soc()` 在"collective 路线"与"default flatten+split_sizes 路线"间分派——A5 被排除出 alltoall 的兼容路线（`IsA2A3Soc`：910B1..310B1 前段 ∪ 9391..950 前段，:555-589）。
- **byte_alignment**（:5707-5731）：reshape 为 [1,numel] 后，SoC≥950 静态免填充；否则按 `ADDRESS_ALIGNMENT_BYTE` 用 `op_plugin::constant_pad_nd` 补齐到对齐字节，bool 先转 int 补完再转回。不均分族（:431-462 `fill_equal_split_sizes_when_empty`/`check_split_sizes`）为 `_reduce_scatter_base_uneven`/`_allgather_base_uneven` 提供等分补全与校验。

## 域配置基础与确定性掩码（getHcclCommConfig :347-375、getDeterministicState :328-344）

`getHcclCommConfig` 在 `HcclCommConfigInit` 上补两件事：buffer size 取 `GetHcclBufferSize()`（P2P 域取 `GetP2PBufferSize()`）；**CANN ≥ 8.2.RC1 时 `hcclDeterministic` 固定写 0xffffffff**（注释原义：临时规避 HCCL 内已知问题），旧 CANN 才走 `getDeterministicState()`——后者以 `HCCL_DETERMINISTIC` 环境变量（仅小写 "true" 判真）优先、否则全局 deterministicAlgorithms，进程内 static 一次缓存。无 `HCCL_COMM_CONFIG_COMM_NAME` 能力时把 config 首部 `size_t` 强写 32——注释原义：兼容旧版 HCCL 的尺寸检查，保留 N±2 版本字段。域级 hccl_config 的逐键映射与类型校验归 [Options 卡](torch_npu_hccl_pg_options.md)；本卡补齐的本地常量：hccl_algo 截断 1600、hccl_retry_enable 50、hccl_retry_params 128、hccl_buffer_name 128、group_name 截断到 `UDI_MAX_LENGTH-1` 并 WARN、hcclExecTimeOut 负值 WARN_ONCE 且 uint32 超 INT32_MAX 报 TYPE、hcclSymWinMaxMemSizePerRank 接受 uint32→uint64 提升。

## 心跳监控线程（heartbeatMonitor :1740-1948）

Watchdog::run 在 `monitorThreadEnabled_` 时启动的独立线程（BUILD_LIBTORCH 跳过；env 面 TORCH_HCCL_ENABLE_MONITORING/HEARTBEAT_TIMEOUT_SEC 语义见 [watchdog 超时卡](torch_npu_hccl_watchdog_timeout.md)），线程体此前零覆盖：

- **DumpPipe 专属全局域**：仅 `global_ranks_in_group` 为空（默认全局 PG）时构造，按全局 rank 命名、容量 `hcclTraceBufferSize_`——避免同 rank 多 PG 重复 hammer TCPStore。轮询间隔在"开 dump 信号检查时取 `coordCheckIntervalMilSec_`、否则 `heartbeatTimeoutInSec_*1000`"间切换。
- **本地/全局 dump 信号**：`shouldDump_` 置位即 `dumpTraceAndResetStatus()`（消息带 lastEnqueued/lastCompleted seq）；全局信号经 `globalStore_->check({EXCEPTION_DUMP})`（间隔同时受 `kWatchdogThreadSleepMillis` 与 `coordCheckIntervalMilSec_` 门，`hasGlobalDumped` 一次性），命中后读 4 字节超时 rank id（尺寸校验 sizeof(int)），store 异常本身也触发 dump。
- **心跳卡死检测**：`heartbeat_`（runLoop 每轮对未完成 work 递增）在 `heartbeatTimeoutInSec_` 内无推进 → shouldDump_ + 终止消息（原文点名 `TORCH_HCCL_HEARTBEAT_TIMEOUT_SEC` 调大或 `TORCH_HCCL_ENABLE_MONITORING=0` 关闭两条出路）；dumpPipe 有请求时 `std::async` best-effort `dumpDebuggingInfo`，训练不中断。
- **退出协议**：`terminateProcessGroup_/collectiveDebugInfoMode_/shouldDump_` 任一为真且监控线程未被通知终止时，先再睡一个 `heartbeatTimeoutInSec_`（为 desync 报告/析构留时窗）；仍未终止则 `monitorThreadEnabled_` 时 `terminateProcess(finalExitMsg)` 杀进程，否则只记 "PGHCCL Monitor Thread is disabled, but would have killed this job"。

## 映射定案与边界

- **covered 指卡**（不重述）：checkHcclComms 的首报去重/SHOULD_TEAR_DOWN 拉倒/恢复摘除 → [健康卡](torch_npu_hccl_comm_health_watchdog_and_nic.md)；windowRegisterAndExchange 与零拷贝互斥 → [缓冲卡](torch_npu_communication_buffers_and_zero_copy.md)；createHcclCommConfigWithOptions 主体 → [Options 卡](torch_npu_hccl_pg_options.md)；allgatherScalableRootInfos（:2457-2529）的 per-root store key `<counter>_scalable_root_<root>`、root0 发布 PTA 版本、multiGet 失败报 "Verify that every root rank is running"、逐项 HCCL_ROOT_INFO_BYTES 尺寸校验与 "PTA version mismatch" WARN——与 [创建卡](torch_npu_hccl_comm_creation_ladder.md) 的 Origin 版本一致性告卫同机制，补在 scalable 多根面；recordDataVol/recordComm 的 NSLB 落盘（`<nslb_path>/<master>_<comm>_<rank>.log` 追加 `HCCL_ALGO` 头）→ 健康卡 NSLB 节。
- **wrapper 族定案**：broadcast/allgather 系/reduce_scatter 系/send/recv/alltoall_base/_alltoallvc 等入口为 collective/pointToPoint 模板 + 上述钩子族的逐算子实例（各仅 hccl 原语与张量整理不同），不逐个承载；pointToPoint 的 `isSendRecvSelf` rank 重编号归 [健康卡 NIC 节]。getMstxHcclMsg（:4171-4226，mstx 消息串拼）、getPtaBuildVersion（:125）、syncStreams/physical_numel/getKeyFrom* 等纯辅助按行锚定案，无独立承重行为。
- **静态口径**：未运行任何通信；A5 截断除、0xffffffff 掩码、`(inf, "")`、EXCEPTION_DUMP 协议均按字面控制流读出。发布版本 对应面未逐一比对（本文主线行为不外推发布版）。
