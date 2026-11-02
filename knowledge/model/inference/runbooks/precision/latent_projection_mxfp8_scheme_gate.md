---
type: Runbook
title: LatentMoE 投影误用量化方案：只在 Linear 显式匹配动态 MXFP8 时启用
description: 按 Kimi K3 Linear 的动态 group-32 W8/A8 MXFP8 条件选择 latent down/up 投影；明确权重、激活与
  ignore 门控，并区分 MXFP8、浮点与不匹配配置。
tags:
- task.debugging
- topic.precision
- topic.mixture_of_experts
status: stable
sources: []
created_at: '2026-10-30T03:17:20Z'
updated_at: '2026-10-30T09:01:39Z'
platforms:
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      model_features:
        all_of:
        - moe
---

# LatentMoE 投影误用量化方案：只在 Linear 显式匹配动态 MXFP8 时启用

## 现象

Kimi K3 的 routed experts 可以使用 MXFP4，但 routed 分支前后的 latent down/up 投影并不是专家 GMM 本身。如果直接把专家或通用 `Linear` 的量化配置传给所有投影，就可能在构造、权重加载或精度验收中进入与 checkpoint 不一致的路线。

需要分别确认 `routed_expert_down_proj`、专家 GMM 和 `routed_expert_up_proj`：不能看到专家已量化、KV cache 为 FP8，或某个全局量化开关非空，就推断这两个 Linear 也应采用同一方案。

## 适用场景与数据流

- 工程入口为 `KimiSparseMoeBlock.__init__()` 中 latent down/up 两个 `ReplicatedLinear` 的 `quant_config` 选择，后续由 `CompressedTensorsConfig` 解析每层实际方法。
- down 投影把 `config.hidden_size` 映射为 `config.routed_expert_hidden_size`；up 投影把 routed expert 的输出映回原 hidden size。两者的量化与 routed expert GMM 的量化要独立核对。
- 目标范围为昇腾 950PR/DT 的这版 K3 量化构造契约。具体 CANN/torch_npu 组合、真实 checkpoint 加载与端到端精度仍须目标环境验收。
- 本卡给出配置判别与构造诊断，不把门控不通过当成修改 checkpoint、扩大容差或强行启用量化的理由；也不扩展到整层 MLA 的独立量化规则。

## 两阶段门控，不能合并成一个开关

第一阶段先从 `target_scheme_map["Linear"]` 读取候选规则，决定是否允许把原 quant config 交给 latent Linear。缺省为 `None`，不是缺省沿用专家量化。

第二阶段由每个 Linear 使用完整 prefix 解析原配置：先检查 per-layer ignore，再匹配该层实际 target，最终选取 scheme。因此第一阶段通过只是“允许继续解析”，不是“强制每一层都量化”。精确名称或 regex target 的匹配先于模块类名；同类 target 的先后仍按实际匹配器的规则和配置顺序核对，不能自行创造优先级。

### 第一阶段的完整代码单元

以下位于 MoE 构造器内；依赖已经取得的 `config`，并为后面两个 Linear 共同准备候选配置：

```python
expert_hidden = config.routed_expert_hidden_size
quant_config = getattr(config, "quant_config", None)
# K3 latent projections use MXFP8 only when Linear explicitly declares
# that scheme. Otherwise keep the existing floating-point path, even
# when a broad Linear target describes MXFP4 routed experts.
linear_scheme = getattr(quant_config, "target_scheme_map", {}).get("Linear", {})
weight_quant = linear_scheme.get("weights")
input_quant = linear_scheme.get("input_activations")
latent_quant_config = None
if (
    weight_quant is not None
    and input_quant is not None
    and input_quant.type == "float"
    and input_quant.group_size == 32
    and quant_config.is_dynamic_group_w8a8_mxfp8(weight_quant, input_quant)
):
    # Pass the original config so per-layer ignore still takes effect.
    latent_quant_config = quant_config
```

该调用进一步使用公共方法判别动态 group W8/A8 MXFP8。下面保留完整谓词，它依赖配置对象的 `get_weight_block_size()`、`QuantizationStrategy` 和 `MX_BLOCK_K`：

```python
def is_dynamic_group_w8a8_mxfp8(self,
                           weight_quant: BaseModel,
                           input_quant: BaseModel,) -> bool:
    weight_block_size = self.get_weight_block_size(weight_quant)
    is_mxfloat = (weight_block_size is not None and weight_block_size[0] == 1 and
                  weight_block_size[1] == MX_BLOCK_K and weight_quant.type == "float")
    is_w8a8_mxfp8 = (weight_quant.num_bits == 8) and (input_quant.num_bits == 8) and is_mxfloat
    weight_strategy = (
        weight_quant.strategy == QuantizationStrategy.GROUP.value
        or weight_quant.strategy == QuantizationStrategy.BLOCK.value)
    # The strategy of mxfp8 is group
    input_strategy = (input_quant.strategy
                == QuantizationStrategy.GROUP.value)
    satisfied_strategies = input_strategy and weight_strategy
    is_dynamic = not weight_quant.dynamic and input_quant.dynamic

    # Both symmetric and asymmetric input quantization supported.
    # Only symmetric weight quantization supported.
    return is_w8a8_mxfp8 and satisfied_strategies and weight_quant.symmetric and is_dynamic
```

