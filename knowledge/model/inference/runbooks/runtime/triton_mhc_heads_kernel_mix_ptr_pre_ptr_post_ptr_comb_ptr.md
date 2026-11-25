---
{
  "type": "Runbook",
  "title": "DeepSeek-V4.1-Flash mHC 系数头 Triton 单核化（vLLM-Ascend，decode 热路径）",
  "description": "在 vLLM-Ascend 上以 DP/EP 部署 DeepSeek-V4.1-Flash（HF 参考小算子基线，`V41_PYTORCH_ATTENTION=1` eager 注意力）时，每层 mLSTM-hc（mHC）系数计算（pre/post/comb 三个头 + 20 轮 Sinkhorn 归一化）由约 290 个/层 的小算子组成。",
  "tags": [
    "task.implementation",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:03Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "950"
  ]
}
---

# DeepSeek-V4.1-Flash mHC 系数头 Triton 单核化（vLLM-Ascend，decode 热路径）

## 适用场景

- 平台范围依据：source 0 seq 617、source 1 seq 30的实际环境/设备记录确认本次为Ascend 950；这里不扩展未记录的产品或版本。

在 vLLM-Ascend 上以 DP/EP 部署 DeepSeek-V4.1-Flash（HF 参考小算子基线，`V41_PYTORCH_ATTENTION=1` eager 注意力）时，每层 mLSTM-hc（mHC）系数计算（pre/post/comb 三个头 + 20 轮 Sinkhorn 归一化）由约 290 个/层 的小算子组成，decode 步 host launch 开销显著。本候选把 mHC 系数头合并为单个 CANN Triton kernel（开关 `VLLM_ASCEND_V41_MHC_TRITON=1`，默认关闭），并保留 eager 回退。硬件为 4×Ascend950PR（DP4/EP4/TP1，权重 deepseek_v4_1_hybrid_fp8_mxfp4，compute bf16，`ENFORCE_EAGER=1`，chunked prefill max_num_batched_tokens=256）。

## 触发与观测

- 基线 decode 慢：DP4 quick 基线（16k 输入/32 输出/并发 4）`Median TPOT 296.14 ms / P95 296.17 ms / 吞吐 2.76 tok/s`（source 1 seq 270）；官方 8 请求基线 P95 TPOT 419.3329 ms、吞吐 10.0379 token/s（source 1 seq 1076）。
- 首版 Triton kernel 使用张量切片 `pre[:, 0:4]`，CANN Triton 编译报 `ValueError: unsupported tensor index: <triton.language.core.slice object ...>`（source 0 seq 6）。

## 探针与操作

改写为无切片实现：按 lane 区间分别 `tl.load` 4 宽/16 宽 tile（source 0 seq 10，逐字 kernel 见 mechanism_artifacts）。开关接入 `vllm_ascend/models/deepseek_v41`（`VLLM_ASCEND_V41_MHC_TRITON`），prefill（T=64）自动回退 eager 位精确路径（source 0 seq 52 的 parity 输出）。

## 机制与判别

- Triton(Ascend) 不支持 `tl` 张量切片下标；改用分段 load + `tl.where` 掩码后编译通过并数值对齐。
- 数值：pre/post 与 eager **逐位相等**（max_abs=0）；comb 因 fp32 归约顺序差异 max_abs 1.19e-5（T=1）~4.45e-4（T=4）（source 0 seq 14）；集成后 comb max_abs 3.7e-5、prefill 回退位精确（source 0 seq 52）。
- 算子数：每次系数 pass 设备算子 136→8（约 -94%），每步 kernel 数约 11.6k→1.36k（source 0 seq 276，agent 统计叙述）。
- 端到端 A/B（同日同机连续，DP4/EP4 quick32）：median TPOT 296.14→138.66 ms、吞吐 2.76→4.87 tok/s（source 1 seq 270）。
- 官方 8 请求口径（DP4/EP4，16k in/1k out）：P95 TPOT 233.8755 ms（`native_token_lengths_verified=true`）、吞吐 18.5365 token/s（source 1 seq 270），相对基线 −44.2%/+84.7%（source 1 seq 1076）。
- 可区分解释：收益主要来自 host launch 次数下降（rope 融合等不减少 launch 的改动无收益，见同 trace 的 rope 负结果）；comb 的 4e-4 级数值差未影响精度验收。

## 验证信号

