---
{
  "type": "Runbook",
  "title": "FIA workspace 显存观测与固定 scratch 试验：持有者及覆盖边界待核对",
  "description": "来源记录FIA查询workspace约1233.4MiB/卡，并在组合配置下试用256MiB固定scratch。128MiB的MIN_OK仅为单形状未报错，没有数值对照；executor持有归因及跨负载容量保证尚未证实。",
  "tags": [
    "task.debugging",
    "topic.memory"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-13T02:13:38Z",
  "platforms": []
}
---
# FIA workspace 显存观测与固定 scratch 试验：持有者及覆盖边界待核对

## 适用场景

vllm-ascend的FIA/MLA图模式服务中，workspace分配可能挤占MoE所需显存；需要区分查询API返回量、实际存活分配、运行配置变化和固定scratch实验的覆盖范围。

## 触发与观测

来源开启FIA及较高KV/batched配置时发生MoE workspace分配OOM，关闭FIA可运行。MEMDBG显示本例FIA workspace为1233.4MiB/卡；npu-smi在两次配置中记录61371与60114MB/卡，差约1257MB，提示优先检查该分配。

独立探针在q `[16,4,1024]`、k `[256,1,128,1024]`、actual_seq_kvlen=32768等特定参数下扫描workspace，返回128MiB的MIN_OK。此处OK仅指该次调用没有抛异常且同步完成，**没有数值对照，不等于真实最小需求或通用安全边界**。

## 探针与操作

1. 记录真实模型与各调用shape、查询返回bytes、分配生命周期、图捕获/缓存和每rank显存；ON/OFF对照保持其他配置一致。
2. 源码线索为tiling在拿不到真实序列长度时进入isTilingSink最坏情况计算。将源码版本、查询形状与运行产物绑定后再解释返回量。
3. 若扫描更小workspace，应在隔离实验中覆盖实际shape、dtype、KV长度与图模式，除异常/同步外还需数值对照；一次MIN_OK不能给整个服务设固定容量。
4. 若调查谁持有返回buffer，应核对真实executor/图/缓存的所有权与释放过程，做单因素生命周期对照；改cap后显存未下降本身不能确定持有者。

## 机制与判别

来源最终在其mla_v1.py分支尝试绕过查询并固定分配256MiB，以下保留分配改动节选，删除了未证实的所有权及通用安全断言注释：

```python
if workspace is None:
    _fia_ws_bytes = 256 * 1024 * 1024
    workspace = torch.empty(
        _fia_ws_bytes // 2,
        dtype=torch.bfloat16,
        device=q_nope.device,
    )
```

这是一份特定服务中的实验改动记录，不是通用workspace容量建议。来源关于buffer被aclOpExecutor钉住的说法最初为助手的可能解释，随后写进补丁注释；没有所有权源码/分配追踪/受控释放证据，本卡不把它作为已确认根因。

tiling源码线索节选：

```cpp
if (actualSeqQTnd != nullptr && actualSeqKvTnd != nullptr) {
        ComputeSeqLenAndDecodeFlagsForFAI(faInfo, aicoreNum, actualSeqQTnd, actualSeqKvTnd, batch);
    } else {
        faInfo.isTilingSink = true;
    }
    faInfo.workspaces = context->GetWorkspaceSizes(1);

    return ge::GRAPH_SUCCESS;
```

## 验证信号

- 来源组合配置（bypass、data模式、kv 2048M、batched 1024、seqs 16、capture sizes 4至64）记录bench_serve_8的40/40请求成功、无OOM；另有改变batched到512后的MMMU 900/900完成、score 0.7722。
- 这些运行同时改变多项配置，不能将全部显存或吞吐变化归到bypass，也不证明固定容量对任意32K请求都安全。batched 1024在大图场景仍有OOM记录，须保留该反例。
- 单形状MIN_OK没有数值对照；128MiB“真实需求”、256MiB“2倍安全余量”和超范围请求“必定只会报容量不足”的保证均不采用。

## 适用与失效边界

本卡支持优先调查workspace分配与记录特定负载的实验结果。不同token数、heads、D、dtype、KV长度或运行产物均需重新验证。不能把固定scratch当普遍替代查询API的修复，也不能凭补丁注释确定executor的持有行为。
