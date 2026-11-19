---
type: API
title: npu_qkv_rms_norm_rope_cache 与 rope_quant_kvcache 家族：QKV 融合写入与量化 KV Cache 写读
description: 区分 QKV 三分支融合写入（RMSNorm+RoPE+PA_NZ 量化缓存）与 rope_quant/dequant_rope_quant 的量化缓存写读往返，保留原地/functional 返回差异、scale 方向冲突与用例 skip 状态。
tags:
- task.lookup
- topic.kv_cache
- topic.compute.quantization
- topic.attention
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QkvRmsNormRopeCacheNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RopeQuantKVCacheKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DequantRopeQuantKVCacheKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_qkv_rms_norm_rope_cache.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_rope_quant_kvcache.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QkvRmsNormRopeCacheNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RopeQuantKVCacheKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DequantRopeQuantKVCacheKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
created_at: '2026-11-12T04:21:27Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# npu_qkv_rms_norm_rope_cache 与 rope_quant_kvcache 家族：QKV 融合写入与量化 KV Cache 写读

## 版本与范围

本卡依据 OpPlugin 主线候选固定提交与同代发布固定提交，两 pin 中三个实现文件与相关 yaml/meta 登记为注释剔除后 token 等价（仅排版差异）。OpPlugin 仓库没有这组接口的官方 API 文档页，schema 以 `op_plugin_functions.yaml` 登记为准；其中 qkv 变体标注 `op_api: [v2.6, newest]`，rope_quant 二元组标注 `op_api: all_version`。主线候选的软件配套尚未确认，不能据此推定任一发布组合支持这组接口。

## npu_qkv_rms_norm_rope_cache(+functional)：QKV 三分支融合写入

接口声明（yaml 登记）：

```text
torch_npu.npu_qkv_rms_norm_rope_cache(qkv, q_gamma, k_gamma, cos, sin, index, q_out, k_cache, v_cache,
    qkv_size, head_nums, *, k_scale=None, v_scale=None, k_offset=None, v_offset=None,
    epsilon=1e-6, cache_mode='PA_NZ', is_output_qkv=False) -> (Tensor, Tensor, Tensor)
```

对 QKV 投影输出一次性完成三分支处理，host 端通过 `EXEC_NPU_NO_FORMAT_CHECK_CMD` 直接下发 `aclnnQkvRmsNormRopeCache`：

- **q 分支**：RMSNorm（`q_gamma`，`epsilon`）后全维 RoPE（cos/sin），结果写入原地参数 `q_out`；
- **k 分支**：RMSNorm（`k_gamma`）+ RoPE 后，若提供 `k_scale/k_offset` 则量化（官方 golden 为 `out/scale (+offset)` 后 round 截断到 `[-128, 127]`）写入 k_cache；
- **v 分支**：不做 norm 与 RoPE，直接按 `v_scale/v_offset` 量化写入 v_cache；
- 返回值 `(q_out_before_quant, k_out_before_quant, v_out_before_quant)` 是量化前的中间结果，仅 `is_output_qkv=True` 时分配有效（形状 `(B*S, N*D)`，dtype 同 qkv）；`is_output_qkv=False` 时运行时把三个返回值赋为默认构造的 `at::Tensor()`——未定义（undefined）张量对象，不是已分配的空张量，不要对其做形状或元素数假设。

布局与参数边界按实际生效路径分层：

