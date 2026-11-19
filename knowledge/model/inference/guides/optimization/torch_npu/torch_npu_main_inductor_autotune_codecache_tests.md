---
type: Guide
title: torch_npu 主线 inductor autotune/codecache 测试契约：缓存工件计数、TuningProcess 设备表、配置哈希补丁与 profiler 会话互斥
description: 记录主线 test/_inductor 中 autotune_codecache 族 7 个文件（共 691 行）的测试侧契约：caching_precompile 下 NPU 前反向恰好产出 2 个 autotune 工件而 CPU 为 0、五类缓存工件计数 save/load 对称、无工件重编译与 fail_on_recompile 下的 dynamo 计数、TuningProcessPool 设备表未被替换且 ASCEND_VISIBLE_DEVICES 保序收窄、patch_is_gpu 幂等、triton_config_to_hashable 递归冻结等价且三模块共享绑定、profiler 进程级单例下 batch/bandwidth 基准回落事件计时器、用户 triton.autotune 与 TMA 缺席断言。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_codecache.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_async_autotuner.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_autotune_process.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_autotune_profiler_session.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_user_autotune_npu.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_triton_config_hash.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_triton.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/version_mark.py
  role: constraint
created_at: '2026-11-12T15:36:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 主线 inductor autotune/codecache 测试契约

