---
type: Guide
title: torch_npu 发布版 TileGenerator 裁剪决策链（descend_* 本体与两 pin 预算演进）
description: 记录发布 pin codegen/tile_generator.py 253 行全文本：字面 1024//dtype_bytes 停止预算、64KiB 候选上限、split 轴不 32 字节对齐、halve/quarter-step/last-split 三种下降策略与 persistent r 轴冻结、low_dim 20% 平衡护栏；对照主线 runtime 版 574 行的 ub_size/input_ptr_num/tiny_kernel/program_threshold 设备推导预算、递归多轴下降、multibuffer 与 SIMT num_warps 扫描、UB 溢出有界重试。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/codegen/tile_generator.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_triton_heuristics.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/tile_generator.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/runtime/triton_heuristics.py
  role: implementation
created_at: '2026-11-12T08:39:57Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 发布版 TileGenerator 裁剪决策链（descend_* 本体与两 pin 预算演进）

## 固定版本与适用范围

发布 pin（f3ecfe4a）`torch_npu/_inductor/codegen/tile_generator.py`（253 行全文逐行）。主线 pin（ac0e1564）对应文件为 `_inductor/runtime/tile_generator.py`（574 行全文逐行）。两文件 `diff -q` 字节不同，本卡给出**语义级**对照而非逐字节谱系：release 版停止预算是字面常量、主线版本改为设备属性推导，下降算法从单轴循环演进为递归多轴。消费点：release 由 `npu_triton_heuristics.py` 的 `triton_config_npu_index` 构造并调 `descend_split_tiling()`（import 锚 `:72`，构造细节 `:1132-1174` 见[发布版扁平接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)，本卡不重复）；主线由 `runtime/triton_heuristics.py:97` 导入，在 `_triton_config_npu_index_legacy`（`:3916-3930` 定向读）按 `_use_fasta_autotune` 与 `TileGenerator` 二选一，并从 `triton_meta["signature"]` 数 `input_ptr_num`、从 `inductor_meta` 读 `npu_kernel_type`（缺省 "simd"）。纯静态：未运行任何配置生成或编译。draft、platforms 为空。

## release 版预算与候选门槛（`__init__`/`:13-53` 与工具方法）

| 实际门槛 | 动作 | 失败/版本边界 |
| --- | --- | --- |
| 轴既不在 `tiling_axis` 也不在 `split_axis`（`:33-37`） | `blocks/sub_blocks` 该轴置 1，不参与裁剪 | split 轴记名 `XBLOCK`、tiling 轴记名 `XBLOCK_SUB`（`:38-41`） |
| `stop_numel = 1024 // dtype_bytes`（`:28`；dtype None 按 1 字节，`:63-67`） | 字面 1KiB 元素预算，全下降循环的目标体积 | **不随设备/UB 属性变化**；主线版本改为多因子推导（见下节） |
| `valid_tile_numel`：候选总体积 ≤ `16384*4 // dtype_bytes`（`:69-72`，字面 64KiB） | 超限候选直接不入表（`:112`） | 主线版本此上限改为 `ub_size`（SIMT 时 128KiB）推导 |
| `aligned_numel`：32 字节对齐（`:56-61`，min_numel = 32//dtype_bytes） | 只用于 **tiling 轴** 候选值（`:98-100`） | **split 轴直接写原始 blocks[axis]，不对齐**（`:96-97`）；主线版本两轴都过 `aligned_numel_32byte`（`:240-250`）——对齐面是真实语义差异 |
| `calculate_total_numel`（`:80-93`） | 名义上对 `candidate_blocks` 逐候选取最小，实际**不是**逐候选最小值：内层函数忽略 `candi_blocks` 参数、恒乘**当前** `self.sub_blocks` 的 tiling 轴乘积——候选表非空时每轮测得同一当前值，空表返回 `sys.maxsize` | 参数被忽略对下降算法结果的影响未验证，静态记录、不推断无害；主线版本内层改读全部 sub_blocks 乘积（`:225-238`，口径亦不同） |

