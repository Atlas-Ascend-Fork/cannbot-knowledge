---
type: Guide
title: 主线 DVM 测试族：融合触发条件、分解表消费、K=1 降级与图融合回退守卫
description: 固定提交下 test/_inductor/dvm 六个测试文件揭示的 DVM 融合行为：int64/int32 规则差异、K=1 矩阵降 k.mul、rms_norm 经 dvm 分解表激活、DvmGraphFusionPatch 的动态图 stride 补丁守卫、FlexAttention 无可编译 choices 的当前态、npu_backend 编译选项路由。
tags:
- task.testing
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/dvm/test_dvm_mlir_fusion.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/dvm/test_dvm_graph_fusion.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/dvm/test_dvm_flex_attention.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/dvm/test_dvm_elu_native.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/dvm/test_dvm_fake_tensor_cache_on_off_crosscheck.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/_inductor/dvm/test_dvm_kernel.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/decomp.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/dvm/config.py
  role: implementation
created_at: '2026-11-12T17:05:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 主线 DVM 测试族：融合触发条件、分解表消费、K=1 降级与图融合回退守卫

## 固定版本与范围

主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 `test/_inductor/dvm/` 六文件。后端选择码生成/回退/布局缓存/Triton 模板边界的实现面归 [DVM 融合执行卡](torch_npu_dvm_mlir_codegen_and_fallback.md)，成本预测归 [区域预测卡](torch_npu_dvm_fusion_region_cost_prediction.md)，数学注册层归 [分解注册卡](../../../../training/guides/torch_npu_mlir_dvm_decomposition_registry_and_training_math.md)。本卡只记测试侧契约。全部静态阅读，未运行。

## mlir_fusion：融合触发条件与数值契约（test_dvm_mlir_fusion.py，826 行）

运行前提：`TORCHINDUCTOR_NPU_BACKEND=dvm`（多数用例再加 `INDUCTOR_DVM_ENABLE_MATMUL_FUSION=1`）。

- **规则面差异**：int64 加/比较/链（add/greater/greater_equal/equal/select）融合进 DVM kernel（:216-279）；int32 `bitwise_not` 不融合（生成代码无 `k.logical_not`，:498-508）——int64 逐点可入、int32 位运算走回退是规则表的显性分界。BOOL 位运算融合为 `k.logical_and/or/not`（:483-496）。`silu`/`silu_backward` BF16 对 aclnn eager `torch.equal` **逐位相等**（:229-248）。
- **矩阵**：K=1 的 mm/bmm/addmm 降级为 `k.mul`（不出 `k.matmul`，:609-657）——1×N 外积按逐点处理；mm/bmm/addmm/baddbmm 模板正常融合 `k.matmul`；view-only epilogue 不阻止融合、view+pointwise epilogue 融合、多用户输出融合（:659-745）；bmm 两个输入是同一 buffer 的不同 reshape 时输入元数据保持独立（:747-762）。`mm(a,b.t()).sum()` 反向不产生 `dvm_fused_matmul_backward`（:510-527）。
- **分解表消费**（与 [分解注册卡](../../../../training/guides/torch_npu_mlir_dvm_decomposition_registry_and_training_math.md) "六条注册被注释" 的对账）：DVM 后端经 `dvm_config.enable_decomp_list`/`disable_decomp_list`（同时出现时 disable 优先）消费这些数学分解——`npu_rms_norm` 默认分解（生成代码无 `torch.ops.npu.npu_rms_norm.default(`），把 forward 放 disable 列表则保留 aten 调用、把 backward 放 enable 列表则 backward 仍分解为 `@dvm.kernel`（:324-369 子进程用例）；`npu_rms_norm`/`npu_rms_norm_backward` 分解对 CANN 实现的数值容差按 dtype 分层 fp32 1e-4 / fp16 1e-3 / bf16 5e-3，gamma 支持 1 维与 2 维（:373-404）；`npu_linear`(+backward) 分解为 `k.matmul`（≥3 次）且 relu 以 `k.maximum` 融入同一 kernel（:528-554）。elu 除外——走 DVM 原生 aclnn 回退（见 elu 节）。
- **codegen/回退观测**：patch `_is_node_supported_by_dvm_rule` 强制 codegen 期全 FX 回退时，生成代码出现 `async_compile.import_fx(`（分区保持）；正常路径 `@dvm.kernel`。`triton.autotune_at_compile_time` 开启时每个编译产物的模块 docstring 含 "Compile-time auto-tuning block:" 且不含 `@dvm.kernel`/`import_fx`（:147-195）。`copy_`/`copy` 均以 `@dvm.kernel` codegen（:764-788）。deterministic 模式下归约两次运行 atol=0 相等（:463-481）。`options={"triton.cudagraphs": True}` 下 DVM 编译产物入 NPUGraph 复用（:421-438）。`npu_fusion_attention` BNSD/TND（含 actual_seq_qlen/kvlen）在 DVM 后端 fullgraph+dynamic 编译（:790-821，子进程隔离，理由=后端初始化改进程全局状态，即分解注册卡记录的 `importlib.reload(torch._inductor.graph)`）。
- **测试基建事实**：`options={"npu_backend": "dvm"}` 是环境变量之外的编译选项路由（elu 文件同款）；dvm/ 六文件本身无 runIfVersion 版本门（该门只出现在 `test/_inductor/` 根目录测试文件，如 test_symbolic_grouping.py:33，版本门事实由[分组 meta 构造卡](torch_npu_main_inductor_grouped_meta_construction.md)的纯函数验收契约节承载）。

