---
type: Guide
title: 原生距离函数：950DT与文档版本的支持差异
description: 区分PairwiseDistance类和functional、pdist的版本标记以及cosine_similarity的输入类型；含 cdist/pdist 家族 Eager 实现层：p 的 inf 哨兵分裂、_pdist_backward 的 CPU triu 索引桥与 cdist 反向复用、_cdist_backward 主线三层门与发布恒门的 pin 差。
tags:
- task.implementation
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn-functional.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn-functional.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/PdistKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/PdistBackwardNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/CdistBackwardNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CdistKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CdistBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/PdistKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/PdistKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/CdistBackwardNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/CdistKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/CdistBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/PdistKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/struct_codegen.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/model.py
  role: implementation

created_at: '2026-11-09T12:17:09Z'
updated_at: '2026-11-14T01:56:26Z'
platforms:
- a2
- a3
- '950'
---

# 原生距离函数：950DT与文档版本的支持差异

## 固定版本与产品

依据TorchNPU固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的PyTorch2.7.1、2.9至2.14支持页及完整子方法，产品按A2/A3训练系列与950DT逐项记录，不扩展950PR或发布组合。文档版本差异不直接证明发行历史或实际包回归。上游“已验证产品”属于清单口径，本卡仅静态审阅，未执行上游、NPU或性能实验。

## 距离入口逐项选择

| 入口 | A2/A3 | 950DT |
| --- | --- | --- |
| nn.PairwiseDistance | 七版本列支持 | 七版本列支持 |
| F.pairwise_distance | 七版本列支持 | 七版本明确不支持 |
| F.pdist | 七版本列支持 | 2.7.1及2.9..2.12不支持，2.13/2.14列支持 |
| nn.CosineSimilarity、F.cosine_similarity | 列支持 | 列支持 |

上述类与functional或文档版本差异保留，不把PairwiseDistance类当作已确认的950 functional替换配方，也不据页面变化宣称安装包实际回归/修复。F.cosine_similarity的x1/x2仅列FP16/FP32；类条目和pdist未另给完整dtype细表，不以省略补齐BF16、复数、梯度、广播或距离阶数。

## 验收边界

固定距离定义、真实dtype、形状、归约及前后向需求，检查实际Kernel与结果，再比较误差、内存和吞吐。支持标记不表示与所有损失或对比学习任务可无条件交换；本卡没有运行距离计算或NPU实验。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn.md)（primary）
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-7-1/torch-nn-functional.md)（constraint）
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-9-0/torch-nn-functional.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-10-0/torch-nn-functional.md)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-11-0/torch-nn-functional.md)（constraint）
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-12-0/torch-nn-functional.md)（constraint）
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-13-0/torch-nn-functional.md)（constraint）
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-nn-functional.md)（primary）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-10-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-11-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-12-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-13-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-7-1/torch-nn-functional.md)（constraint）

- [英文复核与实现来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-9-0/torch-nn-functional.md)（constraint）

## cdist/pdist 家族的 Eager 实现层：p 哨兵分裂、CPU 索引桥与 pin 差

