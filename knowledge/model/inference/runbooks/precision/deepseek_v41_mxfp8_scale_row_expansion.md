---
type: Runbook
title: FP8块scale转换：按目标行组布局逐字节展开
description: 仅在数据字节编码不变且目标把 32×32 块 scale 改为每行 1×32 组时，按输出行逐字节展开；文件筛选与键名规则仅是 recipes 转换器条件。
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
- DeepSeek V4.1：MXFP8 scale 字节展行
---

# FP8块scale转换：按目标行组布局逐字节展开

## 适用性与框架边界

通用原则：量化格式适配必须同时核对权重逻辑轴、数据字节编码、scale 的覆盖集合和 loader/kernel 消费布局。只有目标覆盖合同改变而数据编码不变时，才可能用字节复制实现转换。

必要条件：本卡具体展行公式仅适用于同一 W[N,K] 的源 scale 覆盖 32×32 块、目标 scale 覆盖每行 1×32 组，并保持 E8M0 字节含义不变的接口。其它块大小、转置、scale 编码或重新量化需求不能直接套用 32 倍展行。

recipes 专属操作：`.scale`/`.weight` 文件键、同 shard 配对、指定 dtype/shape 的筛选、`.weight_scale` 加载别名、config/index 文件名和 total_size 更新都仅属于参考转换/加载器，外部框架不需要采用这些名称或文件组织。

vLLM 读者可沿 model loader → 模型 `load_weights`/参数 weight loader → quant method 与 post-load 转换确认真实格式，再核对选定后端消费的 scale 布局。这只是职责入口，没有证明 vLLM 使用该表示、兼容此转换或已完成接入。

## 现象

Linear 可按逻辑矩阵 Y[T,N]=X[T,K]×W[N,K]ᵀ 理解：T 是 token 行数，K 是输入 hidden 宽度，N 是输出特征数。低精度 W 除了数据字节，还需要 scale 说明每组数据的量级；加载器必须知道一个 scale 覆盖哪些行列。

当源 checkpoint 以二维 32×32 权重块共享一个 E8M0 scale，而目标接口按每行的 32 列一组消费同编码 scale 时，便满足本卡的格式条件。权重数据不变，但原 scale 行要复制到它覆盖的每个输出行。仅把配置里的 weight_block_size 改为 [1,32]，没有让数据满足新布局。

E8M0 scale 还有一个独立风险：它的单字节内容是特定浮点编码。这里 view(uint8) 是取同一存储的位视图，不能用数值 cast 替代；后者把编码当数值转换，不能保证保留原始位。此卡验证的是布局与字节搬运边界，没有实际 E8M0 算术或 NPU 数值验收。

## 适用场景

用于模型量化加载或 checkpoint 转换中的 scale 覆盖不匹配诊断。先在自己的框架确认源/目标的矩阵轴、每个 scale 覆盖的数据元素和字节编码，再判断是否满足本卡 32×32→1×32 的必要条件。未满足条件时，应选择目标接口要求的转换，不直接调用参考 expand_scale。

证据案例是 recipes/CANN Executor 的 V4.1 离线转换器 expand_scale/main 和 scale 装载分支；源码目标 Ascend 950，CANN 运行版本未知。该案例适用粒度 exact_task、路线 recommended_fastpath，仅表示核对其当前格式合同。已有 CPU 一字节代理测试，未读写真实 checkpoint；CPU 代理不等于实际 E8M0 或 NPU 数值验证。

## 判别方法

