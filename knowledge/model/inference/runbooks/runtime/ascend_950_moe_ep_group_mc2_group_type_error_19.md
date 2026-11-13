---
{
  "type": "Runbook",
  "title": "950 平台 moe_ep_group_mc2 未设置 group_type 导致 HCCL error code 19",
  "description": "cann-recipes-infer（K3 系模型等）推理迁移到新 CANN 包 + 950 平台后，_init_parallel_comm_groups 阶段 moe_ep_group_mc2 通信组创建失败的场景。",
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
# 950 平台 moe_ep_group_mc2 未设置 group_type 导致 HCCL error code 19

## 适用场景
cann-recipes-infer（K3 系模型等）推理迁移到新 CANN 包 + 950 平台后，_init_parallel_comm_groups 阶段 moe_ep_group_mc2 通信组创建失败的场景。

## 触发与观测
报错 RuntimeError: create_config:../torch_npu/csrc/distributed/HCCLUtils.cpp:140 NPU function error: device error type 0, error code is 19（get_hccl_comm_name → HCCL communicator 配置创建阶段，参数错误）；日志同屏有 init_comm_group_by_ranks: group=moe_ep_group_mc2 ... group_type=None platform_version=950。

## 探针与操作
1) 在日志中确认 group_type=None platform_version=950。
2) rg 对比各模型 register_group 的 group_type：glm_5（mc2_group_type）、deepseek_v4（moe_ep_mc2_group_type）、qwen3_5（group_type=3 if _PLATFORM_VERSION == "950" else None）、kimi_k3 仓库版（group_type=3）。
3) grep 服务器版本：test.py:2479 group_type=None（旧逻辑），当前仓库 modeling_kimi_k3.py:2574 group_type=3。

## 机制与判别
判别与修复：moe_ep_group_mc2 的 register_group 在 950 平台必须设置 group_type=3（aiv）；glm_5/deepseek_v4/qwen3_5 等支持 950 的模型均为 group_type=3 if 950 else None；报错服务器运行的是旧版本（group_type=None），需同步新版或同样改 group_type=3，见工件。

机制片段：
```
# 服务器当前（报错）：group_type=None
# 当前仓库（已修复）：group_type=3
self.comm_manager.register_group(
    name="moe_ep_group_mc2",
    ...
    group_type=3,  # 950 平台必须设置 hccl_op_expansion_mode=aiv
)
```

## 验证信号
诊断型会话（分析用户提供的远端日志 + 仓库源码比对），修复方向与跨模型证据链完整；本轨迹内未执行修复与复跑验证。

## 适用与失效边界
适用于 950 平台 mc2 通信组注册；服务器运行旧版 modeling/test 代码时需同步新版或同样补 group_type=3。

## 结论与证据边界
- 判别与修复：moe_ep_group_mc2 的 register_group 在 950 平台必须设置 group_type=3（aiv）；glm_5/deepseek_v4/qwen3_5 等支持 950 的模型均为 group_type=3 if 950 else None，当前仓库 modeling_kimi_k3.py:2574 已修复，报错服务器运行的是旧版本（group_type=None，对应 test.py:2479 逻辑），需同步新版或同样改 group_type=3
