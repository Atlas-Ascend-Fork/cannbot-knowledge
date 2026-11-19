---
type: Guide
title: 主线 Inductor triton_experimental 测试族：严格模式回退登记、设备门与回归契约
description: 固定提交下 te_* 回退族、GENERATE_LIST 面、native_dropout/RNG 设备门、int64 降位与 QR 布局等回归测试的断言契约，与既有实验
  Triton 实现面卡配对。
tags:
- task.testing
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_contiguous_lowering.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_unique_fallback.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_matmul_backward.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_grid_sampler_3d_fallback.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_npu_gather_backward_fallback.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_npu_dropout_fallback.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_nearest_backward_fallback.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_qr_fallback_layout.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_qr_fallback_layout_out.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_int64_range_downcast.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_native_dropout_decomp_device_gate.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_rng_decomp_device_gate.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_hypot_generate_list.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_correctness_fixes.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_downcast_memo_windows.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_source_pin.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_import_lazy_device_queries.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_linearize_shape.py
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_reduction_shape.py
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_spatial_native_fallback.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_kernel_patterns.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_dynamic_shapes.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/test_embedding_fallback.py
  role: constraint
created_at: '2026-11-13T00:12:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 主线 Inductor triton_experimental 测试族：严格模式回退登记、设备门与回归契约

## 固定版本与范围

主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 `test/_inductor/triton_experimental/` 测试树静态阅读：17 个文件全文（上列 primary）、2 个文件局部窗（linearize_shape :1-50、reduction_shape :1-30）。全部文件以 `os.environ.setdefault("TORCHINDUCTOR_NPU_BACKEND", "triton_experimental")` 选定 TE 后端。未运行任何测试、未编译 kernel、未 mock 之外的设备调用。实现面批量回退/生成列表机制由 [激活与 lowering 路由卡](torch_npu_experimental_triton_activation_and_lowering_routes.md) 持有（GENERATE_LIST/KEEP_UPSTREAM_LOWERING/EXPLICIT_FALLBACK_LIST 三表与展开语义），本卡记录测试侧断言的契约本身。

## 严格模式显式回退族（EXPLICIT_FALLBACK_LIST）

十二个 te_* 回退测试共享同一断言骨架：(a) 目标算子各 overload 在 `lowering_fallback_list.EXPLICIT_FALLBACK_LIST`（登记表是逐条具体 OpOverload，非 packet）；(b) `lowering.EXPLICIT_FALLBACK_LIST is lowering_fallback_list.EXPLICIT_FALLBACK_LIST`——消费方与定义方同一对象，防止 stale import 静默不注册；(c) 严格模式编译（`config.patch("implicit_fallbacks", False)` + `force_disable_caches`，并以 `torch_npu.utils._dynamo._InductorNpuRegistry._loaded_backend == "triton_experimental"` 断言后端真实生效）后经 mock `GraphLowering.save_output_code` 检查生成代码含 `torch.ops.<op>(`，数值/梯度对 eager 收敛。各文件钉住的登记事实：