## 逐项解释接受条件

| 对象 | 必须成立的条件 | 常见误读 |
|---|---|---|
| 候选位置 | 显式存在 `target_scheme_map["Linear"]`，其中有 `weights` 与 `input_activations` | 只有 `MoEGMM` 或专家 MXFP4 方案不满足 |
| 权重位宽/类型 | `num_bits=8`，`type="float"` | 不能把 int8 或 MXFP4 当成同一种 MXFP8 |
| 权重量化方式 | `dynamic=False`、`symmetric=True` | 不对称或动态权重不通过该谓词 |
| 权重分组 | `group` 且 `group_size=32`，或 `block` 且解析后为 `[1,32]` | 只看 strategy 名，不看真实块大小，会漏掉不匹配配置 |
| 激活位宽/类型 | `num_bits=8`、`type="float"` | 公共谓词外还存在 K3 构造侧的显式 type 判断 |
| 激活策略 | `dynamic=True`、`strategy="group"`、`group_size=32` | 激活的 group size 检查不能仅靠权重块大小代替 |
| 激活对称性 | 本门控没有额外要求其为对称 | 不应凭经验增加一个实现中不存在的拒绝条件 |

这里的权重 scale 与激活 scale 各司其职：静态权重 scale 是加载契约的一部分，动态激活 scale 在执行时计算。不能因为二者都称 group scale 就交换使用，也不能从 group size 相同推导 weight/scale 布局必定兼容。

## 第二阶段：保留原配置的原因

现有 `get_quant_method()` 先检查 ignore，再进入实际 scheme 解析：

```python
def get_quant_method(
    self,
    layer: torch.nn.Module,
    prefix: str,
) -> Optional["QuantizeMethodBase"]:
    if should_ignore_layer(layer_name=prefix, ignore=self.ignore,
                           fused_mapping=self.packed_modules_mapping):
        return UnquantizedLinearMethod()
    if isinstance(layer, LinearBase):
        scheme = self.get_scheme(layer=layer, layer_name=prefix)
        layer.scheme = scheme
        return CompressedTensorsLinearMethod(self)
    elif isinstance(layer, FusedMoEGMM):
        moe_method = CompressedTensorsMoEGMMMethod.get_moe_method(self, layer)
        return moe_method
    return None
```

如果将第一阶段结果复制成一份“只含 MXFP8”的简化配置，会丢失 ignore、精确名称或 regex target。该实现因此传递原 quant config，让每层保持 checkpoint 的真实规则。实际未被 ignore 的投影若命中不支持的 scheme，也应保留解析错误，而不是默默换成另一个方法。

第二阶段还有独立的 `quant_format` 条件：`_get_scheme_from_parts()` 先调用 `is_activation_quantization_format(self.quant_format)`，格式被接受后才按具体 weight/activation 方案分派。即使 group size、位宽和动态条件都正确，格式不被接受时仍会抛出原始 `NotImplementedError`，不能记成 MXFP8 已启用或成功浮点回退。完整分派方法如下，依赖现有的格式判别器和各 Linear scheme 类：

```python
def _get_scheme_from_parts(
        self,
        layer_name: str,
        weight_quant: BaseModel,
        input_quant: BaseModel) -> "CompressedTensorsScheme":

    if is_activation_quantization_format(self.quant_format):
        if self.is_dynamic_token_w8a8_int8(weight_quant, input_quant):
            return CompressedTensorsW8A8Int8LinearMethod(
                strategy=weight_quant.strategy,
                is_static_input_scheme=False,
                input_symmetric=input_quant.symmetric)
        elif self.is_dynamic_token_w8a8_hifloat8(weight_quant, input_quant):
            return CompressedTensorsW8A8Hif8LinearMethod(
                strategy=weight_quant.strategy,
                is_static_input_scheme=False,
                input_symmetric=input_quant.symmetric)
        elif self.is_dynamic_group_w8a8_mxfp8(weight_quant, input_quant):
            return MxFp8LinearMethod()
        elif self.is_dynamic_group_w8a8_fp8(weight_quant, input_quant):
            weight_block_size = self.get_weight_block_size(weight_quant)
            return Fp8PerTileLinearMethod(self, weight_block_size)
        elif self.is_dynamic_group_w4a4_mxfp4(weight_quant, input_quant):
            return MxFp4LinearMethod()

    raise NotImplementedError(
        "No compressed-tensors compatible scheme was found.")
```

## 构造选择怎样影响实际计算

这两个完整方法说明为什么验收时必须查看最终方法，而不能只读候选配置。它们位于同一 MoE 类，依赖已有投影、RMSNorm 和 `torch_npu`；down 的量化结果与 scale 会传给后续投影，up 则保留归一化语义：