1. 在自己的框架找到 checkpoint 读取/转换、量化配置选择、参数 scale 装载和实际消费算子。以逻辑矩阵 Y[T,N]=X[T,K]×W[N,K]ᵀ 确认 N/K，不凭物理 tensor shape 推断轴；若存在转置或 packed 布局，先还原其逻辑对应。
2. 写清每个源 scale 与目标 scale 覆盖的 W 元素。若源是 32×32 块且目标是每行 1×32 组，N/K 均整除 32，则输入 S 的 shape 为 [N/32,K/32]，目标 S′ 为 [N,K/32]，精确关系是 S′[32i+r,j] 的原始字节等于 S[i,j]，r=0…31。元素数变为 32 倍；一字节 scale 新增字节为 31×(N/32)×(K/32)。这是满足这些条件时的接口转换，不是 FP8 权重重新量化。
3. 核对原始位和覆盖轴。若数据与 scale 编码不变，W 字节应保持，S′ 的每个输出行应对应同一个逻辑权重行。用位视图保持字节，不能把数值 cast 当成位复制；若目标编码不同，应按目标方法转换，不能套用本卡字节复制结论。
4. 在自己的 loader/quant method/post-load 后检查最终名称映射、dtype、scale 覆盖轴与后端实参，最后验反量化/矩阵数值。若字节重复正确而数值仍错，检查编码、逻辑轴及消费合同，不重复展开来“补救”。

**格式条件教学推演（非 NPU 实测）**：下方 CPU 探针使用两行两列字节。取 W 的逻辑尺寸 N=64、K=64，源 scale 为 2×2，字节行 [1,127]、[2,254]；目标为 64×2，行 0–31 复制第一行、行 32–63 复制第二行。从 4 字节变为 128 字节，新增 124；127/254 只标记位负载，不解释成 E8M0 数值。若重复列或交错行，shape/元素数可能看似合理，却已改变输出行的 scale 归属。逐行字节比对才能判别。

### recipes 参考转换/加载器的专属规则

- **tensor 筛选与同 shard 配对**：该 main 仅处理名称以 .scale 结尾、float8_e8m0fnu、二维的 tensor，且同一 shard 有同 base 的 .weight；后者必须二维 float8_e4m3fn、两轴整除 32，scale 精确匹配 [N/32,K/32]。其它项原样复制。已是 [N,K/32] 的 scale 不命中，跨 shard 的 weight/scale 也不匹配；这些是此转换器的筛选能力，不是格式本身要求同 shard。
- **文件名与大小元数据**：该 main 使用 model.safetensors.index.json、config.json 和 *.safetensors，保留 weight_map；仅当 index.metadata 含 total_size 时增加 grand_added。外部框架按自身文件合同核对全部转换覆盖与字节总量。
- **loader 名称和位视图**：该加载器在 Attention/共享专家分支把 .scale 改为 .weight_scale，并对特定 scale 做 uint8 位视图；Engram wkv 的指定 scale 也做位视图。它不在加载时再复制 32 行，具体命名与分支不适用于所有模型 loader。

复验应记录预期转换集合、实际命中集合、W 与未转换 tensor 的字节不变，以及 scale 新增字节。参考 main 生成输出文件不证明所有预期项都命中。下面命令仅用于 recipes 原仓可选导航：

```bash
rg -n 'expand_scale' models/deepseek_v4_1/utils/convert_model.py
```

## 完整代码

以下仅为 recipes/CANN Executor 的完整源码对照；保留逐块导读用于核验，外部框架无需采用其目录、类名或配置结构。

<details>
<summary>展开 recipes 参考实现：完整代码与逐块导读</summary>

以下保留固定源码中的完整函数或因果块；块外导读说明它们怎样连接。

`expand_scale` 只接收 scale，返回沿第 0 轴重复 BLOCK 次的同 dtype tensor。它不检查权重、不改配置；筛选责任在 main。中间 uint8 视图用于保持字节，repeat_interleave 的 dim=0 正是输出行轴。

```python
def expand_scale(scale: torch.Tensor) -> torch.Tensor:
    """
    Expands a 32x32-block FP8 scale to 1x32-group format by repeating each
    row 32 times along dim 0.

    Args:
    scale (torch.Tensor): Scale tensor of shape (N // 32, K // 32) and
        dtype float8_e8m0fnu.

    Returns:
    torch.Tensor: Expanded scale tensor of shape (N, K // 32).
    """
    return scale.view(torch.uint8).repeat_interleave(BLOCK, dim=0).view(scale.dtype)
```

