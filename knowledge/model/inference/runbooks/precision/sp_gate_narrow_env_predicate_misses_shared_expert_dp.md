---
type: Runbook
title: 序列并行(FlashComm V1)分支用只查环境变量的窄谓词门控：漏掉 shared_expert_dp 单开的 SP 强制耦合、静默走非 SP 布局致精度回归
description: 序列并行相关分支若只检查 FlashComm 环境变量，会漏掉 enable_shared_expert_dp 单独开启时强制启用 SP 的语义，导致 MoE+EP 张量在部分代码走 SP、部分代码走非 SP 布局，token 数、padding 和 all-gather 不一致并静默产生精度回归。修复是让 forward context、linear op、shared-expert、worker、dummy run 和平台断言统一调用 enable_sp(vllm_config, enable_shared_expert_dp)，编译 pass 场景再与 enable_sp_by_pass 取并集，同时删除窄谓词。适用失败签名为 shared_expert_dp=true、FlashComm 环境变量均关闭时无错误但 accuracy 下降；核心原则是 SP 谓词必须覆盖环境开关、shared-expert 耦合和编译 pass 三类来源。
tags:
- task.debugging
- topic.mixture_of_experts
- topic.parallelism
- topic.precision
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/6883
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 序列并行(FlashComm V1)分支用只查环境变量的窄谓词门控：漏掉 shared_expert_dp 单开的 SP 强制耦合、静默走非 SP 布局致精度回归

## 信号（现象）

MoE 模型跑 [expert-parallel](../../concepts/parallelism/expert_parallel.md) + 共享专家走 DP（`enable_shared_expert_dp: true`），而 FlashComm 相关环境变量都关着，推理**不报错、不告警，但输出精度回归**（accuracy issues）。表象是「模型能正常 serve、能返回、只是答案变差」——没有崩溃、没有 shape 报错，只有数值精度退化。

适用条件：
- 后端为 vllm-ascend（vLLM 昇腾后端），workload 为 MoE + [序列并行(SP/FlashComm V1)](../../concepts/parallelism/sp_tp_sp.md)；
- 打开了 `enable_shared_expert_dp`，但**没有**显式设 `VLLM_ASCEND_ENABLE_FLASHCOMM1` / `VLLM_ASCEND_ENABLE_FLASHCOMM`（二者均为 0）；
- 精度回归由「配置层面本该走 SP、实际部分路径走了非 SP 布局」造成，而非量化/算子本身的数值问题。

不适用：观测到崩溃、shape 报错、或未开 `enable_shared_expert_dp` 时，属其它信号。

## 触发条件

同一份代码里存在两个**语义不同**的 SP 门控谓词，而 SP 相关分支被误挂到了「窄」的那个：

- **窄谓词（只查环境变量）**：`enable_flash_comm_v1()`，语义 = `VLLM_ASCEND_ENABLE_FLASHCOMM1 OR VLLM_ASCEND_ENABLE_FLASHCOMM`。它只反映「用户是否显式设了 FlashComm 环境变量」。
- **广义谓词（反映 SP 实际是否生效）**：`enable_sp(vllm_config=None, enable_shared_expert_dp=False)`。它在环境变量之外，还编码了一条**强制耦合**：若调用方传入 `enable_shared_expert_dp=True` 且此前 `_ENABLE_SP` 为 False，则强制置 `_ENABLE_SP = True`，并打印 `shared_expert_dp requires enable_sp = True`。即「shared_expert_dp 单开 ⇒ SP 必须开」这条耦合**只在广义谓词里成立**。

触发点：当 `enable_shared_expert_dp=True` 且两个 FLASHCOMM 环境变量都为 0 时，两谓词发散——广义 `enable_sp(...)` 返回 True，窄 `enable_flash_comm_v1()` 返回 False。任何本该按「SP 是否实际生效」门控、却误用了窄谓词的分支，此时都会**静默跳过 SP 路径**。

复现配置：

```bash
vllm serve DeepSeek-V2-Lite-W8A8 \
  --tensor-parallel-size 2 --data-parallel-size 2 \
  --enable-expert-parallel --enforce-eager \
  --additional-config '{"enable_shared_expert_dp": true}'
# 且 VLLM_ASCEND_ENABLE_FLASHCOMM1=0 且 VLLM_ASCEND_ENABLE_FLASHCOMM=0
```

## 根因

SP 的**真实启用条件不是**「用户是否设了 FlashComm 环境变量」，而是「SP 在本次运行是否实际生效」——后者除环境变量外，还包含 `enable_shared_expert_dp` 单开这条强制耦合（以及 SP 编译 pass 路径）。用只查环境变量的窄谓词门控 SP 分支，等于丢掉了这条耦合：`enable_shared_expert_dp` 会在别处把模型置于「SP 已生效」的假设下运行，而窄谓词却让一部分 SP 分支以为「SP 没开」。

