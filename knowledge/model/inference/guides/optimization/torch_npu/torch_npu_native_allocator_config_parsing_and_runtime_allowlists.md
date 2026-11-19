---
type: Guide
title: TorchNPU原生分配器配置：解析状态、白名单与版本差异
description: 对照两版完整配置类，区分环境与运行时白名单、状态重置、数值单位及扩展段能力探针顺序，并给出分配器消费面的文档/实现对照证据。
tags:
- task.optimization
- topic.memory
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUAllocatorConfig.h
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUAllocatorConfig.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUAllocatorConfig.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUAllocatorConfig.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.h
  role: implementation
created_at: '2026-11-11T05:13:04Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU原生分配器配置：解析状态、白名单与版本差异

固定PyTorch主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf与发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b，完整读取两版NPUAllocatorConfig.h/cpp，并定向读取两版setAllocatorSettings完整函数。产品及部署配套未核对，本卡不作平台范围声明。选择开关和文档门槛复用[推理显存配置](../torch_npu_allocator_options.md)，本卡补充本地解析和状态消费者，不把“键被接受”当作设备支持或性能收益。未导入、构建或运行上游，也未执行地址保留探针。

## 两版入口与状态归属

主线类名为NPUAllocatorConfig。max_split_size、garbage_collection_threshold、expandable_segments、large_segment_size、roundup_power2_divisions、pinned_use_background_threads、max_non_split_rounding_size及两个pinned阈值getter先调用本类instance，再委托外部c10::CachingAllocator::AcceleratorAllocatorConfig。其余getter读取本类成员。头文件说明NPU专属环境变量必须经这个入口初始化，不能直接读公共配置单例并假定PYTORCH_NPU_ALLOC_CONF已解析。外部ATen公共解析器实现不在本卡读取范围。

主线instance使用静态对象和call_once；PYTORCH_NPU_ALLOC_CONF与PYTORCH_ALLOC_CONF只要同时存在就拒绝，包括一个为空的情况。均未设置则返回，不解析；只设置一个则选择其值。环境首次读取与运行时显式parseArgs是两个入口，修改进程环境不会使已经成功完成的call_once再次读取。

发布类名为CachingAllocatorConfig；堆上静态单例只读getenv("PYTORCH_NPU_ALLOC_CONF")并传入parseArgs，没有主线双名称选择逻辑。发布自持max_split_size、GC、expandable_segments及16桶舍入数组；其默认max split为size_t最大值、GC为0、expandable为False、数组全0。不要把主线的公共配置委托或新别名回推至发布版。

两版头部均有16KiB对齐、2MiB小块、20MiB大块及1MiB至64GiB的16桶舍入常量；主线头另有10MiB的kMinLargeAlloc常量，发布配置头没有这项声明，不能据此否定发布版其他分配器文件存在相关尺寸边界。主线保留常量不等于本地仍实现发布版的桶索引算法。两版自持的pin expandable、pinned register、page 1g和lazy reclaim初值为False，对齐存储为16384字节、旧segment成员为0；主线另有fraction=1.0、pinned reserve=0、release lock=False、throw OOM=False。这里的旧segment成员0不能改写成解析器内部默认已存20MiB；后续分配器如何选默认段属于另一层。

## 主线的两阶段解析和键集合

parseArgs空字符串立即返回，不重置这些成员。非空先遍历ConfigTokenizer：未知键拒绝，公共解析器认识但NPU未允许的键也拒绝；supported_settings非空时还检查调用方白名单，skipKey后核对逗号。通过键预检后先调用公共配置parseArgs(env)，再逐个解析NPU字段，最后执行组合检查。数值错误或后续组合错误可能发生在此前状态已经写入之后，本地没有事务回滚，不应将这个入口当作原子更新或“省略即全部恢复默认”。公共tokenizer的空白和语法细节不能套用下文发布版自写lexer。