`main(fp8_path,output_path)` 按 shard 读取 tensor 并写出新 checkpoint。`current_state_dict` 决定权重/scale 能否同 shard 配对，`new_state_dict` 接收展行结果或原 tensor；`grand_trans` 统计命中项，`grand_added` 统计新增一字节元素数。末尾只在存在 total_size 时累加它，并保存配置与原 weight_map。该完整函数没有在本次 CPU 测试执行。

```python
def main(fp8_path, output_path):
    """
    Expands 32x32-block FP8 weights to 1x32-group format and rewrites the quantization config.

    This function reads the checkpoint under fp8_path, expands every F8_E8M0 scale
    of shape (N // 32, K // 32) to shape (N, K // 32) by repeating each scale row 32 times,
    and saves the converted checkpoint to output_path. It also replaces the fp8
    quantization_config of config.json with a compressed-tensors config generated
    via convert_config.py, preserving the nested text_config / vision_config structure.

    Args:
    fp8_path (str): The path to the directory containing the input checkpoint
        shards, model.safetensors.index.json and config.json.
    output_path (str): The path to the directory where the converted checkpoint
        is saved.

    Notes:
    - The function assumes the scales are stored in safetensor files.
    - Routed experts and engram embed (already 1x32) and all bf16/fp32 tensors
      are copied byte-identically.
    """
    os.makedirs(output_path, exist_ok=True)
    model_index_file = os.path.join(fp8_path, "model.safetensors.index.json")
    config_file = os.path.join(fp8_path, "config.json")
    with open(model_index_file, "r") as f:
        model_index = json.load(f)
    with open(config_file, "r") as f:
        config = json.load(f)

    old_quant, new_quant = convert_quantization_config(config)

    grand_trans = 0
    grand_added = 0
    safetensor_files = sorted(glob(os.path.join(fp8_path, "*.safetensors")))
    for safetensor_file in tqdm(safetensor_files):
        file_name = os.path.basename(safetensor_file)
        current_state_dict = load_file(safetensor_file, device="cpu")
        new_state_dict = {}
        for weight_name, weight in current_state_dict.items():
            if (weight_name.endswith(".scale")
                    and weight.dtype == torch.float8_e8m0fnu
                    and weight.dim() == 2):
                base = weight_name[:-len(".scale")]
                weight_key = base + ".weight"
                if weight_key in current_state_dict:
                    w = current_state_dict[weight_key]
                    if (w.dtype == torch.float8_e4m3fn and w.dim() == 2
                            and w.shape[0] % BLOCK == 0 and w.shape[1] % BLOCK == 0
                            and weight.shape[0] == w.shape[0] // BLOCK
                            and weight.shape[1] == w.shape[1] // BLOCK):
                        new_scale = expand_scale(weight)
                        new_state_dict[weight_name] = new_scale
                        grand_trans += 1
                        grand_added += new_scale.numel() - weight.numel()
                        continue
            new_state_dict[weight_name] = weight

        new_safetensor_file = os.path.join(output_path, file_name)
        save_file(new_state_dict, new_safetensor_file, metadata={'format': 'pt'})

    copy_py_json(fp8_path, output_path)

    new_model_index_file = os.path.join(output_path, "model.safetensors.index.json")
    new_config_file = os.path.join(output_path, "config.json")
    metadata = dict(model_index.get("metadata") or {})
    if "total_size" in metadata:
        metadata["total_size"] += grand_added
    with open(new_model_index_file, "w") as f:
        json.dump({"metadata": metadata, "weight_map": model_index["weight_map"]}, f, indent=2)
    with open(new_config_file, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Done. scales expanded: {grand_trans} (+{grand_added / 2**30:.3f}GiB)")
    print(f"output: {output_path}")
```

装载因果块针对 Attention/共享专家把 scale 键改成 weight_scale，再将 scale 做 uint8 位视图；Engram wkv 的特定 scale 也做位视图。它消费离线已展开的字节，不在加载时再复制 32 行。名字匹配与字节表示是两条独立检查。

