---
{
  "type": "Runbook",
  "title": "veRL DAPO 开启 use_kl_in_reward 后 KeyError response_mask：宿侧 batch 字段缺失的定界与排除设备侧判据",
  "description": "DAPO 后训练（veRL 框架，Python 3.10.17，Megatron）开启 algorithm.use_kl_in_reward 后，trainer.fit() 在 apply_kl_penalty（ppo/ray_trainer.py:138 读取 data.batch[\"response_mask\"]）抛 KeyError：TensorDict 仅含 attention_mask/input_ids/position_ids/prompts/responses/token_level_scores 六键，主进程 PID:3251 退出并记录 ERR99999 UNKNOWN applicaiton exception（Device:-1/RankID:-1）。",
  "tags": [
    "task.debugging",
    "topic.reinforcement_learning"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# veRL DAPO 开启 use_kl_in_reward 后 KeyError response_mask：宿侧 batch 字段缺失的定界与排除设备侧判据


## 适用场景

DAPO 后训练（veRL 框架，Python 3.10.17，Megatron）开启 algorithm.use_kl_in_reward 后，trainer.fit() 在 apply_kl_penalty（ppo/ray_trainer.py:138 读取 data.batch["response_mask"]）抛 KeyError：TensorDict 仅含 attention_mask/input_ids/position_ids/prompts/responses/token_level_scores 六键，主进程 PID:3251 退出并记录 ERR99999 UNKNOWN applicaiton exception（Device:-1/RankID:-1）。判别：堆栈 18 行全为 Python 帧、无任何 CANN/驱动/HCCL 帧 → 宿侧应用层字段缺失而非 NPU 设备故障（修复方向与修复建议块未进入账本证据，本卡不作断言）。

## 触发与观测

> 触发：DAPO 后训练（veRL 框架 main_dapo.py / dapo_ray_trainer.py / dapo_megatron_trainer.yaml，Megatron，Python 3.10.17）同时打开 algorithm.use_kl_in_reward 配置项后，训练启动阶段 trainer.fit() 抛出未捕获 KeyError（TensorDict 中找不到 response_mask 键），训练主进程（PID:3251）异常退出，宿侧记录 "[ERROR] 2025-12-01-15:56:00 (PID:3251, Device:-1, RankID:-1) ERR99999 UNKNOWN applicaiton exception"。

**机制片段：M1**：

```
17: KeyError: 'key "response_mask" not found in TensorDict with keys [\'attention_mask\', \'input_ids\', \'position_ids\', \'prompts\', \'responses\', \'token_level_scores\']'
18: [ERROR] 2025-12-01-15:56:00 (PID:3251, Device:-1, RankID:-1) ERR99999 UNKNOWN applicaiton exception
```

## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${VERL_ROOT}`：该次实验的 veRL 工程检出根目录。


**机制片段：M2**：

```
1:   File "${VERL_ROOT}/verl/trainer/main_dapo.py", line 177, in run
2:     trainer.fit()
3:   File "${VERL_ROOT}/verl/trainer/dapo_ray_trainer.py", line 198, in fit
4:     new_batch, kl_metrics = apply_kl_penalty(
5:   File "${VERL_ROOT}/verl/trainer/ppo/ray_trainer.py", line 138, in apply_kl_penalty
6:     response_mask = data.batch["response_mask"]
```

## 机制与判别

> 根因直接机制：apply_kl_penalty 在 ppo/ray_trainer.py:138 硬编码读取 data.batch["response_mask"]，而当前 TensorDict 仅含 [attention_mask, input_ids, position_ids, prompts, responses, token_level_scores]，键不存在 → KeyError（消息逐字列出全部现有键，是字段缺失的运行时等价执行证据）；上游触发（confirmed）：开启 use_kl_in_reward=True 后 dapo_ray_trainer.py:198 的 fit() 进入 apply_kl_penalty 分支；实现层根因（hypothesis）：DAPO 数据流在调用前未向 batch 计算写入 response_mask（batch 中连 old_log_probs 也没有，说明失败点位于 actor/reward 早期阶段），需以现场 veRL commit 源码核对后升级为 confirmed。

> 判别依据（排除 NPU 设备侧故障）：堆栈 1-17 行全为 Python 帧（main_dapo.py → dapo_ray_trainer.py → ppo/ray_trainer.py → tensordict），无任何 CANN/驱动/HCCL/AI Core 帧；错误包装行 Device:-1/RankID:-1 未绑定 NPU 设备。"用户修改脚本引入" 与 "原版 DAPO 流程缺陷" 两实现层假设因缺源码/版本无法区分，保留 unresolved。

**机制片段：M3**：

```
## 根因分析

- **direct_mechanism（confirmed）**：`apply_kl_penalty` 在 `ppo/ray_trainer.py:138` 硬编码读取 `data.batch["response_mask"]`，而当前 TensorDict 仅含 `[attention_mask, input_ids, position_ids, prompts, responses, token_level_scores]`，键不存在 → `KeyError`。KeyError 消息逐字列出全部现有键，是字段缺失的运行时等价执行证据。
- **upstream_trigger（confirmed）**：开启 `algorithm.use_kl_in_reward=True` 后，`dapo_ray_trainer.py:198` 的 `fit()` 进入 `apply_kl_penalty` 分支（input.json 现象与 traceback 调用点一致）。
- **implementation_root_cause（hypothesis）**：DAPO 数据流在调用 `apply_kl_penalty` 之前未向 batch 计算并写入 `response_mask`（该字段通常由 actor 侧 log-prob/损失掩码流程产出；batch 中连 `old_log_probs` 也没有，说明失败点位于 actor/reward 早期阶段），即该版本 DAPO 流程与 KL-in-reward 路径不兼容；结合环境注明"使用自己修改的脚本"，也不排除用户改动引入。需以现场 veRL commit 源码核对后升级为 confirmed。

竞争假设处置：NPU 设备侧故障（AI Core Error/掉卡/OOM/通信）已排除——堆栈 1-17 行全为 Python 帧，无任何 CANN/驱动/HCCL 帧，错误包装行 Device:-1/RankID:-1 未绑定设备；"用户修改脚本引入"与"原版 DAPO 流程缺陷"因缺源码/版本无法区分，保留 unresolved。
```

## 验证信号

本卡验证信号并入『触发与观测』『机制与判别』：来源结论 与登记机制片段：M1/M2/M3（KeyError 错误输出、traceback 堆栈、根因分析报告）。

## 适用与失效边界

适用：veRL/DAPO 系宿侧 Python 异常导致训练进程退出的定界；触发词为 KeyError + TensorDict 键列表 + ERR99999 UNKNOWN applicaiton exception（Device:-1/RankID:-1）。失效边界：本规则依赖 KeyError 消息列出全部现有键这一运行时等价证据；若错误来自设备侧（含 CANN/HCCL 帧）则不适用；实现层根因与用户改动 vs 原版缺陷的区分需现场 veRL commit 源码，诊断内未闭合（fix_verified=false、reproducible=false）。
