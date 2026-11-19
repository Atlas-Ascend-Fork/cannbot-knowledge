---
type: Guide
title: Profiler 内存时间线与元数据：采集前提和统计归因
description: 说明 memory timeline 开关、事件分类、设备选择和预置/动态元数据的不同时间点。
tags:
- task.debugging
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/ascend_pytorch_profiler_user_guide.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-profiler.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/ascend_pytorch_profiler_user_guide.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/profiler/memory_timeline.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/profiler/memory_timeline.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SECURITYNOTE.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SECURITYNOTE.en.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/SECURITYNOTE.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/profiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/profiler_interface.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler_interface.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/_profiler_path_creator.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_profiler_path_creator.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/get_trace_id.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/get_trace_id.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/set_custom_trace_id_callback.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/set_custom_trace_id_callback.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-_KinetoProfile.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-_KinetoProfile.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-_KinetoProfile.md
  role: constraint
created_at: '2026-11-09T02:54:19Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# Profiler 内存时间线与元数据：采集前提和统计归因

## 版本与范围

依据固定 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 和 OpPlugin 主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的相应接口文档，限定 A2/A3。主线配套仍需核验，不回推为 26.0/PyTorch2.8 已支持所有选项。未运行采集或分析实验。

## 内存时间线

profile 对象的 export_memory_timeline(output_path,device) 从已采数据导出指定设备，device 形如 npu:0，且必须实际存在于此次采集。需要 record_shapes=True、profile_memory=True，并至少开启 with_stack 或 with_modules；仅打开 profile_memory 不能保证获得完整归因时间线。

.html 导出内嵌图，需要 matplotlib；.json/.json.gz 为按类别汇总的时间点；raw.json.gz 为原始事件，含时间、动作、字节数与类别。动作可为 PREEXISTING、CREATE、INCREMENT_VERSION、DESTROY；分类包括参数、优化器、输入、临时、激活、梯度、AUTOGRAD_DETAIL 和 UNKNOWN。

这些类别描述所采进程/设备范围，不应把 UNKNOWN 直接叫作泄漏，也不能把时间线总额视作整机全部设备内存。OOM 快照与 Profiler 时间线的采集方式、历史和覆盖范围分别核验。

## 元数据时间点

preset_metadata_json 在 prof.start() 前提供静态配置；add_metadata_json 和 add_metadata 在启动后记录动态 JSON 或文本。JSON value 用 json.dumps 生成合法字符串，避免同类键重复覆盖导致归因混乱。

元数据保存在 profiler_metadata.json；指南还说明已选环境变量在 Text/Db 导出下可进入 META_DATA。只采集列出的环境项，不能因为元数据文件存在就假定全部进程环境、软件配套和随机种子都已记录。

- [OOM 分配器快照](torch_npu_oom_memory_snapshot.md)
- [allocated、reserved 与设备占用](torch_npu_memory_counters.md)


## 使用后核验

先检查采集窗口、rank、线程、活动类型与配置是否生效，再核对实际产物和业务开销；缺少数据不等于该阶段耗时为零。关闭调试配置后再测正常性能。

- [基础采集、调度与解析](torch_npu_profiler_capture_schedule.md)

## 数据库中的内存生命周期

需要区分申请、释放与实际归还内存池时，使用[MEMORY_RECORD 与 OP_MEMORY](torch_npu_profiler_memory_database.md)的组件、设备和流字段；时间线类别、数据库记录和 OOM 历史不是相同观测。

## 原生支持清单的导出与元数据边界

同一PyTorch主线原生Profiler页在2.7.1、2.9..2.12以_KinetoProfile.add_metadata/add_metadata_json/export_chrome_trace/export_stacks列三类产品，在2.13/2.14的profile.*条目改为中文仅A2/A3、英文950不支持；NPU形式仍对应torch_npu.profiler._KinetoProfile的方法。export_memory_timeline各版中文只列A2/A3、英文明确950不支持，不能由旧类级三产品表扩展时间线导出。

