---
{
  "type": "Runbook",
  "title": "五类 torch_npu 融合算子对 FP8 GQA MoE 模型（Ascend950PR/torch_npu 2.12.0）的实测不适配边界",
  "description": "为 Hunyuan-A13B-Instruct-FP8（RoPE→per-head QK RMSNorm 顺序、FP8 E4M3 激活量化、Paged KV cache [blocks,128,8,128] bf16、单卡无 EP）逐一评估候选融合算子并做文档与运行时双重验证，确认五类不适配：npu_rms_norm_quant/npu_add_rms_norm_quant 量化输出仅 INT8（不能做 norm+FP8 融合）；npu_grouped_matmul_finalize_routing weight 仅 int8/int4 且 a8w8 要求 NZ（不支持 FP8）；npu_kv_rmsnorm_rope_cache 语义为 MLA latent 的 RMSNorm→RoPE→写 cache（顺序/对象不符）；npu_scatter_pa_kv_cache 的 PA_ND 模式不被支持、PA_NZ 对该 cache 触发末维 32 Byte 约束错误（None/Norm 可用且与 scatter_nd_update_ 逐位一致）；MC2 dispatch/combine 仅 EP 并行有意义。",
  "tags": [
    "task.debugging",
    "topic.precision",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "950"
  ]
}
---

# 五类 torch_npu 融合算子对 FP8 GQA MoE 模型（Ascend950PR/torch_npu 2.12.0）的实测不适配边界

## 适用场景

- 场景：为 FP8（E4M3 激活）、GQA、RoPE→per-head QK RMSNorm 顺序、Paged KV cache `[blocks, 128, 8, 128]` bf16、单卡无 EP 的 MoE 模型（Hunyuan-A13B-Instruct-FP8）做融合算子选型时，明确哪些候选算子不可用及原因。
- 平台/版本：Ascend950PR_9589，torch_npu 2.12.0，CANN 9.1.0；证据来自本地 `_op_plugin_docs.py` 文档查询 + 设备上运行时探针。
- 目标：把「文档看似可用」与「运行时/语义确实不可用」区分开，避免无效接入。

## 触发与观测

- 触发：阶段 3 融合算子匹配分析要求对每个候选算子给出采用/不适配结论及证据；以下五类候选在文档查询或运行时探针中被客观证据排除。
- 关键运行时失败观测（`npu_scatter_pa_kv_cache`，对 `[8,128,8,128]` bf16 paged cache、slot `arange(21)` 写入探针，逐字）：

```
PA_NZ FAIL RuntimeError('npu_scatter_pa_kv_cache:../third_party/op-plugin/op_plugin/ops/opapi/ScatterPaKvCacheNpuOpApi.cpp:65 NPU function error: call aclnnScatterPaKvCache failed, error code is 561103
[ERROR] 2026-10-10-19:01:23 (PID:4161673, Device:0, RankID:-1) ERR00100 PTA call acl api failed.
[PID: 4161673] 2026-10-10-19:01:23.437.970 Invalid_Argument(EZ0026): Parameter keyCache.lastDimSize of ScatterPaKvCache has incorrect value 256. Reason: the last dim of key cache must be 32 Byte.
        Solution: Check whether the parameter value is correct.
```

  同一探针中 PA_ND 模式同样失败（`Parameter cacheMode of ScatterPaKvCache has incorrect value PA_ND. Reason: cacheMode only support None, Norm or PA_NZ.`）。

## 探针与操作

- PA cache 写探针：固定 `[NB,BS,NH,D]=[8,128,8,128]` bf16 cache，对 `cache_mode in (PA_ND, PA_NZ, None, 'Norm')` 逐一调用并与 `npu_scatter_nd_update_` 参考对齐。
- 文档约束查询：`torch_npu_query.py --docs-path <venv>/torch_npu/_op_plugin_docs.py show <op>` 读取本地算子文档原文。

文档证据原文（逐字）：

`npu_rms_norm_quant` 量化输出约束（来源记录#150）：

