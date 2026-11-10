---
{
  "type": "Runbook",
  "title": "M-b 方案不可行：`npu_moe_init_routing_v2` 的 scale/第 4 输出不承载 per-expert input_scale",
  "description": "为消除 MoE FP8 逐行激活 scale 的 `repeat_interleave` 动态形状图中断，曾尝试（方案 M-b）向 `npu_moe_init_routing_v2` 传 per-expert 一维 scale 并取第 4 输出（`[S*K]` 静态形状）替代 `repeat_interleave`。实测不可行：非量化 `quant_mode=-1` 下 per-expert scale 被 tiling 校验拒绝（期望 NUM_ROWS 维）；`quant_mode=0/1` 下第 4 输出在探针中全为 0.0，且官方文档明确 scale 语义为 per-row/per-channel，不承载 per-expert input_scale。最终采用 `repeat_interleave(..., output_size=S*K)` 钉静态形状。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "950"
  ]
}
---

# M-b 方案不可行：`npu_moe_init_routing_v2` 的 scale/第 4 输出不承载 per-expert input_scale

## 适用场景

- 模型/框架：Hunyuan-A13B-Instruct-FP8 MoE FP8 路径——`npu_moe_gating_top_k_softmax` → `npu_moe_init_routing_v2`（`quant_mode=-1` 非量化路由，FP8 显式做）→ FP8 `npu_grouped_matmul`（`scale` + `per_token_scale`）→ `npu_moe_finalize_routing`；MoE 逐行激活 scale 原由 `torch.repeat_interleave(self.w13_input_scale, tokens_per_expert)` 构造。
- 平台/版本：Ascend950PR_9589 单卡；CANN 9.1.0；torch 2.12.0+cpu / torch_npu 2.12.0。
- 目标与工作负载：消除 `repeat_interleave` 的数据依赖动态形状图中断（npugraph_ex 适配）。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

- 尝试（M-b）：向 `npu_moe_init_routing_v2` 传 per-expert 一维 `scale=self.w13_input_scale`（`quant_mode=0/1`），拟取第 4 输出（`[S*K]` 静态形状）替代 `repeat_interleave` 消除动态形状图中断。
- 探针（S=4, H=64, E=8, K=2，`scale=torch.arange(1,E+1)` per-expert）实测输出（原文）：

```
=== TEST 1: routing v2 scale expansion ===
quant_mode=-1: FAIL RuntimeError The Inner error is reported as above. The process exits for this inner error, and the current working operator name is aclnnMoeInitRoutingV3.
Since the operator
quant_mode=0: expanded=(8, 64) rowidx=(8,) tpe=[0, 0, 0, 0, 0, 0, 0, 0] out4=(8,) out4dtype=torch.float32 out4=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
quant_mode=1: expanded=(8, 64) rowidx=(8,) tpe=[0, 0, 0, 0, 0, 0, 0, 0] out4=(8,) out4dtype=torch.float32 out4=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
```

- `quant_mode=-1` 失败的底层报错（原文）：

```
[E1010 20:39:40.006756939 OpParamMaker.cpp:453] operator():../third_party/op-plugin/op_plugin/ops/opapi/MoeInitRoutingV2KernelNpuOpApi.cpp:322 NPU function error: call aclnnMoeInitRoutingV3 failed, error code is 561103
[ERROR] 2026-10-10-20:39:40 (PID:233928, Device:0, RankID:-1) ERR00100 PTA call acl api failed.
[PID: 233928] 2026-10-10-20:39:40.885.935 Invalid_Argument(EZ0024): Parameter scale dim[0] of MoeInitRoutingV3 has incorrect value 8. It should be 4.
```

- torch_npu 官方 op 文档（`_op_plugin_docs.py`，`npu_moe_init_routing_v2` 条目原文）：

```
11039:         scale：Tensor类型，可选参数，用于计算量化结果的参数。数据类型支持float32，数据格式要求为ND。如果不输入表示计算时不使用scale，且输出expanded_scale中的值未定义。
11040:             非量化场景下，如果输入则要求为1D的Tensor，shape为(NUM_ROWS,)。
11041:             动态quant场景下，如果输入则要求为2D的Tensor，shape为(expert_end-expert_start, H)。
```

