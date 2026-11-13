---
{
  "type": "Runbook",
  "title": "Hunyuan-A13B FP8 在 Ascend950PR 上 A1–A5+M1–M3 融合算子全链路替换与端到端验证",
  "description": "在 torch_npu 2.12.0 + CANN 9.1.0 + Ascend950PR_9589 单卡上，把 Hunyuan-A13B-Instruct-FP8（W8A8 静态 per-tensor）的 Attention 子链路（A1 npu_add_rms_norm / A2、A4 npu_rms_norm / A3 npu_apply_rotary_pos_emb TND / A5 npu_quantize）与 MoE（M1 npu_moe_gating_top_k_softmax → M2 npu_moe_init_routing_v2 + FP8 npu_grouped_matmul + npu_moe_finalize_routing / M3 npu_swiglu）全量替换 dense 计算，专家权重加载后一次性重排为 w13[E,H,2I]/w2[E,I,H] grouped-matmul 布局。逐模块等价（A1 added 与 A5 逐位一致，其余 max_abs ≤ 0.03125）、CPU 黄金参考对齐 cosine 0.99989 且贪心 token 全匹配、3 条不等长 packed 多 batch 与 solo 一致；batch 1 / 21-token prefill / 8-token 输出负载下 Prefill 1923.02→176.33 ms、Decode 7 步均值 1748.09→110.18 ms（reviewer 独立复核）。",
  "tags": [
    "task.implementation",
    "topic.model_serving",
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
# Hunyuan-A13B FP8 在 Ascend950PR 上 A1–A5+M1–M3 融合算子全链路替换与端到端验证

## 适用场景

- 模型/框架：Hunyuan-A13B-Instruct-FP8（HunYuanMoEV1ForCausalLM，80.39B 参数、32 层、64 专家 top-8 + 1 共享 MLP，GQA 32/8 heads、head_dim=128、RoPE→per-head QK RMSNorm 特有顺序），独立部署自管 Runner（非 cann-recipes-infer executor）。
- 平台/版本：Ascend950PR_9589 单卡（HBM 可见 123.25 GiB），torch_npu 2.12.0 + torch 2.12.0+cpu + CANN 9.1.0（须含 ascend950 ops_nn 算子子包，`env.sh` 自动探测完整 CANN 安装），eager 模式。
- 量化：W8A8 FP8 E4M3，activation_scheme=static，per-tensor scale（checkpoint 自带 `weight`/`weight_scale`/`input_scale`）。
- 目标与负载：阶段 3 融合算子优化（阶段 2 已完成 FA v2 TND，跳过 FA 算子本身），P0+P1 全量实施 A1–A5（Attention 子链路）与 M1–M3（MoE）；验证负载为 batch 1、21-token prefill、8-token 输出。
- 缺失信息：单卡单负载口径；未做多卡/EP/图模式验证；A1–A5 组内单算子性能未隔离（开关按组控制）。

## 触发与观测

- 基线（阶段 2 FA 后、阶段 3 前）：`agentic/baseline/baseline_metadata.json` 记录 batch 1 负载 Prefill 1923.02 ms、Decode 采集脚本均值 1740.72 ms（剔除首个 decode；同日志完整 7 步均值为 1748.09 ms）；analyzer 定位根因为 MoE dense dispatch——每层固定计算 `64 × expert_capacity` 行专家 MLP，decode（S=1）时 capacity 下限 = topk = 8 → 512 行/层、有效仅 8 行，约 64× 冗余。
- 算子可用性客观核查（analyzer，设备上 `hasattr(torch_npu, op)` 全 True）：`npu_rms_norm`/`npu_add_rms_norm`/`npu_apply_rotary_pos_emb`/`npu_swiglu`/`npu_moe_gating_top_k_softmax`/`npu_moe_init_routing_v2`/`npu_grouped_matmul`/`npu_moe_finalize_routing`/`npu_quantize` 等均存在。
- 替换后整链路（implementer 自验证 + reviewer 独立复核）端到端观测：`bash infer.sh` 输出正常（`<answer> Paris. </answer>`，可读、不重复、非全零、不提前 EOS）。

## 探针与操作

改动文件：`models/modeling_hunyuan.py`、`runner_hunyuan_a13b_fp8.py`、`tools/compare_golden_npu.py`。开关：`HY_ENABLE_FUSION`（默认 1，控制 A1–A5）、`HY_ENABLE_MOE_FUSION`（默认 1，控制 M1–M3；置 0 回退 stacked dense 路径）、`HY_MOE_DEBUG=1` 打印逐层负载/capacity。CPU 黄金路径不变（`_is_npu()` 保证 CPU 全部回退 eager 参考）。

替换清单（原算子 → NPU 融合算子）：

- A1 残差 add + post_attention_layernorm → `npu_add_rms_norm`（用返回的 `added` 作为 MLP 前残差）
- A2/A4 input/final/QK RMSNorm → `npu_rms_norm`
- A3 RoPE → `npu_apply_rotary_pos_emb(layout='TND', rotary_mode='half')`，cos/sin 按 position_ids gather 成 `[T,1,128]`，保持 Hunyuan「RoPE 先于 QK norm」顺序
- A5 激活量化 → `npu_quantize`
- M1 Gate → `npu_moe_gating_top_k_softmax` + top-k 概率归一化（等价 `topkgating` 的 router_probs）
- M2 专家计算 → `fuse_experts()` 加载后一次性重排 `w13[E,H,2I]`/`w2[E,I,H]`（FP8，K×N），forward 走 `npu_moe_init_routing_v2` → FP8 `npu_grouped_matmul`（scale per-N + per_token_scale per-row）→ `npu_moe_finalize_routing`
- M3 SwiGLU → `npu_swiglu`（专家 GMM 输出天然 [gate|up]；共享 MLP 用 `cat([gate,up])` 后调用）

A5 的融合实现（`FP8Linear.forward`，逐字）：

```
            # A5: fuse the static activation quantisation
            #   xq = clamp(x / input_scale, -448, 448).to(fp8)
            if ENABLE_FUSION:
                xq = torch_npu.npu_quantize(
                    x2, self.input_scale, None, torch.float8_e4m3fn, -1, True
                )
            else:
                xq = torch.clamp(
                    x2.float() / self.input_scale, -FP8_MAX, FP8_MAX
                ).to(torch.float8_e4m3fn)
```

M1+M2+M3 fused 前向核心（`HunYuanMoE._fused_forward`，逐字）：

```
        expanded_x, expanded_row_idx, tokens_per_expert, _ = torch_npu.npu_moe_init_routing_v2(
            x,
            expert_idx=topk_idx,
            active_num=S * K,
            expert_num=E,
            expert_tokens_num_type=1,      # count mode
            expert_tokens_num_flag=True,
            active_expert_range=[0, E],
            quant_mode=-1,                 # non-quantised routing (FP8 done explicitly)
        )

        # ---- w13 = [gate | up] ----
        row_is13 = torch.repeat_interleave(self.w13_input_scale, tokens_per_expert)  # [M]
        xq = self._quant_fp8(expanded_x, row_is13[:, None])
        mm13 = torch_npu.npu_grouped_matmul(
            [xq], [self.w13_weight],
            scale=[self.w13_scale_gmm], per_token_scale=[row_is13],
            group_list=tokens_per_expert, split_item=3, output_dtype=x.dtype,
            group_type=0, group_list_type=1, tuning_config=[0],
        )[0]
        act = torch_npu.npu_swiglu(mm13)                 # [M, I]

        # ---- w2 = down ----
        row_is2 = torch.repeat_interleave(self.w2_input_scale, tokens_per_expert)
        aq = self._quant_fp8(act, row_is2[:, None])
        expert_out = torch_npu.npu_grouped_matmul(
            [aq], [self.w2_weight],
            scale=[self.w2_scale_gmm], per_token_scale=[row_is2],
            group_list=tokens_per_expert, split_item=3, output_dtype=x.dtype,
            group_type=0, group_list_type=1, tuning_config=[0],
        )[0]

        combined = torch_npu.npu_moe_finalize_routing(
            expert_out,
            skip1=None, skip2=None, bias=None,
            scales=topk_weight.to(expert_out.dtype),
            expanded_src_to_dst_row=expanded_row_idx,
            export_for_source_row=None, drop_pad_mode=2,
        )
        return shared + combined
```

## 机制与判别

- 性能主杠杆是 MoE 稀疏化：dense dispatch 的 64× 行冗余被 grouped_matmul 按 `tokens_per_expert` 分组消除；A1–A5 均为小算子，收益次要。该归因由同会话组级消融支持（见验证信号 c3），但组内单算子未隔离，属当前实现的粒度限制。
- FP8 专家 GMM 的反量化链为乘法 `out = (xq@w) × scale[e,n] × per_token_scale[m]`，静态激活方案把每行所属专家的 `input_scale` 作为 per-row `per_token_scale`、`weight_scale` 广播为 per-N scale（详见[FP8(E4M3) npu_grouped_matmul 静态 per-tensor 激活 scale 的接入语义与前置校验](../precision/fp8_e4m3_npu_grouped_matmul_per_tensor.md)）。
- MoE capacity 语义与基线 topkgating 的等价性是独立机制（详见[NPU dropless MoE 路由对基线 capacity-mask topkgating 的精确等价修复](../precision/npu_dropless_moe_capacity_mask.md)），不在本卡重复。
- reviewer 独立复测与 implementer 自验证使用不同测试工件（reviewer 自写 `tools/reviewer_module_check.py`、`tools/reviewer_multibatch_check.py` 与消融日志），结论一致。
- 未验证推断：多卡 EP 场景、图模式（阶段 5）下的行为未在轨迹内验证。

## 验证信号

（平台：Ascend950PR_9589 单卡 / torch_npu 2.12.0 / CANN 9.1.0；性能均为 warm-up 后单次观测或 7 步均值，负载配置一致；Decode 比较统一采用完整 7 步均值）

- c1：Hunyuan-A13B-Instruct-FP8 单卡 eager、batch 1、21-token prefill、8-token 输出负载下，A1–A5+M1–M3 全融合使 Prefill 耗时 1923.02 ms 降至 176.33 ms（reviewer 独立复测，单次观测）。〔基线 signals：来源记录#53（baseline_metadata.json）；候选 signals：来源记录#165（logs/reviewer_stage3_infer.log）〕
- c2：同负载下 Decode 完整 7 步均值由 1748.09 ms 降至 110.18 ms（reviewer 复测 7 步均值：110.20/110.91/109.90/109.79/110.79/110.09/109.56 ms）。
- c3：组级消融归因（同会话同负载、整组开关粒度）：仅阶段 2 FA（f0_m0）Prefill 1780.01 ms；加 A1–A5（f1_m0）1551.41 ms；加 M1–M3（f0_m1）214.85 ms；全融合 176.33 ms——Prefill 收益主要来自 M1–M3 MoE 稀疏化，A1–A5 小算子组贡献次要。〔signals：来源记录#214〕
- c4：融合后 NPU FP8 前向与 CPU BF16 黄金参考对齐：prefill logits 余弦 0.99989（替换前基线 0.99985），贪心生成 token 完全一致（token_match=true、无首个分歧步），prefill top10 重叠 9/10。〔signals：来源记录#120〕
- c5：逐模块替换前后对比（替换前 eager vs 替换后融合，NPU 同权重）：A1 残差 added 逐位一致、A5 激活量化逐位一致、A3 RoPE max_abs=0.015625、A2/A4 RMSNorm max_abs=0.03125、M3 SwiGLU max_abs=0.015625、M1–M3 MoE（S=1/7/40）max_abs≤0.0024 且 mean_rel≤0.006。〔signals：来源记录#149〕
- c6：3 条不等长 prompt 的 packed 多 batch 与各自 solo（batch 1）贪心 token 序列完全一致（3/3 match，RESULT: PASS），融合路径（含 capacity 掩码语义）在 packed 路径不改变生成结果。〔signals：来源记录#226；implementer 侧 batch=2 packed 亦通过 来源记录#367〕
- c7：npu_quantize 的 dtype 文档枚举（div_mode=True）仅列 qint8/quint8/int32，但本机实测接受 torch.float8_e4m3fn 且与 clamp(x/s) 结果逐位一致（maxerr=0.0）；端到端 A5 融合逐模块复核同样逐位一致（bitwise_equal=True）。〔signals：来源记录#171、来源记录#149〕

## 适用与失效边界

- 版本边界：结论基于 torch_npu 2.12.0 / CANN 9.1.0 / Ascend950PR_9589；文档 dtype 列表与运行时能力存在滞后（如 npu_grouped_matmul、npu_quantize 的 FP8 支持），换版本须重做单算子冒烟。
- 量化边界：仅验证静态 per-tensor scale 的 W8A8 FP8 checkpoint；动态量化 / block-wise / MX 方案未验证。专家 gate/up input_scale 相等是 w13 合并共享 scale 的前提（本 checkpoint 全量核对成立），迁移到其他 checkpoint 前必须重新核对。
- 负载边界：性能数字为 batch 1、21-token prefill、8-token 输出、warm-up 后单次观测；不同 batch/序列长度/并行度（TP/EP）下未验证，不能外推为通用加速承诺。
- 结构边界：Hunyuan 的 RoPE→QK norm 顺序被显式保留；A3 的 TND cos/sin 须 gather 成 [T,1,D]（D=128 满足产品约束）。
- 回退条件：`HY_ENABLE_FUSION=0` / `HY_ENABLE_MOE_FUSION=0` 可整组回退 eager/dense 路径；CPU 黄金参考路径始终不融合。若 MoE 专家负载超载且未启用精确 capacity 掩码（见 [NPU dropless MoE 路由对基线 capacity-mask topkgating 的精确等价修复](../precision/npu_dropless_moe_capacity_mask.md)），语义不等价，必须回退或修掩码。
- 停止条件：golden 对齐（cosine/token match）或 packed 多 batch 一致性失败时停止上库；单算子级性能归因需求当前实现不满足（开关按组控制）。