```python
            if "rotary_emb.inv_freq" in name:
                continue
            if ".ffn.shared_experts." in name or ".attn." in name:
                name = name.replace(".scale", ".weight_scale")
                if name.endswith(".weight_scale"):
                    # Scales are repeated offline; preserve their E8M0 bits when loading.
                    loaded_weight = loaded_weight.view(torch.uint8)
            elif name.endswith(".engram.wkv.scale"):
                loaded_weight = loaded_weight.view(torch.uint8)
```

</details>

## 设计决策

当接口只改变 scale 的覆盖行而不改变数据/scale 编码时，逐字节复制可避免解码→重编码；变换可在离线转换或自身框架受控的加载后处理中完成，应由实际消费合同决定。recipes 选择离线展行，并用严格 dtype/shape 判据排除其它张量及已是行组格式的项；这是分支选择的静态结论，不是完整流程幂等性的运行证明。

## 系统信息

通用入口是 checkpoint 转换、模型 weight loader、量化方法与后端 post-load 布局。recipes 对照的转换与配置更新在 `models/deepseek_v4_1/utils/convert_model.py`，scale 消费分支在 `models/deepseek_v4_1/models/modeling_deepseek.py`；依赖原工程 IO 与 PyTorch dtype 支持。目录、文件名和参数名称只是参考实现导航。

## 预防

为每个目标量化参数保存逻辑 N/K、源/目标 scale 覆盖、编码与实际转换覆盖记录；转换后按字节检查正确行复制和 W 不变，按自身文件合同更新大小元数据。复核 recipes 转换器时，再检查其名称/dtype/shape/同 shard 筛选与 total_size 增量；不能把这些筛选约束作为其它框架必须采用的组织方式。

## 验证信号

固定源码核对确认 expand_scale、main 的筛选/写回，以及 loader 的 scale 位视图分支。（来源平台：源码目标 950；证据等级：artifact_verified。）

已有隔离 CPU 测试以 uint8 与 float8_e4m3fn 作一字节代理，确认行重复 32 次且字节保持；下面内联探针展示 uint8 路径的 shape、重复行和新增 124 字节输出。e4m3fn 是代理 dtype，没有测试 E8M0 算术、实际 E8M0 view、完整 main、safetensors 或 NPU 数值。（来源平台：CPU，源码目标 950；证据等级：tool_observed。）

### 已有 CPU 最小复现

下方为已有 CPU 最小复现，先将 expand_scale 与其依赖放入同一命名空间。payload 的数值只标记字节；该探针直接调用函数，不经过 main 的 E8M0 筛选。随后 text 块保留已有实际输出。

```python
import json
import torch

BLOCK = 32
# uint8 is a one-byte payload proxy; this is not an E8M0 arithmetic test.
payload = torch.tensor([[1, 127], [2, 254]], dtype=torch.uint8)
expanded = expand_scale(payload)
assert list(expanded.shape) == [64, 2]
assert torch.equal(expanded[:32], payload[0].expand(32, 2))
assert torch.equal(expanded[32:], payload[1].expand(32, 2))
print(json.dumps({"shape": list(expanded.shape), "row_copies": 32,
                  "byte_payload_preserved": True,
                  "extra_payload_bytes": expanded.numel() - payload.numel()}))
```

```text
{"shape": [64, 2], "row_copies": 32, "byte_payload_preserved": true, "extra_payload_bytes": 124}
```

## 失效边界

实际 E8M0 的 CPU view 支持依赖 PyTorch 版本，本次未验证，也未安装新依赖。recipes 参考 main 在 weight/scale 不同 shard 时不转换，此限制不表示跨 shard 不能实现同一格式转换；完整流程的输出文件、总量、格式排除与数值均待真实 checkpoint 验收。没有 NPU 推理、编译、实际 E8M0 或模型精度结果；CPU 代理通过只证明该范围内的字节搬运。

## 坏实践

只改配置不改 scale 布局；沿列重复或交错行；用数值 cast 替代位视图；无条件展开已经是行组格式的 scale；把一字节代理通过说成 E8M0/NPU 数值通过。
