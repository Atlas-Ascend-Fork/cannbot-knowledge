---
type: Runbook
title: 权重键名不匹配：核对参数对象与实际加载覆盖
description: checkpoint 键名不匹配时，沿自身模型的参数 identity、weight loader 分派与实际加载覆盖核对；DSpark 替换表和 required 清单仅是 recipes 案例。
tags:
- task.debugging
- topic.checkpointing
- topic.speculative_decoding
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:37:06Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1：DSpark 权重别名与加载门禁
---

# 权重键名不匹配：核对参数对象与实际加载覆盖

## 适用性与框架边界

通用原则：checkpoint 名称、模块注册键、实际 Parameter 对象和“已经加载”的记录不是同一件事。别名适配应保持目标对象 identity，并证明必需参数确实经过正确 weight loader 写入；只看到新键或非空加载集合不足以验收。

必要条件：先确认自身框架如何登记/去重共享参数、checkpoint tensor 由谁映射与分派、量化/分片何时处理，以及模型定义的必需/可共享/可选参数。具体覆盖集合应来自自己的模型 schema。

recipes 专属操作：`model.layers`/`layers`→`mtp`、Markov/路由/共享专家键名替换、setdefault 冲突策略、HC/Markov/Confidence/Sink required 清单和缺项豁免仅属于 DSpark 参考加载器；不能把这些字段或模块结构要求加给其它框架。

vLLM 读者应沿 model loader → 具体模型 `load_weights` → 参数 weight loader/quant method → post-load 与加载完成检查定位职责，分别核对名字、对象、分片和覆盖。这里只映射职责，没有验证 vLLM 使用该 DSpark schema、同名配置或版本兼容。

## 现象

模型权重文件的键名与内存模块的注册路径属于两个命名空间。相同 Parameter 可以被不同属性引用；PyTorch named_parameters 的去重与遍历顺序会影响暴露哪条注册路径。加载器若拿注册名直接查 checkpoint 名，可能找不到本应对应的 tensor；反过来，映射后的键存在也可能写入错误对象或错误分片。

诊断时应保留完整链条：checkpoint tensor → 名称映射 → 参数对象 → 专属加载器 → 最终加载覆盖。共享对象的别名可以只加载一次，但应由模型/加载器合同明确其所有者与覆盖计数，不能仅按字符串数量判断成功。

recipes/CANN Executor 的 DSpark 案例展示了这种错位：构造将 decoder 挂到 self.model，再让 self.mtp 引用同一组 layers；checkpoint 使用 mtp.<stage>，而参数遍历可能先暴露 model.layers.<stage>。adapter 生成指向原 Parameter 的键名视图，加载器再记录命中键并做一般覆盖与关键集合检查。本卡记录这些检查，不是一次真实 checkpoint 装载成功。

该参考草稿还含不同职责的头与层参数：采集 L 个主模型目标层、hidden 宽 H 时，main_proj 把 L×H 拼接特征映为 H 宽草稿输入；Markov 把 token ID 映成 R 维向量再投到 V 维词表修正；Confidence 把 H 维 hidden 与 R 维 Markov 向量拼接后投成每步一个分数。它们轴与 owner 不同，不能因处于同一 stage 就共用加载假设；其它模型未必具有这些头。

## 适用场景

用于 checkpoint 名称与模型参数登记不一致、共享参数别名冲突或加载结束仍缺必需参数的诊断。主线从自身模型注册、实际 Parameter identity、loader 分派与覆盖合同出发；具体名称映射与必需清单由目标模型确定。

证据案例是 recipes/CANN Executor 当前 V4.1 DSpark 的 adapt_safetensors_field_dspark、proposal 构造/load_weights 与 _validate_dspark_loaded_weights；源码目标 Ascend 950，CANN 版本未知。该案例适用粒度 exact_task、路线 recommended_fastpath，表示按它自己的 schema 查漏装。已有隔离 CPU 别名/集合检查，没有真实模型 named_parameters 遍历、safetensors 装载或 NPU 推理。

## 判别方法

