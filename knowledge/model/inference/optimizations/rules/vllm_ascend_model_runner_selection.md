---
type: Optimization
title: vLLM Ascend Runner 选择规则：V2 默认、功能回退与环境覆盖
description: 按环境覆盖、功能排除表和Worker选择实际Runner，区分V1 PP异步允许列表与async_scheduling默认关闭、V2验证patch和各进程安装时序；回退不代替模型/硬件性能验收。
tags:
- task.optimization
- topic.model_serving
- topic.compilation
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/mrv2_utils.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/worker_310p.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/test_mrv2_utils.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/patch_use_v2_model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/platform/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/worker/patch_v2/patch_use_v2_model_runner.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/patch/__init__.py
  role: supporting
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/config/vllm.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/patch/platform/test_patch_use_v2_model_runner.py
  role: evidence
created_at: '2026-10-29T08:35:04Z'
updated_at: '2026-10-30T01:36:59Z'
platforms:
- a2
- a3
- 310p
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Runner 选择规则：V2 默认、功能回退与环境覆盖

## 适用场景与问题信号

适用于 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 的 Runner 初始化和性能基线选择，参考 vLLM `v0.32.0`。当增加功能后执行路径变化、不同进程选到不同 Runner，或同一调参结果不可复现时，先核对本规则。Runner V1/V2 与 vLLM 的 V1 engine 不是同一个维度。

## 选择顺序

1. `VLLM_USE_V2_MODEL_RUNNER` 在上游解析后不是 `None` 时，返回该显式值，优先于默认排除表。
2. 未设置环境覆盖时，命中 `_v2_blacklist()` 的任一条件就选择 V1 并记录原因。
3. 其余配置默认 V2。排除表以功能与配置为依据，不按平台身份直接排除 310P。

固定实现的排除条件如下：

| 条件 | 精确判据或需要区分的边界 |
| --- | --- |
| pooling | `runner_type="pooling"` 或 `is_pooling_model is True` |
| VL encoder graph | `compilation_config.cudagraph_mm_encoder is True` |
| draft window | `additional_config.draft_window_size` 不为 `None`，不是仅检查大于零 |
| DSA-CP | `enable_dsa_cp` 经布尔、整数 1 或字符串 `1/true/yes` 判断启用 |
| suffix / ngram | speculative method 为 `suffix`、`ngram` 或 `ngram_gpu` |
| 独立 draft model | speculative method 为 `draft_model` |
| DFlash2 图路径 | draft 架构含 `DFlash2DraftModel`，且 draft 的 `enforce_eager` 不是 `True` |
| p-eagle | method 为 `eagle` 或 `eagle3`，同时 `parallel_drafting is True` |

例如，仅有 LoRA、Mooncake connector 或 `parallel_drafting=True` 并不单独构成这个版本的排除条件；这只描述 Runner 选择，不证明它们与其他功能全面兼容。

## 实施要点

保存环境覆盖、配置和选择日志，确认 Worker 实际构造的 Runner。标准 Worker 按 property 在 V1/V2 之间选择；310P 的 `NPUWorker310._create_model_runner()` 分别构造 `NPUModelRunner310` 或 `NPUModelRunner310V2`，不能套用“310P 一律 V1”的历史判断。

`apply_v2_model_runner_config_patch()` 把 `VllmConfig.use_v2_model_runner` 替换为 Ascend property，并接管对应上游验证。类补丁须在前端、EngineCore 和 Worker 等读取它的进程重新应用。只检查前端的一个配置值不足以定位多进程问题。

显式覆盖可以绕过默认排除表，但不会取消其余模型和功能校验。例如固定平台逻辑要求具备 `DSV41_PACKED_CACHE` 的 DeepSeek V4.1 路径使用 V2，强制 V1 可直接被拒绝。不要用覆盖开关把未支持功能写成已支持。

## 收益、代价与性能验证

本规则用于确认实验实际比较的是哪条执行路径。没有固定 workload 下 V1/V2 的统一收益数据，不能承诺 V2 必然更快。相同模型、权重、硬件、输入、并行和功能下，先对齐精度，再分别记录预热、TTFT/TPOT、吞吐、峰值显存及波动。功能变化、配置自动回退或执行类不同的结果须分开报告。

## 回退与停止条件

可用 `VLLM_USE_V2_MODEL_RUNNER=0` 显式回到 V1，但先确认目标模型和功能允许 V1；需要比较默认策略时移除覆盖并重新启动各进程。选择与预期不符、功能校验失败或输出不正确时停止性能结论，检查排除原因和实际调用类。

## Evidence

