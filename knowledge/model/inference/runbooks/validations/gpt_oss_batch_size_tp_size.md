---
{
  "type": "Runbook",
  "title": "gpt_oss 声明类约束无校验：batch_size=2 被静默接受、tp_size 不一致被静默重解释",
  "description": "gpt_oss README 声明仅支持 batch_size=1、YAML 注释要求三个 tp_size 相同，但两者均无校验：batch_size=2 全程无 ERROR/WARNING 被静默接受（default 数据集被 Pad 逻辑复制最后一条 prompt 填充、仅 1 个请求输出；LongBench 下双请求真实执行且输出可读（未做任务精度验收）），tp_size 不一致被静默重解释为 MoE EP 并行（moe_ep_size=2）正常运行。配置语义静默偏移，文档声明不可信。",
  "tags": [
    "task.debugging",
    "task.testing",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "a3"
  ]
}
---
# gpt_oss 声明类约束无校验：batch_size=2 被静默接受、tp_size 不一致被静默重解释

## 适用场景

- 模型/框架：cann-recipes-infer `models/gpt_oss`（GPT-OSS-20B bf16，39GB 3 分片），统一推理入口 `executor/scripts/infer.sh`（eager 模式，宿主机直接执行，无 Docker）。
- 平台/版本：Atlas A3（Ascend 910_9362 ×16），CANN 9.2.0，torch 2.10.0+cpu，torch_npu 2.10.0.post7，transformers 5.0.0，Python 3.11.15（来源记录 为 2026-10-16、来源记录 为 2026-10-14 两次独立运行）。
- 工作负载：README/YAML 注释声明的配置约束（batch_size=1、三个 tp_size 一致）的可信度评估；用户按文档预期配置时的行为。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

触发 1：README 第 144 行声明 `> - 目前仅支持prompt的batch_size为1。`（来源记录 T 48 读取 README 原文）；触发 2：YAML `parallel_config` 注释 `# Set the values of attn_tp_size, moe_tp_size, and lmhead_tp_size to be the same.`。

观测（逐字客观输出）：

- batch_size=2 + default 数据集（来源记录 T 254）：
```
T 254 | 1
[INFO][2026-10-16 21:04:28.749][infer.py:164] InferenceConfig(... scheduler_config=SchedulerConfig(batch_size=2, max_new_tokens=100, max_prefill_tokens=8192, batch_size_per_dp_rank=2, ...) ...)
```
（`1` 为 `grep -c "Request.*outputs"` 结果——只有 Request 0 一条输出；T 250 显示运行正常完成、decode 序列约 28ms。）
- batch_size=2 + LongBench（来源记录 T 273）：
```
[INFO][2026-10-16 21:07:38.892][infer.py:95] Request 0: outputs: analysisWe need to summarize the provided excerpt. The excerpt is from "The Coxon Fund" by Henry James. ...
[INFO][2026-10-16 21:07:38.892][infer.py:95] Request 1: outputs: analysisWe need to summarize the provided excerpt. The excerpt is from a book titled "MARY, A Fiction" by Mary Wollstonecraft? ...
[INFO][2026-10-16 21:07:38.893][infer.py:144] gpt_oss decode average inference time cost is 30.75 ms
```
- tp_size 不一致（来源记录 T 284，YAML 为 attn_tp_size=2 / moe_tp_size=1 / lmhead_tp_size=2）：
```
T 284 | ParallelConfig(world_size=2, global_rank=0, local_rank=0, attn_tp_size=2, attn_dp_size=1, offline_prefill_dp_group_size=1, cp_prefill_dp_size=1, embed_tp_size=1, embed_dp_size=2, moe_tp_size=1, moe_ep_size=2, lmhead_tp_size=2, dense_tp_size=1, shared_tp_size=1, o_proj_tp_size=1, cp_size=1)
Request 0: outputs: analysisThe user says: "An attention function can be described as mapping a query and a out
```
（实际配置保留 moe_tp_size=1，并派生 moe_ep_size=2、embed_dp_size=2，且双 rank 运行成功、输出正常。）

## 探针与操作

探针 YAML（来源记录 C 221 写入 `tc_batch2.yaml`，逐字）：

```
model_config:
  model_name: "gpt_oss"
  model_path: "${LOCAL_PATH_1}"
  exe_mode: "eager"
  enable_profiler: False

data_config:
  dataset: "default"
  input_truncated_len: 4096

parallel_config:  # Set the values of attn_tp_size, moe_tp_size, and lmhead_tp_size to be the same.
  world_size: 1
  attn_tp_size: 1
  moe_tp_size: 1
  lmhead_tp_size: 1

scheduler_config:
  batch_size: 2
  max_new_tokens: 100
```

（LongBench 版本仅把 `dataset: "default"` 改为 `dataset: "LongBench"`；tp 不匹配版本把 world_size=2、attn_tp_size=2、moe_tp_size=1、lmhead_tp_size=2。来源记录 C 209/C 252/C 273 用 `sed` 从官方 `gpt_oss_20b.yaml` 派生同型用例。）