## graph_fusion：独立图融合入口与 stride 补丁守卫（test_dvm_graph_fusion.py，175 行）

`DvmGraphFusionPatch()` 是独立于后端安装的上下文管理器式图融合补丁（graph_fusion 入口的实现面见[融合执行卡](torch_npu_dvm_mlir_codegen_and_fallback.md)的独立 graph_fusion 入口节），测试用它配 plain inductor 编译跑通 pointwise/matmul/npugraph。守卫 `adb97b9`：`_dvm_generate_fallback_kernel` 仅在 `is_fx_dynamic(gm)` 为假时调用 `patch_gm_placeholder_strides_from_codegen_args(gm, bufs)`；`is_fx_dynamic` 对 `symbolic_trace`+真实张量 meta 的图返回假、对 `torch.export` 动态 dim 的图返回真——动态子图 codegen 跳过 stride 补丁，静态子图照常补（:103-171）。

## FlexAttention 当前态与 elu 原生回退

- test_dvm_flex_attention.py（569 行）**全部四个用例 `@unittest.skip`，理由统一为 "DVM FlexAttention has no compilable choices in the current DVM backend"**——与 [融合执行卡](torch_npu_dvm_mlir_codegen_and_fallback.md) "loader 在配套 Triton 可用时注册 NPU FlexAttention 模板" 合读：模板注册存在但当前 DVM 后端对它产不出可编译 choice，四个端到端/结构契约（组合掩码、Triton 模板、compile-time autotune、env 后端选择）处于停用状态。脚本内静态断言 `aten.index.Tensor in _get_flex_attention_additional_lowerings()`。
- test_dvm_elu_native.py（52 行）：elu **不在分解表**（docstring 原义，策略断言在 test_dvm_decomp.py，该文件不在本固定树 dvm/ 目录），经 DVM 后端的 aclnn 原生回退数值收敛；`options={"npu_backend": "dvm"}` 编译选项路由；注释两个基建事实——import `torch_npu._inductor` 即在导入时装载后端（首个 compile 变成进程内 default→dvm 切换），纯 `import torch_npu` 不装载；"npu normal kernel has no bf16 support"（elu 参考先 fp32 构造再转）。

## FakeTensor 缓存等价与直接 kernel API

- test_dvm_fake_tensor_cache_on_off_crosscheck.py（97 行）：DVM 后端下 FakeTensor dispatch cache 关闭与开启+crosscheck 两种配置产出的 FX 逐节点 Tensor 元数据（example_value/val 经 `extract_tensor_metadata`）完全相等——缓存开启不改变 DVM 图的形状/步长/dtype 元数据流。docstring 同款警告：模块顶层 import `torch_npu._inductor` 会钉住后端，须 env+`register_inductor_npu` 先行。
- test_dvm_kernel.py（39 行）：`dvm.kernel(ktype="vector"/"split", dyn_shape=True)` 装饰、`k.load` 隐式广播、`k.scalar`、`k.sum(keepdim)`、`run()` 写预分配输出 vs 调用返回新输出——为 [融合执行卡](torch_npu_dvm_mlir_codegen_and_fallback.md) 已记录的 call/run 双合同的直接使用镜像。

## 已覆盖镜像与边界

- 配置默认（enable_cat=False、`INDUCTOR_DVM_ENABLE_MATMUL_FUSION` 精确 '1'、view_fusion_level、vf_fusion 三级）归 [融合执行卡](torch_npu_dvm_mlir_codegen_and_fallback.md) config 节；cat 融合测试以 `mock.patch(enable_cat=True)` 打开是消费方式镜像。
- 分解数学本体（RMSNorm/SwiGLU/Rotary 公式与未安装状态）归 [分解注册卡](../../../../training/guides/torch_npu_mlir_dvm_decomposition_registry_and_training_math.md)；本卡的贡献是**DVM 路径下这些分解实际经 dvm decomp 表激活**的对账事实与数值容差锚。
- 静态口径：未运行任何测试；`torch.equal` 的 BF16 逐位相等、容差分层、skip 状态均为源码记录，不外推任意 shape/版本组合。