```
y: Device侧的Tensor类型。数据类型支持INT8。shape、数据格式需要与入参x保持一致。支持非连续的Tensor，不支持空Tensor。
```

`npu_grouped_matmul_finalize_routing` weight 约束（来源记录#155）：

```
- weight(Tensor, 计算输入): 必选参数，一个3D的Device侧Tensor输入，矩阵计算的右矩阵，不支持非连续的Tensor。数据类型支持int8、int4。a8w8场景下数据格式支持NZ，维度为(e,k,n)，e取值范围为[1, 256]，n取值为32整数倍且大于等于256，a8w4场景下数据格式支持ND，维度为(e,k,n)，k只支持2048，n只支持7168。
```

`npu_kv_rmsnorm_rope_cache` 语义（来源记录#121）：

```
融合 MLA 结构中 RMSNorm + RoPE + ScatterUpdate(KVCache 写入) 三步骤
```

分析结论的工件记录（progress.md §3.5 不适配表，逐字，来源记录#7）：

```
| `npu_kv_rmsnorm_rope_cache(_v2)` | ⛔ 不适配 | 语义为 **RMSNorm→RoPE→cache 写**，面向 MLA latent；本模型是 **RoPE→per-head QK RMSNorm→cache 写**，顺序/对象均不同（阶段 2 已同结论） |
| `npu_rms_norm_quant` / `npu_add_rms_norm_quant` | ⛔ 不适配 | 量化输出**仅支持 INT8**，本模型激活量化是 **FP8 E4M3**，无法用其做「norm+FP8量化」融合 |
| `npu_grouped_matmul_finalize_routing` | ⛔ 不适配 | 文档限定 weight 为 **int8/int4（a8w8/a8w4）且 NZ**，不支持 FP8 |
| `npu_moe_distribute_dispatch_v2` / `combine_v2`（MC2） | ⛔ 不适用 | 单卡、无 EP；仅在 EP 并行时才有意义 |
```

PA cache 写探针的正面对照输出（None/Norm 模式与 `npu_scatter_nd_update_` 参考对齐，逐字，来源记录#167）：

```
None OK err 0.0
Norm OK err 0.0
```


## 机制与判别

- `npu_rms_norm_quant`/`npu_add_rms_norm_quant`：文档明确量化输出仅 INT8；FP8 E4M3 激活量化模型无法用其做「norm+量化」融合——这是硬约束而非实现缺口。
- `npu_grouped_matmul_finalize_routing`：weight dtype 限定 int8/int4，a8w8 还要求 NZ 格式；FP8 权重既不在 dtype 支持内也不满足格式要求。本模型 FP8 专家 GMM 改用非融合链 `npu_grouped_matmul` + `npu_moe_finalize_routing`（见 [FP8(E4M3) npu_grouped_matmul 静态 per-tensor 激活 scale 的接入语义与前置校验](fp8_e4m3_npu_grouped_matmul_per_tensor.md)）。
- `npu_kv_rmsnorm_rope_cache(_v2)`：语义面向 MLA latent 的 RMSNorm→RoPE→写 cache；Hunyuan 是 RoPE→per-head QK RMSNorm→写 cache，顺序与归一化对象都不同，融合会造成语义错误。
- `npu_scatter_pa_kv_cache`：cache_mode 枚举仅 None/Norm/PA_NZ（PA_ND 报 Invalid_Argument）；默认 PA_NZ 对末维 128 元素（bf16，lastDimSize=256 字节）的 cache 触发「the last dim of key cache must be 32 Byte」约束——即该默认模式对常规 `[.., num_kv_heads, head_dim]` 布局不可用；None/'Norm' 模式可用且与 `npu_scatter_nd_update_` 逐位一致（err 0.0）。本模型阶段 2 已用 `npu_scatter_nd_update_` 写 cache，无需替换。
- MC2 dispatch/combine：语义绑定 EP 并行（跨卡 token 派发/聚合），单卡无 EP 场景无意义。
- 未验证推断：`npu_scatter_pa_kv_cache` 末维 32 Byte 约束的精确判读（要求 32 字节或 32 字节对齐）未进一步实验，仅确认该调用组合报错；若 cache 布局改为满足约束的形态（如末维恰为 32 字节倍数/特定压缩布局），PA_NZ 是否可用未验证。

