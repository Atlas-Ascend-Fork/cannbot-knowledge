---
type: Runbook
title: Kimi K3 投影融合后量化 ignore 失效：按 checkpoint 的未融合名称匹配
description: 排查 gate_up_proj、qkv_proj 与 checkpoint 的 gate/up、q/k/v 命名映射，保留分层 ignore
  语义；来源后续把修复收敛到 K3 构造侧。
tags:
- task.debugging
- topic.precision
- topic.compilation
status: stable
sources: []
created_at: '2026-10-30T03:17:20Z'
updated_at: '2026-10-30T09:01:39Z'
platforms:
- '950'
---

# Kimi K3 投影融合后量化 ignore 失效：按 checkpoint 的未融合名称匹配

## 现象

在昇腾 950PR/DT 的 Kimi K3 compressed-tensors 路线中，checkpoint 已把某些未融合投影列入 `ignore`，模型实际构造的融合 Linear 却仍得到量化方法。仅查看配置文件的 ignore 字符串会误以为配置已生效；关键是配置如何被传到创建 `gate_up_proj`、`qkv_proj` 的位置，以及该位置使用什么名字匹配。

例如 checkpoint 可以分别记录 `gate_proj` 与 `up_proj`，运行时却将两者包装成 `gate_up_proj`。把融合名字直接与未融合的 ignore 列表比较，会漏掉应保持浮点的矩阵。q/k/v 合并成 qkv 时也有同类命名边界。

## 适用场景与定位入口

- 工程形态：K3 的融合 Linear 构造与量化配置解析，不是事后对已加载权重做 dtype cast。
- 相关入口：`KimiMLP` 的 gate/up 融合、KDA 模块的 qkv 融合、模型本地 `_fused_linear_quant_config()`，以及 compressed-tensors 的 `should_ignore_layer()`。
- 目标平台为 950PR/DT；具体 CANN/torch_npu 版本和端到端精度不在本轮验证范围内。本卡的稳定内容是命名、配置传递与构造路径诊断。
- 不适用于任意名称相似的矩阵，也不允许忽略 checkpoint 的分层配置，强制把所有融合权重设为浮点或量化。

## 先把三个名称空间对齐

| 名称空间 | 例子 | 作用 |
|---|---|---|
| checkpoint 原始投影名 | `gate_proj`、`up_proj`；`q_proj/k_proj/v_proj` | ignore 和分层量化意图可能按这些名保存 |
| 运行模块名 | `gate_up_proj`、`qkv_proj` | `Linear` 构造拿到的实际 prefix |
| 融合映射 | `gate_up_proj -> [gate_proj, up_proj]` | 将运行模块还原成各 shard 名后逐个匹配 |

必须保留完整层级 prefix。`model.layers.0...` 的排除规则不能因只拿末段 `gate_proj` 比较而扩散到其他层；regex 也要按匹配器支持的 `re:` 语义核对，不能当作普通子串查找。

## 完整判别与构造单元

模型本地 helper 如下。只有 `CompressedTensorsConfig` 才走该判断；被 ignore 时返回 `None`，否则把原配置传下去，以保留其余 target/scheme 行为：

```python
def _fused_linear_quant_config(quant_config, prefix):
    """Resolve checkpoint shard ignore entries for a K3 fused Linear."""
    if isinstance(quant_config, CompressedTensorsConfig) and should_ignore_layer(
        layer_name=prefix,
        ignore=quant_config.ignore,
        fused_mapping=quant_config.packed_modules_mapping,
    ):
        return None
    return quant_config
```

gate/up 构造侧必须先登记映射，再用同一融合 prefix 做判断和构造。以下是完整的映射与构造因果单元；位于 `KimiMLP.__init__()`，依赖该构造器已有的维度与 TP 参数：

```python
intermediate_size = intermediate_size or config.intermediate_size
quant_config = getattr(config, "quant_config", None)
if quant_config is not None:
    quant_config.packed_modules_mapping["gate_up_proj"] = ["gate_proj", "up_proj"]
# Gate first, then up, matching SituAndMul's chunk order.
self.gate_up_proj = MergedColumnParallelLinear(
    hidden_size,
    [intermediate_size] * 2,
    bias=False,
    tp_size=tp_size,
    tp_rank=tp_rank,
    quant_config=_fused_linear_quant_config(quant_config, f"{prefix}.gate_up_proj"),
    prefix=f"{prefix}.gate_up_proj",
)
```

`should_ignore_layer` 的完整判断值得保留，因为“只要一个 shard 命中就整层忽略”与实际契约不同。该函数依赖模块内已导入的类型与 `check_equal_or_regex_match`：

