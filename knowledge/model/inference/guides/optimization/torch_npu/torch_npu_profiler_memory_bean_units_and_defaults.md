---
type: Guide
title: Profiler内存Bean：原始字节、CSV单位与缺失值边界
description: 区分MemoryUse与GE/NPU内存记录的字节、KB、MB、时间单位以及None、零值、设备标签和转换错误。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_ge_memory_record_bean.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_ge_op_memory_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_memory_use_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_npu_mem_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_npu_module_mem_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_ge_memory_record_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_ge_op_memory_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_memory_use_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_npu_mem_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_npu_module_mem_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_common_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_common_bean.py
  role: implementation
created_at: '2026-11-11T04:30:34Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler内存Bean：原始字节、CSV单位与缺失值边界

## 版本与解释范围

本卡核对TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的五类内存Bean。成对完整AST相同，原始文本差异已核；只解释这里实际实现的布局和投影，产品平台未知，保持draft。没有运行采集、SQL或设备实验。

CommonBean保留传入字典引用，不复制。MemoryUseBean在构造时把固定区转换为内部字段；其余CSV Bean通常在访问property/row时才转换字典值。后续字典修改、访问时机和CSV字符串/数字类型会影响结果，类型注解和列名不保证数据已经校验。

## MemoryUse：字节输入与不同出口

固定格式`<7q2b3B2Q`共77字节：依次为ptr、时间、alloc_size、total_allocated、total_reserved、total_active、stream_ptr七个有符号64位，device_type/device_index两个有符号字节，component_type/data_type/allocator_type三个无符号字节，TID/PID两个无符号64位。没有本机对齐。时间在构造时经syscnt与本地时钟两级转换；校准前提见[框架记录解码](torch_npu_profiler_framework_bean_wire_formats.md)。

|属性|实际单位和用途|
|---|---|
|alloc_size|原字节除1024，输出KB；alloc_size_for_db原字节不变。|
|total_allocated/total_reserved/total_active|原字节除1024²，输出MB；对应`*_for_db`仍是原始字节。|
|ptr、stream_ptr、pid、tid|返回解包整数，本类不根据地址复用或进程作用域建立全局对象身份。|
|component_type/data_type/allocator_type/device_type|返回原槽；is_inner_allocator仅判断allocator_type==0，is_npu仅判断device_type==20。|
|device_index|覆盖值不是-1时优先返回覆盖值，否则取原槽转int；setter直接写值，不检验设备枚举。|

row固定为`[PTA, 时间us字符串加制表符, allocated_MB, reserved_MB, active_MB, stream_ptr, device_tag]`。device_type为20时标签`NPU:<index>`，**其他所有类型都标CPU**，不是只有CPU_ID==0才进该分支；不能据这个标签证明原始设备类型有效。row第一列始终PTA，并未依据component_type自动标出workspace。分配/释放分类、生命周期配对、PTA与GE合并属于[内存合并](torch_npu_profiler_pta_ge_memory_merge.md)、[算子内存归因](torch_npu_profiler_op_memory_pairing_and_attribution.md)与[数据库内存解析](torch_npu_profiler_memory_database.md)，不能由getter完成。

## GE快照与算子记录使用不同默认值

GeMemoryRecordBean的component返回Component字段；time_ns把Timestamp(us)转ns，缺少时间时传入None并可能转换失败。Total Allocated(KB)/Total Reserved(KB)默认0，再float后除1024成为MB；显式None、空串或坏数值不是这个默认0。device默认空字符串。total_active getter为0、stream_ptr为None，是本类未提供对应测量的占位。

它的row却固定为`[GE, 时间us字符串加制表符, allocated_MB, reserved_MB, None, None, device]`：首列不使用component getter，active槽使用None而非getter的0。不要把getter占位和导出缺失值混成真实测得的零活跃内存。