- 单元 parity：`T=1/4 pre/post max_abs=0.000e+00`、comb ≤4.454e-04（source 0 seq 14，tool_observed，单卡 Ascend950PR）。
- DP4/EP4 全量 C-Eval（1346 题，冻结 checker）：micro 79.4948%（1070/1346）/ macro 80.3531%，`status=pass`、`request_errors=0`，服务日志佐证 `world_size=4`、`Local/global number of experts: 96/384`（source 1 seq 743、1068，tool_observed）。
- 另有 DP3/EP3（3 卡）全量 C-Eval：micro 80.3120%/macro 80.9532% pass（source 1 seq 22，单次观测）。

## 适用与失效边界

- 仅验证于 vLLM-Ascend + Ascend950PR + DSv4.1-Flash fp8/mxfp4 权重、`ENFORCE_EAGER=1`、chunk 256 配置；comb 头非逐位一致（Sinkhorn 归一化归约顺序），依赖 C-Eval 级精度验收而非 bit-exact。
- 官方口径重复测量波动大：同一配置 8 小时前后 P95 TPOT 233.88→263.22 ms（+12.6%），与另一配置在同 20 分钟内重测差异 0.2%（source 1 seq 1136/1140），跨时段对比需谨慎。
- prefill 路径走 eager 回退，本 kernel 只加速 decode；T=64 以上未验证 Triton 路径。

## 附：断言存档

- CANN Triton 不支持张量切片下标（pre[:, 0:4] 触发 ValueError: unsupported tensor index），改用分段 tl.load 后 mHC 系数头可单核化
- mHC Triton 与 eager 参考一致性：pre/post max_abs=0（逐位相等）；comb 因 fp32 归约顺序 max_abs 1.19e-5(T=1)~4.45e-4(T=4)；集成后 comb 3.7e-5 且 prefill T=64 回退 eager

```text
@triton.jit\ndef _mhc_heads_kernel(mix_ptr, s_ptr, b_ptr, pre_ptr, post_ptr, comb_ptr, T,\n                      EPS: tl.constexpr, ITERS: tl.constexpr, HC: tl.constexpr):\n    rows = tl.arange(0, 16)\n    rowok = rows < T\n    # ---- pre / post heads: logits are lanes [0, 2*HC) ----\n    c8 = tl.arange(0, 8)\n    m8 = tl.load(mix_ptr + rows[:, None] * (2 * HC + HC * HC) + c8[None, :],\n                 mask=rowok[:, None], other=0.0)\n    s0 = tl.load(s_ptr)\n    s1 = tl.load(s_ptr + 1)\n    b8 = tl.load(b_ptr + c8)\n    sc = m8 * tl.where(c8 < HC, s0, s1)[None, :] + b8[None, :]\n    pre = tl.sigmoid(tl.where(c8 < HC, sc, 0.0)) + EPS\n    pre = tl.where(c8 < HC, pre, 0.0)\n    post = 2.0 * tl.sigmoid(tl.where(c8 >= HC, sc, 0.0))\n    post = tl.where(c8 >= HC, post, 0.0)\n    p4 = tl.arange(0, 4)\n    tl.store(pre_ptr + rows[:, None] * HC + p4[None, :], pre[:, 0:4], mask=rowok[:, None])\n    tl.store(post_ptr + rows[:, None] * HC + p4[None, :], post[:, 0:4], mask=rowok[:, None])\n    # ---- comb head: logits are lanes [2*HC, 2*HC + HC*HC) ----\n    c16 = tl.arange(0, 16)\n    m16 = tl.load(mix_ptr + rows[:, None] * (2 * HC + HC * HC) + 2 * HC + c16[None, :],\n                  mask=rowok[:, None], other=0.0)\n    s2 = tl.load(s_ptr + 2)\n    b16 = tl.load(b_ptr + 2 * HC + c16)\n    logits = m16 * s2 + b16[None, :]\n    mval = tl.max(logits, axis=1)\n    e = tl.exp(logits - mval[:, None])\n    comb = e / tl.sum(e, axis=1)[:, None] + EPS\n    c = tl.reshape(comb, (16, HC, HC))\n    for it in tl.static_range(0, ITERS):\n        if it == 0:\n            c = c / (tl.sum(c, axis=1)[:, None, :] + EPS)\n        else:\n            c = c / (tl.sum(c, axis=2)[:, :, None] + EPS)\n            c = c / (tl.sum(c, axis=1)[:, None, :] + EPS)\n    out = tl.reshape(c, (16, HC * HC))\n    tl.store(comb_ptr + rows[:, None] * (HC * HC) + c16[None, :], out, mask=rowok[:, None])
```
