---
{
  "type": "Runbook",
  "title": "npu_clipped_swiglu 的非对称截断参数映射与 Step3/HYV4 样本精度验证",
  "description": "npu_clipped_swiglu 以 alpha=1.0、bias=0.0、interleaved=False、limit=截断值调用时与 HF 风格 _apply_gate（gate.clamp(max=limit) 后 silu、up.clamp(±limit)）在 所测 fp32 样本逐位相等；bf16 样本 max_abs=0.5，不能由该探针证明全域 ≤1 ULP；CANN 官方公式 A.clamp(min=None,max=limit)、B.clamp(-limit,limit)、y=A*sigmoid(alpha*A)*(B+bias) 与该非对称语义完全一致，gate 分支不做下界截断（gate<−15 区域输出 ~3.5e-9 吻合）。",
  "tags": [
    "task.implementation",
    "topic.precision",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "950"
  ]
}
---
# npu_clipped_swiglu 的非对称截断参数映射与 Step3/HYV4 样本精度验证

## 适用场景

- 模型/框架：路由专家 SwiGLU 带 ±limit 截断的 MoE 推理（HYV4 `swiglu_limit=10.0` 的 `_apply_gate`、Step-3.7-Flash `L43/44` 同风格、`cann-recipes-infer/module/fuse_moe_gmm.py` 的 clamped-SwiGLU 分支）；作为 `npu_swiglu`（无 clamp）不能覆盖该语义时的替代融合算子。
- 平台/版本：Ascend950PR_9589 单卡、CANN 9.1.0、torch_npu 2.12.0。`npu_clipped_swiglu` 的本地 docstring「支持的型号」仅列 Atlas A2 推理系列 / Atlas A3 推理系列，但 ascend950 kernel 目录存在 `ops_nn/clipped_swiglu`，本组来源观测以运行时数值复核为准。
- 工作负载：bf16 为主（fp32 亦支持）；权重布局 [gate_half | up_half] 前后切分（非 gpt_oss 交织），`interleaved=False`。

## 触发与观测

被替换的参考语义（`models/modeling_hy_v4.py` 的 `_apply_gate`，事件 281 原文 875–879 行）：

```
875:     def _apply_gate(self, gate_up: torch.Tensor) -> torch.Tensor:
876:         gate, up = gate_up.chunk(2, dim=-1)
877:         gate = gate.clamp(min=None, max=self.swiglu_limit)
878:         up = up.clamp(min=-self.swiglu_limit, max=self.swiglu_limit)
879:         return F.silu(gate) * up
```

注意这是**非对称**截断：gate 只做上界 clamp、先 clamp 后 silu；up 双侧 clamp。若直接用不带 clamp 的 `npu_swiglu`（事件 211：`npu_swiglu (no clamp) cos vs ref=0.99975967`，明显低于 clipped 版本 0.99999619），数值语义不满足。阶段 3.1 探针（单算子，256×1536 bf16、输入 ×3.0 覆盖截断区，事件 211）首次观测：`clipped_swiglu ok shape=(256, 768) cos=0.99999619 maxdiff=5.000e-01`。

reviewer 复核时曾在 clamp 边界看到 `maxdiff=5.000e-01`（事件 152：`clamp-edge: maxdiff=5.000e-01 bits_equal=False`），定位后（事件 156）为 bf16 大值 1 ULP：`gate= 10.5 up= 7.875 ref= 79.0 fused= 78.5`（gate 被 clamp 到 10 后 silu(10)*7.875≈78.75，bf16 相邻表示为 79.0/78.5）。

## 探针与操作

阶段 3.1 探针的等价性测试（来源记录 事件 45，`.scratch/moe_fusion_probe.py` 原文）：

```
41: print("\n=== npu_clipped_swiglu vs manual HYV4 gate (alpha=1, limit=10, bias=0, interleaved=False) ===")
42: gu = torch.randn(256, 2 * 768, dtype=torch.bfloat16, device=dev) * 3.0
43: gate, up = gu.chunk(2, dim=-1)
44: ref = F.silu(gate.clamp(max=lim)) * up.clamp(-lim, lim)
45: try:
46:     out = torch_npu.npu_clipped_swiglu(gu, dim=-1, alpha=1.0, limit=lim, bias=0.0, interleaved=False)
47:     cos = F.cosine_similarity(ref.flatten().float(), out.flatten().float(), dim=0).item()
48:     md = (ref.float() - out.float()).abs().max().item()
49:     print(f"clipped_swiglu ok shape={tuple(out.shape)} cos={cos:.8f} maxdiff={md:.3e}")
```

reviewer 的 fp32/bf16 双精度判别探针（来源记录 事件 159，命令原文核心段）：

```
for dt in (torch.float32, torch.bfloat16):
    g = torch.linspace(-25,25,2000,dtype=dt,device="npu:0").reshape(50,40)
    u = torch.linspace(-15,15,2000,dtype=dt,device="npu:0").reshape(50,40)
    x = torch.cat([g,u],dim=-1)
    gate,up = x.chunk(2,-1)
    ref = F.silu(gate.clamp(min=None,max=10.0))*up.clamp(min=-10.0,max=10.0)
    fused = torch_npu.npu_clipped_swiglu(x,dim=-1,alpha=1.0,limit=10.0,bias=0.0,interleaved=False)
    d=(ref.float()-fused.float()).abs()
```

