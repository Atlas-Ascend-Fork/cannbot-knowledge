---
type: Guide
title: Profiler文本通信分析：分步、汇总比率与矩阵样本
description: 补齐文本通信JSON的输入、P2P名称分组、加和比率与未写回带宽，区分矩阵样本排序和真实吞吐。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_communication_parser.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_file_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_file_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_communication_parser.py
  role: implementation
created_at: '2026-11-11T05:56:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler文本通信分析：分步、汇总比率与矩阵样本

固定PyTorch主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`与发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`。完整核对CommunicationParser：主线287行、发布286行；主线全文、所有发布raw差异与完整AST定义逐项对照，变化的run和类型回落函数按完整文本核对。仅日志与发布额外未知类型告警不同，核心聚合分支一致。整卡draft/空平台，未解析采集数据或执行上游。

本卡补文本communication.json/communication_matrix.json入口及完整汇总链；Db关联/矩阵共有样本规则复用[数据库归因](torch_npu_profiler_database_trace_and_communication_attribution.md)，本地JSON不是对全部跨rank通信或链路性能的认证。

## step列表、闭区间和无数据

构造器初始化空step_list、合成root和空kernel字典。run初始化日志，先取TREE_BUILD_PARSER和RELATION_PARSER建立step，再顺序生成通信JSON和矩阵JSON；异常返回FAIL/None，无异常返回SUCCESS/None。树非空但kernel字典空会记错误，仍调用get_step_range；缺step则回落一个step_id=None、[0,+inf]且comm_ops为空的窗口。

通信分析输入为空时直接不写该JSON，矩阵输入为空也直接返回；两个输出互不代替，SUCCESS不证明二者均存在。FileManager.create_json_file对空data同样直接返回，已有旧文件不会由这条空分支自动清理。

split_comm_op_by_step以Communication Time Info里的Start Timestamp(us)经convert_us2ns转ns，按首个start<=ts<=end归步。**若step_list恰一项，先把全部communication_data直接赋给该项comm_ops，再继续扫描时间。** 所以单step路径并非严格过滤到窗口；多个step才仅保留命中项。该引用也保留原输入对象，不是深复制。start缺失不补0，转换错误可让run失败。

输出step名字用truthy step_id拼`step`前缀；无/假值则用`step`。矩阵若所有step的comm_ops都为空，会把全部原矩阵放到`step`；否则遍历step_list，归入首个comm_ops包含该操作名的step，没有自己再按矩阵时间分步。重复step标签/操作名及跨界记录要回查，不从输出键名推断全量时间裁剪。

## P2P和total是名称分类

操作名先lower；hcom_send、hcom_receive、hcom_batchsendrecv前缀归p2p，total前缀丢弃，其余一概collective。该分组不是设备P2P能力探针，也没有认证所有未知名称都是集合通信。

get_comm_type用本地正则的第一个匹配，未命中才取`__`前缀，发布额外告警。正则存在短候选先行：reduce在reducescatter之前、alltoall在alltoallv/alltoallvc之前，不能把结果说成总是最长完整通信类型。分组key由(匹配类型, 名称最后一个@后缀, link)组成；并向原link数据写Op Name为第一个@前缀。类型/group/link的解析没有转义或完整schema校验。

## 时间总和与没有保存的带宽结果

compute_total_info分别给p2p/collective追加Total Op Info；空组不追加。时间字段除Wait Time Ratio、Synchronization Time Ratio、Start Timestamp外直接累加，没有时间区间并集。两个比率重新算为：

```text
Wait Time Ratio = wait / (wait + transit)
Synchronization Time Ratio = synchronization / (transit + synchronization)
```

compute_ratio在分母绝对值<1e-15时返回0，否则round到4位；没有把输入采集完整性编码到这个0。带宽按transport分组，只加Transit Time(ms)、Transit Size(MB)与Size Distribution的两个槽；分布结构/数值无额外校验。

**compute_bandwidth_ratio只调用compute_ratio，返回值没有写回bandwidth_dict。** 因而该文本Total Op Info不能被描述为这里已保存重新计算的Bandwidth(GB/s)。类中另一个compute_total_link_info会按link累加size/time、后写transport，并明确存sum(size)/sum(time)到带宽字段；但本模块generate路径没有调用这个方法，不把它的写回作用套给上面的文本总和。

## 矩阵样本及解释边界

get_matrix_ops_dict先分p2p/collective，再按类型/group/link聚合样本。integrate_matrix_data原地按已有Bandwidth(GB/s)降序，取top1、索引len//2的middle、bottom1；数量足够再取bottom2/3。这是按带宽排序后的样本，不是按时间次序、耗时最大者或分位数插值。

total带宽为sum(Transit Size(MB))/sum(Transit Time(ms))，transport取最高带宽样本；本地不按transport另分组、不做重叠时间并集或各带宽算术平均。top/middle/bottom可能引用同一原对象，原始通信信息还会被补Op Name并排序；不能把这些输出视作互不重叠的独立通信量再相加。

实际诊断先核原记录数、单位、step、group/link、unknown名称和传输类型，再读比率。缺JSON/零分母/缺归步不是“通信零成本”，total与样本极值也不直接给出硬件峰值、模型独占带宽或通信暴露关键路径。未做数值、吞吐或解析复现。

## Evidence

- [ac0e156 _communication_parser.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_communication_parser.py)：范围 1–287。
- [ac0e156 _constant.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py)：范围 282–294。
- [ac0e156 _file_manager.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_file_manager.py)：范围 79–84, 86–99。
- [f3ecfe4 _constant.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py)：范围 277–289。
- [f3ecfe4 _file_manager.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_file_manager.py)：范围 91–96, 98–111。
- [f3ecfe4 _communication_parser.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_communication_parser.py)：范围 1–286。
