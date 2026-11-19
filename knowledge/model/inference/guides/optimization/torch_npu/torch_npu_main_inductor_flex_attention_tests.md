---
type: Guide
title: 主线 Inductor flex_attention 测试族：融合边界、kernel_options 传导与源码结构契约
description: 固定提交下 test/_inductor 四个 flex_attention 运行/结构测试与 triton_experimental flex_attention 测试的断言契约，与既有 flex 实现面卡配对。
tags:
- task.testing
- topic.attention
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_flexattnetion.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_flex_attention_dynamic_mask_metadata.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_flex_attention_dynamic_mask_out.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_npu_fusion_attention_graph.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/flex_attention/test_flex_attention.py
  role: primary
created_at: '2026-11-13T00:10:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 主线 Inductor flex_attention 测试族：融合边界、kernel_options 传导与源码结构契约

## 固定版本与范围

主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的五个测试文件全文静态阅读：`test/_inductor/test_flexattnetion.py`（64 行）、`test_flex_attention_dynamic_mask_metadata.py`（118 行）、`test_flex_attention_dynamic_mask_out.py`（81 行）、`test_npu_fusion_attention_graph.py`（97 行）与 `triton_experimental/flex_attention/test_flex_attention.py`（180 行）。未运行任何测试、未编译 kernel、未创建 block mask 或 NPU 张量。全部测试带 `runIfVersion(max="2.13")` 版本门（区间求交语义见[归约/Welford 测试契约卡](torch_npu_main_inductor_reduction_welford_tests.md)）；两个 metadata 类整体 `@unittest.skip("temporarily skip for now")`（:33/:63）、dynamic_mask_out 的 decoding 分派次序测试单独 `@unittest.skip("temporarily disabled pending decoding dispatch update")`（:56）——跳过状态本身是实现意图的静态证据，断言内容仍按源码记录。

## 运行面契约

- **融合外存边界**（test_flexattnetion.py :21-39）：`torch.compile(flex_attention(q,k,v).cos())` 后断言 `metrics.num_bytes_accessed < 访问字节数*(6+1)`——`num_accesses` 基数 6 上再 +1 的 fudge 因子注释原义是"目前会写多余的 logsumexp"；外存上限按 1*8*1024*64*sizeof(float32) 计算。同文件 :42-60 断言 `kernel_options={"BLOCK_M": 16}` 经 `run_and_get_code` 生成的代码含字面量 `BLOCK_M : tl.constexpr = 16`——用户 kernel_options 到模板常量的传导是可编译期核验的契约。
- **npu_fa 前反向**（test_npu_fusion_attention_graph.py）：`NpuGraphAttentionFunction.apply`（:10-36）输出形状 q 同形、logsumexp/seed 两输出 (2,4,8,8)、第 4 输出 shape (0,)，可 backward；`torch.ops.npu_graph.npu_fa` 带 `scale=2.0`（:38-53）同形状契约；`npu_fa_backward` 在 meta 设备（:56-71）按 BSH 布局给出 dq/dk/dv 同形且 `result[3] is None`——meta 实现被显式当契约钉住；带 `scale_value=2.0` 的真机反向（:73-93）对 `aclnnFlashAttentionScoreGrad` 字样的 RuntimeError 显式容忍（pass），其余错误上抛。npu_graph 命名空间注册面由 [图注意力桥卡](torch_npu_inductor_graph_attention_bridge.md) 持有，本节只记测试侧期望。

## 源码结构契约（无设备）

- **dynamic_mask_metadata**（两跳过类）：结构类 :36-44 断言 lowering 源含 `_filter_autotune_ir_nodes`、`_attach_flex_subgraph_dependencies`、`template_buffer.subgraph_inps/subgraph_outs` 且**不含** `apply_kernel_options_from_eager_block_mask`、`flex_attention_metadata.py` 文件不存在——eager 元数据路径被移除是可文本核验的结构不变量；:47-60 用 AST 取 `flex_attention_in_loop_grid` 函数段，断言签名头部含 `min` 且源含 `min(total_tiles, meta["NUM_CUBE_CORE"])`——in-loop grid 以 Cube 核数封顶总 tile 数。运行类 :66-114：`mask_mod` 捕获动态 shape 张量（mark_dynamic 0 维）时 32/48 两种窗口尺寸共用一次编译（`counter.frame_count == 1`，CompileCounterWithBackend），block_mask 不带 `_npu_flex_attention_kernel_options` 属性，数值对 eager 参考 atol/rtol 2e-2；该类还有 IS_ASCEND950 门（:27：`torch_npu._C._npu_get_soc_version() >= 260`，注释称 950 才支持全部稀疏 mask tile 配置、910B/A2 会 NoValidChoicesError）。
- **dynamic_mask_out**：:13-27 以 `rsplit("def flex_attention_backward…")` 再 `split("fwd_placeholder_inps =")` 截取 backward 前段，断言含 `kernel_options.setdefault("PRESCALE_QK", False)` 与 `setdefault("WRITE_DQ", True)`——直接反向入口补齐这两个公共缺省（PRESCALE_QK 语义见 [后向路由卡](../../../../training/guides/torch_npu_flex_attention_backward_routes_and_gradients.md) 的 dK 累加节）；:30-43 断言 lowering 含 `flex_decoding_template`、`_use_flex_decoding(`、`_create_npu_flex_decoding_kernel`、`flex_decoding_template.maybe_append_choice(` 与 `cur_kernel_options.setdefault("USE_TMA", bool(torch.xpu.is_available()))`——短序列走社区 flex_decoding 模板（判据见 [前向派发卡](torch_npu_flex_attention_forward_dispatch.md)）；:46-53 断言模板**不含** `flex_decoding_npu`/`flex_decoding_npu_source`、含 `_wrap_upstream_template(` 与 `_upstream_flex_decoding_template`——解码模板复用上游而非独立 NPU 变体；:55-65（跳过）钉 `_use_flex_decoding(` 在 `configured_mask_out = bool(` 之前的分派次序；:67-77 断言 `backend = kernel_options.get("BACKEND", "AUTO")` 与显式 `TRITON_DECODE` 不满足判据时报 "BACKEND='TRITON_DECODE' was specified but flex_decoding cannot be used"（与派发卡的报错语义配对）。

