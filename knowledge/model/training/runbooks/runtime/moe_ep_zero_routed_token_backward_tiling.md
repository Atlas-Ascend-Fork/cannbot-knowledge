---
{
  "type": "Runbook",
  "title": "MoE EP 的 rank 级零 token：区分通信空分片与 unpermute grad tiling 拒绝",
  "description": "真实双卡用例中零 routed token rank 前向完成、反向在 MoeTokenUnpermuteGrad 报 input shape has 0；CPU fake 通过不能覆盖设备 tiling 限制。",
  "tags": [
    "task.debugging",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# MoE EP 的 rank 级零 token：区分通信空分片与 unpermute grad tiling 拒绝

## 适用场景

torchtitan-npu EP>1，当前 rank 的全部本地 expert 都未收到 routed token。记录芯片标识不足以确定注册平台家族。

## 触发与观测

EP=2、四专家、全部 token 路由到另一 rank 的 expert 时，rank0 local_counts=[0,0]、routed_shape=(0,2)。

## 探针与操作

分别构造整个 rank 零 token 和仅某个本地 expert 零 token，对比 CPU fake 与真实 NPU；保持空输出仍连接 autograd。

原始源码差分或测试输出（用于核对）：

```text
[rank 0] local_counts=[0, 0] routed_shape=(0, 2)
[rank 1] local_counts=[6, 0] routed_shape=(6, 2)
```

原始源码差分或测试输出（用于核对）：

```text
[rank0]: RuntimeError: npu_moe_token_unpermute_grad:../third_party/op-plugin/op_plugin/ops/opapi/StructKernelNpuOpApi_28.cpp:129 NPU function error: call aclnnMoeTokenUnpermuteGrad failed, error code is 561002
[rank0]: [ERROR] 2026-08-25-00:19:18 (PID:1160306, Device:0, RankID:0) ERR00100 PTA call acl api failed.
[rank0]: [PID: 1160306] 2026-08-25-00:19:18.320.311 Execution_Error(EZ1008): Failed to execute operator MoeTokenUnpermuteGrad_86. Reason: Failed to execute tiling function.
[rank0]:         Solution: 1.If the tiling function does not exist, check whether the tiling function is registered successfully. 2.If the tiling function fails to be executed, check the implementation logic of the tiling function.
[rank0]: TraceBack (most recent call last):
[rank0]:         [MoeTokenUnpermuteGrad] input shape has 0.[FUNC:Tiling4MoeTokenUnpermuteGrad][FILE:moe_token_unpermute_grad_tiling.cpp][LINE:307]
```

## 机制与判别

本例失败发生在 unpermute grad 的 tiling 对整体零 shape 的检查，而不是凭“空分片”一词就归为通信挂死。某个 expert 为零但 rank 总 token 大于零，是不同的边界条件。

## 验证信号

原始 NPU 双卡输出显示 rank0 空输入后反向报 561002，包含 [MoeTokenUnpermuteGrad] input shape has 0；CPU fake 同类场景通过。另一份来源是补充语境，不计为第二次独立复现。

## 适用与失效边界

记录绑定所用算子版本；新版空输入支持需重新核对。测试脚本必须保持真实 expert_forward 的空张量路径，不能用脱离梯度图的 zeros_like 冒充该复现。