## 验证信号

（平台：Ascend950PR_9589 / torch_npu 2.12.0 / CANN 9.1.0）

- c1：npu_rms_norm_quant / npu_add_rms_norm_quant 的量化输出仅支持 INT8，不能用于 FP8(E4M3) 激活量化的『norm+量化』融合。〔signals：来源记录#150（本地文档原文，y 仅 INT8）〕
- c2：npu_grouped_matmul_finalize_routing 不支持 FP8 权重：文档限定 weight 数据类型为 int8/int4，a8w8 场景还要求 NZ 格式（k 为 16 整倍数、n 为 32 整倍数且 ≥256 等额外约束）。〔signals：来源记录#155（本地文档原文）〕
- c3：npu_scatter_pa_kv_cache 的 cache_mode 仅支持 None/Norm/PA_NZ（传 PA_ND 直接报 Invalid_Argument）；默认 PA_NZ 对 [blocks,128,8,128] bf16 paged cache 触发『keyCache.lastDimSize ... 256 ... the last dim of key cache must be 32 Byte』约束错误；cache_mode=None/'Norm' 可用且与 npu_scatter_nd_update_ 结果逐位一致（err 0.0）。〔signals：来源记录#163（两种模式失败原文）、#167（None/Norm 模式 OK err 0.0）〕
- c4：npu_kv_rmsnorm_rope_cache(_v2) 的语义是 MLA latent 的 RMSNorm→RoPE→ScatterUpdate(KVCache 写入) 三步融合，与 Hunyuan 的 RoPE→per-head QK RMSNorm→写 cache 顺序/对象均不同，不能用于该模型的 KV 写链路融合。〔signals：来源记录#121（文档语义原文）〕
- c5：npu_moe_distribute_dispatch_v2 / npu_moe_distribute_combine_v2（MC2）仅在 EP 并行时有意义，单卡（无 EP）部署不适用。〔signals：来源记录#7（progress.md §3.5 不适配表工件）〕
- 正面对照（避免误伤同类算子）：`npu_quantize` 实测接受 `torch.float8_e4m3fn` 且与 clamp(x/s) 逐位一致（来源记录#171：`npu_quantize fp8 OK torch.float8_e4m3fn 0.0`）；FP8 `npu_grouped_matmul` 可跑通（见 [FP8(E4M3) npu_grouped_matmul 静态 per-tensor 激活 scale 的接入语义与前置校验](fp8_e4m3_npu_grouped_matmul_per_tensor.md)）。即「量化输出仅 INT8」只适用于 *_rms_norm_quant 家族与 grouped_matmul_finalize_routing，不适用于 npu_quantize / npu_grouped_matmul 本体。

## 适用与失效边界

- 适用：同为 FP8 E4M3 激活量化、GQA 非 MLA 结构、Paged KV `[blocks, block_size, num_kv_heads, head_dim]` 布局、单卡部署的模型做融合算子排除清单。
- 版本边界：结论绑定 torch_npu 2.12.0 / CANN 9.1.0 的本地文档与运行时；文档与运行时已证实存在漂移（npu_quantize/npu_grouped_matmul 的 FP8 支持），升级后须重新核对文档与运行时双证据。
- 失效条件变化：若模型改为 MLA latent（RMSNorm→RoPE→cache）或激活量化改为 INT8，`npu_kv_rmsnorm_rope_cache` / `*_rms_norm_quant` 的排除结论可能反转；若部署改为多卡 EP，MC2 需重新评估。
- 停止条件：遇到文档明确 dtype/格式硬约束（如上）时不应尝试强行接入；运行时探针报 Invalid_Argument 类约束错误时以错误原文为准记录边界，不做无依据的 workaround。
