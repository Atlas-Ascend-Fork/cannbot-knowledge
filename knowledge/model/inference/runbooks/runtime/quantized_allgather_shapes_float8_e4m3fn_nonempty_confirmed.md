---
{
  "type": "Runbook",
  "title": "量化 CP 空分片与实分片在同一 AllGather 中 dtype 不一致（FP8 vs uint8）",
  "description": "Kimi K3/K31 DSA 量化 + Context Parallel（CP）Prefill 场景：短序列使某 rank 的 CP 分片为空时，空分片张量与打包 KV 的实分片张量进入同一次集合通信。本规则来自 K31 适配 PR #1 检视（source 0 seq 671-678）。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-20T14:17:05Z",
  "platforms": []
}
---

# 量化 CP 空分片与实分片在同一 AllGather 中 dtype 不一致（FP8 vs uint8）

## 适用场景

Kimi K3/K31 DSA 量化 + Context Parallel（CP）Prefill 场景：短序列使某 rank 的 CP 分片为空时，空分片张量与打包 KV 的实分片张量进入同一次集合通信。本规则来自 K31 适配 PR #1 检视（source 0 seq 671-678）。

## 触发与观测

- 触发：量化 CP 路径中，实分片把打包 KV 以 `uint8` 传输；空分片用 `layer_cache["nope_cache"].new_empty(...)` 创建，继承缓存张量的 `float8_e4m3fn` dtype，补齐后两者参与同一 `all_gather_into_tensor`（source 0 seq 622/678）。
- 触发条件举例（agent_narrative，source 0 seq 678）：TP16、CP2、有效长度不超过 16 时产生空 CP 分片。
- 原始观测（CPU 捕获真实类方法，tool_observed，source 0 seq 571/572）：

```
Empty quantized CP rank first AllGather (out/in dtype, shapes): (torch.float8_e4m3fn, torch.float8_e4m3fn, (32, 656), (16, 656))
Nonempty quantized CP rank first AllGather: (torch.uint8, torch.uint8, (32, 656), (16, 656))
Confirmed: ranks use different collective dtypes for the same packed cache
```

## 探针与操作

- 探针 A（source 0 seq 569/571）：AST 提取 PR 中 `KimiDSAAttention._gather_prefill_cp_cache` 与 `_forward_prefill_cp`，剥离装饰器后组装成独立类执行；用桩 `Dist.all_gather_into_tensor` 在集合通信入口抛出捕获异常，记录 output/input 的 dtype 与 shape。空分片分支走 `enable_dsa_quant=True`、`nope_cache` 为 `torch.float8_e4m3fn`、`indexer_key_cache` 为 `torch.uint8` 的构造。
- 探针 B（source 0 seq 619/621/623）：`curl` 拉取 Ascend/pytorch v2.10.0 `torch_npu/csrc/distributed/ProcessGroupHCCL.cpp`，`rg 'Float8|float8|kByte|HCCL_DATA_TYPE_FP8'` 核对 dtype→HCCL 类型映射分支。

## 机制与判别

- 机制（源码，tool_observed，source 0 seq 622/623）：

```python
            index_q = hidden_states.new_empty(
                0, self.indexer.num_heads, self.indexer.head_dim,
                dtype=torch.float8_e4m3fn if self.enable_dsa_quant else hidden_states.dtype,
            )
            ...
            keys = {
                name: layer_cache[name].new_empty(0, layer_cache[name].shape[-1])
                for name in names
            }
```

空分片经 `layer_cache[name].new_empty` 继承源缓存 dtype：`nope_cache` 是 `float8_e4m3fn`，而打包字节的 `indexer_key_cache` 系列为 `uint8`，导致同一 packed cache 的通信载体 dtype 不一致。

- 判别（source 0 seq 621/623/678）：torch_npu v2.10.0 `ProcessGroupHCCL.cpp` 中 `at::kBool || at::kByte` 走字节分支（5323/5587/5666/5747/5751 行附近），`Float8_e5m2 || Float8_e4m3fn` 走独立分支（7906-7907 行）；即 `uint8` 与 `float8_e4m3fn` 映射为不同 HCCL 类型（UINT8 vs FP8E4M3，映射实现在 HCCLUtils.cpp），不会自动统一成字节，违反集合通信各 rank 类型一致的要求。
- 修复方向（agent_narrative，source 0 seq 678）：量化空分片统一创建为 `uint8`，保持打包数据的字节语义。

## 验证信号

- tool_observed（source 0 seq 571/572）：空/实分片 AllGather dtype 捕获输出逐字如上；探针脚本 exit_code 0。
- tool_observed（source 0 seq 621/623）：torch_npu 2.10 源码 rg 结果（kByte 分支与 Float8 分支并存）。
- agent_narrative（source 0 seq 667/668/678）：三处问题检视报告与映射源码引用。
- 验证层级：CPU 方法执行捕获 + 上游源码静态核对；未执行 NPU 多卡集合通信实测。

## 适用与失效边界

- 结论绑定 torch_npu v2.10.0 的 HCCL 映射行为；其他版本需重查映射源码。
- 仅覆盖量化 CP 空分片场景；非量化路径空分片 dtype 跟随 hidden_states，不在本规则范围。
- 未验证修复后行为（本会话只检视未改码）；`new_empty` 继承 dtype 的陷阱在任意“按缓存模板建空张量”的并行代码中同类存在。

## 附：断言存档

- 量化 CP 下空分片与实分片在同一 all_gather_into_tensor 中 dtype 不一致：实分片打包 KV 以 uint8 传输，空分片经 layer_cache["nope_cache"].new_empty(...) 继承 float8_e4m3fn；实测捕获空分片 (float8_e4m3fn,(32,656)/(16,656)) vs 实分片 (uint8, 同 shape)
