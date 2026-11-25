---
{
  "type": "Runbook",
  "title": "torch_npu.npu_rotary_mul 部分旋转限制：ro_dim < head_dim 时 tiling 拒绝（x[128] vs cos[96]）",
  "description": "模型/框架：daVinci-MagiHuman（DiT 视频生成，15B，40 层）DiT denoiser RoPE 融合尝试；daVinci-MagiHuman_gitcode 工作目录（progress.md 记录环境 PyTorch 2.10.0 / torch_npu 2.10.0 / CANN 9.0.0，单卡可见）。",
  "tags": [
    "task.testing",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-20T14:17:06Z",
  "platforms": []
}
---

# torch_npu.npu_rotary_mul 部分旋转限制：ro_dim < head_dim 时 tiling 拒绝（x[128] vs cos[96]）

## 适用场景

- 模型/框架：daVinci-MagiHuman（DiT 视频生成，15B，40 层）DiT denoiser RoPE 融合尝试；daVinci-MagiHuman_gitcode 工作目录（progress.md 记录环境 PyTorch 2.10.0 / torch_npu 2.10.0 / CANN 9.0.0，单卡可见）。
- 任务：以 `npu_rotary_mul` 替换手动 `apply_rotary_emb_torch`（rotate_half + repeat + cat）的轻量融合扫描。
- 缺失信息：本目录 NPU 型号未直接记录（progress.md 称单卡、SP 需 device_count>=2 被 block）。

## 触发与观测

端到端 T2V 打开 RoPE 融合后，每个注意力层均出现算子级失败并被 fallback 捕获（source 0 seq 237，tool_observed 逐字）：

```text
[Warning] RoPE NPU fusion failed, fallback to torch: npu_rotary_mul:../third_party/op-plugin/op_plugin/ops/opapi/RotaryMulKernelNpuOpApi.cpp:65 NPU function error: call aclnnRotaryPositionEmbeddingV2 failed, error code is 561103
[ERROR] 2026-06-11-17:09:18 (PID:352063, Device:0, RankID:0) ERR00100 PTA call acl api failed.
EZ9999: Inner Error!
EZ9999[PID: 352063] ... (EZ9999):  input last dim (head_dim) should be equal, but get x [128] and cos [96].[FUNC:CheckShapeSupport][FILE:rope_rotate_half_tiling.cpp][LINE:426]
       input shape does not meet the requirements.[FUNC:DoRotateHalfTiling][FILE:rope_rotate_half_tiling.cpp][LINE:509]
```

## 探针与操作

尝试的替换实现（source 0 seq 199，编辑文本逐字）：

```python
def apply_rotary_emb_npu(x, cos, sin):
    """
    NPU fusion version: apply_rotary_emb_torch -> npu_rotary_mul
    x: (1, seqlen, nheads, headdim)
    cos, sin: (seqlen, rotary_dim / 2)

    Prerequisites:
    - ro_dim == headdim (RoPE covers full dimension)
    - cos/sin in [-1, 1] range (satisfied by cos/sin functions)
    - interleaved=False (half mode)
    """
    # Expand cos/sin to match x layout: [L, D/2] -> [1, L, 1, D]
    cos_expanded = repeat(cos, "l d -> l 1 (2 d)")  # [L, 1, D]
    sin_expanded = repeat(sin, "l d -> l 1 (2 d)")  # [L, 1, D]
    cos_final = cos_expanded.unsqueeze(0).to(x.dtype)  # [1, L, 1, D]
    sin_final = sin_expanded.unsqueeze(0).to(x.dtype)  # [1, L, 1, D]
    return torch_npu.npu_rotary_mul(x, cos_final, sin_final, rotary_mode="half")
```

前置单测（合成数据，ro_dim==head_dim==128 全维旋转）：初次用 randn 生成 cos/sin（越界 [-1,1]）最大差 5.2e-2；改用真实频率 band 后 max diff 1.848e-02 / mean 1.430e-03，在放宽到 5e-2（BF16 容差）后通过（source 0 seq 157、192，tool_observed；阈值由 1e-3 放宽为 agent 决策）。

## 机制与判别

- 失败根因：该模型 `ElementWiseFourierEmbed` 输出为 6×B=96 维（B=dim//8=16），rope 只覆盖 head_dim=128 的前 96 维（部分旋转），`npu_rotary_mul(rotary_mode="half")` 的 tiling 检查要求 x 末维 == cos/sin 末维，96≠128 直接被 `CheckShapeSupport` 拒绝（source 0 seq 237、258、259）。
- 可区分分支：错误定位在 tiling 形状检查（rope_rotate_half_tiling.cpp:426）而非 dtype/workspace；同一实现对全维（128==128）合成数据可正常出结果（seq 192），证明失败由部分旋转维度不匹配触发，不是算子不可用或 cos/sin 数值越界单因导致（合成越界只造成精度差、不报错）。
- 精度边界（附加观测）：BF16 下全维替换与 torch 实现最大绝对差 ~1.8e-2、均值 ~1.4e-3（单测、合成数据、BF16，单次）；1e-3 阈值不适用，需按 BF16 容差评估。
- 未验证推断：对 96 维部分旋转先 pad cos/sin 到 128 再切片是否可行，本轨迹未尝试。

## 验证信号

- 失败信号：如上逐字算子错误，每次注意力前向重复出现（source 0 seq 237，tool_observed）。
- fallback 有效：`try/except` 捕获后回退 torch 路径，运行完成，denoise 43.092s（source 0 seq 237 后段 Time Elapsed，tool_observed；与开启融合的期望收益无关，仅证明回退保住了可用性）。
- 本候选为 negative_result：该替换路线在此模型结构下不可采用，不声称任何加速。

## 适用与失效边界

- 适用结论：`npu_rotary_mul` 仅当 RoPE 覆盖全部 head_dim（ro_dim==head_dim）时可用；部分旋转 RoPE（如本例 FourierEmbed 6×B=96 < 128）在 tiling 阶段被硬性拒绝。规划 RoPE 融合前应先核对 rope 输出维度公式与 head_dim 的关系，勿只看接口签名。
- 失效/风险：cos/sin 需在 [-1,1]（文档约束）；BF16 精度容差需按 1e-2 量级评估；本观测基于 torch_npu 2.10.0/CANN 9.0.0 记录环境，版本升级可能放开限制（未验证）。
- 回退条件：保留 torch 原实现 fallback；或改造 RoPE 为全维旋转后重试（属模型结构改动，本轨迹未做）。

## 附：断言存档

- npu_rotary_mul(rotary_mode="half") 的 tiling 检查要求 x 末维==cos/sin 末维：daVinci-MagiHuman ElementWiseFourierEmbed 输出 6*B=96 维部分旋转 (head_dim=128) 时，aclnnRotaryPositionEmbeddingV2 报 561103：input last dim (head_dim) should be equal, but get x [128] and cos [96] (rope_rotate_half_tiling.cpp:426)。

```text
def apply_rotary_emb_npu(x, cos, sin):\n    \"\"\"\n    NPU fusion version: apply_rotary_emb_torch -> npu_rotary_mul\n    x: (1, seqlen, nheads, headdim)\n    cos, sin: (seqlen, rotary_dim / 2)\n    \n    Prerequisites:\n    - ro_dim == headdim (RoPE covers full dimension)\n    - cos/sin in [-1, 1] range (satisfied by cos/sin functions)\n    - interleaved=False (half mode)\n    \"\"\"\n    # Expand cos/sin to match x layout: [L, D/2] -> [1, L, 1, D]\n    cos_expanded = repeat(cos, \"l d -> l 1 (2 d)\")  # [L, 1, D]\n    sin_expanded = repeat(sin, \"l d -> l 1 (2 d)\")  # [L, 1, D]\n    cos_final = cos_expanded.unsqueeze(0).to(x.dtype)  # [1, L, 1, D]\n    sin_final = sin_expanded.unsqueeze(0).to(x.dtype)  # [1, L, 1, D]\n    return torch_npu.npu_rotary_mul(x, cos_final, sin_final, rotary_mode=\"half\"
```
