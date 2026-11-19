---
type: Guide
title: TorchNPU HCCL 通信域健康层：ASD 静默检查、看门狗错误轮询、NIC 主备切换、resume 与 NSLB 记录
description: 从 ProcessGroupHCCL 两版源码记录 silenceCheck 触发门槛与缓存、Watchdog/checkHcclComms 异步错误处理模式、_set_switch_nic_comm 的 P2P rank 重编号、resume_hccl_comm 与 RESUME_MODE_ENABLE 的拷贝降级消费、NSLB 数据量与通信域记录及 waitForFutureOrTimeout 分支。
tags:
- task.debugging
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/Init.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/HcclCompile.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SilentCheckV2KernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.hpp
  role: implementation
created_at: '2026-11-12T14:26:35Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU HCCL 通信域健康层：ASD 静默检查、看门狗错误轮询、NIC 主备切换、resume 与 NSLB 记录

## 固定版本与范围

主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 与发布快照 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 的 `csrc/distributed/ProcessGroupHCCL.cpp`（8194/7132 行）。只读静态行段审阅：未创建进程组/通信域/流/事件，未运行 HCCL/ACLNN，未写任何状态或 NSLB 文件。相邻卡边界：域创建阶梯/流选择/coalescing 见 [通信域创建阶梯](torch_npu_hccl_comm_creation_ladder.md)；Work 等待与内存生命周期见 [跨流内存复用卡](torch_npu_collective_memory_reuse.md)，域级 `hccl_config` 见 [Options 卡](torch_npu_hccl_pg_options.md)，零拷贝与超时记账见 [通信缓冲卡](torch_npu_communication_buffers_and_zero_copy.md)，分布式故障定位的排查框架见 [集合通信故障卡](torch_npu_collective_failure_triage.md)。**与创建阶梯卡的分工**：[通信域创建阶梯](torch_npu_hccl_comm_creation_ladder.md)按「创建生命周期」成卡，已完整覆盖其主题；本卡的静默检查/看门狗/NIC/resume/状态与数据量记录是通信域建立后的健康运维面，属不同生命周期阶段，两卡互为邻接。

## ASD 静默数据检查（silenceCheck）

触发门槛（集合通信入口 :4515-4524，同构入口 :4751-4757/:5002-5008）：`model_state().get_model_mode() == L_TRAIN` 且 `GetSilenceCheckFlag() != CHECK_CLOSE`（`NPU_ASD_ENABLE`，OptionsManager.cpp :464-475）且 opType 既非 UNKNOWN 也非 BROADCAST（batch_isend_irecv 输入不校验、Broadcast 只需检测 src rank——注释原义）；对每个输入在对应 hcclStream 上执行。`silenceCheck`（主线 :4226-4262，发布 :3591-3621，两版逐字符等价）：非 float/bfloat16 直接返回；`requires_grad` 返回；非 SEND/RECV/UNKNOWN 的 opType 还要求 `get_call_state() == L_BACKWARD`（即只在反向窗口检查集合通信）；ALLREDUCE 且 `numel() <= 1` 返回（注释：Barrier 会调 allreduce，过滤无效调用）。通过过滤后按 opType 建 `{step: zeros(1, Long), cache: zeros(3, Float)}` 缓存（hpp :1356 的 `silenceCheckCache_`，进程级不淘汰），`at::norm(input)` 后调 `op_plugin::_npu_silent_check_v2(val, input, cache, step, min_steps=100.0 固定, GetSilenceUpperThresh().first/second, GetSilenceSigmaThresh().first/second, GetSilenceCheckFlag())`；阈值环境变量 `NPU_ASD_UPPER_THRESH`（默认 1e6/1e4）与 `NPU_ASD_SIGMA_THRESH`（默认 1e5/5e3）。委派体在 op-plugin 固定提交 d84e9b1d 的 `SilentCheckV2KernelNpuOpApi.cpp:28-60`：`DO_COMPATIBILITY(aclnnSilentCheck, aclnnNotFound)` 缺符号直接 TORCH_CHECK 失败；double 阈值统一降精度为 float 后 `EXEC_NPU_CMD(aclnnSilentCheck, ...)`，返回 Int 张量。

## 看门狗异步错误轮询