| 主线集合 | 精确键 |
| --- | --- |
| getKeys注册的10个NPU键 | pin_memory_expandable_segments、pinned_mem_register、base_addr_aligned_kb、page_size、segment_size_mb、multi_stream_lazy_reclaim、pinned_reserve_segment_size_mb、per_process_memory_fraction、release_lock_on_npumalloc、throw_on_npumalloc_oom |
| kNPUSupportAccKeys允许的9个公共键 | max_split_size_mb、garbage_collection_threshold、roundup_power2_divisions、expandable_segments、pinned_use_background_threads、large_segment_size_mb、max_non_split_rounding_mb、pinned_max_round_threshold_mb、pinned_max_cached_size_mb |

getKeys在文件尾交给REGISTER_ALLOCATOR_CONFIG_PARSE_HOOK。本地只看到宏调用，不能据此展开外部注册机制或编造公共解析器实现。公共选项的取值验收需继续核对实际配套ATen；NPU文件中的白名单不等于公共实现每条规则都已在此重写。

## NPU字段的数值、单位与能力检查

isDigit拒绝空串并要求每字符isdigit；base_addr_aligned_kb还用stoi结果回写文本长度检查，接受0..16且拒绝前导零，存储时乘1024。segment_size_mb也要求整数20..512，存储乘1048576字节；主线一进入这个旧选项解析器就警告改用large_segment_size_mb。getter或日志标签含mb/kb不意味着原始成员仍用该单位。

page_size只接受小写1g并把标志置真，没有一个本地False文本分支。multi_stream_lazy_reclaim、主线release_lock_on_npumalloc和throw_on_npumalloc_oom等布尔解析只接受精确True/False。per_process_memory_fraction用stod并检查闭区间[0,1]，没有检查stod消费位置，不能声称这里实现严格整串浮点语法。pinned_reserve_segment_size_mb直接保存tokenizer.toSizeT结果，未在这里乘MiB；它与旧segment成员的存储单位不同。

pin_memory_expandable_segments=True时，两版都检查CANN最低8.5.0，低于要求时警告并置False。主线GetSocVersion达到Ascend950系列（包含旧称Atlas A5）对应枚举时跳过驱动版本检查，较早枚举才检查最低25.5.0；发布版没有这个跳过分支，仍检查驱动25.5.0。源码中的设备分支和注释不是完整产品支持矩阵，不能替代部署配套验收。

pinned_mem_register通过AclrtMallocHostWithCfgExist检查能力，不可用时警告并置False；警告文字提到CANN 8.5.0、驱动26.0.rc1，实际本地条件是该能力探针。若register仍为True且pin expandable为True，再把register关闭。初始化开关、探针存在和实际Host分配效果需分别核对。

## 扩展段探针、冲突和日志顺序

主线解析后若公共expandable_segments为True，先要求max split为size_t最大值且GC阈值为0，再调用AclrtReserveMemAddress请求512字节地址。成功且指针非空时checked release；否则先NPU_CHECK_ERROR(status)，再警告并让公共解析器解析expandable_segments:False。错误检查可能提前结束该分支，不能承诺每个保留失败都会顺利降级False。本卡没有执行这个探针。

主线pin expandable与非默认pinned_max_round_threshold/pinned_max_cached_size组合会警告阈值不起作用；page_size 1g与非默认段组合会警告大于1MiB池的段设置被覆盖。large segment非20MiB且旧segment成员非0时警告同时设置和弃用。这里记录解析器的检查/警告，不以其代替完整分配器调用链或测量结果。

主线最后分别记录本地和公共配置。base_addr_aligned_kb与segment_size_mb标签对应的变量已存字节；roundup_power2_divisions日志输出的是数组size，不是特定请求采用的分段值。throw_on_npumalloc_oom头注释描述预先拒绝超配额申请；设备malloc主路径的行级证据见后文「throw_on_npumalloc_oom 与 fraction 的两级门机制」，其余申请路径未逐一核对，不能把一个getter和注释扩展为所有申请路径均已验证。

## 发布版lexer、重置与舍入桶

lexArgs把逗号、冒号和方括号作为独立token，只移除ASCII空格，不是移除任意空白；consumeToken检查索引和目标字符。发布parseArgs在检查env是否nullptr之前，先重置max split、GC和16桶数组；没有重置所有布尔或其他字段，set_expandable_segments_flag也保持此前状态。不能把注释“set the default values”解释为全配置复位。

