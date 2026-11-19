---
type: Guide
title: 实验 Triton 组合 kernel：准入、成员身份与 tile 分派
description: 保存静态同构逐元素组合的依赖/资源拒绝、slot重命名、单配置分派及普通生成回退和释放恢复边界。
tags:
- task.optimization
- topic.compilation
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton_combo_kernel.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/launcher_codegen.py
  role: implementation
created_at: '2026-11-11T09:20:09Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验 Triton 水平组合 kernel：准入、成员身份与 tile 分派

## 固定实现与默认关闭

依据 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的完整 triton_combo_kernel.py 258 行和所列 scheduling、foreach、launcher/config 消费者。发布固定快照在这些精确实验路径缺失，只说明局部来源关系。没有导入、运行 partition/IR/生成器/模板、查询设备、编译或计时，平台及完整运行正确性未知。

enable_te_combo_kernel 默认 False，成员数上限默认 8。allow_dynamic_shapes、allow_a5、allow_autotune 虽有配置声明，当前所读准入/构造没有据它们放宽条件：

is_a5() 为真始终拒绝、只收静态 shape，组合器也显式 enable_autotune=False。A5 是代码本地 SoC 判断，不能从这个拒绝规则或预留名称推导任意产品矩阵。

## scheduling 的真实准入

需要线性化、2..max_members 成员且不是 C++ wrapper。每个外层成员可以包含多个调度节点，但不能为空，且其中任何节点都不能为 reduction、foreach 或 template。第一节点的 numel 必须为 int/SymPy Integer、rnumel==1、numel<2^31，其他内部节点 group 必须相同；这里没有为任意非法/负尺寸额外建立完整合法性证明。

每个成员读取/写入的 buffer 名不能相交，mutations 也须为空。能取得的每个 buffer layout 必须连续；成员内 dtype 只能一种、写出的 layout.size 只能一种，成员之间 numel、输出 shape 和 dtype 都相同；int64/float64 被拒绝。布局/dtype 查询只将 AttributeError/RuntimeError/KeyError 转成拒绝理由，不能推广成任意异常都自动回退。

还要求任何成员写出的**名字**不与其他成员的读/写名字相交。这是 read_writes 名称集合检查，不是对任意 storage 别名、跨流或外部副作用的完整分析。ABI 预算按各成员依赖读写项个数累加再加 1，与上游 combo_kernel_max_num_args 作 `>=` 比较后拒绝，不在这里展开最终参数去重/打包合同。

UB 估算为 `256 * dtype.itemsize * max(2,最大单成员读名数+写名数) * 2`，超过 getter 返回的容量就拒绝。它不相加所有成员的 live vectors，也不逐项测量实际融合中间值或编译器缓冲；通过这条式子不是真实 UB 分配验收。

## partition 之后仍有检查

准入通过后才为各成员计算 schedule、SIMDKernelFeatures、tiling，并调用外部 horizontal_partition。partition 非空、总成员数与输入相等，每个分区仍要 2..max_members，且每个 tiling 的键严格为 {x,r0_}、分区内 tiling 相等；否则生成普通成员 kernel。

这个总数检查不在本地另行认证外部 partition 的元素唯一性/完整覆盖。每个分区实际使用 TEComboKernel(xblock=256)，新建子 kernel 后还 assert 线性化且 no_x_dim 为假，再绑定 slot、创建成员、重排 tensor dims、生成节点 schedule，最后逐成员应用线性化。继承的 partition、tiling、参数合并、代码生成和图依赖实现均不因本地通过就自动闭合。

## 成员命名与符号表更新

TEComboSubKernel 初始 combo_num/local_tile 为 None；set_combo_slot 保存 slot 与 local_tile 名，并给每个 tree 安装 lookup 包装。tree.prefix 保留，因为它仍参与轴语义。

包装仅在 lookup **新建节点**使 tree.nodes 长度变化时，把 node.name 加 `_slot` 后缀，调用 node.codegen.cache_clear，再更新符号登记；已有节点原样返回，不回填旧名字。lookup 的 `_te_combo_suffixed` 标志防止重复包装，不能把任意后续换 slot 称为会重新命名全部旧条目的协议。

rekey 会从 V.kernel.range_tree_nodes 移除旧符号、登记新符号；倒序找到 tree.var_list 中最后一个旧符号并替换，旧符号存在于 var_ranges 时移动其值。tree.nodes 仍按原 index expression 作键，不在此更换。它只更新这些本地登记，不证明任意外部缓存、映射、引用或重复符号都已全局同步。

iteration_ranges_get_pid 在 local_tile 非 None 且线性化时返回成员局部 tile，否则委托上游。相同 tree prefix 下的成员靠后缀和局部 tile 区分，不是各自启动独立设备 kernel。

## 一份生成代码与两种计数

