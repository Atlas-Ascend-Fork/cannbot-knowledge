---
type: Guide
title: 实验Triton归约候选：默认公式、入口优先级与UB边界
description: 区分归约早退、r0_公式三分区、最小/均宽、UB近似与外部Config归一化的真实边界。
tags:
- task.optimization
- topic.compilation
- topic.compute.reduction
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py
  role: implementation
created_at: '2026-11-11T08:42:19Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验Triton归约候选：默认公式、入口优先级与UB边界

## 固定局部范围

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的_red_formula_configs、两个小型配置/宽度helper和reduction的前段实际调用链；均宽、类型表与共享容量按同一固定源和[逐元素候选指南](torch_npu_experimental_triton_pointwise_candidate_filters.md)复用。覆盖persistent_reduction完整函数及当前codegen禁用门控；整个3293行heuristics不在本卡范围，也不覆盖reduction剩余legacy候选。没有导入、生成Config、执行数学/设备探测或编译实验，平台未知，保持draft与空平台。

## 先看入口是否到达默认公式

reduction先将reduction_hint写入inductor_meta；调用方提供字典时该赋值并非先复制出独立metadata。no_x_dim为真时复制size_hints并把x设1；它与batch_invariant为if/elif，因此前者优先。batch_invariant分支只在正int原x>64时夹到64，并直接请求(64,128)配置后返回。请求值还要经过下述factory与上游helper，不在此宣称最终tile必定原样或已证明跨batch数值一致。

普通继续路线才显式拒绝triton_meta=None。len(size_hints)为2或3时，truthy npu_permute_gather元数据优先读取其XBLOCK/R0_BLOCK并int转换后立即返回；其次truthy pin_xr按逗号split为两个int并返回。这里不重新证明permute-gather改图合法性，也不捕获任意缺字段或配置格式错误。

只有上述早退未命中，且模块autotune_enhance为真、ncfg.autotune_fallback为假、两个max_autotune开关均未开时，才调用默认公式并返回。所读config初值为autotune_enhance=True、autotune_fallback=False、pin_xr=None；模块捕获与运行态配置另核。不满足门槛时后续legacy与其他hint路径未在本组展开，不能把本卡当成所有归约的统一候选算法。

外层还计算全部非x尺寸的乘积rnumel，并有ND线性化注释；**默认公式本身仍直接取size_hints['r0_']**，没有消费外层这个总乘积。不能把该注释自动补成多归约轴的默认公式已经使用总归约元素数；最终上游ND拆分与实际kernel需各自验证。

## 最小宽度与均宽用途不同

公式取xnumel=size_hints.get('x',1)、rnumel=size_hints['r0_']。num_load缺省或假值归1，num_reduction缺省或假值归0，没有为任意非法metadata建立完整类型/正数防御。

_min_ptr_elem_bytes只看signature中的*指针字符串，在已知宽度里取最小值，未知类型忽略，没有已知值时用4；_ceil_mean_ptr_elem_bytes却把未知指针按4计入向上平均。两者并不是同一个“第一个输入dtype”；共享表中的fp64/f64为4、i64为8等值仅是此估算表，不可按dtype名自行改成真实Tensor sizeof。

记d为最小宽度，d_ub为向上均宽，公式用：

```text
x_cap = 2的向下幂(min(xnumel,4096))
P = 2048 if d <= 2 else 4096
buffers = num_load + num_reduction + 1
ub_cap = capacity / (d_ub * buffers * overhead_factor)
rmax = 2的向下幂(min(rnumel,max(ub_cap,1)))
r_cap = next_power_of_2(rnumel)
```

本地_p2floor对<1返回None，_p2round按round(log2(...))选幂、<1回1。这些边界分支不等于整个公式支持空或非正归约尺寸；例如后续仍有除rnumel、log2比例和上下界比较，没有统一兜底。

## 三个归约区间的实际候选

add(X,R)只检查X≤xnumel且R≤r_cap，加入set；它不是通用X/R正数、资源或shape合法性验证器。

