---
type: Guide
title: mspti 活动 Profiler 会话与 trace 元数据清洗补丁：libkineto 注册、采集排空与控制字符防护
description: 记录主线独有的 libkineto IActivityProfiler 会话（PrivateUse1 注册、活动类型到 msptiKind 映射、缓冲采集、外部关联 flow 链接、停止排空）与 MsptiInterface 符号懒加载层、torch.profiler add_metadata 控制字符清洗 init patch 的完整行为。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/profiler/mspti_activity_profiler.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/profiler/mspti_activity_profiler.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/interface/MsptiInterface.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_add_metadata_sanitizer_patch.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/profiler_patches.py
  role: implementation
created_at: '2026-11-12T14:26:35Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# mspti 活动 Profiler 会话与 trace 元数据清洗补丁：libkineto 注册、采集排空与控制字符防护

## 固定版本与范围

主线 pin（ac0e1564）独有：发布 pin（f3ecfe4a）全树 rg 无 `mspti_activity_profiler`/`MsptiActivityProfiler`/`_add_metadata_sanitizer_patch`，`mspti` 字样仅命中 `csrc/profiler/mstx_mgr.cpp:243` 的 `libmspti.so` 库名字符串。Python/文档面另见 [kineto profile API 卡](../../../apis/torch_npu/profiler_kineto_profile.md)与 [子线程卡](torch_npu_profiler_child_threads.md)；`_inductor` 侧 `mspti_batch_benchmark` 不在本卡范围。本卡覆盖 C++ 会话层五文件（mspti_activity_profiler.cpp 463 行全文、mspti_activity_profiler.h 82 行全文、MsptiInterface.cpp 231 行全文、_add_metadata_sanitizer_patch.py 156 行全文、profiler_patches.py 登记段）。纯静态阅读：未运行任何 profiler 会话，未加载 libmspti.so，未写 trace；draft、platforms 为空。

## libkineto 注册面与会话门槛

`MsptiActivityProfilerPoc`（.h :59-79）是 `libkineto::IActivityProfiler`：`name_` 为 `"mspti"`，但 `availableActivities()` 只声明 `CONCURRENT_KERNEL` 一个成员（:78）。注册首选上游宏 `REGISTER_PRIVATEUSE1_PROFILER`（写入 PrivateUse1ProfilerRegistry，.cpp :448-449），宏不存在时回退静态初始化 `libkineto::api().registerProfilerFactory`（:451-459）。两个 `configure` 重载（:429-444）都收敛到同一判定：请求类型集含 `CONCURRENT_KERNEL`/`GPU_MEMCPY`/`GPU_MEMSET`/`GPU_USER_ANNOTATION` 任一（`privateUse1Requested` :50-54）才返回会话对象，否则返回 nullptr——即 MEMCPY/MEMSET/ANNOTATION 类型即使不在 avail_ 声明里也能驱动会话，类型集以 configure 实参为准。`MsptiActivityProfiler` 会话持有该类型集并按 `computeEnabledKinds`（:56-72）映射 mspti kind：选 CONCURRENT_KERNEL 会同时启用 `MSPTI_ACTIVITY_KIND_KERNEL/COMMUNICATION/ACL_API/EXTERNAL_CORRELATION` 四种，MEMCPY/MEMSET 各自一一对应。

## start/stop 生命周期与排空

`start()`（:205-236）：先清 `g_events`/`g_externalByCorrelation`/`g_launchSites` 三个全局缓存；`IsSupportMsptiFunc()` 为假时把 `"libmspti.so not available - mspti session inactive"` 记入 `errors_` 并提前返回（状态不进入 RECORDING）。随后 `MsptiSubscribe` + `MsptiActivityRegisterCallbacks(bufferRequested, bufferCompleted)` + 逐 kind `MsptiActivityEnable`，任何一步失败都只追加进 `errors_`（`"msptiSubscribe failed"`/`"msptiActivityRegisterCallbacks failed"`/`"msptiActivityEnable failed for kind N"`）而不中止，最后置 `g_sessionActive`、重置 push/pop 计数、注册关联回调、`status_=RECORDING`。`stop()`（:238-301）先摘关联回调再排空（保证拆除期间没有新 push）；push/pop 计数不平衡时 LOGW。排空循环：`MsptiActivityFlushAll(1)` 后睡 25ms，事件数连续 3 次无增长即退出，安全上限 400 次迭代并 LOGW「drain hit the safety bound」；随后逐 kind Disable、Unsubscribe，再补一次 FlushAll 收尾，`status_=PROCESSING`。

