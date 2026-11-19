---
type: Guide
title: TorchNPU 内存调试：禁用缓存、配额与预防式 OOM
description: 区分物理容量不足、进程配额和提前拒绝，说明计数器、自动快照缺失与关闭缓存的开销。
tags:
- task.debugging
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_NO_NPU_MEMORY_CACHING.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/TORCH_NPUGRAPH_GC.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/PYTORCH_NO_NPU_MEMORY_CACHING.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/TORCH_NPUGRAPH_GC.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUWorkspaceAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/register/OptionsManager.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_compiler/_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/graphs.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_compiler/_config.py
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/graphs.py
  role: implementation
created_at: '2026-11-09T06:08:21Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# TorchNPU 内存调试：禁用缓存、配额与预防式 OOM

## 固定版本与范围

依据 TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`，按这三份中英文环境页共同列出的A2/A3及950DT限定；不扩展950PR；逐项版本门槛独立核对，不回推至 26.0/PyTorch2.8 发布基线。本文仅静态审阅，没有 NPU 实验。

## 禁用缓存是定位手段

PYTORCH_NO_NPU_MEMORY_CACHING 默认未设或0复用内存，1在生命周期结束后直接归还驱动，默认使用aclrtMalloc/aclrtFree并关闭虚拟内存，频繁分配会显著变慢。它不增加物理容量，也不是所有OOM的修复。使用check_uce_in_memory时文档要求该变量**未配置**，不能只用语义相似的0替代其明确条件。

## 配额与提前拒绝

per_process_memory_fraction 默认1、范围[0,1]，初始化按设备总显存计算本进程额度，超限OOM；要求TorchNPU≥26.1/PyTorch≥2.10。多进程额度不自动协调其他组件独占内存，不能用各进程额度之和代替实测总使用。

throw_on_npumalloc_oom 默认False；True在底层申请前检查本进程已分配量+本次申请是否超过设备上限，超限直接抛OutOfMemoryError，跳过释放空闲块、Host-Device同步及重试。要求TorchNPU≥26.2/PyTorch≥2.13。

环境变量或set_per_process_memory_fraction设置的fraction<1时，该预防选项不生效。提前拒绝累加memory_stats的num_oom_rejections，可用reset_accumulated_memory_stats清零；**此路径不触发OOM_SNAPSHOT_ENABLE**，没有快照不能证明没有发生拒绝或OOM。

## 分清捕获时的 Python GC

TORCH_NPUGRAPH_GC 默认0，不主动触发Python GC；1在Capture中主动GC且增加捕获开销，不能当作Device缓存释放开关。只用0/1：其他值在PyTorch2.7.1之前回到0，2.7.1及以后回到1，依赖未定义取值会造成版本差异。

- [OOM快照和历史](torch_npu_oom_memory_snapshot.md)
- [计数器与保留显存口径](torch_npu_memory_counters.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_NO_NPU_MEMORY_CACHING.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/TORCH_NPUGRAPH_GC.md)（constraint）

- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/PYTORCH_NO_NPU_MEMORY_CACHING.md)（constraint）

- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md)（constraint）

- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/TORCH_NPUGRAPH_GC.md)（constraint）

## 禁用缓存的实现层

`OptionsManager::CheckForceUncached()`（主线 OptionsManager.cpp :674-683）以 static lambda 一次求值：`GetBoolTypeOption("PYTORCH_NO_NPU_MEMORY_CACHING")`（:213-217）先做 strtol 归一化——任意非零数值（如 2）都归 1，非数字或空串静默归 0（即保持复用）。随后查 `memoryCacheMode` 表（:58，{{0,"open"},{1,"close"}}）；因为输入只可能是 0/1，find 永远命中，`:678` 的 "PYTORCH_NO_NPU_MEMORY_CACHING should be 0 or 1." TORCH_CHECK **不可达**。文档「配置为 1 时关闭」在实现层是「任意非零数值都关闭、非数字等同未配置」。发布版同构（:583-592），唯一差异是把名单表搬进 `getMemoryCacheMode()` 头内联 helper（发布 OptionsManager.h :75-79）。

非缓存分配路径（主线 NPUCachingAllocator.cpp）：`DeviceCachingAllocator::allocate`（:4141-4143）仅当 `CheckForceUncached()` **且** `currentStreamCaptureStatus()==CaptureStatus::None` 才走非缓存——图捕获进行中无条件回落缓存路径；此时 deleter 换 `uncached_delete`（:3606-3611：NpuSysCtrl 初始化完成后先 `npuSynchronizeDevice(false)`（不做错误检查），再 `aclrtFree`），并以 `AclrtMallocAlign32(size+AddPadSize(), ACL_MEM_MALLOC_HUGE_FIRST)` 申请。`allocate_with_aligned`（:4172-4181）在此基础上再加 base_addr_aligned_kb 对齐量（该入口的对齐语义见 [分配器配置卡](torch_npu_native_allocator_config_parsing_and_runtime_allowlists.md) 的「PYTORCH_NPU_ALLOC_CONF 文档声明与实现对照」节）；`raw_deleter`（:4189-4193）按同一开关返回 deleter。`AddPadSize()`（:166-178）static 一次：Ascend950 且 CANN≥9.1.0 时为 0，否则 32 并 WARN_ONCE。workspace 分配器的非缓存路径（NPUWorkspaceAllocator.cpp :513-527）固定 +32 与 `ACL_MEM_MALLOC_HUGE_ONLY`，与主分配器的 HUGE_FIRST 不同——workspace 面已由 [workspace 流缓存卡](torch_npu_native_workspace_stream_cache_and_deleters.md) 持有，此处只对照申请策略。

图池与恢复交互（主线）：`releasePool`（:2435-2440）在图池引用归零且 `CheckForceUncached() && !is_capture_context()` 时 `npuSynchronizeDevice(true)` 后 `release_cached_blocks`。`_npu_setCheckpointPoolState`（Module.cpp :539-546）在 CheckForceUncached 为真时直接 TORCH_CHECK 失败（"checkpoint do not support enabling PYTORCH_NO_NPU_MEMORY_CACHING"）——checkpoint 恢复与非缓存模式在该入口互斥。`check_uce_in_memory`（Module.cpp :759-797）的 UCE 判级依赖 `checkUceInMemPool` 遍历缓存池块（NPUCachingAllocator.cpp :1134 起）并在临时内存分支调 `emptyCache(false)`：非缓存模式下分配不进池，文档「使用 check_uce_in_memory 时该变量必须未配置」在实现层对应池判级链失去判级对象；其值 1（非 PyTorch 内存）方向的因果未运行验证。

文档正文写「每次通过 aclrtMallocAlign32 或 aclrtMalloc 接口申请」，CAUTION 又写「默认使用 aclrtMalloc 和 aclrtFree」：所读两 pin 的全部非缓存申请点都经 `AclrtMallocAlign32`（主分配器 HUGE_FIRST、workspace HUGE_ONLY），未在这些文件读到裸 `aclrtMalloc` 调用；「关闭虚拟内存」的开关语句不在本卡核验范围，不外推。以上全部为静态阅读，未运行任何分配路径。

## TORCH_NPUGRAPH_GC 的两个实现锚

`torch_npu/_compiler/_config.py:5`：`force_npugraph_gc: bool = Config(env_name_default="TORCH_NPUGRAPH_GC", default=False)`，经 `torch.utils._config_module` 的 `install_config_module` 安装——env 读取依赖 PyTorch 的 config module 机制；**该文件两 pin 逐字节相同**（sha256 一致）。消费点在捕获 `__enter__`：主线 `torch_npu/npu/graphs.py:913-921` 顺序为 `torch.npu.synchronize()` → `if force_npugraph_gc: gc.collect()` → `torch.npu.empty_cache()` + `torch_npu.npu.host_empty_cache()`——Python GC 先于两段缓存清空，且仅发生在每次捕获进入时，不是常驻周期任务；发布同构（`graphs.py:518-521`）。上文「不能当作 Device 缓存释放开关」的实现层根据即此：开关只追加 gc.collect() 一步，empty_cache/host_empty_cache 与默认路径相同。
