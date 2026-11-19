---
type: Guide
title: 实验 Triton select-lane：扩大加载、寄存器切片与边界条件
description: 说明非归约跨步 load 的结构记录、直接与间接内轴判定、select/strided-slice 发射和扩大读取边界，区分局部早退与编译回退。
tags:
- task.optimization
- topic.compilation
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py
  role: implementation
created_at: '2026-11-11T09:03:20Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验 Triton select-lane：扩大加载与寄存器切片

## 固定范围与目标

依据 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的实验 codegen 中完整 select-lane 记录、索引关系、加载重写、strided-slice 发射器和所列真实调用/AST helper；没有读取整个 8617 行 codegen 或默认后端实现。发布固定快照在本轮两个精确实验路径缺失，仅说明局部来源关系，不推导发布没有索引或切片优化。

这条机制在**非 reduction** 的线性化 kernel 中把部分跨步加载改成连续加载，再以寄存器级 extract_slice 取出需要的 lane。它与[permute 归约加载](torch_npu_experimental_triton_permute_gather_rewrite.md)使用不同准入和生成规则；源码中单次 DMA、逐字节相同或测时收益的注释不是本次运行结果。没有导入、执行 AST/SymPy 解释器、生成器、模板、设备或测试，平台范围未知。

## 先记录结构，不按最终字符串猜测

load 调用上游后，将原 index、结果变量、准备后的 load index 交 `_maybe_record_select_lane_load`。记录要求配置 select_extract_slice 开启、kernel 已选线性化、当前不在 reduction，结果有 name 且 index 为 SymPy 表达式。

原 index 的每个 free symbol 都必须能在 range_tree_nodes 中找到，且不是 reduction node；额外动态尺寸符号会拒绝。每个线性系数必须是 int/SymPy Integer；去掉全部线性项后的 residue 不能再含自由符号。有任一系数为 1 就拒绝，最小系数须属于 {2,4,8}。记录以结果变量名为键，保存 lane、prepared index 和输入指针名；prepared index 不是 SymPy 表达式时退回原 index，同名记录会更新。

这些门槛并没有独立检查原输入 dtype 的字节宽度、每次加载是否小于 16 字节或 UB 总预算。residue 也没有被限定为 0；不能只凭最小系数是 K，就推导所有额外读取的 K 个 lane 都落在原始物理存储内。

## 实际调用时点与 tile 几何

所读 codegen_body 的 `linearize_info is None` 分支先完成上游 body 和地址替换，处理可选的 promoted reduction rewrite 后，再调用 select-lane 重写，随后才处理 bool-vector 比较。这里只核该分支，不把它写成所有 codegen_body 路线都已经展开。

重写另要求 select_extract_slice 开启、尚未设 `_npu_select_slice_done`、不在 reduction、同时满足 `_npu_linearize` 与 `_linearize_applied`，并有 targets。遍历所有非 reduction tree 的 var_tensor_dims 建立 slot→name，合并 node_block_constexpr 为 name→tile token；重名/重 slot 按遍历覆盖，没有在此单独拒绝冲突。

取实际 tensor ndim 的最后 slot 为 inner，必须有对应 name。其他 slot 的 tile token 必须齐全；select 路线的 extract sizes 把 inner 设为 1，其他维保留 token，offsets 全 0、strides 全 1。没有 slot 或必要 token 就早退，不依赖固定的轴名称。

## 区分直接、间接与未发现内轴依赖

`_select_index_node_relation` 先看 prepared index 的自由符号名：直接含 inner_name 就立即返回 direct。否则从各 tree_node_mapping 收集表达式，沿符号名称依赖遍历，发现 inner_name 才返回 indirect，并以 visited 防止重复遍历；没有发现则两项都 False。它只基于提供的映射，不是对任意外部表达式来源的完整依赖证明。

直接依赖走 strided-slice，受另一个 select_extract_slice_strided 开关控制；间接依赖保留原行；未发现依赖才走普通 select。配置文件中两个开关初值均为 True，不代表任意运行会话都保持该值或所有 kernel 都命中。

