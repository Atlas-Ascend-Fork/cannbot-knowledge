---
{
  "type": "Runbook",
  "title": "world_size=1 跑 K3 MoE Prefill：默认 process group 未初始化即调 dist.all_to_all_single（无 moe_ep_size=1 全本地分支）",
  "description": "world_size=1 跑 K3 MoE Prefill 直接调 dist.all_to_all_single 报 Default process group has not been initialized：ModelRunner 仅 world_size>1 才 init_process_group，而 MoE 路径缺 moe_ep_size=1 全本地分支。",
  "tags": [
    "task.debugging",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# world_size=1 跑 K3 MoE Prefill：默认 process group 未初始化即调 dist.all_to_all_single（无 moe_ep_size=1 全本地分支）


## 适用场景
cann-recipes-infer 单机（world_size:1、with_ckpt=False）smoke 推理中带 MoE 层的 kimi k3 模型 Prefill 崩溃排障；适用于评估推理框架单 rank 路径的分布式依赖。

## 触发与观测
单机 smoke 在 MoE Prefill 崩溃：ValueError: Default process group has not been initialized（此前 warning allow_internal_format=False 只是布局提示，不是崩溃原因）。

## 探针与操作
操作：读 traceback 定位 dispatch_double_routing → dist.all_to_all_single；核对 ModelRunner 的进程组初始化条件。关键代码与调用：

```text
if torch.npu.is_available() and self.world_size > 1:
    torch.distributed.init_process_group(...)
```


```text
dist.all_to_all_single(owner_counts, tokens_per_expert, group=group)
```


## 机制与判别
判别：这不是权重/tokenizer/CANN 问题——是单 rank 路径缺分布式初始化时 MoE 通信原语直接失效。

关键结论：

- world_size=1 的 smoke 在 MoE Prefill dispatch_double_routing 调 dist.all_to_all_single 时抛 ValueError: Default process group has not been initialized, please make sure to call init_process_group（traceback 定位 modeling_kimi_k3.py:1550）。
- 根因：ModelRunner 只在 torch.npu.is_available() and self.world_size > 1 时 torch.distributed.init_process_group(...)，而 MoE Prefill 仍调用 dist.all_to_all_single；当前 K3 MoE 路径没有处理 moe_ep_size=1 的全本地执行分支。

## 验证信号

来源 smoke 的 traceback 报 `Default process group has not been initialized`，调用点位于 MoE prefill 的 all_to_all_single。源码确认 ModelRunner 仅在 NPU 可用且 world_size>1 时初始化进程组；没有针对 world_size=1 修订后的通过记录。

## 适用与失效边界
适用：world_size=1 的 K3/K3 类 MoE 模型单机 smoke。失效边界：1) 正式单机 MoE 需要 moe_ep_size=1 的全本地执行分支或 tiny-world 初始化进程组，本轨迹未实现与验证；2) 结论基于 3 层缩小模型（含 MoE 层），纯 dense 或 MLP-only 模型不受影响。