发布识别11个键：max_split_size_mb、garbage_collection_threshold、expandable_segments、pin_memory_expandable_segments、pinned_mem_register、base_addr_aligned_kb、page_size、segment_size_mb、roundup_power2_divisions、pinned_use_background_threads、multi_stream_lazy_reclaim。max split要求数字且大于20，再按size_t可表示范围限制并乘MiB；GC用stod检查严格开区间(0,1)。expandable精确True/False，True时在自身解析器执行地址保留与释放；失败分支同样先检查status再警告关闭，不保证每种失败可回退。出现expandable键会置持久explicit flag；最后expandable为真且explicit flag真时要求max split/GC默认，否则在非默认冲突时警告并关闭。保留这个分支顺序，不替调用者推定此前状态。

roundup_power2_divisions标量要求0或2的幂并填满16桶。列表中每个分段数也要求0或2的幂；边界为正的2的幂，索引log2(boundary)钳到0..15，首项先填充其索引之前的桶再写当前桶；大于号项从last_index+1填到末尾，结束要求右括号。这里没有额外的严格递增或去重边界检查，不能将文档示例当作本地完整校验器。getter对size==0或空数组返回0，其余按请求大小相对1MiB的log2索引钳到16桶范围。发布pinned后台线程布尔由自身成员保存，主线则委托公共配置。

发布parseArgs末尾同样按能力和pin expandable组合处理register开关。发布未含主线新字段、公共新键、旧segment弃用警告和完整配置日志，不依据相似类名推定功能一致。

## 运行时setter：发布1项，主线8项

两版setAllocatorSettings均先emptyAllNPUStream并检查成功，再把非空supported_settings交解析器。这是Host任务队列排空入口，不能据此写成完整设备同步屏障；队列协议见[Host环队列与排空](torch_npu_native_repository_ring_and_host_drain.md)。

| 固定实现 | 运行时白名单 |
| --- | --- |
| 发布 f3ecfe4a7ef7395754da7ca2e35661a7132b519b | expandable_segments |
| 主线 ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf | expandable_segments、max_split_size_mb、max_non_split_rounding_mb、release_lock_on_npumalloc、throw_on_npumalloc_oom、per_process_memory_fraction、pinned_max_round_threshold_mb、pinned_max_cached_size_mb |

主线8项不是环境变量19项全部可动态修改；发布1项也不能概括主线实现。公开文档与源码出现不同范围时，明确固定版本和证据类型，不通过删掉一方来消解差异。测试或部署前记录实际包、初始配置、设置字符串、失败前后状态、Host队列和设备同步协议，以及内存/数值验收；只解析成功不代表改善碎片、OOM或吞吐。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUAllocatorConfig.h)（primary），读取范围 1–174。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUAllocatorConfig.cpp)（implementation），读取范围 1–416。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUAllocatorConfig.h)（implementation），读取范围 1–146。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUAllocatorConfig.cpp)（implementation），读取范围 1–395。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp)（implementation），读取范围 867–882。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp)（implementation），读取范围 877–885。

## PYTORCH_NPU_ALLOC_CONF 文档声明与实现对照

对照主线文档页 `docs/zh/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md`（286 行全文）逐句核对本卡两版解析器之外的**分配器消费面**；行号为主线 ac0e1564 `NPUCachingAllocator.cpp/.h`、`OptionsManager.cpp`。行为层结论（拒绝/计数/不触发快照/各键文档表述）由[内存调试与拒绝路径卡](torch_npu_memory_debug_and_rejection.md)、[重试与 GC 卡](torch_npu_allocator_retry_gc_and_oom.md)、[OOM 快照卡](torch_npu_oom_memory_snapshot.md)与[原生内存 API 卡](torch_npu_native_memory_api_scope.md)持有——其中原生内存 API 卡的键表按文档页转述，其 base_addr_aligned_kb 条目已按本节实现口径表述；本节给这些文档声明补齐行级实现证据，并记录两处文档/实现偏差。发布版解析器无主线新字段（本卡前文两版键集合表），下列 throw_on/fraction/新阈值事实**不外推发布版**。

