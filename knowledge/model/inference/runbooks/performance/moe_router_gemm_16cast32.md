---
{
  "type": "Runbook",
  "title": "A5(950) 上 MoE router 门控 GEMM 用 torch_npu.npu_fused_matmul(fused_op_type=\"16cast32\") 把 bf16→fp32 cast 融进单算子，替代 vllm-ascend 的显式 Cast+MatMulV3 两算子路径",
  "description": "A5(950) 上 MoE router 门控 GEMM 需 fp32 精度 logits（[2,4096]×[256,4096]→[2,256]）：vllm-ascend 两条 router 路径都是显式 Cast+MatMulV3 两算子，而 cann-recipes-infer 950 分支用 torch_npu.npu_fused_matmul(fused_op_type=\"16cast32\") 把 bf16→fp32 cast 融进单算子；权重 dtype/格式（bf16 ND vs fp32 ND/NZ）是接入的主要适配点。",
  "tags": [
    "task.implementation",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "950"
  ]
}
---
# A5(950) 上 MoE router 门控 GEMM 用 torch_npu.npu_fused_matmul(fused_op_type="16cast32") 把 bf16→fp32 cast 融进单算子，替代 vllm-ascend 的显式 Cast+MatMulV3 两算子路径


## 适用场景
适用场景：DeepSeek 类 MoE 在 Ascend A5（platform_version=="950"）上需要 fp32 精度 router logits（[2,4096]×[256,4096]→[2,256]），且 profiling 发现门控 GEMM 前有独立 Cast 算子时。

## 触发与观测
触发与观测：profiling 中 vllm-ascend 的门控分解为 Cast/InplaceCopy（AI_VECTOR_CORE）+MatMulV3（MIX_AIC）两算子，而同工作负载 recipes 侧只有一个 FusedMatMul（MIX_AIC）。

## 探针与操作
探针与操作：对 gate 计算前后做 msprof/torch profiler 算子统计，确认是否存在独立 Cast 节点及其耗时；grep 代码库 npu_fused_matmul / fused_op_type 确认是否已采用融合路径。

## 机制与判别
机制与判别：torch_npu.npu_fused_matmul(x, weight, fused_op_type="16cast32") 把 bf16→fp32 输入 cast 融进 matmul 内核，单算子完成且消除 casted activation 的额外 HBM。vllm-ascend 两条 router 路径（internal：hidden_states.float() + F.linear(..., gate.weight_fp32)；external：F.linear(hidden_states.float(), self.gate.weight)）都是显式两算子。采纳时的格式注意：recipes 950 路径 gate 权重保持 bf16、只融合输入侧 cast；vllm-ascend 现状 weight_fp32 是 fp32 ND（fp32 不做 NZ 转换）而 bf16 gate.weight 是 NZ——替换时要么按 recipes 保持 bf16 ND，要么确认 npu_fused_matmul 接受 fp32 权重配 16cast32 模式。


机制片段：


```
        # compute gating score
347:         if self.platform_version == "950":
348:             logits = torch_npu.npu_fused_matmul(hidden_states.view(-1, h), self.gate.weight, fused_op_type="16cast32")
349:         else:
350:             logits = self.gate(hidden_states.view(-1, h).to(torch.float32))
351:         topk_idx, topk_weight, _ = OpKernel.gate_topk(self, logits, input_ids)
```


```
            if self.is_internal_router:
804:                 gate = self.gate
805:                 assert gate is not None
806:                 # NOTE(Angazenn): To make this cast explicitly, the hbm usage might
807:                 # increase with extra hidden states. We also assume that all gate
808:                 # linear is unquantized so that we the weight is pre-casted in
809:                 # process_weights_after_loading of AscendUnquantizedLinearMethod.
810:                 hidden_states_fp32 = hidden_states.float()
811:                 before_routed_experts = torch.npu.current_stream().record_event()
812:                 router_logits = F.linear(hidden_states_fp32, gate.weight_fp32)
813:                 after_routed_experts = torch.npu.current_stream().record_event()
814:             else:
815:                 before_routed_experts = torch.npu.current_stream().record_event()
816:                 after_routed_experts = None
```

## 验证信号
验证信号：验证层级为源码阅读+git 历史（source_read）：recipes 950 分支代码与 vllm-ascend internal router 代码均逐行核对。本会话未做性能实测，两边的算子耗时数据来自用户提供的 profiling，未构成同会话可比基线，故不标注性能增益数值。

## 适用与失效边界
适用与失效边界：仅适用于 A5/950 平台（recipes 非 950 分支同样退回显式 cast）；需 fp32 门控精度的 DeepSeek 类 MoE。局限：性能收益未在本轨迹内实测；权重 dtype/格式（bf16 vs fp32 ND、NZ）是接入时的主要适配点。

## 结论与证据边界

- ：cann-recipes-infer 的 Deepseek-v4 MoE 门控在 platform_version=="950" 分支调用 torch_npu.npu_fused_matmul(hidden_states.view(-1, h), self.gate.weight, fused_op_type="16cast32")——单个 FusedMatMul（MIX_AIC）完成 [2,4096]×[256,4096]→[2,256]，bf16→fp32 cast 融进 matmul 内核、无独立 Cast 算子；非 950 平台走 self.gate(hidden_states.view(-1, h).to(torch.float32)) 的显式两算子路径；950 下 gate 用 ReplicatedLinear 且 params_dtype 为 bf16。

- ：vllm-ascend 的 internal router 路径（fused_moe.py shared_forward_impl 的 is_internal_router 分支）做 hidden_states_fp32 = hidden_states.float() 后 F.linear(hidden_states_fp32, gate.weight_fp32)——即 profile 里的 Cast/InplaceCopy（AI_VECTOR_CORE）+MatMulV3（MIX_AIC）两算子；external 路由在模型侧同样 F.linear(hidden_states.float(), self.gate.weight)；is_internal_router 定义为 gate 非空且带 weight_fp32 属性（precast_fp32_weight=True 时由 AscendUnquantizedLinearMethod 预铸 fp32 ND 权重）。
