---
{
  "type": "Runbook",
  "title": "LLM Decode 图中断定位：`torch._dynamo.explain` 紧凑实例探针与 npugraph_ex 直接编译复现",
  "description": "为判断 LLM eager 代码能否入图，用本模型 1 层紧凑实例（FP8、融合算子全开、随机权重）跑 `torch._dynamo.explain` 可稳定复现 decode 路径的 graph_break_count 并给出可区分的中断位置（`.item()`、FA v2 Tensor 长度→`aten._local_scalar_dense`、`repeat_interleave` 数据依赖形状）；再对未改造代码直接 `torch.compile(backend=\"npugraph_ex\")` 验证 fullgraph=True 的 guard 失败与 fullgraph=False 的 aclrtMemcpy 捕获失败。结合 op schema（`SymInt[]?`）与 torchair/protobuf 可导入性可判别后端选择与修复方向。",
  "tags": [
    "task.debugging",
    "topic.compilation",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-03T12:00:00Z",
  "platforms": [
    "950"
  ]
}
---

# LLM Decode 图中断定位：`torch._dynamo.explain` 紧凑实例探针与 npugraph_ex 直接编译复现

## 适用场景

- 模型/框架：任意准备适配 npugraph_ex/GE 图模式的 NPU LLM eager 代码（本例：Hunyuan-A13B-Instruct-FP8，FP8 + 融合算子 + Paged KV + FA v2 TND 路径）。
- 平台/版本：Ascend950PR_9589 单卡；CANN 9.1.0；torch 2.12.0+cpu / torch_npu 2.12.0；torchair（GE）因环境缺 protobuf 不可导入。
- 目标与工作负载：判断 eager decode 路径能否入图、定位全部 graph break、并判别后端（npugraph_ex vs GE）可用性。

## 触发与观测

- 触发：图模式适配阶段，需先确认当前代码的图中断点。直接 `torch.compile(backend="npugraph_ex")` 即失败（见下）。
- 观测一（explain 探针）：小模型 `torch._dynamo.explain` 输出（原文，含位置）：

```
===SUMMARY=== graph_break_count = 12 graph_count = 13
num_break_reason_entries = 7

### BREAK 0 : Unsupported Tensor.item() call with capture_scalar_outputs=False
    at modeling_hunyuan.py line 875 -> seq_len = int(position_ids.max().item()) + 1

### BREAK 1 : Error when attempting to resolve op packet
    at modeling_hunyuan.py line 803 -> hidden_states = self.self_attn(
    at modeling_hunyuan.py line 681 -> attn_output = self._fa_forward(
    at modeling_hunyuan.py line 720 -> attn_output, _ = torch.ops.npu.npu_fused_infer_attention_score_v2(

### BREAK 2 : Error when attempting to resolve op packet
    at modeling_hunyuan.py line 681 -> attn_output = self._fa_forward(
    at modeling_hunyuan.py line 720 -> attn_output, _ = torch.ops.npu.npu_fused_infer_attention_score_v2(

### BREAK 3 : Error when attempting to resolve op packet
    at modeling_hunyuan.py line 720 -> attn_output, _ = torch.ops.npu.npu_fused_infer_attention_score_v2(

### BREAK 4 : Dynamic shape operator
    at modeling_hunyuan.py line 820 -> hidden_states = self.mlp(normed)
    at modeling_hunyuan.py line 561 -> return self._fused_forward(hidden_states)
    at modeling_hunyuan.py line 528 -> row_is13 = torch.repeat_interleave(self.w13_input_scale, tokens_per_expert)  # [M]

### BREAK 5 : Dynamic shape operator
    at modeling_hunyuan.py line 528 -> row_is13 = torch.repeat_interleave(self.w13_input_scale, tokens_per_expert)  # [M]

### BREAK 6 : Dynamic shape operator
    at modeling_hunyuan.py line 539 -> row_is2 = torch.repeat_interleave(self.w2_input_scale, tokens_per_expert)
```

- 观测二（直接编译复现，原文）：

```
=== TEST 2: npugraph_ex on tiny model decode ===
npugraph_ex fullgraph=True: FAIL UserError: Consider annotating your code using torch._check*(). Could not guard on data-dependent expression u0 + 1 > 0 (unhinted: u0 + 1 > 0).  (Size-like symbols: none)

consider using data-dependent friendly APIs such as guard_or_false, guard_or_true and statically_known_true.
Caused by: if seq_len > self.m
npugraph_ex fullgraph=False: FAIL RuntimeError: copy_between_host_and_device_opapi:../torch_npu/csrc/aten/ops/op_api/CopyKernelOpApi.cpp:55 NPU function error: aclrtMemcpy, error code is 107030
```

- 观测三（op schema）：`print(torch.ops.npu.npu_fused_infer_attention_score_v2.default._schema)` 显示 `SymInt[]? actual_seq_qlen=None, SymInt[]? actual_seq_kvlen=None`。
- 观测四（GE 不可用）：`import torchair` 报（原文）：

```
importlib.metadata.PackageNotFoundError: No package metadata was found for protobuf
An error occurred when import `torchair` and the above is the specific error message.
This error message was generated when import torchair, but thrown asynchronously here.
Please check the error message above.
```

## 探针与操作

探针一（explain，用本模型 1 层紧凑实例：FP8、融合全开、随机权重、`HunYuanConfig(vocab_size=512, hidden_size=1024, ..., num_experts=4, moe_topk=[2], rope_scaling={"type": "dynamic", "alpha": 1000.0, "factor": 1.0}, ...)`；注意 transformers 5.x 要求 dynamic rope 带 `factor` 键，否则构造期 KeyError）：

```
import torch._dynamo as dynamo
dynamo.config.cache_size_limit = 1
try:
    explanation = dynamo.explain(fn)(input_ids, position_ids, past, meta)
    print("===SUMMARY=== graph_break_count =", explanation.graph_break_count, "graph_count =", len(explanation.graphs))
```

再遍历 `explanation.break_reasons` 打印 `reason` 与 `user_stack` 中本模型文件的行号/源码行即可得到观测一。探针二（直接编译）：同一实例上 `torch.compile(model.decode或model, backend="npugraph_ex", fullgraph=True/False)` 分别跑一步 decode，得到观测二。探针三（schema）：`torch.ops.npu.<op>.default._schema` 直接打印 ATen 签名。探针四（后端可用性）：`import torch_npu.dynamo.npugraph_ex` / `import torchair` 分别试导入并 `importlib.metadata.version("protobuf")`。

失败路线（不可采用）：在系统 python（未 source CANN env.sh）跑 `import torch_npu` 会报 `libhccl.so: cannot open shared object file`——须先 source env.sh（自动探测含 `lib64/libhccl.so` 与 ascend950 `ops_nn` 的 CANN 安装）。

## 机制与判别

- 探针：用本模型 1 层紧凑实例（FP8、融合全开、随机权重）跑 `torch._dynamo.explain` 可稳定复现 decode 路径 `graph_break_count = 12`（graph_count=13，去重 7 条原因），并给出可区分的中断位置：`Tensor.item()`（modeling_hunyuan.py:875 `seq_len = int(position_ids.max().item()) + 1`）、FA v2 传 Tensor 长度（:720，调用链 803→681→720，`aten._local_scalar_dense`）、`aten.repeat_interleave.Tensor` 数据依赖形状（:528/:539）。
- 复现（直接编译）：对未改造代码 `torch.compile(backend="npugraph_ex")`，fullgraph=True 报 `Could not guard on data-dependent expression u0 + 1 > 0 ... if seq_len > self.max_seq_len_cached`（RoPE 分支 guard 失败），fullgraph=False 在 capture 阶段报 `aclrtMemcpy, error code is 107030`——两种模式都不可用，须先修复图中断。
- 机制判别：FA v2 的 ATen schema 将 `actual_seq_qlen`/`actual_seq_kvlen` 声明为 `SymInt[]?`，eager 下传 Tensor 须经 `aten._local_scalar_dense` 转 host 标量，因而打断图；修复方向是 Decode 传 host `List[int]`。（仓内参考 `models/hy3/models/modeling_hy_v3.py` 的 npugraph_ex decode 分支正是从 `ForwardMetaData` 取 `actual_seq_lengths_cu_list_q`/`actual_seq_lengths_list_kv` 传 list，eager/GE 分支传 Tensor。）
- 环境分支：本环境 `import torchair` 因缺 `google.protobuf`（`importlib.metadata.PackageNotFoundError: No package metadata was found for protobuf`）失败，GE 图模式不可评估；`torch_npu.dynamo.npugraph_ex` 可直接 import，构成后端选择（主选 npugraph_ex）的判据。
- 可区分解释分支：fullgraph=True 的 guard 失败由 `.item()` 派生的动态 `seq_len` 连锁触发（同一 `.item()` 若只存在于 eager 分支则 fullgraph 不再失败，实施后验证成立）；fullgraph=False 的 `aclrtMemcpy` 失败说明 capture 阶段存在 host-device 拷贝（`aten._local_scalar_dense` 路径），单靠放宽 fullgraph 掩盖不了。
- 未验证推断：GE 路径修复后的行为（protobuf 补齐前不可评估）。

## 验证信号

均在本机（Ascend950PR_9589 单卡、CANN 9.1.0、torch/torch_npu 2.12.0）实测，证据等级：探针脚本 stdout / 退出码。

- explain 探针两次运行稳定复现 `graph_break_count = 12 graph_count = 13`（analyzer 事件 163/167/171）；修复后同一探针 `graph_break_count = 0 graph_count = 1`（implementer 事件 227、reviewer 独立复跑事件 105）——探针结论在全模型捕获上得到验证（`compiling Decode with npugraph_ex (fullgraph=True, dynamic=True)` 成功）。
- 直接编译失败两次复现（事件 201/205）；schema 打印（事件 89）与 break 位置吻合。
- 单次观测口径；探针为小模型（1 层、随机权重），全模型行为由实施/审查轨迹闭环验证。

## 适用与失效边界

- 适用：入图前诊断——先 explain 定位全部中断，再直接编译验证 fullgraph 两种模式，最后查 op schema 决定传参形态。
- 失效/风险：紧凑实例用随机权重，覆盖控制流/形状路径但不覆盖数值正确性；`dynamo.config.cache_size_limit` 需调低避免多次 trace 干扰。
- 环境边界：torchair/GE 依赖 protobuf；缺 protobuf 时只能选 npugraph_ex。GE 修复方案（补 protobuf + 传 Tensor + `dynamic=False`）在本轨迹未验证。
- 停止/回退条件：explain 显示 0 break 且 fullgraph 捕获成功即可进入性能/精度验证；否则按"触发与观测"分类逐项修复。
