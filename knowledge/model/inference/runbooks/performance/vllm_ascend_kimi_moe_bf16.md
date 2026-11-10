---
{
  "type": "Runbook",
  "title": "vllm-ascend Kimi K3 MoE 路由门控 bf16 化：Cast 定位、跨分支移植与默认开启（本次实现）",
  "description": "K3 MoE 路由的 Cast(DT_BF16→FLOAT)+fp32 MatMulV3 定位于 vllm_ascend/ops/fused_moe/gate_linear.py（fp32 根源是构造参数 params_dtype=torch.float32），csrc 证据确认 MoeGatingTopK 原生接受 DT_BF16。本次实现将 main 分支的 bf16 路由改动按 releases/v0.27.1rc 结构移植为 4 文件 +77/-7（用户提交 895b8ba03），再简化为 K3 专属默认开启（无条件 enable_bf16_compute()，删除环境变量）。本轨迹内未做 NPU 运行验证与性能测量。",
  "tags": [
    "task.implementation",
    "topic.model_serving",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "agnostic"
  ]
}
---

# vllm-ascend Kimi K3 MoE 路由门控 bf16 化：Cast 定位、跨分支移植与默认开启（本次实现）

## 适用场景

- 框架/模型：vllm-ascend（昇腾 NPU 硬件插件）上的 Kimi K3（model_type `kimi_linear`，Stable LatentMoE，896 experts / Top-16）推理。
- 分支/版本：本卡的实现落在 `releases/v0.27.1rc` 分支（对齐上游 vLLM 0.27.1；git describe `v0.19.1rc1-1942-g13329edfc`）；同一改动在 main 分支的对应提交为 `7550790a8 [MoE] Delete cast`。两分支的 gate_linear.py 结构不同（main 为 #16189 重写版，release 保留 #9617 原始形态 `super().__init__ + force_fp32_compute=True`），不能直接 cherry-pick。
- 目标：消除 K3 MoE 路由门控热路径上的 Cast(DT_BF16→FLOAT) 与 fp32 MatMulV3，让路由 GEMM 以 bf16 计算并直接供 MoeGatingTopK 消费。
- 缺失信息：本轨迹无 NPU 环境，硬件口径为讨论口径（A5/A3，见失效边界）；无精度与性能数据。

## 触发与观测

用户在 K3 profile 中观测到 MoE 层存在 Cast(DT_BF16→FLOAT) + MatMulV3 算子对，后续算子为 DynamicMxQuant / QuantBatchMatmulV3 / MoeGatingTopK。

定位结论（修正过一次的最终版本）：**K3 MoE 路由的 Cast(DT_BF16→FLOAT) 与 fp32 MatMulV3 定位于 vllm_ascend/ops/fused_moe/gate_linear.py 的 forward，fp32 根源是构造参数 params_dtype=torch.float32；K3 走外挂 gate 路径（kimi_k3.py 的 gate 调用点），不在 fused_moe.py 的 internal-router 路径上。**

- 最初怀疑的 `fused_moe.py:391/393 _compute_router_logits`（internal-router 路径，`hidden_states_fp32 = ... .float()` + `F.linear(hidden_states_fp32, gate.weight_fp32)`）对 K3 不执行：K3 的 `AscendKimiMoE` 未向 FusedMoEFactory 传 `gate=`，`is_internal_router=False`。
- K3 实际执行：`kimi_k3.py` 中 `router_logits, _ = self.gate(hidden_states)`，上游 `GateLinear` 经 CustomOp 替换为 `AscendGateLinear`（release 分支 utils.py:744 按 `is_deepseek_mla` 条件注册；上游 model_type 列表含 `kimi_linear` 与 `k3_dspark`，故 K3 满足条件）。
- MoeGatingTopK 的输入是 gate 的直接输出（路由分支），不是 QuantBatchMatmulV3 的输出；hidden_states 分支（DynamicMxQuant + latent down）与路由分支在 `AscendKimiMoE.forward` 处分叉，profile 时间序相邻不等于数据串联。

修改前（releases/v0.27.1rc 的 gate_linear.py，#9617 原始形态，T367 逐字）：

```
54:     def forward(self, x: torch.Tensor):
55:         # TODO: Remove this workaround after upgrading to a vLLM version that
56:         # no longer forces router logits to bf16 via
57:         # self.gate.set_out_dtype(torch.bfloat16).
58:         if x.dtype != torch.float32:
59:             x = x.to(torch.float32)
60:
61:         output, output_bias = ReplicatedLinear.forward(self, x)
62:
63:         return output, output_bias
```

## 探针与操作

可行性探针（均为只读代码检查）：

1. csrc 算子 dtype 注册（grep `op_host` 下 dtype/DT_）：
   - `moe_gating_top_k_def.cpp:24/30/36` 注册 x/bias/y dtype 为 `{ge::DT_FLOAT16, ge::DT_FLOAT, ge::DT_BF16}`；
   - tiling 校验明确 "only supports float32, half, bf16"。
   结论：**MoeGatingTopK 的 csrc 算子注册 dtype 含 ge::DT_BF16（moe_gating_top_k_def.cpp:24/30/36），bf16 logits 可直接进入路由算子，无需保留 Cast。**（T153 逐字节选）