1. 在自己的框架找到模型参数登记/遍历、checkpoint tensor 迭代、名称适配、weight_loader 分派和加载完成检查。为一条关键权重保留“注册原名→适配名→checkpoint 键→实际 Parameter 对象→实际 loader 写入/加载记录”，再覆盖模型定义的全部必需参数。
2. 检查共享对象与冲突：适配前后预期别名是否仍指向同一 Parameter；多个原名若映到同一个键，是否确为共享对象，冲突策略是否明确。若映到不同对象，先定位注册/别名冲突，不能依赖遍历顺序静默择一。
3. 检查实际 loader：命名命中后，tensor 是否进入正确的普通/stacked/expert/量化分支，其 dtype、逻辑轴、shard_id/expert_id 是否对应目标参数。Attention head/组分片、词表列分片和专家矩阵分片需各自检查；scale 位视图也不能替代格式检查。
4. 对账实际加载覆盖：按自身模型 schema 区分必需、共享和明确可选项，核对每个必需对象是否被正确加载，以及 post-load 后表示是否完整。名字齐全不证明写入轴或数值正确；随后才在真实 checkpoint 上验分片、数值与模型输出。若键已齐全而输出异常，转查实际 tensor/执行，不继续扩大字符串替换范围。

### recipes DSpark 参考加载器的具体规则

以下映射表、冲突策略和 required 清单只属于该参考实现，不能作为其它模型的命名或模块要求。

| recipes 当前注册/内部名 | recipes checkpoint 名职责 | 本案例应检查什么 |
|---|---|---|
| layers.<stage> 或 model.layers.<stage> | mtp.<stage> 草稿 stage | stage 为草稿层序号，不能误换成主模型层号 |
| markov_head.markov_w1 / markov_w2 | markov_head.embed / head | token ID 的低秩向量与词表修正分别装载 |
| tid2eid / e_score_correction_bias | gate.tid2eid / bias | token 到专家映射与路由修正，不是普通 Linear |
| shared_experts.down_proj | shared_experts.w2 | 共享专家输出投影的专属命名适配 |

**参考案例教学推演（非 NPU 实测）**：已有 CPU 探针把两个不同对象依次放入字典。先来的 model.layers.0.markov_head.markov_w1.weight 改成 mtp.0.markov_head.embed.weight；后来的同名 checkpoint 路径因 setdefault 不覆盖已有项，结果仍指向先来的 alias 对象。调换顺序，保留对象也调换。因此本 adapter 是“首次插入值保留”，不是“canonical 名称总优先”。真实共享引用若原本为同一 Parameter，映射不复制权重；若冲突项指向不同对象，应先调查冲突。

**参考前缀缺口**：dspark_model.layers.0 没有直接改成 mtp.0 的分支；replace("model.","",1) 反而得到 dspark_layers.0。注释提到该前缀不代表代码支持，不能扩展兼容声明。

**参考覆盖门禁**：该 load_weights 先处理 scale 位视图，再做 stacked/expert/普通参数分派；结束时比较 params_dict 的未加载键，并检查草稿 required。smooth_scale/w2_alpha 一类一般缺项可告警继续，required 不因此豁免。这个豁免与检查顺序只是本加载器合同。

**参考 required 清单及职责**：清单包含 stage 0 的 main_proj/main_norm，最终 stage 的 norm/HC/Markov embed 与 head/Confidence projection，以及每 stage 的 attn_sink。HC 参数控制多路残差流混合：hc_attn_* 服务 Attention 前后，hc_ffn_* 服务 FFN 前后；hc_pre 准备子层输入及混合系数，hc_post 把子层输出合回残差流。本卡只检查参数键/对象，没有验证残差混合数值。只补 Markov 而缺 Confidence/Sink，该门禁仍拒绝；外部模型应按自己实际具有的模块定义必需集合。

复验先在自身模型构造后导出真实注册键、identity、checkpoint 清单和加载记录，再核对专属 loader 的轴/量化处理；CPU 字典 probe 不替代真实模型遍历。下面命令仅用于 recipes 原仓可选导航：

```bash
rg -n 'adapt_safetensors_field_dspark' models/deepseek_v4_1/models/modeling_dspark.py
```

## 完整代码

以下仅为 recipes/CANN Executor 的完整源码对照；保留逐块导读用于核验，外部框架无需采用其目录、类名或配置结构。

<details>
<summary>展开 recipes 参考实现：完整代码与逐块导读</summary>

以下保留固定源码中的完整函数或因果块；块外导读说明它们怎样连接。

`adapt_safetensors_field_dspark` 输入“注册名→Parameter”字典，输出“checkpoint 名→同一个 Parameter”的视图。`k` 在前缀和 replacements 两步中变化，`v` 从不复制；`fix_dict.setdefault` 只保留当前迭代第一个碰到该键的对象。函数注释中的意图必须以这段实际条件为准。

