---
type: Runbook
title: 量化KV缓存读写错配：按字节布局核对接口
description: 量化KV接口诊断：仅当writer/reader的dtype、MX组、BF16 scale与行字节布局匹配时采用本文规则；其他缓存格式先核对自身合同。
tags:
- task.debugging
- topic.kv_cache
- topic.data_movement
- topic.precision
status: draft
sources: []
created_at: '2026-11-02T08:24:24Z'
updated_at: '2026-11-03T01:36:07Z'
platforms:
- '950'
aliases:
- DeepSeek V4.1 窗口cache的dtype与字节视图
---

# 量化KV缓存读写错配：按字节布局核对接口

## 适用性与框架边界

本卡是**接口条件知识**：可直接借鉴的是“分配器、writer 与 reader 对同一字节区必须采用一致表示”。下面的具体修正只适用于文中 `kv_compress_epilog_v2` writer 与 `mixed_quant_sparse_flash_mla` reader 的配套接口；目标算子、版本和行布局未匹配前，不能照搬 FP8 分配或 uint8 view。

MXFP8 组32、MXFP4 分组、BF16 scale、行补齐、二维展平、null block/slot 归一化和 `PA_BBND` 均是该接口及 recipes 适配条件。它们不是 vLLM 或通用 PagedAttention 缓存格式；`view` 重解释也不能用数值 cast 替代。

vLLM 读者应对照实际选中的 **Attention backend、KV cache spec、缓存分配及更新接口**；ModelRunner/metadata builder 提供写入槽时，再追踪请求到物理槽的映射。只有对应表示和消费合同确实一致，才应用下文具体字节预算；没有验证 vLLM 选用这些算子。

## 现象

量化 KV（Key/Value，历史键值）缓存 shape 正确，却在写入时被拒绝，或写后读出的注意力结果异常，应记录同一 storage 的分配、写入和读取解释，而不是只比较 shape。持久缓存与 Prefill 临时缓存若被同一 writer/reader 消费，应分别验证相同的接口条件。

下面以窗口缓存（近期 token）为接口对照。所列 recipes writer 要求 FP8 容器，reader 接收 uint8 字节视图；历史修改把 dtype view 的位置从写入侧移到读取侧。素材没有 profiler 或拷贝日志，因此只能据此诊断接口一致性。

## 适用场景

以下精确规则仅适用于模型缓存分配器、自定义 Torch writer `custom.kv_compress_epilog_v2` 与融合 `mixed_quant_sparse_flash_mla` 的集成；源码目标 950，部署 CANN/torch_npu 版本和 NPU 运行未确认。适用粒度 `same_operator`，路线优先级 `recommended_fastpath` 表示当前代码的选择，仍为静态诊断草稿。这里只覆盖当前模型显式展平后交给 writer 的二维行布局；不能直接外推为 writer 的四维分页布局。

## 根因与判别方法

先从自有接口取得数据编码、scale 编码、分组、行步长与地址单位，建立 allocator→writer→reader 的字节表；任一不匹配就停止套用下列尺寸。针对本文已列接口，先区分数值和容器。这里 MXFP8/MXFP4 指一组浮点数据共享 scale 的量化格式：FP8 数据每值占 1 字节，FP4 每两个值占 1 字节；量化 scale 是 BF16（bfloat16，每个 2 字节）。一行缓存包含数据区、scale 区和对齐字节，整行不能当作一串 FP8 数值参与算术。

| 元数据/张量 | 轴、单位与范围 | 生产者 → 消费者 |
|---|---|---|
| D / `head_dim` | 一条未打包 KV 的通道数；须满足相应量化组整除条件 | 模型配置 → 行宽计算与 writer |
| 窗口行宽 C | `align_up(D+2×(D/32),32)` 字节，MXFP8 数据加每组32值的 BF16 scale | 分配器 → writer / Attention |
| 压缩 KV 行宽 | `align_up(D/2+2×(D/16),32)` 字节；是另一种 MXFP4 契约 | 压缩缓存分配 → 对应读写算子 |
| 模型窗口 Tensor | `[物理块数,S,1,C]`，S 为每块槽数；FP8 容器每元素1字节 | CacheEntry 或 Prefill 临时分配器 → writer |
| writer 的 `x` / `cache` | `x=[写入行数,D]` BF16；cache 展平为 `[总槽数,C]` | KV 投影 → 二维量化写入 |
| `slot_mapping` | 每个 x 行对应的扁平目标槽；`-1` 为不写入，block 0 为 null 保留块 | 缓存管理/元数据归一化 → writer |

