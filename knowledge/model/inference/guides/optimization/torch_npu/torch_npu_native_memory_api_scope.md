---
type: Guide
title: 原生NPU内存API：MemPool线程、快照与产品范围
description: 区分内存池与全局分配器、Host和设备统计，保留快照参数接线及导出可能触发Profiler的副作用。
tags:
- task.implementation
- topic.memory
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-cuda.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-cuda.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-cuda-memory.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-cuda-memory.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-cuda-memory.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-cuda-memory.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-cuda-memory.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-cuda-memory.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-cuda-memory.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-accelerator.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-accelerator.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/memory.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/private_apis.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/private_apis.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_ALLOC_CONF.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/PYTORCH_ALLOC_CONF.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_NO_NPU_MEMORY_CACHING.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/PYTORCH_NO_NPU_MEMORY_CACHING.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/TORCH_NPUGRAPH_GC.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/TORCH_NPUGRAPH_GC.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/OOM_SNAPSHOT_ENABLE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/OOM_SNAPSHOT_ENABLE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/OOM_SNAPSHOT_PATH.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/OOM_SNAPSHOT_PATH.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/memory_resource_overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/memory_management/memory_resource_overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-Tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/Memory-management-API.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/Memory-management-API.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/Memory-management-API.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/memory.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp
  role: implementation
created_at: '2026-11-09T13:09:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生NPU内存API：MemPool线程、快照与产品范围

## 固定版本与范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 中PyTorch2.7.1、2.9至2.14的中英文原生支持页及所指实现；收录/缺项、类/方法与产品标记分别保留，不将文档版本差异直接视为实际发行历史。产品为各条目明列的A2/A3训练系列与950DT，不扩展950PR，也不推导主线与26.0/PyTorch2.8或其他主线已配套。支持表不替代完整参数、底层能力和设备验证，本卡未执行上游或NPU实验。

## MemPool的所有权与线程范围

CUDA页将memory.MemPool适配为torch.npu.memory.MemPool，并说明torch.npu.MemPool/torch_npu.npu.MemPool等价，列三类产品。原型MemPool(allocator=None,use_on_oom=False,no_split=False)：默认沿用当前缓存分配器；use_on_oom允许池外申请OOM时最后使用该池；no_split不拆分内存段。它不是更换全局分配器，也不是保证不会OOM或不产生碎片。

用户池id为Tuple[int,int]，首项0、第二项按创建递增，以区别NPUGraph内部池。对象本身持一个引用，进入use_mem_pool加一、退出减一；退出上下文和释放使用该池的Tensor都是回收前提，不能只据Python变量离开作用域认定所有资源已释放。

use_mem_pool只路由当前线程的申请，内部新建线程不会自动使用该池。固定memory.py使用try/finally结束分配路由并releasePool，对应引用计数递减；调用方仍负责Tensor和跨流消费者生命周期。950DT只支持默认缓存分配器创建池，不支持allocator参数指定NPUPluggableAllocator。

独立NPUPluggableAllocator/change_current_allocator的原生中文表只列A2/A3、英文明确950不支持，初始化前切换与回调ABI见[分配器生命周期](torch_npu_pluggable_allocator_lifecycle.md)；不能由MemPool默认缓存分配器支持扩大自定义分配器范围。

## 属性、快照与版本表的差异

MemPool.snapshot返回按池ID过滤的segments列表，跨设备；use_count返回int。2.11..2.14中英文另明确不支持include_traces参数，2.7.1/2.9/2.10未写这句；固定实现snapshot(self)无该参数，不能从旧页省略推定支持。

旧三版本MemPool文字同时称不提供原生PyTorch2.7的MemPoolContext/MemPool.allocator，中文却又列allocator属性的三产品支持表，2.7.1还单列MemPoolContext.active_pool支持。保留文档内部张力，不据子项表生成已确认调用配方；当前所读Python类只公开id/use_count/snapshot。use_mem_pool上下文的产品表不扩展这些旧接口。

## 统计入口的边界

empty_cache/mem_get_info、memory_stats/summary/allocated/reserved、max/reset_peak、memory_cached/max/reset_max、caching_allocator_alloc/delete/get_allocator_backend等相应项列三类产品，按NPU形式调用；支持表未给所有参数/返回规格。set_per_process_memory_fraction中文仅列A2/A3、英文明确950不支持；不把其他quota参数名或一次返回成功当作完整显存隔离。

