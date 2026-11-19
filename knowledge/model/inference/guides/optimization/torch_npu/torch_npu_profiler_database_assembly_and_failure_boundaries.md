---
type: Guide
title: Profiler数据库装配：输入迁移、落库事务与部分失败
description: 梳理双版本DbParser调度、基础元数据和GC落表流程，并整合SQLite连接句柄、逐批提交、空结果歧义与句柄生命周期；区分解析成功、缺表、单项失败及文件迁移的实际边界。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_db_parser.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/prof_db_parse/_db_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_basic_db_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/prof_db_parse/_basic_db_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_gc_record_db_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/prof_db_parse/_gc_record_db_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_base_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_base_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_fwk_file_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_db_manager.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_db_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_singleton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_singleton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_file_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_file_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
created_at: '2026-11-11T03:55:41Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler数据库装配：输入迁移、落库事务与部分失败

## 固定模块与范围

本卡完整审阅TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 和发布 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 的DbParser、BasicDbParser、GCRecordDbParser、BaseParser，以及prof_common_func的_db_manager.py、_singleton.py数据库管理器实现。DbParser调度数据库生产，不是数据库文件的只读查询接口。新知识产品与完整配套未知，保持draft/空平台；只静态读文本/AST，没有构造或运行上游解析器、SQL、文件迁移、SQLite或采集。

BaseParser保存原param_dict引用，提取profiler_path/output_path与export_type。是否有CANN路径决定从COMMON_CONFIG还是ONLY_FWK_CONFIG取依赖/模式，缺项默认SUB_PROCESS及空依赖，再交给ConcurrentTask；不是复制一份独立输入配置，也不在这里确认调度成功。调度器、路径发现及数据库管理器仍是独立依赖。

## DbParser的顺序和返回值

run先load_info，再以rank决定汇总名：rank_id=-1使用默认数据库名，否则为`ascend_pytorch_profiler_<rank>.db`；分别初始化TorchDb与AnalysisDb输出路径。这些操作位于子parser循环的try之前，其失败不自动经过后面的FAIL返回和finally。

基本顺序为Basic→FwkApi→Memory→GCRecord→StepInfo。只有存在CANN路径且Level不是None，才追加Communication和TraceStepTime两个分析表parser。逐个构造并传同一个deps_data，返回数据以`setdefault(name,data)`登记，已有同名依赖不会被覆盖。单个parser返回非SUCCESS仅打印错误并继续；只有循环中的异常才让DbParser返回FAIL。finally关闭两个DB连接，正常走完循环返回SUCCESS。因此总流程成功不能证明所有子表都存在、每行完整或各子parser均成功。

- [trace关联、step与通信归因](torch_npu_profiler_database_trace_and_communication_attribution.md)
- [内存组件和GE配对](torch_npu_profiler_pta_ge_memory_merge.md)
- [迭代区间聚合](torch_npu_profiler_step_interval_aggregation.md)

## 基础输入迁移与元数据

BasicDbParser按目录原始遍历顺序寻找首个匹配`^msprof_\d+\.db$`的CANN文件，先在CANN根找，未找到再去mindstudio_profiler_output目录。每个候选调用check_db_file_vaild，RuntimeError会告警后跳过；这里没有排序或合并全部候选。匹配后以`shutil.move`移至TorchDb目标，再连接，故实际运行会移动输入文件。外部文件验证、move冲突和SQLite事务语义不由本地调用保证。

后续按以下顺序写入：

| 本地方法 | 具体边界 |
| --- | --- |
| create_ascend_db | 连接失败抛RuntimeError，由run捕获为FAIL。 |
| save_rank_info_to_db | 建RANK_DEVICE_MAP并先清空已有数据；每个发现的device写rank-device对，没有device写INVALID_VALUE。不是保留msprof原映射。 |
| save_host_info_to_db | HOST_INFO已存在则直接返回；否则调用get_host_info保存host_uid/name，不在此刷新旧表。 |
| save_env_vars_info_to_db | 调collect_env_vars，将其ENV_VARIABLES值JSON编码写META_DATA；只确认调用与编码，不认证外部收集名单。 |
| save_profiler_metadata_to_db | 缺profiler_metadata.json或JSONDecodeError仅告警并返回；合法JSON对象逐项把key转str、value转JSON保存。其他结构/异常可使run失败，已发生的文件迁移或写入没有本地统一回滚。 |

主线与发布的基础流程相同；差异是日志级别/文字和正则的raw-string写法，所读正则内容相同。日志变化不能被提升成新增支持或字段变化。

## GC落表与缺失

GCRecordDbParser先连接TorchDb，再调用FwkFileParser.get_gc_record_db_data；所读主线生产函数把GC事件转为`[ts,ts+dur,contact_2num(pid,tid)]`，无事件返回空列表。只有列表非空才建GC_RECORD并插入；空数据可返回SUCCESS但不新建表。任意捕获异常返回FAIL/None；这不是Python未发生GC或设备内存已释放的证明。字段单位与采集阈值沿[GC和Host诊断](torch_npu_profiler_gc_and_host_system.md)分别核对。

## 连接失败与空句柄

