---
type: Guide
title: torch_npu triton_experimental 静态/快速 launcher 测试契约：资格判定、工件适配、pickle 恢复、胜者卸载与标量 ABI
description: 记录主线 test/_inductor/triton_experimental 静态 launcher 集成测试（1553 行全文）、fast launcher 测试（520 行全文）与共享 utils（110 行全文）的测试侧契约：can_statically_launch 的钩子/运行时支持/workspace/用户自定义内核门、_arg_kind 标量映射、host args layout 与尾指针、npubin pickle 往返与缓存恢复、autotune 胜者卸载时序与拥有者生命周期、静态路径不构造普通 launcher 的正向证据、signed/unsigned/bool/float 标量 ABI 字面指纹、fast launcher 的构建克隆全局/失败不缓存/胜者替换/特殊调用旁路/降浮点包装、TASK_QUEUE_ENABLE=0/1 变体声明。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_static_launcher_integration.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_triton_experimental_fast_launcher.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/fast_launcher_test_utils.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/static_launcher/compile_result.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/static_launcher/adapter.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py
  role: implementation
created_at: '2026-11-12T14:58:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu triton_experimental 静态/快速 launcher 测试契约：资格判定、工件适配、pickle 恢复、胜者卸载与标量 ABI

## 固定版本与适用范围

主线 pin（ac0e1564）`test/_inductor/triton_experimental/`：`test_static_launcher_integration.py`（1553 行全文）、`test_triton_experimental_fast_launcher.py`（520 行全文）、`fast_launcher_test_utils.py`（110 行全文）。文件头自我声明：单元+进程内验收，静态支持缺失时**正测试失败**（不是跳过）；FXGraph 缓存测试只做内存态重置+磁盘重载，不证明新进程/worker 恢复；启动期环境变量解析与 raw-only 恢复不在本套件；用户 `@triton.autotune` 仍走上游启发式，不计入 experimental 后端覆盖；fast launcher 参照本仓 PyTorch b62a09d1dd4 的 `TestFastCudaLauncher`，队列变体声明为"新进程中 TASK_QUEUE_ENABLE=0 与 =1"。设备用例 `SupportedDevices(["Ascend910B","Ascend910_93","Ascend950"])`（pure SIMT ABI 仅 950）。实现语义归 [静态 launch 契约卡](torch_npu_experimental_triton_static_launch_contract.md)与[grid/launcher codegen 卡](torch_npu_experimental_triton_grid_and_launcher_codegen.md)，C++ 侧归[原生运行时卡](torch_npu_static_launcher_native_runtime_cpp.md)。全部静态阅读，未运行任何测试；draft、platforms 为空。

## 资格判定 `can_statically_launch` 的单元契约

| 门 | strict=True | strict=False |
| --- | --- | --- |
| legacy `launch_enter/exit_hook` 属性或现代 `knobs.runtime` 钩子非空 | `CannotStaticallyLaunchNPUKernel`，消息含 "launch enter hook enabled" 等原文 | 同左（钩子门不放宽） |
| `_C._StaticNpuLauncher` 缺 API/缺绑定/`_is_supported()` 假 | `CannotStaticallyLaunchNPUKernel`，消息含 "aclrtLaunchKernelWithHostArgs" | 返回 None（静默回退，adapter 不被调用） |
| `use_static_triton_launcher=False` | 不做任何运行时探针（`_is_supported` 被 patch 成 AssertionError 也不触） | 同左 |
| workspace 必需（metadata workspace_size=1） | 抛 "workspace is required" | None + INFO 日志 "Bypassing NPU static Triton launcher for kernel {name} due to workspace is required"；name 取 `inductor_meta["kernel_name"]` > `binary.name` > "unknown" |
| `HeuristicType.USER_AUTOTUNE` 且 `static_launch_user_defined_triton_kernels=False` | 抛 "user-defined Triton kernel" | 同左（改 True 才放行） |

`prepare_for_caching`：`keep_static_cubin_raw=False`（默认）丢 `npubin_raw`，True 保留——FX 缓存落盘保留原始工件受该开关控制。

## 工件适配器与 `NPULaunchMetadata`

