---
type: Guide
title: Profiler组件内存合并：PTA、GE与分配释放配对
description: 补齐双版本MemoryDbParser的GE事件类型、按算子地址设备配对、未知释放及落表槽位，并保留PTA与GE的时序合并口径。
tags:
- task.debugging
- topic.performance.analysis
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_memory_view_parser.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_memory_view_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_memory_db_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/prof_db_parse/_memory_db_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_ge_memory_record_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_memory_use_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_db_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_parser_config.py
  role: implementation
created_at: '2026-11-10T13:28:29Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler组件内存合并：PTA、GE与分配释放配对

本卡定向审阅TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的MemoryViewParser/MemoryDbParser组件总量消费者，并对照发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的选定方法。所比Text七个与Db七个方法AST相同；主线bean、schema、上游CANN导出和未比方法不由此获得两版相同保证。平台未知，保持draft、空平台；未执行上游、SQL或采集解析。

## 入口与来源

解析配置把Text tensorboard handler连接到MemoryViewParser；Db handler连接DbParser，其PYTORCH_DB_MAP包含MemoryDbParser。消费者从MEMORY_PREPARE取得PTA记录，所选run分支调用合并与输出，不是仅有未连接的辅助函数。是否实际采到数据、表或文件仍取决于采集配置和版本。

| 产物链 | 所读输入与转换 |
| --- | --- |
| Text | CANN CSV中的GE_MEMORY_RECORD通过GeMemoryRecordBean转换；Component=GE进入ge_record_list，其他组件留component_list；NPU_MEMORY中的APP行另加入输出。`_get_data_from_file`面对同类型多个文件仅取set的一个文件，不合并所有分片。 |
| Db | 从NPU_OP_MEM读取时间、设备及totalAllocate/totalReserve，经get_ge_record_list生成GE快照；没有该表时get_ge_memory_data直接返回。不会仅凭Text的组件文件推定Db一定具有APP等同行。 |
| PTA | 消费已准备记录的time_ns及allocator总量；Workspace组件进入单独分支。原始框架分配配组/算子归属见[OP内存配组](torch_npu_profiler_op_memory_pairing_and_attribution.md)。 |

这里的当前固定字符串是`PTA`、`GE`、`PTA+GE`、`APP`、`WORKSPACE`；不是跨版本枚举保证。Db实际以字符串ID保存组件，需关联STRING_IDS。

## 组合行是沿用最近值的时序合并

两个实现先按时间排序GE列表，假设PTA列表已排序，然后双指针交织。每处理一条普通当前记录，都输出当前原始组件行和一条PTA+GE行；组合值为当前allocated/reserved/active加上**同设备对侧最近已处理记录**的对应总量。尚无同设备对侧记录时，PTA+GE直接使用当前值，不补虚构的另一侧采样。

这是一条由事件触发更新、沿用另一侧最近值的合成曲线，不是每个时间点重新同步测量两组件，也没有线性插值、时间窗口容差或按stream相等来配对。组件分项、组合行、APP不可再次相加当作独立占用。

当GE时间等于PTA时间，条件`ge_time >= pta_time`先处理PTA，再处理GE。因此同一个时间戳可以先后有两条不同的PTA+GE值：第一条仍用旧GE值，第二条才用新GE值；仅按timestamp去重、求和或随意保留第一条会改变含义。这个结论来自静态分支顺序，未运行采集样例。

WORKSPACE仅输出原行，不额外生成PTA+GE，也不覆盖用于后续GE合并的last_pta_record。Text的APP/其他组件输出与这条合并曲线分开；输出整个文件行序还包含先前APP和末尾component_list，不能把它视作所有组件统一全局时间排序后的表。

## 设备和流字段的边界

last_ge_record和last_pta_record按设备身份索引：Text使用`NPU:<index>`等device_tag，Db使用deviceId。在CANN路径只得到一个device id时，PTA侧采用该id；否则MemoryUseBean.device_index仍回到记录自身索引。这样处理不是全局rank到设备的通用映射，也不提供跨进程身份恢复。

组合行的stream_ptr优先取当前行非零/真值，否则沿用对侧最近行；它只是携带一个可得流指针，不要求两个来源属于同流。不能用组合行的单个streamPtr把allocated/reserved总量解释成该流独占量。

## CSV和Db的数值合同

| 项目 | 所选主线实现 |
| --- | --- |
| Text时间/总量 | 内部按time_ns合并，写Timestamp(us)；MemoryUseBean字节除`1024²`，GeMemoryRecordBean的KB除1024，输出列标MB。 |
| Db时间/总量 | 合并保留来源timestampNs/time_ns及整数Byte量，没有Text的us/MB转换；这是所选实现证据，不回写为全部发布文档的单位保证。 |
| GE Active/Stream | Text原始GE.row以None填写active/stream，但参与合并的total_active属性为0、stream_ptr为None；Db构造GE行为active=0、stream=None。PTA+GE的Active因此没有独立测量到GE active量。 |

