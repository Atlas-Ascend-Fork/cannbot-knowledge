---
type: Runbook
title: MegaMoE 权重 scale 对接：uint8 E8M0 编码应重解释为浮点 scale 视图
description: 固定分支修复在 MegaMoE 调用前为两组专家 scale 建立 E8M0 view，保留原始字节与存储；缺少实机修后结果，不能把数值
  cast 当作兼容修复。
tags:
- task.debugging
- topic.precision
- topic.mixture_of_experts
status: draft
sources: []
created_at: '2026-10-30T03:17:20Z'
updated_at: '2026-10-30T09:01:39Z'
platforms:
- '950'
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      model_features:
        all_of:
        - moe
      phase:
      - prefill
---

# MegaMoE 权重 scale 对接：uint8 E8M0 编码应重解释为浮点 scale 视图

## 现象与适用场景

Kimi K3 的 MegaMoE Prefill 路线把 dispatch、GMM1、SiTU、GMM2 和 combine 接成一个调用。专家权重仍来自已有 loader，但算子调用边界对 scale 的 dtype 要求可能与 split 路线不同。遇到该接入点的 dtype/精度问题时，需要同时检查 `w13_weight_scale` 和 `w2_weight_scale`，不能只检查权重张量或确认某个全局量化开关已经打开。

本卡针对昇腾 950PR/DT、量化专家权重、`KimiSparseMoeBlock._run_megamoe()` 的接口适配。现有变更的范围是“loader 保存原始 E8M0 编码字节，而 MegaMoE 需要 E8M0 dtype”；没有本轮目标 NPU 修前、修后结果或完整原始错误输出。具体 CANN、torch_npu 和 MegaMoE 包版本应在部署机记录，当前保持 draft。

## 相关入口与数据含义

调用链是 MoE Prefill routed states 与路由结果进入 `_run_megamoe()`，从 `self.experts` 取两组专家权重与 scale，再把 `MoEContext` 中已初始化的 `mega_sym_buffer` 交给 `mega_moe()`。

| 参数 | 对应对象 | 核对重点 |
|---|---|---|
| `l1_weights` | `w13_weight` | 专家第一段融合投影，使用本调用声明的量化权重格式 |
| `l1_weights_sf` | `w13_weight_scale` | 必须与第一组 weight 的专家、分片和 scale 布局对应 |
| `l2_weights` | `w2_weight` | 第二段投影，不可误复用第一段 scale |
| `l2_weights_sf` | `w2_weight_scale` | 必须独立完成同样的 E8M0 dtype 适配 |
| `topk_ids/topk_weights` | 路由结果 | dtype 和有效 token/专家映射另按路由契约核对 |
| `sym_buffer` | `moe_ctx.mega_sym_buffer` | 缺失时应保留初始化错误，不应归因为 scale dtype |

## 根因：编码与数值转换不是一回事

loader 的 `uint8` 张量保存的是 E8M0 编码字节。把这些字节直接作为 `uint8` 交给一个要求 E8M0 的接口，会使接口看到的 dtype 与编码含义不一致。`view(torch.float8_e8m0fnu)` 保留底层存储并重新解释编码；`.to(torch.float8_e8m0fnu)` 则把 uint8 的整数数值转换成浮点数，改变了所表示的 scale。

因此本处置不是重新估计 scale、重新量化权重或改 checkpoint。即使 view 后 shape 没变，也要核对两组 weight/scale 的对应关系与包版本的真实 schema。字节数一样不能单独证明 scale 语义正确。

## 完整调用单元：变更前与变更后

下面是 `_run_megamoe()` 的完整方法。它依赖已有类成员、`mega_moe` 和 `torch_npu`，不能脱离模型初始化与通信域注册独立运行。保留全方法有助于核对两个 scale 以及 `sym_buffer`、路由参数和激活配置没有被一起改动。

变更前：

```python
def _run_megamoe(self, routed_states, topk_idx, topk_weight, moe_ctx):
    """Run Prefill routed experts through MegaMoE dispatch/compute/combine.

    Dispatch + GMM1 + SiTU + GMM2 + Combine are completed by a single mega_moe
    operator, replacing Prefill's double-routing pipeline.

    sym_buffer is allocated once by KimiLinearForCausalLM after communication-domain
    registration, passed through MoEContext, and reused throughout inference.
    """
    if moe_ctx is None or moe_ctx.mega_sym_buffer is None:
        raise RuntimeError("MegaMoE requires an initialized sym_buffer")
    sym_buf = moe_ctx.mega_sym_buffer
    l1 = [self.experts.w13_weight]
    l1_s = [self.experts.w13_weight_scale]
    l2 = [self.experts.w2_weight]
    l2_s = [self.experts.w2_weight_scale]
    y, _ = mega_moe(
        x=routed_states,
        topk_ids=topk_idx.to(torch.int32),
        topk_weights=topk_weight,
        l1_weights=l1,
        l1_weights_sf=l1_s,
        l2_weights=l2,
        l2_weights_sf=l2_s,
        weight1_type=torch_npu.float4_e2m1fn_x2,
        weight2_type=torch_npu.float4_e2m1fn_x2,
        sym_buffer=sym_buf,
        activation="situglu",
        activation_params={
            "beta": self.experts.situ.beta,
            "linear_beta": self.experts.situ.linear_beta,
        },
    )
    return y
```

