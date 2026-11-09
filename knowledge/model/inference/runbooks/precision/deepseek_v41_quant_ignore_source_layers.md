---
type: Runbook
title: 量化排除列表失效：核对读取点与权重所有者
description: 量化排除规则未生效时，沿自身框架的配置读取链和参数所有权核对；源层列表、嵌套处理与组格式仅是 recipes 转换器对照。
tags:
- task.debugging
- topic.checkpointing
- topic.precision
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:37:06Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1：量化 ignore 的源层映射
---

# 量化排除列表失效：核对读取点与权重所有者

## 适用性与框架边界

通用原则：量化排除列表必须匹配真实参数所有者，并被运行时实际选中的量化配置读取点消费。共享 KV/索引状态的消费层不一定持有生成这些状态的权重；应从自身框架的模型加载与量化方法选择过程核对，而不是先寻找 recipes 文件。

必要条件：先确认所用量化方法支持按模块名排除、名称匹配发生在什么阶段，以及共享/别名参数由谁拥有。本卡不规定其它框架的模块命名、配置嵌套层级或必须保留原表示的模块。

recipes 专属操作：下文 `text_config` 元数据读取、顶层 `quantization_config` 写回、两种源层列表及旧压缩比分支、具体 ignore 名单和 Linear/MoEGMM 组生成都只属于参考转换器；CPU fixture 也只验证该转换器的字典/字符串契约。

vLLM 读者可沿 model loader → 模型配置解析/量化方法选择 → 具体模块参数装载与 post-load 过程定位职责，核对自己的量化配置和模块名匹配规则。这里没有同名字段或目录的等价承诺，也未验证 vLLM 接入或版本兼容。

## 现象

量化权重包含低位宽数据和解释它的元数据：某个 Linear/MoE 模块使用多少位、哪些元素共享 scale、哪些模块保留原有表示。ignore 是按模块名称列出的“不要按该量化方案处理”的名单；它本身不执行矩阵转换，也不证明模型数值正确。

每个 token 的 hidden state 是一行特征向量。Attention 生成查询与 KV（键/值），Indexer 产生稀疏注意力要使用的索引；当模型复用其它源层产生的 KV/索引时，“消费这些状态的层”不一定拥有相应投影权重。症状可能是排除名单里出现不存在的参数名、真正的权重所有者没有被排除，或者配置文件里已经写入规则而运行时仍选择了另一量化方案。

应分开诊断所有权与配置读取链：前者决定规则应指向哪个参数，后者决定规则是否生效。recipes 参考案例同时展示了这两类问题：旧版按 compress_ratio 枚举会选错/漏掉模块；转换器读取嵌套语言模型元数据，却将量化配置写到自己的顶层消费入口。

## 适用场景

用于支持模块级量化排除的模型加载/离线转换诊断。先读取自身框架的模型参数登记和量化方案选择结果，再把预期排除项与实际参数所有者、实际匹配后的方案逐项对账。可迁移的是这个核验顺序，不是 recipes 的配置格式。

证据案例是 V4.1 recipes/CANN Executor 的离线量化转换与装载入口，涉及 generate_ignore_item、convert_quantization_config 和量化组生成器；源码目标 Ascend 950，CANN 运行版本未知。此参考案例的适用粒度 exact_task、路线 recommended_fastpath，表示优先核对其当前转换/读取契约。已有隔离 CPU 配置测试，没有真实权重转换或 NPU 精度测试。

## 判别方法

1. 沿自身框架的配置生产与消费链确认读取点：checkpoint 配置由谁解析，量化方法由谁选择，排除规则在参数登记前还是后匹配。记录运行时真实读到的方案，而不仅比较输出 JSON。若配置内容正确而方案未选中，先修读取链或配置写入位置。
2. 为排除项建立参数所有权对应：从实际模块/参数键名识别权重 owner，区分“持有投影权重”与“复用投影结果”。共享参数还需核对别名是否指向同一对象，以及量化方法最终处理的注册入口，避免按每个消费层重复生成不存在的参数名。
3. 再检查方案与数据的对应关系：A/W 表示激活/权重位宽；共享 scale 的元素粒度与二维块尺寸不是同一概念。排除名单匹配正确只说明规则命中了预期对象，不能替代实际 dtype、scale 覆盖轴、装载与数值检查。

### recipes 参考转换器的具体规则

以下各项只解释该参考转换器，不是其它框架的配置要求。