`Watchdog::runLoop`（主线 :2151 起）每 `kWatchdogThreadSleepMillis`（1000ms，:581）醒一次；`watchdogStatus == STOP` 时跳过检查；否则调 `checkHcclComms`（:2184）。`checkHcclComms`（主线 :2104-2149，发布 :1997-2040）：`asyncErrorHandling_ == NoHandling` 直退；持 `mutex_` 遍历 `devHCCLCommMap_` 每个 key，`checkForHCCLErrorsInternal`（:2375-2385）逐 comm `checkForHcclError()`，非 SUCCESS 即以 `c10_npu_get_error_message()` 造 runtime_error 异常指针。错误处理语义：首次出错的 key 进 `reportedErrorComms_`（去重）、写静态 `exceptionMessage_`、`C10_LOG_API_USAGE_ONCE("ProcessGroupHCCL.handleException")`；`SHOULD_TEAR_DOWN`（TearDown/SkipCleanUp 模式，hpp :210/:218）时 rethrow 把整个进程拉倒（日志原义 "To avoid data inconsistency, we are taking the entire process down"）；错误状态消失的 key 从 `reportedErrorComms_` 摘除并记「cleared/recovered」。错误模式四值 `NoHandling/TearDown/CleanUpOnly/SkipCleanUp`（hpp :210）。runLoop 同段还处理：状态保存开关（`TORCH_HCCL_STATUS_SAVE_ENABLE`/`_PATH` 默认 `/tmp`/`_INTERVAL` 默认 2 秒、<=0 重置并 WARN_ONCE，OptionsManager.cpp :354-380）下的目录准备与按间隔刷新，以及完成 Work 的 ephemeral 超时回冲（:2305-2331）与 `refreshStatusInfo(work, "start"/"end")`（:2591-2607，seq+status 相同则不刷新）。

## NIC 主备切换（_set_switch_nic_comm）

Python 入口 `Init.cpp:371-376`（`ranks`/`useBackup` 默认空列表）。`setSwitchNicComm`（主线 :4019-4049，发布 :3398-3424）：先 `hcclCommWorkingDevNicSetExist()` 符号存在性门（HcclCompile.h :530-534，static 缓存；缺失 LOGI "Skip it." 并返回 true，即旧 HCCL 上该调用是无害空操作）；再按 rankid 解析设备键，遍历该键全部通信域调 `setCommWorkingDevNic`。`setCommWorkingDevNic`（主线 :3960-4017）：P2P 型（`hcclCommType == 1`）把全局 rank 重编号为 P2P 域内 0/1——`p2pRank = rankid <= p2pPeer ? 0 : 1`，自环（`rank_ == p2pPeer`）时目标取 0，否则 `1 - p2pRank`；非 P2P 型在 `groupRanks()` 里查本地序号，查不到的 rank 静默丢弃；收集 `sendRanks/useBackup` 后调 `hcclCommWorkingDevNicSet(comm, ranks, useBackup, n)`（HcclCompile.h :537-547 懒加载 TORCH_NPU_GET_FUNC），失败仅 LOGI 并返回 false。逐字符对比：两版唯一差异是主线把 `ranks[i] == rankid` 写成 `ranks[i] == static_cast<uint32_t>(rankid)`（发布版无 cast），无行为差异。

## resume 与 RESUME_MODE_ENABLE

`resume_hccl_comm(device_id)`（Init.cpp :369 绑定；主线 :3924-3958，发布 :3302-3336，逐字符等价）：按设备键与 `p2pSendRecvKeys_[rank_]` 登记的全部 P2P 域，逐 comm 调 `HcclCommResumeFace`（HcclInterface.cpp :35-39，懒加载映射到 HCCL `HcclCommResume` 符号），`HCCL_CHECK_ERROR` 失败即抛。注意 `RESUME_MODE_ENABLE`（OptionsManager.cpp :90-96）不在本函数内读取：其真实消费点是拷贝内核的同步失败降级——`CopyKernelOpApi.cpp:93-99` 与 `CopyKernel.cpp:153-158` 在 `aclrtSynchronizeStream`（后者为带超时变体）失败且 resume 模式开启时降级为 `TORCH_NPU_WARN`（"But in checkpoint-resume mode will not throw exceptions."），否则 `AT_ERROR`。`ROOTINFO_SUBCOMM` 派生子域与 resume 模式不兼容的告警已由[通信域创建阶梯](torch_npu_hccl_comm_creation_ladder.md)记录，本卡不重复。

## NSLB 数据量与通信域记录