**教学推演，非上板观测。** 取 D=64 仅演示字节预算：窗口数据占64字节，两个 BF16 scale 占4字节，对齐后 C=96，余下28字节是对齐空间。相同 D 的压缩 KV 是32字节数据加8字节 scale，再对齐到64字节。二者即使都以单字节 Tensor 存放，也不具有相同的解释方式。若对窗口整行调用 `.to(torch.uint8)`，会按 FP8 数值转换这些字节，连嵌入的 scale 位模式也会被当作 FP8 数值；`view(torch.uint8)` 才表达按原字节重新解释的意图。

当前 C++ 入口规定 `mxfp8_bf16` 配 FP8 cache、group=32，`mxfp4_bf16` 配 uint8 cache及允许的 group。窗口分配满足前者，Attention 再读 byte view。源码能证明参数准备相配，不能单独证明运行中完全没有额外 copy。

## 快速检查

1. 记录自有 Attention backend 的 cache spec、writer/reader 版本及字节布局。先确认是否精确采用本文接口；若不是，应使用自身编码和行宽合同。确认匹配后，再分别检查持久窗口和 Prefill 临时分配器的 dtype、元素字节数、shape、stride 与行宽，两者都须满足该 writer 的 FP8 容器要求。
2. 对已匹配的量化 writer，记录 mode、group、输入 x dtype、slot 数和展平后的行宽。把 D=64 教学例子换成真实 D 按字节重算；dtype 匹配但行宽或 scale 位置不符，仍支持布局问题，应继续查 host tiling 与部署算子 ABI（接口二进制契约）。
3. 跟随同一缓存到 Attention 入口，检查是 byte view 还是数值 cast；检查存储标识、offset、stride 与写后字节。预期重新解释后字节不变，不能靠两种 dtype 都占1字节就判断一致。确认额外 copy 是否发生必须另取 profiler。
4. 按目标后端自己的地址合同检查每个写入行对应的 slot；在本文 recipes 适配中，合法槽指向本请求，null block/无效槽已按当前元数据规则屏蔽；当前 `update_win_kv` 依赖上游归一化，不能只看它本身没有 mask 就补回旧逻辑。
5. 在目标环境逐字节对比合法槽、无效槽与未命中槽，并比较 Attention 读取结果。Meta 校验通过只排除部分入口错误；NPU 写后读取、行布局和拷贝行为仍需分别验收。

## 完整代码

下列 recipes 完整实现用于核对本文证据。按块外导读比较输入、轴与生产消费关系；外部引擎应先完成上面的职责和接口检查。

<details>
<summary>recipes 读写接口对照：分配、字节视图与完整 writer</summary>

### 历史修改前：写入处做dtype view

历史前版把缓存展平成二维，再解释成 `PACKED_KV_COMPUTE_DTYPE` 交给 writer；`valid` 用保留的 null block 范围屏蔽无效槽。此处展示旧 dtype 接口位置，不表示当前仍在此处生成 mask。

```python
    def update_win_kv(self, kv, slot_mapping, cache):
        slots = slot_mapping.reshape(-1).long()
        # Evicted/padded pages use null block 0 as well as slot -1.
        valid = slots >= cache.shape[1]
        torch.ops.custom.kv_compress_epilog_v2(
            cache=cache.view(-1, cache.shape[-1]).view(PACKED_KV_COMPUTE_DTYPE),
            x=kv.view(-1, self.head_dim),
            slot_mapping=slots.masked_fill(~valid, -1),
            quant_group_size=32,
            quant_mode="mxfp8_bf16",
            round_scale=True,
        )
```

### 历史修改后：直接交给writer

历史后版移去写入处的 dtype view，前提是分配端已给出 writer 所需 dtype。单独移除此 view 而不改分配器，不能完成这次迁移。

```python
    def update_win_kv(self, kv, slot_mapping, cache):
        slots = slot_mapping.reshape(-1).long()
        # Evicted/padded pages use null block 0 as well as slot -1.
        valid = slots >= cache.shape[1]
        torch.ops.custom.kv_compress_epilog_v2(
            cache=cache.view(-1, cache.shape[-1]),
            x=kv.view(-1, self.head_dim),
            slot_mapping=slots.masked_fill(~valid, -1),
            quant_group_size=32,
            quant_mode="mxfp8_bf16",
            round_scale=True,
        )
```

### 当前行宽公式