- `_arg_kind` 全表：`*fp32→tensor`、`i1→bool`、`u1→u32`、**`fp16/bf16→f32`（半精度标量提升为 f32 槽）**、`fp32/f32→f32`、`fp64→f64`、i8/i16/i32/i64/u8/u16/u64 原宽；`tensordesc<2>` 抛 `NPUStaticArtifactError`（Tensor descriptor 不支持）。
- 适配器过滤**声明 constexpr 与隐式常数**：`signature` 键为索引/名字/元组三种 Triton 形态都要兼容；`constants={1:128, 3:1}`（XBLOCK 显式 + equal-to-1 隐式）后 `runtime_arg_names=("out","xnumel")`、`arg_kinds=("tensor","i32")`，而 `launcher_arg_names` 保留 `("out","xnumel","implied")`；无运行时参数时三元组皆空。
- `host_args_layout` 由 Triton 代次决定：`IS_TRITON_36_PLUS` → `TRITON_ASCEND_3_6`（尾指针 1；pure SIMT 3），否则 `TRITON_ASCEND_3_2`（尾指针 0）；`load_kernel` 把归一化后的尾指针数作为 `_load_kernel` 最后实参转发。
- SIMT/FFTS 元数据：`parallel_mode="simt"`+`is_pure_simt`+`shared_mem_dynamic_size=4096` → `enable_simt/is_pure_simt/target_support_ffts` 全真；`global_scratch_size`/`profile_scratch_size` 非零即抛 "… is required but unsupported"，0 允许；`mix_mode/parallel_mode/shared_mem_dynamic_size/is_pure_simt|force_simt_only` 缺失即抛。
- `NPULaunchMetadata.validate`：`schema_version` 必须 1；`host_args_layout` 已知；`target_arch ∈ {Ascend910B, Ascend910D, Ascend910_93, Ascend910_95, Ascend950}`；`mix_mode` 合法、`parallel_mode` 非空；`shared_mem_dynamic_size/workspace_size/lock_num` 非负；`is_pure_simt=True` 要求 `enable_simt`；`num_ctas=1`、`cluster_dims=(1,1,1)`。
- 磁盘恢复：`reload_npubin_path` 把 `npubin_raw` 写入 triton cache；raw 为空抛 RuntimeError "saved by TritonBundler not found"。

## pickle 往返与拥有者生命周期

- pickle 往返后 `runtime_arg_indices=(0,2)` 重算、`npubin_raw` 保留、`npubin_path/loaded_kernel/function/_c_impl` 清空（lambda 故意不可 pickle，活性句柄必须失败）；旧版 state 缺 `runtime_arg_indices`/`_c_impl` 也能 `__setstate__` 恢复。
- `close()` 幂等（重复 close 只卸载一次，`loaded_kernel/function` 置 None）。
- launcher（生成函数）通过 `__globals__["runner"].__self__` **持有 kernel 拥有者与 loaded_kernel**：删 result 不触发卸载，删 launcher 后 `weakref` 归零、恰好一次 "unload"。
- `kernel.run` 只接受**运行期实参数量**：多传一个位置实参抛 RuntimeError "unexpected argument count"。

## autotune 胜者/败者时序（单元，真实生成 launcher + 假 C 绑定）

胜者不是第一个 config：`benchmark_all_configs` 受控计时返回 loser 2.0/winner 1.0 后——benchmark 完成事件先于 loser 卸载；`TritonBundler.put_winner` 恰被调用一次（winner.cache_hash）；败者 kernel `loaded_kernel` 置 None 且恰一次 unload，胜者保留；再次 `run(stream=456)` 直接 launch 胜者（**不重载**）；此后 `loser_result.kernel.close()` 不再产生第二次 unload。`NPUCachingAutotuner.run` 全程不得调用上游 `CachingAutotuner.run`（"ABI alignment must not migrate the run lifecycle"），`benchmark_run=True` 也保持 NPU 分派；launcher 列表被替换后下次 run 用新胜者。生成 launcher 的签名来自 `extra_launcher_args`（`["extra","stream"]`）、`_expected_positional_count` 计数、无 defaults/closure；普通（非静态）`NPUTritonCompileResult.make_launcher` 保持 runner 参数 ABI 且 `_is_static=False`，`_init_handles` 正常调用——两条 codegen 路径共存不互染。

## 进程内集成：静态路径的正向证据

`_observe_launch` 四重观察：静态路径**不得**调用 `CompiledKernel._init_handles`、**不得**构造普通 `driver.active.launcher_cls`；`AsyncCompile.triton` 编译的 `npu_triton_heuristics` 内核名必须出现（证明没有只选外部算子）；完整缓存命中（restore）时 `triton.compile` **不得**被调用。设备矩阵 910B/910_93/950：