GeOpMemoryBean的name为`cann::`加Name；Name缺失时可能TypeError。Size(KB)、Allocation Time(us)、Duration(us)、Device原样读取，不自动转float。release_time仅在allocation_time和dur都truthy时将两项us各转ns相加，再导出us字符串加制表符；否则None。因此数字0为假，但CSV字符串`"0"`为真，不能把这种条件理解成健壮的数值零判定。

Allocation/Release Total Allocated(KB)与Reserved(KB)四属性对truthy值执行float/1024，否则None；字符串`"0"`会得到0.0，数字0或空串得到None。row的15槽为`[name,size,allocation,release,None,duration,None,allocation_allocated_MB,allocation_reserved_MB,None,release_allocated_MB,release_reserved_MB,None,None,device]`，未实现的active、workspace或关联槽不能补成测量值。本类从现成记录推导释放时间，没有执行PTA地址配对，也不证明峰值、泄漏或关联算子唯一。

## NPU CSV的特殊投影

NpuMemoryBean仅当event等于APP时返回行，否则返回空列表。输出顺序为event、timestamp(us)、allocated(KB)、memory(KB)、active、stream_ptr、Device_id；**只有memory(KB)的值执行float/1024**，其他字段按字典get默认空字符串原样输出，allocated(KB)并不一起换算。该静态列名不能作为所有数值已统一单位的保证；没有headers属性来自动重命名这个换算后的槽。

NpuModuleMemoryBean在构造时将Total Reserved(KB)默认0转float/1024，再转str写进原字典的Total Reserved(MB)。row按Device_id、Component、Timestamp(us)、Total Reserved(MB)、Device固定顺序get，缺省空字符串；headers直接返回类上的SHOW_HEADERS列表，未复制。原字典被改写和表头可变，复用同一输入时应保留这个影响。

## 时间精度与错误边界

convert_us2ns按十进制字符串拼接三位小数，不足补零、超出截断而非四舍五入，并移除末尾制表符；多小数点和无法转成整数的内容会失败，不支持把科学计数法或None当成通用可容错输入。convert_ns2us_str要求整数ns（无穷特殊分支除外），用字符串插小数点并追加tail，不能把任意float直接交给它。

这些换算不是内存指标计算。对照同一记录时先标明原字节、KB、MB和数据库出口，区分缺字段、显式None、数字0、字符串0与空row，再检查设备覆盖和时间基准。Bean不检查数值非负、字典schema、采集完整性或跨stream重叠，也未测得产品支持与性能收益。

## Evidence

本文所依据的完整模块与有界辅助来源如下；未列完整范围的依赖保持独立待审，固定提交不等于设备验证。

- [ac0e156 _ge_memory_record_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_ge_memory_record_bean.py)：1–47。
- [ac0e156 _ge_op_memory_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_ge_op_memory_bean.py)：1–69。
- [ac0e156 _memory_use_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_memory_use_bean.py)：1–149。
- [ac0e156 _npu_mem_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_npu_mem_bean.py)：1–22。
- [ac0e156 _npu_module_mem_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_npu_module_mem_bean.py)：1–21。
- [f3ecfe4 _ge_memory_record_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_ge_memory_record_bean.py)：1–47。
- [f3ecfe4 _ge_op_memory_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_ge_op_memory_bean.py)：1–69。
- [f3ecfe4 _memory_use_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_memory_use_bean.py)：1–149。
- [f3ecfe4 _npu_mem_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_npu_mem_bean.py)：1–22。
- [f3ecfe4 _npu_module_mem_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_npu_module_mem_bean.py)：1–21。
- [ac0e156 _constant.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py)：40–40、79–79、82–82、83–83、84–84、87–87、88–88、89–89、268–279、282–294。
- [ac0e156 _common_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_common_bean.py)：1–21。
- [f3ecfe4 _constant.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py)：43–43、79–79、82–82、83–83、84–84、87–87、88–88、89–89、263–274、277–289。
- [f3ecfe4 _common_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_common_bean.py)：1–21。