```
  Line 24:             .DataType({ge::DT_FLOAT16, ge::DT_FLOAT, ge::DT_BF16})

  Line 30:             .DataType({ge::DT_FLOAT16, ge::DT_FLOAT, ge::DT_BF16})

  Line 36:             .DataType({ge::DT_FLOAT16, ge::DT_FLOAT, ge::DT_BF16})
```

2. 数值面评估：输入 hidden_states 本身是 bf16，fp32 cast 不增加信息；gate 权重 checkpoint 原生 bf16（`params_dtype=torch.float32` 只是无损上采样）；NPU Cube bf16 MatMul 内部 fp32 累加。唯一数值差异是 logits 输出的 bf16 舍入（near-tie 分数可能翻转专家选择）。仓内前科：`ops/linear.py:110` 注释 "must use fp32 to avoid accuracy degradation in dsv4"（#9617 的精度担忧来自 DeepSeek 类模型）。

实施操作（两轮）：

第一轮（main 分支，后被用户提交为 `7550790a8`）：envs.py 新增开关、gate_linear.py 读开关切换 params_dtype、fused_topk_router.py bias dtype 适配；随后按"仅 K3 生效"重构为 `enable_bf16_compute()` 显式 opt-in（模型代码调用，非全局 CustomOp 生效）。

第二轮（releases/v0.27.1rc 移植）：**本次实现将 main 分支的 bf16 路由改动按 releases/v0.27.1rc 分支结构移植为 4 文件 +77/-7（envs.py、gate_linear.py、kimi_k3.py、fused_topk_router.py），移植版由用户提交为 895b8ba03 [MoE] Delete cast。**（T482 `git diff --stat` 客观输出：4 files changed, 77 insertions(+), 7 deletions(-)；T511 `git log` 显示 `895b8ba03 [MoE] Delete cast`）

移植时的分支适配要点：

- envs.py：release 分支无 `_strict_binary_env` helper，按本分支惯例（与 `VLLM_ASCEND_KIMI_K3_ATTNRES_FUSED_ENABLED` 同构）写为（C462 逐字）：

```
    "VLLM_ASCEND_ENABLE_GATE_BF16": lambda: bool(int(os.getenv("VLLM_ASCEND_ENABLE_GATE_BF16", "0"))),
```

- gate_linear.py：保留本分支的 `super().__init__ + force_fp32_compute=True` 构造（不能照搬 main 的跳过上游构造版本），追加 `use_bf16_compute` 标志、`enable_bf16_compute()` 方法与 `info_once` 日志（T486 逐字）：

```
74:         if self.use_bf16_compute:
75:             return
76:         self.use_bf16_compute = True
77:         self.weight = torch.nn.Parameter(
78:             self.weight.data.to(dtype=torch.bfloat16),
79:             requires_grad=self.weight.requires_grad,
80:         )
81:         logger.info_once(
82:             "AscendGateLinear: bf16 router compute enabled (removes the Cast(BF16->FP32) and the fp32 MatMulV3 from the MoE router hot path)."
83:         )
84:
85:     def forward(self, x: torch.Tensor):
86:         if self.use_bf16_compute:
87:             if x.dtype != self.weight.dtype:
88:                 x = x.to(self.weight.dtype)
89:         elif x.dtype != torch.float32:
90:             # TODO: Remove this workaround after upgrading to a vLLM version that
91:             # no longer forces router logits to bf16 via
92:             # self.gate.set_out_dtype(torch.bfloat16).
93:             x = x.to(torch.float32)
94:
95:         output, output_bias = ReplicatedLinear.forward(self, x)
96:
97:         return output, output_bias
```

- kimi_k3.py：import + opt-in（env 唯一读取点）。
- fused_topk_router.py：`_bias_for_logits_dtype` 一次性缓存 + `bias_opt` 调用点替换（本分支无 hash vision 分支，改动更小；详见[vllm-ascend MoE 路由 logits 切 bf16 时的 MoeGatingTopK bias dtype 硬约束与休眠 Parameter 重赋值缺陷](../precision/vllm_ascend_moe_logits_bf16.md)）。

第三轮（默认开启简化，工作区未提交）：**随后按用户要求简化为默认开启：kimi_k3.py 在 AscendKimiMoE 构造中无条件调用 self.gate.enable_bf16_compute()（仅保留 isinstance(self.gate, AscendGateLinear) 守卫），删除 VLLM_ASCEND_ENABLE_GATE_BF16 环境变量条目；默认开启版为工作区未提交改动（相对 895b8ba03 增量 3 文件 +11/-21）。**（T507 `git diff --stat`：3 files changed, 11 insertions(+), 21 deletions(-)）

kimi_k3.py 最终形态（T515 逐字）：