## 缓冲采集与记录解码

`bufferRequested`（:74-86）按 `kBufferSize` 8 MiB（:28）`posix_memalign` 对齐分配，失败时清零三个出参让 mspti 侧感知不可用。`bufferCompleted`（:92-138）持锁循环 `MsptiActivityGetNextRecord`：KERNEL 记录的 name 取 `k->name`，空则回退 `k->type` 再回退 `"mspti_kernel"`，保存 device/stream/correlationId/kernelType；COMMUNICATION 记录映射为 `COLLECTIVE_COMM` 活动并带 commName；EXTERNAL_CORRELATION 只写入 `g_externalByCorrelation[correlationId]=externalId` 映射；其余 kind 静默丢弃。会话侧自增 id `g_corrCounter` 从 `1<<30` 起（:48，注释强调小于 2^32-1），与 mspti 原生 correlationId 分开存（`correlation` vs `msptiCorrelation`）。缓冲处理完 `free(buffer)`。

## 外部关联与 CPU→NPU flow 链接

`registerCorrelationCallback`（:145-194）注册全局 RecordFunction 回调（`needsIds(true)`、needsInputs/Outputs 均 false）：会话不活跃时直接返回 nullptr（不 push）；活跃时把 `fn.handle()` 以 `MSPTI_EXTERNAL_CORRELATION_KIND_CUSTOM0` push 进 mspti，并在 `g_launchSites[id]` 记录宿主时间戳/pid/tid（Utils::GetClockTime/GetPid/GetTid）。pop 侧校验栈顶值与上下文 id 一致，不一致仅 LOGW（注释：栈是每线程的，只可能是同 kind 被别处 push）。`processTraceImpl`（:319-396）导出时：事件的 `externalId` 为 0 且 `msptiCorrelation` 非零时查 `g_externalByCorrelation` 补全；得到 externalId 后设 `flow.id/flow.type=kLinkAsyncCpuGpu/flow.start=0`，并对每个 externalId 首次出现时额外发射一个 `PRIVATEUSE1_RUNTIME` 尾事件（device=pid、resource=tid、startTime==endTime、`flow.start=1`）——kineto 据此画出 CPU 发射点到 NPU 内核的箭头。捕获窗口过滤只在 `startTime>0 && endTime>startTime` 时生效，窗口外事件计入 dropped。KERNEL 事件附 `type`（带引号）与 `streamId` 元数据，COLLECTIVE_COMM 附 `commName` 与 `streamId`；结尾 LOGI 输出 emitted/linked/flows/dropped 四计数。

## 设备与资源车道

`getDeviceInfo`（:398-403）返回设备名 `"Ascend NPU"`，sort index 固定 `0x1000000`（注释：高于任何真实进程号，让 NPU 车道渲染在 CPU 车道下方）。`getResourceInfos`（:405-423）只从 CONCURRENT_KERNEL 事件收集 `(device, stream)` 去重对，资源名 `"NPU stream <id>"`——头文件注释说明设备内核必须有 (device, stream) 车道否则 kineto 导出时丢弃。`getTraceBuffer` 恒返回 nullptr（本会话不产生 CPU 追踪）。

## libmspti 符号懒加载层

