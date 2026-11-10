---
{
  "type": "Runbook",
  "title": "npu_grouped_matmul 权重布局必须为 [E,K,N]：[E,N,K] 布局报 aclnn 161002 错误的定位与转置修复",
  "description": "HYV4 MoE 融合探针以 F.linear 风格 [E,N,K] 权重调用 npu_grouped_matmul 时报 RuntimeError（aclnnGroupedMatmulV5 error 161002，AclNN_Parameter_Error(EZ1001) 维度不匹配）。将 gate_up/down 专家权重 permute(0,2,1) 转置为 [E,K,N] 后调用成功：单层 MoE（E=256/H=2816/I=768/top-8）融合路径 decode 0.522 ms / prefill 0.698 ms，对逐专家循环 cos 0.99998。",
  "tags": [
    "task.debugging",
    "topic.graph_execution",
    "topic.mixture_of_experts"
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

# npu_grouped_matmul 权重布局必须为 [E,K,N]：[E,N,K] 布局报 aclnn 161002 错误的定位与转置修复

## 适用场景

- 模型/框架：HYV4（`hy_v4`，vendored `models/modeling_hy_v4.py`，逐专家 `HYV4Experts` 循环改造）及任何把 `nn.Linear` 风格专家权重 `[E, N, K]` 喂给 `torch_npu.npu_grouped_matmul` 的 MoE 推理实现；参考链路同 `cann-recipes-infer` 的 hy3 / deepseek_v4 / gemma_4 单卡 TP 路径。
- 平台/版本：Ascend950PR_9589 单卡、CANN 9.1.0（ascend950 kernel 目录 `ops_transformer/grouped_matmul_apt`）、torch 2.12.0+cpu、torch_npu 2.12.0。
- 工作负载：bf16 非量化 MoE 专家计算（本例 E=256 / H=2816 / I=768 / top-8，`split_item=3`、`group_list_type=1`）。量化场景（int8/int4 weight + NZ 格式）布局约束不同，不在本卡范围。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

把 PyTorch `F.linear` 习惯的专家权重布局（每个专家权重为 `[N, K]`，堆叠为 `[E, N, K]`）直接传给 `npu_grouped_matmul`，算子在 aclnn 层报错。阶段 3.1 只读探针（`${LOCAL_PATH_1}`）首次运行输出（事件 201，原文）：

```
=== npu_grouped_matmul layout probe ===
[layout:w[N,K]] FAIL RuntimeError: npu_grouped_matmul:../third_party/op-plugin/op_plugin/ops/opapi/GroupedMatmulKernelNpuOpApi.cpp:340 NPU function error: call aclnnGroupedMatmulV5 failed, error code is 161002
[ERROR] 2026-10-13-16:07:
[layout:w[K,N]] ok shape=(5, 6)
```

同一事件里，基准部分用未转置权重的融合路径同样失败：

```
=== MoE layer decode(1 tok) ===
loop         : 18.601 ms
fused FAIL RuntimeError: npu_grouped_matmul:../third_party/op-plugin/op_plugin/ops/opapi/GroupedMatmulKernelNpuOpApi.cpp:340 NPU function error: call aclnnGroupedMatmulV5 failed, error code is 161002
[ERROR] 2026-10-13-16:07:04 (PID:239366, Device:0, RankID:-1) ERR00100 PTA call acl api failed.
[PID: 239366] 2026-10-13-16:07:04.811... AclNN_Parameter_Error(EZ1001): Dim 1 value of x[0] should be equal with dim 1 value of
```

（最后一条 EZ1001 报错在原始日志中即被截断；`loop : 18.601 ms` 一行同时说明逐专家循环基线在此规模可测。）

## 探针与操作

布局探针用极小维度（E=4, K=8, N=6）对两种候选布局做二分验证，先于全量基准定位问题：

```
24: def try_layout(w, tag):
25:     try:
26:         y = torch_npu.npu_grouped_matmul([xr], [w], group_list=counts_t, group_type=0,
27:                                          group_list_type=1, split_item=3)[0]
28:         print(f"[layout:{tag}] ok shape={tuple(y.shape)}")
29:         return y
30:     except Exception as e:
31:         print(f"[layout:{tag}] FAIL {type(e).__name__}: {str(e)[:200]}")
32:         return None
33:
34: print("=== npu_grouped_matmul layout probe ===")
35: y_nk = try_layout(w_nk, "w[N,K]")
36: y_kn = try_layout(w_kn, "w[K,N]")
```

修复：把专家权重一次性转置成 `[E, K, N]`（`x[M,K] @ w_g → [M,N]`）， fused 基准改喂转置后的 `gate_up_kn` / `down_kn`（失败路线——直接喂 `[E,N,K]` 权重——不可采用）：

```
64: H, I, NE, TOPK = 2816, 768, 256, 8
65: gate_up = torch.randn(NE, 2 * I, H, dtype=torch.bfloat16, device=dev) * 0.02
66: down = torch.randn(NE, H, I, dtype=torch.bfloat16, device=dev) * 0.02
67: # npu_grouped_matmul expects weight [E, K, N] (x[M,K] @ w_g -> [M,N])
68: gate_up_kn = gate_up.permute(0, 2, 1).contiguous()
69: down_kn = down.permute(0, 2, 1).contiguous()
```

即 `gate_up_proj [E,2I,H] → [E,H,2I]`、`down_proj [E,H,I] → [E,I,H]`，加载期一次性 `permute(0,2,1)`，不是每步转置。修复后同探针重跑（事件 211）成功。

## 机制与判别

- 结论一（布局契约）：npu_grouped_matmul 的权重布局实测要求 [E,K,N]（x[M,K] @ w_g → [M,N]）：传入 [E,N,K]（F.linear 风格）布局时报 RuntimeError: npu_grouped_matmul:../third_party/op-plugin/op_plugin/ops/opapi/GroupedMatmulKernelNpuOpApi.cpp:340 NPU function error: call aclnnGroupedMatmulV5 failed, error code is 161002（伴随 AclNN_Parameter_Error(EZ1001): Dim 1 value of x[0] should be equal with dim 1 value of，原始日志即在此截断）。锚点/信号：来源记录 事件 201（布局二分探针：`w[N,K]` FAIL、`w[K,N]` ok shape=(5, 6)）。
- 结论二（修复有效）：将 gate_up_proj [E,2I,H] / down_proj [E,H,I] 以 permute(0,2,1) 转置为 [E,H,2I] / [E,I,H] 后，单层 MoE 融合路径与逐专家循环数值等价：decode(1 token) cos=0.99998128、prefill(13 token) cos=0.99998337，maxdiff=1.221e-04。锚点：来源记录 事件 207（转置修改）；信号：事件 211（融合路径 decode 0.522 ms / prefill 0.698 ms 对 loop 17.037 / 139.363 ms）。
- 可区分解释：同一错误码在"布局错误"与"输入 x 维度不匹配"两种场景下都会出现（EZ1001 文案 `Dim 1 value of x[0] should be equal with dim 1 value of ...`），本例用极小维度布局二分探针将其定位为权重布局维度序问题，而非 x 自身 shape 错误——若 fused 路径的 x（expanded[M,K]）shape 错误，`w[K,N]` 分支也会失败，而实测 `w[K,N]` 成功。
- 未验证推断：ascend950 之外的芯片（A2/A3）上该布局契约由官方文档口径佐证（`npu_grouped_matmul` 文档 weight 支持逐组 [K,N]），本组来源观测未在其它芯片复测。

## 验证信号

以下均为本组来源观测轨迹内客观观测，平台 Ascend950PR_9589 单卡、bf16、随机权重：

- 事件 201（来源记录）：`[layout:w[N,K]] FAIL ... error code is 161002` / `[layout:w[K,N]] ok shape=(5, 6)`（布局二分，直接证据）。
- 事件 211（来源记录，修复后单次运行）：
  - `=== MoE layer decode(1 tok) ===`：loop 17.037 ms、fused(clip) 0.522 ms、`cos(loop,fused)=0.99998128 maxdiff=1.221e-04`；
  - `=== MoE layer prefill(13 tok) ===`：loop 139.363 ms、fused(clip) 0.698 ms、`cos(loop,fused)=0.99998337 maxdiff=1.221e-04`。
- 事件 218（来源记录）：router/rms_norm/rope/swiglu 次级探针在同一进程跑通（本卡不展开）。
- 交叉佐证（单次观测）：来源记录 事件 223 在真实维度（256×1536 / 256×2816 转置视图）再次以 `cos=0.999998` 跑通 `[E,K,N]` 调用。

收益口径：17.037→0.522 ms 与 139.363→0.698 ms 为同一探针进程内的单次基准（各 bench 6/20 次取平均），仅表征该单层探针负载，不等同整网收益（整网口径见 [HYV4 五点 torch_npu 融合替换（MoE init_routing_v2→grouped_matmul→clipped_swiglu→grouped_matmul→finalize_routing 等）的模块级/整网验证与同会话 A/B 性能](../performance/hyv4_torch_npu_moe_init_routing_v2_grouped_matmul.md)）。

## 适用与失效边界

- 布局契约针对非量化 bf16/fp16 路径（本例 `quant_mode=-1`、`split_item=3`、`group_list_type=1`、`group_type=0`）；量化 GMM（a8w8/a8w4、NZ 格式）布局要求不同，需另行验证。
- 权重转置必须一次性完成（加载期/惰性缓存），每步转置会把收益吃掉；转置为 `.contiguous()` 拷贝的显存代价与替代方案见 [npu_grouped_matmul 直接消费 permute(0,2,1) 非连续转置视图，免除 [E,K,N] 专家权重的 contiguous 拷贝（约 10 GiB/4 层）](../performance/npu_grouped_matmul_permute_contiguous_gib.md)。
- `[E,N,K]` 直传是失败路线，不可采用；报错来自 aclnn 层（EZ1001 维度不匹配），Python 侧无更具体提示，极小维度布局探针是最快定位手段。
- 34 层完整配置下逐专家循环与融合路径的绝对数值未在本组来源观测测量（本组来源观测为 4 层单卡可行性配置）。