| 测试文件 | 登记内容 | 故障背景（docstring 原义） |
|---|---|---|
| test_te_unique_fallback（:4-13, :35-54） | `_unique`/`_unique2` 的 default/out 四 overload | index_fill 编译反向达 `aten._unique.default`，无上游 lowering/decomp，批量扫描看不见（#4937） |
| test_te_matmul_backward（:1-8, :73-105） | `aten.matmul_backward` 进 TE decomposition 表（:83 断言 `in decompositions`） | TE 登记器漏登记该 decomp，严格模式反向 MissingOperatorWithoutDecomp（#4930） |
| test_te_nearest_backward_fallback（:34-93） | `upsample_nearest1d/3d_backward.default` | TE disable_implicit_decomposition 弹出前向 py_kernel 后 1d/3d 反向裸露（#4934） |
| test_te_grid_sampler_3d_fallback（:40-151） | grid_sampler_3d(+backward) 的 default/out 四 overload；:68-75 断言全部已在 lowerings 且记入 FALLBACK_LIST（含 opinfo 不自达的 .out 对） | 上游无 lowering/decomp，CUDA 仅因 implicit_fallbacks 默认开启而能编译 |
| test_te_npu_gather_backward_fallback（:44-157） | `npu.npu_gather_backward.default` | gather/take_along_dim/quantile(nan)/multi_margin_loss 反向携带的私有算子无上游去处（两例 float64/float32 未断言，注释称另有根因） |
| test_te_npu_dropout_fallback（:45-129） | `npu._npu_dropout.default` + `npu.npu_dropout_backward.default`，且 :52-57 断言 `_npu_dropout` **不**在 GENERATE_LIST | 该算子曾列 GENERATE_LIST——该表只豁免批量回退、不提供 lowering，等于无主；每个算子只能有一个家（one home per op） |
| test_te_contiguous_lowering（:4-59, :62-102） | `aten.contiguous` 在 GENERATE_LIST 且 `npu_contiguous`（委托 `npu_clone`）已注册为 lowering；:49-59 以本地重实现的展开不变量断言其被豁免、不在 FALLBACK_LIST | diag_embed 六 dtype 反向链尾 `mask_tensor(...).contiguous()` 裸露（#4933） |
| test_te_qr_fallback_layout（:1-85） | 非登记表断言：eager linalg_qr（aclnn）返回行主序 Q/R 而 ATen meta 按 LAPACK 列主序声明，编译消费方曾按 meta 建布局读到转置步长（svd_lowrank/pca_lowrank 谱塌缩，#5072）；四用例编译 mm/lowrank 链/批量投影/complete+r 模式对 eager 逐元素收敛 | |
| test_te_qr_fallback_layout_out（:1-107） | `.out` 半边：`_replace_qr_fallback_example_output`（meta 注册面，见 [Meta 注册链卡](torch_npu_meta_registration_patch_chain.md)）对位置 tuple（PyTorch2.13）与 dataclass（2.14+）两种 ProcessKernelResult 兼容（:47-63 无设备）；`out=` 编译须写回所给缓冲（data_ptr/stride 同一，:67-88）；转置视图 `out=` 被 Dynamo 在 tracing 期拒绝（gb0241，:92-106）——该形态当前不构成编译路径守卫 | |
| test_te_fake_tensor_cache_on_off_crosscheck（:32-89） | 以自定义 backend 收集 FX 节点 example_value/val 元数据，断言 FakeTensor cache 关闭与开启+crosscheck 两种配置产出完全相同的逐节点 TensorMeta | |

## 设备门与 RNG 契约

- **native_dropout 设备门**（test_native_dropout_decomp_device_gate，#4939）：`_override_native_dropout_decomp()` 重写 aten.native_dropout(_backward) 三处表项（inductor 表前/反向 + extra_random_decomps 前向）；守卫识别以 `_npu_decomp_override` 标记为主、`__module__/__qualname__` 兜底（:62-86）。门契约（:96-121）：override 装好后 CPU/meta 输入不得派发任何 `npu._npu_dropout`/`npu.npu_dropout_backward` 私有目标；微妙腿（:123-155）：`fallback_random=True` 时 `select_decomp_table()` 是 inductor 基表、其 vanilla 前向 native_dropout 条目本就不存在，被门包装的 wrapper 须对非 NPU 输入返回 NotImplemented 留给 FallbackKernel——与不 import torch_npu 时的行为一致。NPU 输入保持私有 kernel 路线（:195-210，mask 形状与 grad 不同=打包 uint8）。实现面 `_is_npu`/标记语义见 [dropout/RNG 分解卡](torch_npu_experimental_triton_gelu_rmsnorm_dropout_rng_decompositions.md)。
- **RNG 门**（test_rng_decomp_device_gate，#5249）：`_npu_rng_gate` 包装 bernoulli/uniform(_)/rrelu_with_noise(_/functional) 各 packet 的**全部 overload**（:33-40 注释：遍历 overloads() 保持守卫诚实）；测试断言合并表中已存在的 RNG decomp 都带 `_npu_rng_gate` 标记（:57-72）、native_dropout override 不被误包装（:74-83）、NPU 输入 NotImplemented/CPU 输入真张量（:86-96）；dropout 家族编译产物 bitwise 相等（rtol=0/atol=0）且不含 `inductor_random`（philox 不泄漏回编译图，:99-134）。

