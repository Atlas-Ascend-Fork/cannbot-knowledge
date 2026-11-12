---
type: Runbook
title: 推理精度分诊：packed 专家权重、zero expert、容差与请求状态
description: MoE 输出接近零时检查 packed checkpoint 专家权重加载；用 BF16 相对误差与算子容差、scale、请求状态和首差异证据定位精度问题。
tags:
- task.debugging
- topic.precision
- topic.mixture_of_experts
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-precision-debug/SKILL.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/fuse_moe_gmm.py
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/README.md
  role: supporting
- resource: https://www.hiascend.com/document/detail/zh/mindstudio/80RC1/practicalcases/optimizationmodelinference/toolsample4_008.html
  role: supporting
created_at: '2026-11-09T09:23:50Z'
updated_at: '2026-11-10T01:23:11Z'
platforms:
- agnostic
aliases:
- packed expert 权重漏加载
- 算子精度容差与 BF16 相对误差
- DP 请求 token 同步边界
- CLOSE_MATMUL_K_SHIFT
- 温度为零仍不确定
- 调试 dump 改变现象
---

# 推理精度分诊：packed 专家权重、zero expert、容差与请求状态

## 快速检查与定位顺序

固定实际权重、tokenizer、输入、随机性与执行模式，先判断首个差异在 Prefill 还是 Decode，再沿层→Attention/MoE/MLP→算子定位。比较相同输入下的输出、shape、dtype、scale 和状态更新；不要仅比较生成文本。近零输出、cosine 或 max-relative-diff 只是线索，容差应按目标算子、dtype、近零分母与最终任务确定，不把旧表 BF16 1e-3 或量化 1e-2 当通用验收线。

## 可复用的症状分流

| 症状 | 检查证据与处置 |
| --- | --- |
| MoE 输出全零或接近零 | checkpoint 是 packed tensor 还是逐 expert 键；核对 loader 映射、EP 本地切片与实际 copy，未加载不能靠调 scale 修复 |
| 换路由后 zero/copy expert 结果错 | 核对 active_expert_range 与真实 expert/identity 分界，identity 贡献应基于原始 MoE 输入和相应权重，而不是已变换的专家输出 |
| W8A8 从某层开始放大 | 检查该层真实位宽、per-channel/per-token scale、dtype、重排和后处理；不要只看模型量化名字 |
| 语义大致正常但严重重复 | 核对 embedding/normalization factor、位置、KV 更新与训练结构删减；有额外归一化时不能只跳过组件而丢掉幅度修正 |
| 多步后 NaN 或跨 batch 不一致 | 找到首个非有限张量，检查请求所有权、token/位置/KV 对齐与路由有效行，而不是从最后一层倒推唯一原因 |

LongCat double-routing 中把 zero expert 权重与 routed expert 分开，路由后的输出再加原始输入乘 identity_weight；MC2 的 copy_expert_num 是另一条实现，不能重复加 identity。没有该语义的普通 MoE 不套此修法。

## 图模式和分布式边界

eager 正确、图模式错误时，按捕获、功能化、后端执行逐层定界，检查假原地算子的变异/别名声明，以及冻结权重、非连续布局和缓存地址；关闭某优化只用于缩小范围，不自动证明唯一根因。

DP 可能处理独立请求。旧经验“每步 dist.broadcast(next_token, src=0) 给所有 DP rank”不能作为通用修复，否则会覆盖不同请求的 token；只对确实复制同一请求且协议要求一致的参与者同步，独立 DP 请求保持各自所有权。历史 Mamba cache index=0 与 max-mamba-cache-size=512 仅是缺少完整版本/硬件条件的 workaround 记录，不能替代当前框架的状态缓存契约或当生产推荐。

## 非确定性和观测扰动

temperature=0 或固定随机种子不单独保证底层浮点归约一致。MindStudio 8.0.RC1 的推理定位文档将 `CLOSE_MATMUL_K_SHIFT=1` 列为可疑 Matmul 的错峰策略对照手段；它不是所有 NaN 或精度问题的默认修复，也不证明设置后整网必然确定。固定 Recipes 代码没有该变量的调用点，部署须核对对应 CANN 版本；定位后恢复原设置，并重新验证实际吞吐和输出。

若加 print/dump 后现象改变，优先检查未初始化内存、越界、别名/复用和跨流时序，不凭现象直接断言算子错误。同步和 host 拷贝会改变执行时序，应减少探针并只比较 cache 的有效位。两侧按请求、层、生成步和张量语义对齐；近零值比对需要合理 atol，不能只给 rtol 或将不同请求的存储顺序直接对齐。

## 验证、回退与残留风险

修复后覆盖多请求、不等长、Prefill→Decode、真实路由、目标量化和图模式，保存首差异消失与任务精度信号。每次只改已定位的一项；失败回退相应模块和缓存状态。来源历史数值未给完整实验条件，本卡没有将它们当收益或精度保证，也没有执行 NPU 验证。

相关：[FA/KV 精度](precision_kvcache_fa_fusion_pitfalls.md)、[量化 scale 链](../../guides/integration/w8a8_mlp_and_moe_scale_flow.md)、[Mamba/GDN 状态](precision_mamba_gdn_linear_attention.md)、[gate 权重布局](../runtime/ge_graph_moe_gate_router_weight_layout.md)。

## Evidence

- [.agents/skills/model-infer-precision-debug/SKILL.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/.agents/skills/model-infer-precision-debug/SKILL.md)
- [models/longcat_flash/models/modeling_longcat_flash.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/longcat_flash/models/modeling_longcat_flash.py)
- [module/fuse_moe_gmm.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/module/fuse_moe_gmm.py)

- [integration/sglang/qwen3-next/README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/README.md)（supporting）

- [https://www.hiascend.com/document/detail/zh/mindstudio/80RC1/practicalcases/optimizationmodelinference/toolsample4_008.html](https://www.hiascend.com/document/detail/zh/mindstudio/80RC1/practicalcases/optimizationmodelinference/toolsample4_008.html)（supporting）