## triton_experimental flex_attention 测试（:1-180）

文件头 `os.environ.setdefault("TORCHINDUCTOR_NPU_BACKEND", "triton_experimental")`。源码结构类 :32-52 断言：实验模板模块的 `load_flex_template` 与上游 flex.common 同一对象、`compute_sparse_mask_kernel_compact`/`compact_sparse_mask_grid` 与默认（非实验）kernel 模块同一对象——稀疏 mask 计算不复制实现；`vars(te)` 中 `flex_` 前缀导出的 kernel 名全部以 `te_` 开头（命名契约与 [源适配卡](torch_npu_experimental_flex_attention_source_adapter.md) 的 te_ 前缀/propagate_nan 改写节配对）；`_compile_copy(_register_npu_inductor_flex_attention, {}, transform=True)` 的产物与原函数**不同一**（源码复制不回写原函数）。融合预算类 :54-66：`_LINEARIZE_FUSION_CAPTURE_BUDGET`（捕获 buffer 数）与 `_NODE_BUDGET`（FX 非输出节点数）恰好在边界内时 `_prepare_linearize_fusion_options` 置 `FUSE_SMALL_SUBGRAPHS=True`，节点数 +1 或 buffer 数 +1 即 False（预算上界的测试侧镜像，实现在 [源适配卡](torch_npu_experimental_flex_attention_source_adapter.md) 的 `FUSE_SMALL_SUBGRAPHS` 重赋值节）。运行类 :80-176：bfloat16、`_check_code` 断言生成代码 import `torch_npu._inductor.triton_experimental.npu_triton_heuristics` 且**不** import `runtime.triton_heuristics`、含 `Original ATen: [flex_attention]` 注释锚；causal/score_mod/window 前向（atol 4e-2）、前反向（梯度 atol 12e-2）；:158-176 不可达 KV 尾用例（Q 384/KV 512）断言 K/V 梯度在 384 之后切片 `count_nonzero==0`——因果 mask 下 KV 尾部梯度恒零是 TE flex 路径的数值契约。

## 边界与静态口径

- 实现面归属：前向派发/判据归 [前向派发卡](torch_npu_flex_attention_forward_dispatch.md)，后向路由与 PRESCALE_QK 语义归 [后向路由卡](../../../../training/guides/torch_npu_flex_attention_backward_routes_and_gradients.md)，mask 内存路径归 [mask 内存路径卡](torch_npu_flex_attention_mask_memory_paths.md)，模板适配/预算/te_ 命名归 [源适配卡](torch_npu_experimental_flex_attention_source_adapter.md)，npu_graph 注册归 [图注意力桥卡](torch_npu_inductor_graph_attention_bridge.md)——本卡只记测试侧断言契约，不重述实现。
- 本卡为测试侧唯一承载：四个根级测试文件名与断言语义在 canonical 全树零命中（负向 rg）；`flex_attention_in_loop_grid` 的 `min(total_tiles, NUM_CUBE_CORE)` 锚、BLOCK_M constexpr 传导、num_bytes_accessed 融合边界、WRITE_DQ 缺省、动态 shape 单编译计数均为首次行级记录。
- 跳过测试的断言（metadata 两类、decoding 次序、aclnnFlashAttentionScoreGrad 容忍）是固定提交的静态意图记录，不证明当前测试套实际执行它们；所有数值 atol/rtol 均未运行验证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_flexattnetion.py)（primary）：:1-64 全文（:21-39 融合外存边界、:42-60 BLOCK_M 传导）。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_flex_attention_dynamic_mask_metadata.py)（primary）：:1-118 全文（:27 IS_ASCEND950 门、:33/:63 类级 skip、:36-60 结构断言、:66-114 动态 shape 单编译）。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_flex_attention_dynamic_mask_out.py)（primary）：:1-81 全文（:13-27 反向缺省、:30-43 解码模板、:46-53 上游复用、:55-65 skip 次序、:67-77 TRITON_DECODE 拒绝）。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_npu_fusion_attention_graph.py)（primary）：:1-97 全文（:10-36 apply 形状、:38-53 scale、:56-71 meta 反向、:73-93 容忍子句）。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/flex_attention/test_flex_attention.py)（primary）：:1-180 全文（:32-52 组件同一性、:54-66 预算边界、:80-176 运行契约与 KV 尾零梯度）。