行宽函数返回的是字节预算，也就是单字节容器的尾维长度。`is_compressed` 同时改变数据位宽和 scale 分组，不能只把 D 除以2。

```python
def get_kv_cache_dim(head_dim: int, *, is_compressed: bool = False) -> int:
    data_bytes = head_dim // 2 if is_compressed else head_dim
    quant_group_size = 16 if is_compressed else 32
    # FP8/FP4 data followed by one BF16 scale per quantization group.
    return align_up(data_bytes + 2 * (head_dim // quant_group_size), 32)
```

### 当前临时窗口cache分配dtype

临时窗口缓存通过此函数取得 FP8 容器 dtype；它与持久窗口 CacheEntry 的 dtype 需要配套核对。

```python
    def get_win_kv_cache_dtype(self):
        return PACKED_KV_COMPUTE_DTYPE
```

### 当前prefill全长窗口cache完整分配

Prefill 分配器先按每请求真实长度计算块数，从 block 1 起分配实际块，再为每个 token 生成扁平 slot。返回的三个量是临时 cache、请求到物理块的表以及与 packed token 同序的 slot；额外的 block 0 保留为 null。

```python
    def build_prefill_full_kv_metadata(self, input_ids, actual_seq_lengths_q):
        actual_seq_lengths_q = actual_seq_lengths_q.view(-1)
        block_nums = (actual_seq_lengths_q + self.block_size - 1) // self.block_size
        full_block_num = int(block_nums.sum().item())
        max_block_num_per_batch = int(block_nums.max().item()) if block_nums.numel() > 0 else 0
        bsz = actual_seq_lengths_q.shape[0]

        full_block_table = torch.zeros(
            (bsz, max_block_num_per_batch),
            dtype=torch.int32,
            device=input_ids.device,
        )
        slot_mappings = []
        next_block_id = 1
        for batch_idx, (seq_len, block_num) in enumerate(zip(actual_seq_lengths_q.tolist(), block_nums.tolist())):
            if block_num == 0:
                continue

            block_ids = torch.arange(
                next_block_id,
                next_block_id + block_num,
                dtype=torch.int32,
                device=input_ids.device,
            )
            full_block_table[batch_idx, :block_num] = block_ids

            local_position_ids = torch.arange(
                seq_len,
                dtype=torch.int64,
                device=input_ids.device,
            )
            block_indices = local_position_ids // self.block_size
            position_offsets = local_position_ids % self.block_size
            cur_slot_mapping = block_ids[block_indices].to(position_offsets.dtype) * self.block_size + position_offsets
            slot_mappings.append(cur_slot_mapping.to(torch.int64))
            next_block_id += block_num

        full_slot_mapping = torch.cat(slot_mappings, dim=0) if slot_mappings else torch.empty(
            (0,),
            dtype=torch.int64,
            device=input_ids.device,
        )

        # Temporary full-length Win KV cache used during prefill.
        full_kv_cache = torch.zeros(
            (
                full_block_num + 1,
                self.block_size,
                1,
                self.cache_dim,
            ),
            dtype=self.get_win_kv_cache_dtype(),
            device=input_ids.device,
        )
        return full_kv_cache, full_block_table, full_slot_mapping
```

### 当前窗口量化写入

当前 writer 方法只负责把 KV 和已准备的 slot 送入算子；量化组的实际值与 mode 的合法组合要按入口核对，不能从常量名字猜它采用压缩 KV 的分组。

```python
    def update_win_kv(self, kv, slot_mapping, cache):
        torch.ops.custom.kv_compress_epilog_v2(
            cache=cache.view(-1, cache.shape[-1]),
            x=kv.view(-1, self.head_dim),
            slot_mapping=slot_mapping.view(-1),
            quant_group_size=MXFP4_SCALE_GROUP_SIZE,
            quant_mode="mxfp8_bf16",
            round_scale=True,
        )
```

### 当前Attention使用byte view读取

Attention 参数准备把窗口同一容器解释成 uint8。Q 为查询，ori 为窗口分支，cmp 为压缩历史分支；TND 表示 packed token/头/通道，`PA_BBND` 是此算子规定的分页缓存布局标识。索引、长度与 block table 决定哪些字节可被消费。