host_memory_stats、reset_peak_host_memory_stats列三类产品；host_memory_stats_as_nested_dict与reset_accumulated_host_memory_stats从2.11..2.14收录，中文仅列A2/A3、英文明确950不支持。device/Host统计不是同一口径，计数器复位也不等于释放内存。[allocated/reserved与npu-smi层次](torch_npu_memory_counters.md)另有定义。

中文还列get_per_process_memory_fraction、memory_snapshot、memory.caching_allocator_enable、use_mem_pool及从2.9起收录的reset_accumulated_memory_stats；英文未重复部分条目，不把缺项变成任意产品的绝对不支持。accelerator.memory的empty_cache/empty_host_cache/get_memory_info、allocated/reserved/max/stat/reset十个入口仅在2.13/2.14中英文收录，均列三类产品；不能按相近名字补齐更旧版本。

## 不同snapshot入口不是同一对象

另七份中文CUDA Memory Usage页列_snapshot/_dump_snapshot三类产品。固定NPU memory_snapshot(mempool_id=None)返回segments列表并按pool ID过滤；私有_snapshot返回包含segments和device_traces的字典。_snapshot虽然签名有device=None，代码却调用_npu_memorySnapshot(None)，未消费device；不能据传入device断言已按设备过滤。

_snapshot(augment_with_fx_traces=True)会尝试把FX生成文件堆栈关联回模型源码，要求同一进程已编译相关FX图，只给相应Frame增补FX字段；compile_context与轨迹字段也不能直接当作所有版本/外部工具的固定Schema。

_dump_snapshot默认文件dump_snapshot.pickle，先pickle.dump快照，再尝试保存组件内存信息；若后者失败，会初始化、启动并停止一次CPU/NPU Profiler并完成采集收尾。它不是无副作用的纯文件写入，计时与已有采集状态要分别核对；本卡未执行采集、导出或加载pickle。OOM自动触发条件、历史开关与组件CSV门槛另见[OOM指南](torch_npu_oom_memory_snapshot.md)，其A2/A3整体范围不由本接口表扩展。

## 验收

固定池、线程、设备、统计窗口和活跃Tensor，检查真实路由/释放与跨流寿命；对快照区分当前segments、历史事件、FX归因与组件导出。比较关闭调试后的稳态时间和峰值，不能用池存在、empty_cache或一次快照判定无泄漏/无OOM。

## Host内存统计的私有到公开标记

private_apis两侧将torch.cuda.reset_accumulated_host_memory_stats/host_memory_stats_as_nested_dict的NPU形式分别指为torch_npu.npu的同名方法，明确A2/A3支持、950暂不支持，并说明从PyTorch2.9.0开始改为公开接口。私有页仍保留说明不意味着公开条目失效；统计/清零与设备内存快照、池snapshot分别核对，不能从Host名字推断全部设备分配器计数或返回结构。

## 950DT环境配置与方法支持分别核对

同提交中英文分配器、禁用缓存、捕获GC和自动OOM环境页均列A2/A3及950DT。以下是环境页的合同，不把它们扩展为前述所有内存方法都支持950，也不扩为950PR：