运行命令：`bash executor/scripts/infer.sh --model gpt_oss --yaml tc_batch2.yaml 2>&1 | tail -15`（及 LongBench、tp 不匹配变体）。

## 机制与判别

机制（`executor/offline/offline_inference.py` 请求填充逻辑，来源记录 T 262 读取原文，行 148-164）：

```
148:         # Add all requests to scheduler
149:         request_ids = []
150:         prompt_map = {}
151:         for prompt in prompts:
152:             request_id = self.scheduler.add_request(prompt=prompt, sampling_params=sampling_params)
153:             request_ids.append(request_id)
154:             # simplified process, to be optimized
155:             prompt_map[request_id] = prompt
156:             if len(request_ids) >= batch_size:
157:                 break
158:
159:         original_request_count = len(request_ids)
160:         if len(request_ids) < batch_size:
161:             # Pad requests to batch_size if needed
162:             while len(request_ids) < batch_size:
163:                 request_id = self.scheduler.add_request(prompt=prompts[-1], sampling_params=sampling_params)
164:                 request_ids.append(request_id)
```

- 结论 1：gpt_oss README 声明"目前仅支持prompt的batch_size为1"，但 batch_size=2 被静默接受，全程无任何 ERROR/WARNING，运行正常完成——该约束未在框架或模型层实现校验。
  - 信号：来源记录 T 250/T 254（default）、T 273（LongBench）；来源记录 T 225/T 229/T 233（default）、T 256（LongBench）。
- 结论 2：default 数据集（仅 1 条内置 prompt）下 batch_size=2 由调度器把最后一条 prompt 复制填充到 batch_size（T 262 行 160-164 的 Pad 逻辑），结果只按 original_request_count 输出 1 个请求，填充请求的结果被丢弃——表现为"batch=2 配置、1 个请求输出"；LongBench（多样本）下 batch_size=2 真实执行 2 个请求且两个请求均返回与各自样本相关的摘要文本；未通过 golden 或任务评分验证摘要正确性，decode 平均 30.75 ms（来源记录 T 273）/30.41 ms（来源记录 T 256）。
  - 判别：该填充机制说明 batch_size 语义为"调度器批量填充目标"，default 数据集下的"仅 1 输出"不是 batch 失效而是数据集只有 1 条 prompt；两个数据集的行为差异可区分"约束生效但静默降级"与"约束完全未实现"两个解释分支——观测（无任何提示、LongBench 真实双请求正常）支持后者。
- 结论 3：attn/moe/lmhead tp_size 不一致（注释要求相同）时被静默重解释为 TP+EP 混合并行（ParallelConfig 实际 moe_ep_size=2、embed_dp_size=2），双 rank 运行成功、输出可读（未做任务精度验收），无任何提示——框架自动派生 EP 参与并行，但没有改变用户显式指定的 moe_tp_size=1。可确认的是行为与 YAML 的同值注释不一致，不能据此认定已有 TP 值被覆盖。
  - 信号：来源记录 T 277（无报错输出）、T 284（实际生效 ParallelConfig）；来源记录 T 277（tc_unequal_tp world_size=2, attn_tp=2 正常完成，decode 平均 34.62 ms）。
- 未验证推断：batch>1 的限制可能适用于其他模型规格（如 120B）或其他执行模式，本组来源观测仅在 20B eager 下验证；tp 静默重解释的性能/显存影响未量化。

## 验证信号

- 来源记录：T 250（batch2+default 正常完成）、T 254（仅 1 个请求输出 + InferenceConfig batch_size=2/batch_size_per_dp_rank=2）、T 258（Request 0 输出、1 次 prefill）、T 273（batch2+LongBench Request 0/1 双输出、decode 平均 30.75 ms）、T 277（tp 不匹配无报错）、T 284（moe_ep_size=2 静默重解释 + 输出正常）。
- 来源记录：T 225（batch2+default 正常完成）、T 229/T 233（仅 1 个请求输出 + InferenceConfig batch_size=2）、T 256（batch2+LongBench Request 0/1 双输出、decode 平均 30.41 ms）、T 277（tc_unequal_tp 正常完成、decode 平均 34.62 ms）。
- 机制原文：来源记录 T 262（offline_inference.py 148-164 行）。
- 平台与证据等级：Atlas A3 宿主机直跑；以上均为工具结果原文；单次观测（每种配置在每条轨迹各执行 1 次，两条轨迹跨两天独立复现，结论一致）。

## 适用与失效边界

- 适用：gpt_oss 20B bf16 + eager + 单卡（batch2）与 world_size=2 混合并行（tp 不一致）场景；README 声明的两条约束在该场景下不可信，不能作为配置依据。
- 失效边界/未知：
  - 120B / 其他执行模式 / npugraph 下的 batch_size>1 行为未测试；
  - batch_size 远大于数据集样本数时的填充行为（复制最后一条 prompt）意味着 token 统计与吞吐指标会被填充请求计入，用 default 数据集测性能时需注意（本组来源观测未量化该影响，为机制推断）；
  - README 约束是否在其他模型/版本仍被遵守未知；框架版本变化后需重新验证；
  - "约束应为强制报错"还是"README 应更新"取决于上游意图，轨迹内无法判定。