## 数值正确性回归

- **int64 范围感知降位**（test_te_int64_range_downcast，#4947）：TE 曾无条件把 int64 降 int32，`torch.masked.{amax,amin,argmax,argmin}` 的 int64 identity（INT64_MIN/MAX）被渲染成 `tl.full([1], …, tl.int32)` 且换行回绕——全掩码行 amax 得 0（应 INT64_MIN）、amin 得 -1（应 INT64_MAX）、负值行 0 填充盖过真实最大值、argmax 差一；宽负载（|x|≥2^31）经 `*i32` 指针截断。修复后：超范围常量保持原生 `tl.int64`（源码断言 `{INT64_MIN}, tl.int64` 在、`, tl.int32` 不在，:80-117）、宽负载精确（:134-146）、int32 in-range 与 float 路径无回归（:153-172）。实现面见 [边界降精度卡](torch_npu_experimental_triton_boundary_downcast_and_writeback.md) 与 [int64 卡](torch_npu_experimental_triton_int64_index_data_and_global_type_patches.md) 的宽常量豁免标记。
- **两项通用修复**（test_correctness_fixes）：纯归约图曾引用未定义 xmask 的 NameError（mul/where 叶），rsplit 跨核 OUTER 归约曾把 numel 映到错误父前缀致 r0_0 子轴错尺寸——两族编译对 eager 精确（:34-76）；第三项 stride 保持边界降位归 #46074 专文件（不在本卡）。
- **降位 memo 的图窗口**（test_downcast_memo_windows）：i64→i32 边界降位 memo 在 ACLGraph 捕获/图树 warmup 期间**不得**登记（池块被 memo 钉住会破坏 `check_memory_pool()`）；测试以 mock 三态（普通去重命中同一对象、capture/warmup 各返回新对象且 memo 表为空，:36-114）。实现面见 [边界降精度卡](torch_npu_experimental_triton_boundary_downcast_and_writeback.md) 的 memo 节。
- **hypot 生成名单**（test_hypot_generate_list，#5002）：`aten.hypot` 须在 GENERATE_LIST——批量回退会把每个注册 lowering 改回 fallback，修复前 hypot 静默退化为 aten fallback、upcast 计数为 0；测试断言名单成员（:37-38）、编译产物含 `libdevice.hypot(` 不含 `torch.ops.aten.hypot`（:78-81，剥离 FX 注释行后检查），并附 profiler chrome trace 佐证 `fused_hypot` 上设备、无 `aten::hypot`（:92-128）。

## 缓存键与安装契约

- **TeSourcePin 指纹**（test_te_source_pin）：`_te_source_digest` 确定性、对 `.py` 内容编辑与新增 `.py` 敏感、对非 `.py` 与 `__pycache__` 盲（:63-91）；`get_hash_for_files` 进程级 lru_cache——编辑只在新进程生效，缓存指纹忠实于进程实际导入的代码（:54-61 注释）；uuid 为 bytes 且跨实例稳定（:93-99）。安装组合（:102-158）：TeSourcePin 无条件安装（elide 开关不控制指纹）、ElideIntFloatIntPass 仅开关开时追加、重装幂等、已有 CustomGraphPass 组合、第三方 raw callable 原样中止不伪造 uuid。实现面见 [整数往返省略卡](torch_npu_experimental_triton_integer_roundtrip_elision_scope.md) 的 TeSourcePinPass 节。
- **forked worker 导入惰性**（test_import_lazy_device_queries :1-80）：三契约——`import torch_npu._inductor`（TE 链）不触发 `_lazy_init`（fresh 子进程内 mock 断言，:50-68）；`_npu_get_soc_version` 在未初始化/已初始化/forked child 三态返回同值（:70-80 起）；惰性 config/heuristics 与 eager 同数（:109 起，不在本窗范围）。动机：生成的 kernel 模块在 Inductor forked compile worker 内 import 该链，设备初始化会 "Cannot re-initialize NPU in forked subprocess" 杀掉 ≥2-kernel 编译。
- **延迟形状断言**（局部窗）：`NPUTritonKernel.codegen_shape_assert` 先渲染占位（`tmp0.shape[0] == XBLOCK`），splice 后按 `_npu_assert_shapes` 回填实际块名——早渲染不冻结期望形状（test_linearize_shape :29-49）；归约路径同契约（test_reduction_shape :18-27）。该 `codegen_shape_assert`/`_npu_assert_shapes` 锚为测试侧首次记录，实现上下文归 [线性化 header 卡](torch_npu_experimental_triton_linearize_header_tile_odometer_mask.md)。