| 环境配置 | 限定与版本 |
| --- | --- |
| PYTORCH_NPU_ALLOC_CONF / PYTORCH_ALLOC_CONF | 统一名要求TorchNPU≥26.2且PyTorch≥2.10，二者互斥；NPU参数不直接等同CUDA。max_split默认无限大、非默认>20MB；GC阈值(0,1)默认禁用，任一非默认须关闭expandable_segments |
| expandable_segments / page_size | 扩展段默认False且HDK≥23；page_size仅1GB，HDK≥25.0.RC1/CANN商用≥8.1.RC1，明确约束为请求>1MB生效，≤1MB不生效；物理页与20MB默认段粒度分开 |
| base_addr_aligned_kb / segment_size_mb / large_segment_size_mb | 对齐整数0..16KB默认16、仅扩展段；≥2MB大块尽量按16KB对齐基址，配置0为跳过该额外基址重对齐——实现无主动512B基址对齐步骤，申请尺寸仍按512B倍数向上舍入，不据配置值断言返回地址的512B对齐性（行级证据见[原生配置解析器](torch_npu_native_allocator_config_parsing_and_runtime_allowlists.md)）；旧段整数20..512MB默认20仅VM且已废弃，新段整数>10MB默认20同时适用VM/非VM，要求TorchNPU≥26.1/PT≥2.11。page_size优先于新段、新段优先于旧段，max_split须≥新段 |
| roundup_power2_divisions / max_non_split_rounding_mb | 前者默认512B舍入，可统一或按幂区间分段；后者默认20MB正整数，仅请求>max_split时约束足够大的候选块余量，不能复用小于请求的块 |
| multi_stream_lazy_reclaim / release_lock_on_npumalloc | 均默认False；前者按文档要求TorchNPU7.3.0以上、优先空闲块，Events>512或无可用块再查询，释放条件/峰值不变；后者底层分配时释放部分锁，可增加资源占用、自定义分配器兼容需核对 |
| per_process_memory_fraction环境项 | 默认1、[0,1]，初始化限额，TorchNPU≥26.1/PT≥2.10；该环境支持不能覆盖set_per_process_memory_fraction方法明确950不支持的产品表 |
| pinned memory选项 | 三种后台Events/扩展段/Host注册、两个大块舍入和缓存阈值按[专门配置指南](torch_npu_pinned_memory_options.md)逐项门槛；Host扩展段与注册互斥，扩展段忽略阈值并告警，不能当Device池别名 |
| PYTORCH_NO_NPU_MEMORY_CACHING / TORCH_NPUGRAPH_GC | 前者未配/0复用、1禁用且默认关闭VM并降速，check_uce_in_memory要求未配置；GC默认0、1捕获时主动GC并增加开销，非法值在PT2.7.1前后分别落0/1 |
| throw_on_npumalloc_oom / OOM_SNAPSHOT_ENABLE/PATH | 预防拒绝要求TorchNPU≥26.2/PT≥2.13，fraction<1时不生效；拒绝增加num_oom_rejections但不触发自动快照。快照0默认关闭、1含历史、2仅当前；路径默认cwd，自定义须已存在可写。环境支持不证明组件CSV等扩展产物亦全支持950 |

完整分配器数值与1MB原文口径见[A2/A3优化指南](../torch_npu_allocator_options.md)，分配器各键文档/实现偏差的行级证据见[原生配置解析器](torch_npu_native_allocator_config_parsing_and_runtime_allowlists.md)；上述950DT环境入口单独消费其明列范围，本文未执行分配、GC、采集或加载快照。

## 内存总览是能力导航，不覆盖逐方法产品表

同提交中英文memory_resource_overview把体系分为框架生命周期/Autograd层、Device缓存分配器层、NPU特有优化层。六类特性为虚拟内存、快照、自定义分配器、跨流复用、IPC和每流TaskQueue；导航中的“可直接复用”没有独立产品矩阵，不能覆盖详情的950DT自定义分配器/IPC排除或方法表差异。

| 总览列出的入口组 | 使用时保留的粒度 |
| --- | --- |
| empty/zeros/ones/rand，to/npu/half/bfloat16 | device=npu是创建/搬运的入口，Tensor.cuda在对照表出现不等于未迁移的CUDA调用自动变NPU；dtype/shape/contiguous按逐接口表 |
| pin_memory与DataLoader(pin_memory=True) | Host锁页与Device缓存池不同，后台线程/扩展段/注册及阈值按[pinned配置](torch_npu_pinned_memory_options.md) |
| view/reshape/permute/transpose与add_/mul_/relu_ | 概述把它们归为共享存储/原地节省，不能据分类保证任意stride的reshape都无新分配，或取消原地的别名/Autograd限制；核对实际storage和[布局语义](torch_npu_native_tensor_layout.md) |
| no_grad/inference_mode、AMP、checkpoint、参数共享 | 概述列禁Autograd、低精度、重计算和共享权重几类机制，各自的RNG、梯度、dtype与状态约束独立；不是所有内存优化可机械叠加 |
| save/load与map_location | 选择CPU/NPU加载位置是Checkpoint管理层，不等于改变活跃模型、所有状态或跨版本格式；本卡未加载文件 |
| allocated/reserved及max、summary、empty_cache、两类reset | Tensor、缓存、摘要和统计窗口按各自口径，清峰值/累计计数不释放活跃内存 |
| MemPool/use_mem_pool、进程fraction、history/snapshot | 按前文线程/池所有权、950方法例外与快照结构，不从总览名称补齐完整契约 |
| _save_segment_usage/_save_memory_usage、Profiler profile_memory | 静态SVG与Profiler分配时间线是不同产物，前者不等于采集设备时间，后者要适配实际NPU Profiler接口 |

