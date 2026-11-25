---
{
  "type": "Runbook",
  "title": "MiniMax-H3 FL2VA 融合算子优化反致 denoise 变慢：npu_fusion_attention BSND 布局长序列回归",
  "description": "MiniMax-H3长序列注意力微基准中BSND慢于BNSD/SDPA；整网归因与修复收益尚未闭合，SwiGLU必须另核对半区语义，不能凭小幅度探针直接保留。",
  "tags": [
    "task.optimization",
    "topic.performance.analysis"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:04Z",
  "updated_at": "2026-11-23T06:30:53Z",
  "platforms": []
}
---


# MiniMax-H3 FL2VA 融合算子优化反致 denoise 变慢：npu_fusion_attention BSND 布局长序列回归

## 适用场景

Ascend NPU（4 卡 dispatch：text_encoder npu:0..1、33B DiT transformer npu:2..3）上以 diffusers（0.36.0.dev0，attention_dispatch 注册表）跑 MiniMax-H3 FL2VA 视频生成推理：56 头×128 head_dim、50 层+2 refiner、单序列 S≈42730 token、BF16。当给推理脚本叠加 torch_npu 融合算子补丁（npu_rms_norm / npu_swiglu / `DIFFUSERS_ATTN_BACKEND=_native_npu`）后 denoise 阶段整体变慢时适用。

## 触发与观测

- 触发（source 0 seq 1，用户报告）：融合算子优化后 `denoise.denoise -> denoise.after_denoise` 耗时从 1278.057s 增至 1405.22s。
- 日志比对（source 0 seq 264/270，工具读日志）：融合前 fl2va_4d_last_frame_1.log = 1278.057s；融合后 log_20260812_114832.log = 1405.220s、log_20260812_111320.log = 1406.032s（两日志含逐字行 `Patched nn.RMSNorm -> npu_rms_norm`、`Patched SwiGLU -> npu_swiglu`、`Switched attention backend to _native_npu (npu_fusion_attention BSND)`）。注意同日无融合跑 log_20260812_093317.log 为 1655.934s——同日基线本身波动大，比对必须用带 patch 标记的日志。
- profiling（source 0 seq 50/56，op_statistic.csv，profiling 那次未开融合）：FlashAttentionScore 72 次、23.34s、占 62.3%、avg 324ms/call；MatMulV3 21.6%；attention 是绝对大头。

## 探针与操作

- before 机制（source 0 seq 239，git diff 逐字）：问题脚本加了
```python
os.environ.setdefault("DIFFUSERS_ATTN_BACKEND", "_native_npu")
```
并在 `patch_fusion_ops()` 内：
```python
    from diffusers.models.attention_dispatch import _AttentionBackendRegistry, AttentionBackendName

    backend = os.environ.get("DIFFUSERS_ATTN_BACKEND", "native")
    if backend == "_native_npu":
        _AttentionBackendRegistry._active_backend = AttentionBackendName._NATIVE_NPU
        logger.info("Switched attention backend to _native_npu (npu_fusion_attention BSND)")
```
- 判别性微基准（source 0 seq 312，同机同 shape B=1,N=56,S=42730,D=128 BF16，warmup3 + 计时10 次均值）：
```python
    out2 = torch_npu.npu_fusion_attention(
        q2, k2, v2, N, input_layout='BSND', scale=1.0/float(D**0.5),
        pre_tockens=65536, next_tockens=65536, keep_prob=1.0, sync=False, inner_precise=0
    )[0]
```
  对照组：`F.scaled_dot_product_attention(q,k,v)`（BNSD）与 `npu_fusion_attention(..., input_layout='BNSD')`。
- 附带微基准（source 0 seq 307，shape [1,100,5376] BF16，100 次均值）：`torch_npu.npu_rms_norm(x, w, epsilon=1e-5)[0]` vs `torch.nn.functional.rms_norm`；SwiGLU 精度用典型 hidden 幅度（输入×0.02）比对。
- 历史编辑（source 0 seq332）：删除后端切换并保留RMSNorm/SwiGLU。这个历史决定不证明SwiGLU正确；采用前必须满足[半区交换与回退边界](../precision/npu_swiglu_gate_order_halves_swap.md)，原先未交换halves的补丁不能直接保留。

## 机制与判别

- 判别性结果（source 0 seq 313，逐字）：`SDPA (BNSD) [B=1,N=56,S=42730,D=128]: 329.5ms` / `npu_fusion_attention (BSND): 419.2ms` / `npu_fusion_attention (BNSD): 329.7ms`。同一 API 只改 `input_layout`：BSND 比 BNSD 慢 ~27%，而 SDPA≈BNSD——**布局是唯一判别变量**，慢的不是 npu_fusion_attention 算子本身而是 BSND 路径。基线profiling另记录288次Transpose（source 0 seq192/193），但seq265确认对应09:33运行没有融合补丁；该统计仅描述基线，不能证明启用 `_native_npu` 后的内部转置、次数或布局转换成本，后端实现层归因仍待带标记的独立profiling。
- 归因边界：同shape微基准支持BSND路径在该测试中较慢，但整网日志存在明显运行波动，未做去掉后端切换后的整网重跑。SwiGLU输入乘0.02的样例diff=0.000042只代表小幅度观测（seq318/319），不能证明半区语义等价；不得据此断言整网回归唯一来自attention，或建议原样保留未交换的SwiGLU。
- 混杂承认：profiling 数据（09:33）来自未开融合的跑，其 op 占比只用于确认 attention 占大头，不用于融合后归因；归因靠同 shape 微基准 + 带标记日志时间比对。

## 验证信号

- 设备级微基准（等级：设备功能+性能观测，单机单次）：attention 布局对比与 RMSNorm/SwiGLU 计时（source 0 seq 313/308，tool_observed）。
- e2e 日志（等级：用户跑批日志、工具读取）：1278.057s（无融合）vs 1405.220/1406.032s（融合，patch 标记在日志中逐字可查）；同日另一无融合跑 1655.934s 说明 run-to-run 波动大（source 0 seq 264/270）。
- 修复验证缺口：删除后端切换的编辑已应用（source 0 seq 332-333），但本轨迹内**没有修复后的 e2e 重跑**，e2e 恢复 1278s 量级属未验证预期；微基准预测的 ~90-120s 恢复为推断。

## 适用与失效边界

- 适用：diffusers attention_dispatch长序列负载下，先用真实shape对比SDPA/BNSD/BSND。RMSNorm微基准收益不替代整网精度；SwiGLU须确认gate半区并按[专门诊断卡](../precision/npu_swiglu_gate_order_halves_swap.md)修正，之后仍需端到端消融。
- 失效/不覆盖：27% 差值绑定本例 shape（S=42730, N=56, D=128, BF16, keep_prob=1.0, inner_precise=0, 单机）单次观测，短序列/其他 N、D 未必同向；e2e 修复收益未闭环；torch_npu/diffusers 版本升级后 BSND 路径可能改进，需按同法重测。

## 附：断言存档

- 本次B=1、N=56、S=42730、D=128、BF16的微基准：BSND419.2ms、BNSD329.7ms、SDPA329.5ms；仅支持该输入与条件下的布局差异。
- 整网日志回归尚无修复后重跑，不能唯一归因；SwiGLU的小幅度样例不证明gate语义一致，必须先核对半区交换。