模型内调用（GMM 输出上）：`torch_npu.npu_clipped_swiglu(hidden, dim=-1, alpha=1.0, limit=self.swiglu_limit, bias=0.0, interleaved=False)`（[HYV4 五点 torch_npu 融合替换（MoE init_routing_v2→grouped_matmul→clipped_swiglu→grouped_matmul→finalize_routing 等）的模块级/整网验证与同会话 A/B 性能](../performance/hyv4_torch_npu_moe_init_routing_v2_grouped_matmul.md) 机制工件 856–859 行）。

## 机制与判别

- 结论一（等价性）：npu_clipped_swiglu(x, dim=-1, alpha=1.0, limit=10.0, bias=0.0, interleaved=False) 与 F.silu(gate.clamp(min=None,max=10.0))*up.clamp(-10.0,10.0) 在本次 fp32 采样输入上逐位相等（maxabs=0.000e+00、bits_equal=True），所测 bf16 样本 maxabs=5.000e-01（日志 max_ulp=0.99 实际按 abs(ref)*2^-7 归一化，并非精确 ULP 距离）。锚点：来源记录 事件 159（探针命令）；信号：事件 160（`torch.float32 maxabs=0.000e+00 max_ulp=0.00 bits_equal= True` / `torch.bfloat16 maxabs=5.000e-01 max_ulp=0.99 bits_equal= False`）。
- 结论二（非对称语义）：非对称截断语义吻合：gate 分支仅上界截断（无下界），gate<−15 区域 fused 输出 ~3.47e-9 与参考一致，与 CANN 官方公式 A = A.clamp(min=None, max=limit) 精确对应。锚点：来源记录 事件 106（官方 docstring）；信号：事件 160（`gate<-15 count 400 ref/fused sample 3.471985809966327e-09 3.471985809966327e-09`，fp32/bf16 两行均吻合）。官方公式原文（事件 106）：
- 结论三（规模观测）：单算子规模（256×1536，bf16，输入 ×3.0 覆盖截断区）cos=0.99999619、maxdiff=5.000e-01（bf16 大值 1 ULP 量级）；接入 MoE experts 整链路后模块级 cos 0.99998295–0.99998409。锚点：来源记录 事件 211；信号：同事件 + 来源记录 事件 143（`fusion_modules.json` moe_experts_decode/prefill）。

官方公式依据（torch_npu `_op_plugin_docs.py`「npu_clipped_swiglu」条目，事件 106 原文）：

```
11745:                                                   当 interleaved 为 false 时，表示前后切分：h = x.shape[1] // 2, A = x[ : , : h], B = x[ : , h : ]
11746: (4)根据输入参数 alpha、limit、bias 进行变体SwiGlu计算，公式如下：A = A.clamp(min=None, max=limit), B = B.clamp(min=-limit, max=limit)
11747:                                                                 y_glu = A * sigmoid(alpha * A)
11748:                                                                 y = y_glu * (B + bias)
```

判别要点：文档默认参数是 `alpha=1.702, limit=7.0, bias=1.0, interleaved=True`（gpt_oss 风格），直接按默认调用不等价；必须显式传 `alpha=1.0、bias=0.0、interleaved=False` 才落到 Step3/HYV4 的 `silu(clamp(gate))*clamp(up)` 语义。可区分验证手段即上述 fp32 逐位比较 + gate 负区探针（若 gate 做了双侧 clamp，负区参考会变为 silu(-limit)*clamp(up)，通常不为0，并会与不做下界截断的参考不同，本次负区样本与无下界截断参考吻合，支持文档中的非对称语义）。

## 验证信号

本组来源观测轨迹内客观观测（Ascend950PR_9589 单卡）：

- 来源记录 事件 211（单次运行）：`clipped_swiglu ok shape=(256, 768) cos=0.99999619 maxdiff=5.000e-01`；`npu_swiglu (no clamp) cos vs ref=0.99975967`（对照）。
- 来源记录 事件 143 / 来源记录 事件 148：模块级 moe_experts_decode cos 0.99998409、moe_experts_prefill 0.99998295（含 clipped_swiglu 的整链路）。
- 来源记录 事件 156（clamp 边界定位）：`maxdiff 0.5 mean 0.004951368551701307`、`gate= 10.5 up= 7.875 ref= 79.0 fused= 78.5`——0.5 是幅度 79 处的 bf16 1 ULP，非语义差异。
- 来源记录 事件 160（reviewer 独立复核，单次运行）：fp32 `maxabs=0.000e+00 ... bits_equal= True`；bf16 `maxabs=5.000e-01 max_ulp=0.99`；两 dtype 下 `gate<-15` 区域参考/融合输出均为 ~3.47e-09 且相等。

## 适用与失效边界

- 参数映射前提：目标语义必须确实是「clamp 在 silu 之前 + gate 仅上界 + up 双侧 + 无 +1 偏置 + 前后切分」；gpt_oss 交织布局（interleaved=True 默认）或 gelu 语义不适用。
- bf16 下 maxdiff 可达 0.5（本样本绝对误差；日志未计算精确 ULP 距离），对逐位一致口径不满足；本次 fp32 样本逐位成立，不保证所有输入。若精度口径要求逐位，需按实际输入域重测，不能仅凭本探针承诺 fp32 路径全域逐位相等。
- docstring 支持型号列表未含 ascend950，本卡结论以「kernel 目录存在 + 运行时数值复核」为准；换芯片/升级 CANN 需重跑上述 fp32 逐位探针。
- 输入 x 要求连续（docstring：不支持非连续 Tensor）——GMM 输出本身连续，直接串接成立；若上游产出非连续视图需先 `.contiguous()`。
- `npu_clipped_swiglu` 的 `group_index` 参数可对 GMM 输出做按组截断（Sum(group_index) 过滤 pre 轴），本组来源观测未使用该能力，未验证。