**池边界与粒度（两个不同常量）**：小块池判定 `size <= kSmallSize`（kSmallSize=1MiB，:103；get_pool :2732-2753）；大块申请向上取整到 2MiB（kRoundLarge=2097152，:105）；`round_size` 把申请尺寸（先加 `AddPadSize()`）向上取整到 512B 倍数、下限 512B（kMinBlockSize=512，:102；函数体 :2247-2257），作用于申请尺寸而非地址。「小于1MB小块池」与「大块 2MB 粒度」是两个不同常量，不是同一个阈值。page_size 1g 时 `IsMallocPage1GMem` 分支按 kExtraLargeBuffer 整倍申请（:1224-1228）。

**base_addr_aligned_kb 的实现真身（文档/实现偏差一）**：块重对齐门 `params.size() >= kRoundLarge && expandable_segments() && align_round != 0 && ptr % align_round != 0`（:1435-1462，门条件 :1437-1438），通过后以内偏移裁剪方式生成对齐子块，且仅在 `offset_size + params.size() <= params.block->size` 时生效（:1441）；align_round 取 `base_addr_aligned_size()`（默认存 16384 字节）。这里要区分三层：`round_size` 的 512B 处理是**申请尺寸舍入**（上段）；本门是**额外的基址重对齐**；配置为 0 时 `align_round == 0`，**跳过的是这个额外处理**——实现中不存在一个主动的 512B 基址对齐步骤，块基址保持池中原有地址。文档「仅在 expandable_segments 为 True 生效」「大于等于2MB」与实现一致；文档「配置为0时申请内存的基地址512B对齐」按字面读会多出一个实现中不存在的行为承诺。该窗口读不出跳过后基址是否恰好 512B 对齐：块地址来自此前分配的段与底层分配接口，本窗口未读取其地址性质，既不能据此断言返回地址具备 512B 对齐，也不能断言不具备。[原生内存 API 卡](torch_npu_native_memory_api_scope.md)与[推理显存配置](../torch_npu_allocator_options.md)的对应条目已按本节口径表述。

**allocate_with_aligned 入口是另一种主动对齐机制**：`allocate_with_aligned`（:4158-4186）把申请尺寸加上 `base_addr_aligned_kb*1024` 的对齐余量后申请——非缓存路径经 `AclrtMallocAlign32`（另加 AddPadSize，:4172-4178），缓存路径经本分配器 malloc（:4179-4182）——再把返回地址向上取整到该倍数得到 devPtr，realPtr 保留为删除基址（:4184-4185）。这是入口内的主动地址对齐，不依赖 expandable_segments，与缓存路径 :1435-1462 的重对齐门是两个机制；其入参由调用方传入（非缓存路径的条件与删除器见[内存调试与拒绝路径卡](torch_npu_memory_debug_and_rejection.md)）。

**multi_stream_lazy_reclaim 的实现细节**：`kLazyQuerySize=512`（:119）；开启且非 capture 上下文时，挂起事件总数 `sum > 512` 才 `process_events`（:1258-1268），找不到可用块再补一次（:1280-1284）；关闭时每次 malloc 前 `process_events`（:1216-1228）。文档「阈值 512 或找不到可用块才查询、仅影响查询频率不改变释放条件」一致；两点文档未记：**图捕获上下文一律退回立即查询**（npuEventQuery 在捕获中非法）；「先回收再选块」的重排是为修复「get_free_block 取出未终态化块 + process_events 合并相邻块」的损坏窗口（:1243-1257 源注释），调用次数与旧实现保持一致。