- pointwise fp32/fp16/int32；纯 SIMT ABI（`compile_mode="simt_only"` @triton.jit，950）：`is_pure_simt/enable_simt` 真并复算一致。
- **signed 标量 ABI**：i8/i16/i32/i64 全负值四槽（-113/-30001/-(2^30)+7/-(2^40)+19）防交换/符号扩展/截断；普通 launcher 的 i8 解析器当前拒负值，故改用 `warmup`+独立期望值。
- **bool/float 标量 ABI**：`arg_kinds` 兼容 `("tensor","bool","f32")`（Triton 3.2 i1）或 `("tensor","u32","f32")`（3.6 u1）；单个已装载内核跨 `(True,3.25)/(False,7.5)/(True,-2.25)` 复用。
- **窄标量**：u1→u32 值面验证；fp16/bf16 标量 skipTest（"Triton Ascend does not yet support fp16/bf16 scalar ABI"）。
- 回退面：strict=False + adapter 抛错 → 走普通 launcher（static=False 断言 `_init_handles`/launcher_cls 被调用，adapter 仍被调用过）；两档 strict 下显式 `use_static_triton_launcher=False` 同样普通路径；**同进程 toggle**（关→reset→开）成立。
- 场景面：非连续广播（storage_offset>0 的转置）、规约尾（257）、动态形状三尺寸（1024/1537/1024）、空张量混合 cat、非默认流、NPUGraph 捕获重放。
- FXGraph 缓存：miss 后 `fxgraph_cache_miss>0` 且 `triton_bundler_save_static_autotuner>0`；内存缓存重置（**不用 purge=True**，保留磁盘）+ 可选重定位 TRITON_CACHE_DIR 后，命中 `fxgraph_cache_hit>0`、`triton_bundler_load_static_autotuner>0` 且 `triton.compile` 零调用——`keep_static_cubin_raw=False` 下仅凭 bundle 内 .npubin 恢复（不主张跨进程/raw-only 覆盖）。

## fast launcher 契约（Python 面，C++ 边界 mock）

隔离配置（fast_launcher_test_utils.py `:11-55`）：临时双 cache 目录、`compile_threads=1`、`cpp_wrapper=False`、静态开关恒 True+strict、`use_fast_triton_launcher=enabled`、`enable_fast_launch=False`（复用低层计划不依赖旧开关）、fx/autotune 远程缓存全关、`TRITON_FAST_PTR=false`；退出前先 `torch.npu.synchronize()` 再清缓存（"Finish queued work before cache cleanup can release kernel owners"）。

- **构建克隆全局**：`_build_fast_launcher` 用同一 `__code__`、**新 `__globals__`**（runner 换成 `_FastNpuLauncher(kernel.loaded_kernel)`），`_static_kernel_owner` 保留原 kernel，config/cache_hash/n_regs/n_spills/shared/store_cubin/_is_static/_npu_def_args/_expected_positional_count 全等；fast 调用不落原 runner；基线仍可用；删 baseline+tuner 后拥有者仍活，删 optimized 才释放。
- **不可用即静态回退**：`_FastNpuLauncher` 构造抛 ValueError → `_cached_launcher=baseline`，构造次数恰 `int(enabled)`；旧式 `def old_launcher(stream, runner=runner)` 签名**不被静默替换**（builder 返回 None 且不触碰构造器）。
- **成功后才建缓存**：第一次 run 走静态 runner（events 含 "static"）→ 构建 fast（恰一次）→ 后续全走 fast；**首次失败不缓存**（RuntimeError 抛出后 `_cached_launcher` None、builder 未调用）；**fast 异常不重放**（第二次调用抛出、optimized 恰调用一次、原 kernel.calls 恰 1——失败不自动降级回静态）。
- **胜者替换失效旧 fast**：`launchers=[new]` 后下次 run 用新 launcher，旧 optimized 不再被调，builder 收到新胜者。
- **特殊调用旁路**：`benchmark_run=True` 或缺省参调用（kwargs 形态）绕过缓存 fast 直接落基线，**不重建**（builder 仍只调用过一次），steady 调用回到 fast。
- **autotune 只为选中胜者构建**：受控 `autotune_to_one_config` 先选中再 build（events ["select","build"]，winner 恰 launch 一次后构建）。
- **降浮点包装保持 ABI**：`_wrap_launcher_with_downcast` 包裹 optimized fast launcher 后 `_expected_positional_count` 不变；input/output/双向三模式 int64→int32 转换与写回验证（input_output 模式原地 `add_`）。

## fast launcher 设备面