- **嵌套配置与字段优先级**：`fields=config.get("text_config") or config`，非空 text_config 是元数据来源。kv_source_layers/index_source_layers 各自仅在规范键缺失时使用 *_source_layer_ids；规范键存在但为空，不回退到非空别名。主转换器要求两表均非空，且层数、压缩比列表和长度满足检查。
- **源层列表与具体模块名**：源层分支对每个 Indexer 源层列 weights_proj、compressor.wgate/wkv，对每个 KV 源层列 attn.compressor.wgate/wkv，再加 head 并立即返回。仅两个参数均为 None 时 helper 走旧压缩比分支并追加 mtp.0.head。空列表不是 None，helper 与主转换器的入口前提不同。
- **写入层级与组格式**：该转换器把 quantization_config 写回顶层，供本实现 model_worker/get_quant_config 读取；text_config/vision_config 对象及 model_type 不主动改写。Linear 组 A8/W8，MoEGMM 组 A8/W4 且强制 MX；group_size=32 是共享 scale 粒度，weight_block_size=[1,32] 是每行沿权重输入轴的 32 元素组，不能替代实际字节转换。

**参考案例教学推演（非 NPU 实测）**：下方 CPU fixture 使用四层配置，KV 源层为 1，Indexer 源层为 1、3：后者贡献 2×3=6 个模块名，前者贡献 1×2=2 个，再加 head，共 9 项。层 3 即使压缩比不符合旧规则，仍因持有 Indexer 权重而进入名单；其它消费层不会因此生成重复的本层权重名。若规范 kv_source_layers=[] 而别名非空，主转换器仍退出；不能删 guard 来得到输出文件。

复验先确认自身运行时的每个排除项命中正确参数所有者，并检查目标量化方法的真实选择结果；再验证实际 tensor/scale 的装载与数值。若仅在复核 recipes 参考案例，可用下面命令导航，不要求外部框架具有该目录：

```bash
rg -n 'generate_ignore_item' models/deepseek_v4_1/utils/convert_config.py
```

## 完整代码

以下仅为 recipes/CANN Executor 的完整源码对照；保留逐块导读用于核验，外部框架无需采用其目录、类名或配置结构。

<details>
<summary>展开 recipes 参考实现：完整代码与逐块导读</summary>

以下保留固定源码中的完整函数或因果块；块外导读说明它们怎样连接。

`generate_ignore_item` 输入层数、每层压缩比和可选的两类源层列表，输出模块名字符串列表。前半段按源层所有权生成并 return；后半段才是旧 ratio 分支。各层索引必须落在 [0,num_layers)，名单中的“层号”是权重所有者，不是所有消费者。

```python
def generate_ignore_item(num_layers, compress_ratios, kv_source_layers=None, index_source_layers=None):
    """
    Generate a list of layer names to be ignored during quantization.
    """
    ignore = []
    if num_layers is None or compress_ratios is None:
        raise ValueError("num_hidden_layers and compress_ratios are required")
    if len(compress_ratios) < num_layers:
        raise ValueError(
            f"compress_ratios has {len(compress_ratios)} entries, "
            f"but num_hidden_layers is {num_layers}"
        )
    if kv_source_layers is not None or index_source_layers is not None:
        for i in (index_source_layers or []):
            if i < 0 or i >= num_layers:
                raise ValueError(f"index source layer {i} is out of range")
            ignore.append(f"layers.{i}.attn.indexer.weights_proj")
            ignore.append(f"layers.{i}.attn.indexer.compressor.wgate")
            ignore.append(f"layers.{i}.attn.indexer.compressor.wkv")
        for i in (kv_source_layers or []):
            if i < 0 or i >= num_layers:
                raise ValueError(f"KV source layer {i} is out of range")
            ignore.append(f"layers.{i}.attn.compressor.wgate")
            ignore.append(f"layers.{i}.attn.compressor.wkv")
        ignore.append('head')
        return ignore
    for i in range(0, num_layers):
        ratio = compress_ratios[i]
        if ratio == 4: # model have compress ratios [1, 4, 128]
            ignore.append(f"layers.{i}.attn.indexer.weights_proj")
            ignore.append(f"layers.{i}.attn.indexer.compressor.wgate")
            ignore.append(f"layers.{i}.attn.indexer.compressor.wkv")
            ignore.append(f"layers.{i}.attn.compressor.wgate")
            ignore.append(f"layers.{i}.attn.compressor.wkv")
        if ratio == 128: # model have compress ratios [1, 4, 128]
            ignore.append(f"layers.{i}.attn.compressor.wgate")
            ignore.append(f"layers.{i}.attn.compressor.wkv")
    ignore.append('mtp.0.head')
    ignore.append('head')
    return ignore
```