```python
def _routed_expert_down_quant(
    self, hidden_states: torch.Tensor
) -> tuple[torch.Tensor, Optional[torch.Tensor]]:
    """Quantize routed input before the latent down projection."""
    if isinstance(
        self.routed_expert_down_proj.quant_method, UnquantizedLinearMethod
    ):
        return hidden_states, None
    quantized, scale = torch_npu.npu_dynamic_mx_quant(
        hidden_states, dst_type=torch.float8_e4m3fn
    )
    return quantized, scale
```

```python
def _routed_expert_up(self, routed_output: torch.Tensor) -> torch.Tensor:
    if isinstance(self.routed_expert_up_proj.quant_method, UnquantizedLinearMethod):
        routed_output = self.routed_expert_norm(routed_output)
        return self.routed_expert_up_proj(routed_output)

    gamma = self.routed_expert_norm.weight.to(dtype=routed_output.dtype)
    routed_output, routed_scale, _ = torch_npu.npu_rms_norm_dynamic_mx_quant(
        routed_output,
        gamma,
        beta=None,
        epsilon=self.routed_expert_norm.variance_epsilon,
        round_mode="rint",
        dst_type=torch.float8_e4m3fn,
    )
    return self.routed_expert_up_proj(
        routed_output,
        dynamic_scale=routed_scale,
    )
```

未量化的 down 直接使用原输入，up 使用独立 RMSNorm 后再投影；量化分支使用动态 MX 量化，up 通过融合 RMSNorm 与 MX 量化产生输入及 scale。不能为了回退只移除量化调用却遗漏归一化。若更具体的 target 改变了最终 scheme，仍须核对它是否兼容这条运行路径；第一阶段门控没有替每个具体 target 完成运行验收。

## 判别与处置步骤

1. 分开记录专家 GMM、down 投影和 up 投影的完整 prefix，读取它们在 checkpoint 配置中的 target 与 ignore；不要用专家的最终 dtype 代替两个 Linear 的诊断。
2. 查看 `Linear` 候选中 weight/activation 的原始字段和解析结果，按上表逐项判断。配置本身解析失败时先报告该错误；“解析失败”与“可解析但门控拒绝”是不同情况。
3. 门控拒绝时，核对两个 latent Linear 是否确实以 `quant_config=None` 构造，并使用匹配的浮点权重。保持专家原来的量化路线，不能顺便取消专家量化。
4. 门控通过时，保留原配置传递，继续检查每个投影的 ignore 和实际 target。分别记录 `quant_method`、`scheme`、weight dtype、weight_scale 与加载布局；down/up 可能因分层规则得到不同结果，不能只检查其中一个。
5. 确认方法与 checkpoint 的真实内容一致后，才进入原精度验收。浮点构造不代表已正确反量化；量化字节不能简单 `.to(bfloat16)` 冒充浮点权重。

## 验证信号与验收矩阵

本轮已核对 K3 门控、公共谓词、ignore 与 target 的实际解析顺序。以下是应在目标实现上逐例执行的验收，不是本轮已经运行的模型测试：

| 场景 | 本地门控与预期构造结果 |
|---|---|
| `Linear` 完整满足条件，`quant_format` 被接受，投影未 ignore，实际 target 为 MXFP8 | 传原配置；`quant_method=CompressedTensorsLinearMethod`，实际 `scheme=MxFp8LinearMethod` |
| 同样的合法候选，但该投影被 ignore | 第一阶段仍传原配置；第二阶段选择 `UnquantizedLinearMethod` |
| 只有专家 MXFP4 方案，未声明 `Linear`；或缺激活描述 | 保持 `quant_config=None`，采用未量化构造 |
| 配置可解析，但激活 group size 不是 32，或权重非对称 | 本地门控拒绝，投影保持浮点构造 |
| 合法 `Linear` 候选，某投影另有更具体 target | 继续按完整 prefix 解析该 target；记录真正方法或明确的不支持错误，不能只看通用候选 |
| 量化字段满足条件，但 `quant_format` 不被分派器接受 | 保留 `NotImplementedError`；不计为 MXFP8 启用或成功回退 |
| 配置字段本身无法解析 | 保留原始解析错误；不计为成功回退 |

## 设计决策、回退与失效边界

该门控把“专家量化”和“latent Linear 量化”拆开，默认保留原浮点投影，仅在实现明确支持的动态 MXFP8 契约下进入后续解析。这样既避免宽泛 MXFP4 规则误作用，也保留每层 ignore 和精确 target 的决定权。

回退应恢复与 checkpoint 匹配的浮点 down/up 投影，并保留专家原量化方案及路由。不要修改 checkpoint 来强行通过门控，不要只改 dtype 而遗漏 scale/布局，不要把本卡扩展成 MLA 的选路规则。

未决项是目标 checkpoint 下两个投影各自的真实加载结果、原模型精度和性能验收。此处稳定的是配置与构造判别，不包含端到端误差、显存或加速收益的实测承诺。
