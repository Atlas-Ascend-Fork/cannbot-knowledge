---
type: Guide
title: 原生概率分布：采样、CPU回退和950DT方法边界
description: 区分分布类与采样/统计子项，整理CPU回退、随机行为、协方差维度和变换约束。
tags:
- task.optimization
- topic.precision
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-distributions.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-distributions.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-distributions.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-distributions.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-distributions.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-distributions.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-distributions.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-distributions.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-distributions.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-distributions.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-distributions.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-distributions.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-distributions.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-distributions.md
  role: constraint
created_at: '2026-11-09T13:33:55Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 原生概率分布：采样、CPU回退和950DT方法边界

## 固定版本与证据

依据TorchNPU主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的PyTorch2.7.1、2.9至2.14中英文原生支持页。按具体类/方法、文档版本与A2/A3训练系列、950DT分别消费，未收录不等于已证实不支持；不扩展950PR，不回推26.0/PyTorch2.8发布组合，不补造清单没有给出的参数或默认值。本卡仅静态审阅，未运行上游、采样、量化、训练或设备实验。

## 分布类、方法和可重参数化标志分层

清单覆盖Bernoulli/Beta/Binomial/Categorical/Cauchy/Chi2/ContinuousBernoulli/Dirichlet/Exponential/FisherSnedecor/Gamma/Geometric/Gumbel/HalfCauchy/HalfNormal/Independent/InverseGamma/Kumaraswamy/LKJCholesky/Laplace/LogNormal/LowRankMultivariateNormal/MixtureSameFamily/Multinomial/MultivariateNormal/NegativeBinomial/Normal/OneHotCategorical/Pareto/Poisson/RelaxedBernoulli/LogitRelaxedBernoulli/RelaxedOneHotCategorical/StudentT/TransformedDistribution/Uniform/VonMises/Weibull/Wishart。除下面单列的Wishart类外，中文这些类列三类产品；英文没有InverseGamma，ExponentialFamily/Normal/Uniform没有独立类级产品表，不能用英文子方法反填类表。

Distribution基类两侧均没有独立类级表；arg_constraints、batch_shape/event_shape、mean/mode/stddev/support/variance及set_default_validate_args列三类产品，中文另对cdf/entropy/enumerate_support/expand/icdf/log_prob/perplexity/rsample列三类产品。sample_n仅中文2.7.1收录。has_rsample/has_enumerate_support的支持表表示这些属性纳入清单，不表示返回值为True，更不保证任意采样方法都有可重参数化梯度。

## 950DT不能由父类表补齐的子项

下表各行中文仅列A2/A3，英文明确950DT不支持；未在该行出现的其他方法仍按它自己的条目消费，不能反推所有继承方法或组合均可用。

| 分布/对象 | 较窄的条目 |
| --- | --- |
| Bernoulli | mode、support |
| Beta | expand |
| Categorical | sample |
| Cauchy | support、variance |
| FisherSnedecor | mean、mode |
| Gamma | arg_constraints、expand、rsample |
| Geometric | arg_constraints、log_prob |
| Gumbel、HalfCauchy | expand |
| HalfNormal | variance |
| Independent | expand、has_enumerate_support、has_rsample、sample |
| LKJCholesky | arg_constraints、expand、log_prob、sample、support |
| Laplace | expand、stddev、variance |
| LogNormal | expand、has_rsample、scale |
| LowRankMultivariateNormal | entropy、expand、has_rsample、log_prob、scale_tril、variance |
| MixtureSameFamily | expand、has_rsample、mean、sample |
| Multinomial | log_prob、logits、sample |
| MultivariateNormal | entropy、support |
| NegativeBinomial | support |
| Normal | sample |
| OneHotCategorical、Pareto、RelaxedBernoulli | expand |
| RelaxedOneHotCategorical | temperature |
| StudentT | has_rsample、mean、variance |
| TransformedDistribution | arg_constraints、expand、sample |
| VonMises、Weibull | expand |
| Wishart | 类本身，以及log_prob、mode、precision_matrix、rsample、scale_tril、support |

Wishart的arg_constraints/covariance_matrix/entropy/expand/has_rsample/mean/variance却列三类产品，不能由这些子项反推950完整Wishart流程。Normal类的950随机行为说明与sample的较窄支持表也同时保留，不以一段行为描述覆盖具体方法排除。

## CPU回退与随机结果

Binomial、Chi2、Dirichlet、FisherSnedecor、Gamma、HalfCauchy、HalfNormal、LKJCholesky、NegativeBinomial、Poisson、RelaxedOneHotCategorical、StudentT的类条目提示可能回退CPU；具体方法还包括Binomial.log_prob，Cauchy.log_prob/rsample，Dirichlet.log_prob/rsample，Gamma.cdf/log_prob，Kumaraswamy.entropy，Laplace.icdf，LogNormal.entropy，MultivariateNormal.log_prob/rsample和NegativeBinomial.sample。它们不是“必定回退”或“所有未标项均为纯NPU”的证明。

Exponential、Normal、Uniform明确950DT随机数生成行为与GPU实现一致、结果与A2/A3不同。不要据此承诺任意种子、软件版本和算法跨设备逐位一致，采样数值与统计/梯度验收分开，参见[随机状态命名空间](../../inference/guides/optimization/torch_npu/torch_npu_native_rng_state_scope.md)。MultivariateNormal.covariance_matrix另限制dim不超过8192，不把该局部字段扩展为所有分布/方法的统一维度上限。

## 变换、KL和约束注册

Abs/Affine/Cat/Exp/LowerCholesky/PositiveDefinite/Power/Reshape/Sigmoid/Softplus/Tanh/Softmax/Stack/StickBreakingTransform列三类产品，中文还列ComposeTransform、IndependentTransform及torch.distributions.CumulativeDistributionTransform。Transform的inv/sign/log_abs_det_jacobian/forward_shape/inverse_shape两侧列三类产品，中文另有类级表；这不是任意变换组合、逆变换与梯度均等价的保证。

AbsTransform明确950DT不支持COMPLEX64/128，CorrCholeskyTransform中文仅A2/A3、英文950不支持。ConstraintRegistry类列三类产品，register却中文只列A2/A3、英文950不支持。constraints的cat/dependent_property/greater_than/less_than/multinomial/stack列三类产品；Constraint及check、is_dependent只在中文列三类产品。

kl_divergence两侧列三类产品，register_kl只在中文列三类产品，不能由入口存在推定任意分布对已经注册解析KL。utils.broadcast_all仅中文2.13/2.14收录，列三类产品。未给出的完整dtype、分布参数合法域、broadcast和事件维度合同保持未知。

## 优化验收

固定实际分布、方法、参数范围、样本shape、随机状态和求导路径，比较统计量、log_prob及所需梯度，并检查实际CPU回退/传输，再测稳态与端到端开销。不能以类构造或has_rsample可读取代替采样和训练正确，本文没有生成随机样本。

- [已纳管CPU回退和兼容实现边界](../../inference/guides/optimization/torch_npu/torch_npu_cpu_fallback_and_compatible_impl.md)
- [自动微分的命名空间与高阶约束](torch_npu_native_autograd_transforms.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-distributions.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-distributions.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-distributions.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-distributions.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-distributions.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-distributions.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-distributions.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-distributions.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-distributions.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-distributions.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-distributions.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-distributions.md)（primary）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-distributions.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-distributions.md)（constraint）