## 普通 select：多读 K lane，保留第一个

只处理可解析的字符串 load 赋值，目标名必须在 targets 中；非字符串 DeferredLine 等原样保留。AST parser 要求单目标 Name 的 Assign，并允许 load 外层 `.to(...)` 链；其他表达式不会被当作任意通用 load 匹配。

select 路线构造 `arange(0,K)`，按 inner slot 广播，在**原 load 指针表达式**上加这一 lane 变量，保留原 mask、kwargs 和外层转换后发射扩大加载；再 extract_slice 取各维 offset=0、非 inner 维原 tile、inner size=1，得到原赋值名。

这条路没有新增一份覆盖扩大 lane 范围的物理容量检查，原 mask 会随扩大表达式使用。只有输出保留一个 lane，不等于被丢弃的 lane 完全没有被读取；原 residue/最后一行存储等前提仍须结合上游布局和真实生成结果核对，不能从注释直接认证任意偏移都安全。

## strided slice：扩大 inner，按步长取回

直接 inner 路线重新从 prepared index 计算该 inner 的系数 k，要求为整数且属于 {2,4,8}；它不简单照搬记录时全部系数中的最小 K。展开 `prepared_index-k*inner` 后仍含 inner 就拒绝；还必须取得 inner tile token。

原 load 还须有第二个位置参数，且该 mask AST 内出现 `<inner_name>mask`。否则发射器返回 None、保留原加载。命中后使用：

```text
lane = arange(0, k * inner_tile)
widened_mask = k * inner_offset + lane < k * inner_numel
address = saved_pointer + base_index + k * inner_offset + lane
extract inner size = inner_tile，inner stride = k
```

其他维的 extract size 保留对应 tile token，stride=1。mask 中该 Name 的所有匹配处由 AST 替换为 widened_mask 变量，其他 AST 结构、load kwargs 和外层 cast 保留；这里要求的是 Name 出现，并未额外分析整个布尔 mask 的极性/组合是否就是某种标准约束。

边界公式使用**当前逻辑 inner_numel**，本地没有另取原始输入物理行长度作比较。因此不能把 `k*inner_numel` 无条件称为原存储的真实边界，也不能仅凭它证明末尾所有额外 lane 都合法；上游逻辑切片长度与原布局关系仍是未闭合条件。这条路线确实多读约 k 倍 inner lane、丢弃其余，性能需要结合带宽与下游广播核对，不能套用“连续加载一定更快”。

## 发射、一次性状态与失败边界

本地 overrides.extract_slice 只把字符串参数原样插入、可迭代参数用 str 逐项拼接成列表文本，再返回 `extract_slice(...)` 表达式；没有在这个小方法执行寄存器操作、验证 offsets/sizes/strides 或解析外部 op 的设备语义。实际 import 注入、底层切片实现与代码编译不在本组展开。

扫描成功后才在 changed 时替换 body._lines；扫描走到末尾就置 `_npu_select_slice_done=True`，即使没有任何匹配行成功改变。前面的 gate/token 早退不会置该标志；“每 kernel 一次”应结合这个实际时点理解。

局部不匹配会保持原行，但整个扫描、index_to_str、SymPy/AST 操作和 overrides 调用没有统一的总 except。不能把返回 None 的若干预条件检查推广成所有发射/编译失败都会自动重试原代码，也没有在这里提供整体回滚协议。

排查时保存原/准备后 index、常量 residue、记录的最小 K 与实际 inner 系数、slot/token、直接/间接关系、扩大地址和最终 mask、extract 几何、done 标志与真实运行结果。局部重写命中不能代替越界、别名、dtype、动态尾块、数值和性能检查；本次未运行这些检查或增加 verified。

## Evidence

- [固定源码 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py)（primary）：126–151、166–194、2015–2029、2345–2377、2481–2546、4937–4977、5216–5492；仅所列有界函数/调用分支/声明，外部 IR、存储、切片 op 与设备生成另计。
- [固定源码 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)（implementation）：35–38；仅所列有界函数/调用分支/声明，外部 IR、存储、切片 op 与设备生成另计。