门槛（:4526-4542，发布版同构）：`nslb_path`（`NSLB_CP` 环境变量，OptionsManager.cpp :348-350）非空且未到终点时，`op_id_ <= GetNslbCntVal()` 的前 N 个集合操作逐个 `recordDataVol`；`op_id_ >= nslb_num` 时置 `nslb_is_end` 并 `nslb_record_end`（:3762-3780：写 `<nslb_path>/end_<MASTER_ADDR>_<pid>.log` 标记文件，目录缺失则 mkdir）。`recordDataVol`（主线 :2547-2583，发布 :2340-2374）：文件名 `<MASTER_ADDR>_<commName>_<rank>.log`（`MASTER_ADDR` 缺失即 TORCH_CHECK 失败），目录不存在则 mkdir、文件不存在则建（0600 组 0640 权限），追加行 `op dataVol rank`（op 转小写），首行按需写 `HCCL_ALGO=`（仅当设置了该环境变量且文件首次创建）。`recordComm`（主线 :2731-2768，发布 :2467-2499）：向 perfdump 文件追加 `[COMM]:<commName>,<op>,<group_ranks>` 行，进程内 `commset` 按 (commName, op) 去重——同一通信域同一 op 只记一次。两版唯一实质差异是 `recordDataVol` 的错误文案（主线 "Failed to prepare HCCL status save directory. Please verify the path is accessible and writable." vs 发布 "Open shared directory failed. Please check whether input path is valid."）。

## waitForFutureOrTimeout

主线 :1435-1465（发布 :1254-1300，逐字符等价）：`fut.valid()` 前置；`wait_for` ready 时 `get()` 只留成功/异常日志（不重抛，除非 throwException 分支），超时时组 "Future for {desc} timed out after {N} ms"；`throwException` 为真且有错误消息才抛 `DistBackendError`。调用点 :1718（shutdown 路径，见 Work 卡主题）。

## 失效边界与静态口径

- 两版等价性按 `tr -d ' \t\n'` 逐字符比对得出：silenceCheck/setSwitchNicComm/resumeHcclComm/checkHcclComms/checkForHCCLErrorsInternal/recordComm/waitForFutureOrTimeout 全等价；setCommWorkingDevNic 差一个 uint32 cast、recordDataVol 差错误文案，均已在正文标注。
- `checkForHCCLErrorsInternal` 对 `hcclComm->checkForHcclError()` 的语义依赖 HCCL 侧实现，本卡只记录调用面；`HcclCommResume`/`hcclCommWorkingDevNicSet` 同理。
- NSLB/perfdump/状态保存的文件产物未实际生成；`StatusInfo`/`recordHcclStatus` 的落盘细节（:2609-2700 一带）只在 watchdog 触达范围内引用，未逐行成卡，不在本卡断言范围。
- `NPU_ASD_ENABLE` 的完整模式枚举（PRINT_WARN_LOG 之后的分支）与 `_npu_silent_check_v2` 的语义阈值含义属 op-plugin/ASD 侧知识，本卡只锚定 ProcessGroupHCCL 的调用面与参数来源。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp)（primary）：:581、:1435-1465、:2104-2149、:2151-2200、:2305-2340、:2375-2385、:2547-2583、:2591-2616、:2731-2768、:3762-3780、:3924-3958、:3960-4017、:4019-4049、:4226-4262、:4515-4545。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/ProcessGroupHCCL.cpp)（primary）：:1254-1300、:1997-2040、:2340-2374、:2467-2499、:3302-3336、:3338-3396、:3398-3424、:3591-3621；行段等价性按 sha256 → 去空白 → 全空白折叠 token → 注释剥离 token 逐级比对口径核对。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp)（implementation）：:90-96（RESUME_MODE_ENABLE）、:348-350（NSLB_CP）、:354-380（状态保存三参）、:464-475（NPU_ASD_ENABLE）、:528-545（两阈值）。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/Init.cpp)（implementation）：:369-376（绑定面；绑定名单已在阶梯卡整体记录，此处只取三个入口）。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/HcclCompile.h)（implementation）：:530-547（符号存在性与懒加载）；`HcclInterface.cpp:35-39`（HcclCommResumeFace→HcclCommResume）。
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SilentCheckV2KernelNpuOpApi.cpp)（implementation）：:23-60 全文（DO_COMPATIBILITY 门与 EXEC_NPU_CMD 委派）。

## Watchdog::runLoop 全分支（主线 :2151-2364）

进入 while 前：`needSetDevice=true`、`lastrecordtime/timenow` 基准、`recordflag=false`（`completedWorkList` 声明后未在本段使用）。每轮循环四段：