变更后：

```python
def _run_megamoe(self, routed_states, topk_idx, topk_weight, moe_ctx):
    """Run Prefill routed experts through MegaMoE dispatch/compute/combine.

    Dispatch + GMM1 + SiTU + GMM2 + Combine are completed by a single mega_moe
    operator, replacing Prefill's double-routing pipeline.

    sym_buffer is allocated once by KimiLinearForCausalLM after communication-domain
    registration, passed through MoEContext, and reused throughout inference.
    """
    if moe_ctx is None or moe_ctx.mega_sym_buffer is None:
        raise RuntimeError("MegaMoE requires an initialized sym_buffer")
    sym_buf = moe_ctx.mega_sym_buffer
    l1 = [self.experts.w13_weight]
    # The loader stores E8M0 encodings as bytes; MegaMoE requires the
    # actual E8M0 dtype. Reinterpret without converting values or copying.
    l1_s = [self.experts.w13_weight_scale.view(torch.float8_e8m0fnu)]
    l2 = [self.experts.w2_weight]
    l2_s = [self.experts.w2_weight_scale.view(torch.float8_e8m0fnu)]
    y, _ = mega_moe(
        x=routed_states,
        topk_ids=topk_idx.to(torch.int32),
        topk_weights=topk_weight,
        l1_weights=l1,
        l1_weights_sf=l1_s,
        l2_weights=l2,
        l2_weights_sf=l2_s,
        weight1_type=torch_npu.float4_e2m1fn_x2,
        weight2_type=torch_npu.float4_e2m1fn_x2,
        sym_buffer=sym_buf,
        activation="situglu",
        activation_params={
            "beta": self.experts.situ.beta,
            "linear_beta": self.experts.situ.linear_beta,
        },
    )
    return y
```

## 判别与处理步骤

1. 确认当前实际进入的是 MegaMoE Prefill 路线；若执行的是 split GMM 或 Decode 路线，应核对该路线自己的接口，不能套用此调用点。
2. 对两组 scale 分别记录 dtype、shape、stride、元素字节数、storage 地址，并确认 loader 保存的是有效 E8M0 编码而非普通整数数值。不要构造一组任意 uint8 数据就认定接口已适配。
3. 检查部署 MegaMoE 的 scale 参数 schema。只有它要求 E8M0 dtype、而当前 buffer 为原始字节载体时，才采用上述 view。
4. 在两组调用点同时建立 view。检查 view 前后原始字节和底层 storage 地址一致，逻辑形状与 weight/scale 对应不变；不替换参数所有者，不修改 weight dtype 和 checkpoint。
5. 先与原 split 路线按相同输入、权重、路由和有效专家行对齐输出，再进行整网验收。若仍失败，继续检查布局、分片、真实算子版本与路由语义，不扩大容差来覆盖问题。

## 设计决策

适配放在 MegaMoE 的接口边界，使其它仍消费字节 scale 的路径保持原有契约。两组 scale 都在同一处显示列出，避免第一层修复而第二层遗漏。使用 view 保留原始量化内容，便于同输入对照并把差异归因到 dtype 解释。

该决定不意味着所有 MC2/GMM 接口都接收相同 dtype；图边界也可能有不同要求，见 [可变 C8 MLA 图边界](../compilation/mutable_mla_fp8_e8m0_graph_boundary.md)。

## 验证信号与部署验收

本轮能核对的是完整调用函数中两组 scale 都增加了 E8M0 view，其余权重、路由、共享 buffer 和激活参数仍按原契约传递。这只证明存在该适配实现，不证明目标算子已运行通过。

部署验收须同时保留：两组 scale 的字节/存储一致性、真实量化权重下与 split 路线的输出对齐、有效专家行覆盖，以及整网原精度验收。性能对比只有在同配置精度通过后才有意义；本卡不提供未经实测的收益数字。

## 坏实践、回退与失效边界

不要对 uint8 编码做数值 cast；不要只适配 `w13` 而遗漏 `w2`；不要为了消除错误重新量化 checkpoint；不要把命名为 scale 的任意张量都解释为 E8M0；不要把 `sym_buffer` 未初始化的错误归给 dtype。

回退时恢复匹配版本的完整调用点，或成套退回原 split 路线，并核对其 weight/scale 接口。未决项优先是取得目标 MegaMoE 包的真实 schema 与同输入修前、修后结果；在此之前，本卡只作为接口对接诊断，不声明已完成 NPU 修复或整网精度验收。
