---
type: Guide
title: Profiler算子耗时解析：Host扣减、设备累加与队列关联
description: 核对operator_details.csv的Self/Total算式、HostToDevice与队列映射，区分缺失关联、跨流重叠及两版线程匹配。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_operator_view_parser.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_operator_view_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_torch_op_node.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_torch_op_node.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_tree_builder.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_tree_builder.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_fwk_cann_relation_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_fwk_cann_relation_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_fwk_file_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_fwk_file_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_cann_file_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_cann_file_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_event_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_parser_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_parser_deps_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prepare_parse/_fwk_pre_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prepare_parse/_relation_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_node_info_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_event_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_node_info_bean.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
created_at: '2026-11-10T12:49:51Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler算子耗时解析：Host扣减、设备累加与队列关联

## 导出入口与版本

本卡定向审阅TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的文本operator_details.csv调用链，对照发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的算式与队列关联。两版OperatorViewParser和TorchOpNode完整AST相同；以下明确指出TreeBuilder的线程差异，不宣称全部Profiler解析器相同。整卡平台未知，保持draft、空平台，没有导入上游、解析采集数据或运行设备实验。

Text配置列入OperatorViewParser。带CANN的依赖链将Torch算子树、CANN timeline、relation与Torch算子数据交给它；框架单独导出则可直接用Torch数据重建树。TreeBuildParser把enqueue数据交给FwkFileParser，RelationParser把dequeue数据交给FwkCANNRelationParser。这里只说明已注册的消费路径，不保证采集活动、Level或原始数据已满足。

FwkFileParser在未采CPU activity时不给出Torch算子树。OperatorViewParser没有节点时直接返回，不应把缺少CSV解释成模型没有算子；有节点但没有关联Kernel时，设备求和会得到0，仍不证明设备未执行。[数据库关联与单位](torch_npu_profiler_database_relations.md)和[采集/解析开销](torch_npu_profiler_measurement_overhead.md)继续独立适用，本卡只讲该文本视图的具体算式。

## Host Self扣直接子节点，不是CPU利用率

TorchOpNode定义Host Total为该框架事件记录的dur，Host Self为dur减去直接child_list中各事件dur之和；不是再次扣全部后代，也没有在这里求时间区间并集、按线程CPU占用分摊或排除阻塞等待。两值以ns取得，CSV层转为us。

因此父子Total存在包含关系，不能将各行Total相加得到完整训练步Host时长；Self也不是线程忙碌百分比或“纯算子计算”。发生嵌套、缺事件或异常重叠时，先检查树和原始区间，再解释差值；该算式本身没有替分析者证明数据覆盖完整。

CSV逐框架算子输出，移除虚拟root，名称包含ProfilerStep#的节点不单独写该表。它不是按同名算子自动求平均的分组统计，也不是业务step wall time。

## Device值为关联Kernel dur的算术和

每个节点分别按corr_id_self与corr_id_total取Kernel列表，直接相加float(kernel.dur)。With AICore列仅对原事件args中Task Type等于AI_CORE的子集求和，不等于硬件利用率或所有设备工作都已采全。EventBean的Kernel dur原单位为us，CSV没有再按Host的ns转换一次；匹配用的ts则会转成ns。

Self对应直接归属的关联，Total含沿父链传播的关联；不能相加Self与Total，也不能再把AICore子集当额外时间。求和没有按多个stream的执行区间合并，也没有在本循环做Kernel唯一性去重，因此重叠任务的dur和可以超过同窗口经过的时间，重复关联也需要回查。Device Total并不是最早Kernel开始到最晚结束的跨度，更不是跨流关键路径。

Host和Device字段来自不同层事件，异步执行允许二者重叠，不能直接相加推导端到端训练时长。若想解释Host空隙或通信暴露时间，应继续看原始时间线与step范围，不能只看这一行CSV。

## 从HostToDevice flow到队列corr_id

CANN解析先按HostToDevice flow id收集start/end，在end端用(pid,tid,ts)精确找对应X事件，最后以start端时间（转ns）作为字典键保存Kernel。缺start/end或找不到对应Kernel时不会虚构配对；未匹配Kernel可产生警告。它不是按算子同名或“找最近Kernel”建立关系。

有dequeue区间时，combine_kernel_dict按ACL开始时间排序，扫描区间，将处于dequeue起止内的ACL条目转到该dequeue.corr_id下；落不到这些区间的条目没有本函数的最近邻回退。无dequeue数据时原样返回以ACL时间为键的字典。

框架enqueue/dequeue区间来自同tid及origin_name的start/end标记配对，dur是各自end-start，不是此处计算enqueue到dequeue的排队等待。end没有找到start时计失败并跳过；存在OP_MARK文件这一has_task_queue_data判据，也不独自证明所有标记完整配对。

OperatorViewParser仅在has_task_queue_data为假时，按ACL时间沿树补归属。已有标记文件但数据缺失/配对失败时，不能预期这条无队列分支一定补齐设备关联；应检查原始标记、失败日志与flow，而不是将设备0解释成零成本。

## 主线新增enqueue线程一致检查

TreeBuilder按时间把Torch事件和enqueue事件放进树。主线只在当前节点存在event且tid等于enqueue.tid时更新其corr_id；发布版在相同位置直接update_corr_id，没有这项检查。主线中不同线程未附着该节点的enqueue，不应靠时间邻近强行补给它。