```python
def should_ignore_layer(
    layer_name: Optional[str],
    ignore: Iterable[str] = tuple(),
    fused_mapping: Mapping[str, list[str]] = MappingProxyType({})
) -> bool:
    if layer_name is None:
        return False

    # layer_name = model.layers.0.self_attn.qkv_proj
    # proj_name = qkv_proj
    proj_name = layer_name.split(".")[-1]

    # Fused layers like gate_up_proj or qkv_proj will not be fused
    # in the safetensors checkpoint. So, we convert the name
    # from the fused version to unfused + check to make sure that
    # each shard of the fused layer has the same scheme.
    if proj_name in fused_mapping and layer_name not in ignore:
        shard_proj_names = fused_mapping[proj_name]

        # Convert fused_name --> [shard_names]
        shard_names = [
            layer_name.replace(proj_name, shard_proj_name)
            for shard_proj_name in shard_proj_names
        ]

        # Layer should be ignored if shards are ignored.
        ignore_layer = None
        for shard_name in shard_names:
            should_ignore_shard = check_equal_or_regex_match(
                layer_name=shard_name, targets=ignore)

            # If shard_idx=0, set layer ignore to match shard.
            if ignore_layer is None:
                ignore_layer = should_ignore_shard

            # If shard_idx=1+ confirm scheme matches prior shards.
            elif should_ignore_shard != ignore_layer:
                raise ValueError(f"Found a different quantization schemes for "
                                 f"{shard_proj_names} in {layer_name}. vLLM "
                                 "requires all to use the same scheme.")

    # Unfused layers like down_proj and o_proj will match
    # the safetensors checkpoint already.
    else:
        ignore_layer = check_equal_or_regex_match(layer_name=layer_name,
                                                         targets=ignore)

    if ignore_layer is None:
        raise ValueError("ignore_layer must be True or False, but now is None")
    return ignore_layer
```

它对融合 shard 逐个匹配：全部命中则忽略，全部不命中则继续量化流程；如果不同 shard 的 ignore 结果不同，抛出错误。直接列出完整融合层名的 ignore 则按直接匹配路径处理。

## 排查与处置步骤

1. 记录 checkpoint 的完整 ignore、`packed_modules_mapping`、融合模块 prefix，以及最终 Linear 类型。保留模型层号与模块层级，不只截图一个开关。
2. 确认当前代码由谁处理融合 ignore：有的版本在公共 `CompressedTensorsConfig.get_quant_method()` 传入映射；模型本地方案则由上述 helper 在构造时返回 `None`。先跟实际调用链，不要求这两个位置同时重复适配。
3. 对 `gate_up_proj` 检查两个 shard，对 `qkv_proj` 检查三个 shard。映射顺序还应符合实际融合矩阵的拼接顺序；修 ignore 不能顺便改变权重布局。
4. 若匹配结果为“全部排除”，确认构造的实际 Linear 得到未量化路径；若“全部未排除”，确认保留原 quant config 并解析该层应有 scheme。不要仅从配置传入非空推断最后一定量化。
5. 若部分 shard 排除、部分未排除，按现有 matcher 明确报错并保留配置。先处理 checkpoint 与融合后端能力的矛盾，不能擅自量化整个矩阵或忽略整个融合层。
6. 在修正配置传递后，用同一 checkpoint 重新加载并记录该层 `quant_method`、如存在的 `scheme`、weight dtype 和布局，再运行原精度验收。

## 设计决策

模型本地 helper 把 K3 特有的融合命名适配限制在构造处，避免为了单个模型改变公共配置对象对其他模型的默认行为。返回原 quant config 而不重新拼一份简化配置，是为了保留原有 target、每层规则和后续解析约束。

映射只解决名称转换。它不证明融合矩阵的所有 shard 能支持不同量化方案；当前判断要求 ignore 一致，错误信息应该保留下来作为不兼容配置的信号。

## 验证信号与验收矩阵

本轮已核对 helper、映射登记、融合构造和 matcher 的实际代码。未执行模型精度测试，以下是部署时必须验证的行为，不是本轮运行通过的结果：

| 配置情形 | 应观察到的行为 |
|---|---|
| 融合层所有 shard 都在 ignore | 整个融合 Linear 采用未量化构造；其余层规则保持原意 |
| 所有 shard 都不在 ignore | 原 quant config 保留，再根据该层 target 解析实际 scheme |
| 仅部分 shard 命中 ignore | 构造/解析明确失败，不能静默选择其中一种方案 |
| 仅某一层被排除 | 只有对应完整 prefix 的层改变，其余层不被误排除 |
| 直接列出完整融合层名 | 按直接 ignore 规则命中，不依赖未融合名字列表补猜 |

验收时需同时检查 `quant_method` 与真正的 `scheme`，并确认加载的权重与浮点/量化路线匹配。构造结果正确后仍须跑原模型精度验收；它不能替代张量内容和输出验证。

## 坏实践、回退与失效边界

不要把最后一段投影名当完整 prefix；不要把部分 shard 不一致当作整层任选浮点或量化的许可；不要给融合矩阵随意做数值 cast；不要同时在公共和模型本地重复加规则却不核对调用顺序。

回退时成套恢复模型本地融合构造及对应映射，保留 checkpoint 配置。若部署版本的公共实现已支持融合匹配，应复核是否还需要本地 helper，避免重复覆盖。一般加载布局规则见 [量化权重布局与命名](../../optimizations/rules/quant_weight_load_layout_and_naming.md)。本卡不处理部分 shard 混合量化的新后端能力，也不提供端到端精度或性能承诺。