## 探针与操作

- 探针脚本：`${LOCAL_PATH_1}`（TEST 1）——`torch_npu.npu_moe_init_routing_v2(x, expert_idx=idx, scale=scale, active_num=S*K, expert_num=E, expert_tokens_num_type=1, expert_tokens_num_flag=True, active_expert_range=[0,E], quant_mode=qm)`，对 `qm ∈ {-1, 0, 1}` 分别取 4 个输出并打印 shape/值。
- 失败路线（不可采用）：per-expert 一维 scale + `quant_mode=-1`（tiling 直接拒绝）；`quant_mode=0/1` 期望第 4 输出承载 per-expert input_scale（探针全 0，且语义不符）。

## 机制与判别

- 失败：`quant_mode=-1` 下 per-expert scale 直接被 tiling 校验拒绝（`Parameter scale dim[0] of MoeInitRoutingV3 has incorrect value 8. It should be 4.`，即期望 NUM_ROWS 维）；`quant_mode=0/1` 下第 4 输出虽为 `[S*K]` 形状但探针中全为 0.0——torch_npu 官方文档明确 scale 在非量化场景要求 1D (NUM_ROWS,)、动态量化场景要求 2D (expert_end-expert_start, H)，均为 per-row/per-channel 语义，不承载 per-expert input_scale。
- 可区分解释分支：a) scale 应传 per-expert（E 维）——被 tiling 校验与文档双重证伪；b) 第 4 输出可按需改写为 per-expert 展开——探针全零 + 文档"不输入 scale 时输出值未定义"，不可依赖；c) 动态量化 2D (E, H) 形态可承载——仅当激活 scale 本身 per-channel 时才有意义，本模型是 per-tensor 静态 scale，不匹配。
- 未验证推断：真实权重下 `quant_mode=0/1` 第 4 输出是否仍为 0（探针为随机权重；但语义已由文档排除，不依赖该观测）。

## 验证信号

均在本机（Ascend950PR_9589 单卡、CANN 9.1.0）实测，证据等级：探针 stdout / 算子报错码 + 官方文档。

- 探针（analyzer 事件 201、implementer 复看事件 59）：`quant_mode=-1` 报 `aclnnMoeInitRoutingV3 failed, error code is 561103` / `Invalid_Argument(EZ0024): Parameter scale dim[0] ... incorrect value 8. It should be 4.`；`quant_mode=0/1` 第 4 输出 `[S*K]` 全 0.0。
- 实施期最终裁决（implementer 记录）：未采用 M-b，实测该输出的 `scale` 入参语义为 per-row/per-channel，无法直接承载 per-expert 静态 input_scale。
- 单次观测（一次探针运行），结论以算子报错与官方文档为主证据。

## 适用与失效边界

- 边界（采用的替代）：`torch.repeat_interleave(..., output_size=S*K)` 把输出形状钉为静态（语义不变），配合该改法 graph_break_count 降为 0；`output_size` 方案比 M-b 改动更小更稳。最终代码：

```
        # ---- w13 = [gate | up] ----
        # ``output_size=S*K`` pins the repeat output to a static shape: without it
        # Dynamo treats the (expert-count-derived) length as a dynamic/data-dependent
        # shape and breaks the graph.
        row_is13 = torch.repeat_interleave(self.w13_input_scale, tokens_per_expert, output_size=S * K)  # [M]
```

- 适用边界：本结论针对"per-expert 标量 input_scale 展开为 per-row scale"这一用法；若模型的激活量化本来就是 per-token/per-channel（动态量化），2D scale (E, H) 形态是另一条路径，本轨迹未验证。
- 版本边界：torch_npu 2.12.0 / CANN 9.1.0 的 `npu_moe_init_routing_v2` schema 与文档语义；后续版本（如 MoeInitRoutingV4）语义可能变化，需重核。
- 停止条件：见到 `EZ0024 Parameter scale dim[0]` 报错即说明 scale 维度语义不匹配，应回到文档核对 scale 形状定义，不要尝试换 quant_mode 绕过。
