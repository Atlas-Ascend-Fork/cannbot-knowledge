---
type: Guide
title: Profiler分类内存时间线：版本迁移、字节累计与导出差异
description: 区分raw纳秒有符号事件与汇总微秒类别字节，解释PREEXISTING、版本迁移、前导零列和HTML独立分配器峰值。
tags:
- task.debugging
- topic.performance.analysis
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_memory_timeline_parser.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_memory_timeline_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_parser_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
created_at: '2026-11-10T13:11:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Profiler分类内存时间线：版本迁移、字节累计与导出差异

## 从已采数据导出，不是实时allocator快照

本卡完整阅读固定主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`的1099行本地内存时间线模块，并逐行、完整AST对照发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`。两版去行尾空白后相同，严格AST仅有CategoryElement说明docstring尾空格不同；时间线、大小与导出本地规则相同。本轮配套补全分类和数据流主题，不据此声称外部EventTree/运行环境schema或真实归因完全一致。整卡平台未知，保持draft、空平台，未执行上游、采集解析或导出。

公开export_memory_timeline先检查record_shapes/profile_memory及with_stack或with_modules、有效采集路径，再调用专门分析入口；没给device时根据当时NPU可用性选npu:0或cpu，不是自动选择本次数据量最大的设备。具体采集/产品条件沿用[时间线文档](torch_npu_profiler_memory_and_metadata.md)，不从实现推导额外产品支持。

MemoryTimelineParser按后缀先选html，再选raw.json.gz，否则走汇总JSON（.gz时压缩）。导出方法在没有匹配数据时可以只打印错误并return，外层run仍可成功返回；返回None或分析状态没有异常不能独立证明文件已生成，应检查实际产物。

## 事件身份、大小和PREEXISTING

TensorKey含设备类型/索引、tensor id和Storage；Storage的相等/哈希按allocation_id，指针用于关联检查，不能只按相同ptr把多次生命周期合并。无法取得完整TensorKey的分配记录另按(ptr,device)追踪，分类落Unknown，而不是自动判成模型激活或泄漏。

StorageSizeDict先由Tensor元数据的shape元素乘dtype_size估算，每个key保留所见最大逻辑大小；随后每个key首次所见的可关联Allocation事件绝对字节数（setdefault）覆盖估算，缺key默认0。它不是对任意stride/view存储跨度或底层allocator保留量的完整重建，输入元数据和分配事件的完整性会影响曲线。

未在窗口观察到create但已有version0 Tensor分类时，timeline补时间戳-1的PREEXISTING；Unknown释放若没有对应live创建，也补PREEXISTING后再DESTROY。-1是预存基线，不是实际申请于负时间或原始采集前的精确申请时刻。PREEXISTING不等于泄漏，缺采窗口与长期存活应分别核对。

## 版本增长迁移类别，不增加同一字节两次

timeline按时间及Action值排序。Action值为0=PREEXISTING、1=CREATE、2=INCREMENT_VERSION、3=DESTROY；create/preexisting加字节，destroy减字节。Tensor原地变更产生版本增长时，从旧version类别减去numbytes，再向新version类别加同样字节。

因此INCREMENT_VERSION可以只是类别迁移，不是新增同等分配。raw导出会为它写两行同时间/同action的负、正字节；不能把raw绝对值相加当成新增显存。Unknown的DeviceKey也不应凭action名字强行猜出Tensor版本身份。

类别来自另一套Python tracer/dataflow/梯度等推导。本轮分类规则已完整静态补到[类别推断](../../../../training/guides/torch_npu_profiler_memory_category_inference.md)，schema与版本边界补到[数据流合同](torch_npu_profiler_memory_schema_and_dataflow_versions.md)；没有实际验证分类精度，Unknown比例变化不独自证明优化失效或内存泄漏。

## raw和汇总JSON的时间、列号不同

| 产物 | 时间与数值 |
| --- | --- |
| raw.json.gz | 每行(timestamp_ns, action, signed_bytes, category_index)，保留-1预存标记；版本迁移写两行 |
| .json/.json.gz | [timestamps_us, sizes_by_category]；ns经int(ts/1000)转us，同一转换后时间在一行继续累计字节 |
| HTML | 汇总时间减最小值作为相对起点，再以ms画图；按类别cumsum并除1024^3成图示GB |

汇总中负时间基线被替换为扫描得到的最小有效时间；这不会恢复真实历史申请时间。多个ns事件可落在相同us行，基线和首个实际时间还可能显示在同一时间坐标；需要事件顺序时查看raw及准确单位，不将汇总采样点视作原始全部纳秒边界。

本快照的raw category_index顺序为Parameter=0、Optimizer State=1、Input=2、Temporary=3、Activation=4、Gradient=5、Autograd Detail=6、Unknown=7，来自颜色字典插入顺序，不是Category Enum.value。汇总sizes向量在这八列前另有恒0前导列，真实类别索引要加1；该首列不是总字节或Unknown。解析外部工具应按准确格式/版本处理，不用同一个列号同时读raw与汇总。