| rnumel | 本地请求集合 |
| --- | --- |
| ≥50000 | X取1/2/4/8，R取512/1024/2048/4096的组合，经add上界检查。此分支没有使用rmax去过滤组合。 |
| ≤64 | R取rnumel本身及其next_power_of_2；按P/rnumel的近邻幂pX，尝试X={1,pX//4,pX//2,pX,2pX,4pX}，仅在X≤x_cap时加入。不能统称所有R请求都是2次幂。 |
| 其余 | 按比例与拟合常量算锚点(pX,pR)，做局部X/R网格，再追加小R、填满R及大X锚点。 |

MID的split为 `2**(-2.06+0.59*log2(xnumel/rnumel))`；pX由sqrt(P*split)取近邻幂并夹x_cap，pR由sqrt(P/split)取近邻幂并夹rmax。X梯级含1、半pX、pX、2pX与x_cap，R梯级为半pR、pR、2pR并各自夹取。

之后尝试pR/4、pR/8、16、32的小R列；rnumel≤ub_cap时还按X=1..128的2次幂追加R=rnumel；最后追加(x_cap,2)与(x_cap,min(rnumel,8))。这些独立轴上界没有形成统一的**X×R≤ub_cap**最终检查，尤其不能因为代码算过ub_cap就把每个候选认证为UB合法。实际编译错误跳过仍按[候选编译回退](torch_npu_experimental_triton_compile_tiers_and_resource_fallback.md)的准确范围。

set中的pair排序后交factory；集合为空则回退(1,max(1,min(rnumel,16384)))。注释“1 legal tile”不替代上游helper和编译器验收，也没有重新按add条件验证该回退。源码的语料分区、拟合系数和R²说明不是本次性能实验。

## factory只归一hint，外部规则仍独立

npu_triton_config_reduction先复制size_hints，对其中每个正int值调用next_power_of_2，不仅处理x；其他值保持。再将归一化hints和原请求x/r、num_stages、num_warps、register_intensive交给从torch._inductor.runtime.triton_heuristics导入的triton_config_reduction，直接返回结果。

这一步没有在本地展开上游XBLOCK最大值、ND归约拆分、warp推导或所有合法性检查；不能把包装注释的4096约束当成本组已完整核验的外部实现。请求pair的set去重，也不能无条件保证上游转换后的Config对象全部不同。

核对真实工作负载时保留入口早退、完整size_hints与r0_、signature宽度、计数metadata、共享容量来源、请求pair和最后实际Config，再验证数值、资源与计时。不能把选到一个候选、提示“legal”、或公式回退当作已支持全部多轴归约、dtype、产品或图模式；本卡没有执行这些验证或新增verified。

## persistent 接口与当前 codegen 禁用边界

同一固定版本还保留完整的 `persistent_reduction` 启发式函数，但本地 `NPUTritonKernel.should_use_persistent_reduction()` 恒返回 False；`codegen_static_numels` 遍历到 reduction tree 且 `self.persistent_reduction` 为真时直接抛 AssertionError。这个固定 codegen 路径选择循环归约；函数存在、配置枚举成功或注释里的“无 R 循环”，均不能证明当前默认编译链已支持 persistent kernel。这里没有执行覆盖方法或断言，也不把这条局部边界扩展为所有 NPU 归约方案的能力结论。

保留接口先向传入的 inductor_meta 写入 reduction_hint；为 None 才新建字典。no_x_dim 为真时复制 size_hints 并把 x 设为1，triton_meta 为 None 则先抛 ValueError。它只取 r0_ 作为 rnumel；虽然读取并切片 axis_hints，该局部变量没有参与后面的候选构造，不能据此称逐轴提示已经生效。

batch_invariant 且非 no_x_dim 时提前走单配置：复制 hints，仅当 x 为整数且大于64才将该 hint 夹到64，再以请求 X=64 构造配置。正整数 rnumel 原值作为 r_fixed，其余交给外部 next_power_of_2；不会统一把正整数 r 向上取2次幂。该分支在后面的 `len(size_hints)==2` 检查之前返回，删除 Config.kwargs 中的 R0_BLOCK，并传 PERSISTENT_REDUCTION 类型给 cached_autotune。它提供单候选请求，不构成跨 batch 同一二进制或设备合法性的本次验证。

普通分支只接受 len(size_hints)==2，否则末尾抛 NotImplementedError。初始 X 候选按下表的顺序选分支；前面命中后不再进入后面的 hint/disable/default 分支。

| 优先级条件 | 初始 X 请求 |
|---|---|
| max_autotune 或 max_autotune_pointwise；否则模块级 autotune_enhance | 1、2、4、8、16 |
| INNER | 1、2、4 |
| OUTER | 16、32、64、128、256、512、1024 |
| OUTER_TINY | rnumel<=256 时为 `2*(256//rnumel)`，否则1 |
| 调用当时的 disable_pointwise_autotuning 返回真 | 32 |
| 其余 | 1、2、4、8、16、32、64 |

这些分支先构造 R 扫描范围，随后在 rnumel 为 int 且>=8、尚不在列表时追加原值，并追加正整数 R0_BLOCK_HINT；但代码紧接着把整个 r_list **覆盖**为只含 r_fixed 的列表。因此前面的 R 候选和显式 R0_BLOCK_HINT 最终均不保留。不能仅看到范围生成和 hint 插入，就称 persistent 会扫描多个 R。中间构造仍实际发生，函数没有总 try/except，也没有在 OUTER_TINY 的整数除法前统一验证 rnumel 为正。

XBLOCK_HINT 只采纳 isinstance(int) 且正的元素，取乘积后把从1开始、不超过 min(乘积,4096) 的2次幂加入 X 列表；这是向列表追加提示范围内的幂次，不能套用另一条归约路径的“至少达到提示”规则。xnumel 是正整数时再过滤 X<=xnumel；列表为空退到[1]。persistent_cfg 调用同一外部归约 Config 工厂后，先显式覆盖 kwargs 的 R0_BLOCK 为请求 r，再由外层逐配置删除 R0_BLOCK。其他字段仍受外部工厂影响，不能把表里的 X 请求自动等同为最终 kwargs。

最后若当时绑定的 disable_pointwise_autotuning 返回真，只保留配置列表第一项；它不直接选择设备实测最快项。该文件的默认 helper 是 `not inductor_meta.get("autotune_pointwise", True)`，其名称是安装时可重绑的接口，不能把默认定义外推为所有安装环境的唯一门控。最终仍交 cached_autotune，编译、计时与安装链按各自证据另计。R0_BLOCK 删除旁的注释称其应由 static numels 硬编码，而本版本 codegen 对 persistent 分支先断言；两处应一起看，不能仅据注释补出一个已经启用的无循环实现。

## Evidence

- [npu_triton_heuristics.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py)（primary）：31–31、51–58、70–70、1628–1628、1668–1676、2537–2576、2579–2595、2603–2789；仅此有界helper/调用者/声明，不提升整个模块资格。
- [config.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)（implementation）：169–169、172–172、405–405；仅此有界helper/调用者/声明，不提升整个模块资格。

## persistent 接口与禁用门控的新增有界证据

- [npu_triton_heuristics.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py)（primary）：198–204、3040–3189；仅所列完整函数/默认helper/codegen门控，不提升整个模块资格。
- [triton.py](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py)（implementation）：2187–2228；仅所列完整函数/默认helper/codegen门控，不提升整个模块资格。
