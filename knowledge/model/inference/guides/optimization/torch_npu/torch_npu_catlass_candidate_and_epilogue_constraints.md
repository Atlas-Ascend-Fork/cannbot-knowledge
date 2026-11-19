---
type: Guide
title: Inductor Catlass 实际候选生成与 Epilogue 融合限制
description: 从固定源码解释 Catlass 库发现、形状提示、候选去重截断及调度器的 Pointwise、快速融合与 EVG 门槛。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/gemm_template.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/catlass_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/catlass_scheduling.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py
  role: implementation
created_at: '2026-11-10T11:16:22Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Inductor Catlass 实际候选生成与 Epilogue 融合限制

## 固定版本与范围

定向审阅 PyTorch/TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 Catlass 模板、候选生成和 Epilogue 调度门槛。发布版 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 不含本卡主源 `torch_npu/_inductor/codegen/catlass/gemm_template.py` 这一文件；这只证明该路径不能直接移植为发布版说明，不断言发布版完全不存在其他矩阵乘实现。

未导入 Catlass、执行上游代码或验证设备，本卡使用 `draft`、空平台。文档声明的硬件范围与开关用法见[矩阵乘调优与配置](torch_npu_inductor_catlass_autotune.md)；本卡补充消费者实际拒绝或改写候选的条件，不把开关打开等同于融合成功。

## 先核对实际加载的模板库

`try_import_catlass()` 首先尝试 Python 搜索路径中的 `catlass` 和 `catlass_cppgen`；成功时会将 `catlass_dir` 指向该包的 `source` 目录。只有这条路径触发 `ModuleNotFoundError`，才继续尝试配置目录下的 `python/catlass_cppgen`，借缓存目录的符号链接装载。

因此环境变量里指定的目录不是实际模板来源的充分证据；同时存在已安装包时，应核对导入日志和实际包位置。这个发现函数有 `lru_cache`，也不应依赖运行中切换路径立即重新选择库。这里只分析源码优先级，未安装或加载任何包。

## 候选使用形状和布局信息，并会去重和截断

模板把输入的 shape、stride 和 dtype 转成 Catlass `OpTensor`。符号值先代入 `backed_var_to_val`，不能转成整数时使用 `8192` 提示值；`get_shape_desc()` 和布局兼容检查也有相应提示路径。**8192 是候选构造/优化提示的兜底值，不是用户输入被补齐到 8192 的保证，也不代表动态范围已逐值调优。**

`_gen_ops_cached()` 根据设备架构、输入描述和是否 grouped mm 构建 `Gemm`/`GroupGemm`，先获取库返回的 kernels，再添加默认调优配置及 `generate_configs()` 产生的 tiling。只有 `matmul.allow_hf32` 为真且两个输入类型都是 FLOAT 时，才将 `is_hf32=True` 传给这条候选构造路径；不从此推导所有 FP32 算子都走同一精度策略。

随后 `gen_ops()` 以 `op.gen_kernel_name()` 为键去重，并用 `catlass_max_profiling_configs` 切片。该配置默认 `None`，即本处不截断；源码注释称限制值主要用于缩短 CI 测试。截断发生在候选列表进入调优之前，不是按测得性能选前若干名；减少它可能漏掉最优候选，不能当作无损提速。

`_add_catlass_gemm_choices()` 还明确要求传入 `alpha == 1` 且 `beta == 1`，否则告警并直接返回。没有生成 ops 时记录 `No suitable Catlass GEMM configs found, fallbacks used`，并输出输入/输出 layout 和 stride。该函数返回只表示本处未添加 Catlass 候选，最终是否存在其他可执行候选仍需检查外围 lowering 和调优结果。

## Epilogue 不是任意后处理融合

`CATLASSScheduling._can_fuse_epilogue_impl()` 的重要限制包括：

- 当前不支持已有 Epilogue 上继续链式叠加，函数断言已有 Epilogue 列表为空；待融合节点若已是 `FusedSchedulerNode` 则直接拒绝。
- 每个节点都须是有名字的 `ComputedBuffer`，内部是 `Pointwise`，且输出 size 与 Catlass 模板一致；第一个 Epilogue 必须读取该模板结果。
- 有 alias/mutation、reduction 的节点被拒绝。节点 dtype 或 stride 可以不同这条注释，不意味着任意布局都被证明可融合，后续 EVG 转换仍需成功。
- `catlass_epilogue_fusion_enable` 与 Inductor 通用 `config.epilogue_fusion` 必须同时启用，模板的 `epilogue_fusion_type` 不能为零。
- 调度器先尝试将节点转成 EVG 表达；不支持的操作会拒绝。之后检查快速融合；若快速融合不支持，模板必须支持 EVG，且这条 EVG 回退检查拒绝 bfloat16 输出节点。

这些检查给出可尝试融合的必要条件，不证明融合后的候选最终胜出。横向融合消费者 `can_fuse_horizontal()` 固定返回假；不能用 Catlass 有 Epilogue 融合来推导两个并列 GEMM 会合并。

## 快速融合和 EVG 采用不同路径

`_try_fast_fusion()` 只接受一个 Epilogue 节点，去掉 load 后仅支持 `add`、`relu`，并限制各自操作次数。`add` 的其他输入必须是一维且 stride 为 1 的 bias，矩阵 Add 不能由这条快速路径处理；可表达 biasAdd、ReLU 或 biasAdd+ReLU。

生成阶段先尝试快速融合，失败才转 EVG。若原模板已有 Bias、Epilogue 只含 ReLU，主线保留原 Bias；额外融合 Bias 时会调用 `may_adjust_l1_tile_for_bias()` 尝试调整 L1 tiling。这里仅记录模型图到模板的决策，不给出未经验证的 Kernel tiling 配方。

模板通过 `is_support_relu`、`is_support_evg` 标记决定融合类型，支持 EVG 时类型设为 2；不能因为图里含 ReLU 就忽略实际模板能力。诊断时分别保留候选生成告警、WhyNoFuse 原因、最终生成代码与实际执行路径，再比较首编译和稳态成本。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/gemm_template.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/catlass_utils.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/codegen/catlass/catlass_scheduling.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py)（implementation）
