---
type: Guide
title: SGLang Diffusion Ascend CI：A3用例、质量基线与Host页缓存
description: 区分历史A3性能表、部分不做一致性的用例和加载期Host内存规避，给出可复核验收方法。
tags:
- task.implementation
- topic.diffusion
- topic.precision
- topic.performance.analysis
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/test/server/ascend/testcase_configs_npu.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/test/server/ascend/conftest.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/test/server/ascend/perf_baselines_npu.json
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/test/server/ascend/test_server_1_npu.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/test/server/ascend/test_server_2_npu.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/test/test_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/test/unit/test_consistency_metrics.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/multimodal_gen/test/server/ascend/test_glm_image_distributed.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/scripts/ci/utils/diffusion/prefetch_consistency_gt.py
  role: implementation
created_at: '2026-11-08T12:27:30Z'
updated_at: '2026-11-09T04:31:18Z'
platforms:
- a3
---

# SGLang Diffusion Ascend CI：A3用例、质量基线与Host页缓存

## 用例不是全平台支持表

Ascend套件区分1/2 NPU：单设备含ERNIE、GLM、FLUX、ZImage、Wan小模型和图像编辑；双设备包含TP2 FLUX/H3、QwenImage Ring2、Wan2.2 W8A8 Ulysses2、LTX2 Ulysses2、MOVA TP2等。部分用例consistency=False，只检服务/性能，不能当质量验收。H3、MOVA用例还固定Host内存参数与offload设置，换规格需重新验。

perf_baselines_npu.json标注Ascend A3历史参考值；它们不是本次测量，也不自动适用于950。conftest只对推理latency设guard，加载latency收集但不assert。A3 CI池的4 NPU与128GiB cgroup可能因权重页缓存挤占offload内存，fixture用posix_fadvise(DONTNEED)释放非当前模型的clean文件页；这是特定CI隔离措施，不是模型kernel优化。

## 一致性与验收

公共测试固定CI媒体数据版本。设置 SGLANG_CONSISTENCY_GT_DIR 后直接读取本地候选文件，不执行官方来源优先选择；本卡 prefetch 流程使用测试常量指向的 sglang_generated/ascend，即 SGLang Ascend 基准，不能当官方基准验收。仅未配置本地目录的远程查找，才按官方输出声明映射及 skip 条件选择来源：NPU 有声明且未跳过时优先官方 Ascend，否则从 SGLang 路径开始；修改采样步数、seed、mask或缓存必须匹配基准协议。mock平台选择/量化路由测试只验证Python控制流，不能证明NPU硬件执行正确。

复核时保存实际模型/依赖、设备数、并行、Host限制、采样参数、基准来源和每项开关，区分服务启动、质量和性能三个结果；不以跳过一致性或宽latency容差代替质量。本次未执行这些CI、模型或benchmark，只读取定义。整卡讨论来源明确的A3测试环境。

## 基准预取的防混用边界

prefetch_consistency_gt显式拒绝非NPU平台，避免从同名CUDA GT目录预取而误通过文件名检查；它要求GT base URL具有测试常量的固定raw前缀，变化时直接失败。缓存按revision分目录，已有.complete也重查所有启用一致性用例的候选文件，验证完整后才安装临时目录并导出SGLANG_CONSISTENCY_GT_DIR。文件存在性/版本检查不等于输出质量通过；本次没有联网预取、运行脚本或比较图像。
