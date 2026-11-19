---
type: Guide
title: Catlass GEMM codegen 本体：模板 kernel 签名与 workspace 双 pass、tile 自调生成器与 EVG Python 前端
description: 记录主线 _inductor/codegen/catlass 的四个未映射文件：CATLASSTemplateKernel 的签名/布局参数/workspace 两次调用链、TileAutotune 按 L1/L0 预算生成 tile 候选的启发式、epilogue 转 EVG Python 表达的代码生成与外部 catlass_cppgen 的示例张量桥。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/catlass_kernel.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/catlass_library/gemm_autotune.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/catlass_python_evg.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/catlass_library/evg_extension.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/catlass_utils.py
  role: implementation
created_at: '2026-11-12T14:26:35Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Catlass GEMM codegen 本体：模板 kernel 签名与 workspace 双 pass、tile 自调生成器与 EVG Python 前端

## 固定版本与范围

主线 pin（ac0e1564）的 `_inductor/codegen/catlass/` 全目录；发布 pin（f3ecfe4a）**没有该目录**（负向 rg 证实，发布版 codecache 侧差异已由 [Catlass 二进制缓存卡](torch_npu_catlass_binary_cache_and_loading.md)声明）。邻卡边界：候选构造与融合门槛（`catlass_utils._gen_ops_cached`、EVG 决策、`may_adjust_l1_tile_for_bias` 的调度侧调用）见 [候选与 Epilogue 限制卡](torch_npu_catlass_candidate_and_epilogue_constraints.md)；`.so` 编译/缓存/加载链见缓存卡；调优开关的文档契约见 [矩阵乘调优卡](torch_npu_inductor_catlass_autotune.md)；cpp_wrapper 侧 CATLASS 前缀段消费见[主线 cpp wrapper 发射卡](torch_npu_main_inductor_cpp_wrapper_codegen_and_launch.md)。本卡覆盖四个本体文件：catlass_kernel.py 640 行全文、gemm_autotune.py 360 行全文、catlass_python_evg.py 307 行全文、evg_extension.py 32 行全文。`catlass_cppgen` 是外部包（本仓快照内无源码，requirements/.gitmodules 无登记，仅记录 import 面）。纯静态阅读：未编译模板、未运行 autotune、未生成 EVG 代码；draft、platforms 为空。

## 模板 kernel 与签名（catlass_kernel.py）

类型映射：`_DTYPE_TO_CPP` 复制上游 `DTYPE_TO_CPP` 后把 bfloat16→`bfloat16_t`、float16→`half`（:31-38，注释原义：catlass kernel 用 Ascend 工具链编译而非 ATen，`at::BFloat16` 等命名不可用），`CATLASSKernelArgs.cpp_argdefs` 用该表生成参数声明（:86-94）。`CATLASSTemplateBuffer`（:60-84）在 TemplateBuffer 上加 `workspace_size`/`template`/`is_mix`/`epilogue_fusion_type`，`emulate_store_fn` 对每个输出发空 store 供内存规划。`CATLASSTemplateKernel.def_kernel`（:224-275）以 `input_reorder` 支持模板形参序与实际输入序错位（docstring 例：模板 [X,W,Bias]、实参 [Bias,X,W] → reorder [2,0,1]），生成的签名为 `int {kernel_name}({arg_defs}, const int M, const int N, const int K, size_t* workspace_size, uint8_t* workspace, aclrtStream stream)`（`_EXTRA_CPP_ARGS` :103，M/N/K 由 `init_layout_args` 从 X/W 的倒数两维推导 :188-198）。

## call_kernel 的 workspace 两条路（:277-442）

cpp_wrapper 分支（:293-301）：断言 wrapper 是 `CppWrapperCpu`，注册进 `initialized_kernels`（导出 C 符号）、把签名里的占位 `KERNEL_NAME` 换成真实名，workspace_size 位置写 `nullptr`——注释说明该调用不再用于查询尺寸，尺寸此前已取得。Python 分支：tensor 参数包成 `c_void_p(data_ptr())`、unspec 参数 `.item()` 化。动态形状且有 workspace 时走**两次调用**（:324-391）：首次传 `byref(c_size_t)` + `None` workspace + `None` stream 只查询字节数（`from ctypes import c_size_t, byref` 的 import 由 `_catlass_dynamic_shape_imports_added` 标记只 splice 一次），再 `empty_strided((size,), (1,), dtype=torch.uint8)` 分配，第二次传 `c_void_p(workspace.data_ptr())` 经 `generate_kernel_call` 补 stream，最后显式 `del workspace` 绕过内存规划（注释：动态尺寸不适合缓冲复用）。静态路径（:392-442）：`nullptr`/`None` 占 workspace_size，有 workspace 时经 `WorkspaceArg`（`WorkspaceZeroMode.UNINITIALIZED`）分配并在调用后释放，`is_multi_stream()` 时带 `origin_node` 变体。`load`/`store` 是内存规划用的 mock（:539-549）。`CATLASSTemplateCaller`（:552-640）：`precompile`/`benchmark` 委派给 `CATLASSBenchmarkRequest`，`call_name` 为 `catlass_template_kernels.{name}`，`hash_key` 拼 category 与 bmreq，`info_dict` 固定 `{"backend": "NPU", "op_type": ...}`，`output_node` 先 `bmreq.update_workspace_size()` 再建 buffer。

## tile 候选生成器（gemm_autotune.py）

