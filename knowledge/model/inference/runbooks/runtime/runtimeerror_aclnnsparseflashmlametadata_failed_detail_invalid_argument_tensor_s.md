---
{
  "type": "Runbook",
  "title": "DSv4.1 vLLM-Ascend：融合算子 `_C_ascend.sparse_flash_mla` 路径不可用（metadata 形状 + worker SIGSEGV）",
  "description": "DSv4.1-Flash 在 vLLM-Ascend（Ascend950PR，DP4/EP4）尝试把 38/40 层注意力从 PyTorch 参考实现切到融合算子 `_C_ascend.sparse_flash_mla`",
  "tags": [
    "task.testing",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:03Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "950"
  ]
}
---

# DSv4.1 vLLM-Ascend：融合算子 `_C_ascend.sparse_flash_mla` 路径不可用（metadata 形状 + worker SIGSEGV）

## 适用场景

- 平台范围依据：source 0 seq 615、source 0 seq 617的实际环境/设备记录确认本次为Ascend 950；这里不扩展未记录的产品或版本。

DSv4.1-Flash 在 vLLM-Ascend（Ascend950PR，DP4/EP4）尝试把 38/40 层注意力从 PyTorch 参考实现切到融合算子 `_C_ascend.sparse_flash_mla`（`VLLM_ASCEND_V41_PYTORCH_ATTENTION=0`，P1 候选）以降低 decode 注意力成本（估计占 decode 步 100~120 ms 的主要份额）。

## 触发与观测

- 第一次启动：worker 在 `_build_sas_metadata → sparse_flash_mla_metadata` 处报 `RuntimeError: call aclnnSparseFlashMlaMetadata failed, detail: ... Invalid_Argument_Tensor_Shape_Size(EZ0014): Parameter metadata of aclnnSparseFlashMlaMetadata has incorrect shape size 1024. It should be 2048.`（source 0 seq 98，tool_observed）。
- 修正 metadata 缓冲为 2048 后重启：服务 READY，但首个 canary 批次全部失败——canary 结果 `{"completed": 6, "planned": 60, "correct": 0, "request_errors": 6}`，quick/official bench 全零（`status: invalid`，`p95_tpot_ms: 0.0`）；服务日志显示 `Worker proc VllmWorker-0 died unexpectedly (exit code: None)`，Python faulthandler 输出 C 栈转储（SIGSEGV），无 Python 异常帧（source 0 seq 399/421，tool_observed）。

## 探针与操作

- 探针 1（形状）：按报错把 SFA metadata 输出缓冲从 1024 恢复为默认 2048（source 0 seq 98 后续修正，seq 101 记录"installed aclnn kernel wants 2048"）。
- 探针 2（可用性）：修正后完整复跑 canary → quick → official 链，捕获 worker 死亡与 C 栈转储（source 0 seq 395-421）。
- 对照：同环境 `V41_PYTORCH_ATTENTION=1`（PyTorch 参考注意力）全链路正常（后续全部验收基于该路径）。

## 机制与判别

- 两级失败可区分：EZ0014 是适配层参数形状错误（可修）；修正后的 SIGSEGV 发生在融合 kernel 首次 forward（10 token 首请求），是 C 级崩溃，Python 层无法捕获——疑似适配层 ABI（`cmp_residual_kv`/`seqused_cmp_kv`/max_seqlen 传参）问题导致 kernel 读非法内存（假设，未用最小用例证实）。
- 判别：崩溃仅在融合路径出现；同配置切回 PyTorch attention 立即恢复，排除硬件与环境因素。

## 验证信号

- 全部为服务日志/canary 结果原始输出（tool_observed）；P1 候选据此被判定"淘汰"，最终交付使用 `V41_PYTORCH_ATTENTION=1` + mHC Triton（见 w03-s1-c1）。

## 适用与失效边界

- 绑定当前 vllm_ascend `sparse_flash_mla` 绑定（aclnn SparseFlashMla 算子版本）；aclnn/适配层修复后需用本探针链（metadata=2048 → canary 10 token 请求）重验。
- 负结果只主张"该版本组合下融合路径不可用于 DSv4.1 服务"；不外推到其他模型或其他 aclnn 注意力融合算子。
- SIGSEGV 根因（ABI vs kernel 内部缺陷）未定位，修复建议仅为"回退 PyTorch 路径"。

## 附：断言存档

- 融合路径第一次失败：aclnnSparseFlashMlaMetadata EZ0014——metadata 参数 shape size 1024 应为 2048（适配层缓冲尺寸错误，可修）

```text
RuntimeError: call aclnnSparseFlashMlaMetadata failed, detail:[PID: 90599] 2026-11-04-17:35:40.825.094 Invalid_Argument_Tensor_Shape_Size(EZ0014): Parameter metadata of aclnnSparseFlashMlaMetadata has incorrect shape size 1024. It should be 2048.
```