```python
def adapt_safetensors_field_dspark(params_dict: Dict):
    """Build a checkpoint-name view of DSpark's registered parameters.

    DSpark checkpoints expose ``mtp.<stage>``.  Depending on registration order
    PyTorch reports the same parameters as ``dspark_model.layers.<stage>`` (or
    through the inherited ``model.`` prefix).  Keep the actual Parameter values
    while returning aliases in the checkpoint namespace.
    """
    fix_dict = {}
    for k, v in params_dict.items():
        if k.startswith("layers."):
            k = "mtp." + k[len("layers."):]
        elif k.startswith("model.layers."):
            k = "mtp." + k[len("model.layers."):]
        elif "model." in k and not k.startswith("model."):
            k = k.replace("model.", "", 1)

        replacements = (
            ("tid2eid", "gate.tid2eid"),
            ("e_score_correction_bias", "bias"),
            ("shared_experts.down_proj", "shared_experts.w2"),
            ("markov_head.markov_w1", "markov_head.embed"),
            ("markov_head.markov_w2", "markov_head.head"),
        )
        for old, new in replacements:
            k = k.replace(old, new)
        # Avoid overwriting a canonical alias when the module is reachable via
        # both ``mtp`` and ``dspark_model`` registration paths.
        fix_dict.setdefault(k, v)
    return fix_dict
```

`_validate_dspark_loaded_weights` 输入已记录加载键的集合。`last_stage_idx=层数-1` 用于最终头/归一化，required_params 再补每 stage 的 sink；missing_required 是集合差，非空即抛明确异常。该检查没有读取 tensor 内容，因此不能验证数值或 shard 轴。

```python
    def _validate_dspark_loaded_weights(self, loaded_params: Set[str]):
        last_stage_idx = self.dspark_num_layers - 1
        required_params = {
            "mtp.0.main_proj.weight",
            "mtp.0.main_norm.weight",
            f"mtp.{last_stage_idx}.norm.weight",
            f"mtp.{last_stage_idx}.hc_attn_fn",
            f"mtp.{last_stage_idx}.hc_attn_base",
            f"mtp.{last_stage_idx}.hc_attn_scale",
            f"mtp.{last_stage_idx}.hc_ffn_fn",
            f"mtp.{last_stage_idx}.hc_ffn_base",
            f"mtp.{last_stage_idx}.hc_ffn_scale",
            f"mtp.{last_stage_idx}.markov_head.embed.weight",
            f"mtp.{last_stage_idx}.markov_head.head.weight",
            f"mtp.{last_stage_idx}.confidence_head.proj.weight",
        }
        required_params.update(
            f"mtp.{stage_idx}.attn.attn_sink" for stage_idx in range(self.dspark_num_layers)
        )
        missing_required = sorted(required_params - loaded_params)
        if missing_required:
            raise ValueError(
                f"DSpark speculative decoding required weights missing from checkpoint load: {missing_required}"
            )
```

proposal 构造先建立 self.model，再将 self.mtp 指向 model.layers，解释同一对象为何可能出现不同可达路径。ignore_share_weight、lm_head=None 与专家计数是草稿构造上下文；mtp 名称是公开 schema/内部复用名，不等于原生 MTP backend。

```python
    def __init__(self, config: DeepseekV41Config, infer_config: InferenceConfig, **kwargs):
        super().__init__(config, infer_config, comm_manager=kwargs.get("comm_manager"), is_mtp=True)
        self.dspark_block_size = config.dspark_block_size
        self.dspark_target_layer_ids = config.dspark_target_layer_ids
        self.dspark_noise_token_id = config.dspark_noise_token_id
        self.dspark_markov_rank = config.dspark_markov_rank
        self.dspark_num_layers = config.n_mtp_layers
        self.ignore_share_weight = True

        self.compiled_forward_spec_decode = None

        dspark_kwargs = {
            **kwargs,
            "global_rank": self.global_rank,
            "is_mtp": True,
            "comm_manager": self.comm_manager,
        }
        self.model = DeepseekV41DSparkModel(
            config, infer_config, **dspark_kwargs,
        )
        self.mtp = self.model.layers
        self.kv_cache = self.model.kv_cache
        self.lm_head = None
        self.top_k = config.dspark_n_activated_experts
        self.num_experts_per_tok = config.dspark_n_activated_experts
        self.num_experts = config.dspark_n_routed_experts
```

