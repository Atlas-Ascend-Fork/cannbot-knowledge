---
{
  "type": "Runbook",
  "title": "vLLM-Ascend 新模型接入：混合 page size 的 KV cache 组必须 BLHNC 布局",
  "description": "在 vLLM-Ascend（vLLM v0.29.0 主线 + vllm_ascend，CANN 9.2.0，Ascend）上接入自带多种 KV cache 组、且各组 page size 不同的自定义模型（本例 DeepSeek-V4.1：window cache 与 compress cache 两组，page size 32768 与 65536 字节）。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:03Z",
  "updated_at": "2026-11-20T14:17:03Z",
  "platforms": []
}
---

# vLLM-Ascend 新模型接入：混合 page size 的 KV cache 组必须 BLHNC 布局

## 适用场景

在 vLLM-Ascend（vLLM v0.29.0 主线 + vllm_ascend，CANN 9.2.0，Ascend）上接入自带多种 KV cache 组、且各组 page size 不同的自定义模型（本例 DeepSeek-V4.1：window cache 与 compress cache 两组，page size 32768 与 65536 字节）。默认 LBNHC 布局下引擎在 KV cache 组构建阶段直接失败。

## 触发与观测

- mini checkpoint（8 层小模型、随机权重）拉起 LLM 引擎，模型构建后报：
  `ValueError: KV cache layout LBNHC cannot express this model's mixed page sizes ([32768, 65536]); a backend should declare block-outermost supported layouts (e.g. BLHNC), or set VLLM_KV_CACHE_LAYOUT=BLHNC.`（source 0 seq 352，tool_observed）。

## 探针与操作

- 按报错设置环境变量 `VLLM_KV_CACHE_LAYOUT=BLHNC`（source 0 seq 355-360 的补丁与重启）。

## 机制与判别

- LBNHC 把 block 维放在内层，要求同一布局表达所有 KV 组的 page 结构；两组 page size 不同（32768 vs 65536 字节）时无法用单一 LBNHC 形状表达。BLHNC 将 block 维外置，混合 page size 可分别表达。这是布局语义约束（报错文本即给出修复方向），不是数值或硬件问题。
- 判别：设置前后同一 mini 模型同一命令，唯一变量是布局变量；设置后 KV cache 张量分配进入下一阶段（forward 调试），错误消失。

## 验证信号

- 引擎通过 KV cache 分配阶段（随后错误转移至 forward 期的 `attn_metadata is None` 等下一类问题），修复效果为启动链推进的 tool_observed 证据（source 0 seq 360 之后）。

## 适用与失效边界

- 适用于多 KV cache 组、混合 page size 的自定义模型；单一 page size 模型无需设置。
- 自定义 attention backend 需自行处理 BLHNC 绑定张量形状（本例在 backend 内 reshape）。
- 后续本 shard 还发现 Ascend runner 对 `SlidingWindowMLASpec.head_size_v=0` 的 K/V 拆分假设（需自定义 spec 设 head_size_v）等相邻接入问题，未包含在本卡；本 shard 结束时端到端 parity 未达成（token match 0/5），本卡只主张该单一错误的修复。

## 附：断言存档

- 多 KV cache 组混合 page size（[32768, 65536]）模型在默认 LBNHC 布局下启动失败：ValueError: KV cache layout LBNHC cannot express this model's mixed page sizes；设置 VLLM_KV_CACHE_LAYOUT=BLHNC 后通过 KV cache 构建
