---
type: Guide
title: torch_npu Inductor Triton matmul kernel 家族：注册门、模板选择栈与 tiling 生成
description: 记录主线 _inductor/kernel/ 矩阵乘族的注册链（mm/addmm/bmm/grouped_mm/multi_slice_concat）、tuned_mm 的候选选择栈与四个 NPU Triton 模板门槛、_gen_tile_combos 与 optimize_tiling 的 aclnn 级 tiling 移植、bmm 退化分解与 multi_slice_concat 回退条件，及发布版无 kernel/ 目录的边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/__init__.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/mm.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/mm_common.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/bmm.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/mm_grouped.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/multi_slice_concat.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/kernel/optimize_tiling.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/ascend_custom_passes/register_custom_pass.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/__init__.py
  role: implementation
created_at: '2026-11-12T06:50:18Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu Inductor Triton matmul kernel 家族：注册门、模板选择栈与 tiling 生成

## 固定版本与适用范围

`torch_npu/_inductor/kernel/` 是主线 pin（ac0e1564）独有目录（mm.py 2619、bmm.py 1902、mm_common.py 79、mm_grouped.py 305、multi_slice_concat.py 355、optimize_tiling.py 1111，wc -l 实测；另有 flex_attention 系列五件，其中三件已被既有卡引用，不在本卡范围）。发布 pin（f3ecfe4a）`torch_npu/_inductor/` 下无 `kernel/` 目录（`ls` 报不存在，全 pin `find torch_npu -type d -name kernel` 零命中）；发布版 `_inductor/__init__.py` 全文（160 行）只有 `_register_npu_inductor_fallbacks` 与 `_register_npu_inductor_decompositons`，rg `_register_npu_inductor_mm|addmm|bmm|grouped|multi_slice` 零命中——发布版没有这套 lowering。本卡只写主线 Triton 后端（`TORCHINDUCTOR_NPU_BACKEND` 缺省 default）的矩阵乘族；DVM 后端只从 kernel/ 取 flex_attention（`_load_dvm_backend`，`:163-177`）；triton_experimental 隔离树另见既有卡族。ATen 层的 matmul 分发（MatmulByBmmV2 等）是另一层，不与本卡互相推导。静态阅读口径：未编译任何 kernel、未执行选择算法。draft、platforms 为空。

## 注册门

`_load_triton_backend`（`_inductor/__init__.py:284-305` 逐行读）：`npu_config.enable_full_lowering_fallback.strip() == "allfallback"`（env `NPU_INDUCTOR_FALLBACK_LIST`，分支 `:293-294`）时**跳过** `_register_npu_inductor_fallbacks()` 与 mm/addmm/bmm/grouped/multi_slice 这组命名注册函数，改走 `_enable_full_lowering_fallback()` 的整树 fallback 策略——该策略自身仍可注册 handler，不能说成“不注册任何 lowering”；否则（`:295-302`）依次 `_register_npu_inductor_fallbacks()`、`_register_npu_inductor_mm()`、`_register_npu_inductor_addmm()`、`_register_npu_inductor_bmm()`、`_register_npu_inductor_grouped_mm()`，`multi_slice_concat` 单独受 `TORCHINDUCTOR_ENABLE_MULTI_SLICE_CONCAT`（默认 False）控制；`_register_npu_inductor_flex_attention()`（`:304`）与 `install_device_lowering_dispatch(LOWERING_OVERRIDE_OP)`（`:305`）位于分支之外，两种模式下均无条件执行。`kernel/__init__.py`（5 行全文）只做 re-export。fx 侧配套 pass 的总开关在 `fx_passes/ascend_custom_passes/register_custom_pass.py:24-29`：`DEFAULT_SHUT_DOWN_PASSES` 按 `TORCHINDUCTOR_ENABLE_FUSED_MATMUL_RELU`/`TORCHINDUCTOR_ENABLE_GRAD_MATMUL_TRANSPOSE_OPT`/`TORCHINDUCTOR_ENABLE_MULTI_SLICE_CONCAT`/grouped fusion 四个配置项决定 `sink_pointwise_cat_pass`、`multi_slice_concat_pass`、`grad_matmul_transpose_opt_pass`、`fused_matmul_relu_pass` 是否关闭（pass 本体不在本卡范围）。

## `tuned_mm` 候选选择栈（mm.py:2115-2259 逐行读）

`register_lowering(aten.mm)` 后，按序累积 choices，最终 `autotune_select_algorithm` 选优：