1. 状态保存开关 `CheckStatusSaveEnable()` 为真时：`checkAndMakePath(GetStatusSavePath(), …)`（:463-541：目录不存在则 `create_directories` 并逐步校验 W_OK，各步失败仅 LOGW/stdout 不抛）预建目录；`timenow-lastrecordtime > GetStatusSaveInterval()*1000ms` 决定当前周期是否落盘（`recordflag`，:2166-2171）。
2. 持 `workMetaListMutex_`，`workMetaListCV_.wait_for(kWatchdogThreadSleepMillis=1000ms, terminateProcessGroup_)`；醒来后 `watchdogStatus == STOP` 直接 continue；否则 `checkHcclComms()`（上节）。
3. 遍历 `workMetaList_`，对每个 work 依序：首 work 时 `needSetDevice` 一次性置 `SetThreadAffinity(device)`+`SetDevice` 并把静态 `ProcessGroupHCCL::deviceId_` 固定为该 work 首设备（此后整个 runLoop 不再改）；该步异常经 `get_device_error()`（:724-742，七种子串匹配：UCE ERROR/HBM MULTI BIT ECC ERROR/SUSPECT MEM ERROR/HCCS LINK ERROR/UB LINK ERROR/HCCL OP RETRY FAILED/SUSPECT REMOTE ERROR）提取设备错误写入全局 `device_error_msg`（:150-151），不含 "FORCE STOP" 的异常置全局 `force_stop_error_flag=true`。随后 `checkAndSetException()`（未终止时）、`checkDispatch()`（:999-1019：未派发时长超过 `GetDispatchTimeout()`（:978-992，默认 600s；HCCL_EXEC_TIMEOUT 在 (150,630) 区间时减 30s 收紧，越界仍用默认）仅告警一次并置 is_reported；派发成功清位）、`checkExec()`（:1021-1041：exec 超时线 = `GetHCCLExecTimeout()`（<=0 时取默认 1836s，:86）-60 且不低于 60s；超时置 `is_dumped` 一次性返回 true）。
4. `dumpOnException_ && exec_timeout`：把 rank 序列化写 `globalStore_` 的 EXCEPTION_DUMP 键、首次置静态 `shouldDump_`（该分支无 sleep）；`timedOut = work.checkTimeout()`（:951-975：超过 opTimeout_ 生成 "Watchdog caught collective operation timeout" runtime_error 并 setException，已有异常不覆盖）。`work.exception()` 时：dumpOnException_ 分支写同一 dump 键后 `sleep_for(heartbeatTimeoutInSec_)`；`desyncDebug_ && timedOut` 时 `retrieveDesyncReport(store_, "HCCL", rank, size)` 打印失步报告（取失败仅记 ERROR，主线的键名文案是 TORCH_HCCL_DESYNC_DEBUG）；最后 `work.handleException(asyncErrorHandling_)`。desyncDebug_ 下另有 `logWorkStart/logWorkEnd`；`monitorThreadEnabled_` 时把更大 seq 的已启动 work 写入 `pgStatus_->lastStartedSeq/WorkName/NumelIn/NumelOut`。
5. 完成清理（`isCompleted()`）：dispatched 且 is_reported 的补派发成功告警并清位；`stashed_for_allocator_safety_` 非空则整组持 `shelvesMutex_` push 进 `shelvesToUnstash_`；持 `mtxTimeoutExtension_` 归还 `ownedEphermeralTimeout_`（主线特有记账，见 [跨流内存复用卡](torch_npu_collective_memory_reuse.md) 的超时延长语义，发布无此段）；状态保存开启且无异常时 `refreshStatusInfo(work,"end")`；更新 `pgStatus_->lastCompleted*` 四字段；`HCCLTraceBuffer::get()->retire_id(trace_id_, true)`；从列表 erase。未完成分支：状态保存开启且已启动时 `refreshStatusInfo(work,"start")`；逐 work `heartbeat_++`。
6. 锁外收尾：状态保存开启且 `is_refreshed` 时 `updateStatusOutput()`（:2610-2616：持 StatusMapmutex_ 把单条 StatusInfo 写入 `StatusOutput_[options_->group_id]` 并清 is_refreshed，pgId 空则不写）；`recordflag && recordHcclStatus(GetStatusSavePath())` 成功才把 lastrecordtime 重置为当前时刻。

