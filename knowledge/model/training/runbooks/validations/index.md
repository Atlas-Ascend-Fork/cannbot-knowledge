# 模型训练验证方法

- [rollout dump 的采样 token surprisal 分桶：均值下降、百分比舍入与判读边界](rollout_dump_vllm_surprisal.md)：用 vLLM rollout_log_probs 统计采样 token 的 surprisal 均值、分位数及各数值区间贡献。单次观测中均值从 0.2094 降至 0.0160 nats/token；后期两个高 surprisal 桶的 token 占比虽均显示 0%，仍分别贡献 29% 和 24% 的总 surprisal，不能判为归零。分桶不识别语法或决策位置，也不能单独裁决 KL-Cov 效果、探索预算或是否重启。
- [sigtrace CULPRIT 误报判读：首条 nan_count 行、同配置噪声底与 logger 门控](sigtrace_culprit_nan_count_logger.md)：sigtrace check 模式报的 CULPRIT 可能是 absmax-only 噪声抢位：first_introducer 按时间先到先得（本例一个 nan=0 的 absmax 发散 kernel 抢先 2 秒占位，真 NaN 源落入被 logger 吞掉的 PROPAGATED warning 分支）；同配置两次 run 仅 51.9% 的 key 在容差内一致，输入侧 77%/88% 的 run 间抖动会把真源降级为 PROPAGATED；record() 用 setdefault 使 json 值与日志值错位 4 个数量级。可靠定位信号是日志里第一条 nan_count 发散行：它之前 nan/inf 发散为 0 次。
