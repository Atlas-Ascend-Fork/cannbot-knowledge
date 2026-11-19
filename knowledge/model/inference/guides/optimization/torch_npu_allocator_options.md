---
type: Guide
title: TorchNPU 推理显存配置：扩展段、碎片与版本门槛
description: 根据碎片和 Host 下发信号选择 PYTORCH_NPU_ALLOC_CONF，记录 expandable_segments 的冲突和较新选项的产品/PyTorch
  版本门槛。
tags:
- task.optimization
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/virtual_memory.md
  role: supporting
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_ALLOC_CONF.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUAllocatorConfig.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/PYTORCH_ALLOC_CONF.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/pytorch_comparison.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/pytorch_comparison.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/memory_management/virtual_memory.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/mapping_between_virtual_addresses_and_physical_memory.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/mapping_between_virtual_addresses_and_physical_memory.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp
  role: implementation
created_at: '2026-11-08T11:58:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# 推理缓存分配器的条件化配置

## 先明确问题

记录实际 Tensor 使用、分配器保留、非活动切分块和峰值，区分容量不足、碎片与 Host 管理开销。对同一输入和并发只改一个选项；设置发生在进程初始化前，并保存完整环境。

## 选择与限制

expandable_segments 默认 False，适合反复申请相近但变化大小的内存。开启要求配套 HDK 至少 23.0.0；max_split_size_mb 或 garbage_collection_threshold 任一为非默认值时，必须关闭 expandable_segments。max_split_size_mb 面向大量非活动切分块导致的 OOM，不能作为所有 OOM 的统一修复。

扩展段通过保留虚拟地址、按需映射物理内存减少碎片，并不增加设备物理容量。固定主线文档给出 torch.npu.memory._set_allocator_settings("expandable_segments:True")，并写明 PyTorch≥2.6.0、仅支持修改 expandable_segments；这条文档描述不能概括同一固定主线源码的全部白名单。发布 f3ecfe4a7ef7395754da7ca2e35661a7132b519b 的 setAllocatorSettings 实现只允许 expandable_segments；主线 ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf 实现允许 expandable_segments、max_split_size_mb、max_non_split_rounding_mb、release_lock_on_npumalloc、throw_on_npumalloc_oom、per_process_memory_fraction、pinned_max_round_threshold_mb、pinned_max_cached_size_mb 共8项。两者都先排空Host任务队列，不等同于环境变量全部选项都可动态修改，也不据此承诺设备同步或配置收益。解析状态、错误顺序和版本区别见[原生配置解析器](torch_npu/torch_npu_native_allocator_config_parsing_and_runtime_allowlists.md)。自定义分配器和跨进程 IPC 的配套另见[交付与共享边界](torch_npu/torch_npu_custom_allocator_and_ipc.md)。

multi_stream_lazy_reclaim 延迟 Event 查询，主要针对多流 Host 下发瓶颈；它不改变释放条件或内存峰值。固定来源要求 TorchNPU 7.3.0 以上版本；单流、少流或非 Host 瓶颈时收益有限。

page_size=1g 要求 Ascend HDK 至少 25.0.RC1、CANN 商用至少 8.1.RC1，且须核对来源列出的产品支持范围。本卡的 A2/A3 范围不代替其他型号的逐项核对。该选项作用于大块内存池：大于 1MB 的申请采用 1GB 粒度，小于等于 1MB 时不生效。来源明确与其他特性同时配置时仅 page_size 生效，不能假定其他分配器选项仍叠加生效。

## 主线选项的版本门槛

| 选项 | 来源明确的门槛 |
| --- | --- |
| pinned_use_background_threads | TorchNPU 26.0.0 且 PyTorch 至少 2.8.0 |
| large_segment_size_mb | TorchNPU 至少 26.1.0 且 PyTorch 至少 2.11.0 |
| per_process_memory_fraction 环境配置项 | TorchNPU 至少 26.1.0 且 PyTorch 至少 2.10.0 |
| throw_on_npumalloc_oom | TorchNPU 至少 26.2.0 且 PyTorch 至少 2.13.0 |
| PYTORCH_ALLOC_CONF 别名 | TorchNPU 至少 26.2.0 且 PyTorch 至少 2.10.0 |

支持别名的版本同时设置 PYTORCH_ALLOC_CONF 和 PYTORCH_NPU_ALLOC_CONF 会报错。主线声明的较新选项不能套用到 26.0.0／PyTorch 2.8 发布组合；具体开关还需核对运行包实现。

## 验证与回退

记录同负载下 OOM、内存统计、峰值、Host 时间和精度。未改善或引入波动时恢复原环境并重启进程；empty_cache 不是清理活跃 Tensor 或 HCCL 内存的方法。本卡基于固定主线说明，未进行显存或性能测试。

## 版本入口

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)：来源快照、部署配套和实际运行验证分别核对。

## 对齐、舍入与段大小的具体约束