- 运行时 C++ host 检查（`prepare_before_quant`）只有三项：`qkv_size` 长度必须为 4 `[B, S, N, D]`、`head_nums` 长度必须为 3 `[Nq, Nk, Nv]`、`qkv` 必须是 2D `(B*S, (Nq+Nk+Nv)*D)`；违反在 host 直接报错。
- `q_gamma/k_gamma` 1D、`cos/sin` 2D `(B*S, D)` 是 **Meta-only** 检查（FakeTensor/导出追踪路径的 Python 校验），运行时 C++ host 路径不做这两组 rank 校验。
- cache 布局与 index 行为是参考性约定（来自官方 golden/用例，不是本地 host 校验）：默认 `cache_mode='PA_NZ'` 下 k_cache/v_cache 为 `(block_num, N*D//32, block_size, 32)`，末维 32 是 NZ 粒度；`index` 为 int64 逐 token 槽位，**负值跳过写入**（padding token）；官方用例用非零占位预填缓存校验只覆盖命中槽位。
- `functional` 变体语义相同，但先 `clone()` 三块原地参数再执行，返回 6 元组（三个 pre-quant 中间 + 三个克隆后的 q_out/k_cache/v_cache），适合不想破坏原缓存的调用方。
- meta 对该入口按 `qkv.dtype` 分配返回三元组；`is_output_qkv=False` 时 Meta 返回三个 `torch.empty([])`——有定义的 rank0（0 维）单元素占位，不是零元素空张量。注意与运行时区分：运行时返回未定义的 `at::Tensor()`，Meta 返回有定义的 rank0 占位，两条路径的输出不是同一对象、定义性也不同，不要把一方的形状约定套到另一方。

## npu_rope_quant_kvcache / npu_dequant_rope_quant_kvcache：量化缓存写读往返

两个入口共用同一设备入口 `aclnnDequantRopeQuantKvcache`：

```text
torch_npu.npu_rope_quant_kvcache(x, cos, sin, k_cache, v_cache, indices, scale_k, scale_v, size_splits,
    *, offset_k=None, offset_v=None, quant_mode=0, input_layout="BSND",
    kv_output=False, cache_mode="contiguous") -> (Tensor, Tensor, Tensor, Tensor, Tensor)
```

- 输入 `x` 为拼接的 qkv 行（2D `(B, Q+K+V)` 或 3D `(B, S, Q+K+V)`），host 按 `size_splits[0]`（q 段宽度）除以 `v_cache.size(3)`（head 维 D）推 `q_headdim`。检查顺序注意：C++ 先执行 `size_splits[0] >= 0`（访问首项）再检查 `size_splits` 长度是否为 3，长度 1-2 且首项非负的输入会通过首项检查、由长度守卫拒绝，空输入则在长度检查之前就越界访问首项（失败形态未定义），不能指望长度守卫先行拒绝；Meta 侧先查长度再访问首项。4D 缓存校验两侧对象不同：C++ host 查 `v_cache_ref.dim() == 4`（上文 `q_headdim` 推导的 head 维即取自 `v_cache_ref.size(3)`）；Meta 共享推导查的是 `k_cache.dim() == 4` 并从 `k_cache` 推 head 维，Meta 不校验 `v_cache` 维度。
- q 段 RoPE 后作为 `q_output` 返回（dtype 同 cos，形状 2D `(B, q_headdim, D)` / 3D `(B, S, q_headdim, D)`）；k 段 RoPE 后、v 段直接，经 `scale_k/scale_v (+offset_k/offset_v)` 量化并按 `indices` scatter 写入 k_cache/v_cache；k_cache/v_cache 原地更新并作为返回元组后两项回传；
- `kv_output=False` 时 k/v 输出为 `{0}` 形状占位；`quant_mode` 仅 `1` 映射为字符串 `"dynamic"`，其余任意整数值（含 0）都落入 `"static"`，host 不做数值 0/1 枚举校验；`cache_mode` 默认 `"contiguous"`；
- `npu_dequant_rope_quant_kvcache` 与之同构，但 host TORCH_CHECK 与 meta `torch._check` 都强制 `x.dtype == Int32`（输入已是量化整数），并额外接受 `weight_scale/activation_scale/bias` 三个可选输入——用于反量化-RoPE-再量化的往返（例如配合量化输出算子把整型中间重新写缓存）。

