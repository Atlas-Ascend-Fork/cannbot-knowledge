---
{
  "type": "Runbook",
  "title": "vllm-ascend MoE 路由 logits 切 bf16 时的 MoeGatingTopK bias dtype 硬约束与休眠 Parameter 重赋值缺陷",
  "description": "把 MoE router gate 输出从 fp32 改为 bf16 时，MoeGatingTopK 的 tiling 校验要求 bias dtype 严格等于输入 x dtype，而 K3 的 e_score_correction_bias 是 fp32 Parameter；fused_topk_router.py 原有 L143-144 的原地重赋值在 bias 为注册 Parameter 且 dtype 首次不同时可能触发 TypeError；普通 Tensor 若成功重赋，之后 dtype 相同不会每步重复 Cast。代码修复采用按 dtype 缓存（_bias_cast_cache），以避免“只用局部变量转换”方案可能新增的每步 Cast；该轨迹无设备运行验证。判别分支含 A3（csrc 算子，仓内可验证 DT_BF16）与 A5（torch_npu 内置算子，仓内不可验证）。",
  "tags": [
    "task.debugging",
    "topic.precision",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "agnostic"
  ]
}
---
# vllm-ascend MoE 路由 logits 切 bf16 时的 MoeGatingTopK bias dtype 硬约束与休眠 Parameter 重赋值缺陷

## 适用场景

- 框架/模型：vllm-ascend 上的 MoE 模型推理（证据来自 Kimi K3，model_type `kimi_linear`，896 experts / Top-16 + grouped topk + `e_score_correction_bias`），凡把 router gate 输出从 fp32 改为 bf16 的改动都适用。
- 分支/版本：releases/v0.27.1rc 与 main 分支（两分支的 fused_topk_router.py 此段改前一致：L143-144 原地重赋值、`bias_opt=self.e_score_correction_bias`）。
- 平台：Ascend NPU；A2/A3 与 A5 的 MoeGatingTopK 实现不同（见机制与判别）。

## 触发与观测

触发条件：把 MoE router gate 的 logits 输出从 fp32 改为 bf16（例如 K3 gate bf16 化）。

客观观测（代码级证据，T153/T385/T447）：

1. csrc tiling 硬校验（moe_gating_top_k_tiling.cpp，T153 逐字节选）：

```
  Line 291:         (xDtype != ge::DataType::DT_FLOAT && xDtype != ge::DataType::DT_FLOAT16 && xDtype != ge::DataType::DT_BF16),
  Line 292:         OP_LOGE(context_, "x dtype %s error, only supports float32, half, bf16. please check.",
```

```
  Line 300:                     OP_LOGE(context_, "bias dtype %s not equal x dtype %s, please check.",
```

即 x 只接受 float32/half/bf16，且 bias dtype 必须与 x dtype 严格相等，否则算子返回失败。

2. K3 的 `e_score_correction_bias` 是 fp32 Parameter（kimi_k3.py 中 `nn.Parameter(torch.empty(num_experts, dtype=torch.float32))`），经 `e_score_correction_bias=...` 传给 router。

结论：**MoeGatingTopK 的 tiling 校验要求 bias dtype 与输入 x dtype 严格相等（moe_gating_top_k_tiling.cpp 报 "bias dtype %s not equal x dtype %s, please check."），K3 的 e_score_correction_bias 为 fp32，gate 输出改 bf16 后若不在某处适配 bias，算子直接返回失败。**

## 探针与操作

探针：

1. 读 `fused_topk_router.py` 的 bias 处理段（T385 逐字，改前原状）：

```
  Line 143:         if self.e_score_correction_bias is not None and self.e_score_correction_bias.dtype != router_logits.dtype:
  Line 144:             self.e_score_correction_bias = self.e_score_correction_bias.to(router_logits.dtype)
```

2. 查 csrc `op_host` 的 dtype 校验（见上 T153）。
3. 查硬件分派（`device/device_op.py`，T298 逐字）：

```
1624: def get_device_adaptor() -> type["BaseDeviceAdaptor"]:
1625:     adaptor_by_family = {
1626:         DeviceAdaptorFamily.STANDARD: BaseDeviceAdaptor,
1627:         DeviceAdaptorFamily.FP8_OPTIMIZED: A5DeviceAdaptor,
1628:         DeviceAdaptorFamily.COMPATIBILITY: Ascend310PDeviceAdaptor,
1629:     }
1630:     return adaptor_by_family[get_current_hardware_profile().device_adaptor_family]
```

操作（修复，随 bf16 gate 改动成套提交）：把条件性的原地重赋值改为"首次转换 + 按 dtype 缓存"，调用点改用 `bias_opt`（C474/C477）。核心实现（C474 逐字）：

```
    def _bias_for_logits_dtype(self, logits_dtype: torch.dtype) -> torch.Tensor | None:
        """Return e_score_correction_bias in the router logits dtype.

        MoeGatingTopK requires bias dtype == x dtype. The bias is normally a
        fp32 Parameter; when the logits arrive in bf16
        (VLLM_ASCEND_ENABLE_GATE_BF16=1) it is cast at most once per dtype
        and cached, so the steady-state forward (including ACLGraph capture)
        carries no bias Cast op. Reassigning ``self.e_score_correction_bias``
        in place would both add a Cast to every forward and fail with a
        TypeError when the attribute holds a registered ``nn.Parameter``.
        """
        bias = self.e_score_correction_bias
        if bias is None or bias.dtype == logits_dtype:
            return bias
        cached = getattr(self, "_bias_cast_cache", None)
        if cached is None or cached.dtype != logits_dtype:
            cached = bias.to(logits_dtype)
            self._bias_cast_cache = cached
        return cached
```