## 测试族定案与边界

- 本卡覆盖 triton_experimental 测试树的 17 个文件全文（flex_attention/test_flex_attention.py 归[flex 测试卡](torch_npu_main_inductor_flex_attention_tests.md)）；其余测试文件（autotune reset/launcher codegen/combo/provable clamp/range tree/reduction alias/permuted store/separable index 等）与对应实现面卡（[自动调优计时卡](torch_npu_experimental_triton_autotune_timing_and_input_isolation.md)、[缓存身份卡](torch_npu_experimental_triton_autotune_cache_identity_and_tile_consistency.md)、[启动器代码生成卡](torch_npu_experimental_triton_grid_and_launcher_codegen.md)、[组合准入卡](torch_npu_experimental_triton_combo_admission_and_tile_dispatch.md)、[掩码索引夹逼卡](torch_npu_experimental_triton_masked_index_clamp_proof.md)、[归约索引别名卡](torch_npu_experimental_triton_reduction_index_alias_contract.md)、[融合置换存储卡](torch_npu_experimental_triton_fusion_permuted_store_and_read_budget.md)、[可分离高级索引卡](torch_npu_experimental_triton_separable_advanced_index.md)）一对一配对，测试文件为纯数值/镜像用例时不重复展开。
- 测试文件与故障号（#4930/#4933/#4934/#4937/#4939/#4947/#5002/#5072/#5249）在 canonical 全树的测试侧语义 rg 零命中（唯一例外是路由卡持有 EXPLICIT_FALLBACK_LIST 实现面本身）；docstring 所述修复因果是固定提交的静态记录，未经运行复现。
- 所有 mock/子进程手段（GraphLowering.save_output_code、TorchDispatchMode 记录、fresh interpreter、profiler trace）均为测试侧阅读结论；`_loaded_backend` 断言说明 TE 编译链的后端选择是可观测单点。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_contiguous_lowering.py)（primary）：:1-106 全文（GENERATE_LIST 豁免不变量 :49-59、六 dtype diag_embed :62-102）。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_unique_fallback.py)（primary）：:1-96 全文（同对象接线 :48-54、具体 overload :44-46、index_fill 反向 :56-92）。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_matmul_backward.py)（primary）：:1-109 全文（decomposition 表断言 :83、`_loaded_backend` 守卫 :49-52、矩阵幂 :100-105）。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_grid_sampler_3d_fallback.py)（primary）：:1-155 全文（四 overload :51-75、生成代码断言 :140-142、三 dtype 前反向 :90-151）。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_npu_gather_backward_fallback.py)（primary）：:1-161 全文（私有目标检查 :108-115、四函数族 :117-157）。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_npu_dropout_fallback.py)（primary）：:1-133 全文（one-home-per-op :52-57、seed 对齐 :74-76/:100-101）。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_nearest_backward_fallback.py)（primary）：:1-97 全文（1d/3d 登记 :72-77、F.interpolate 反向 :79-93）。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_qr_fallback_layout.py)（primary）：:1-91 全文（#5072 谱塌缩背景 :1-9、四消费链用例）。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_qr_fallback_layout_out.py)（primary）：:1-112 全文（ProcessKernelResult 兼容 :47-63、out= 写回 :67-88、Dynamo 拒绝 :92-106）。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_int64_range_downcast.py)（primary）：:1-185 全文（`_run_te` 源码断言助手 :45-69、P4D-1/2/6 用例 :80-146、对照用例 :153-172）。
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_native_dropout_decomp_device_gate.py)（primary）：:1-214 全文（标记识别 :62-86、八探测 :96-121、fallback_random NotImplemented :123-155、NPU 路线 :195-210）。
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_rng_decomp_device_gate.py)（primary）：:1-138 全文（overload 遍历 :33-40/:57-72、bitwise 家族 :99-134）。
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_hypot_generate_list.py)（primary）：:1-132 全文（名单 :37-38、代码断言 :71-81、trace 佐证 :92-128）。
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_correctness_fixes.py)（primary）：:1-80 全文（xmask :34-58、rsplit :61-76）。
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_downcast_memo_windows.py)（primary）：:1-118 全文（三态 mock :36-114）。
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_te_source_pin.py)（primary）：:1-162 全文（指纹三性 :63-91、安装组合 :102-158）。
- [固定来源 17](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_import_lazy_device_queries.py)（primary）：:1-80（三契约 docstring :10-21、fresh 子进程框架 :33-48、`_lazy_init` mock :50-68、soc 三态 :70-80）；:83-195 不在本卡范围。
- [固定来源 18](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_linearize_shape.py)（constraint）：:1-50（codegen_shape_assert 延迟回填契约窗）。
- [固定来源 19](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/triton_experimental/test_reduction_shape.py)（constraint）：:1-30（归约形状断言同契约窗）。

