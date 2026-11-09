---
type: Optimization
title: vLLM Ascend 原生 FP8：block scale、950 重组与浮点回退预算
description: 对原生 block-wise FP8 权重按硬件和层形态选择 MXFP8 重组或模型 dtype 展开，检查 scale 配对、归约维整除和
  MLA 吸收层，避免按磁盘位宽估算显存。
tags:
- task.optimization
- topic.precision
- topic.memory
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/configs/fp8_config.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/quantization/methods/w8a8/fp8_block.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/quantization.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.agents/skills/vllm-ascend-model-adapter/references/fp8-on-npu-lessons.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/.agents/skills/vllm-ascend-model-adapter/references/troubleshooting.md
  role: supporting
created_at: '2026-10-29T09:34:19Z'
updated_at: '2026-10-29T16:27:59Z'
platforms:
- a2
- a3
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend 原生 FP8：block scale、950 重组与浮点回退预算

## 条件与问题信号

适用于固定 Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 标准后端的 `quant_method="fp8"` checkpoint。310P 的配置注册不在此范围。模型能加载却权重显存接近 BF16、950 某层没有进入 FP8 matmul，或 weight_scale_inv shape 失败时，先检查本规则。

## 输入格式与层选择

AscendFp8Config 要求 `weight_block_size` 存在且 activation_scheme 为 dynamic；per-tensor/per-channel 原生 FP8 不在该路径内。ignored_layers/modules_to_not_convert 及 packed 映射决定跳过层，跳过的 Linear/MoE 返回浮点方法，不能强行给它们套量化 scale。

权重按二维 `[out,in]` 存储，每个 `block_n × block_k` tile 配一个 float32 scale。期望 scale shape 为两轴向上整除后的尺寸，不能把倒数命名、逐层 scale 或量化权重分片任意混配。resolve_block_scales 在权重设备上用 float32 乘 scale，再存入模型 dtype，分行处理以约束临时展开开销。

## 执行选择与例外

| 路径 | 实际处理 | 预算和边界 |
| --- | --- | --- |
| 950 常规层 | 展开后重组为 MXFP8，配 E8M0 scale，再使用对应量化方法 | scale 分组与归约维须匹配；加载期仍有临时展开/重量化开销 |
| 其他标准平台 | 展开为模型 dtype，走非量化 GEMM/MoE | 磁盘 FP8 不等于运行期一字节权重，按实际 dtype 预算 |
| 950 归约维不满足 MX group | 该层回到模型 dtype | 不能由卡型保证所有层都使用 MXFP8 |
| MLA/SFA 吸收的 kv_b_proj | 保留展开矩阵供 Attention 拆分吸收 | 该投影不再走普通 apply，不能为节省一份权重破坏吸收输入 |

MoE 按专家展开或原地重量化，减少一次性展开整个专家栈；但最终权重、scale、临时张量和 KV 总预算仍需分开计算。文档的“约两倍”描述只针对浮点展开权重，不能直接乘成整机峰值显存结论。

## 收益、风险与验证

候选收益是减少运行期权重存储或使用相应量化算子；来源未提供统一端到端收益。固定模型、权重和 workload，先检查各关键层的真实方法、dtype 和 scale layout，再对齐输出、精度及加载峰值，最后测稳态吞吐/时延。

不能把 block FP8 转 MXFP8 视为字节保持或数学无损；具体误差由转换与算子验证决定。shape 校验失败、scale 未配对、意外浮点回退或精度退化时停止收益判断，恢复原量化配置或明确采用已验证浮点路径。

## Evidence

FP8Config 的格式门控与 fp8_block 的 Linear/MoE 加载、尾块、重组和 fallback 分支均已核对；未执行 NPU 数值与性能实验。



## 适配经验中的“FP8不支持”必须按实现裁决

同一固定提交的FP8适配经验记录过`fp8 quantization is currently not supported in npu`，并建议weight/weight_scale_inv配对展开；这个历史故障信号不能代替当前原生block-FP8实现的选择条件。当前950常规层可能展开后重组MXFP8，其他平台或不满足group条件的层走模型dtype；Attention吸收层又有自己的例外。不能按“checkpoint标成fp8”就统一禁用，也不能反过来给per-tensor/per-channel或非dynamic配置强行套block路径。

经验中严格检查未配对weight/scale、真实shard和KV-head复制norm分片仍有诊断价值，但具体loader在哪个阶段拒绝漏键需要按实际实现核验。dummy能走算子/API不等于真实scale与所有必需参数都正确；用真实权重和完整模型通过[分阶段验收](../../guides/bringup/vllm_ascend_new_model_onboarding.md)后，才进行数值与内存/性能比较。经验里的AIV通信展开建议也不是所有FP8失败的通用修法。
