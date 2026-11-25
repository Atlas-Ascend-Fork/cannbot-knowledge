---
{
  "type": "Runbook",
  "title": "MQSMLA compressor 量化模式与 epilog 实现的 dtype 契约矩阵（E2M1 解码逐码精确）",
  "description": "模型/框架：DeepSeek V4.1 MQSMLA compressor（comp KV cache 量化），cann-recipes-infer-g2 仓库；面向 Ascend NPU 的 AscendC epilog（`kv_compress_epilog_v2`，mxfp4_bf16）与 PyTorch native epilog 双实现。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-20T14:17:05Z",
  "platforms": []
}
---

# MQSMLA compressor 量化模式与 epilog 实现的 dtype 契约矩阵（E2M1 解码逐码精确）

## 适用场景

- 模型/框架：DeepSeek V4.1 MQSMLA compressor（comp KV cache 量化），cann-recipes-infer-g2 仓库；面向 Ascend NPU 的 AscendC epilog（`kv_compress_epilog_v2`，mxfp4_bf16）与 PyTorch native epilog 双实现。
- 平台：CPU 侧对照评审 harness（CPU fallback / mocked C++ interface）+ AscendC C++ 断言路径。
- 工作负载：v41 compressor 评审（cache_shape [256,288]、quant_group_size 32、quant_mode mxfp4_bf16、round_scale=True、x_scale 1.0 的 fp4_writer_interface 合同）。

## 触发与观测

对 {unquant, float8} × {epilog=native, epilog=ascendc} 四种组合逐一探测（source 0 seq 137，tool_observed，评审 harness 输出逐字）：

```json
{
  "unquant,epilog=native": "accepted by CPU fallback / mocked C++ interface",
  "unquant,epilog=ascendc": "AssertionError: C++ requires uint8 for mxfp4_bf16",
  "float8,epilog=native": "RuntimeError: index_copy_(): self and source expected to have the same dtype, but got (self) Byte and (source) BFloat16",
  "float8,epilog=ascendc": "accepted by CPU fallback / mocked C++ interface",
  "FP4_decode_layout": "exact equality for all 16 E2M1 codes, 16 distinct BF16 group scales, D=512, row=288 bytes",
  "same_logic:build_cache_mapping": true,
  "same_logic:compute_comp_kv": true,
  "same_logic:_native_compressor_fallback": true,
  "same_logic:forward": true,
  "Indexer": "byte-identical"
}
```

同事件还记录 supplied 元数据不匹配：`fused_compressor_with_our_metadata → KeyError: 'c2a_cmp_state_1d'`、`our_C1A_FA_with_supplied_metadata → KeyError: '1'`、`supplied_base_quant_config → 'QuantizationConfig' object has no attribute 'cmp_cache_quant_group_size'`。

## 探针与操作

- 探针即上述四组合矩阵 + 逐模块逻辑一致性 diff（build_cache_mapping/_entry_link_setter/compute_comp_kv/_native_compressor_fallback/forward 逐项 same_logic 比对）+ E2M1 全码表解码一致性检查（16 个 E2M1 码、16 个不同 BF16 group scale、D=512、row=288 字节）。
- 配套接口合同（fp4_writer_interface）：cache dtype `torch.uint8`、slots `[128, -1]`、kwargs `{quant_group_size: 32, quant_mode: "mxfp4_bf16", round_scale: true, x_scale: 1.0}`（source 0 seq 137 逐字）。

## 机制与判别

- 结论：quant 模式与 epilog 实现存在硬性 dtype/接口契约——
  1. `unquant` + ascendC epilog：C++ 侧要求 mxfp4_bf16 路径 cache 为 uint8，unquant 传入非 uint8 直接 AssertionError；
  2. `float8` + native epilog：native `index_copy_` 要求 self 与 source dtype 一致，uint8 cache 与 BF16 source 失配抛 RuntimeError；
  3. 只有 (unquant, native) 与 (float8, ascendC) 两组配对可运行。
- README 同步的配置约束（source 0 seq 1033，逐字）：「Cache 模式与 epilog 必须配套设置：`float8` 配 `compressor_epilog: ascendc`，`unquant` 配 `compressor_epilog: native`；LI cache 的 E8M0 scale 与 comp cache 的 BF16 scale 属于两套不同的缓存格式。」
- 判别：错误类型本身可区分根因——AssertionError（C++ 合同校验）≠ RuntimeError（aten 算子 dtype 推导），据此可将「配置错配」与「数值精度问题」分开。
- E2M1 解码逐码精确相等表明 FP4 编解码不是精度损失源；精度问题应到分区顺序/元数据（见 本卡草稿）去找。

## 验证信号

- tool_observed（source 0 seq 137）：四组合运行结果 + E2M1 全码表 exact equality + 5 个关键函数 same_logic:true + Indexer byte-identical；scratch_report 落盘 `/var/folders/.../v41-compressor-review-0qiip1vq`（路径在轨迹内为 mac 侧临时目录）。
- 信号等级说明：均为评审 harness（CPU fallback / mocked C++）级观测，非 NPU 真机运行。

## 适用与失效边界

- 适用于：cann-recipes-infer-g2 / deepseek_v4_1 MQSMLA compressor 的 epilog×quant 配置排障；错误消息可作指纹快速定位配错。
- 失效边界：矩阵结论来自 CPU/mock 层；ascendC 真机行为以 C++ 断言为准但未在真机复现该矩阵；`QuantizationConfig` 属性名差异（`cmp_cache_quant_group_size`）属 supplied 侧版本不一致，随版本演进可能变化。
- 元数据 Key 不匹配（c2a_cmp_state_1d / compressed_keys）说明两套实现的状态元数据 schema 不同，互换 cache 时需显式映射，不应静默兼容。

## 附：断言存档

- quant 模式与 epilog 必须配套：unquant+ascendC 触发 C++ uint8 断言、float8+native 触发 index_copy_ dtype 失配，仅 (unquant,native) 与 (float8,ascendC) 可运行