这些零/None属于具体构造字段，不能据此认定GE真实active使用量为零。时间单位、框架总量和设备进程总量应分别核对；字段解释复用[内存数据库文档](torch_npu_profiler_memory_database.md)。

## 诊断使用和边界

比较优化前后时，固定设备、采集窗口、导出模式、事件覆盖与组件来源；先拆出原始PTA/GE，再按相同合并规则理解PTA+GE峰值。缺对侧记录或多文件仅取一份会影响曲线完整性，不能把下降独自解释为模型节省显存。

本卡覆盖总量获取、时序合并和直接输出消费者，并给出下文所列完整MemoryDbParser与主线OP_MEMORY列顺序；CANN采集/导出、其他数据库生产schema和真实数据完整性仍独立核验。未知数据、未产表和零量不是同一状态；未执行统计、内存或性能实验。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_memory_view_parser.py)（primary）：主线定向范围 20–161。
- [固定实现来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_memory_view_parser.py)（implementation）：发布版选定方法AST对照范围 40–51, 54–73, 75–90, 92–97, 99–133, 140–145, 147–161。
- [固定实现来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_memory_db_parser.py)（implementation）：主线定向范围 15–22, 43–96, 105–139, 186–243, 249–253。
- [固定实现来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/prof_db_parse/_memory_db_parser.py)（implementation）：发布版选定方法AST对照范围 67–79, 81–96, 131–139, 186–199, 201–235, 237–243, 249–253。
- [固定实现来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_ge_memory_record_bean.py)（implementation）：主线定向范围 9–47。
- [固定实现来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_memory_use_bean.py)（implementation）：主线定向范围 57–115, 139–149。
- [固定实现来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py)（implementation）：主线定向范围 80–90。
- [固定实现来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_db_parser.py)（implementation）：主线定向范围 20–27, 39–65。
- [固定实现来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_parser_config.py)（implementation）：主线定向范围 76–124, 135–154。

## 完整MemoryDbParser补充：GE生命周期与落表

完整读取两固定版1–253行，模块AST完全相同，原始文本差异仅空白；该结论只针对MemoryDbParser，不提升整套MemoryView/Prepare或原始采集为两版完全相同。卡片生命周期、平台与来源沿用既有记录，没有新增verified。

run先从CANN路径取device列表：只有恰好一个设备时覆盖PTA输出device_index，否则用-1并逐记录回落；连接失败抛异常。随后设MEMORY字符串ID起点，取MEMORY_PREPARE的Db生命周期列表与pta_record_list，按**GE读取→组件快照→OP_MEMORY→STRING_IDS**保存。部分列表可被原地改写，不是一份完全隔离的输入快照。

get_ge_memory_data只在NPU_OP_MEM存在时读operatorName/addr/type/size/timestampNs/totalAllocate/totalReserve/deviceId，SQL没有ORDER BY。type经STRING_IDS解析并缓存，值恰为release时把size乘-1；缺类型或空类型抛RuntimeError，其他名称按原size处理。它先生成GE快照（Active=0、stream=None），再配对算子生命周期；原始GE快照不能据此证明真实active为零。

get_ge_op_mem_data按输入遍历，以**(operatorName ID,addr,deviceId)**作键。size>0保存当前分配，重复键覆盖旧值；size<0只有已有同键分配才输出成对记录并删除，缺分配的释放跳过，size=0不配对。配对使用时间戳相减，没有额外核对释放大小相等、时间单调、stream或跨进程身份；SQL无排序尤其需要核对输入顺序。剩余分配保留申请信息，release/activeRelease/duration等未知槽为None，不补0或直接判泄漏。

成对GE输出按真实列表与主线schema填`duration=release_timestamp-allocation_timestamp`，activeReleaseTime/activeDuration、Active总量和stream留None。类内OpMemoryTableRow把索引5命名ACTIVE_DURATION、6命名DURATION，但实际GE列表和TableColumnsManager的OP_MEMORY列顺序是5=duration、6=activeDuration；本模块实际只用该enum的NAME索引。不能按未使用的enum标签反向解释真实列或擅自交换值。

save_op_memory_data_to_db在PTA/GE均空时不建表；否则将PTA每条name原地转STRING_ID，再拼接GE行写入。GE operatorName本来就是源表ID，不在这里重新按字符串注册。save_memory_record_data_to_db先生成PTA快照、执行前文时序合并，非空才建MEMORY_RECORD；save_strings_id最后取出并清空字符串管理器映射后写STRING_IDS。字符串起点只重设计数，并不在此证明其他阶段的单例缓存已重置。

以上补齐本地枚举、构造、配对、保存和异常路径；原始内存事件、allocator、MemoryPrepare、GE导出与数据库管理器的事务/重复插入仍分别核验。先比较同设备、同窗口的原始行与配对前后数量，再解释组合峰值或释放缺失，不以一次成功返回替代数值和内存验收。

## 完整数据库链与补充证据

- [固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_memory_db_parser.py)（implementation）：1–253。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/prof_db_parse/_memory_db_parser.py)（implementation）：1–253。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py)（implementation）：304–305、355–356、407–432。