## 补充文件：spatial_native_fallback、kernel_patterns、dynamic_shapes 与 embedding

三个此前归属未核的测试文件与 root 级 test_embedding_fallback.py 的归属核对如下：

- **test_spatial_native_fallback.py（99 行）→ covered**：`reflection_pad2d(+backward)`、`upsample_bilinear2d(+backward)` 四 overload 属实为 [激活与 lowering 路由卡](torch_npu_experimental_triton_activation_and_lowering_routes.md) EXPLICIT_FALLBACK_LIST 已登记项；测试骨架与前文严格模式族同型（implicit_fallbacks=False + force_disable_caches + save_output_code 断言 `torch.ops.aten.<op>.default(` 出现、前反向对 eager 收敛），size 与 scale_factor 两种 upsample 入口各一例。无新事实。
- **test_kernel_patterns.py（109 行）→ covered（数值镜像）+ 新锚一对**：五用例（pointwise 广播/view/permute、int64 pointwise、扩展归约、gather/scatter、storage-offset 切片输入）为纯数值镜像，实现面归既有 TE 卡族。新锚是 wrapper 双标记：`EXPERIMENTAL_MARKER`（`from torch_npu._inductor.triton_experimental import npu_triton_heuristics`）与 **DEFAULT_MARKER（`import torch_npu._inductor.runtime.triton_heuristics as triton_heuristics`）**——后者是默认（非实验）后端 wrapper 的代码指纹，此前全树零记录；测试拒绝"默认 NPU Triton wrapper 被生成"，即两套 heuristics 导入行可作为产物归属判别。
- **test_dynamic_shapes.py（116 行）→ closed_with_new_fact**：pointwise/归约/gather+scatter 在 `dynamic=True + options={"npu_backend": "triton_experimental"}` 下一次编译跨 3 组行数复用（数值镜像）。新契约：**`test_dynamic_layer_norm_keeps_static_reduction_numel_runtime`**——门 `IS_TRITON_36_PLUS && !device_props.is_a5()`（skip 原文 "pre-A5 Triton 3.6 regression"）；仅 batch 轴动态而归约维静态（layer_norm 最后维 2560）时，生成代码**不得**把 `'r0_numel': 2560` 冻进 `'constants'`（assertNotRegex），尾批 1279 行复用同一编译产物。即 TE 后端对"静态归约长度 + 动态批"的层归一须保持 r 轴 numel 为运行时参数；

  这条与[归约/Welford 测试契约卡](torch_npu_main_inductor_reduction_welford_tests.md)的主线 Welford 动态层归一契约（不回退 native kernel）分属两个后端面。
- **test_embedding_fallback.py（31 行，root 级）→ excluded_pure_smoke**：`aten.embedding_dense_backward`（[1,512] 索引 + [1,512,128] 梯度，num_weights=512，atol 1e-1）单用例编译对 eager 数值比较，无 NPU 特有分支断言、无结构断言；实现面 embedding 反向归 eager/OpPlugin 域，不构成本树测试侧缺口，不另建卡。
