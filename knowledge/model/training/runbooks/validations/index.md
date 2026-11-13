# 模型训练验证方法

- [rollout dump 的采样 token surprisal 分桶：均值下降、百分比舍入与判读边界](rollout_dump_vllm_surprisal.md)：用 vLLM rollout_log_probs 统计采样 token 的 surprisal 均值、分位数及各数值区间贡献。单次观测中均值从 0.2094 降至 0.0160 nats/token；后期两个高 surprisal 桶的 token 占比虽均显示 0%，仍分别贡献 29% 和 24% 的总 surprisal，不能判为归零。分桶不识别语法或决策位置，也不能单独裁决 KL-Cov 效果、探索预算或是否重启。
- [sigtrace CULPRIT 与 NaN 定位边界：日志顺序、运行间差异与 logger 门控](sigtrace_culprit_nan_count_logger.md)：sigtrace 的 first_introducer 会先记录任意字段的首次发散，并不专门标记 NaN。本例 CULPRIT 为 absmax 发散，另一个 kernel 随后才记录 NaN；默认 logger 又隐藏 PROPAGATED warning。应分别核对采集覆盖、运行间差异和每次调用，首个已记录 NaN 输出只是定位候选，不能独立证明真实引入点。

- [torch_npu ERR99999 多 rank 失败时的 execute_log 与 plog 计数分流](err99999_multi_rank_first_error_boundary.md)：来源 execute_log 仅一个 worker 有一条 ERROR，所查 8 个 worker 的 plog 均为零 ERROR。计数可定位后续应读的日志，不能单凭零计数认定环境故障或排除 CANN。
- [无 NPU 环境下 monkeypatch 假 torch_npu 验证 micro_pipeline_tp 融合算子入参的单元测试模式](fake_torch_npu_monkeypatch_micro_pipeline_tp_test.md)：torchtitan-npu micro_pipeline_tp 融合算子 PR 的无 NPU 回归验证模式，让 CPU 开发机也能锁定 NPU 融合算子的入参转发与 fail-fast 行为契约。
- [Kimi K3 四融合算子 NPU smoke 精度测试落地（从配置提取 shape、逐输出逐梯度对比 + CPU FP64 oracle）与 quick shape 91 用例通过](kimi_k3_fused_ops_shape_inference_rel_l2_gates.md)：在 torchtitan-npu ops_test 分支落地 attn_res/conv1d/situ/kda 四融合算子的 NPU smoke 精度测试：从正式 DeepEP 配置动态提取 T=8192、R=131072、H=96 等参数推算单卡输入 shape，统一比较 forward、全部输入梯度和参数梯度，小形状用 CPU FP64 oracle；静态检查通过，服务器 quick shape 91 用例全部通过（生产 shape 仍需另行运行）。
- [train/rollout logprob 差异回放测量链路：纯 .pt 回放机制确认与 --train-logprobs-only 干跑接线验证](train_rollout_logprob_diff_replay_measurement.md)：为定位 qwen3.5-9B 训练与推理 logprob 差异最大的环节，确认既有 replay-qwen35-9B-tbench-torchtitan.sh 为纯 .pt 回放（--load-debug-rollout-data 强制 debug_train_only，不启动 vLLM 引擎/沙箱/AgentENV，样本内 rollout_log_probs 为原始 run 落盘值），且训练侧已有 train_rollout_logprob_abs_diff 指标（CI 阈值 ≤0.1）。