返回值固定为 `(q_output, k_output, v_output, k_cache, v_cache)` 五元组；meta 对两个入口共用同一推导（校验 x 维度、k_cache 4D、size_splits 长度），`dequant` 分支在共用推导前先做 Int32 检查。

## 与相邻入口的关系

- [npu_kv_rmsnorm_rope_cache](npu_kv_rmsnorm_rope_cache.md) / [npu_kv_rmsnorm_rope_cache_v2](npu_kv_rmsnorm_rope_cache_v2.md)：只处理 KV 两分支（单 gamma，kv 4D），v2 另有 `k_cache_dtype/ckv_cache_dtype` 整型枚举控制缓存 dtype；qkv 变体没有 dtype 枚举参数，量化缓存 dtype 由调用方传入的 cache 张量本身决定。
- torchair 两个固定版本都带有这三个入口的 GE converter，图捕获路径的 lowering 语义见[RoPE Cache lowering](../../guides/optimization/torchair/torchair_ge_rope_cache_lowering.md)；本卡只覆盖 Eager 层 host 行为。
- ATB 侧的分页 KV 写链路（ReshapeAndCache 等）见[ATB KV Cache 写入与分页读取](../../guides/torch_npu_atb_kv_cache_write_and_paged_read_preparation.md)，与本卡 opapi 入口互不替代。
- 设备算子层（aclnnQkvRmsNormRopeCache）的 Host/Launcher 语义见[aclnn qkv_rms_norm_rope_cache](../../../../ops/ascendc/operators/aclnn/transformer/posembedding/qkv_rms_norm_rope_cache.md)。

## 收益与成本

预填充阶段把 QKV 投影后的 norm/rope/量化/缓存写入合并为单设备调用，省去拆分、量化与 scatter 的多次下发和中间张量；量化写路径（INT8 缓存 + per-head scale/offset）把 KV 缓存内存压到 1 字节/token 维，配合后端量化注意力使用。`functional` 变体显式 clone 三个 buffer（q_out/k_cache/v_cache，共三次拷贝与分配申请）；`dequant_rope_quant` 往返的反量化-RoPE-再量化数学与其融合 SDK 入口（`aclnnDequantRopeQuantKvcache`）共享，不能据此推断它带来额外独立 launch。两者仅在需要保原缓存或整型中间回写时使用。

## 失效边界

- 两组官方用例全部带 `@unittest.skip("skip … now")` 装饰器并标注 `SupportedDevices(["Ascend910B"])`：本卡描述基于源码与用例 golden 的静态阅读，未做任何运行验证，不能据用例存在推定该路径已通过 CI。
- **scale 方向（按接口分开描述）**：`aclnnQkvRmsNormRopeCache` 与 `aclnnDequantRopeQuantKvcache` 是两个不同的 SDK 接口，各自 golden 的 scale 参考约定相互独立——qkv 变体 golden 用 `out/scale (+offset)`，rope_quant 二元组 golden 用 `key*scale + offset`。方向相反不构成单一接口的契约冲突，也不存在一个统一的 aclnn scale 方向能同时解决两者；每个接口的真实方向都未经运行验证，采用前必须用实测算子输出分别确认，不要照抄任一 golden。
- `dequant_rope_quant_kvcache` 的 `weight_scale/activation_scale/bias` 分支没有官方用例覆盖（测试只构造了 scale/offset 基础路径），其与 Int32 输入的组合行为未知。
- `npu_qkv_rms_norm_rope_cache` 的 `cache_mode` 除默认 `PA_NZ` 外的取值没有官方用例，host 侧只透传字符串，不枚举校验；`input_layout`（rope_quant 二元组）同理只透传。
- qkv 变体 yaml 标注 `op_api: [v2.6, newest]`：该标注只是本固定源的注册/生成证据，不能据此推断所有更旧版本的 torch_npu 二进制/包普遍缺失此入口；跨版本脚本如需稳健可做存在性探测。rope_quant 二元组为 `all_version` 登记。
