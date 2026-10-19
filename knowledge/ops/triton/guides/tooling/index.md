# 工具参考（skill 参考文档 verbatim 归档）

verbatim 搬运自 `cannbot-skills` `triton_dev_v2` 分支各算子 skill 的 `references/` 参考文档
（锁定 commit `bf861dda`），**正文未提炼**，仅改写 frontmatter 与跨文档调用关系
（相对链接指向 knowledge 内目标）。这些是各优化/诊断/任务构建工具的**操作口径与判定规则**，
与设计期约束（`../constraints/index.md`）、优化期改写（`../../optimizations/operator_optimization/index.md`）
调用方互补。

## MFU 测定（cannbot-skills `triton-mfu-analyzer`）

- [怎么写 flops.py](mfu_flops_guide.md)：MFU 分子口径——flops/flops_parts 接口与逐段拆分自检。
- [极限 MFU 的测定：(case, 倍率) 二维搜索](mfu_max_shape_search.md)：(用例, 倍率) 网格上找 MFU 最大点。
- [MFU 采集指南（官方 operator_mfu 等价口径）](mfu_profiling_guide.md)：采集命令与标称/实测峰值口径。
- [PMU 是什么，以及怎么读它](mfu_pmu_guide.md)：性能计数器语义与 MFU 依据。
- [坑与解读（MFU 测定）](mfu_pitfalls.md)：峰值口径、dtype 修正、profiling 误差等易错点。

## 仿真器瓶颈诊断（cannbot-skills `triton-simulator-optimizer`）

- [msprof op simulator 采集与解析](simulator_msprof.md)：上板仿真采集与桩流水解析。
- [瓶颈诊断（pipe 占比规则）](simulator_bottleneck_diagnosis.md)：按 pipe 占比判瓶颈类型与 MMAD 上限判定。

## 精度调试（cannbot-skills `triton-precision-debug`）

- [NPU 浮点除法 scale 校正](precision_divide_scale_calibration.md)：坐标/权重查找表法规避硬件除法精度差。
- [精度对齐调试完整案例 —— DynamicQuant](precision_alignment_guide.md)：端到端逐位比对定位分叉点复刻算术路径。
- [Attention 低精度逐位契约](precision_attention_lowprec_contract.md)：FA fp16/bf16 四条逐位契约与 1-ulp 诊断。

## 任务构建（cannbot-skills `triton-task-extractor`）

- [算子任务格式规范](task_format.md)：Model / get_inputs / get_init_inputs / get_input_groups 结构约定。
