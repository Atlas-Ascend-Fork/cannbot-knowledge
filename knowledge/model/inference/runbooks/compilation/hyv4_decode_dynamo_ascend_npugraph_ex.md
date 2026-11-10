---
{
  "type": "Runbook",
  "title": "HYV4 Decode 入图前的 Dynamo 图中断六类根因与最小判别探针（Ascend npugraph_ex 适配）",
  "description": "对 HYV4 paged decode 前向用 torch._dynamo.explain 只读追踪，实测 30 graph / 29 break，并用最小化探针把中断分离为六类根因：中间张量 .is_npu 属性分支（fundamental Data-dependent branching）、FA v2 actual_seq_* 以 Tensor 传入 SymInt[]? 形参（aten._local_scalar_dense）、动态 kv_len 切片/mask、Runner 每步重建输入张量、eager MoE nonzero、函数内 import torch_npu。关键判别：.device.type == \"npu\" 在中间张量上 Dynamo 可静态解析（0 break），而 .is_npu 不可；GE/torchair 后端在本机因 protobuf 缺失不可用。",
  "tags": [
    "task.debugging",
    "topic.compilation",
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

# HYV4 Decode 入图前的 Dynamo 图中断六类根因与最小判别探针（Ascend npugraph_ex 适配）

## 适用场景

- 模型/框架：HYV4（`model_type = hy_v4`，对应 `tencent/Hy4-preview`；MLA + DSA indexed attention + iHC 超连接 + 256 专家 MoE + attention sink）独立部署（vendored `models/modeling_hy_v4.py` + 自管 Runner），阶段 3 已完成 torch_npu 融合算子（MoE experts/router、RMSNorm、MLP SwiGLU、RoPE）与 Paged MLA + FA v2。
- 平台/版本：Ascend950PR_9589 单卡，CANN 9.1.0（driver 7.0.t9.0.B887），torch 2.12.0+cpu，torch_npu 2.12.0，transformers 5.19.0；venv 中 protobuf/google 包完全未安装。
- 目标：在把 LLM Decode 前向交给 `torch.compile(backend="npugraph_ex")` 之前，枚举并分类 Dynamo 图中断（graph break），判定哪些可消除、哪些是 fundamental；本卡是只读诊断（阶段 5.1 分析），修复配方见[HYV4 Decode 29 处 Dynamo 图中断消除配方：npugraph_ex 整图捕获 + 0 重编译 + 同会话 decode 4×提速](hyv4_decode_dynamo_npugraph_ex.md)。

## 触发与观测

对融合全开、L=4 的真实 paged decode 前向运行 `torch._dynamo.explain`，实测 30 graph / 29 break；`fullgraph=True` 编译首个报错即中间张量 `.is_npu` 属性分支。逐字观测（探针 `.scratch/graph_break_probe.py`，日志 `.scratch/graph_break_fused.log`）：

```
exit=0
GRAPH_COUNT 30
GRAPH_BREAK_COUNT 29
BREAK[0] Data-dependent branching
    at modeling_hy_v4.py:991 forward
    at modeling_hy_v4.py:94 forward
```

fullgraph=True 首个报错（`.scratch/graph_compile_probe.log`）：

```
exit=0
EAGER_DECODE_MS 12.9
FULLGRAPH_TRUE_FAIL Unsupported('Data-dependent branching\n  Explanation: Detected data-dependent branching (e.g. `if my_tensor.sum() > 0:`). Dynamo does not support tracing dynamic control flow.\n  Hint: This graph break is fundamental - it is unlikely that Dynamo will ever be able to trace through your code. Consider finding a workaround.\n  Hint: Use `torch.cond` to express dynamic control flow.\n\n  Developer debug context: attempted to jump with GetAttrVariable(TensorVariable(), is_npu)\n\n For more details about this graph break, please visit: https://meta-pytorch.github.io/compile-graph-break-site/gb/gb0170.
```

## 探针与操作

全部探针只读、不改模型代码（写在 `.scratch/`）：

1. **后端可用性探针**（`graph_probe_npugraph_ex.py` / `graph_probe_ge.py`）：tiny Linear+ReLU 分别用 `torch.compile(backend="npugraph_ex")` 与 `backend="npu"` 捕获。
2. **中断枚举探针**（`graph_break_probe.py`）：`backend="eager"` 只读 trace 真实 decode 前向，打印 `GRAPH_COUNT / GRAPH_BREAK_COUNT` 与逐条 `BREAK[i]`（含 user_stack 定位到 modeling 文件行号）。
3. **最小判别探针**：用最小 Module 分别验证 `.is_npu` 五种写法、`SymInt[]` 形参传 Tensor vs `list[int]`：
   - `torch._dynamo.explain` 版（`if x.is_npu`、`if flag and x.is_npu`、分支内 `import torch_npu` 等）；
   - `torch.compile(fullgraph=True)` 版取真实报错（`intermediate_is_npu` / `tensor_dims`）与 `list_dims` 对照；
   - 五写法对照（`graph_break_pattern_probe.py`，见下方机制工件第一段）。
4. **op schema 打印**：`torch.ops.npu.npu_fused_infer_attention_score_v2.default._schema`。
5. **npugraph_ex 源码核对**：`torch_npu/dynamo/npugraph_ex/_acl_concrete_graph/acl_graph.py` 的 `_REPLACE_FUNC_MAP`（FA v2 static-workspace 替换与 replay 更新键）。

## 机制与判别

结论与证据（以下每条为本卡结论原文）：

- 在 Dynamo 追踪下，作用于中间张量的 if y.is_npu: 分支触发 fundamental 的 Data-dependent branching（报错 attempted to jump with GetAttrVariable(TensorVariable(), is_npu)），而同一判断改写为 y.device.type == "npu" 后 0 中断；作用于函数入参或 nn.Parameter 的 .is_npu 同样不中断。
  - 判别证据一（五写法最小探针，tool_result 逐字）：

```
variant_param_is_npu: graphs=1 breaks=0
variant_param_device: graphs=1 breaks=0
variant_interm_is_npu: graphs=0 breaks=-1
variant_interm_device: graphs=1 breaks=0
variant_global: graphs=1 breaks=0
```

  - 判别证据二（fullgraph 隔离探针，tool_result 逐字）：

```
intermediate_is_npu FULLGRAPH ERR: Data-dependent branching
tensor_dims FULLGRAPH ERR: Could not extract specialized integer from data-dependent expression u0 (unhinted: u0).  (Size-like symbols: none)
```

- npu_fused_infer_attention_score_v2 的 actual_seq_qlen/kvlen 形参 schema 为 SymInt[]? 而非 Tensor；图模式下传 Tensor 会触发 aten._local_scalar_dense 中断（HYV4 decode 每层 1 次、L=4 共 4 次），传 list[int] 则 0 中断。
  - schema 逐字（`_schema` 打印截取）：

```
npu::npu_fused_infer_attention_score_v2(Tensor query, Tensor key, Tensor value, *, Tensor? query_rope=None, Tensor? key_rope=None, Tensor? pse_shift=None, Tensor? atten_mask=None, SymInt[]? actual_seq_qlen=None, SymInt[]? actual_seq_kvlen=None, Tensor? block_table=None
```

  - npugraph_ex 侧对 FA v2 的 replay 更新支持（`acl_graph.py` 逐字，说明 list[int] 形态可在 replay 期刷新、不需重编译）：

```
if hasattr(torch.ops.npu, "npu_fused_infer_attention_score_v2"):
    _REPLACE_FUNC_MAP.update({torch.ops.npu.npu_fused_infer_attention_score_v2.default:
        StaticWorkspaceReplaceFunc(
            get_workspace=torch.ops.npu._npu_fused_infer_attention_score_v2_get_max_workspace.default,
            out_operator=torch.ops.npu.npu_fused_infer_attention_score_v2.out,
            workspace_keys=["workspace"],
            output_keys=["attention_out", "softmax_lse"],
            updated_param_keys=["actual_seq_qlen", "actual_seq_kvlen"],
        )
    })
```

- 本机（CANN 9.1.0、torch_npu 2.12.0、protobuf/google 包未安装）上 GE（torchair/backend npu）因 ge_ir_pb2.py 调 importlib.metadata.version("protobuf") 抛 PackageNotFoundError 而不可用；npugraph_ex 后端可用（tiny Linear+ReLU 捕获成功）。
  - GE 失败逐字行：`importlib.metadata.PackageNotFoundError: No package metadata was found for protobuf`
  - npugraph_ex 成功逐字行：`NPUGRAPH_EX_OK (1, 64) 15.829185485839844`
- HYV4 paged decode 前向（fusion 全开、L=4）在 torch._dynamo.explain 下实测 GRAPH_COUNT=30 / GRAPH_BREAK_COUNT=29，中断归为六类：A 中间张量 .is_npu、B FA actual_seq_* 传 Tensor、C 动态 kv_len 切片/mask、D Runner 每步重建输入张量、E eager MoE torch.nonzero、F 函数体内 import torch_npu。其中：
  - A（fundamental）：`HYV4RMSNorm` L94、`_apply_rotary_half_packed` L193、`HYV4MLP` L704、`HYV4TopkRouter` L729-731、`HYV4Experts` L791 的 `if ... .is_npu:`；
  - B：`_forward_paged` FA 调用把 `actual_seq_qlen/kvlen` 按 Tensor 传入 `SymInt[]?` 形参 → `aten._local_scalar_dense`（explain 下每层 1 次、共 4 次）；
  - C：indexer `cache[...][:kv_len]` 与每步 `[1,1,1,kv_len]` mask 的动态 shape；
  - D：Runner 每步重建 `slot_mapping/actual_seq_*/position_ids/mask` 张量（identity/shape guard）；
  - E：仅 `fuse_moe_experts=False` 时 eager MoE `torch.nonzero`（L=2 探针中可见 `aten.nonzero.default` Dynamic shape operator 中断；融合全开时不出现）；
  - F：函数体内 `import torch_npu`（7 处）。
- 可区分解释分支：A/B/C 为 fundamental、需改模型代码；D 需改 Runner（预分配原地更新）；E 用融合开关规避；F 外提 import。`.device.type` 在中间张量上静态可解析是 A 的判别要点；`list[int]` vs Tensor 是 B 的判别要点（`list_dims` 0 break vs `tensor_dims` data-dependent expression）。
- 未验证推断：GE 是否在补装 protobuf wheel 后即可用（离线环境未提供 wheel，未验证）；六类之外是否存在仅在真实 npugraph_ex 编译（而非 explain）下暴露的隐藏中断（由[HYV4 Decode 29 处 Dynamo 图中断消除配方：npugraph_ex 整图捕获 + 0 重编译 + 同会话 decode 4×提速](hyv4_decode_dynamo_npugraph_ex.md)的捕获结果间接否定：1 graph/0 break）。

## 验证信号

仅列本组来源观测轨迹内实际观测到的信号（单次观测、单卡、随机权重）：

- `torch._dynamo.explain` decode 前向：GRAPH_COUNT=30 / GRAPH_BREAK_COUNT=29（融合全开、L=4）；L=2 首轮 16/15。
- fullgraph=True 首报 `attempted to jump with GetAttrVariable(TensorVariable(), is_npu)`；fullgraph=False 可跑（~11.38 ms/步含 warmup，非干净图，不可作收益定论；eager 12.9 ms，单次观测）。
- 五写法探针、`intermediate_is_npu`/`tensor_dims` 隔离探针、FA v2 schema（`SymInt[]?`）、`acl_graph.py` `updated_param_keys` 如上逐字。
- 后端探针：`NPUGRAPH_EX_OK`（npugraph_ex 可用）；GE `PackageNotFoundError: No package metadata was found for protobuf`（不可用）。
- 证据等级：以上均为本机单次/少量次数 tool_result 观测；宿主存在多组重载作业，绝对耗时漂移大，性能数字不作为本卡依据。

## 适用与失效边界

- 结论限定：Ascend950PR_9589 + CANN 9.1.0 + torch 2.12.0+cpu + torch_npu 2.12.0；`.is_npu` 判别依赖 Dynamo 对 TensorVariable 属性的静态解析行为，torch/Dynamo 版本变化可能改变结论。
- GE 不可用结论仅限"protobuf 未安装"这一环境；装齐 protobuf 后需重新探测。
- `SymInt[]?` 传 Tensor 的中断行为在 npugraph_ex（aclgraph 捕获）路径成立；torchair/GE 的 FA 接口（`torchair.ops`）按参考仓库（gemma_4）记载可接受 Tensor 形态，属不同后端、不同结论。
- DSA indexer 的"当前 no-op"判断仅当 `index_topk(2048) >= kv_len` 成立；kv_len > 2048 时跳过 indexer 不再等价，需切 sparse FA 路径。
- eager MoE `nonzero` 中断仅在融合开关关闭时出现；图模式必须与 MoE 融合协同。
- 停止条件：若 profiling 显示 decode 已 compute-bound（融合后），图模式收益只剩 launch 开销空间，投入产出需重估（本组来源观测分析当时的倾向性结论即"先 profiling、暂缓全图改造"，后续经用户决策才实施）。