上文逐项选择只锚定公开支持表；本节补齐 `pdist`/`_pdist_forward`/`_pdist_backward`/`_cdist_forward`/`_cdist_backward` 在两版OpPlugin固定树（主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`）的 Eager 实现层；`cdist` 本身已在支持表核对，其 gen 登记与本节 `_cdist_forward` 同构配对、不重复展开。yaml 登记主线与发布两版本对照：`_cdist_backward`/`_cdist_forward`/`_pdist_forward`/`pdist` 主线与发布两版本均 acl_op+op_api all_version 且字段逐字相同（主线126–128、130–142、704–706、3955–3957；发布126–128、130–142、673–675、3847–3849）；`_cdist_forward` 与 `cdist` 另带 gen_opapi（new_params `p_float: static_cast<float>(p)`、`mode: std::abs(p-2.0)<1e-6 ? 2 : compute_mode.value_or(0)`，out 尺寸=`op_infer::cdist_npu_output_size(x1, x2)`、dtype=`x1.scalar_type()`，exec aclnnCdist）。**`_pdist_backward` 只在主线登记 `op_api: [v2.14, newest]`（主线701–702，无 acl_op 条目）；发布版本 yaml 无该条目、opapi 目录亦无手写文件（负向定案）**——发布固定树内没有 _pdist_backward 的 NPU 实现（上游 ATen/组合回退未核对，不外推为不可用）。opapi 目录主线与发布两版本均无 Cdist 前向手写文件（find 零命中），`cdist`/`_cdist_forward` 的 op_api 路由全部来自生成层。本节只读源码，未运行任何设备或CPU算子。

| 入口 | 实际门槛→动作 | 失败/边界 |
| --- | --- | --- |
| pdist/_pdist_forward（opapi 手写 PdistKernelNpuOpApi，主线24–48、发布24–41） | `DO_COMPATIBILITY(aclnnPdist, acl_op::_pdist_forward(self, p))`后 TORCH_CHECK `p >= 0`（原文"pdist only supports non-negative p values"，VALUE）；**主线独有退化形状短路**：`self.size(0) <= 1 或 self.size(1) == 0` 时直接 `at::zeros(pdist_npu_output_size(self), self.options())`（注释原文"aclnnPdist crashes on such inputs...mirroring the acl_op fallback"）；`p` 为 inf 时取 float `+inf`，否则 TORCH_CHECK `p <= float max`（原文"p dose not support float64 currently."，dose 拼写按原文记录，TYPE）；`apply_tensor_without_format(self, output_size)` 后单次 `EXEC_NPU_CMD(aclnnPdist, self, p_float, result)`。`pdist` 入口纯委托 `at::_pdist_forward`（本文件 50–52/43–45），**本层无 dim/浮点检查** | 发布版本无退化短路（n<=1 或空特征维仍向 SDK 下发命令，接受性未核对）；单host命令≠单device kernel；aclnnPdist 对 p 的设备侧解释未核对 |
| _pdist_backward（主线 opapi 手写 PdistBackwardNpuOpApi 22–68；发布无文件、无 yaml 条目） | **无专用 aclnn 反向命令、无 DO_COMPATIBILITY**：TORCH_CHECK `p >= 0`（VALUE）；梯度归零短路——`self.dim() != 2 或 size(0) <= 1 或 p == 0 或 size(1) == 0` 时 `at::zeros_like(self)`（注释引 CPU `apply_backward_pdist` 的 p==0 空分支同型）；**`at::triu_indices(n, n, 1)` 在 CPU 构造后 `.to(self.device())`**（注释原文"triu_indices has no NPU kernel"——索引元数据 Host 计算加一次 H2D）；`self.contiguous()`（注释：为 CANN<9.2.0 的 acl_op 回退准备连续输入）；grad/pdist 各两次 `index_put_({row, col})`/`({col, row})` 散射进两个对称 (n, n) 零对角矩阵；结尾委托 `op_api::_cdist_backward(grad_matrix, self_contiguous, self_contiguous, p, dist_matrix)`（注释自述：G 对称零对角时 cdist 反向的行和即 pdist 梯度） | 组合链命令数（CPU triu、H2D、index_put_×4、cdist_backward 内部再分派）按实际时间线核对；index_put_ 的 NPU 实现属索引族不在此展开；主线 `[v2.14, newest]` 版本门下 v2.13- 构建的注册面不在本卡核对范围 |
| _cdist_backward（opapi 手写，主线22–101、发布22–56；**pin 差定案**） | 主线：入口先 `grad.contiguous()`（注释：double-backward 图会喂入转置/非连续梯度、acl_op 回退要求连续）；`DO_COMPATIBILITY(aclnnCdistBackward, acl_op::…(grad_contiguous, …))`；p 为 inf→哨兵 `-1`，否则 TORCH_CHECK `p <= float max`（PARAM）；**三层条件门**：`p_in_range = (0 <= p <= 2) 或 p == -1` 且 `GetSocVersion() < Ascend950` 且 `!is_gte_cann_version_920()` 时整段转 `acl_op::_cdist_backward`（注释原文"Before CANN 9.2.0, aclnn has precision issues when handling integers and infinity"）；随后 TORCH_CHECK `c1 == c2`（PARAM）；batch `at::infer_size` 广播+expand+contiguous；空 batch/r/c → `at::zeros_like(x1)`；out 尺寸/dtype 跟 x1_broadcast；EXEC aclnnCdistBackward(grad_contiguous, x1_broadcast, x2_broadcast, cdist_contiguous, p_cast, out)。发布：DO_COMPATIBILITY 用原始 grad；同 p_cast；**`p_in_range` 恒转 acl_op（无 SoC/CANN 门）**；无列检查、无广播、无空快捷；out 尺寸=x1.sizes() 且 **dtype=grad.scalar_type()**；EXEC 直发原始张量 | 主线与发布两版本三层不对称按原文记录：主线仅「p∈[0,2]∪{inf} 且 SoC<950 且 CANN<9.2」才回落，950 或 CANN≥9.2 仍走 aclnn；发布对同一 p 区间恒回落。输出 dtype 参照 pin 分裂（主线跟 x1、发布跟 grad）——混合精度用例按 pin 核对，不互推 |
| _cdist_forward（生成层，模板推导） | 生成的 op_api wrapper：`DO_COMPATIBILITY(aclnnCdist, acl_op::_cdist_forward(...))`（acl_op 登记在场）+ new_params `p_float`/`mode` + out 按 `cdist_npu_output_size(x1, x2)`/`x1.scalar_type()` 申请 + 单次 `EXEC_NPU_CMD(aclnnCdist, x1, x2, p_float, mode, out)` | 生成体不随仓提交，按 struct_codegen 模板静态推导（与[激活精度卡]_add_relu 同口径），未运行 gencode；生成层 `p_float=static_cast<float>(p)` **不做 inf→-1 映射**（aclops 路做，见下）——inf 经 float 收窄后进命令的解释未核对 |
| _cdist_forward/cdist（aclops，主线23–117、发布23–107） | `_cdist_forward`：五道 TORCH_CHECK（x1/x2 `dim() >= 2`、`x1.size(-1) == x2.size(-1)` 列相等、x1/x2 `isFloatingType`、`p >= 0`）；p 为 inf→**哨兵 -1**，否则 p<=float max（TYPE，原文"npu does not support float64"）；`mode = compute_mode.value_or(0)` 且 TORCH_CHECK `mode ∈ [0,2]`（VALUE，原文"possible modes: 0, 1, 2, but was: ..."）；batch infer_size 广播后两级 expand+contiguous（batch 维再 r1/r2 维）；`apply_tensor(tensor1_broadcast, result_size)` 后 ACE 命令 `Cdist`（attr `p`），结尾 `result.view(output_size)`。`cdist` 入口：命名张量分支（compute_cdist_outnames+去名拷贝+传播）——主线包在 `#if !VERSION_BETWEEN(V2R13, VERSION_NEWEST)` 内（≥2.13 构建丢弃），发布无版本门恒在（≤2.12 构建主线与发布两版本等价） | inf 哨兵 -1 与 pdist 前向的 +inf 分裂按原文记录；主线 `expand_batch_product` 为 int64_t、发布 int（乘积溢出面不同，字面按原文记录不判意图）；两级 expand+contiguous 是回退路的额外可见准备成本 |
| _cdist_backward（aclops，主线与发布两版本去空白字符流相同，22–73） | 四道连续性 TORCH_CHECK（x1/x2/cdist/grad 必须 contiguous，原文"_cdist_backward requires X1 to be contiguous"等，TYPE）；p 为 inf→-1；**无列相等检查、无 p 范围检查**（检查面与 opapi 层不对称）；四输入各自 view+expand+contiguous 到统一广播形；`apply_tensor(tensor1_broadcast, x1.sizes())` 后 ACE 命令 `CdistGrad`（attr `p`） | 上文 _pdist_backward 的委托链最终落在此文件或 aclnn 命令（按主线门分派）；广播展开的连续化成本按实际输入核对 |
| pdist/_pdist_forward（aclops，主线与发布两版本去空白字符流相同，主线24–63） | `_pdist_forward`：`size(0) <= 1` → `apply_tensor(self, {0})` 空输出；否则 p<=float max（TYPE，原文"npu dose not support float64"，dose 按原文记录）；`size(1) == 0` → **`acl_op::fill_(result, 0)`**（fill 命令而非 Pdist 命令——与 opapi 主线短路同效果不同实现）；否则 ACE 命令 `Pdist`（attr `p`，inf→+inf）。`pdist` 入口：TORCH_CHECK `dim() == 2`（PARAM，原文"pdist only supports 2D tensors, got: ..."）、`isFloatingType`（TYPE）、`p >= 0`（VALUE）后委托 `_pdist_forward` | dim==2/浮点检查**只在 aclops 入口**，opapi 纯委托路没有——走 op_api 路时维度合法性交 SDK；空输出的 dtype/options 跟 self |
| 尺寸 helper（KernelNpuOutputSize.cpp，主线371–387、1040–1046；发布337–353、887–893） | `cdist_npu_output_size`：TORCH_CHECK x1/x2 `dim() >= 2`（原文"Dim of x1 should be grater than 2..."，grater 拼写按原文记录）+ batch infer_size + `{batch…, r1, r2}`；`pdist_npu_output_size`：无任何检查，`{n*(n-1)/2}`（严格上三角打包长度） | pdist 输出长度公式即上三角元素数；n<2 时结果为 0 长度（与短路一致），不在 helper 层拒绝 |