|选项|范围、默认与组合规则|
|--|--|
|max_split_size_mb|默认无限大，非默认值必须大于20MB；大于阈值的块不再切分，针对非活动切分块导致的碎片评估。|
|garbage_collection_threshold|默认不开启，范围 (0,1)，超过容量比例后优先回收长期未复用块，需结合进程显存因子。|
|base_addr_aligned_kb|默认16，整数0..16，仅 expandable_segments=True 生效；≥2MB大块申请尽量按指定 KB 对齐基址。配置 0 表示跳过该额外重对齐——实现中没有主动的 512B 基址对齐步骤，申请尺寸仍按 512B 倍数向上舍入，不能据配置值断言返回地址一定具备或不具备 512B 对齐；对齐不等于增加可用显存。|
|segment_size_mb|旧虚拟内存段选项，默认20，整数20..512MB，仅扩展段大块池生效，已废弃；large_segment_size_mb 优先，page_size 又优先于两者。|
|large_segment_size_mb|默认20，整数>10MB；虚拟内存中控制物理申请粒度，非虚拟内存中控制1..10MB请求的段大小。与 max_split_size_mb 同配时，后者须≥该值。|
|roundup_power2_divisions|默认按512B向上对齐；可设置统一分段数，或按2的幂区间设置数组，目标是让相近大请求复用同类块，代价是额外舍入容量。|
|max_non_split_rounding_mb|默认20MB、正整数；新请求D大于max_split阈值时，候选空闲块A与D之差≤该值才可整块复用；请求不超过max_split阈值时该项不生效。|
|release_lock_on_npumalloc|默认False；True在底层分配时释放部分锁以减少Host竞争，但可能增加资源占用，与自定义显存管理需另核对。|

虚拟内存大块物理段默认20MB、小块默认2MB且不可配置。增大段或舍入粒度会减少申请/映射调用，也可能加剧内部浪费；不能只看接口调用数下降。multi_stream_lazy_reclaim=True 优先用空闲块，在 Event 数超过512或找不到可用块时再查询，仍需等待相关事件完成才释放。

开启扩展段的单进程多卡还取决于 TorchNPU6.0.RC3/HDK24.1.RC3 及以后配套；旧驱动不能套用新多卡能力。Host pinned memory、进程配额与预防拒绝另见[内存调试与OOM路径](torch_npu/torch_npu_memory_debug_and_rejection.md)和[pinned memory配置](torch_npu/torch_npu_pinned_memory_options.md)。

## 统一分配器入口与首次读取

固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的独立PYTORCH_ALLOC_CONF页将它定义为统一分配器配置入口；TorchNPU≥26.2.0且PyTorch≥2.10.0时优先使用，功能按NPU专属选项页核对。跨加速器使用同名入口不意味着所有CUDA/XPU选项和NPU可直接互换，NPU还有page_size、base_addr_aligned_kb等专属参数。

NPUAllocatorConfig::instance以call_once读取两个变量。两者只要同时存在就报错，即使其中一个是空字符串；不能靠将旧变量设为空来选择新变量，应从启动环境真正移除另一项。均未配置才保持默认；首次解析后再修改进程环境不重新走该读取路径，运行时有限设置接口仍按前文自己的版本/选项限制核对。

这只是统一入口与解析时机的补充，不把26.2新名称回推到26.0/PyTorch2.8发布组合；切换变量名也不改变每项显存配置的产品范围、冲突和数值验收条件。

## 大小边界与舍入区间的原文口径

两语言配置页的概述均写“小于1MB用小块池，反之大块池”，后面的page_size使用约束却写“申请大于1MB才生效，≤1MB不生效”。保留这处1MB边界表述差异：page_size验收按其明确的使用约束，不用概述替恰好1MB的请求承诺大页。未配置page_size时，该约束所述物理页粒度为2MB；虚拟大块段默认20MB是另一层次，不把页与段混为同一参数。

base_addr_aligned_kb=16在大块申请≥2MB时尽量保持16KB基址对齐；这不是所有小申请都保证同样对齐。roundup_power2_divisions的数组例子`[256:1,512:2,1024:4,>:8]`按<256MB、256..512MB、512MB..1GB及更大区间分别设置1/2/4/8个分段；只说明请求大小的舍入，不让不够大的空闲块变成可用块。max_non_split_rounding_mb的A−D条件同样只讨论足以满足请求的候选块，不能因负差值满足不等式而复用小于请求的块。

PyTorch对照页把PYTORCH_ALLOC_CONF列为同名入口，设备专属旧名字作为兼容入口；在TorchNPU中仍受两个变量互斥、NPU专属参数及各自版本限制约束，不据同名推定CUDA分配器所有选项可直接搬用。

## Evidence

- [docs/zh/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md)（primary）
- [虚拟地址与扩展段](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/virtual_memory.md)（supporting）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_ALLOC_CONF.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUAllocatorConfig.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/PYTORCH_ALLOC_CONF.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/pytorch_comparison.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/pytorch_comparison.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/memory_management/virtual_memory.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/mapping_between_virtual_addresses_and_physical_memory.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/mapping_between_virtual_addresses_and_physical_memory.png)（constraint）

- [运行时setter固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp)（implementation），完整函数范围 867–882。

- [运行时setter固定实现](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp)（implementation），完整函数范围 877–885。

- [分配器尺寸舍入与基址重对齐固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp)（implementation），读取范围 :102-105、:1435-1462、:2247-2257；行级对照见[原生配置解析器](torch_npu/torch_npu_native_allocator_config_parsing_and_runtime_allowlists.md)。
