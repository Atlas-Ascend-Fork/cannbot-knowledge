---
{
  "type": "Runbook",
  "title": "GPT-2 系模型 QKV 三投影融合单 GEMM（保留 custom_query 末层）的 decode 加速",
  "description": "对 GPT-2 系 eager attention 在任务碎片固定开销主导的 bs=1 decode 场景，将 q/k/v 三个同输入投影合并为单 GEMM [3H,H]（权重行拼接、数值等价），q 输入不同的末层（custom_query）保留不融合。pangu_2_6B 31/32 层融合后 L0 门禁 8/8 cos=1.000000，TPOT 中位 29.433→27.477ms（-6.6%）、吞吐 +7.1%；代价是峰值显存 9.99→12.30GB。",
  "tags": [
    "task.implementation",
    "topic.model_serving"
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
# GPT-2 系模型 QKV 三投影融合单 GEMM（保留 custom_query 末层）的 decode 加速

## 适用场景

- 模型/框架：GPT-2 系 eager attention（q/k/v 为三个同输入的独立 nn.Linear+bias），PyTorch + torch_npu 路线的 NPU 推理。
- 本例：imone/pangu_2_6B（32 层 × hidden 2560 × 32 头 head_dim=80），fp32，Ascend950PR_9589 单卡，CANN 9.1.0 + 950-ops，torch_npu 2.12.0.post2。
- 负载：bs=1、prompt 17 token、greedy 生成 16 token 的 decode；eager、无并行。
- 前提（重要）：诊断提出任务下发与执行粒度开销的假设，尚未隔离算力/带宽等因素（见 [小 batch decode 的 bf16 负结果与任务下发开销排查](decode_bf16.md) 的判别实验）；融合目标是减少线性投影调用：32 层原有 96 次 Q/K/V 投影，31 层各由 3 次变 1 次、末层保留 3 次，理论变为 34 次（减少 62 次）。这不是重新统计的设备 kernel 任务数。

路径补充：`${WORK_ROOT}` 为本地推理迁移/性能实验工作根，包含文中 mia、venv 与 task-workspace 相对目录。按本地环境设置变量，保留文中的相对路径关系。

## 触发与观测

- 事件 761/768：matmul 类占设备时间 88.9%，但 bf16 单因子探针（事件 778：TPOT 29.797ms vs 基线 29.433ms，来源约定不计可靠差异）未取得时延收益；仅凭该实验不能证伪算力瓶颈或确定时延地板。
- 来源提案用每任务约 40µs 估计融合收益，但该固定开销没有直接测量，且提案未按最终 31 层实现核对调用数；不将其作为性能上界。

## 探针与操作

实现为运行时单因子变换：只新增融合模块 + 替换 forward，不改原始权重，可逆（重新加载即回退）。完整实现（事件 785 写入的 opt_qkv_fuse.py 全文逐字）：

```
#!/usr/bin/env python3
"""候选 C2-qkv-fuse（S3 融合域，单因子）:
将 GPTPanguAttention 的 q/k/v 三投影融合为单 GEMM [3H,H]（仅 q/k/v 同输入的层）。
最后一层使用 wqe custom_query（q 输入≠kv 输入）→ 保持原实现不融合（拓扑保真项）。
数值等价: 权重按行拼接, 单 addmm 逐行累加语义与分立 addmm 一致。
"""
import types

import torch
from torch import nn


def _fused_forward(self, hidden_states, layer_past=None, attention_mask=None,
                   head_mask=None, custom_query=None, use_cache=False,
                   output_attentions=False):
    # 与原实现逐行对齐（modeling_gptpangu.py:95-133），仅 q/k/v 来源替换
    qkv = self.qkv_proj(custom_query if custom_query is not None else hidden_states)
    query, key, value = qkv.split(self.embed_dim, dim=-1)

    query = self._split_heads(query, self.num_heads, self.head_dim)
    key = self._split_heads(key, self.num_heads, self.head_dim)
    value = self._split_heads(value, self.num_heads, self.head_dim)

    if layer_past is not None:
        past_key, past_value = layer_past
        key = torch.cat((past_key, key), dim=-2)
        value = torch.cat((past_value, value), dim=-2)

    present = (key, value) if use_cache else None

    attn_output, attn_weights = self._attn(query, key, value, attention_mask, head_mask)
    attn_output = self._merge_heads(attn_output, self.num_heads, self.head_dim)
    attn_output = self.c_proj(attn_output)
    attn_output = self.resid_dropout(attn_output)

    outputs = (attn_output, present)
    if output_attentions:
        outputs += (attn_weights,)
    return outputs


def apply(model):
    """返回 (融合层数, 变更描述)。可逆性: 只新增模块+替换 forward, 不改原权重。"""
    n = 0
    layers = model.transformer.h
    hidden = model.transformer.embed_dim
    for i, block in enumerate(layers):
        if i == len(layers) - 1:
            continue  # 最后一层 custom_query 语义, 不融合
        attn = block.attn
        fused = nn.Linear(hidden, 3 * hidden, bias=True,
                          device=attn.q_proj.weight.device,
                          dtype=attn.q_proj.weight.dtype)
        with torch.no_grad():
            fused.weight.copy_(torch.cat(
                [attn.q_proj.weight, attn.k_proj.weight, attn.v_proj.weight], dim=0))
            fused.bias.copy_(torch.cat(
                [attn.q_proj.bias, attn.k_proj.bias, attn.v_proj.bias], dim=0))
        attn.qkv_proj = fused
        attn.forward = types.MethodType(_fused_forward, attn)
        n += 1
    return n, f"qkv fused on {n}/{len(layers)} layers (last layer kept for custom_query)"
```

验证命令（单因子入口 --opt qkv-fuse；先 L0 精度门禁再 P0 性能复检，均逐字）：

```
. ${WORK_ROOT}/mia/scripts/setup_env.sh && cd ${WORK_ROOT} && venv/bin/python mia/scripts/precision_l0.py task-workspace/models/pangu_2_6B --dtype fp32 --opt qkv-fuse 2>&1 | grep -vE "Warning|warn|GenerationMixin|owner|👉|auto class|related|trust_remote_code|jieba|prefix|Loading" | tail -16; echo exit=$?
```

```
. ${WORK_ROOT}/mia/scripts/setup_env.sh && cd ${WORK_ROOT} && venv/bin/python mia/scripts/bench.py task-workspace/models/pangu_2_6B npu npu-c2-qkvfuse-fp32 --prompt-id s03 --rounds 10 --warmup 3 --opt qkv-fuse --note "candidate C2" 2>&1 | grep -vE "Warning|warn|GenerationMixin|owner|👉|auto class|related|trust_remote_code|jieba|prefix|Loading" | tail -22
```

## 机制与判别

- 数值等价性：融合权重 = [Wq; Wk; Wv] 按行拼接 + bias 拼接，单 addmm 后 split(embed_dim)，与三个独立 addmm 的逐行累加语义一致 → L0 实测 cos=1.000000（事件 816）。
- 末层 custom_query 保真：GPTPangu 最后一层 block 的 q 输入来自 wqe(position_ids) 而非 hidden_states（q 输入≠kv 输入），按本方案融合会改变语义 → 该层跳过，31/32 层融合。
- 收益观测：31 层 Q/K/V 线性投影理论减少 62 次调用，TPOT 下降约 6.6%。实际设备 kernel 数未重新统计；融合也改变 GEMM 形状和存储行为，无法把全部收益归给固定任务开销。
- 显存代价（混杂因素须承认）：变换会新增 [3H,H] 融合权重副本且不删除原 q/k/v 权重 → 峰值显存上升；生产部署可改为删除原始三权重以省回。

结论（性能判）：在 pangu_2_6B fp32、bs=1、prompt 17 token、greedy 生成 16 token 的 decode 场景，QKV 三投影融合（31/32 层，末层保留 custom_query 不融合）使 TPOT 中位数从 29.433ms 降至 27.477ms（-6.6%），吞吐从 33.98 升至 36.39 tok/s（+7.1%）。

结论（等价判）：融合变换在实数代数上等价；已测样本的 L0 门禁 8/8 PASS，logit 余弦 1.000000；一键复现与回归套件复检 TPOT 中位 27.642ms 稳定。

结论（代价判）：融合的显存代价：峰值显存从 9.994GB 升至 12.298GB（新增 [3H,H] 融合权重副本且原 q/k/v 权重未删除）。

## 验证信号

- 事件 816：L0 门禁 8/8 PASS（cos=1.000000，exit=0；验证前提检查断言融合层数 n>0）。
- 事件 820：TPOT 中位 27.477ms（基线 29.433ms，-6.6%）、TTFT 中位 27.019ms、吞吐 36.39 tok/s、峰值 12.298GB。
- 事件 835：一键复现输出 `qkv fused on 31/32 layers (last layer kept for custom_query)`，生成文本与 golden 一致（sha 一致路径复现）。
- 事件 854：回归套件（L0 + P0 复检）TPOT 中位 27.642ms、REGRESSION GREEN。
- 基线信号：事件 675（npu-c0-fp32，同会话同口径 P0 协议：warmup 3 + 10 轮中位）。
- 平台 Ascend950PR_9589 / CANN 9.1.0 + 950-ops / torch_npu 2.12.0.post2；同会话可比基线、单次会话观测（收益条件：bs=1 decode、eager、任务开销主导）。

## 适用与失效边界

- 收益条件：任务碎片固定开销主导（bs=1/小 batch decode、eager 模式）；若算力/带宽主导（大 batch、prefill），单 GEMM 的任务数削减收益趋小（未测）。
- 结构边界：q/k/v 不同输入的层（custom_query、cross-attention）不可按此融合；有 RoPE 交错的实现须先核对投影输入是否同源。
- 资源边界：本实现峰值显存 +23%（9.99→12.30GB）；显存受限部署须删除原始三权重或换融合权重替换策略。
- 版本边界：固定开销与 aclnn 调度随 CANN/驱动漂移，跨版本须重跑判别与基准；head_dim=80 非 2 幂对 tile 效率的影响未单独评估。
- 停止/回退：变换可逆（重新加载模型即回退）；若 L0 出现 cos 下降或吐字异常，按硬 FAIL 回退并走逐层定位。