update_corr_id把id放入当前节点Self，并沿父链加入Total；无队列的时间补归属则把id加到路径各层Total，最深命中节点Self。两版后者方法AST相同。发布combine_kernel_dict用sorted(list(keys))，主线用sorted(keys)，这处书写差异不算算法升级；发布标记配对与CANN flow选择的所审主体规则相同，日志措辞有差异。

这些局部规则不证明所有跨线程、跨stream或嵌套场景都能完整归因。定位优化优先级时保留revision、Text/Db模式、CPU/NPU活动、OP_MARK及配对失败、HostToDevice flow、原始dur单位、Self/Total包含关系和真实时间线；确认关联后再决定是Host准备、队列等待还是设备执行问题。本卡没有新增verified或性能收益结论。

## 事件Bean的混合单位与可变引用

两版EventBean、NodeInfoBean与TorchOpNode已补全文本/完整AST对照。EventBean保留传入字典引用，device_id初始化为-1；ts把输入us经convert_us2ns转换为ns，缺ts按0，dur却原样get默认0，仍是us。end_ns使用`ts + int(raw_dur*1000)`，不是对dur调用同一个十进制转换函数；不应把字符串dur的注解当成所有getter都已安全数值化。pid缺省空字符串、tid缺省0、name缺省空字符串、id缺省None均按原类型返回。

unique_id拼接pid、tid、转换后的ts，未加入device、name或原flow id，不能证明跨设备/同刻事件全局唯一。is_ai_core仅在args中的Task Type精确等于AI_CORE时成立，缺args为False。字典后续修改会影响未缓存的getter。

NodeInfoBean保留原Kernel列表引用，构造时计算device_dur为各float(dur)之和，device_dur_with_ai_core为同条件子集之和；最早时间取min(kernel.ts)，最晚时间取max(kernel.ts+convert_us2ns(kernel.dur))。空列表会在min/max失败，没有空事件返回零的分支；列表之后被修改也不重算这些缓存。跨度、累加值和AICore子集是不同概念，仍未做去重或时间并集。

## 树节点查找和corr传播的本地边界

TorchOpNode的event、parent、children、corr_id_self和corr_id_total均保留可变引用/列表。pid/name/inputshape/callstack/start/end转发到event，输入shape缺省空字符串；虚拟root的event=None不支持任意这些getter。add_child_node只append，不替child重写parent、不排序、不验包含。

match_child_node用二分定位开始时间不晚于查询值的最右候选，前提是child_list已按开始时间排序。**它没有独立校验首个child的开始下界**；查询早于首个child开始时仍可能选首项，只要该项end大于查询值。结束边界使用严格`end > ts`，相同结束点不匹配；不要将该方法描述为任意输入下健壮的闭区间查找。

is_profiler_step判断名称中是否包含ProfilerStep#，不是仅判断前缀。update_corr_id先append当前Self，再在仍有parent时向当前及非root祖先的Total append；虚拟root不加Total。update_corr_id_self/total也只append，不去重。上述列表、顺序、下界和root行为没有由类型注解保证，分析异常Self/Total或重复关联时应保留这些原始条件。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_operator_view_parser.py)（primary）：定向范围14–80。
- [固定实现来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_operator_view_parser.py)（implementation）：定向范围14–80。
- [固定实现来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_torch_op_node.py)（implementation）：定向范围37–100。
- [固定实现来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_torch_op_node.py)（implementation）：定向范围37–100。
- [固定实现来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_tree_builder.py)（implementation）：定向范围11–52。
- [固定实现来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_tree_builder.py)（implementation）：定向范围11–51。
- [固定实现来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_fwk_cann_relation_parser.py)（implementation）：定向范围20–35, 51–60。
- [固定实现来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_fwk_cann_relation_parser.py)（implementation）：定向范围20–35。
- [固定实现来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_fwk_file_parser.py)（implementation）：定向范围46–98, 167–168。
- [固定实现来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_fwk_file_parser.py)（implementation）：定向范围46–98。
- [固定实现来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_parse/_cann_file_parser.py)（implementation）：定向范围188–238, 264–265。
- [固定实现来源 12](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_parse/_cann_file_parser.py)（implementation）：定向范围127–167。
- [固定实现来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_event_bean.py)（implementation）：定向范围15–59。
- [固定实现来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py)（implementation）：定向范围79–79, 258–265。
- [固定实现来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_parser_config.py)（implementation）：定向范围43–59, 117–121。
- [固定实现来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_parser_deps_config.py)（implementation）：定向范围24–39, 72–78。
- [固定实现来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prepare_parse/_fwk_pre_parser.py)（implementation）：定向范围54–71。
- [固定实现来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/prepare_parse/_relation_parser.py)（implementation）：定向范围24–39。

本文所依据的完整模块与有界辅助来源如下；未列完整范围的依赖保持独立待审，固定提交不等于设备验证。

- [ac0e156 _event_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_event_bean.py)：1–59。
- [ac0e156 _node_info_bean.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_node_info_bean.py)：1–42。
- [ac0e156 _torch_op_node.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_bean/_torch_op_node.py)：1–100。
- [f3ecfe4 _event_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_event_bean.py)：1–59。
- [f3ecfe4 _node_info_bean.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_node_info_bean.py)：1–42。
- [f3ecfe4 _torch_op_node.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_bean/_torch_op_node.py)：1–100。
- [ac0e156 _constant.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py)：268–279、282–294、79–79。
- [f3ecfe4 _constant.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py)：263–274、277–289、79–79。