**throw_on_npumalloc_oom 与 fraction 的两级门机制（文档两个「不生效」条款的行级锚定）**：`allowed_memory_maximum` 仅当 fraction<1 时被设置（:1012-1014 注释原文 "set iff memory fraction is less than 1"；init :1054 setMemoryFraction；运行时 setter :1752-1762 以 aclrtGetMemInfo 总量换算，TORCH_CHECK [0,1]）。malloc 先过分数门（:2989-2993 超限即置 ACL_ERROR_RT_MEMORY_ALLOCATION 返回），**再**进 throw_on 预拒绝块（:2995-3027：`max_allowed = per_process_memory_fraction() × device_total`；`device_free` 取了但不用——校验确实只看「已分配+本次申请 vs 总量配额」；`stats.num_oom_rejections++`；`TORCH_NPU_WARN_ONCE "Preemptively rejecting allocation..."`）。因此：(a) fraction<1.0（环境变量或 `set_per_process_memory_fraction` 两路都设 allowed_memory_maximum）时超限请求被分数门先拒，throw_on 的计数/一次性告警/预拒绝观察者不触发——文档「fraction<1.0 时 throw_on 不生效」成立；(b) throw_on 拒绝时跳过 mempool 回退/缓存释放重试链（:1296-1308，与重试卡结论互证），由 :3669-3678 以 `TORCH_CHECK_WITH(OutOfMemoryError, ..., "Allocation was preemptively rejected because it would exceed per_process_memory_fraction limit")` 抛出；该路径只异步派发 `oom_rejection_observers_`（:1319-1338，detached 线程），不经过真实 OOM 分支（:1368-1396 的 `stats.num_ooms++` 与 `oom_observers_` 派发）。OOM 快照观察者 `oom_observer` 恰挂在后者（OptionsManager.cpp :711-757：`attachOutOfMemoryObserver` 装载、`IsOomSnapshotEnable` 首调装入、dump 文件名 `oom_snapshot_<pid>_<时间戳>.pickle` 经 `torch_npu.npu.memory._dump_snapshot` 落盘），故「throw_on 拒绝时 OOM_SNAPSHOT_ENABLE 不生效」成立。`num_oom_rejections` 在累计统计重置块清零（:1852）。

**OOM 快照开关的实现细节（文档/实现偏差二）**：`IsOomSnapshotEnable`（OptionsManager.cpp :738-757）strtol 裸读、无 {0,1,2} 集合校验——非 0/2 的任意非零值都落入「全历史」分支（模式 2 记 `"state"`、其他非零记 `"all"`），文档页只声明 0/1/2 三态；`OOM_SNAPSHOT_PATH` 缺省 "./" 且 `realpath` 失败即 TORCH_CHECK（:683-694），与快照卡「路径必须存在且可写」互证。

**max_non_split_rounding_mb 消费面**：get_free_block 超尺寸分支（:2877-2881）——`p.size() >= max_split_size()` 且候选块 `size >= p.size() + max_non_split_rounding_size()` 时拒绝复用；即文档「保留块 A、请求 D（D>C）时 A-D≤B 才复用、D≤C 时本项不生效」的逆否表达，一致。默认 20MB 是主线委托公共解析器的键，本卡 NPU 窗口不含公共默认值，不据此外推。

**文档侧版本与产品声明（不外推）**：各键 TorchNPU/PyTorch/HDK/CANN 版本门槛、page_size 的页表/TLB 收益叙述、「单进程多卡与驱动版本互锁」为文档侧声明；源码可核的仅 pin expandable 的 CANN 8.5.0/驱动 25.5.0 探针（本卡前文）与 `pinned_use_background_threads` 等委托面。`pinned_max_round_threshold_mb/pinned_max_cached_size_mb` 消费端在非 expandable pinned 分配路径；该路径实现不在本卡读取范围内，本卡不对其行为作断言，相关配置门槛见[pinned memory配置](torch_npu_pinned_memory_options.md)。

## 附加核验来源

- [memory_management/PYTORCH_NPU_ALLOC_CONF.md @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/memory_management/PYTORCH_NPU_ALLOC_CONF.md)（primary；:1-286 全文）
- [主线 OptionsManager.cpp @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionsManager.cpp)（implementation；:676-757 连续窗：GetOomSnapshotDumpPath/oom_observer/IsOomSnapshotEnable）
- [主线 NPUCachingAllocator.h @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.h)（implementation；:213-226 观察者 typedef 窗）

已列来源的扩展阅读窗（不新增条目）：主线 NPUCachingAllocator.cpp 增读 :102-105、:660-668、:1010-1016、:119（kLazyQuerySize）、:1210-1360、:1435-1462、:1740-1765、:1845-1856、:2247-2257（round_size）、:2732-2753、:2866-2890、:2985-3030、:3665-3690、:4155-4186；发布版 NPUCachingAllocator.cpp 未新增阅读窗（发布无 throw_on/fraction 门，发布面由本卡原有两版对照承担）。
