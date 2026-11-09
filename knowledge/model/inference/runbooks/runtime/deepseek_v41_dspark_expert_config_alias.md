---
type: Runbook
title: recipes专用：DSpark专家配置字段映射
description: 仅适用于 recipes/CANN Executor 的 DSpark 字段适配：核对草稿专家 top-k 别名、缺键优先级及 MoE helper/框架计数两处读取差异。
tags:
- task.debugging
- topic.model_adaptation
- topic.speculative_decoding
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:37:06Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1：DSpark 专家配置别名
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - cann_executor
---

# recipes专用：DSpark专家配置字段映射

## 适用性与框架边界

本卡字段映射与回退规则仅适用于 recipes/CANN Executor 的 DSpark 配置适配。`dspark_num_experts_per_tok` 和 `dspark_n_activated_experts` 不是已核验的 vLLM 公共参数，不应直接加入原生 vLLM 配置。

通用原则：配置兼容需同时确认字段语义、归一化优先级和全部读取点；一处 helper 的回退不证明其它消费者得到相同值。

必要条件：采用下文相同的发布配置、运行时展平过程与草稿层构造，才适用该别名映射和计数选择；模型本身支持的专家数/top-k 还需另验。

recipes 专属操作：`text_config` 展平、缺规范键才补别名、以 layer_id 区分主干/追加层、helper 的零值回退和 proposal 直接赋值均为本参考实现规则。

vLLM 读者应在自己的 model loader/模型配置解析与模型构造中确认 MoE 读取的字段及语义，再检查参数装载和分布式组前提。这里没有同名开关翻译、vLLM 接入或版本兼容验证。

## 现象

token 是分词后的序列元素，hidden 向量是模型在该位置的特征表示。MoE 层对每个 token 的 hidden 向量选择 k 个专家执行计算。专家总数 E 表示可选专家集合大小，top-k 表示每 token 实际激活数；两者影响路由、dispatch 的工作量和返回结果的合并，不能互换。

DSpark 是这里 recipes/CANN Executor 的推测解码草稿实现：它产生候选 token，主模型验证并按接受流程决定可保留部分。主模型与草稿可以有不同的专家总数和 top-k。发布配置的 text_config 用 dspark_num_experts_per_tok 表达草稿 top-k，运行时却读取 dspark_n_activated_experts。若别名未归一化，或只检查某个 MoE helper，草稿层与调度 worker 看到的专家计数可能不同。

当前源码的特殊点是：MoE helper 对缺失/零值有回退，proposal model 暴露给框架的计数却直接取 DSpark 字段。不能根据一处 helper 的回退就认为整个草稿模型都有有效配置。

## 适用场景

仅用于 recipes/CANN Executor 的 V4.1 发布配置归一化及草稿专家计数静态排查，入口为 get_config_dict、get_moe_config 与 proposal 构造。源码目标 Ascend 950，CANN 版本未知；没有真实权重装载或路由执行。适用粒度 exact_task，路线 recommended_fastpath，表示遵守当前字段契约。

可迁移的是检查别名归一化与所有消费者的一致性；具体字段名、层编号与回退规则属于本实现，不能直接套到另一框架。

## 判别方法

在该 recipes 路径中找配置解析/展平入口、MoE 层 router 构造、草稿模型向 worker 公开计数的入口。记录原始字段、归一化结果及两个消费者最终使用的 E/k；不要只看配置文件中的单个键。

以下归一化顺序仅属于 recipes 运行时配置适配，不能套用到其它框架或本仓离线转换器。有两层：先 pop text_config，再用 update 将其字段合入顶层字典，同名项在这一步以 text_config 为准；然后只有规范键 dspark_n_activated_experts **不存在**且发布别名存在时才映射。规范键即使值为 0，也不触发别名覆盖。

**教学推演（非 NPU 实测）**：为便于区分，假设主模型 top-k=4、发布草稿别名=2。以下都指 text_config 展平之后：

