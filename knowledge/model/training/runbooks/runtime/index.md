# 运行问题

- [ReTool RL 本地数据集加载失败：显式选择 parquet 与默认配置](retool_local_parquet_loading.md)：在 Qwen3 Tool Agent 的历史 veRL checkout 中，处理本地 parquet 推断错误和 AIME 多配置 schema 混入，保留数据选择的边界。

- [KL-Cov 单 response 微批中心化退化：step 级选择 mask 实现及验证边界](cov_grpo_response_step.md)：GRPO 单 response 微批中 advantage 为常数时，中心化协方差失去区分 token 的信号，不能依赖 torch.topk 的并列索引顺序。轨迹实现 actor 侧 step 级选择 mask，并验证纯 Python 分桶回填与静态编译；尚未验证修订后的实机训练效果。27 步熵下降是故障观测，不能证明唯一根因或据此决定丢弃 checkpoint、调整 ratio。
- [CP 与 CPU offload 排障：延长 HCCL 超时仍失败](cp_cpu_offload_hccl_timeout_extension_negative_result.md)：训练日志在 300s 与 600s 超时设置下都出现同序号单元素 ALLREDUCE 失败，不能把延长超时或首步成功当作多步训练修复。

- [KL-Cov 策略损失移植 vime（torchtitan/megatron 双后端）与 --keep-old-actor 生效前提](cov_vime_torchtitan_megatron_keep.md)：把论文 arXiv:2505.22617 的 KL-Cov 惩罚（verl PR #1830 loss_mode=kl_cov）移植进 vime：ppo_utils 新增 compute_kl_cov_loss（无 clip 的 -A·ratio 主项 + top 协方差 token 上 β·|Δlogp| 惩罚），megatron/torchtitan 两后端接入，--use-kl-cov/--kl-cov-ratio/--kl-cov-coef 三参数与互斥校验，run/resume/replay 三脚本默认启用。关键前提是 --keep-old-actor：async 单步更新下 old log probs 用当前权重预计算会使 Δ≡0、惩罚恒为 0。实机 27 步验证 loss 管道与 TB 指标（kl_cov、pg_clipfrac）落盘。注意：协方差选择位置缺陷（修复与验证边界见正文）在该 27 步运行中尚未修复。