```python
    def prepare_fa_kwargs(
        self,
        q: torch.Tensor,
        win_kv: torch.Tensor,
        cmp_kv: Optional[torch.Tensor],
        cmp_sparse_indices: Optional[torch.Tensor],
        attn_metadata: Dict,
        is_prefill: bool,
    ):
        # V4.1 ratio 0 is window-only; ratio 1 still has indexed shared KV.
        has_cmp_kv = self.compress_ratio > 0
        win_key = "full_kv" if is_prefill else "win_kv"
        attn_kwargs = {
            "q": q,
            "ori_kv": win_kv.view(torch.uint8),
            "ori_sparse_indices": attn_metadata["win_sparse_indices"],
            "ori_block_table": attn_metadata["block_table"][win_key],
            "cu_seqlens_q": attn_metadata["cu_seq_lens_q"],
            "seqused_q": None,
            "seqused_ori_kv": attn_metadata["actual_seq_k"],
            "ori_topk_length": attn_metadata["win_topk_length"],
            "sinks": self.attn_sink.detach(),  # The DSL ABI requires a plain Tensor.
            "quant_mode": 1,
            "softmax_scale": self.softmax_scale,
            "layout_q": "TND",
            "layout_kv": "PA_BBND",
            "return_softmax_lse": False,
            "metadata": attn_metadata["kernel_metadata"][f"{self.attention_type}_metadata"],
        }
        if has_cmp_kv:
            # Preserve shared_idx; only the FA input uses zero-based [T, 1, K] indices.
            cmp_sparse_indices = cmp_sparse_indices.reshape(q.shape[0], 1, cmp_sparse_indices.shape[-1])
            cmp_sparse_indices = F.pad(
                cmp_sparse_indices, (0, self.config.index_topk - cmp_sparse_indices.shape[-1]), value=-1)
            ratio_key = str(self.compress_ratio)
            attn_kwargs.update({
                "cmp_kv": cmp_kv,
                "cmp_sparse_indices": cmp_sparse_indices,
                "cmp_block_table": get_cmp_block_table(attn_metadata, self.compress_ratio),
                "seqused_cmp_kv": attn_metadata["compressed_seq_lens"][ratio_key],
            })
            attn_kwargs["cmp_topk_length"] = attn_metadata["cmp_topk_length_by_ratio"][ratio_key]
        return attn_kwargs
```

### writer完整Torch入口与共享校验

按三段阅读这份入口：

1. `NormalizeQuantMode` 接受并归一化模式字符串，拒绝未知模式。
2. `ValidateKvCompressEpilogV2Inputs` 依次检查 cache 的二维/四维形状、x 与 slot 行数和连续性、BF16 输入、量化 group/mode、预留 scale 参数以及 cache dtype；这些检查不覆盖所有上板地址约束。
3. NPU 入口把 mode 转为整型、取 blockStride 后调用 ACLNN；Meta 入口只运行共享校验，不执行写入。两者都通过不等于四维与当前二维布局可互换，实际字节写入仍由部署后端决定。