`convert_quantization_config` 接受整个 checkpoint config，原地写顶层 quantization_config，并返回 (旧量化配置, 新量化配置)。`fields` 仅决定读取元数据的位置，`cache_scheme` 描述几类缓存位宽，`quant_ignore_layers` 是前一个 helper 的结果。两个源层列表都非空是该入口额外施加的条件。

```python
def convert_quantization_config(config):
    """
    Rewrite config['quantization_config'] in place: pop the fp8 quantization_config,
    generate a compressed-tensors config and set it at the top level (where
    model_worker and get_quant_config read it). text_config / vision_config
    are left untouched.
    Returns (old_config, new_config).
    """
    fields = config.get("text_config") or config
    num_layers = fields.get("num_hidden_layers")
    compress_ratios = fields.get("compress_ratios")
    kv_source_layers = fields.get("kv_source_layers", fields.get("kv_source_layer_ids"))
    index_source_layers = fields.get("index_source_layers", fields.get("index_source_layer_ids"))
    if not kv_source_layers or not index_source_layers:
        sys.exit("config.json: kv_source_layers / index_source_layers are required "
                 "to generate the quantization ignore list")
    if num_layers is None or compress_ratios is None:
        sys.exit("config.json: num_hidden_layers / compress_ratios are required")
    if len(compress_ratios) < num_layers:
        sys.exit(
            f"config.json: compress_ratios has {len(compress_ratios)} entries, "
            f"but num_hidden_layers is {num_layers}"
        )
    cache_scheme = {"kv_cache_scheme": {"num_bits": NUM_BITS_8, "type": "float"},
                    "comp_cache_scheme": {"num_bits": NUM_BITS_4, "type": "float"},
                    "li_cache_scheme": {"num_bits": NUM_BITS_4, "type": "float"}}

    old_quant = config.pop("quantization_config", None)

    quant_ignore_layers = generate_ignore_item(num_layers, compress_ratios,
                                               kv_source_layers, index_source_layers)
    quantization_config = generate_quant_config(
        cache_scheme, quant_ignore_layers, w4a8=True, is_mx=True)
    quantization_config["weight_block_size"] = [1, BLOCK]
    config["quantization_config"] = quantization_config
    return old_quant, quantization_config
```

`generate_quant_group` 生成激活/权重的共享 scale 规则。dynamic=True 的输入激活 scale 与 dynamic=False 的权重 scale 属于不同生产阶段；is_mx 决定 group/block 表示，不能把 group_size 与二维块尺寸混为一谈。此函数不接收实际 tensor，也不转换数据。

```python
def generate_quant_group(a_num_bits=8, w_num_bits=8, activation_use_clip=False, is_mx=False):
    input_group_size = None
    weight_group_size = None
    weight_block_size = None
    activation_quant_strategy = "group"
    weight_quant_strategy = "group" if is_mx else "block"
    # 32: 32 elements has same scale element when mxfp for dsv4
    # 128: 128 elements has same scale element when fp for dsv4
    input_group_size = 32 if is_mx else 128
    weight_group_size = 32 if is_mx else None
    weight_block_size = "128x128" if not is_mx else None
    quant_group = {"input_activations": {"actorder": None, "block_structure": None, "dynamic": True,
                                         "group_size": input_group_size, "num_bits": a_num_bits,
                                         "observer": "memoryless", "observer_kwargs": {},
                                         "strategy": activation_quant_strategy, "symmetric": True, "type": "float"},
                   "activation_use_clip": activation_use_clip,
                   "output_activations": None,
                   "weights": {"actorder": None, "block_structure": weight_block_size, "dynamic": False,
                               "group_size": weight_group_size, "num_bits": w_num_bits,
                               "observer": "minmax", "observer_kwargs": {},
                               "strategy": weight_quant_strategy, "symmetric": True, "type": "float"}}
    return quant_group
```

`generate_quant_config` 将前一函数的方案挂到 Linear/MoEGMM 两类目标，并附上 ignore/cache_scheme。w4a8 决定是否加入专家矩阵组；即使外部 is_mx 为假，该 W4 专家组也显式强制 MX。这是配置职责的末端，真正读取与执行在模型装载/算子侧。