| 规范字段状态 | 归一化得到的草稿字段 | 追加草稿层的 MoE helper | proposal 框架计数 |
|---|---|---|---|
| 规范键缺失、别名为 2 | 2 | 2 | 2 |
| 规范键为 3、别名为 2 | 3 | 3 | 3 |
| 规范键为 0、别名为 2 | 0 | 回退到主模型 4 | 直接读到 0 |

第三行说明“键存在”和“值可用”不同，回退也只发生在 helper 内。它是读代码推演，不是可用部署配置；应提供有效草稿元数据并复查两个消费者，而不是依赖回退掩盖缺项。专家总数 dspark_n_routed_experts 也有同样的 helper/框架直接读取差别。

再核对层的角色：layer_id<num_hidden_layers 的主干始终取主模型 E/k；追加层才取草稿值并按 helper 规则回退。若字段正确但主/草稿选错，转查层编号与构造调用；若两个入口都一致，再继续核对专家权重覆盖、router 的选择数、EP/TP 分片整除及实际路由输出。复验应同时观察草稿层和 worker 的 E/k，不能只让配置解析无异常就结束。以下仅是 recipes 原仓可选导航：

```bash
rg -n 'get_config_dict' models/deepseek_v4_1/models/configuration_deepseek.py
```

## 完整代码

以下仅为 recipes/CANN Executor 的完整源码对照；保留逐块导读用于核验，外部框架无需采用其目录、类名或配置结构。

<details>
<summary>展开 recipes 参考实现：完整代码与逐块导读</summary>

以下保留固定源码中的完整函数或因果块；块外导读说明它们怎样连接。

`get_config_dict` 接受发布配置，返回展平/规范化的 config_dict 与剩余 kwargs。本卡关注 text_config 的 update 和 DSpark 条件别名；其它 rope、源层、视觉字段分支是同一完整函数的背景，不能把运行时展平行为误认为离线量化转换器也会展平。

```python
    @classmethod
    def get_config_dict(cls, pretrained_model_name_or_path, **kwargs):
        config_dict, kwargs = super().get_config_dict(pretrained_model_name_or_path, **kwargs)
        # The released V4.1 checkpoint stores language-model fields under
        # ``text_config``.  The CANN model consumes a flat config, so normalize
        # the upstream names before constructing this config object.
        text_config = config_dict.pop("text_config", {})
        config_dict.update(text_config)
        rope_scaling = config_dict.get("rope_scaling")
        if rope_scaling:
            rope_scaling = dict(rope_scaling)
            if "rope_type" not in rope_scaling and "type" in rope_scaling:
                rope_scaling["rope_type"] = rope_scaling["type"]
            if (
                "original_max_position_embeddings" not in rope_scaling
                and "origin_max_position_embeddings" in rope_scaling
            ):
                rope_scaling["original_max_position_embeddings"] = rope_scaling[
                    "origin_max_position_embeddings"
                ]
            config_dict["rope_scaling"] = rope_scaling
        if "kv_source_layers" not in config_dict and "kv_source_layer_ids" in config_dict:
            config_dict["kv_source_layers"] = config_dict["kv_source_layer_ids"]
        if "index_source_layers" not in config_dict and "index_source_layer_ids" in config_dict:
            config_dict["index_source_layers"] = config_dict["index_source_layer_ids"]
        if (
            "candidate_source_layer" not in config_dict
            and "candidate_source_layer_id" in config_dict
        ):
            config_dict["candidate_source_layer"] = config_dict[
                "candidate_source_layer_id"
            ]
        if "engram_pad_id" not in config_dict and "engram_pad_token_id" in config_dict:
            config_dict["engram_pad_id"] = config_dict["engram_pad_token_id"]
        if (
            "dspark_n_activated_experts" not in config_dict
            and "dspark_num_experts_per_tok" in config_dict
        ):
            config_dict["dspark_n_activated_experts"] = config_dict[
                "dspark_num_experts_per_tok"
            ]

        # Flatten vision fields and prefix their names with vision_.  HF renamed
        # max_num_tokens to max_image_tokens in the V4.1 release.
        vision_config = config_dict.pop("vision_config", None)
        if vision_config:
            max_image_tokens = vision_config.get(
                "max_num_tokens", vision_config.get("max_image_tokens")
            )
            if max_image_tokens is None:
                raise ValueError(
                    "vision_config must define max_image_tokens "
                    "(or legacy max_num_tokens)"
                )
            config_dict.update(
                vision_n_layers=vision_config["num_hidden_layers"],
                vision_dim=vision_config["hidden_size"],
                vision_n_heads=vision_config["num_attention_heads"],
                vision_inter_dim=vision_config["intermediate_size"],
                vision_patch_size=vision_config["patch_size"],
                vision_rope_theta=vision_config.get("rope_theta", 10000.0),
                vision_downsample_ratio=vision_config["downsample_ratio"],
                vision_max_n_token=max_image_tokens,
                vision_min_pixels=vision_config["min_pixels"],
                vision_max_wh_ratio=vision_config.get("max_wh_ratio"),
            )
        return config_dict, kwargs
```

