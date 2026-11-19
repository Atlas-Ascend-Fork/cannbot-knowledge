---
type: Guide
title: torch_npu 主线 fasta_autotune 候选生成与批量测量：FastAConfig/TileConfig、FastATileGenerator 候选桶、BinaryBucket 与 profiler 统计
description: 记录主线 runtime/fasta_autotune.py 中 FASTA 主算法面之外的其余段：头部 imports、FastAConfig 与 TileConfig 数据面、FastATileGenerator.descend_split_tiling 的桶/子块枚举（Expert ceil-divide 与常规 core 扫描两套生成器、乘积枚举与 UB/核数过滤）、BinaryBucket 二分编译边界与 ProfileValue 排序数据类、benchmark_all_configs_with_std 中段的清 L2 批量 profiler 测量；主算法面归 FASTA 补丁链卡，两段拼合即为该文件全文。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/fasta_autotune.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/tile_generator.py
  role: implementation
created_at: '2026-11-12T13:18:38Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 主线 `fasta_autotune` 候选生成与批量测量：FastAConfig/TileConfig、FastATileGenerator 候选桶、BinaryBucket 与 profiler 统计

## 固定版本与适用范围

主线 pin（ac0e1564）`runtime/fasta_autotune.py`（1666 行）。[FASTA 补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)持有主算法面 `:25-142`（FastASetting 单例与默认超参）、`:506-795`（NPUFastABucket）、`:841-1465`（NPUFastAutotuner 类体与 Expert/SampleStack 决策）、`:1525-1666`（文件尾）；本卡覆盖其余四段：`:1-24`（imports）、`:143-505`（FastAConfig/TileConfig/FastATileGenerator 候选生成）、`:796-840`（BinaryBucket/ProfileValue）、`:1466-1524`（`benchmark_all_configs_with_std` 中段），两卡拼合即为该文件全文。`FastATileGenerator(TileGenerator)` 的基类预算常量已由补丁链卡钉住（`tile_generator.py:109-163`）；`NPUFastAutotuner.__init__` 退出门与 `_use_fasta_autotune` 选点不重复。发布 pin（f3ecfe4a）无 `fasta_autotune`（补丁链卡负证据，不重跑）。纯静态阅读；draft、platforms 为空。

## 头部 imports（`:1-30`）

上游侧：`Config`/`next_power_of_2`（torch._inductor.runtime）、`triton`/`torch`/`numpy`/`pandas`；本仓侧：`TileGenerator`（.tile_generator）、`NPUCachingAutotuner`（.triton_heuristics）、`npu_config`、`get_byte_per_numel`/`NPUKernelType`、`log`、`simple_trace_handler`（..profiler）——`np`/`pd`/`simple_trace_handler` 均为本卡覆盖的批量测量段（`:1466-1524`）服务。

## FastAConfig 与 TileConfig（`:143-209`）

- `FastAConfig(Config)`（`:143-166`）：在基类字段外新增 `num_vector_core/ub_size/ub_usage/vector_core_num/core_usage=None`、`from_expert=False`（baseline）、`real_ub_size=-1`、`circle_num=-1`；`add_core_ub_info`（`:157-162`）填核/UB 信息并算 `core_usage = core_num / num_vector_core`；`get_config_info`（`:164-166`）格式化输出（含 from_expert）。
- `TileConfig`（`:169-209`）：`blocks`/`sub_blocks` 列表 + `vector_core_num`/`ub`；`cal_vector_core_num` = split 轴 `ceil(numel/block)` 连乘（grid 口径）；`cal_ub_size` = tiling 轴 sub_blocks 连乘（UB 元素口径）；`cal_circle_num` = `ceil(block/sub_block)` 连乘；`generate_base_config` 把 blocks/sub_blocks 按 `block_name`/`sub_block_name` 映射成 cfg dict（tiling 值可经 `deal_function` 后处理，默认恒等）。

## `FastATileGenerator` 候选生成（`:212-503`）