```cpp
/**
 * Copyright (c) 2026 Huawei Technologies Co., Ltd.
 * This program is free software, you can redistribute it and/or modify it under
 * the terms and conditions of CANN Open Software License Agreement Version 2.0
 * (the "License"). Please refer to the License for details. You may not use
 * this file except in compliance with the License. THIS SOFTWARE IS PROVIDED ON
 * AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY, OR FITNESS
 * FOR A PARTICULAR PURPOSE. See LICENSE in the root of the software repository
 * for the full text of the License.
 */

#include "ops_common.h"
#include <cctype>
#include <string>
#include <torch/library.h>

namespace custom {
using namespace at_npu::native;

namespace {
// 与算子侧 IR/tiling 一致的维度与量化约束常量。
constexpr int64_t KCEV2_CACHE_RANK_2D = 2;
constexpr int64_t KCEV2_CACHE_RANK_4D = 4;
constexpr int64_t KCEV2_CACHE_UNIT_DIM_INDEX = 2;
constexpr int64_t KCEV2_CACHE_LAST_DIM_INDEX = 3;
constexpr int64_t KCEV2_QUANT_GROUP_16 = 16;
constexpr int64_t KCEV2_QUANT_GROUP_32 = 32;

std::string NormalizeQuantMode(const std::string &quantMode) {
  size_t begin = 0;
  size_t end = quantMode.size();
  while (begin < end &&
         std::isspace(static_cast<unsigned char>(quantMode[begin]))) {
    ++begin;
  }
  while (end > begin &&
         std::isspace(static_cast<unsigned char>(quantMode[end - 1]))) {
    --end;
  }

  std::string mode;
  mode.reserve(end - begin);
  for (size_t i = begin; i < end; ++i) {
    mode.push_back(static_cast<char>(
        std::tolower(static_cast<unsigned char>(quantMode[i]))));
  }
  if (mode == "mxfp8_bf16" || mode == "mxfp4_bf16") {
    return mode;
  }
  TORCH_CHECK(false,
              "quant_mode should be one of [mxfp8_bf16, mxfp4_bf16], but got '",
              quantMode, "'");
}

void ValidateKvCompressEpilogV2Inputs(at::Tensor &cache, const at::Tensor &x,
                                      const at::Tensor &slotMapping,
                                      int64_t quantGroupSize,
                                      const std::string &quantMode,
                                      double xScale) {
    TORCH_CHECK(cache.dim() == KCEV2_CACHE_RANK_2D || cache.dim() == KCEV2_CACHE_RANK_4D,
                "cache must be 2D or 4D, but got rank ", cache.dim());
    if (cache.dim() == KCEV2_CACHE_RANK_4D) {
        TORCH_CHECK(cache.size(KCEV2_CACHE_UNIT_DIM_INDEX) == 1,
                    "4D cache dim 2 must be 1, but got ", cache.size(KCEV2_CACHE_UNIT_DIM_INDEX));
        TORCH_CHECK(cache.stride(KCEV2_CACHE_LAST_DIM_INDEX) == 1,
                    "4D cache last dimension must be contiguous, but stride(3)=",
                    cache.stride(KCEV2_CACHE_LAST_DIM_INDEX));
    }
    TORCH_CHECK(x.dim() == KCEV2_CACHE_RANK_2D, "x must be 2D, but got rank ", x.dim());
    TORCH_CHECK(slotMapping.dim() == 1, "slot_mapping must be 1D, but got rank ",
                slotMapping.dim());
    TORCH_CHECK(x.size(0) > 0 && x.size(1) > 0, "x dimensions must be positive");
    TORCH_CHECK(slotMapping.size(0) == x.size(0),
                "slot_mapping length must equal x dim 0, got ",
                slotMapping.size(0), " and ", x.size(0));
    TORCH_CHECK(x.scalar_type() == at::kBFloat16,
                "x dtype must be bfloat16, got ", x.scalar_type());
    TORCH_CHECK(slotMapping.scalar_type() == at::kInt ||
                    slotMapping.scalar_type() == at::kLong,
                "slot_mapping dtype must be int32 or int64, got ",
                slotMapping.scalar_type());
    TORCH_CHECK(x.is_contiguous() && slotMapping.is_contiguous(),
                "x and slot_mapping must be contiguous");
    if (cache.dim() == KCEV2_CACHE_RANK_2D) {
        TORCH_CHECK(cache.is_contiguous(),
                    "2D cache must remain contiguous for the existing layout1 path");
    }
    const bool validModeAndGroup =
        (quantMode == "mxfp8_bf16" && quantGroupSize == KCEV2_QUANT_GROUP_32) ||
        (quantMode == "mxfp4_bf16" &&
         (quantGroupSize == KCEV2_QUANT_GROUP_16 || quantGroupSize == KCEV2_QUANT_GROUP_32));
    TORCH_CHECK(validModeAndGroup,
        "invalid quant_mode and quant_group_size combination: "
        "supported combinations are (mxfp8_bf16, 32), "
        "(mxfp4_bf16, 32), and (mxfp4_bf16, 16), but got ",
        quantMode, " and group size ", quantGroupSize);
    TORCH_CHECK(quantGroupSize != 0 && x.size(1) % quantGroupSize == 0,
        "x last dimension must be divisible by quant_group_size, got d=",
        x.size(1), " and quant_group_size=", quantGroupSize);
  TORCH_CHECK(x.size(1) <= 8192, "x last dimension must not exceed 8192, got ",
              x.size(1));
  TORCH_CHECK(xScale == 1.0, "x_scale is reserved and must be 1.0, got ",
              xScale);

  const bool fp8Cache = cache.scalar_type() == at::ScalarType::Float8_e4m3fn ||
                        cache.scalar_type() == at::ScalarType::Float8_e5m2;
  TORCH_CHECK((quantMode == "mxfp8_bf16" && fp8Cache) ||
                  (quantMode == "mxfp4_bf16" && cache.scalar_type() == at::kByte),
              "cache dtype does not match quant_mode: mxfp8_bf16 requires "
              "float8_e4m3fn/float8_e5m2 and mxfp4_bf16 requires uint8");
}
} // namespace

void KvCompressEpilogV2Npu(at::Tensor &cache, const at::Tensor &x,
                           const at::Tensor &slotMapping,
                           int64_t quantGroupSize, std::string quantMode,
                           bool roundScale, double xScale) {
  const std::string normalizedQuantMode = NormalizeQuantMode(quantMode);
  ValidateKvCompressEpilogV2Inputs(cache, x, slotMapping, quantGroupSize,
                                   normalizedQuantMode, xScale);
  const int64_t quantModeInt = normalizedQuantMode == "mxfp8_bf16" ? 2 : 4;
  const int64_t blockStride = cache.stride(0);
  EXEC_NPU_CMD_V1(aclnnKvCompressEpilogV2, cache, x, slotMapping,
                  quantGroupSize, quantModeInt, roundScale, xScale, blockStride);
}

void KvCompressEpilogV2Meta(at::Tensor &cache, const at::Tensor &x,
                            const at::Tensor &slotMapping,
                            int64_t quantGroupSize, std::string quantMode,
                            bool roundScale, double xScale) {
  const std::string normalizedQuantMode = NormalizeQuantMode(quantMode);
  ValidateKvCompressEpilogV2Inputs(cache, x, slotMapping, quantGroupSize,
                                   normalizedQuantMode, xScale);
}

} // namespace custom

TORCH_LIBRARY_IMPL(custom, PrivateUse1, m) {
  m.impl("kv_compress_epilog_v2", &custom::KvCompressEpilogV2Npu);
}

TORCH_LIBRARY_IMPL(custom, Meta, m) {
  m.impl("kv_compress_epilog_v2", &custom::KvCompressEpilogV2Meta);
}
```