线程外壳 `Watchdog::run`（:1972-2006）：`SetThreadType(WATCHDOG_THREAD)`；`monitorThreadEnabled_` 时启动 `heartbeatMonitor` 线程（BUILD_LIBTORCH 编译下跳过）；runLoop 正常返回记 info 日志；异常路径——std::exception 且静态 `exceptionMessage_` 为空时填 `e.what()`，`recordHcclStatus(path, end=true, error=true)`（全文件唯一 error=true 调用点，通信子群也落盘）；未知异常仅 `recordHcclStatus(path, true)`；两路径都构造 `watchDogException_` 后 `std::rethrow_exception` 把看门狗线程拉倒。runLoop 出 while 后的终止尾（:2344-2364）：再 `recordHcclStatus(path)` 一次；`terminateProcessGroup_` 为真时 `recordHcclStatus(path, end=true)` 并清空 workMetaList_。

`refreshStatusInfo`（:2591-2608，发布 :2376-2394 去空白同构）：seq 与 status 均与当前 StatusInfo 相同才返回 false 不刷新；否则填 seq、pgId（options_->group_id）、opType、commIds（global_ranks_in_group 逐 rank 空格拼接，空表写 "all"）与 status。StatusStruct 字段即上述五项（hpp :1164-1171；StatusOutput_ 为 pgId→StatusStruct 静态 map，hpp :1178/:1180）。

## recordHcclStatus 落盘细节（主线 :2618-2729 vs 发布 :2405-2465）

共同骨架：通信子群（global_ranks_in_group 非空）且非 error 提前 return true 不落盘——例行落盘只属全局组，子群仅在 error=true 时落；`StatusOutput_` 为空返回 false（主线 :2630-2633 附 LOGI）。文件名 `torch_hccl_status-<global_rank>_<master_addr>_<deviceId_>_<numRanks_>_<pid>_<毫秒时间戳>.log`：global_rank 子群取 `global_ranks_in_group[rank_]`，否则 rank_；MASTER_ADDR 缺失回退 "127.0.0.1" 并 WARN；firstrecordtime/endrecordtime 是函数级 static（首次/终止各冻结一次）——同一进程多次落盘共享首时间戳，end 版另记终止时刻。`is_master = (global_rank==0)`。JSON：last_comm_op 数组（每个已登记 pg 一条 seq/op_type/pg_id/comm_ids/status）、is_master、exceptionMessage_（静态全局，checkHcclComms 首错写入）、global_pg_end_time。

主线独有：整函数 try/catch（std::exception 与 `…` 均 LOGW+stdout+return false）；持 StatusMapmutex_ 先把 `StatusOutput_` 拷进局部 `statusSnapshot` 再序列化（注释原义：防其他通信线程并发写 map 重分配造成脏读）；写 `<目标>.tmp` 再 `std::rename`，写失败或改名失败都 WARN+stdout、删 tmp、return false——落盘原子性由 tmp+rename 提供。发布版直接以 trunc 打开目标文件、无 try/catch、无写失败检查、持同一把锁直接读 StatusOutput_ 不做快照；发布 checkAndMakePath 错误文案 "Open shared directory failed. Please check whether input path is valid."（主线 "Failed to prepare HCCL status save directory. Please verify the path is accessible and writable."，与 recordDataVol 同款两版文案差异）。两版 JSON 字段、文件名模式、子群跳过规则一致（去空白比对）。

## runLoop 两版实质差异

发布 runLoop（:2042-2243）与主线骨架一致，实质差异四点：(1) 发布在完成清理 erase 后调用 `c10_npu::NPUGraph::dec_pending_event_queries()`（:2207；同文件 :4004/:4220/:4477 另三处），把 NPUGraph 待查事件计数与 work 完成联动；主线 csrc 全树 `pending_event_quer*` 零命中——该机制只在发布树存在。(2) 主线完成清理含 ephemeral timeout 归还块，发布无。(3) 失步报告失败文案发布为 HCCL_DESYNC_DEBUG、主线为 TORCH_HCCL_DESYNC_DEBUG。(4) 发布在循环头缓存 `status_save_enable/status_save_path` 局部量复用，主线循环体内逐次调 OptionsManager（选项本身 static 缓存，语义等价）。状态保存三参解析（OptionsManager.cpp :352-380）已由 [HCCL 状态采证卡](torch_npu_hccl_status_capture.md) 持文档面（含文件名成分承诺），本两节为其补实现面，不重述文档声明。