状态：`expert_configs/aligned_numel_num/num_vector_core/max_ub_size_numel/configs`（`:218-222`）。`add_multibuffer`（`:224-230`）显式 no-op（docstring 原义：tilegen 内不起作用，目的是减少 config 数与后续编译时间）。`calc_total_programs_by_config`（`:232-240`）= split 轴 `ceil(numel/block)` 连乘。`old_descend_split_tiling`（`:242-243`）转调基类。

**两套 block/sub 枚举器**：

| 枚举器 | block 侧 | sub_block 侧 |
| --- | --- | --- |
| `get_block_and_sub_list`（`:245-304`） | split 轴按核数倒序扫 `math.ceil(numels[axis] / use_core_num)`（`:272`，**真除法+math.ceil**）去重降序；非 split 轴固定 `[blocks[axis]]` | tiling 且非 no_loop 轴：`start_sub_block = min(aligned_numel(b), start_ub)`；`b>32` 时从 start 降序到 `stop_ub`、步长 `sub_block_step`（persistent_reduction 再补 `1..stop-1` 全档）；`b<=32` 降到 1；persistent 的 r 轴与非 tiling 轴一律 `[b, b]` |
| `get_block_and_sub_list_ceil_divide`（`:328-390`） | split 轴 `ceil_divide(numels[axis], use_core_num)`（`:364`，**整数 ceil-divide**——与上行 `math.ceil(真除)` 是两套字面实现，大 numel 下浮点精度行为可能不同，静态记录） | 先定 aligned 轴：persistent 且 `numels[r_axis[0]] % aligned_numel_num == 0`（或无非 r 轴）选 r 轴，否则 `max(not_r_axis)`；aligned 轴 stop_ub 向上对齐；sub 列表经 `cal_sub_blocks_with_circle_num`（`:313-326`：按 circle 数 1..block 推 `ceil(block/circle)`，sub < stop_ub 即停，与上一保留值差 ≥ aligned 或 <32 才收，aligned 时过 `strict_aligned_numel`——`:306-311`：`32//dtype_bytes` 对齐，小值退 `next_power_of_2`） |

`descend_split_tiling`（`:395-503`）主流程：`max_ub_size_numel = get_ub_size()×1024 // dtype_bytes`（`:396-399`，A2:192KB/A5:256KB 注释原义；`get_ub_size` 本体归补丁链卡读窗）；`aligned_numel_num = 32 // dtype_bytes`。①`use_tile_exp`（`:405-424`）：expert 底座来自基类 `old_descend_split_tiling`——`SIMD_SIMT_MIX` 依次按 `SIMT_ONLY/SIMD_TEMPLATE/SIMD` 三次生成后 extend，其余单次；全部转 `FastAConfig(num_warps=1, num_stages=1)`、`from_expert=True` 并 `add_core_ub_info`。②**非 SIMD 直接返回**（`:427-428`，fasta 只服务 SIMD，与类体退出门一致）。③无轴返回。④按方法分支：`Expert` → `get_block_and_sub_list_ceil_divide(核数扫满, stop_ub=1)`；非 tiny → `get_block_and_sub_list`（start_ub=对齐后满 UB、stop_ub=对齐后 `aligned_numel_num`、步长 aligned），若乘积枚举数 `≤ (num_vector_core − 1) × 3`（`min_avg_core_config_num=3`，`:403/451`）则改全扫（stop=1/stop_ub=1/步长 1）；tiny → 直接全扫。⑤`itertools.product` 全乘积枚举（`:468`），逐项算 grid/UB，**只留 `vector_core_num ≤ num_vector_core` 且 `ub ≤ max_ub_size_numel`** 的 TileConfig（`:478`；`core_bucket[core-1]` 仅 debug 记录）；⑥幸存者经 `generate_base_config` 转 `FastAConfig(num_warps=1, num_stages=1, from_expert=False)` + `add_core_ub_info` + `circle_num`（`:489-502`）。

## BinaryBucket 与 ProfileValue（`:795-838`）