`load_weights` 是完整加载链。输入是 (checkpoint 名,tensor) 的迭代器，输出 loaded_params 集合；params_dict 是别名视图。前部先处理 scale 键与位视图，再按 stacked_params_mapping 合并权重、按 expert_params_mapping 装入专家，最后处理普通参数。`shard_id/expert_id` 是 loader 的分片身份；`dequant_cache` 暂存 wo_a 的 weight/scale 对，齐备后才反量化。末尾 weights_not_loaded 比较全部别名键，随后 required 门禁补强关键集合。看懂这几个中间量，才能区分“键没命中”“分派错”“scale/轴错”和“缺关键头”。

```python
    def load_weights(self, weights: Iterable[Tuple[str, torch.Tensor]]) -> Set[str]:
        """Load DSpark stage weights and adapt checkpoint tensor layouts."""
        stacked_params_mapping, expert_params_mapping = self._load_weight_map()
        # The model owns the layers below ``dspark_model.layers`` while the
        # checkpoint intentionally uses the public ``mtp.<stage>`` namespace.
        # adapt_safetensors_field_dspark returns that public namespace as keys.
        params_dict = adapt_safetensors_field_dspark(dict(self.named_parameters()))
        loaded_params: Set[str] = set()
        dequant_cache = {}
        is_replace_expert_scale_name = any("w13_weight_scale" in key for key in params_dict)

        for name, loaded_weight in weights:
            if "rotary_emb.inv_freq" in name:
                continue
            if ".ffn.shared_experts." in name or ".attn." in name or "main_proj." in name:
                name = name.replace(".scale", ".weight_scale")
                if name.endswith(".weight_scale"):
                    # Scales are repeated offline; preserve their E8M0 bits when loading.
                    loaded_weight = loaded_weight.view(torch.uint8)
            elif name.endswith(".engram.wkv.scale"):
                loaded_weight = loaded_weight.view(torch.uint8)

            for (param_name, weight_name, shard_id) in stacked_params_mapping:
                # Skip non-stacked layers and experts (experts handled below).
                if weight_name not in name:
                    continue
                # We have mlp.experts[0].gate_proj in the checkpoint.
                # Since we handle the experts below in expert_params_mapping,
                # we need to skip here BEFORE we update the name, otherwise
                # name will be updated to mlp.experts[0].gate_up_proj, which
                # will then be updated below in expert_params_mapping
                # for mlp.experts[0].gate_gate_up_proj, which breaks load.
                if (("ffn.experts." in name) and name not in params_dict):
                    continue
                name = name.replace(weight_name, param_name)
                if name.endswith(".bias") and name not in params_dict:
                    continue
                if self.config.quant_config.mm_quant_mode != "w8a8float8":
                    name = name.replace(".scale", ".weight_scale")

                if name not in params_dict:
                    continue
                param = params_dict[name]
                weight_loader = param.weight_loader
                weight_loader(param, loaded_weight, shard_id)
                break
            else:
                for mapping in expert_params_mapping:
                    param_name, weight_name, expert_id, shard_id = mapping
                    if weight_name not in name:
                        continue
                    name = name.replace(weight_name, param_name)
                    if is_replace_expert_scale_name:
                        name = name.replace("w13_scale", "w13_weight_scale").replace("w2_scale", "w2_weight_scale")

                    if name not in params_dict:
                        continue
                    is_gmm_w4mxfloat = ("w4" in self.config.quant_config.gmm_quant_mode and
                                        "mxfloat" in self.config.quant_config.gmm_quant_mode)
                    if is_gmm_w4mxfloat:
                        loaded_weight = loaded_weight.view(torch.uint8)
                    param = params_dict[name]
                    weight_loader = param.weight_loader
                    weight_loader(param,
                                    loaded_weight,
                                    name,
                                    shard_id=shard_id,
                                    expert_id=expert_id)
                    break
                else:
                    # The npu_transpose_batchmatmul op doesn't support the fp8 data type. The weight of wo_a needs
                    # to be converted to bf16.
                    if "wo_a" in name and self.config.quant_config.mm_quant_mode == "w8a8float8":
                        base_name, attr = name.rsplit(".", 1)
                        if base_name not in dequant_cache:
                            dequant_cache[base_name] = {}
                        dequant_cache[base_name][attr] = loaded_weight
                        if "weight" in dequant_cache[base_name] and "scale" in dequant_cache[base_name]:
                            data = dequant_cache.pop(base_name)
                            q_weight = data["weight"]
                            scale = data["scale"]
                            loaded_weight = weight_dequant(q_weight, scale)
                            name = f"{base_name}.weight"

                    if name.endswith(".bias") and name not in params_dict:
                        continue

                    if self.config.quant_config.mm_quant_mode != "w8a8float8":
                        name = name.replace(".scale", ".weight_scale")

                    if name not in params_dict:
                        continue
                    param = params_dict[name]
                    weight_loader = getattr(param, "weight_loader",
                                            default_weight_loader)
                    weight_loader(param, loaded_weight)
            loaded_params.add(name)

        # add checkpoint load check
        weights_not_loaded = set(params_dict.keys()) - loaded_params
        key_weights = {"smooth_scale", "w2_alpha"}
        if weights_not_loaded:
            if all(any(key in name for key in key_weights) for name in weights_not_loaded):
                logger.warning(
                    "Smooth scales were not initialized from checkpoint.")
            else:
                raise ValueError(
                    "Following weights were not initialized from "
                    f"checkpoint: {weights_not_loaded}")
        self._validate_dspark_loaded_weights(loaded_params)
        return loaded_params
```