| 候选源 | 实际门槛 | 动作 | 失败/版本边界 |
| --- | --- | --- | --- |
| `aten_mm.bind` | `use_aten_gemm_kernels()`（torch 上游开关） | 直接加入 extern 候选 | 门槛不满足则完全不加入，不是回退项 |
| CATLASS | 输入连续（mat1/mat2 均按 size/stride 判连续）+ `_is_static_problem` 非零 + `use_catlass_template("mm",...)`（op 在 `catlass_enabled_ops`、`m*n*k` ≥ `catlass_backend_min_gemm_size`、NPU dtype fp16/bf16/fp32、`max_autotune`、CATLASS 后端可用且可导入） | `CATLASS1xGemmTemplate.add_catlass_gemm_choices` | 细节见[Catlass autotune 卡](torch_npu_inductor_catlass_autotune.md)，本卡不重复 |
| CK / Cpp | `use_ck_gemm_template` / `use_cpp_gemm_template`（torch 上游判定） | `CKGemmTemplate`/`CppGemmTemplate.add_choices` | torch 上游模板，本卡不展开 |
| 基本 Triton 模板（CV 融合） | `is_nonzero` + `use_triton_template(layout)`（`utils.py:50-73`：is_gpu 且 NPU dtype ∈ {fp16,bf16,fp32}（可选扩 int32/float8）+ `max_autotune` + TRITON 后端 + `BackendFeature.TRITON_TEMPLATES`） | `add_npu_triton_mm_choices`（mm.py:1078-1130）：`_get_npu_mm_configs` 产出的每个配置生成 `npu_triton_mm_template` choice；模板经 `{{store_output}}` 支持逐元素 epilogue 融合 | 生成异常记 WARNING 日志（`:2176-2177`，`log.warning(..., exc_info=True)`）并跳过该候选，不中断注册；成功添加才记 debug 日志——与 `_gen_tile_combos` 里 `get_optimized_tiling` 失败仅记 debug 是两条不同路径，不得互推 |
| persistent 模板 | 同上 + M/N/K 全为字面量（符号维度直接返回空表，`_get_npu_persistent_mm_configs:1165-1175`） | 常量烤进 kernel：`GROUP_M` 取 `NUM_BLOCKS_M` 的 ≤8 因子（`_gen_group_m_options` 给 {8,4,2,1} 中整除者，避免运行期 `%` 运行值）；`NUM_SMS=min(num_blocks, NUM_CUBE_CORES)`；`NUM_TILES_PER_PROGRAM=ceil(num_blocks/NUM_SMS)`；`num_stages/num_warps=4` | 源码注释明示常量与真实形状不符会**算错结果**（漏 tile/错映射），因此动态形状一律跳过退回基本模板 |
| resident-B 模板 | 静态形状 + `N≥16`（`n<16` 直接空表：BLOCK_N 上取整到 16 会使 DMA 越界读，触发 AICore trap 507015，源码注释原义）+ `round16(N)*round16(K)*元素字节 ≤ L0B 64KiB`（`mm_common.py` 常量）；m 轴不足 `16*num_cube_cores` 时按 `ceil(m/16)` 收缩核数；MMAD N 分形安全上限再过滤 | B 全量驻留 L0B，BLOCK_N=round16(N)、BLOCK_K=K，沿 M-tile 流式；只生成默认 auto multi-buffer 变体（"no-l0c" 变体在该模板 precompile 必败，源码注释原义） | 超任一门槛返回空表静默放弃，其他模板仍可用 |
| resident-A 模板 | 静态形状 + `M≥16`（同 trap 理由）+ `round16(M)*round16(K)*元素字节 ≤ L0A 64KiB` + `round16(M)≤512 且 round16(K)≤512` | A 驻留 L0A，BLOCK_M=round16(M)、BLOCK_K=K，沿 N-tile 流式 | 同上静默放弃 |
| `external_matmul` | torch 上游 config 列表 | `lazy_register_extern_choice(k).bind` 逐个追加 | 上游机制 |
| 兜底 | choices 为空 且非 aten-kernel 且 `autotune_fallback_to_aten`；或 `autotune_select_algorithm` 抛 `NoValidChoicesError` 且 `autotune_fallback_to_aten` | 回退 `aten_mm.bind(...).output_node()`（warning 日志） | `autotune_fallback_to_aten=False` 时 `NoValidChoicesError` 原样抛出 |

`addmm`（`_register_npu_inductor_addmm`，mm.py:2260 起）共用同一生成器族；`_get_npu_mm_configs` 的 docstring 明示 addmm 路径 `max_block_dim=128`（bias epilogue 增加寄存器压力），tuned_addmm 头部另有"无有效 catlass 模板时先用 fallback handler"的注释与 `addmm_args` 公共参数整理（读到 2320 行为止，其后模板组装细节未逐行读）。