create_connect_db对已存在路径先调用FileManager.check_db_file_vaild，这在sqlite try之外。连接实际参数是timeout=2147483、check_same_thread=False；注释称int max，不能据注释改写实参或把长锁等待视为无锁保证。connect或cursor创建抛sqlite3.Error会返回两个EmptyClass，__bool__恒False、__str__为空，虽保存_info也不通过这些方法展示失败详情；cursor创建失败分支未在本地关闭刚建连接。DbParser的finally对两个DB连接调close，若连接已是这类假句柄，close按句柄真值直接返回，不会在这里暴露失败原因。

发布在cursor之后还os.chmod(db_path, 0o640)，主线没有该本地操作；chmod的OSError不属于只捕sqlite3.Error的except，不保证变成假句柄。已有数据库和新建数据库都可能经过这一chmod。check_same_thread=False只是连接参数，不证明业务并发访问或所有调用者均串行安全。

## 逐批提交与部分成功

execute_sql/executemany_sql各取conn.cursor执行，再conn.commit，成功True；sqlite3.Error打印后False，没有rollback或统一关闭临时cursor。insert_data空data直接return，以首行长度生成?占位符，每10000行调用executemany_sql；一批成功就commit，后批失败抛RuntimeError但此前批次不会在本方法整体回滚。create_table_with_headers先查表，已存在直接return，不比较新headers是否与旧schema相同；未存在才把列名/类型拼进CREATE TABLE。clear_table_data空表名/表不存在直接return；存在则DELETE保留结构并经execute_sql提交。table_name、列标识等在这些方法里直接拼SQL，不由值占位符替代标识符处理，也没有完整本地schema/行宽验证；这是调用者约束，不是任意外部输入的数据库接口。

judge_table_exist用sqlite_master查询，name使用?参数，返回fetchone()[0]的计数而非显式bool转换，sqlite3.Error包RuntimeError；创建、插入、清表对False结果再抛异常，不能概括所有DB方法只记日志不失败。对装配诊断的影响：save_rank_info/save_env_vars等写入按上述逐批语义执行，DbParser子循环的SUCCESS只说明调用未抛错，不证明每张表全部行都已提交；某一批失败后，此前批次可能已经留在数据库中，与基础写入一节“已发生的文件迁移或写入没有本地统一回滚”叠加。

## 空结果与失败的歧义

fetch_all_data实际FETCH_SIZE=10000，docstring的1000与代码不同。循环fetchmany后拼data，累计**超过**MAX_ROW_COUNT=100000000才警告并break，返回已累积行；它不是恰好截断在上限的完整结果保证，警告后返回也不附独立截断标志，短批次退出。sqlite3.Error则打印并返回[]，不能把空列表直接解释成真实事件数0；非sqlite错误不统一捕获。fetch_one_data分别捕execute与fetchone的sqlite错误并返回[]；正常无匹配行可返回None，正常命中是行对象，虽注解list也不保证统一list类型。下游把“表为空”当“没有事件”前，需要先排除这两类错误路径；调用者需区分错误日志、None和实际行，而非只对所有返回做同一种解包。

## 句柄生命周期与单例

BasicDb初始化db_path/conn/curs为空；init只在db_path为None时写路径，重复传新路径不会主动切换。create_connect_db已有真conn和curs就True，否则委托DbManager，按句柄真值返回成功；不能用曾调用init证明连接已经打开。其余表/插入/清表/fetch方法直接转发，不另加统一有效性验证。close先将db_path=None，再destroy_db_connect，之后才清conn/curs；若销毁抛错，可能留下“路径已清、句柄未清”的中间状态。destroy任一个句柄为假就return；否则先close cursor再close connection，cursor失败会阻止后一步；没有完整try/finally保证两者都关闭。

TorchDb与AnalysisDb各自经Singleton装饰、各继承BasicDb并调用基类初始化；同进程内不是每次new就得到独立数据库句柄（通用单例装饰器的按类缓存实现见固定来源_singleton.py）。排查同进程反复运行时应记录init/close及异常路径，勿把共享对象、commit成功或表存在各自当全部知识表已正确入库的证明。表级含义仍按[数据库关联](torch_npu_profiler_database_relations.md)等各parser合同解释。

## 验收

保留实际rank/device、CANN候选清单、迁移前后路径、每个子parser状态、已有依赖与最终schema；不要用单个SUCCESS、文件存在或空表代替完整性验收。无CANN、Level=None、缺元数据、空GC及解析失败要区分。数据库管理器的提交、冲突、空结果与句柄生命周期语义已并入本卡上节；调度器、原始采集及厂商导出仍需各自证据，未进行运行或性能验证。

## 完整数据库链与补充证据

- [固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_db_parser.py)（primary）：1–65。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/prof_db_parse/_db_parser.py)（implementation）：1–65。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_basic_db_parser.py)（implementation）：1–123。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/prof_db_parse/_basic_db_parser.py)（implementation）：1–123。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prof_db_parse/_gc_record_db_parser.py)（implementation）：1–51。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/prof_db_parse/_gc_record_db_parser.py)（implementation）：1–51。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_base_parser.py)（implementation）：1–44。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_base_parser.py)（implementation）：1–44。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_fwk_file_parser.py)（implementation）：290–294。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_db_manager.py)（primary）：1–236，全文。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_db_manager.py)（implementation）：1–237，全文。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_singleton.py)（implementation）：1–9。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_singleton.py)（implementation）：1–10。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_file_manager.py)（implementation）：170–176，有界辅助。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_file_manager.py)（implementation）：182–188，有界辅助。
- [固定实现](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py)（implementation）：27–30，有界辅助。
