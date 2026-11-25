---
{
  "type": "Runbook",
  "title": "CANN 9.0.0（A3/910_9362）的 npu_mla_prolog_v3 bf16 非量化路径要求权重 FRACTAL_NZ 布局：enable_weight_nz=False（ND）时 aclnnMlaPrologV3WeightNz 支持列表报 bf16 路径需 NZ；infer.py:194 曾在非 950 平台强制覆盖 yaml 开关，修复后 yaml 显式值优先",
  "description": "在 Ascend A3（910_9362，CANN 9.0.0）上用 cann-recipes-infer 类框架跑 MLA+DSA 新模型（本例 GLM-5.2：`q_lora_rank=2048`、`qk_nope_head_dim=192`、bf16 非量化权重），warmup prefill 在 `torch_npu.npu_mla_prolog_v3` 处失败。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---

# CANN 9.0.0（A3/910_9362）的 npu_mla_prolog_v3 bf16 非量化路径要求权重 FRACTAL_NZ 布局：enable_weight_nz=False（ND）时 aclnnMlaPrologV3WeightNz 支持列表报 bf16 路径需 NZ；infer.py:194 曾在非 950 平台强制覆盖 yaml 开关，修复后 yaml 显式值优先

## 适用场景

- 平台范围依据：source 0 seq 845、source 0 seq 846、source 0 seq 1412的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

在 Ascend A3（910_9362，CANN 9.0.0）上用 cann-recipes-infer 类框架跑 MLA+DSA 新模型（本例 GLM-5.2：`q_lora_rank=2048`、`qk_nope_head_dim=192`、bf16 非量化权重），warmup prefill 在 `torch_npu.npu_mla_prolog_v3` 处失败。适用于判断「是模型适配代码错还是内核契约不支持」。

## 触发与观测

warmup prefill 第一个 minibatch 即失败（source 0 seq 1090/1098），按配置不同出现三级可区分错误：

1. **NZ 权重 + 超限维度**：`enable_weight_nz=True`（`infer.py:194` 在非 950 平台强制覆盖 yaml）+ `q_lora_rank=2048` → `aclnnMlaPrologV3WeightNz` 报 `NnopbaseExecutor...failed`（error 561002，tiling 失败，无显式维度信息）（source 0 seq 1090、1098）。
2. **ND 权重 + q_lora 超限**：改 ND 后 → `mla_prolog_tiling_check.cpp` 显式报 **`Hcq allows only 1536, got 2048`**（Hcq=q_lora_rank）（source 0 seq 1144）。
3. **ND 权重 + q_lora 合规**：`aclnnMlaPrologV3WeightNz` 支持列表显示 bf16 路径**要求权重 FRACTAL_NZ 布局**——之前「bf16 需退 ND」的假设被证伪，该算子要求 NZ（source 0 seq 1307）。
4. **NZ + q_lora=1536**：下一维度顶上限 → **`D allows only 128, got 192`**（D=qk_nope_head_dim）（source 0 seq 1365）。

## 探针与操作

- 逐级二分变量：仅切换 `enable_weight_nz`（并修 `infer.py:194` 使其尊重 yaml 显式值，W8A8 既有 yaml 不受影响）（source 0 seq 1123/1124）；再用权重生成器 `--q-lora-rank/--qk-nope-head-dim/--v-head-dim` 覆盖项生成 CANN-9.0.0 兼容变体（1536/128/128），保持 GLM-5.2 IndexShare 层型不变（source 0 seq 1366/1382）。
- 核对宿主机 CANN 安装：`<internal_build_path> -> cann-9.0.0`，无 9.1（source 0 seq 1146）；glm-5 README 要求 CANN 9.1 镜像。

## 机制与判别

CANN 9.0.0 的 `mla_prolog_v3` 系列内核按 DeepSeek-V3.2 维度构建：bf16 非量化路径要求权重 **FRACTAL_NZ** 布局（`weight_quant_mode=0` 时仍走 WeightNz 内核），且 `q_lora_rank(Hcq)≤1536`、`qk_nope_head_dim(D)≤128`、`v_head_dim≤128`。GLM-5.2 的 2048/192 超限：NZ 路径表现为 561002 通用 tiling 失败、ND 路径表现为 tiling_check 显式上限报错——三级错误串互相可区分，且均已实测复现（source 0 seq 1098、1144、1307、1365）。与模型适配代码无关的判据：traceback 显示失败点在 `prepare_qkv → npu_mla_prolog_v3`（预存在算子调用），IndexShare 线程链在此之前的各帧均正常执行（source 0 seq 1103）。

## 验证信号

修复组合 **NZ=True + q_lora=1536 + qk_nope=128 + v_head=128** 后端到端跑通（source 0 seq 1410/1412）：

- `model run success`，日志 0 个 Traceback/RuntimeError/`allows only`；
- prefill 首次编译 1449.93 ms、warm 23.39 ms；decode ~35.8 ms/step（8 层裁剪随机权重、4 rank A3，仅结构性时延，非性能结论）；
- 随机权重输出乱码 token，符合预期（验证目标是结构执行，非精度）。

真实 GLM-5.2 维度（2048/192）在本机的正确解是升级 CANN 9.1 镜像（glm-5 README 明示），未在本轨迹验证。

## 适用与失效边界

- 结论限 CANN 9.0.0 + A3（910_9362）+ `npu_mla_prolog_v3`（WeightNz 变体）；CANN 9.1 的上限未测。
- `infer.py:194` 平台强制覆盖 `enable_weight_nz` 的行为属该仓实现，修复后 yaml 显式值优先。
- 561002 在 NZ+超限维度下的具体触发路径（是否恒为 Hcq 越界）只有 ND 路径的显式报错佐证，NZ 路径的归因是推断+对照实验支持。
- 兼容变体的时延数字不可外推为真实模型性能（随机权重、8 层、无量化）。

## 附：断言存档

- CANN 9.0.0（A3/910_9362）的 npu_mla_prolog_v3 bf16 非量化路径要求权重 FRACTAL_NZ 布局：enable_weight_nz=False（ND）时 aclnnMlaPrologV3WeightNz 支持列表报 bf16 路径需 NZ；infer.py:194 曾在非 950 平台强制覆盖 yaml 开关，修复后 yaml 显式值优先

```text
platform_version = runner_settings.get("model_config").get("platform_version", "A3")
    # Honor an explicit yaml `enable_weight_nz`. Quantized (W8A8) runs on A3 require NZ weights, but
    # the unquant bf16 path must use ND: the mla_prolog_v3 WeightNz kernel only supports quantized
    # weights (bf16+NZ fails with a tiling error). Existing W8A8 yamls set this True, so they are unaffected.
    enable_weight_nz = runner_settings.get("model_config").get(
        "enable_weight_nz", not platform_version == "950")
```

```text
rm -rf weights_cann90 && python3 utils/gen_random_cropped_weights.py --q-lora-rank 1536 --qk-nope-head-dim 128 --v-head-dim 128 --num-experts 8 --out weights_cann90 --shard-gb 8
```