固定 PyTorch 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`，静态全文阅读 autotune_codecache 族 7 个文件（共 691 行）；实现面语义由既有卡持有（见文末边界）。全部测试未运行，断言均为静态转述。多数用例带 `@runIfVersion(max="2.13")` 门：装饰时把声明区间与 CI 目标区间（`set_ci_version_range` 或 `CI_VERSION_MIN/MAX`）求交，无交集即 skip（version_mark.py :95-118，含 :20-23 示例）。新卡 draft、空平台，不把测试期望当作设备已验证。

## 缓存工件计数契约（test_codecache）

caching_precompile 热加载用例（:54-138）以 `fx_graph_cache`+`autotune_local_cache`+`caching_precompile` 组合参数化 dynamic/device(npu,cpu)/dtype(float32,bfloat16)，图固定 `x.sin() @ y` 前向加反向。**NPU 专属期望**：`autotune_expect = 2 if device == "npu" else 0`，注释原文 “NPU compiles both forward sin and backward cos/mul as autotuned Triton pointwise kernels”（:95-96）——CPU 不产出 autotune 工件，NPU 恰好 2 个（前向 sin、反向 cos/mul）。工件计数 save/load 两侧对称：inductor 2、autotune 2(NPU)/0(CPU)、aot_autograd 1、pgo 0、precompile 1（:97-101、:124-128）。

无工件路径（:107-116）：删除 `<cache_dir>/triton` 后重编译，aot/dynamo 的 miss 计数各翻倍、hit 恒 0；加载工件并设 `fail_on_recompile` stance 后（:122-138）dynamo_cache_hit=1，其余计数不变。setUp 每用例清 counters/DynamoCache/PrecompileContext/AOTAutogradCache/CacheArtifactManager 并 `torch._dynamo.reset()`（:37-44）。`test_codecache` 本体被 `@skip("torch.distributed error")`（:162-164）——其 `CacheBase.get_system()` 断言 device.name 等于 NPU 设备属性、version.cann 等于 `torch.version.cann`（transfer_to_npu 导入前后各一次）仅为静态记录，不构成运行事实。`test_fx_graph_cache_constant_device`（:180-191）锚 int64 常量经 `c.to(x.device)`+index_select 两次编译结果一致，即常量缓存加载后仍在 NPU。

## TuningProcess 设备表适配器（test_autotune_process）

上游 `TuningProcessPool.get_device_list` 未被 NPU 适配替换（模块身份断言，:35-40）；单设备模式返回 [None]（:43-45）。多设备模式经 `patch_tuning_process()`+`get_gpu_type="npu"` 后：`ASCEND_VISIBLE_DEVICES="3,1"` → **[3,1] 保序**、空环境 → [0,1,2,3]（device_count=4，:48-80）。`TuningProcess` 子进程 env 把父 "2,3" 收窄为单卡 "1"，父进程环境不受影响（:83-100）。`patch_is_gpu` 幂等：重复调用清 `get_gpu_type` lru 缓存，GPU_TYPES 列表内 "npu" 只出现一次（:114-130）。

## 配置哈希补丁的等价契约（test_triton_config_hash）

补丁后的 `triton_config_to_hashable` 对既有 key 与原实现等值等哈希（:20-25）；嵌套 list/tuple 递归冻结为等价元组键且不改动原 config 可变性——mutate 原 kwargs 后 key 随之改变（:27-37）；五组不同配置键互异（:39-48）。补丁安装面：重复调用幂等，`runtime_utils/coordinate_descent_tuner/triton_heuristics` 三模块共享同一绑定（:50-54）；`CoordescTuner.cache_benchmark_result(cfg)` → `lookup_in_cache(等价 cfg)` 命中、`unique_configs` 去重为 1（:56-61）。

## profiler 会话互斥与回落（test_autotune_profiler_session）

文件 docstring 固定的行为前提：torch_npu profiler 后端是进程级单例，嵌套会话退出时终结共享 trace，外层报 "Incorrect schedule: Stop profiler while current state is RECORD"。`npu_profiler_session_active()` 跟随 `ProfPathCreator().is_prof_inited`（:43-52）；探针对不可达后端读作无会话而非抛错——探针在 launch 路径上必须不破坏内核下发（:55-65）。`aggresive_autotune` 开启时 batch benchmark 探测到活动会话 → 返回 None 回落逐配置计时、`mspti_batch_benchmark` 不被调用（:67-96）；bandwidth benchmark 探测到会话 → 回落事件计时器 `benchmarker.benchmark_gpu`（:98-129）；`profile_bandwidth=False` 时探针不被调用——autotune 逐 config 计时，无守卫对象时不空跑（:131-152）。

## 端到端与杂项目

`test_async_autotuner`（无版本门）：5 连 addmm+permute/relu/add 的 NPU float32 图经 inductor 编译与 eager 1e-3 一致（:8-46）。`test_user_autotune_npu`：`triton.autotune`（BLOCK_SIZE 64/32、key=n_elements）装饰的用户 kernel 经 inductor 后端在 NPU 可编译执行（:12-46）。`test_triton`：断言 NPU 上 `has_triton_tma/has_triton_tma_device` 为 False（transfer_to_npu 前后），但整测被 `@skip("torch.distributed error")`（:19-32）——TMA 缺席为测试意图记录，运行面未验证。

## 边界

实现面归既有卡：`patch_triton_config_to_hashable`/`patch_tuning_process` 的安装链与替换面归[缓存 autotune 补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)；`patch_is_gpu` 归[发布平铺 autotune 接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)；`npu_profiler_session_active`/`mspti_batch_benchmark` 的实现语义归[主线基准与候选计划卡](torch_npu_main_inductor_runtime_benchmark_and_candidate_plan.md)；[静态/快速 launcher 测试契约卡](torch_npu_experimental_triton_static_launcher_tests.md)在其边界节把 test_codecache :95-96 的 NPU autotune 结构断言归入本族。`run_and_get_code` 类结构断言不在本族，见同目录测试族卡。

## Evidence

- [test_codecache.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_codecache.py)（primary；:1-195 全文）
- [test_async_autotuner.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_async_autotuner.py)（primary；:1-50 全文）
- [test_autotune_process.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_autotune_process.py)（primary；:1-134 全文）
- [test_autotune_profiler_session.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_autotune_profiler_session.py)（primary；:1-159 全文）
- [test_user_autotune_npu.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_user_autotune_npu.py)（primary；:1-50 全文）
- [test_triton_config_hash.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_triton_config_hash.py)（primary；:1-65 全文）
- [test_triton.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_triton.py)（primary；:1-38 全文）
- [version_mark.py @ac0e1564](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/version_mark.py)（constraint；:95-118 runIfVersion 求交语义，:20-23 示例；全文归 welford 测试族卡）