跨行三条：其一，**p 的 inf 哨兵三分裂**——cdist 前向/反向 aclops 与 `_cdist_backward` opapi 把 inf 映射为 -1、pdist 前向两路（opapi 与 aclops）映射为 +inf、生成层 `p_float` 不做映射；同一 p=inf 在不同入口进命令的字面值不同，不互推。其二，**_pdist_backward 是组合链而非命令**——CPU triu_indices、一次 H2D、四次 index_put_ 散射、再复用 `_cdist_backward`（其内按 pin 门再分派 acl_op/aclnn）；迁移对比学习/对比损失的反向耗时应按整链计。其三，**pin 差集中在 `_cdist_backward`**——主线三层条件门（p 区间×SoC×CANN 版本）与发布恒门、输出 dtype 参照（x1 vs grad）、以及主线新增的 grad 连续化/广播/空快捷；两个固定快照不认证同一安装组合，按实际部署核对。

### cdist/pdist 实现层补充证据

- [PdistKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/PdistKernelNpuOpApi.cpp)（primary）：24–48（_pdist_forward 完整函数体，含主线退化短路）、50–52（pdist 委托）。
- [PdistBackwardNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/PdistBackwardNpuOpApi.cpp)（primary）：22–68；完整函数体（含 22–27 设计注释）；**发布版本无此文件**（source_meta present=false，os.path 负向核实）。
- [CdistBackwardNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/CdistBackwardNpuOpApi.cpp)（primary）：22–101；完整函数体（含 grad.contiguous、三层门、广播与空快捷）。
- [CdistBackwardNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/CdistBackwardNpuOpApi.cpp)（implementation）：22–56；完整函数体——恒门、无广播、dtype 跟 grad（pin 差逐行 diff -u 核对）。
- [CdistKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CdistKernelNpu.cpp)（primary）：23–117；_cdist_forward 与 cdist 完整函数体。
- [CdistKernelNpu.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/CdistKernelNpu.cpp)（implementation）：23–107；同构，差异为命名张量分支无版本门与 expand_batch_product 的 int/int64_t 拼写（整文件 diff -u 核对）。
- [CdistBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/CdistBackwardKernelNpu.cpp)（primary）：22–73；完整函数体；与发布去空白字符流相同。
- [PdistKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/PdistKernelNpu.cpp)（primary）：24–63；nocheck/_pdist_forward/pdist 完整函数体；与发布去空白字符流相同。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：371–387、1040–1046；cdist/pdist 两个尺寸 helper 完整函数体。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：337–353、887–893；发布侧同 helper 完整函数体。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：126–142、1579–1590、701–706、3955–3957；_cdist_backward/_cdist_forward（+cdist 配对）/_pdist_backward/_pdist_forward/pdist 条目完整字段。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：126–142、1520–1531、673–675、3847–3849；发布侧同条目（_pdist_backward 缺席为负向事实：整 yaml grep 仅命中上述行）。
- [struct_codegen.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/struct_codegen.py)（implementation）：43–58、108–157、295–476；ACLNN_FUNCTIONS_DEFINITION 模板、版本过滤与 compute_op_api_definition（生成层行为推导依据；该文件亦为[激活精度卡]既有来源）。
- [struct/model.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/torchnpugen/struct/model.py)（implementation）：40–105、230–265；ResInfo 解析（out 变体缺省 dtype=out）与 cmd_args 展开（exec 单元素时按 schema 参数序补全）。
- 负向证据：主线与发布两版本 `op_plugin/ops/opapi/` 无 Cdist 前向手写文件（find 零命中）；发布版本无 PdistBackwardNpuOpApi.cpp 且 yaml 无 _pdist_backward 条目；canonical 与全部 batch*/staged rg `CdistBackwardNpuOpApi|PdistBackwardNpuOpApi|PdistKernelNpuOpApi|aclnnPdist|aclnnCdist|cdist_npu_output_size|pdist_npu_output_size` 零命中——本节为该家族首个实现级小节（上文逐项选择仅 docs 面）。
