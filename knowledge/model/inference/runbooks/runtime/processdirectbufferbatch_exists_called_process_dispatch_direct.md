---
{
  "type": "Runbook",
  "title": "gather_selection_kv_cache 直通缓冲 SyncAll 路径 23ms 退化的瓶颈定位：Pass 2 标量 O(n²) 去重",
  "description": "算子/框架：DeepSeek V3.2 KV cache offload 的 AscendC 自定义算子 `gather_selection_kv_cache`（TilingKey=3，extended buffer / direct buffer per-token parallel，phase=3 SyncAll 三阶段架构），任务说明中的 Ascend 910B3（实际产品未核验）。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:03Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": []
}
---

# gather_selection_kv_cache 直通缓冲 SyncAll 路径 23ms 退化的瓶颈定位：Pass 2 标量 O(n²) 去重

## 适用场景

- 来源的实现背景写910B3，项目资料却将其括注为Atlas A3；本轨迹为代码评审，未提供足以消解该冲突的设备查询，不填写A2或A3。

- 算子/框架：DeepSeek V3.2 KV cache offload 的 AscendC 自定义算子 `gather_selection_kv_cache`（TilingKey=3，extended buffer / direct buffer per-token parallel，phase=3 SyncAll 三阶段架构），任务说明中的 Ascend 910B3（实际产品未核验）。
- 工作负载：bs=16、seq=4（64 token / 40 核）、topk=2048、buffer_capacity=8192、~90% 命中率。
- 目标：解释 direct-buffer SyncAll 路径 23ms 相对 TK3 all-in-one 基线 1.3ms（约 18x）的退化来源。

## 触发与观测

- 评审背景（campaign 记录，source 0 seq 74 引用）："The per-token path measures 23ms versus the TK3 baseline of 1.3ms -- a factor of approximately 18x."
- 代码事实（source_observed）："ProcessDirectBufferBatch exists but is never called from the main Process() dispatch. It is dead code. The 'Direct batch-grouped @90% = 2.49ms' benchmark came from the previous implementation where `ProcessDirectBufferBatch` was used (before the SyncAll architecture was built). Now the only active direct-buffer path is `ProcessDirectBufferParallel`."（source 0 seq 74）
- dispatch 事实：`directBuffer_ && sharedGatheredBuffer_` → `ProcessDirectBufferParallel`（Pass1 全核逐 token 命中检测 → SyncAll → Pass2 每批单核去重+FIFO 分配 → SyncAll → Pass3 全核逐 token miss DMA）（source 0 seq 70/74）。

## 探针与操作

- 静态成本分解（reviewer 从源码推算，source 0 seq 74）：Pass1 每 token ≈0.65ms（CopyIn/Sort/4 次 chunk sort-merge/MTE3 DataCopyPad 8KB），每核 2 token ≈1.3ms——与 TK3 基线同级，不是瓶颈；两次 SyncAll ≈10–40µs，不是瓶颈。
- Pass2（每批单核）逐项核算：8192 次标量 `selKvBlockStatusGm_.GetValue()`（4 token×2048）≈0.25ms；~820 个 miss 各做 2 次 GM 读 + 线性去重搜索（平均 ~410 次标量 UB 读）+ 2 次 GM 写 ≈8.5ms；合计 ≈8.75ms/批，16 批并行时关键路径即最慢批——主导成本（且 23ms 实测提示 O(n²) 搜索与标量 GM 延迟相乘后更差）。
- Pass3 逐 token 遍历全部 2048 topk 项做标量 MISS_FLAG 检查（~4096 次 GM 读/核 ≈0.12ms），miss DMA 与 TK3 相同。

## 机制与判别

- 根因：Pass2 的跨 token 去重是纯标量线性搜索（O(missCount²)）叠加标量 GM 读延迟，是 SyncAll 三阶段架构下 23ms 退化的主导项；MTE3 批量拷贝与 SyncAll 屏障均可忽略。
- 判别：TK2 基线用"UB 累积 + DataCopyPad(MTE3) 整体搬出"写 block_status，不做标量 GM SetValue——"TK2 writes `selBlockStatLocal` (a UB tensor) via scalar `SetValue` operations during computation, and then uses `DataCopyPad` (MTE3) to copy the entire buffer to GM at line 728. This is the key difference -- TK2 does NOT do scalar SetValue to GM."（source 0 seq 59）
- 附带发现：非 SyncAll per-token 循环残留 canary 调试代码（directBuffer_ 模式向全部位置写常量 42，lines 224-231）（source 0 seq 67）。
- 改进方向（评审建议，未实施验证）：Pass2 用 sortBuf_ 做 UB 哈希表把 O(n²) 降为 O(n)；或预分配 FIFO 区间/工作区自旋锁替代 SyncAll（910B 无 AtomicAdd）。

## 验证信号

- source_observed（静态代码核算）+ campaign 历史基准数字（23ms/1.3ms/2.49ms，引自仓库 CLAUDE.md/优化记录）；本 trace 内无新设备运行。
- 证据等级：评审级分析（数值为推算，非实测分解）。

## 适用与失效边界

- 适用于：gather_selection_kv_cache extended-buffer SyncAll 架构在 910B3、bs16/seq4/topk2048 量级的性能归因；标量 GM GetValue/SetValue 反模式排查。
- 失效边界：成本分解为静态推算（30ns/25ns 延迟假设），未做 profile 分段实测；不同 bs/seq/topk/命中率配比下各 Pass 占比会变；优化建议未实施。
- 停止条件：若 Pass2 已改为 UB 哈希或向量化，本瓶颈结论失效；引用 2.49ms 基准时注意其来自已废弃的 ProcessDirectBufferBatch 实现。

## 附：断言存档

- gather_selection_kv_cache direct-buffer SyncAll 路径（phase=3）23ms vs TK3 基线 1.3ms（~18x）：Pass1 每核 ~1.3ms 与基线同级、两次 SyncAll ~10-40µs 均非瓶颈；主导成本是 Pass2 每批单核去重的标量 O(missCount²) 线性搜索 + 标量 GM GetValue/SetValue（~8.75ms/批推算）。
- ProcessDirectBufferBatch 是死代码，'Direct batch-grouped @90% = 2.49ms' 基准来自 SyncAll 架构之前的旧实现；当前唯一激活的 direct-buffer 路径是 ProcessDirectBufferParallel。

```text
ProcessDirectBufferBatch exists but is never called from the main Process() dispatch. It is dead code. The "Direct batch-grouped @90% = 2.49ms" benchmark came from the previous implementation where `ProcessDirectBufferBatch` was used (before the SyncAll architecture was built). Now the only active direct-buffer path is `ProcessDirectBufferParallel`.
```

```text
This is very important. TK2 writes `selBlockStatLocal` (a UB tensor) via scalar `SetValue` operations during computation, and then uses `DataCopyPad` (MTE3) to copy the entire buffer to GM at line 728. This is the key difference -- TK2 does NOT do scalar SetValue to GM. It accumulates in UB and copies via MTE3.
```