</details>

## 设计决策

以 reader/writer 共同声明的物理表示决定分配类型；类型本身不能替代字节布局校验。对本文匹配接口，持久窗口与临时窗口必须统一分配 dtype；只修一处会使 prefill/decode 走不同契约。压缩 KV 与 Indexer 的量化 scale 类型各不相同：本 writer 的行内 scale 是 BF16，不能把 Indexer 的 E8M0 scale pair 规则迁入这里。当前模型将四维 cache 展平成二维后写入，走 row layout；writer 接受四维 Tensor 时采用另一种 token bundle 地址布局，不能只改 rank 而保留原消费逻辑。本卡据分配—writer—reader链诊断接口一致性，历史dtype修改没有实际TensorMove或修后验收证据，不作为修复成功配方。

## 系统信息

recipes 实现对照需要注册自定义 Torch writer、匹配的 ACLNN 实现和量化融合 MLA。持久窗口由模型 CacheEntry 分配为 FP8；临时全长窗口由 metadata builder 使用相同 dtype 分配；压缩 cache 保持 uint8。

## 部署验收

待验：同一 backing storage 的写入前后逐字节对比，覆盖 slot=-1、null block、合法槽与未命中槽；运行 Meta 的 dtype拒绝用例，再在NPU检查写后读取正确性；profile是否仍有TensorMove。现有测试定义包括dtype不匹配拒绝与逐字节原地更新，本轮没有运行。

## 验证信号

本轮只读取固定 Git 源码并恢复原始 blob 与函数字节。以下是实现的静态核对结果，不是模型/NPU 执行结果；未运行源仓脚本、测试、编译或推理。

- 当前源码中窗口 cache 的分配 dtype 为 FP8，writer 接收该 Tensor，融合 Attention 接收其 uint8 view；压缩 KV 使用uint8，入口校验与这两条调用契约一致。（来源平台：950 源码目标，未上板；证据等级：artifact_verified；范围：源码）
- 已读到 writer 的 Meta dtype 拒绝测试和 eager 原地逐字节比较测试定义；没有相应测试执行输出。（来源平台：950 源码目标，未上板；证据等级：artifact_verified；范围：测试定义）

## 预防

联合检查 allocator dtype、行宽、writer mode/group、reader view 与 slot_mapping；部署升级后先核对算子 ABI，不以Python dtype看起来相容作为通过条件。

## 坏实践

对包含嵌入BF16 scale的整行使用 `.to(uint8)`；把不同cache共用同一scale布局；只改持久cache忽略prefill临时buffer；把提交主题中的TensorMove原因当profiler结论。

## 失效边界

四维writer布局已在源码存在，但文档仍主要描述二维行布局，具体支持以当前C++/tiling为准。模型现有二维writer链路不能直接切四维。没有NPU逐字节结果与copy观测，不能保证部署二进制一致，也不能承诺时延改善。空输入、错误group或cache dtype会被接口拒绝；cache行宽最小值由host tiling检查，Meta接受不代表上板可用。