## release 版下降决策（`descend_one_axis`/`:115-180`、`descend_all_low_dims`/`:183-217`、`descend_split_tiling`/`:219-253`）

`descend_one_axis(axis, is_split)`：外层 `thread = 30` 次上限（`:130-131`），每轮先把 `candidate_blocks` 全部 `add_to_configs`，再判断：

| 分支门槛 | 动作 | 失败/版本边界 |
| --- | --- | --- |
| 最小体积 ≤ `stop_numel`（`:137-141`） | 把当前 `blocks` 也入表，`reached_stop_numel=True` 结束 | |
| 该轴 numel == 1（`:143-146`） | `blocks` 入表后结束（**不带** reached 标志） | 调用方据此继续走后续下降阶段 |
| split 轴 + persistent_reduction + 轴名以 "r" 开头（`:148-151`） | 直接置 reached 结束，**不下降 r 轴** | persistent 归约的 split r 轴被冻结 |
| split 轴 + `total_programs > num_vector_core`（`:152-157`） | `calcu_last_split_blocks`（`:43-53`）：按 split 顺序轴前缀的 grid 数反推 `last_splits = num_vector_core // splits`，取 `ceil(numels[axis]/last_splits)` 作为该轴 block，与当前不同则采纳并入 candidate | `num_vector_core` 来自 `_inductor/config.py` 设备推导（910B 上 `num_cube_core*2`，release config `:95-96`），这是该文件唯一设备相关量 |
| split 轴 + `total_programs > num_vector_core//2` 或 dual_reduction（`:158-162`） | candidate 列表保底 3 条（超 2 先 pop(0)）后追加当前 blocks，置 `slow_decend_split` | |
| 快速下降（not slow）：`blocks[axis] = numel//2`；慢速：`step = numel//4 if >1 else 1`，`blocks[axis] = numel - step`（`:164-170`） | halve 或 quarter-step 两种粒度 | 慢速沿 numel 递减而非减半，逼近核数阈值时更细 |
| split 轴收尾：blocks[axis]==1 且 programs 仍 > nvcore//2 或 dual（`:171-173`） | 追加 candidate | |
| 非 split（tiling）轴：numel ≥ 32 → `next_power_of_2(numel//2)`；否则 `numel-1`（`:174-179`） | 幂次或逐减 | 与主线 `descend_tiling_axis` 尾段同形（主线 `:342-347`） |

`descend_all_low_dims`（`:183-217`）：low_dims 各轴联合下降；跳过 persistent r 轴（`:190-191`）与 numel==1；**20% 平衡护栏**——与当前 low_dims 最小值相差不足 20% 的轴跳过（`:195-196`）；numel≥128 幂次减半、否则 `min(aligned_numel(numel//2), next_power_of_2(numel))`（`:197-202`）；外层 `count < 100` 上限（`:206`）；一轮无变化时去掉护栏重跑 `descent_all_axis(0)`（`:214-215`）。

`descend_split_tiling`（`:219-253`）：`while True` 体实为**单趟**——先 split 轴逐个 `descend_one_axis(is_split=True)`（任一 reached 即 break），否则以第一条 candidate 重置 `sub_blocks`（`:246-247`）再下降非 low_dim 的 tiling 轴，最后 `descend_all_low_dims()`，三条路径全部 break（`:242-253`）。因此 release 的候选来源是"split 优先、tiling 补充、low_dims 收尾"的一条链，不是多轴笛卡尔积。入表配置恒 `Config(cfg, num_warps=1, num_stages=1)`（`:113`）。

## 主线版（574 行全文）的预算与算法演进

