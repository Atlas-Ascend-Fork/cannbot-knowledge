---
{
  "type": "Runbook",
  "title": "vLLM 0.18 Mooncake store 秒级耗时的同步等待诊断候选",
  "description": "vllm-ascend + mooncake ascend store 池化 KV 传输（AscendStoreConnector、kv_role=kv_both、protocol=ascend），MoE 模型（Qwen3-235B-A22B-W8A8 级别）、TP+DP+EP、`--async-scheduling` 部署。 版本间池化性能回归定位：同配置下 0.18 劣化而 0.21 正常，需要判别差异在 vllm-ascend 层还是 vllm core 层。 知识形态：diagnostic_rule（trigger / probe / observation / discrimination）。",
  "tags": [
    "task.debugging",
    "topic.kv_cache"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# vLLM 0.18 Mooncake store 秒级耗时的同步等待诊断候选

## 适用场景

- vllm-ascend + mooncake ascend store 池化 KV 传输（AscendStoreConnector、kv_role=kv_both、protocol=ascend），MoE 模型（Qwen3-235B-A22B-W8A8 级别）、TP+DP+EP、`--async-scheduling` 部署。
- 版本间池化性能回归定位：同配置下 0.18 劣化而 0.21 正常，需要判别差异在 vllm-ascend 层还是 vllm core 层。

## 触发与观测


来源用户报告相同启动参数下，0.18 的 batch_get 调用约 3s，0.21 约 500ms，并描述前者多出含 Notify Wait/EVENT_WAIT_SQE 的 stream。两环境 CANN 均为 9.0.0。这些是用户提供的前置观测，轨迹没有完整原始 profiling A/B 可比记录。

## 探针与操作

- 探针 1（代码取证）：拉取 GitHub releases/v0.18.0 分支的 `vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/backend/mooncake_backend.py` 原文核对 set_device/get/put（注意：不能拿 main 分支历史 commit 代替 release 分支）。
- 探针 2（双版本对比）：clone releases/v0.18.0 与 releases/v0.21.0rc（分支名是 `releases/v0.21.0rc`，`releases/v0.21.0rc1` 是 tag 不是分支），逐文件对比 mooncake_backend.py、utils.py、model_runner_v1.py、kv_transfer.py、sampler.py、fused_moe.py、pool_worker.py 的 stream 相关代码。
- 探针 3（效果验证）：在 get() 前后加打点（synchronize 耗时 / batch_get 耗时 / 总耗时），预期 sync 仅几十~几百 ms、batch_get 约 500ms、total 远小于 3s——若成立可作为进一步检查的线索，不能单独证明 3s 的绝大部分是跨 stream 协调的硬件开销而非实际计算。

## 机制与判别

- 假设一（被否决）：多节点 set_device 用全局 rank（npu:8~15 不存在、静默回退 npu:0）导致跨设备同步。否决证据（release 分支实际代码）：

```python
    def set_device(self):
        local_rank = get_world_group().local_rank
        device = torch.device(f"npu:{local_rank}")
        torch.npu.set_device(device)

    def register_buffer(self, ptrs: list[int], lengths: list[int]):
        if os.getenv("ASCEND_ENABLE_USE_FABRIC_MEM", "0") != "1":
            global_te.register_buffer(ptrs, lengths)

    def exists(self, keys: list[str]) -> list[int]:
        return self.store.batch_is_exist(keys)

    def put(self, keys: list[str], addrs: list[list[int]], sizes: list[list[int]]):
        try:
            res = self.store.batch_put_from_multi_buffers(keys, addrs, sizes)
            for value in res:
                if value < 0:
                    logger.error(f"Failed to put key {keys},res:{res}")
        except Exception as e:
            logger.error(f"Failed to put key {keys},error:{e}")

    def get(self, keys: list[str], addrs: list[list[int]], sizes: list[list[int]]):
        try:
            res = self.store.batch_get_into_multi_buffers(keys, addrs, sizes)
            for value in res:
                if value < 0:
                    logger.error(f"Failed to get key {keys}, res:{res}")
        except Exception as e:
            logger.error(f"Failed to get key {keys}, error:{e}")
```

- 来源结论：vllm-ascend releases/v0.18.0 的 MooncakeBackend.set_device 已经使用 get_world_group().local_rank 构造 npu 设备（而非全局 rank），多节点 set_device rank 越界回退假设被 release 分支实际代码否决。
- 来源结论：待验证解释：vllm 0.18 的 async scheduling 在 step N 与 step N+1 之间缺少完整 stream 同步屏障，start_load_kv 调用 batch_get_into_multi_buffers 时上一 step 的 global_stream/HCCL/update 等 pending 操作仍在，mooncake ascend 协议被迫做跨 stream 同步（硬件层 Notify Wait + EVENT_WAIT_SQE，4 个额外 stream），形成 3s 级开销；0.21 的调度与事件处理不同，但完整屏障语义尚未核实。修复（方案一）是在 get() 调用前加 torch.npu.synchronize()，把同步提前到 Python 层完成；该修复效果为用户实测口头确认（store 接口耗时恢复正常），本轨迹内无独立客观复测数据。
- 修复机制单元（方案一，get() 前置同步）：

```python
def get(self, keys: list[str], addrs: list[list[int]], sizes: list[list[int]]):
    try:
        torch.npu.synchronize()  # 新增：等待所有 stream 完成
        res = self.store.batch_get_into_multi_buffers(keys, addrs, sizes)
        for value in res:
            if value < 0:
                logger.error(f"Failed to get key {keys}, res:{res}")
    except Exception as e:
        logger.error(f"Failed to get key {keys}, error:{e}")
```

- 时序模型（判别核心）：`kv_role="kv_both"` 且未开 load_async/use_layerwise 时 `start_load_kv` 的 `m_store.get()` 是同步调用，发生在主线程前向 setup 阶段；0.18 上一 step 的 random_sample（global_stream）、EP all-to-all（HCCL stream）、async 状态更新（update_stream）、异步输出拷贝等仍 pending，mooncake 访问 KV cache 内存时 CANN 发现其他 stream 的 pending 操作即建立跨 stream 同步；0.21 的完整跨流先后关系仍需事件级取证，不能据版本号推导。

## 验证信号


源码读回确认来源 0.18 分支的 set_device 使用 local_rank，get/put 附近没有显式 stream 同步。用户口头反馈在 get 前加入 synchronize 后 store 接口耗时正常；没有独立测得 sync/batch_get/总耗时，也没有端到端性能回归结果。

## 适用与失效边界


这是同步等待归属的诊断候选。显式 synchronize 可能把等待移到调用外，单独 batch_get 变快不代表总耗时或模型性能改善。不同版本存在多项调度变化，尚不能把性能差异唯一归因于上一 step 残留或断言 0.21 存在完整跨流屏障。