`MsptiInterface.cpp` 用 FunctionLoader 注册 `libmspti` 库并登记 10 个符号（:18-28）。`IsSupportMsptiFuncImpl`（:30-41）只检查 `ASCEND_HOME_PATH/lib64/libmspti.so` 经 `Utils::RealPath` 后是否非空，结果 static 缓存。每个包装函数采用同一模式：static 函数指针 + `noFuncFlag`（查到与查不到都缓存，首次查不到 LOGW 一次后恒返回 false），仅 `MsptiActivityEnable/Disable/FlushAll/GetNextRecord/Push/Pop/Unsubscribe` 校验返回值 `MSPTI_SUCCESS`，`MsptiActivityIsEnabled` 透传 bool。`MsptiSubscribe`（:194-210）把回调参数传 nullptr——纯活动订阅，不注册回调函数。

## torch.profiler add_metadata 控制字符清洗

门槛与挂载：`_init/patches/profiler_patches.py:18-20` 以 `@PatchManager.register_patch("profiler")` 登记 `apply_metadata_sanitizer_patch`，import 时执行 `_apply_metadata_sanitizer_patch()`（patch 框架语义归 patch 管理已有卡，此处只钉本 patch）。动作（_add_metadata_sanitizer_patch.py :96-156）：取 `torch.profiler.profiler._KinetoProfile`，无该属性静默返回；`_npu_metadata_sanitized` 标记幂等；包装 `add_metadata`/`add_metadata_json` 两个方法——key 与 value 都先过 `_sanitize_value`（:30-52）：`"`→`'`、`\`→`/`、`\n\r\t\b\f`→空格、其余 `<0x20` 控制字符→空格，返回被改写描述列表；`_sanitize_json_value`（:55-83）对能 `json.loads` 的值逐字符串清洗后以 `ensure_ascii=False` 重序列化（不引入 `\uXXXX` 转义），不能解析的按普通字符串处理。被改写时发 `UserWarning`（`stacklevel=3`，说明改写比写坏整个 trace 代价小）。动机（docstring :99-118 原义）：torch 的 add_metadata 只转义引号不转义反斜杠（`C:\temp` 已是坏 JSON），libkineto 写盘又把反斜杠替换为正斜杠，使 `\"` 变 `/"` 提前终止 JSON 字符串、整个 trace 不可解析；writer 属 PyTorch 的 libkineto，不在本仓，只能在入口移除危险字符。

## 失效边界

- 两处静态口径声明：correlation 自增 id 空间从 2^30 起（余量约 3×2^30 后溢出 int32，超长会话行为未验证）；清洗 patch 只覆盖 `_KinetoProfile` 两个方法，绕过它们的其他 metadata 写入路径不受保护。
- avail_ 只声明 CONCURRENT_KERNEL 与 configure 实际接受的四类型是源码事实，不据此推导 kineto 侧对 MEMCPY/MEMSET 的能力协商细节。
- 未动态验证：8 MiB 缓冲、25ms×3 排空、400 次安全上限、flow 链接效果均来自固定提交行段，未运行 profiler。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/profiler/mspti_activity_profiler.cpp)（primary）：:28、:43-48、:50-72、:74-90、:92-138、:140-201、:205-236、:238-301、:303-317、:319-396、:398-427、:429-444、:446-460。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/profiler/mspti_activity_profiler.h)（implementation）：:19-32（MsptiEvent 结构）、:34-57（会话类）、:59-79（Poc 类与 avail_）。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/interface/MsptiInterface.cpp)（primary）：:11-28（符号登记）、:30-46（存在性检查）、:48-228（十包装函数与 noFuncFlag 模式、:194-210 MsptiSubscribe nullptr 回调）。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_add_metadata_sanitizer_patch.py)（primary）：:5-23（替换表与描述）、:26-52、:55-83、:86-93、:96-156（挂载与包装）。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_init/patches/profiler_patches.py)（implementation）：:18-20（patch 登记）。
- 发布 pin 负向证据：`f3ecfe4a` 全树 rg 上述符号零命中（`mspti` 仅 `csrc/profiler/mstx_mgr.cpp:243`）。
