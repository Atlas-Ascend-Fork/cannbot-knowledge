---
{
  "type": "Runbook",
  "title": "Wan2.1 flash_attention 接入 torch_npu.npu_fused_infer_attention_score（BSND，非因果 MHA）",
  "description": "模型/框架：Wan2.1-T2V-1.3B DiT（12 头 × head_dim 128，标准 MHA，非因果注意力）+ torch_npu 2.8.0（CANN 8.5.0），单卡 NPU 推理；原实现依赖 flash_attn 2/3（NPU 容器未安装）。；任务：t2v-1.3B 832×480、81 帧、50 步采样端到端生成。",
  "tags": [
    "task.implementation",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": []
}
---

# Wan2.1 flash_attention 接入 torch_npu.npu_fused_infer_attention_score（BSND，非因果 MHA）

## 适用场景

- 模型/框架：Wan2.1-T2V-1.3B DiT（12 头 × head_dim 128，标准 MHA，非因果注意力）+ torch_npu 2.8.0（CANN 8.5.0），单卡 NPU 推理；原实现依赖 flash_attn 2/3（NPU 容器未安装）。
- 任务：t2v-1.3B 832×480、81 帧、50 步采样端到端生成。
- 缺失信息：NPU 具体型号未记录。

## 触发与观测

适配目标：原 `wan/modules/attention.py` 的 `flash_attention` 在 flash_attn 缺失时不可用，且含 CUDA 断言。无失败日志（属主动适配，非故障修复）。相关客观观测为端到端运行信号（见验证信号）。

## 探针与操作

参数推导（source 0 seq 61）：head_dim=1536/12=128；q/k/v 在打包前已是 `[B, S, N, D]`（BSND），选择 BSND 免去 TND 的累积和要求与重排；`scale=1/sqrt(128)`（softmax_scale=None 时与 flash_attn 默认一致）；MHA `num_heads=nq`（不传 num_key_value_heads 即等价 0/GQA 关闭）；非因果；`k_lens → actual_seq_lengths_kv`（`.tolist()`）。

实现（source 0 seq 87，修改后文件逐字内容，NPU 分支）：

```python
    # NPU path: use torch_npu.npu_fused_infer_attention_score with BSND layout
    if TORCH_NPU_AVAILABLE and q.device.type == 'npu':
        out_dtype = q.dtype

        def half(x):
            return x if x.dtype in half_dtypes else x.to(dtype)

        b, lq, nq, c1 = q.shape

        q = half(q).contiguous()
        k = half(k).contiguous()
        v = half(v).contiguous()

        if q_scale is not None:
            q = q * q_scale

        scale = softmax_scale if softmax_scale is not None else 1.0 / math.sqrt(c1)
        actual_seq_lengths = q_lens.tolist() if q_lens is not None else None
        actual_seq_lengths_kv = k_lens.tolist() if k_lens is not None else None

        attn_out, _ = torch_npu.npu_fused_infer_attention_score(
            q, k, v,
            num_heads=nq,
            scale=scale,
            input_layout="BSND",
            actual_seq_lengths=actual_seq_lengths,
            actual_seq_lengths_kv=actual_seq_lengths_kv,
        )
        return attn_out.to(out_dtype)
```

类型参数来自完整函数签名（source 0 seq 87）：`dtype=torch.bfloat16`，入口定义 `half_dtypes=(torch.float16, torch.bfloat16)` 并断言 `dtype` 属于该集合。`half(x)` 对已为 FP16/BF16 的输入返回原张量，仅其他类型执行 `x.to(dtype)`；例如 FP32 输入在 `dtype=torch.float16` 时转 FP16，在缺省参数时转 BF16。最后 `attn_out.to(out_dtype)` 转回原始 `q.dtype`，不能用最终返回类型推断内部计算类型。source 0 seq 38 的 self/cross 调用未显式传 `dtype`，因此采用该缺省转换参数；这不是逐项输入 dtype 的运行时探针。

同时 `attention()` 入口分支由 `FLASH_ATTN_2/3_AVAILABLE` 扩为 `TORCH_NPU_AVAILABLE or ...`，在 NPU 调用条件满足时进入该分支；`text2video.py`/`generate.py` 加 `import torch_npu`/`transfer_to_npu`、device 改 `npu:{id}`、`torch.cuda.*` 改 `torch.npu.*`、nccl→hccl（source 0 seq 72-84）。

## 机制与判别

- 布局选择依据：Wan 的 q/k/v 天然 BSND，直接 `input_layout="BSND"` + contiguous，避免 TND 布局的 `actual_seq_lengths` 累积和构造（source 0 seq 61 推理记录，agent_narrative；最终以端到端运行为客观信号）。
- 长度参数按调用点区分：本版 WanSelfAttention 传入 `k_lens=seq_lens`，`q_lens` 缺省；cross-attention 传入 `k_lens=context_lens`，本版 `model.forward` 将 `context_lens` 设为 `None`（source 0 seq 38 的完整 `model.py`）。NPU 分支仅对非空长度调用 `.tolist()`；不能因 batch 为 1 推断长度参数被省略。
- 与 flash_attn 2/3 的数值等价性未做逐算子比对；本轨迹的直接探针仅能确认一次端到端运行的完成日志和输出文件，未检查视频质量。

## 验证信号

- 直接探针：source 0 seq 314/315 的 `tail/ls` 调用及工具返回展示 50/50 进度、保存提示、`INFO: Finished.` 和大小显示为 2.8M 的输出文件；进度条末段显示约 5.67 s/step（单次运行，tool_observed）。这是日志及文件检查，不是后台推理进程退出码的直接返回。
- 任务通知：seq 320 报告后台重跑 completed、exit 0；该事件归一化为 `unknown`。seq 307/310 也是保留的通知，不将它们标作直接工具观测。
- seq 321 的“全部 50 步经过 NPU FlashAttention”是助手汇总；没有逐步、逐算子调用计数或回退探针，不能据此证明 50 步 ×2 前向全量生效或全程无回退。
- 无性能基线、逐算子数值对照或视频质量评测；本卡记录适配代码和一次端到端完成记录，不声称加速或数值等价。

## 适用与失效边界

- 本轨迹范围：Wan2.1 的非因果 MHA、head_dim=128，q/k/v 已是 BSND 且可 contiguous，所示调用使用缺省转换参数 `dtype=torch.bfloat16`；有一次端到端完成记录，未逐项记录输入张量 dtype。其他 DiT、逐算子覆盖率与数值正确性需另行验证。
- 失效/风险：`window_size`/`deterministic`/`causal=True` 等 flash_attn 参数在该 NPU 分支中被忽略（未实现映射），带这些参数的调用语义不等价；非 FP16/BF16 输入在 helper 中转为实参 `dtype` 指定的类型，已是 FP16/BF16 则不转换，返回值再转回原始 q 类型，精度敏感路径需核对调用参数和实际输入；GQA（Nq≠Nk）场景未在本轨迹验证。
- 依赖版本：torch_npu 2.8.0 / CANN 8.5.0。seq 315 的直接日志含 `aten::_linalg_solve_ex.result` 回退 CPU 告警；seq 232 的监控通知报告 autocast 目标 dtype 不受支持而被禁用，seq 295 的监控通知报告 CPU fallback，两者均归一化为 `unknown`。这些记录可作后续排查线索，不能推出所有张量全程保持 bf16 或该注意力路径没有回退。

## 附：断言存档

- Wan2.1 非因果 MHA（head_dim=128）可在 flash_attention 内以 BSND 布局直连 torch_npu.npu_fused_infer_attention_score（num_heads=nq、scale=1/sqrt(128)、q_lens/k_lens→actual_seq_lengths(_kv).tolist()），q/k/v contiguous 无需重排。
- 直接日志及文件探针展示 t2v-1.3B 单次运行 50/50、保存提示、Finished 和输出文件（source 0 seq 315）；后台 exit 0 仅由 seq 320 的 unknown 任务通知报告。没有逐算子全覆盖或无回退的独立验证。

```text
    # NPU path: use torch_npu.npu_fused_infer_attention_score with BSND layout
63	    if TORCH_NPU_AVAILABLE and q.device.type == 'npu':
64	        out_dtype = q.dtype
65
66	        def half(x):
67	            return x if x.dtype in half_dtypes else x.to(dtype)
68
69	        b, lq, nq, c1 = q.shape
70
71	        q = half(q).contiguous()
72	        k = half(k).contiguous()
73	        v = half(v).contiguous()
74
75	        if q_scale is not None:
76	            q = q * q_scale
77
78	        scale = softmax_scale if softmax_scale is not None else 1.0 / math.sqrt(c1)
79	        actual_seq_lengths = q_lens.tolist() if q_lens is not None else None
80	        actual_seq_lengths_kv = k_lens.tolist() if k_lens is not None else None
81
82	        attn_out, _ = torch_npu.npu_fused_infer_attention_score(
83	            q, k, v,
84	            num_heads=nq,
85	            scale=scale,
86	            input_layout="BSND",
87	            actual_seq_lengths=actual_seq_lengths,
88	            actual_seq_lengths_kv=actual_seq_lengths_kv,
89	        )
90	        return attn_out.to(out_dtype)
91
92
```