`TileAutotune`（:38-267）：支持架构仅 `AtlasA2`/`Ascend950`（未知架构 WARN「use the default tile size」后按 AtlasA2 处理，:55-61）；L1/L0 尺寸表（:63-72）：A2 与 950 的 L1 均 512KB、L0A/L0B 均 64KB，L0C 128KB vs 256KB；`aicCoreNum = config.num_cube_core`。`gen_tile_configs`（:200-267）按 dispatch policy 的 stages 折算可用 L1/L0 预算，`add_block_sizes_to_configs`（:217-244）以 16 对齐下降迭代 `BLOCK_min_mn`（`aligned_decrease_iterator` 步长 16、目标比率 0.5、下限 16），`BLOCK_K` 取 `floor_power_of_2(min(K, L1 预算))` 下限 16，`SUB_BLOCK_K` 受 L0 预算约束小于 16 则丢弃该候选；M<N 时小边给 BLOCK_M，否则给 BLOCK_N。`MmadMultiBatch` 特例要求 `l1_k == l0_k`（:240-242）且过滤候选必须 `l1_m>=M && l1_n>=N && l1_k>=K`（:181-198，`filter_funcs` 只登记了这一个 policy）。`tile_heuristics`（:108-176）：按 `ceil(m_iter*n_iter/aicCoreNum)` 分组，组内以 `(尾部块占比>=0.8 ? 1 : 0, l1_k, l0_k)` 为键取最优，同键并存去重，最终 `num_left=4` 截断。`GemmAutotune.gen_configs`（:276-289）以 `(op_kind, dtype_size, dispatch_policy, shape_desc)` 为键缓存；`_is_support_tile_autotune` 排除 `slice_axis=="K"` 与名字含 GroupedMatmul 的 kernel（:14-15）。bias 融合后（调度器无法预知）`may_adjust_l1_tile_for_bias`（:304-316）用 `may_adjust_l1_tileshape`（:18-27：`(m+n)*k*dtype*stages + n*dtype` 超 L1 预算时先缩 K、再缩较大边，每次 16、m/n 下限 16）重排 L1 tile，`set_l1_tile` 同步压低 L0 的 k（:292-301）。`generate_configs`（:344-349）用 `kernel.get_dispatch_policy()[0]`（注释：currently using the first default policy）与 `(M, N, K, layout_Bias)` 组装。入口 `get_gemm_autotune` 单例默认 AtlasA2（:336-341）；消费者 `catlass_utils.py:186/:209`。

## epilogue → EVG Python 前端（catlass_python_evg.py）

`CatlassEVGOpsMixIn`（:21-88）给出表达式到 EVG functor 文本的映射：`to_dtype`→`cast(x, dst, src)`、`constant`→`constant(value, element)`（dtype 经外部 `catlass_cppgen.common.data_type.DataType.from_dtype`）、加减乘除用中缀、relu/sigmoid 前缀；`tanh`/`ge` 直接 `NotImplementedError`（:67-68/:87-88）——即融合子图里出现这些算子会在转换期失败。`CatlassEVGCodegen.ir_to_evg_python_code`（:169-193）在 `V.set_ops_handler` 下逐 epilogue 节点回放 store 函数：累加器不在 `removed_buffers` 时先建 `tmp = accum` 别名并 store（:163-167）；`load` 查别名表，缺名记入 reads；`store` 登记写集合并跟踪 `last_stored_var_name`；`finalize`（:204-210）把最后一次 store 改名为 `D`；`_AssignmentFormatter`（:95-118）负责临时变量与 `DelayReplaceLine`（写入时机再决定变量名是否为 D）。输出三段：`def fn(accum, reads...):` 签名、赋值体、`return ...`（断言 D 在返回集，:292-304）。**索引限制**：`_check_indexing`（:268-290）只接受与 buffer 布局步长兼容（相等或为 0）的索引，否则 `NotImplementedError`——注释原义：CATLASS 不支持任意索引。消费者 `catlass_scheduling.py:25/:334`。`MockCatlassHandler`（:91-93）是内存规划用的直通 handler。`evg_extension.create_example_tensors`（:15-32）把 IR Buffer 的 shape/stride/dtype 转成外部 `catlass_cppgen` 的 `OpTensor.from_shape_stride`，为 EVG Python 前端提供示例张量。

## 失效边界

- `catlass_cppgen` 外部包未固定版本，其源码不在本仓固定来源内：`GemmShape`/`MmadMultiBatch`/`OpTensor`/`DataType` 的行为只按本仓调用面理解。
- tile 配方是**候选生成器**：真正的选择仍走 autotune 测量（测量链见矩阵乘调优卡），`num_left=4`/0.8 尾部占比是源码常量而非调优结论。
- `tile_heuristics` 注释明确「only consider m&n splitting situation」；动态 shape（sympy 表达式）走 `floor_power_of_2` 的 sympy 回退（:78-84）。
- 未验证 MmadMultiBatch 之外 policy 的 filter 缺席语义（`filter_configs` 对未登记 policy 原样返回）。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/catlass_kernel.py)（primary）：:29-94（类型映射与 Args）、:97-275（TemplateKernel 与 def_kernel）、:277-442（call_kernel 双 pass）、:444-549（ptr/size/stride/load/store）、:552-640（Caller）。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/catlass_library/gemm_autotune.py)（primary）：:1-16（import 面与排除谓词）、:18-106（L1 调整与对齐工具）、:108-198（启发式与过滤）、:200-267（tile 生成）、:270-341（GemmAutotune 与单例）、:344-360（入口与 bias 适配）。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/catlass_python_evg.py)（primary）：:18-93（ops mixin 与 Mock handler）、:95-118、:121-230（codegen 主体）、:241-304（load/store/索引/渲染）、:306-307。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/catlass_library/evg_extension.py)（implementation）：:15-32 全文。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/catlass_utils.py)（implementation）：:186、:209（generate_configs 消费点）。
- 发布 pin 负向证据：`f3ecfe4a` 无 `_inductor/codegen/catlass/` 目录（目录级缺失）。