```
323:         self.gate.e_score_correction_bias = nn.Parameter(torch.empty(num_experts, dtype=torch.float32))
324:         if isinstance(self.gate, AscendGateLinear):
325:             # Run the router gate GEMM in bf16, matching upstream's bf16
326:             # router logits: removes the Cast(BF16->FP32) and the fp32
327:             # MatMulV3 from the MoE hot path. Scoped to Kimi K3 only;
328:             # other models keep the fp32 gate.
329:             self.gate.enable_bf16_compute()
```

## 机制与判别

- 默认开启的论证（会话内论证，非运行验证）：上游 vLLM 参考实现本来就是 bf16 路由（gate_linear.py TODO 注释所述 "forces router logits to bf16"），vllm-ascend 的 fp32 是比参考更保守的行为；opt-in 仅存在于 `AscendKimiMoE`（DeepSeek/GLM 等其他模型保持 fp32 gate）；本分支有默认开启先例（`VLLM_ASCEND_KIMI_K3_ATTNRES_FUSED_ENABLED`）。
- 影响面判别：`AscendGateLinear` 是 CustomOp 全局替换，若在 `__init__` 里直接读环境变量，任何使用 GateLinear 的模型开开关都会变 bf16；改为模型代码显式 opt-in 后其他模型结构上不可能被影响。
- 生效确认信号（未在本轨迹运行，仅供验证）：启动日志 grep `bf16 router compute enabled`（info_once 每进程一行，因 `AscendKimiMoE.__init__` 每模型 92 层 MoE 各执行一次）；或 profile 对比 flag on/off 下 moe.gate 段是否仍有 [T,7168] 的 Cast。
- 代价与提醒：失去运行时回退开关（线上出问题需改代码重部署）；bf16 舍入会翻转 near-tie 专家选择，精度 eval 必须做（统计 bf16/fp32 两路径 topk_ids 一致率或跑 eval）；`_bias_cast_cache` 在 RL `update_weights` 更新 bias 时会陈旧（纯推理不受影响）。

## 验证信号

本轨迹内实际观测到的客观信号（全部为代码级，Windows 本机、无 NPU）：

- T87/T367：修改前 gate_linear.py 全文（main/release 两分支的 fp32 Cast 原文）。
- T153：csrc moe_gating_top_k dtype 注册与 tiling 校验证据。
- T427/T431/T439/T443：从上游 vLLM 拉取的 GateLinear / `is_deepseek_mla` 源码（model_type 列表含 `kimi_linear`、`k3_dspark`）。
- T482：移植版 `git diff --stat` = 4 files, +77/-7。
- T511：`git log` 显示用户已提交 `895b8ba03 [MoE] Delete cast`（895b8ba0395a8c82f9e172f12ca316bf2eb4dbda）。
- T507：默认开启版相对 895b8ba03 增量 `git diff --stat` = 3 files, +11/-21。
- T515/T486：默认开启版 kimi_k3.py 与 gate_linear.py 最终文件回读。

未观测到的信号（如实说明）：**本轨迹内未做 NPU 运行验证与性能测量（本机无可用 Python，py_compile 退出码 9009），A5 走 torch_npu.npu_moe_gating_top_k 内置算子、其 bf16 支持在仓内无法验证，须先在 A5 机上做算子冒烟。**（T205 `exit=9009`；T284 device_op.py:993 的 A5 内置算子调用；T298 硬件族分派）

## 适用与失效边界

- 适用：vllm-ascend releases/v0.27.1rc（及结构相同的分支）上的 Kimi K3 推理；`sample_from_anchor` 等路由超参不受本改动影响。
- 失效/风险边界：
  1. 精度：bf16 logits 舍入改变 896 选 16 + grouped topk 的专家选择；DSV4 曾因路由精度劣化引入 fp32（linear.py:110）。上生产前必须跑精度 eval。
  2. 硬件：A2/A3 走仓内 csrc 算子（DT_BF16 已注册、可静态验证）；A5 走 `torch_npu.npu_moe_gating_top_k` 内置算子，bf16 支持未验证——先做单算子冒烟（bf16 x + bf16 bias 调 `torch_npu.npu_moe_gating_top_k`），报 dtype 错误即停止，回退方案是保留 logits→fp32 的小 Cast（[T,896]，仍有净收益）。
  3. bias 适配是成套改动的一部分（见[vllm-ascend MoE 路由 logits 切 bf16 时的 MoeGatingTopK bias dtype 硬约束与休眠 Parameter 重赋值缺陷](../precision/vllm_ascend_moe_logits_bf16.md)），只改 gate 不改 router 会在第一次 MoE forward 失败。
  4. 运行时权重更新（RL）场景 `_bias_cast_cache` 会陈旧，需要补缓存失效。
  5. 两分支结构不同，向其他分支移植时须重做分支适配（envs helper、gate 构造方式、router 分支形态）。
  6. 本卡全部结论为"本次实现"（代码级实现与 diff 校验），无性能结论、无通用加速承诺。