codegen_kernel 至少要求两个成员。公共 imports 来自实验 kernel，extension imports 仅取第一个成员；helper_functions 按完整对象/文本的 OrderedSet 方式去重，不做函数语义等价比较。signature/meta 的 size_dtype 也取第一个成员；Triton 3.6 能力标志为真时向 signature 追加 XBLOCK constexpr，两路线都追加同名 constexpr argdef。

静态 metadata 的每成员 count 按未映射、非 reduction/loop 的 free nodes 计算：每轴 `ceil(length/min(length,xblock))` 的乘积，length 为 0 时该因子为 0；没有 free node 时初值为 1。随后做前缀 offsets 和 total，写 combo_tile_counts、offsets、no_x_dim、固定 xblock、空 dynamic_args、group_dispatch 等 metadata。

inductor_meta 还先记录 Grid1D、num_load 求和、num_reduction=0、成员 free-block 名称数求和、npu_linearize=False 等，再合入外部 inductor_meta_common；这里不把前面的字面值升级为外部合并后每个键一定不变的通用保证。size_hints.x 用 max(1,total*xblock)。

真正生成到 kernel 的每成员 num_blocks 另由 `_npu_emit_total_blocks` 从已生成 `<node>_blocks` 求积：没有因子返回 1，一个因子直接返回名字，多个因子才发射乘法语句。free-block 枚举同样排除 reduction、loop 和 tree_node_mapping 中的辅助轴。静态 metadata 与实际 header/tile 计数的对应仍依赖前面的单轴/tiling 前提，不是任意多轴配置的独立证明。

## 连续 tile 空间由各核分段执行

每个成员的非 reduction/loop tree 必须已有 pre_loop_code，否则 assert；先插入这些 header，生成 num_blocks_i，再构造 S_i 累积和。kernel 把总 tile 空间均分给 total_thread：商决定基础 tiles_per_core，余数给前面的 core；group_base 用商和 min(group_id,core_tail) 计算。

循环内 tile=group_base+i；按 tile<S_(member+1) 的 if/elif 选择一个成员，local_tile=tile-该成员前缀，再插入该成员的 prologue/body/PDL 过滤结果。没有在不同成员之间建立新的数据依赖或同步协议；准入所要求的独立性仍是前提。

foreach 消费者只构造一份 Config：XBLOCK 由 truthy combo_xblock 或默认 256 转 int，num_warps=8、num_stages=1，再交 cached_autotune。这个名称不表示此路径会扫描任意 tile 集合；三个预留 allow 开关也不会在这里改变固定配置。

所读 launcher 以 te_combo_meta **不为 None** 判定 combo，并优先选提供的 num_cores 作为 grid_0，不走 A5 recipe 或普通 xnumel 的缩网格分支。kernel 内 total_thread 使用 core-count getter 的生成值；外部 runner/设备和两处计数来源的完整一致性仍需按[grid 与 launcher 指南](torch_npu_experimental_triton_grid_and_launcher_codegen.md)及真实生成结果核对。

## 早期普通生成与失败后的边界

准入/partition 拒绝时 `_codegen_combo_fallback` 保存 scheduler 原 buffer_names_to_free 并先清空，逐成员 codegen_node，finally 将原待释放集合合回；全部正常完成后才调用 free_buffers_in_scheduler。它没有禁止各成员生成新的释放项；若中途异常，原集合仍恢复，但 finally 后那次统一 free 不会自动执行。

组合路线先收集所有生成源码，再 define kernels；define 列表构造完成后才逐 schedule mark_run、合并移除集合并调用 combo kernel，最后 free。这个时序减少提前标记，但不是覆盖所有中间 CSE、registry、内存元数据和 define 副作用的统一事务；本地没有用总 except 在任何生成/编译失败后自动重走普通成员路线。

验收应记录开关和拒绝理由、成员 read/write/alias 信息、partition、实际 tiling、slot/符号、两套计数、单配置、grid 与 kernel 分派、mark_run 和释放恢复，再核数值与真实性能。少启动几个 kernel、候选通过或源码生成完成都不等于数值/别名/资源/加速已被验证；本次无新增 verified。

## Evidence

- [固定源码 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton_combo_kernel.py)（primary）：1–258；完整本地 combo 模块，所有生成字符串已读，外部基类/模板/设备另计。
- [固定源码 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py)（implementation）：4384–4420、5754–5925；仅所列有界准入/生成/消费/配置。
- [固定源码 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)（implementation）：452–467；仅所列有界准入/生成/消费/配置。
- [固定源码 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py)（implementation）：2029–2029、3192–3209；仅所列有界准入/生成/消费/配置。
- [固定源码 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/launcher_codegen.py)（implementation）：27–29、58–78；仅所列有界准入/生成/消费/配置。