上述历史代码注释中“原地重赋会每步新增 Cast”的说法不准确：普通 Tensor 成功重赋后 dtype 已匹配，后续不会重复转换；注册 Parameter 则可能在首次重赋时报错。每步重复 Cast 是仅改为局部变量但不缓存时的潜在代价。

调用点（C477 逐字要点）：`bias_opt = self._bias_for_logits_dtype(router_logits.dtype)`，再以 `bias_opt=bias_opt` 传入 `DeviceOperator.moe_gating_top_k`。

## 机制与判别

1. 休眠缺陷：**fused_topk_router.py 原有 L143-144 对 self.e_score_correction_bias 的原地重赋值是休眠缺陷：fp32 logits 时 dtype 恒等从不执行；bf16 logits 首次触发时，若该属性是注册进 nn.Module 的 nn.Parameter，重赋普通 Tensor 会抛 TypeError。** 该路径在 fp32 时代从不执行（所有 logits 均 fp32、dtype 恒等），bug 一直休眠；旁证：同文件 hash 分支早已改用局部变量的安全写法。
2. 缓存设计的双重动机：**修复采用 _bias_for_logits_dtype 一次性按 dtype 缓存转换（_bias_cast_cache），在 bias 静态、warmup 已填充缓存且 dtype 不变的前提下，设计上可避免后续 bias Cast；轨迹未设备验证该稳态图；fp32 logits 时 bias 原样返回，与旧代码逐字节一致、纯惰性。**若只改局部变量不做缓存，92 层 MoE 每步各多一次小 Cast，部分抵消删除大 Cast 的收益；缓存转换需在 ACLGraph 捕获前的 warmup 完成；本轨迹未提供捕获产物或稳态图验证。
3. 可区分的解释分支（按报错特征判别）：
   - 运行时报 `bias dtype ... not equal x dtype ...`（GRAPH_FAILED）→ bias 未适配：bf16 logits 配 fp32 bias 直入算子，说明调用方仍传原 Parameter。
   - Python 侧 `TypeError: cannot assign ... as parameter` → 踩中休眠的原地重赋值缺陷（L143-144 首次真正执行）。
   - 无报错但精度劣化 → bf16 舍入翻转 near-tie 专家选择（机制不同于上述两个缺陷）。
4. 硬件分支判别：**A2/A3 走 BaseDeviceAdaptor 的 csrc 算子 torch.ops._C_ascend.moe_gating_top_k（def.cpp 注册 DT_BF16，仓内可验证），A5（FP8_OPTIMIZED）走 A5DeviceAdaptor 的 torch_npu.npu_moe_gating_top_k 内置算子（device_op.py:993），其 bf16 支持仓内无法验证、须上机冒烟。**A5 调用形态（T284 逐字，含手动 renorm :1005-1006）：

```
993:         topk_weights, topk_ids, out = torch_npu.npu_moe_gating_top_k(
994:             x,
995:             k=k,
996:             bias=bias_opt,
997:             k_group=k_group,
998:             group_count=group_count,
999:             group_select_mode=group_select_mode,
1000:             renorm=0,
1001:             norm_type=norm_type,
1002:             routed_scaling_factor=routed_scaling_factor,
1003:             eps=eps,
1004:         )
```

A5 的间接可行证据：仓内 csrc 算子从同族 CANN kernel 移植、注册 FP16/FP32/BF16 三种；A5 手动 renorm 的 bf16 数值影响也未实测。这些信息不构成 bf16 支持或等价性的验证。

## 验证信号

本轨迹内为代码级证据，无运行验证：

- T153：csrc tiling/def 的 dtype 校验原文（本卡的全部机制依据）。
- T385：改前 fused_topk_router.py L143-144/L156 原文（release 分支 grep）。
- T447：release 分支 fused_topk_router.py 改前全文回读（确认与 main 改前形态一致）。
- T475/T478：修复 edit applied（与[MoE gate 的 bf16 接入改动](../performance/vllm_ascend_kimi_moe_bf16.md)同批）。
- T284/T298：A5 内置算子调用与硬件族分派原文。

未观测到的信号：A5 上 `torch_npu.npu_moe_gating_top_k` 的 bf16 冒烟（建议探针：bf16 x + bf16 bias 直接调用，参数对齐 device_op.py:993-1004；报 dtype 错误即停止）；bf16/fp32 两路径 `topk_ids` per-token 一致率统计。

## 适用与失效边界

- 适用：任何"router gate 输出 dtype 改变"的 vllm-ascend MoE 改动（bias dtype 必须跟随 logits dtype）。
- 失效/风险边界：
  1. 本机制为代码级诊断结论，两个失败模式（算子 GRAPH_FAILED / Parameter TypeError）均未在本轨迹实际触发观测。
  2. A5 的内置算子 bf16 支持未验证，上 A5 前必须冒烟。
  3. `_bias_cast_cache` 假设 bias 权重静态：RL `update_weights` 更新 `e_score_correction_bias` 后缓存陈旧，需补失效逻辑；ACLGraph 捕获依赖"缓存转换发生在捕获前的 warmup"这一时序。
  4. 若模型 bias 传 None（`bias_opt=None`），`_bias_for_logits_dtype` 原样返回 None，行为与旧代码一致。