被这条发散影响、会漏走 SP 的典型分支（都因门控条件返回 False 而跳过 SP 逻辑）：

- `ascend_forward_context` 里 `flash_comm_v1_enabled` 的计算——决定后续 context 是否按 SP 走；
- `linear_op.py::apply_impl`——是否执行 `maybe_all_gather_and_maybe_unpad`（SP 下对序列维做 all-gather + unpad 还原全长）；
- 列/行并行 op 选择 `_get_column_parallel_op` / `_get_row_parallel_op`——是否返回 SP 版 op、以及是否对 `shared_expert` 前缀返回 None（共享专家在 SP 下的特殊处理）；
- `worker.py::execute_model`——是否把 `all_gather_group` 置 None；
- `model_runner_v1.py::_dummy_run`——intermediate_tokens 是否按 `tp_size` 切分；
- `platform.py` 的 VL 模型断言。

后果的机理：一旦这些分支与其余**仍按 SP 假设运行**的部分不一致，token 数 / padding / all-gather 与实际张量布局就会**错配**——序列维该被切分/all-gather 的地方没切、该 unpad 的地方没还原，模型跑在半 SP 半非 SP 的混合布局上，数值上表现为精度回归。因为 shape 在各分支内部仍自洽（只是全局语义错），所以**不崩溃、只掉精度**。

## 修法

**把所有反映「SP 是否实际生效」的分支统一收敛到广义谓词，杜绝窄谓词与广义谓词并存导致的发散。** 具体：

1. 把误挂在 `enable_flash_comm_v1()` 上的 SP 门控**全部改回** `enable_sp(...)`（本参考实现涉及 7 个文件：`utils.py`、`ops/linear_op.py`、`ascend_forward_context.py`、`worker/worker.py`、`worker/model_runner_v1.py`、`platform.py` 等）。
2. **删除只查环境变量的窄谓词函数本身**（`enable_flash_comm_v1()`），把其环境变量判断**内联进** `enable_sp` 的 `_ENABLE_SP` 计算，使全仓 SP 门控**只有一个**广义谓词、不再可能发散。
3. 对同时受 SP 编译 pass 影响的路径（如 padding 判定），门控用**并集**覆盖：`enable_sp(self.vllm_config) or enable_sp_by_pass(self.vllm_config)`（如 `model_runner_v1.py::_pad_for_sequence_parallelism` 需把 SP 编译 pass 也纳入 padding 判定）。

修法本质是一条可迁移原则：**给 SP 相关分支挑门控谓词时，谓词必须能反映 SP 的全部实际启用来源（环境变量 + shared_expert_dp 强制耦合 + SP 编译 pass），而不能只查其中一个来源的窄条件。** 让「使能来源」收敛到单一广义谓词，避免同一语义存在宽窄两套谓词、在边角配置下发散。

### 正确性验证

`enable_shared_expert_dp=True` + FLASHCOMM 环境变量全 0 的配置下 serve 起来，检查 SP 路径确实生效（日志 `shared_expert_dp requires enable_sp = True` 应打印、`enable_sp(...)` 应返回 True），并对齐一份「SP 显式开启」或「已知正确」的输出做数值比对。

## 相关经验

- SP 相关的另一类静默不生效见 [MoE 优化/并行在 decode 静默不生效的四类根因](../performance/moe_optimization_silently_disabled_decode.md)——配了不报错但不生效的传播链核查，其中并行使能误挂 `is_prefill` 一类与本页同属「门控谓词选错致静默失效」。
- SP + 联合 token 注意力的精度陷阱见 [hybrid SP 联合 token 注意力精度](precision_hybrid_sp_joint_token_attention.md)。

## Evidence

- 门控从 `enable_flash_comm_v1()` 改回 `enable_sp(...)`（7 文件），且窄谓词函数整体删除、环境变量判断内联进 `enable_sp` 的 `_ENABLE_SP` 计算；`utils.py` 中 `enable_sp` 函数体含 `if not _ENABLE_SP and enable_shared_expert_dp: _ENABLE_SP = True` 与日志 `shared_expert_dp requires enable_sp = True`：合并态 diff 事实 + PR body 明述根因（先前一次改动误把 `enable_sp` 分支替换成 `enable_flash_comm_v1`，`enable_shared_expert_dp` 单开时导致 accuracy issues）@sha 5e24b26a543ae7ab92f7304c127ef27d43420369（state MERGED）。溯源下探 [vllm-ascend-pr-6883-bugfix-rename-enable-flash-comm-v1-back-to-enable-sp](https://github.com/vllm-project/vllm-ascend/pull/6883)。
- 证据强度：源仅给定性判据（accuracy issues → recovered expected behavior and accuracy），未给 before→after 数值精度指标。
- 范围限定：结论仅适用于 vllm-ascend 的 SP/FlashComm-V1 与 shared_expert_dp 门控，未外推到其它谓词或其它硬件。
