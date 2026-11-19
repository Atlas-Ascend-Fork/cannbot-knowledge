---
type: Guide
title: 实验Triton逐元素候选：维度选路、搜索与过滤边界
description: 区分实验Triton逐元素1D/2D/3D的开关与搜索列表、维度预算、均衡/UB近似及模块捕获配置的边界。
tags:
- task.optimization
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/device_props.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py
  role: implementation
created_at: '2026-11-11T08:21:53Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验Triton逐元素候选：维度选路、搜索与过滤边界

## 固定范围与调用顺序

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 实验Triton的本地过滤/估算、默认公式和完整pointwise维度入口，以及所需核数/UB来源、常量与axis_hints提取。本文下述本地候选入口之外的reduction、grid、launcher、编译与计时按各自知识另计；没有读取或提升整个heuristics大模块，也未导入、查询设备、执行生成器或编译实验。

所读pointwise先以size_hints尺寸乘积得numel，计算 `bs=max(256,min(numel//128,1024))`。两个有界调用段均将bs作为min_xblock_floor，先均衡过滤，再UB估算过滤，随后交cached_autotune。该顺序不等于每个pointwise入口都必经两层：所读autotune_enhance分支在未启用autotune_fallback及两个max_autotune开关时，直接用公式候选并提前返回；其实际生成规则见下文默认1D公式小节。

autotune_enhance先由实验config赋给模块同名变量，源码初值True；autotune_fallback初值False，在所读分支直接通过ncfg访问。初值与运行态patch另核，不能把后续任意配置更改都当作已改变模块里先前保存的值。后续编译成功、错误跳过与小block扫描见[候选分层与编译回退](torch_npu_experimental_triton_compile_tiers_and_resource_fallback.md)，不在这里重复资格。

## 一维均衡条件不是注释中的整除规则

_filter_balanced_xblock_configs在size_hints为空时返回list(configs)。只有size_hints恰有一个条目时走一维分支；此时没有有效正x时同样尝试返回原配置列表。XBLOCK不是int或≤0的配置直接保留，不能把本函数当作完整候选合法性检查。