- `require_fast_type`：`torch_npu._C._FastNpuLauncher` 缺失即 AssertionError——"a static fallback is not a passing fast test"；`require_fast_runner` 校验缓存 launcher 的 runner 确为 fast 类型且保留 `_static_kernel_owner`。
- 多张量+None 指针（可选指针置 None 读 0）、零参数内核、signed 全宽（含 2^31-1/2^63-1 上界）、**unsigned 全宽越界拒绝**（-1 与 2^bits 对 TypeError/ValueError/RuntimeError/OverflowError 断言，且失败后输出不被执行——保持原值）、bool/float 标量三组值、**参数错误不执行**（少参/多参/object 实参/i32 上下越界/grid0 为 0 或 2^31 全部拒绝且 out 保持 23）。
- 编译正路径：`use_fast_triton_launcher=True` 时 observe_fast_builds 至少一个 fast 记录且调用数>0；False 时零 fast；动态形状（257/8193/513/257）跨桶命中 fast；非默认流+NPUGraph 捕获重放期间 fast 调用数继续增长并保持数值。

## 相邻卡边界

[静态 launch 契约卡](torch_npu_experimental_triton_static_launch_contract.md)（can_statically_launch/资格面实现）；[grid/launcher codegen 卡](torch_npu_experimental_triton_grid_and_launcher_codegen.md)（生成 launcher 实现）；[原生 launcher C++ 卡](torch_npu_static_launcher_native_runtime_cpp.md)（_StaticNpuLauncher/_FastNpuLauncher C++ 面，测试对其只 mock 边界）；[autotune 缓存身份卡](torch_npu_experimental_triton_autotune_cache_identity_and_tile_consistency.md)与[计时与输入隔离卡](torch_npu_experimental_triton_autotune_timing_and_input_isolation.md)（put_winner/benchmark 语义实现面）；[cpp wrapper 延迟分组卡](torch_npu_main_inductor_cpp_wrapper_deferred_grouped_launch.md)（降浮点写回的 wrapper 面）。`test_codecache.py` 的 NPU autotune_expect 结构断言（:95-96）见[autotune/codecache 测试契约卡](torch_npu_main_inductor_autotune_codecache_tests.md)。

## 失效边界与静态口径

- 全部为测试文件静态阅读，**未运行任何测试**；设备用例依赖 `SupportedDevices` 矩阵与 `torch.npu.is_available()`。
- `_LoadedKernel/_LauncherBinding/FakeKernel` 只假 CANN/C++ 边界，Python 侧拥有权与生成 launcher 为真实代码——该区分是测试文件自己的声明，本卡照录，不据此证明 C++ 行为。
- 字面指纹（`mutated_arg_names`、`triton_poi_fused_native_layer_norm`、`_mask = True` 等）是 ac0e1564 期望值，随版本可变。
- 与 [静态 launch 契约卡](torch_npu_experimental_triton_static_launch_contract.md) 的分工：实现卡拥有资格/工件/布局的实现语义；本卡只钉测试期望。同族 `test_autotune_reset_args.py`（473）/`test_linearize_shape.py`（365）/`test_launcher_codegen.py`（227）/`test_combo_kernel.py`（227）等 te_* 系列不在本卡覆盖范围，本卡不外推。
- fast launcher 队列变体声明（TASK_QUEUE_ENABLE=0/1 新进程）是文件头注记，本卡未运行任何队列变体。

## Evidence

- [triton_experimental/test_static_launcher_integration.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_static_launcher_integration.py)（primary；`:1-1553` 全文）
- [triton_experimental/test_triton_experimental_fast_launcher.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_triton_experimental_fast_launcher.py)（primary；`:1-520` 全文）
- [triton_experimental/fast_launcher_test_utils.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/fast_launcher_test_utils.py)（primary；`:1-110` 全文）
- [static_launcher/compile_result.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/static_launcher/compile_result.py)（implementation；实现体不在本卡范围，被测符号 `NPUStaticTritonCompileResult.can_statically_launch/make_launcher/prepare_for_caching/reload_npubin_path` 归[静态 launch 契约卡](torch_npu_experimental_triton_static_launch_contract.md)）
- [static_launcher/adapter.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/static_launcher/adapter.py)（implementation；同上，`_arg_kind/NPUStaticArtifactAdapter.from_compiled_kernel` 归契约卡）
- [triton_experimental/npu_triton_heuristics.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/npu_triton_heuristics.py)（implementation；被测符号 `NPUCachingAutotuner/_build_fast_launcher/_wrap_launcher_with_downcast/NPUTritonCompileResult` 归他卡，本卡仅测试侧）