```python
def generate_quant_config(cache_scheme, ignores, w4a8=False, is_mx=False):
    """
    Generate a quantization configuration dictionary based on the specified parameters.
    """
    config_groups = {"group_0": {"targets": ["Linear"]}}
    if w4a8:
        config_groups.update({"group_1": {"targets": ["MoEGMM"]}})
    quant_config = {"config_groups": config_groups,
                    "format": "float-quantized",
                    "global_compression_ratio": 1,
                    "ignore": ignores,
                    "quant_method": "compressed-tensors",
                    "quantization_status": "compressed"}
    quant_config.update(cache_scheme)
    quant_config["config_groups"]["group_0"].update(
        generate_quant_group(a_num_bits=NUM_BITS_8, w_num_bits=NUM_BITS_8, is_mx=is_mx)
        )
    if w4a8:
        quant_config["config_groups"]["group_1"].update(
            generate_quant_group(
                a_num_bits=NUM_BITS_8,
                w_num_bits=NUM_BITS_4,
                is_mx=True,  # only support mxfp4 for w4a8 with float type
                )
            )
    return quant_config
```

</details>

## 设计决策

共享状态时，排除规则跟随真实参数所有者；规则的生成、序列化位置和运行时读取属于不同职责。自有框架应按自己的配置合同保留或展平嵌套对象。recipes 选择保留 checkpoint 嵌套结构、把量化配置写到顶层，并保留特定模块的原表示；这些选择不能推导其它框架同名模块也必须忽略。

## 系统信息

通用排查入口是模型配置解析器、量化方法选择器、模块/参数登记与 weight loader/post-load 过程。recipes 对照的 ignore/分组逻辑在 `models/deepseek_v4_1/utils/convert_config.py`，整份配置读写在 `models/deepseek_v4_1/utils/convert_model.py`，其 worker 消费入口是本实现职责。外部框架按职责定位自己的入口。

## 预防

转换前保存配置实际读取点、排除规则的匹配名称空间与参数 owner 对照；转换后同时检查运行时方案选择和实际匹配结果。模型结构或共享关系变化后重做所有权核验。复核 recipes 转换器时，再额外检查规范键/别名优先级、非空条件、顶层写回及原嵌套对象保留。

## 验证信号

固定源码核对覆盖四个完整函数，确认源层分支、输入检查、顶层写回与分组规则。（来源平台：源码目标 950；证据等级：artifact_verified。）

已有隔离 CPU 检查覆盖源层名单、旧 ratio 分支、空表/非法源层/短元数据及顶层写回、嵌套对象保留；下面内联探针输出确认 9 项、无 mtp.0.head、空规范键被拒绝。它没有转换真实权重或验证 NPU 量化数值。（来源平台：CPU，源码目标 950；证据等级：tool_observed。）

### 已有 CPU 最小复现

下方为已有 CPU 最小复现，先把本卡四个完整函数及其依赖放入同一命名空间。它用字典和字符串检查配置契约；NUM_BITS/BLOCK 是该探针依赖，不是模型的性能或 shape 清单。探针后的 text 块是已有实际输出。

```python
import json

NUM_BITS_4, NUM_BITS_8, BLOCK = 4, 8, 32
config = {
    "model_type": "deepseek_v41",
    "text_config": {
        "num_hidden_layers": 4, "compress_ratios": [0, 2, 2, 1],
        "kv_source_layer_ids": [1], "index_source_layer_ids": [1, 3],
    },
    "vision_config": {"hidden_size": 8},
    "quantization_config": {"quant_method": "fp8"},
}
text_object, vision_object = config["text_config"], config["vision_config"]
old, new = convert_quantization_config(config)
assert len(new["ignore"]) == 9 and "mtp.0.head" not in new["ignore"]
assert new["weight_block_size"] == [1, 32]
assert config["text_config"] is text_object and config["vision_config"] is vision_object
assert generate_ignore_item(4, [0, 2, 2, 1], [], []) == ["head"]
text_object["kv_source_layers"] = []
blocked = False
try:
    convert_quantization_config(config)
except SystemExit:
    blocked = True
assert blocked
print(json.dumps({"ignore_count": 9, "mtp_head_ignored": False,
                  "nested_objects_preserved": True, "empty_canonical_blocked": blocked}))
```

```text
{"ignore_count": 9, "mtp_head_ignored": false, "nested_objects_preserved": true, "empty_canonical_blocked": true}
```

## 失效边界

recipes 参考 helper 接受单边或空列表，其主转换器会拒绝任一空列表，不能互换两个入口的前提；其它框架应独立确认自己的规则。未执行真实 checkpoint 转换、权重装载或 NPU 推理；ignore 正确不证明 BF16/MXFP8 dtype、scale 字节、算子支持和模型精度均正确。Attention cache 的内部存储布局不在本卡范围。

## 坏实践

按使用状态的每一层生成并不存在的权重名；把空列表当缺键让别名覆盖；删除必需元数据检查以继续转换；只改 quantization_config 而不验真实权重布局；将 CPU 字典测试说成量化精度通过。
