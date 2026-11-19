---
type: Guide
title: Profiler框架输入与关联：文件选择、队列、API和step边界
description: 核对固定版本Fwk/CANN/Relation完整本地解析，解释文件选择、flow覆盖、前反向连接、MSTX分类及step首末桶边界。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_fwk_file_parser.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_cann_file_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_fwk_cann_relation_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_cann_file_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_fwk_cann_relation_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_fwk_file_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_torch_op_node.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_torch_op_node.py
  role: implementation
created_at: '2026-11-11T04:51:34Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler框架输入与关联：文件选择、队列、API和step边界

## 固定版本与入口范围

本卡完整核对TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`和发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的FwkFileParser、CANNFileParser与FwkCANNRelationParser；两版分别读全文，真实差异见下文。平台未知保持draft，没有导入上游、读取实际采集、运行SQL或调用清理方法。prof_parse的init仅`__all__=[]`，不会自动运行这些解析器。

这里只关闭三个本地模块，PathManager、时钟配置、TraceEventManager、ID管理器、文件读取和外部CANN采集仍按各自来源审阅。记录字节布局、单位和CSV投影见[框架Bean解码](torch_npu_profiler_framework_bean_wire_formats.md)、[指标CSV](torch_npu_profiler_csv_bean_projection_and_metric_boundaries.md)；本卡不把下游表结构、活动配置或文件存在当成数据完整证明。

## 文件发现没有最新或完整性选择

FwkFileParser先取得framework路径，再用os.listdir遍历realpath中的常规文件，按FwkFileParserConfig正则匹配。每个tag用setdefault保留**首先遇到的文件**，本方法不排序、不按时间挑最新、不合并同tag多个分片。目录枚举/路径发现发生在logger初始化之前，也没有本地统一catch；不能把这类失败混成get_file_data_by_tag的空列表。

get_file_data_by_tag无该tag文件返回[]；有文件才读二进制，取登记bean/is_tlv/struct_size交对应Decoder。没有在本方法验证checksum、schema或未知tag配置。has_task_queue_data只判断OP_MARK路径是否登记，未读文件内容；空文件或无成功配对仍可能使后续走“有队列”分支。

CANNFileParser从输出目录、analyze目录和database来源列表汇集路径，仅保留常规文件，依次re.match文件名并按类型写set。覆盖op_summary、npu_mem、msprof timeline、step_trace、GE memory/GE operator memory（含不带ge前缀的别名）、l2_cache、aicpu、communication.json、communication_matrix.json、API/OP统计、NPU模块内存、msprof数据库、communication_analyzer数据库以及NIC/RoCE/PCIe/HCCS。主线新增TASK_TIME=19和SOC_PMU=20及task_time/soc_pmu文件模式，并为四类互连增加slice模式；发布枚举到HCCS=18。正则是发现规则而非严格文件格式验证，多数没有末尾`$`，不能把匹配当完整扩展名或内容认证。

get_file_list_by_type交回内部set（缺类型时新空set），不是不可变副本。get_timeline_all_data按set遍历合并所有timeline，方法不排序；get_analyze_communication_data对多个匹配文件仅取next(iter(set))，也没有最新文件保证。重复flow或相同事件键因此需要回查所选文件集合。

构造CANNFileParser先_file_dispatch再初始化logger，仅_check_cann_path_valid放在try中；缺CANN路径的RuntimeError被打印/记录，不是统一构造失败。发布在不可读/写时_check抛PermissionError并由这层捕获；主线改为warning继续检查，不执行日志建议的chmod。不得据对象已返回推定读取权限、路径和数据都有效。

## JSON形状与HostToDevice连接

_json_load空输入返回[]；坏JSON抛带错误码的RuntimeError；非list或第一项非dict返回[]，**没有逐项确认整个list都是dict**。_json_dict_load对应空输入/非dict返回{}，坏JSON报错，也不验证内部通信schema。后续循环仍可能因坏元素或字段类型失败。

combine_acl_to_npu按HostToDevice的id收集s/f端，缺id按0；同一id重复start或end使用setdefault，保留首个。所有ph=X事件以原始pid、tid、ts的字符串组合为键，重复键后者覆盖前者，不额外限定cat为某一种Kernel。随后用flow end同样的原始三字段键找X事件，找不到则计数warn并跳过；不做最近邻或同名回退，也不证明跨设备/进程全局唯一。

匹配后以flow start的us转ns作为ACL字典键，append EventBean；相同ACL起点可包含多个事件。这里匹配用的原始ts表示，与EventBean.unique_id的转换后ns字段不是同一个构键步骤。没有flow或X会记诊断；缺一端的flow不输出。两版主体规则一致，主线日志更详细，不能由诊断文本变化推导关联算法升级。

get_localtime_diff用ast.literal_eval读取start info，计算`convert_us2ns(CANN_BEGIN_TIME)-int(CANN_BEGIN_MONOTONIC)`；缺CANN路径或start info直接返回0，异常记录后保留默认0。这不是已经测得零时差的保证。del_summary_and_timeline_data逐device路径向remove_path_safety提交summary/timeline删除；del_output_path_data提交输出目录删除，这些是显式方法，普通读取不自动调用，本次没有执行它们，外部路径安全实现未因此完成覆盖。

## OP_MARK配对与文本事件

get_task_queue_data先按time_ns排序，再分别按TID和origin_name维护enqueue/dequeue的开始列表。结束标记pop最后一个开始，给**结束Bean**写ts=start、dur=end-start，append结果后把同桶其余开始全部clear。没有开始的结束计失败并跳过；剩余未结束的start不在本方法计入同样的失败数。输出随结束标记到达顺序生成，不在末尾另按ts排序，也不验证所有嵌套区间完整。corr_id不参与寻找这个start的桶键。

get_torch_op_tree_node和get_fwk_trace_data都先要求CPU activity。前者无Torch数据返回[]；后者从首Torch或首队列事件选择用于元数据的PID，三类都空时返回[]。文本依次生成Torch X、dequeue X+flow end、enqueue X+flow start，并按corr_id从dequeue原名补enqueue显示名；tid_dict中dequeue标True、Torch/enqueue标False，后写可覆盖同TID标志。生成阶段先调用Python重放以更新tid_dict，再生成进程/线程元事件和前反向flow；最终列表先extend这些元事件与flow，再extend Python，最后追加GC。这里区分生成阶段与最终追加顺序，TraceEventManager实际时间/ID编码另计。

Python文本需要hash和函数记录都非空才交PythonTraceParser，未传参数Tensor记录；原始重放边界见[Python与事件树](torch_npu_profiler_python_replay_and_event_tree.md)。get_first_fwk_op返回ts最小项，空输入None，并不直接返回原列表首项。

## 数据库API的ID、MSTX与前反向选择

get_fwk_api同样要求CPU activity及至少一种框架事件。使用选定的一个PID与各事件TID调用contact_2num；本地未按每条记录重新选择PID或校验混合进程数据。先把字符串管理器起点设为FWK API命名空间，依次构造任务队列、Torch/MSTX、Python的11槽记录。Torch槽为开始ns、结束ns、合并PID/TID、连接ID列表、name字符串ID、sequence、forward_tid、dtype字符串ID、shape字符串ID、callchain ID、ApiType；可空输入字段不创建对应ID。队列槽的连接ID用corr_id加FWK偏移交ConnectionIdManager，其他未使用槽为None；队列显示名同文本路径补原名。

主线以`name.startswith("mstx_")`将Torch行分入MSTX；发布只匹配`name == "mstx_mark_op"`。分入MSTX的行不加入普通Torch数组及前反向索引；后续MSTX/CANN实际连接还需[数据库trace关联](torch_npu_profiler_database_trace_and_communication_attribution.md)的条件，不能把名称分组当作已关联成功。

filter_fwd_bwd_event按非负sequence分组，forward_tid==0为start，否则end；文本保存pid/tid/ts并用ts挑更晚候选。**API分支filter_fwd_bwd_api却只保存idx，没有把比较所用ts写回**；在get_fwk_api新建的字典路径，后续同侧候选读取默认负无穷，因而可由遍历后项覆盖，不是已经实现了同样的最大ts选择。不要将两方法的相似名字当成完全相同算法。

两侧都存在时update_fwd_bwd_connection_id把同一个新连接号append到两条Torch行的连接列表。起号来自enqueue corr_id最大值加1（无enqueue为0），随后加FWK偏移并递增；仅dequeue的大corr_id不参与这个max。本地没有对任意外部输入建立全局无冲突证明。Python API也要求hash+函数记录，交重放器生成，不在这里恢复参数Tensor。

get_gc_record_db_data输出GC开始/结束和原PID/TID合并值；trace路径选择第一个device id（无则INVALID_VALUE），通过get_pid_format改写GC Bean.pid再生成X与元事件。GC的tid不会因此同步变化，见Bean的pid setter合同；两种出口的进程标签和单位转换不能混为一项。

## 队列关联与step仅取首末非空桶

FwkCANNRelationParser无dequeue时原样返回以ACL开始ns为键的字典；有dequeue则排序ACL键，单个向前游标按`dequeue.ts <= ACL <= ts+dur`将Kernel扩入corr_id桶。它不排序dequeue输入、不处理任意乱序/重叠的完整区间并集，区间外条目没有最近邻补配。发布sorted(list(keys))与主线sorted(keys)同排序语义。

get_kernel_dict先取CANN flow；非LEVEL_NONE且字典空时打印错误并返回空，否则交上面的组合。get_step_range只选root的直接child中名称包含ProfilerStep#的节点；kernel字典或step列表空则[]。无OP_MARK登记文件时，排序ACL键并按step起止闭区间补corr_id_total；存在OP_MARK文件时不启动这条补充路径。

每个step对corr_id_total排序，找首个及末个有Kernel的**关联桶**：开始取首桶Kernel最小ts，结束取末桶Kernel最大end_ns，再与Host step.end取max；首桶缺失回退Host start，末桶缺失用INVALID_VALUE后再比较。不是遍历全部Kernel求全局最早/最晚，数字corr_id顺序也未在这里被证明等于设备执行顺序，跨stream任务尤其不能由这个范围直接推出关键路径。无任何corr_id_total的step会跳过；step ID取名称最后一个#后的字符串，COMM_OPS初始化空字典、保留FWK_START_TS。

结合[Host/Device耗时](torch_npu_profiler_operator_time_attribution.md)及[step指标](torch_npu_profiler_step_interval_aggregation.md)分析时，先保留文件选择、CPU活动、OP_MARK存在/配对覆盖、flow重复与缺端、PID/TID、时钟和桶排序，再判断空值或跨度。这里没有测得优化收益或硬件支持，也不把局部返回成功登记为全部Profiler已覆盖。

## Evidence

- [ac0e156 _fwk_file_parser.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_fwk_file_parser.py)：完整本地模块1–312。
- [ac0e156 __init__.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/__init__.py)：完整本地模块1–1。
- [ac0e156 _cann_file_parser.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_cann_file_parser.py)：完整本地模块1–323。
- [ac0e156 _fwk_cann_relation_parser.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_fwk_cann_relation_parser.py)：完整本地模块1–105。
- [f3ecfe4 __init__.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/__init__.py)：完整本地模块1–1。
- [f3ecfe4 _cann_file_parser.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_cann_file_parser.py)：完整本地模块1–238。
- [f3ecfe4 _fwk_cann_relation_parser.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_fwk_cann_relation_parser.py)：完整本地模块1–105。
- [f3ecfe4 _fwk_file_parser.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_fwk_file_parser.py)：完整本地模块1–297。

- [ac0e156 TorchOpNode.is_profiler_step](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_torch_op_node.py)：70–71；名称包含ProfilerStep#判据，依赖文件其余定义不由本卡升级。

- [f3ecfe4 TorchOpNode.is_profiler_step](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_torch_op_node.py)：70–71；名称包含ProfilerStep#判据，依赖文件其余定义不由本卡升级。