| 一维条件 | 实际代码 |
| --- | --- |
| xnumel < 核数×256 | 接受XBLOCK≥xnumel，或XBLOCK≥min(xnumel,8)。后者不检查是否整除xnumel，也不要求块数刚好均衡。 |
| 其他正xnumel | 先要求XBLOCK≥min(max(min_xblock_floor,256),xnumel)，再要求ceil(xnumel/XBLOCK)≥max(2,核数//4)。 |
| 全部被过滤 | 返回list(configs)，在所读配置列表调用中重新放回输入候选；不是因筛选失败直接报错。 |

小核条件中较宽的第二条已包含第一条的数值范围，不能把“单block或整除分块”注释当作实际二选一算法。这只是代码谓词；本次没有复现注释中的提速倍数或最优tile结论。

axis_hints虽然是函数形参，函数体并未读取它。docstring所说“≥4个constexpr轴时将floor放宽到256”没有在这个helper中形成分支；所读两个调用者仍传bs。不能据文档句子认定任何多轴1D候选都获得额外放宽，也不据此否定未覆盖的生成器可能存在其他策略。

## 多轴均衡也有整体放回路径

size_hints条目数不是1时，函数只识别x/y/z对应XBLOCK/YBLOCK/ZBLOCK。已知正int尺寸的轴，floor为min(8,numel)，其他情况floor为8；配置中该block不是int就跳过该轴检查，未知轴名也跳过。任一参与检查的block低于floor就移除该配置。

若最终没有保留项仍返回list(configs)。因此过滤不是资源或shape的硬门槛；缺参数、未知轴和整体放回均可能留下尚待实际编译/运行判断的配置。这里没有建立任意一次性迭代器的重放协议，所读调用者使用配置集合/列表。

## UB估算的数学口径

_estimate_pointwise_tile_bytes需要非空axis_hints和正int XBLOCK，否则返回None。每个hint必须是dict且有正int length，否则同样返回None；divisor缺失、类型不符或≤0时用1。它按每个轴计算：

```text
axis_elems = min(length, max(1, XBLOCK // divisor))
tile_elems = product(axis_elems)
live_loads = min(num_load, 8)
buffers = max(1, live_loads + num_reduction + 1)
estimated_bytes = int(tile_elems * 4 * buffers * 2.0)
```

4是固定每元素字节近似，2.0是固定开销系数，8是同时驻留load计数的上限；不是从实际kernel dtype、完整活跃区间、对齐、软件流水或编译器分配表逐项还原。size_hints形参未被该估算函数消费，实际乘积来自axis_hints。

_extract_axis_hint_payloads从block_hints提取正int静态长度、首个含divisors的dict内的正int divisor，同时把triton_meta.axis_hints原样交给后面；这不是对任意嵌套hint的完整验证。实际axis_hints缺失、未知类型或符号值可能使估算不可用，None表示无法估算，不表示占用为0。

## UB过滤保留未知，也保留一个超限候选

_filter_by_ub_estimate仅在configs非空、size_hints条目数恰为1且axis_hints非空时尝试估算，否则返回list(configs)。num_load缺省或假值归1，num_reduction缺省或假值归0；它没有在此完整校验计数类型和非负性，不应将任意非法metadata视为可靠占用估算。

估算为None或不超过容量的项均保留。若所有已估算项都超过容量，按估算值排序，只留下最小的一项；相同估算依输入顺序保留首项。它保留的是估算值最小，不是按XBLOCK或真实UB占用证明最小，更不是保证必定编译成功。

所读一个调用段在两层过滤之后，axis_hints条目数≥3时还可能追加新候选。注释称“XBLOCK=1”，实际传给triton_config_with_settings的是128，并按kwargs去重后追加，没有在该段重新进行UB过滤。配置生成helper本体未在本组展开，不能把注释当作最终XBLOCK=1，或把过滤阶段的结果误当成最终所有候选均已低于估算容量。

## 核数与容量是本地探测和缓存结果

_npu_total_cores在调用时委托get_npu_vector_core_count。该无参lru_cache helper优先取当前设备属性中truthy vector_core_num；其次仅在cube_core_num为真、soc非None且满足“soc∈[220,240)或soc≥250”时取2×cube数；再取truthy multi_processor_count，异常或没有可用值时回40。这里只保存源码判据与回退常量，不把40宣称为所有产品或受限执行流的实际核数。

UB容量在heuristics模块赋值时即调用get_npu_ub_size_bytes：它经内部_soc_version_no_init委托_C接口取soc，非None且≥260返回256×1024，否则或异常返回192×1024。不能用注释中的芯片名称替代这些实际分支，也不将回退数值当作硬件实测容量。这里未验证_C接口的初始化、副作用或fork行为；源码docstring的“Verified”不是本次验证。

两个device helper都没有device参数且以无参lru_cache保存结果，heuristics还保存了容量返回值；它们不是随每次过滤按设备或流重新计算。调试多设备或改变配置时，应保留实际取得的数值和缓存生命周期，而不能只靠函数名假定读到每个新设备的实时限制。

验收时区分原候选、均衡后列表、None/数值估算、容量来源、整体放回及追加候选，再核实际编译错误、独立数值与计时。通过本地过滤不等于UB合法性、性能最优或完整输入支持；本卡没有运行这些实验或新增verified。

## 默认1D公式的输入宽度是metadata近似

所读提前返回分支实际调用_pw1d_formula_configs。本节补该完整函数、_ceil_mean_ptr_elem_bytes与npu_triton_config factory；既有均衡、UB来源、编译、启动器和计时证据复用，不扩大到整个候选生成模块。

numel取size_hints所有值的乘积，num_load缺省或假值用1。dt来自signature中所有字符串且以*开头的指针条目的字节宽度**向上取整平均**，不是首个输入的dtype，也不是最小指针宽度。没有指针时用4，未知指针类型也按4加入平均，标量signature不参与。

该估算表把fp8/i8/u8列1，fp16/bf16/i16列2，fp32/f32/i32以及fp64/f64列4，i64列8；尤其不能按fp64名字自行替换成8后声称是在复算这份代码。它只是固定metadata表，不读取实际Tensor或证明所有边界转换都已完成。signature指针项数与num_load+1也没有在这个helper核验一致，不能把docstring所称平均宽度的保守性推广成真实UB分配保证。

## 预测式、候选数与对齐不能只照注释理解

使用前文相同核数/UB来源，实际计算为：

```text
band = 17500 / ((num_load+1)**0.40 * dt)
wave = (numel / cores)**0.95
ub_cap = capacity / (dt*(num_load+1)*2)
pred = 0.74 * min(max(band,wave), ub_cap, numel)
align = max(1, 32//dt)
hi = min(capacity//(dt*(num_load+1)*2), int(numel))
```

它分别取0.5、1、1.5、2倍pred，先int截断，再按align向上取整并至少1，仅保留1..hi内尚未重复的值；另将hi向下按align对齐，结果≥1且未重复才作为cap候选加入，最后排序。因此基础候选最多5个，并不固定等于docstring的“约3个”。没有基准或误差检验来保证0.74、0.40、0.95这些拟合常量在当前模型最优。

这个函数没有调用前述均衡筛选或按axis_hints乘积计算的UB估算，也没有据此强制XBLOCK≥256或满足相同块数下限；不能把那些分支的候选约束套到这条提前返回路线。

align使用整数32//dt，不是对每种真实输入字节宽度分别求对齐。例如signature含*fp16和*fp32时dt=3、align=10，不能由“32B-align”注释推出所有指针的实际块字节数均为32的倍数。后面的factory还会按x的size_hint夹XBLOCK；最终布局、内存访问及编译合法性继续依赖下层。

若候选为空，函数直接取[int(numel)]，以覆盖注释中的极小输入；numel为0时这里也会留下0。它没有据此建立空输入或0 block可编译/可执行的证明，也没有在本函数完整核验num_load、尺寸或其它metadata的合法值域。

## 小型factory固定warps，额外分块走编译选项

npu_triton_config将XBLOCK设为min(x,size_hints['x'])；仅在y/z为真时分别添加同样夹取的YBLOCK/ZBLOCK。它始终构造num_warps=8的Config，num_stages按实参、缺省1；num_elements_per_warp与min_elem_per_thread虽在签名中，却未在所读函数体消费，不能据传入这些参数宣称它们已改变这里的warps或tile。

auto_blockify_size非None时只写到Config.extra_options，而不写cfg.kwargs/constexpr；编译时如何合并覆盖见[候选编译指南](torch_npu_experimental_triton_compile_tiers_and_resource_fallback.md)。本组没有执行外部Config、编译或缓存序列化，不能仅由注释认证全部第三方选项协议。

公式路线还实时读取ncfg.all_blocks_parallel。该值源码初始True，且最大基础XBLOCK>0、ceildiv(numel,最大基础XBLOCK)>65535时，会在该最大tile上再追加auto_blockify_size为2/4/8的三个配置。ceildiv来自上游runtime_utils，未在本组展开；大网格门槛和额外选项不等于已验证任意grid、折叠协议或收益。外层配置列表最多增加三个候选，之后仍要经历真实编译和计时。

这里显式检查最大XBLOCK>0才计算网格商，避免该分支对空输入回退块直接求除法；这不修复或认证前面的空候选。对比优化时保存实际signature/dt、num_load、numel、核数/容量快照、基础和额外候选及最终编译结果，不能把公式名里的winner预测当作设备实测最优性。

## Evidence

- [npu_triton_heuristics.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py)（primary）：31–31、47–47、1628–1628、1644–1655、1917–2102、2169–2175、2178–2194、2227–2242、2316–2345、2387–2401；仅所列完整helper/常量/调用者语句，不提升整个模块资格。
- [device_props.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/device_props.py)（implementation）：13–15、18–68；仅所列完整helper/常量/调用者语句，不提升整个模块资格。
- [config.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)（implementation）：169–169、172–172；仅所列完整helper/常量/调用者语句，不提升整个模块资格。

## 默认候选公式的来源范围

- [npu_triton_heuristics.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py)（primary）：70–70、1600–1625、1668–1676、2105–2156、2579–2595；仅所列完整helper/表/导入/配置，不提升整个模块资格。
- [config.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)（implementation）：167–167；仅所列完整helper/表/导入/配置，不提升整个模块资格。

## 维度入口的开关顺序不同

完整pointwise入口先从triton_meta['device']取得设备描述，并调用外部autotune_hints_to_configs，之后才进入1D/2D/3D及禁用分支。不能据后面的单配置路径推导这个外部hint处理被跳过或缺少device metadata也能安全回退；本卡没有新展开该外部生成器。

| size_hints条目数 | 本地早期选路 |
| --- | --- |
| 1 | disable_pointwise_autotuning真且两个max_autotune开关均假时，单个bs请求直接交cached_autotune。其余再看模块捕获的autotune_enhance；默认公式路线已由前文覆盖。 |
| 2 | disable真**或**tile_hint==SQUARE，且两个max开关均假时，进入19个请求的列表；它含方形及256×16、512×64、4096×8等非方形形状，不是单个square。 |
| 3 | disable真直接请求16×16×16，**没有**像1D/2D那样再用max开关解除此分支；否则7个固定请求加外部hint候选。 |
| 其他 | 最后抛NotImplementedError；前面的metadata读取和hint生成并未因此预先跳过。 |

这里的“disable”并不跨维度统一代表只剩一个配置。实际Config工厂还会按对应尺寸夹取tile，后续缓存去重也可能合并相同请求；列表条目数不是最终不同二进制数或实际benchmark次数。没有由这些开关证明产品吞吐或正确性。

## 1D宽搜索与缩减搜索是两条路线

当autotune_enhance为真，但autotune_fallback或任一max开关要求绕过默认公式的提前返回时，宽搜索先构造6个bs倍数、20个linspace后向下按32对齐的请求，再加静态长度/除数对齐和外部hint副本。num_elements_per_warp传256与64的两组请求不代表改变warps；前述本地factory没有消费这个形参。

静态长度部分从block_hints.XBLOCK_HINT提取正int，按length×1/2/4/...累加至65536；首个dict载荷中的正divisor再乘1/2/4且不超65536，另固定加入65536。numel不大于65536时还追加numel本身，没有在此把0等非法尺寸统一拒绝；外部完整shape/Config合同独立。

饱和部分令target=max(numel//核数,65536)×2，从65536倍增，只追加不超过numel的项。循环条件在倍增前检查，因此不能把target当作所有最终请求严格不超越的硬上界。对齐项先集合去重排序；hint配置使用deepcopy。最后仍走前文已覆盖的均衡/UB过滤及有条件的后追加，不将宽搜索注释中“饱和/一tile每核”当作本次性能实测。

当模块捕获的autotune_enhance为假时，走另一缩减路线：合并bs倍数与静态/除数extra请求后，只保留排序最小、最大，以及extra集合中最大的至多3项，再去重。它不是完整遍历全部线性化轴的笛卡尔积。

这条路线使用模块级npu_all_blocks_parallel快照，来自ncfg.all_blocks_parallel赋值；不是每次重读同一个config属性。开启时对preferred列表最后至多2项各追加auto_blockify_size=2/4/8（声明候选1被显式跳过），之后才进入既有过滤。它与前文默认公式路线**实时**读取all_blocks_parallel的时点不同；不能把后续config改动当作两条路线同时更新，也不把extra_options当作kernel constexpr。

## 2D限制只管追加的尺寸感知候选

本地_filter_reasonable_pointwise_2d_configs直接返回configs，没有检查函数名所暗示的合理性。前述19项分支仅再调用均衡过滤；一般2D分支则从14个固定请求、(bs,1)/(1,bs)和外部hint开始，随后补尺寸感知项。**这两条2D路径都没有在返回前调用本卡的UB估算过滤器**，不能套用1D的容量筛选结论。

_divisors_down从n开始反复floor-halving，只留下能整除原n的值，最后确保有1；它不是完整整数因子枚举。例如n=12沿12、6、3、1走，不会另枚举4。一般路径分别将y的这些值配X扫表，以及x的这些值配Y扫表，扫表为8..2048的2次幂；只在请求的扫轴不大于对应hint且256≤X×Y≤ncfg.pointwise_tile_max时追加。

pointwise_tile_max在本地源码声明为65536，调用时直接读取ncfg；旁边的“16384”注释没有成为此处实际常量。更重要的是，**这个乘积上下限只用于新增两轮sweep**，不是对先前固定/hinted候选或19项早返列表统一过滤。不能把65536当作最终所有候选的硬tile上限、UB容量或所有设备均能编译的保证。

factory的尺寸夹取发生在创建Config时，候选可能重合；一般2D最后也只有identity helper与均衡过滤。注释中的延迟、winning config和UB-overflow说明是策略意图，本次没有执行任何测量或资源实验。

## 3D不复用2D或1D过滤承诺

3D普通列表为16³、三种64×8×8排列、三种bs×1×1排列，再附外部hint；它直接交cached_autotune，没有在这条路径调用上述均衡或UB helper。禁用时的单16³同样不是实际尺寸一定为16或一定最优的证明，factory仍会夹取各轴。

因此诊断候选数量和调优开销时应保存维度条目数、disable与max有效值、模块捕获开关、tile_hint、外部hints、尺寸/除数请求、追加tile预算与factory后的真实kwargs，再独立核最终编译/计时。本文只闭合固定版本本地pointwise函数的阅读并集，不扩为整个heuristics模块、全部提示生成或设备执行的验收。

## 维度入口的有界证据

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py)（primary）：1639–1640,2195–2226,2243–2315,2346–2386,2402–2534行；所列范围涵盖完整嵌套helper、候选分支及声明，不代表整文件全部语义。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)（implementation）：373–373行；所列范围涵盖完整嵌套helper、候选分支及声明，不代表整文件全部语义。

同一heuristics的2178–2194、2227–2242、2316–2345、2387–2401按完全相同固定字节复用既有有界审阅，与所列分支共同覆盖pointwise的2178–2534；不代表整个3293行模块的全部语义。