`mrv2_utils.py` 给出选择顺序和完整排除表；Worker 和 310P Worker 给出消费路径；`platform.py::_validate_model_runner_config` 给出强制 V2 的反例。UT 定义覆盖环境优先、默认 V2、各回退分支、310P 和 property 重复安装；本次未执行这些 UT 或 NPU 性能测试。

相关机制见[插件架构](../../concepts/frameworks/vllm_ascend.md)与[硬件能力契约](../../concepts/frameworks/vllm_ascend_hardware_profiles.md)。


## V1 PP异步：允许列表与默认开关是两层控制

以下只针对固定vLLM v0.32.0线路与本卡Ascend提交，不由补丁注释的“两个支持版本”推广到未读的main实现。

原生_get_v1_model_runner_unsupported_features在PP>1且async_scheduling为真时加入pipeline parallelism with async scheduling；_validate_v1_model_runner读取该列表，非空就抛Model Runner V1 does not support。Ascend的patch_use_v2_model_runner.py另把该helper包装为_patched_get_v1_model_runner_unsupported_features：先调用原函数，再按_ASCEND_V1_SUPPORTED_FEATURES过滤准确标签。

| 允许列表中的准确字符串 | 过滤所关闭的缺口 |
| --- | --- |
| dspark speculative decoding | 该上游V1拒绝项 |
| dflash2 drafts | 只有上游实际返回同一字符串才会移除 |
| pipeline parallelism with async scheduling | V1 PP异步这一项的上游GPU限制 |

这不是把整个V1 validator改成no-op。固定v0.32.0这段helper的直接追加项如下；两个DFlash子谓词的完整模型识别逻辑不在本次范围内，不能由表内标签反推某checkpoint一定命中。

| 原生直接条件 | 追加标签 | Ascend准确过滤结果 |
| --- | --- | --- |
| prefill_context_parallel_size>1 | prefill context parallel | 保留 |
| PP>1且async_scheduling为真 | pipeline parallelism with async scheduling | 移除这一项 |
| speculative method为dspark | dspark speculative decoding | 移除这一项 |
| speculative enable_adaptive_verification启用 | adaptive draft verification | 保留 |
| _dflash_needs_multi_kv_group()为真 | mixed sliding/full dflash drafts | 保留 |
| _is_dflash_candidate_draft()为真 | DFlash candidate-head drafts | 保留 |
| 非空model_config的is_diffusion为真 | diffusion models | 保留 |
| enable_batch_sharded_sampling启用 | batch-sharded sampling | 保留 |

该v0.32.0 helper没有直接追加dflash2 drafts本身，允许列表保留这个字符串不等于放行另外两个DFlash条件。不能把它们当同义词，也不能从PP异步这一项被移除推定PCP、所有投机方法或所有设备组合已支持。

同时，原生较早的async_scheduling解析在输入为None时读取当时的Runner：若前面其他禁用分支均未命中、PP>1且use_v2_model_runner为False，会把async_scheduling设False。允许列表只过滤后续拒绝项，不把False改成True；因此“默认走同步”与“显式True必然被这个拒绝项挡住”是不同判断。显式True仍会经过executor支持、投机类型/disable_padded_drafter_batch等实际校验，其他平台/配置检查也继续生效。最终以平台钩子后的有效开关、实际scheduler/Runner与进程日志为准，不由最终Runner反推早期property安装时序。

## 两类patch分别核对

mrv2_utils.apply_v2_model_runner_config_patch只安装Ascend的use_v2_model_runner property与空的_validate_v2_model_runner；它本身不安装上述V1允许列表。后者由platform/patch_use_v2_model_runner.py模块导入时替换V1 helper；platform/__init__.py导入该模块，worker/patch_v2/patch_use_v2_model_runner.py再复用同一platform模块。只看到utility被调用，不能认定该进程的V1 helper也已替换；普通导入复用也不承诺任意显式reload/并发patch安全。

原生在current_platform.check_and_update_config后再次按有效Runner选择V1/V2验证方法。Ascend中和V2验证不等于删除V1验证；已安装的V1 wrapper应保留不在允许集合内的拒绝项。多进程取实际安装函数、最终配置和类；不要直接清空整个unsupported列表来绕过不明限制。

固定UT定义包含：mock列表保留PCP/diffusion；PP∈{1,2}、async∈{false,true}与PCP∈{1,2}组合调用真实上游helper/validator；另有V2 spec+PP helper断言。它们是测试定义，不是本次执行结果，未实例化真实PP/CPP Runner来验证模型精度、通信或时延。CPP控制面与实际运行支持应沿[CPP指南](../../guides/optimization/vllm_ascend_cpp_prefill_calibration.md)分别验收。