例如同提交英文2.14的torch.autograd.grad_mode.inference_mode及clone明确950DT不支持，而本总览把inference_mode列为通用复用；保留入口名字和文档层次，不据概述抹去更窄表，也不把该条自动扩成所有Autograd上下文都不支持。Tensor.reshape在同版列三产品和局部self类型，但支持表没有保证特定输入零拷贝。

## 私有SVG导出的读取范围

固定memory.py中的_save_segment_usage(filename="output.svg",snapshot=None)与_save_memory_usage同签名。snapshot为None时各自调用内部_snapshot；显式传入则直接交_segments或_memory转换，再以文本方式写文件，函数没有给出返回数据对象。这两处没有做跨版本快照结构兼容校验；默认文件名相同，分别保存时应明确产物身份。

这里只读取两个函数及所需上下文，不宣称_memory_viz全部实现或外部交互查看器已摄取。手动快照、历史与组件CSV仍按前文及[OOM指南](torch_npu_oom_memory_snapshot.md)分别解释，未导出SVG、调用Profiler或访问设备。

## OpPlugin内存列表与两类清缓存接口

独立Memory目录仅为旧CUDA式统计/分配入口、pluggable和两类清缓存的简要索引，没有新的完整产品矩阵；具体[虚拟地址/Host缓存释放](../../../apis/torch_npu/cache_release.md)分别记录扩展段、物理句柄保留与Host未占用缓存，不能以“轻量empty_cache”名字推定物理内存归还或活跃Tensor释放。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-cuda.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-cuda.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-cuda.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-cuda.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-cuda.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-cuda.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-cuda.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-cuda.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-cuda.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-cuda.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-cuda.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-cuda.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-cuda.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-cuda.md)（constraint）
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-cuda-memory.md)（constraint）
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-cuda-memory.md)（constraint）
- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-cuda-memory.md)（constraint）
- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-cuda-memory.md)（constraint）
- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-cuda-memory.md)（primary）
- [固定来源 20](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-cuda-memory.md)（constraint）
- [固定来源 21](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-cuda-memory.md)（constraint）
- [固定来源 22](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-accelerator.md)（constraint）
- [固定来源 23](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-accelerator.md)（constraint）
- [固定来源 24](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-accelerator.md)（constraint）
- [固定来源 25](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-accelerator.md)（constraint）
- [固定来源 26](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-accelerator.md)（constraint）
- [固定来源 27](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-accelerator.md)（constraint）
- [固定来源 28](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-accelerator.md)（constraint）
- [固定来源 29](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-accelerator.md)（constraint）
- [固定来源 30](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-accelerator.md)（constraint）
- [固定来源 31](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-accelerator.md)（constraint）
- [固定来源 32](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-accelerator.md)（constraint）
- [固定来源 33](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-accelerator.md)（primary）
- [固定来源 34](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-accelerator.md)（constraint）
- [固定来源 35](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-accelerator.md)（constraint）
- [固定来源 36](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/memory.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/private_apis.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/private_apis.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_ALLOC_CONF.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/PYTORCH_ALLOC_CONF.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_NO_NPU_MEMORY_CACHING.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/PYTORCH_NO_NPU_MEMORY_CACHING.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/TORCH_NPUGRAPH_GC.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/TORCH_NPUGRAPH_GC.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/OOM_SNAPSHOT_ENABLE.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/OOM_SNAPSHOT_ENABLE.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/OOM_SNAPSHOT_PATH.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/memory_management/OOM_SNAPSHOT_PATH.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/memory_management/memory_resource_overview.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/memory_management/memory_resource_overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-Tensor.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/Memory-management-API.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/Memory-management-API.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/Memory-management-API.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/memory.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp)（implementation；base_addr_aligned_kb 尺寸舍入与基址重对齐消费面）