</details>

## 设计决策

当目标只是名字适配时，用保留 Parameter identity 的视图可避免复制参数或重建模块树，但映射冲突仍需明确处理。覆盖检查应符合实际共享/可选参数合同，关键参数清单则由模型定义，二者均不等于完整数值验证。

recipes DSpark 选择 setdefault 的首次插入策略、一般漏装检查加显式 required 门禁；它的前缀缺口和冲突顺序都应明示，不靠注释中的“canonical”意图扩大支持。其它框架无需采用相同策略或 required 名单。

## 系统信息

通用定位入口是 model loader、具体模型 load_weights、参数专属 weight loader、quant method/post-load 与覆盖检查。recipes DSpark 的完整对照集中于 `models/deepseek_v4_1/models/modeling_dspark.py`，还依赖原工程映射表、量化配置和参数专属 loader；该路径只用于参考实现导航。

## 预防

真实模型构造后导出注册键与对象 identity，名称适配后检查碰撞、共享引用和 checkpoint 匹配，再按模型合同核对实际加载覆盖与专属 loader。模型树、注册顺序或量化方法变化后重新验证，不能只保留字符串单测。复核 recipes 案例时，还须单独检查其 required 清单与未支持前缀。

## 验证信号

固定源码核对确认别名、关键集合门禁、proposal 注册路径和完整加载器实现。（来源平台：源码目标 950；证据等级：artifact_verified。）

已有隔离 CPU 检查确认对象 identity、首次插入保留、dspark_model.layers 不映射到 mtp，以及缺 Confidence/Sink 的关键集合被拒绝。下面保留的内联探针具体展示前两类名称/冲突行为；没有真实模型遍历或 checkpoint 装载。（来源平台：CPU，源码目标 950；证据等级：tool_observed。）

### 已有 CPU 最小复现

下方为已有 CPU 最小复现，先将 adapter 及其依赖放入同一命名空间。两个 object() 用于区分对象身份；它不建立真正模型或加载 tensor。text 块是已有实际输出，不代表草稿推理通过。

```python
import json

canonical, alias = object(), object()
mapped = adapt_safetensors_field_dspark({
    "model.layers.0.markov_head.markov_w1.weight": alias,
    "mtp.0.markov_head.embed.weight": canonical,
})
assert mapped["mtp.0.markov_head.embed.weight"] is alias
unsupported = adapt_safetensors_field_dspark({
    "dspark_model.layers.0.markov_head.markov_w1.weight": alias,
})
assert unsupported["dspark_layers.0.markov_head.embed.weight"] is alias
assert not any(name.startswith("mtp.") for name in unsupported)
print(json.dumps({"first_insertion_preserved": True,
                  "canonical_always_wins": False,
                  "dspark_model_prefix_mapped_to_mtp": False}))
```

```text
{"first_insertion_preserved": true, "canonical_always_wins": false, "dspark_model_prefix_mapped_to_mtp": false}
```

## 失效边界

recipes DSpark 当前 self.model 注册路径可由显式分支映射，dspark_model.layers 前缀不被正确支持；不能将注释意图扩大为实现兼容性。真实 checkpoint 字段、named_parameters 顺序、全量参数覆盖、scale shape 和权重分片仍待实际装载核对。没有 NPU 推理或提案/接受流程的数值验收，CPU 字典/集合检查只覆盖其测试输入。

## 坏实践

把 setdefault 说成 canonical 始终优先；用字符串替换后键存在来代替对象 identity 与轴检查；忽略不支持前缀；删掉 required 门禁来让缺头权重继续；把加载键集合非空当作完整权重验收。