- `BinaryBucket`（`:795-829`）：对 config_list 的二分搜索，注释原义「在 `11111100000` 里找最后一个 1」（编译结果非 None 为 1）；`get_mid_config(return_result)` 命中则左界右移并记 `result_index`，未命中右界左移；区间耗尽且从未命中时 `result_index = max(0, mid_index − 1)`——**全 0 序列退回首元素**而非 None。
- `ProfileValue`（`:832-838`）：`@dataclasses.dataclass(order=True)`，`launcher`/`config` `compare=False`，比较键为 `profiler_time/profiler_time_sem/profiler_time_std`（默认 None）——排序混合 None 与 float 的实例会 TypeError（Python 字面语义），调用方须保证已填充（静态记录）。

## `benchmark_all_configs_with_std` 中段（`:1466-1524`）

函数头与 `kernel_call` 闭包（`:1444-1461`）：**任一** launcher 超 `config.triton.spill_threshold` 即整体 `return [float("inf"), None, None]`（`:1464-1466`，首命中早退；阈值来源为 torch 上游 config，与 `bench` 的 `inductor_meta` 缺省 16 双轨，见[基准类体卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)）；`kernel_call` 只做 pre_hook（合并参数字典）→ `clone_args` → 发射——**无 `reset_to_zero_args`**（与 NPUCachingAutotuner.bench 的操作数区分不同）；`stream` 在循环体内赋值（`:1468-1469`）、闭包晚绑定。中段：`profiler_active_num=10`；**清 L2**：`l2_cache_size = 192×(1<<20)` 字节、`buffer = torch.empty(l2_cache_size//4, dtype=torch.int, device="npu")`（`:1498-1499`），每个 kernel 的 TOTAL_STEP 循环前 `buffer.zero_()`（`:1510-1511`，按 kernel 粒度非按 step）；profiler 配 `_ExperimentalConfig(aic_metrics=AiCoreNone, profiler_level=Level0, l2_cache=False, data_simplification=False)`（`:1478-1483`）；步常量 `WAIT=1/WARMUP=1/ACTIVE=this_active_num/SKIP_FIRST=1`（`:1493-1496`）；结果目录 `os.getcwd()/profile_result/triton_{md5(uuid)}`；csv 解析（`:1518-1524` 及 `:1525+`，归补丁链卡读窗）：`Name` 以 triton 开头，行数须被 kernel 数整除（否则 `IndexError` `:1529`）且均值段长 > ACTIVE（否则 `IndexError` `:1532`）；每 kernel 取**末尾 ACTIVE 行**的 `Duration(us)`，输出 `(mean, std, sem=std/√n)` 三元组（`:1533-1539`，numpy 口径）；`delete_file` 仅正常返回路径（`:1540/1543`），`IndexError` 抛出时目录保留；无 csv → `([], [], [])`（`:1544`）。与 triton_heuristics 的 `_profile_batch_benchmark`（16 步、ACTIVE=10、行数须恰为 kernel×ACTIVE、µs 求和均摊）是**两套相似但不相同的实现**：fasta 版整除校验+末尾窗口+std/sem，runtime 版精确计数+求和均摊、无 std。

## 失效边界与静态口径

- 本卡全部结论来自两 pin 静态阅读；未运行任何 fasta 生成、二分或 profiler 测量。`math.ceil(真除)` 与 `ceil_divide` 的精度差异仅按字面记录，未构造反例。
- 候选乘积枚举在轴数/枚举档位大时可能爆炸（全扫分支 `stop_ub=1`、步长 1），实际规模受 `min_avg_core_config_num` 分支与 UB/核数过滤约束；本卡未量化生成规模。
- `BenchmarkAllConfigs` 的 `re_profiling`/sem 加宽逻辑（`:1553+`）与文件尾归补丁链卡读窗，本卡不重复；`simple_trace_handler` 本体不在本卡范围。
- 与[TileGenerator 卡](torch_npu_release_flat_inductor_tile_generator_descents.md)（发布版 descend 族）的边界：发布版 `tile_generator.py` 是另一实现；本卡的 `old_descend_split_tiling` 只按基类调用事实引用。

## Evidence

- [主线 runtime/fasta_autotune.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/fasta_autotune.py)（primary；`:1-120`、`:121-320`、`:321-506`、`:793-842`、`:1430-1560` 读窗）
- [主线 runtime/tile_generator.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/tile_generator.py)（implementation；`TileGenerator.__init__` 预算常量归补丁链卡读窗引用）