## tiling 生成：`_gen_tile_combos` 与 `optimize_tiling`

`_gen_tile_combos`（mm.py:937-1001 逐行读）：

- BLOCK_M 候选 = M 在 `[16, min(M,max_block_dim)]` 的因子（优先，消除 padding）∪ 16 对齐标准值（256/128/64/32）回退，≤5 个降序（`_gen_block_m_candidates`，读到 809 行）；BLOCK_N 同法取前 3；BLOCK_K 取前 2。
- L0C 面积过滤：`BLOCK_M×BLOCK_N ≤ 256KiB/4 = 65536` 元素（累加器恒按 fp32 预算，`ACCUM_BYTES=4`）。
- 组合为 M×前3N×前2K 的受限笛卡尔积；全被过滤时保底最小 tile；最后把 `get_optimized_tiling` 的 `(mL1,nL1,kL1)` 追加为一个额外组合（去重，失败仅 debug 日志）。

`optimize_tiling.py` 的 `_get_optimized_tiling`（945-1080 逐行读）是 aclnn MatMulV3 tiling 的仓内移植（docstring 原义"aclnn-quality tiling configs"）：dtype 支持 fp16/bf16/fp32/int8（未知按 2 字节）；`is_streamk_capable` 判定后二选一——StreamK 路径（`do_streamk_tiling`：甜点区把 mCnt/nCnt 拉近 `AIC_NUM/2`、halve-base 判定、DPSK 尾核分配、L0A 预算内求 baseK、bias 时 stepK 收缩为 3、`dbL0C` 按 `base_m*base_n*4*DB≤L0C` 双缓冲、fp32 长K 走 splitK 检查）或 BASIC_ASWT 路径（ResetBase→GetRebalanceBlock→CalcTailBasicBlock→CalL1Tiling→full-load/fixpipe/splitK 覆写：A 或 B 整体驻留 L1 的判定与执行、ON_THE_FLY fixpipe 时 ATrans 的 stepK 重算）。产出 dict 含 `mL1/nL1/kL1/l1BufferNum/l0cDB/baseM/baseN/baseK/stepM/stepN/stepKa/stepKb/usedCoreNum/ubDB/splitKBase`。`optimize_tiling.py` 的平台常量是**优化器文件内写死的字面值**（`:9-17`：`AIC_NUM=28`、`AIV_NUM=56`、`UB_SIZE=253952`、`L1_SIZE=512KiB`、`L0A_SIZE/L0B_SIZE=64KiB`、`L0C_SIZE=256KiB` 等，另有 `:19-27` 的频率/带宽默认值），不随设备属性或 `NPU_DEVICE_LIMIT` 变化；`mm_common.py` 侧的 `L0A_BYTES/L0B_BYTES=64KiB`、`L0C_BYTES=256KiB`、`L1_BYTES=512KiB`、MMAD 16×16 分形、`MIN_WAVES=3`、`L1_BUFFER_COPIES=2` 是该文件自己的字面容量（注释自述取自 catlass/arch.hpp、设备属性不报告故写字面），而核数 `NUM_CUBE_CORES=num_cube_core`（经 config 惰性解析，`NPU_DEVICE_LIMIT` 生效）来自设备侧推导。两个来源相互独立：即使个别数值相等也不构成同源或同一查询口径的证明（mm_common.py 79 行全文读；optimize_tiling.py:9-27 常量段已核）。`get_optimized_tiling` 的消费者是 mm.py 与 bmm.py（rg 确认两处导入）。

## bmm（bmm.py:1777-1902 逐行读 + `_degenerate_axis`:1540）

| 实际门槛 | 动作/分配 | 失败/版本边界 |
| --- | --- | --- |
| 两个输入设备均为 CPU | 内存受限分解：`mat1.get_size()[1]==1` 或 `mat2.get_size()[2]==1` 时 unsqueeze+mul+sum_；否则按"最后两维有一维连续"的偏好布局做 `require_contiguous`（FlexibleLayout 才允许） | 仅 CPU 输入路径；NPU 输入不触发 |
| `_degenerate_axis`：M/N/K 有字面量 1（符号维度不算，`int()` 试探抛错即非字面量） | 同样的 unsqueeze+mul+sum_ 分解，使结果成为普通 pointwise/reduction 节点，epilogue 可由调度器常规融合 | 源码注释原义：字面 1 才能烤进索引；一次 trace 恰为 1 的符号维度留给模板 |
| 正常路径 | choices：aten（`use_aten_gemm_kernels`）→ CATLASS（`batch_stride_largest_or_zero` 且后两维连续 + static + nonzero + `use_catlass_template("bmm",...)`）→ CppBmm → CK → Triton bmm 模板：`static_shape and is_contiguous_input` 时 `batch=int(mat1.size(0))`（批数烤进循环的 T2/T3 变体），否则 batch=0 只给通用模板；空 choices 时补 aten_bmm 兜底（warning） | `autotune_select_algorithm("bmm", ...)` 无独立 NoValidChoicesError 回退分支（与 mm 不同） |

