---
type: Guide
title: Profiler数据库归因：框架连接、迭代窗口与通信矩阵
description: 解释两版本Host调用到任务的连接ID和线程筛选、step区间与通信聚合，避免名称/时间相近配对或误读汇总带宽。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_fwk_api_db_parser.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/prof_db_parse/_fwk_api_db_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_step_info_db_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/prof_db_parse/_step_info_db_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_communication_db_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/prof_db_parse/_communication_db_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_id_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_id_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_communication_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_communication_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_fwk_file_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
created_at: '2026-11-11T03:55:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler数据库归因：框架连接、迭代窗口与通信矩阵

## 固定版本与身份层次

范围为TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`、发布 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 的FwkApiDbParser、StepInfoDbParser、CommunicationDbParser及ID管理模块；继承的通信helper只审Evidence所列范围。保持draft/空平台，未执行SQL或解析器。公开表单位见[数据库字段](torch_npu_profiler_database_relations.md)，调度和部分失败见[装配流程](torch_npu_profiler_database_assembly_and_failure_boundaries.md)。

Str2IdManager对同一非空字符串复用ID，空字符串返回DB_INVALID_VALUE，set_start_id只重设计数；get_all_string_2_id_data取出映射后清空字符串表。ConnectionIdManager每次为传入连接列表分配新组ID，保留原列表引用，不按列表内容去重，查不到组返回[-1]；get_all_connection_ids没有清空映射。CallChainIdManager每次新分配调用链ID，以`;\r\n`切栈并记录字符串ID及深度，读取也不清空。不能把这些组ID直接当CANN connectionId或稳定跨文件身份。

所读主线get_fwk_api要求CPU activity，并选首个框架/队列记录的pid构造globalTid；队列相关ID先由ConnectionIdManager包装，Torch算子连接初始为列表，可混入前后向关联，mstx_前缀另分组。Python trace需hash和func数据同时存在才解析。此生产层限制不由数据库文件存在自动消除。

## 框架到launch：包含、线程与队列

FwkApiDbParser先连接、设字符串ID起点、读取DB_PRE_PARSER。非空时先收Python trace、enqueue、dequeue，再处理Torch和MSTX；最后依次保存PYTORCH_API、STRING_IDS、CONNECTION_IDS、PYTORCH_CALLCHAINS和ENUM_API_TYPE（op/queue/trace/mstx）。连接列表非空才变成组ID，空Torch列表变None；MSTX空列表主线也变None，而发布保留原空列表。表中每个connection组会展开为多行，调用链也按depth展开，不是一行一Kernel。

关联Torch时先在STRING_IDS寻找`launch`且ID为真值，再读CANN_API中name对应、type=10000的调用并按startNs排序；找不到launch，主线以aclgraph可安全缺失的警告返回，发布记错误后返回，均不会补假连接。找不到launch调用也返回。Torch记录按起点排序。

| 分支 | 本地关联机制 |
| --- | --- |
| enqueue与dequeue均非空 | 解包队列组ID取首个相关值，取两端ID集合交集并保留各自原顺序；launch必须严格包含于dequeue区间，再按同一过滤后索引选enqueue，寻找严格包含enqueue的Torch区间，向其连接列表追加launch connectionId。 |
| 任一队列列表为空 | 直接在同globalTid的Torch区间内按严格起止包含扫描launch，保留前进索引。追加动作发生在找到候选后遇到后续不包含分支；本地没有循环末统一flush，不能据单次时间包含就推导一定关联。 |
| MSTX | 调用方先检查MSTX_EVENTS表；方法内框架MSTX mark列表为空就直接返回，不查询。只有框架mark非空才查询，查询无CANN事件时抛RuntimeWarning并让run失败。仅有匹配的双端队列时执行队列关联，没有无队列回落。 |

主线在队列路线新增两处globalTid相等筛选：launch↔dequeue、enqueue↔Torch；发布这两处只比区间。无队列路线两版原本都有线程筛选。相等边界不符合严格`>`/`<`条件；队列交集筛选也没有在本方法重新按ID逐对join，而是依赖过滤后位置对应。主线减少了跨线程误配机会，但未证明任意乱序、重叠或缺失队列均可完整关联。

## StepInfo用Host完整包含建立设备窗口

只从根的直接子节点调用is_profiler_step筛选。连接失败返回空范围；先把存在的框架step时间写STEP_TIME，再检查CANN路径与Level。因此Level=None可以有框架STEP_TIME，却没有后续设备step范围。

有step时CANN_API查询要求type=10000，且整个API满足`step.start<=startNs`和`endNs<=step.end`。按这些connectionId在全TASK表筛记录，globalTaskId作字典键；本地没有另加device键或任务本身时间裁剪。范围起点取关联任务最早start（无任务回落框架start），终点取任务最晚end与框架end的较大值，另保留fwk_step_start_ts。没有step节点则API不加时间窗，范围起点取首设备任务或0，终点保持正无穷，step_id=None。缺表告警返回空数据；主线增加具体表名/连接诊断，未改变以上计算。

## 通信归step依赖时间表，采用闭区间

CommunicationDbParser缺step时使用`[0,+inf]`、None标签的回落窗口。它从CANN分析DB集合只取一个文件，不合并所有文件；分别读取Bandwidth、Matrix、Time已有表。连接失败可告警后返回三个空列表，后续保存连接失败也只告警返回，run仍可能SUCCESS。

Bandwidth和Matrix先按`hccl_op_name@group_name`关联Time行；每条Time的start_timestamp从us转ns，按**首个满足start<=ts<=end的step**附加step和type。边界事件可能与[StepTrace半开区间](torch_npu_profiler_step_interval_aggregation.md)归属不同。无Time匹配的带宽/矩阵行不会独立输出；重复同名Time会再次附加该键下全部相关行。hcom_send/receive/batchsendrecv前缀归p2p，total前缀type为空，其余collective；这些来自名称规则，不是传输内容验证。

## Matrix的top/middle/total不是原始带宽样本平均

矩阵先按step、p2p/collective、操作名@group和src-dst链路构字典，同一操作同一link重复行会被后写覆盖；type为空的total行不进入此重组。继承helper按名称正则提取通信类型，未匹配用`__`前缀回落，发布额外打印未知类型告警。再按(类型,group,link)聚合，原名存Op Name。

每组按bandwidth降序，取top1、中间索引`len//2`、bottom1；数量足够时另取bottom2/3。total使用**sum(transit_size)/sum(transit_time)**，分母绝对值<1e-15返回0，否则round到4位；不等于各带宽的算术平均，也没有消除并发传输的重叠时间。total的transport_type沿最高带宽项，没有另按transport分组；total未携带原操作名，展平时该槽为空。最终再把组名和src/dst从字符串拆出写三张分析表。名称含额外`@`或link含额外分隔符的适用性未被本地校验。

保留操作名、组、rank对、step窗、原始行数和单位，再判断等待/传输/同步；缺关联不是零耗时，聚合比率不是链路峰值或模型独占流量。本次仅静态核对，不认证采集完整性、SQLite写入、外部时钟校准或设备性能。

## 完整数据库链与补充证据

- [固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_fwk_api_db_parser.py)（primary）：1–373。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/prof_db_parse/_fwk_api_db_parser.py)（implementation）：1–237。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_step_info_db_parser.py)（implementation）：1–143。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/prof_db_parse/_step_info_db_parser.py)（implementation）：1–130。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_communication_db_parser.py)（implementation）：1–231。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/prof_db_parse/_communication_db_parser.py)（implementation）：1–231。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_id_manager.py)（implementation）：1–72。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_id_manager.py)（implementation）：1–72。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_communication_parser.py)（implementation）：17–42、56–61、172–184、186–216。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_communication_parser.py)（implementation）：17–42、56–61、170–183、185–215。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_fwk_file_parser.py)（implementation）：200–283。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py)（implementation）：304–305、355–356、389–406、435–461、515–547。