## 分类曲线与标题峰值是两条统计链

HTML堆叠来自上述事件累计；标题Max allocated/reserved则从memory_history逐Allocation事件的total_allocated/total_reserved分别取所选device最大值，缺历史默认0。它们没有要求等于分类堆叠的峰值，也没有把reserved自动分到Parameter等类别。

因此分类总量、allocated、reserved、active及整机设备占用不能互相替代。图中某类的转移可能来自version归因，标题峰值变化可能来自allocator历史；先核device/窗口和原事件，再关联[内存计数](torch_npu_memory_counters.md)或[OOM快照](torch_npu_oom_memory_snapshot.md)。本卡没有运行分类或验证数值，未新增verified、泄漏结论或性能数字。

## 分配记录、时间选择与缺失数据

MemoryProfile先从EventTree取roots，再建DataFlowGraph、StorageSizeDict和分类表；MemoryProfileTimeline构造时立即读取timeline、categories、memory_history。MemoryTimelineParser的deps_data不参与这里的计算；构造函数取device并初始化日志，run统一捕获Exception记录带堆栈错误后返回FAIL，无异常则SUCCESS。

可关联TensorKey的Allocation事件先按start_time_ns排序，再写入(key, is_allocation)到时间的字典；同一key/方向重复记录会以后写时间覆盖，不能把它读成全部malloc/free历史。无法关联TensorKey的分配按(ptr,device)跟踪：正大小首次产生CREATE，尚live时再次正大小产生INCREMENT_VERSION；非正大小走DESTROY，缺对应live时补PREEXISTING。重复未知申请仍按同一numbytes做类别迁移，不会据此重建实际扩容字节或修复不完整采集。

TensorDataFlow边的CREATE/DESTROY取上面的分配时间；变更取节点start_time_ns，DESTROY用该key快照中的最后版本。分配时间字典缺项没有本地补默认时间的保护，后续排序等可抛错并由run返回FAIL。不要从缺失数据推导“自动插值为正确申请时间”。

StorageSizeDict扁平化只处理直接Tensor和一层list输入；遍历PyCall时module_parameters非None就先走module分支，只有否则才走optimizer（含state）分支。逻辑大小由dtype_size逐尺寸相乘后按key取max；它不核任意递归输入、完整view跨度或allocator碎片。DeviceKey按设备类型/索引比较，TensorKey排序以id、allocation_id和设备组成，Storage相等/哈希只按allocation_id而非ptr。

## 设备字符串和HTML失败边界

_parse_device_info对恰等于`cpu`的字符串直接选CPU/-1；其他输入先整体strip再按冒号拆成两段，类型只需在cpu/npu字典内，索引由int转换。它不校验索引存在、非负或设备可用性，所以`cpu:-1`、`npu:-1`可被语法接受；` cpu `不会命中裸cpu分支且因无冒号返回空结果。类型或段数不符打印错误，索引ValueError只返回None。

汇总累计每次遇到不同的转换后us时间就复制前一向量；遇到相同us则继续在末行更新。最小时间逻辑以-1为哨兵且只用正候选缩小已设值，不是通用历史基线恢复；若没有正的实测时间，不能假定补出的基线一定成为正常时间点。

HTML生成会动态import matplotlib.pyplot；仅ModuleNotFoundError被_draw_memory_timeline局部捕获并打印后返回None，其他绘图/import错误交给run外层。它生成PNG后base64嵌入HTML；本地没有显式plt.close，也没有在此处包统一finally资源清理。JSON写文件、路径处理、numpy与matplotlib内部实现不是本卡的整文件覆盖对象。选错设备、无匹配数据、缺matplotlib都可能无产物而run不报FAIL，应核文件存在、格式和单位，不能只看返回状态。

## Evidence

- [ac0e156 _memory_timeline_parser.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_memory_timeline_parser.py)：直接证据范围 1–142, 217–278, 585–680, 869–1099；main complete 1099-line raw text read; release all raw line deltas checked, rstrip-lines exact; strict AST differs only one CategoryElement docstring trailing space; local technical meaning preserved。
- [f3ecfe4 _memory_timeline_parser.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_memory_timeline_parser.py)：直接证据范围 1–142, 217–278, 585–680, 869–1099；main complete 1099-line raw text read; release all raw line deltas checked, rstrip-lines exact; strict AST differs only one CategoryElement docstring trailing space; local technical meaning preserved。
- [ac0e156 profiler.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/profiler.py)：直接证据范围 153–174；bounded old API/config/units facts independently reread; preserve original source and scope。
- [ac0e156 _parser_config.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_config/_parser_config.py)：直接证据范围 98–100, 120–123；bounded old API/config/units facts independently reread; preserve original source and scope。
- [ac0e156 _constant.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py)：直接证据范围 35–36, 87–90；bounded old API/config/units facts independently reread; preserve original source and scope。
- [f3ecfe4 _constant.py](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py)：直接证据范围 38–39, 87–90；bounded exact release time and byte units。