## grouped_mm 与 multi_slice_concat

`_register_npu_inductor_grouped_mm`（mm_grouped.py:274-305）为自定义算子 `torch.ops.npu.npu_grouped_matmul` 注册 lowering，进 `_tuned_grouped_mm_common`（`:157-212`）：`check_catlass_support(mat_a,mat_b,bias,scale,offset,group_list,group_type,group_list_type,act_type,output_dtype)` 不满足时直接 `fallback_handler(torch.ops.npu.npu_grouped_matmul.default)` 回退（`:176-189`）——回退目标是**自定义 NPU 算子** `torch.ops.npu.npu_grouped_matmul.default` 的 eager/fallback 路径，不是 aten_mm，也不据此推断 CPU 执行或与 aten.mm 等价；满足时整理 `grouped_mm_args`、计数器 `aten_mm_info`、可选 tensor 输入 realize 后组装 choices（尾部组装段未逐行读）。

`_register_npu_inductor_multi_slice_concat`（multi_slice_concat.py:234-355 逐行读）为 fx pass 产出的 `MULTI_SLICE_CONCAT_TARGET` 注册 lowering。先 `_dedup_inputs` 去重同源输入；UB 预算 `_max_tile_elems = _ub_bytes() // min(max(1,n_segments),8) // esize`（`_ub_bytes` 从 triton-ascend `graph_ub_budget_bytes_for_arch(arch)` 读，读不到回退 192KiB 并告警；`_ALIGN_BYTES=32`、`_MAX_BLOCK_ROWS=256`）。回退到逐 slice 拷贝（`per_slice_copies` fallback handler）的全部条件：

| 回退条件 | 说明 |
| --- | --- |
| 同名 view 布局不一致 | `_dedup_inputs` 返回 None（warning） |
| `cat_dim` 非 0/1 | 模板只支持这两维 |
| 源 dtype 混合或不属于 `MULTI_SLICE_CONCAT_DTYPES` | 公开算子故重查 |
| 任一 mask 非 bool | 行掩码模板要求 |
| `cat_dim=0` 且 widths 不唯一 | 该维度拼接需等宽 |
| 最宽段 tile（32 字节对齐后）超 UB 预算 | 单行超预算无法再切（BLOCK_ROWS≥1） |
| 无模板配置可编译 | `maybe_append_choice` 后 choices 为空 |

通过后输出 `FixedLayout`（cat_dim=1 时 `[rows,total]`，cat_dim=0 时 `[rows*len(widths),widths[0]]`），grid 覆盖段行而非输出行；**无 store_output 钩子**——融合 epilogue 会被 codegen 静默丢弃，故 `V.graph.no_fuse_buffer_names.add(out.get_name())` 显式禁止再融合（源码注释原义）。

## 失效边界与版本边界

- `allfallback` 模式**跳过** mm/addmm/bmm/grouped/multi_slice 这组命名注册函数、改走 `_enable_full_lowering_fallback()`（`:293-294`）；它既不是“注册整套矩阵乘 lowering”，也不能断言“零注册”——fallback 策略自身仍可注册 handler，flex_attention 注册与 dispatch 安装在分支外照常执行。用户手写 Triton kernel wrapper 仍被保留（config 注释原义）；“全 fallback”不等于禁止手写 kernel。
- persistent/resident 模板只在静态形状出现；动态形状最多用到基本 Triton 模板 + aten/CK/Cpp/CATLASS。
- 发布 pin 无本目录与注册链（本卡开头的全 pin 定向 `find`/rg 记录）；release 上 mm/bmm 走 aten 与其扁平 heuristics（见[发布版扁平接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)）。`TORCHINDUCTOR_ENABLE_MULTI_SLICE_CONCAT` 等默认值与解析细节见[配置解析卡](torch_npu_inductor_config_parsing.md)，本卡只记消费点。
- 静态口径：所有“最优/更优”语义都指 `autotune_select_algorithm` 的选择机制，本卡未运行任何测量，不携带任何形状或模型上的性能结论；`from .optimize_tiling import get_optimized_tiling` 的数值门槛（AIC_NUM 等）以源码常量为准，未做设备复算。