`get_moe_config(layer_id)` 返回 (专家总数, 每 token 激活数)。`main_routed/main_top_k` 是主模型计数；追加层将 DSpark 值转为整数，随后用 or 回退。该方法只返回两个数，不校验权重、路由合法性或其它消费者。

```python
    def get_moe_config(self, layer_id: int) -> tuple[int, int]:
        """Return routed and activated expert counts for a model layer.

        The target backbone uses the regular MoE configuration. Proposal
        layers appended after ``num_hidden_layers`` use the optional DSpark
        configuration and fall back to the backbone values when it is unset.
        """
        main_routed = int(self.config.n_routed_experts)
        main_top_k = int(self.config.num_experts_per_tok)
        if layer_id < self.config.num_hidden_layers:
            return main_routed, main_top_k

        dspark_routed = int(getattr(self.config, "dspark_n_routed_experts", 0) or 0)
        dspark_top_k = int(getattr(self.config, "dspark_n_activated_experts", 0) or 0)
        return dspark_routed or main_routed, dspark_top_k or main_top_k
```

proposal 构造块将 self.top_k、self.num_experts_per_tok、self.num_experts 直接赋成 DSpark 字段，向框架公开。这段没有 helper 的 or 回退，因此是复验一致性时必须单独查看的消费点。

```python
        self.mtp = self.model.layers
        self.kv_cache = self.model.kv_cache
        self.lm_head = None
        self.top_k = config.dspark_n_activated_experts
        self.num_experts_per_tok = config.dspark_n_activated_experts
        self.num_experts = config.dspark_n_routed_experts
```

</details>

## 设计决策

该 recipes 别名只补缺键，保留显式规范值；主干与草稿分开读专家规模。配置兼容不负责专家权重存在性、top-k 合法性或并行整除；这些还需要对应装载和路由入口检查。

## 系统信息

配置入口在 `models/deepseek_v4_1/models/configuration_deepseek.py`；层级选择在 `models/deepseek_v4_1/models/modeling_deepseek.py`；框架计数在 `models/deepseek_v4_1/models/modeling_dspark.py`。三者必须作为同一条配置生产—消费链阅读。

## 预防

保留一份展平后配置，并逐项对照主干 E/k、草稿 E/k 和 worker 暴露计数。覆盖规范键与别名同时存在但不相等、规范值为零、嵌套与顶层同名的检查情形；这些检查计划不构成本卡已执行测试。

## 验证信号

固定源码核对确认配置别名的缺键条件、主干/追加层的计数选择，以及 proposal 框架计数的直接赋值。没有本卡的 CPU guard/路由测试或 NPU 执行结果。（来源平台：源码目标 950；证据等级：artifact_verified。）

## 失效边界

字段缺失或为零时，两处消费者行为不同，真实草稿配置必须另行验收。未验证 malformed bool/string 值、专家权重覆盖、EP/TP 整除或真实路由输出；没有 NPU 推理、真实 checkpoint 装载和通信结果。只读源码不能证明草稿配置可运行；本卡两个 DSpark 字段及其映射不构成 vLLM 公共配置合同。

## 坏实践

让发布别名无条件覆盖规范值；用主模型 top-k 推断草稿 top-k；看到 helper 回退就忽略框架计数为零；把配置字段兼容当作专家权重与路由精度通过。