预算（`__init__` `:111-162`）：`stop_numel = min(max_numel_threshold, max_total_numel // num_vector_core) // 8`（`:136`），其中 `max_numel_threshold = local_mem_size // input_ptr_num // dtype_bytes`（`:134-135`，`local_mem_size`：SIMT_ONLY 时字面 128KiB，否则 `config.ub_size`；`input_ptr_num` 取 3 或签名中 ptr 参数数上限 3，`:132`）；`tiny_kernel = max_total_numel < 128*1024`（`:131`）；`program_threshold` 按 tiny/SIMT 在 `num_vector_core//8` 与 `//2` 间取，再 `min(max_total_numel//128 - 1, ...)` 并 floor 0（`:147-153`）；新增 `no_loop_axis` 与 `real_tiling_axis` 预过滤（`:155-161`，剔除 no_loop 与 persistent r 轴，`rebuild_dynamic_axis` `:165-174` 对 >3 个 tiling 轴且 low_dim 体积乘积未超 4KiB 时把 low_dim 提升进 no_loop）。

算法：split 轴改为 `descend_split_axis_inner(axis_index)` 递归——先按 `can_add_initial_shape` 门槛补初始形状（`:366-374`），再递归进下一 split 轴并 save/restore blocks/sub_blocks（`:377-382`）；candidate 改为去重元组集合（`:420-421`/`:428-429`）；`total_programs > num_vector_core` 时采纳 last-split 后**立即 break**（`:416-423`）；tiny_kernel 在下降中即时入表（`:430-431`）。tiling 轴 `descend_tiling_axis` 同样递归下一个 real_tiling 轴（`:310-318`）。`add_to_configs`（`:270-286`）改回 bool 且门槛更多：超 `max_numel_threshold` 拒绝；配置数 <10 或 tiny 时不再拒小体积，否则拒 `total_numel < stop_numel + 100`（`:274`）；SIMT_ONLY 临时检查 `total_numel*dtype_bytes > 8KiB` 拒绝（源码注释原义"tmp check ... will be removed latter"）；`fill_config` 注入 `compile_mode`（`:251`）且 `Config(num_warps=1, num_stages=2)`（`:285`）。收尾新增：非 SIMT 时 `tune_multibuffer` 把每个配置复制一份 `multibuffer=True`（`:489-496`）；SIMT 时 `tune_simt_num_warps` 以 `[8,16,32,64]` 笛卡尔展开（`:498-506`）；SIMT_ONLY 且存在 0 余块配置时按 `cal_cfg_remain_programs`（`:253-262`）排序并**丢弃全部非 0 余块配置**（`:558-573`，源码注释给出 mask 循环优先的两条理由）。模块级 `ub_overflow_retry_configs`（`:19-105`）：编译 UB 溢出失败后，选 required/available 比最差的种子配置，按 20% 余量（`*4//(required*5)`，`:73`）定目标体积，沿一条链 halve 到目标以下，追加 ≤4 个新配置交编译验证；消费点在主线 `runtime/triton_heuristics.py:1098-1110`（`_ub_retry_attempted`/custom_kernel/group_enabled 三重门槛内调用，rg+定向读确认）。

## 失效边界与静态口径

- 本卡只描述配置生成算法的静态决策，未运行任何生成/编译/测量；"更优 tiling"语义不存在于本卡。
- release 版 `stop_numel` 1KiB 与主线 `//8` 因子都是**源码常量**，与任何硬件查询值的一致性未核，不互推（optimize_tiling 字面常量口径不变）。
- 主线 `_triton_config_npu_index_legacy` 中 `FastATileGenerator` 分支、`NPUKernelType.SIMD_SIMT_MIX` 双遍生成（`:3920-3921` 之后未逐行）未在本卡展开；fasta 机制见[主线 runtime 补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)。
- release 消费端 `triton_config_npu_index` 的 `split_axis_dtype/dual_reduction` 传参面由[发布版扁平接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)闭合，本卡不重复；两卡互链不重叠。
- `descend_one_axis` 的 30 次与 `descend_all_low_dims` 的 100 次是循环护栏，非行为承诺；静态记录。

## 相邻卡边界

[发布版扁平接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)（triton_config_npu_index 消费面）、[主线 runtime 补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)（主线 fasta/五类 autotuner）、[矩阵乘 kernel 家族卡](torch_npu_inductor_triton_matmul_kernel_family.md)（mm 侧 `_gen_tile_combos` 是另一套 tiling 生成，不与本卡互推）。