英文2.10与2.14对export_memory_timeline增加弃用提示、建议上游CUDA memory snapshot路线，并特别要求设备支持范围另核对；其他同提交版本页未重复。它不证明NPU时间线实现已移除，也不意味着任意CUDA快照API可直接代替上述NPU采集/归因合同。普通分配器segments、带历史的快照、Profiler分类时间线分别消费，见[原生内存API](torch_npu_native_memory_api_scope.md)。

## 英文缺项、四项环境和图示身份

中文长指南独立给preset_metadata_json的启动前合同，英文只列初始化后/结束前的add_metadata及add_metadata_json；英文缺少预置入口不等于明确不支持。重复key的动态更新不能未经实现核对就当作逐step历史数据库，记录step_id也不单独保证每次值都保留。

默认采集环境项只列ASCEND_GLOBAL_LOG_LEVEL、HCCL_RDMA_TC、HCCL_RDMA_SL、ACLNN_CACHE_LIMIT。Text模式进入profiler_metadata.json及DB的META_DATA，Db模式进入META_DATA；这些条目不证明收集了全部环境、随机状态或版本配套。JSON/文本元数据可并用但避免同类键相互覆盖。

内存图两语言逐字节相同，已查看：0.34GB allocated/0.38GB reserved和类别堆叠是历史样例，不作本机占用或OOM阈值。参数device文字混写Device ID/Rank ID，实际必须选本次采集中存在的设备；不能把全局rank直接当本机npu索引。该导出与采集rank筛选是不同层次，时间线类别也不是分配器所有内存的完全分类。

两语言指出profile_memory在glibc<2.34的环境可能触发已知Bug19329；外部issue内容不在本卡来源内。这是定位环境相关采集异常的来源线索，不仅凭版本或缺失记录就指定唯一根因，也不代表本次已升级系统或重现故障。

## 性能数据的文件权限与保留范围

主线双语及发布安全声明称Profiler默认不采集，开启后会在本地生成性能记录，文件权限640、目录750。这是这些版本声明的生成策略，不保证复制、归档、共享目录、导出工具或外部存储继承相同权限；模型输入形状、调用栈与元数据也应按实际采集内容决定保留范围。

torch.save产物权限依赖系统设定，不能套用Profiler的640/750保证。声明建议主机/容器按需求控制umask和文件权限；其中列的是参考最大权限，不把0027“及其以上”按数字大小理解为所有更大值都更严格。AOE、算子dump和CANN日志同样会产生本地数据，但并未由此证明它们使用同一Profiler生成权限或覆盖全部模型数据。本次没有修改系统权限、采集或打开数据产物。

## 元数据包装的发布与主线差异

发布类没有preset_metadata_json或trace ID回调；主线的预置字典到start_trace才交给JSON添加函数。add_metadata与add_metadata_json都按key覆盖而非保留逐step历史，finalize保存后清空当前metadata。

两版普通字符串元数据均检查每串4096及getsizeof估计50KiB；发布JSON方法同样检查，主线JSON方法则只验证字符串和JSON合法性，不能给它套同一限制。getsizeof字典加本次键值不是递归精确计算整个元数据容量。见[_KinetoProfile API](../../../apis/torch_npu/profiler_kineto_profile.md)。

主线[trace ID回调](../../../apis/torch_npu/profiler_trace_id.md)在trace初始化时生成、限制返回str长度≤1024，非法或异常回UUID；setter不改已生成ID，getter也不触发落盘。原始数据的保留还受export_only路径和handler归档删除行为影响，不能只由导出方法返回None推断产物存在。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/ascend_pytorch_profiler_user_guide.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-profile.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-profiler.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-profiler.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/ascend_pytorch_profiler_user_guide.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/profiler/memory_timeline.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/profiler/memory_timeline.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SECURITYNOTE.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/SECURITYNOTE.en.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/SECURITYNOTE.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/profiler.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/profiler_interface.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler_interface.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/_profiler_path_creator.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_profiler_path_creator.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/get_trace_id.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/get_trace_id.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/set_custom_trace_id_callback.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/set_custom_trace_id_callback.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-_KinetoProfile.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-profiler/torch_npu-profiler-_KinetoProfile.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-profiler/torch_npu-profiler-_KinetoProfile.md)（constraint）
