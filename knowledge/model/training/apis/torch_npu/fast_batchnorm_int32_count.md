---
type: API
title: contrib FastBatchNorm：num_batches_tracked 的 int32 化与同步回退边界
description: 保存 contrib FastBatchNorm1d/2d/3d/FastSyncBatchNorm 的计数缓冲 int32 化语义、momentum=None 的宿主回读、同步门控与框架 BN 回退及转换辅助的适用范围。
tags:
- task.optimization
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/_batchnorm_with_int32_count.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/batchnorm_with_int32_count.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/contrib/test_batchnorm_with_count_int32.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/_batchnorm_with_int32_count.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/batchnorm_with_int32_count.py
  role: implementation
created_at: '2026-11-13T05:23:23Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# contrib FastBatchNorm：num_batches_tracked 的 int32 化与同步回退边界

## 固定版本与范围

静态审阅 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 `torch_npu/contrib/module/_batchnorm_with_int32_count.py`（420 行全文）、再导出壳 `batchnorm_with_int32_count.py`（7 行全文）、`torch_npu/contrib/__init__.py` 与 `torch_npu/contrib/module/__init__.py` 的暴露面，以及仓库内测试 `test/contrib/test_batchnorm_with_count_int32.py` 的期望断言。发布版本 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b` 的同名实现文件 Git blob 与主线不同（再导出壳主线与发布两版本 完全相同），未逐行比对，版本差异待发布版本 分区核实。op-plugin 文档归档的 torch_npu-contrib 目录没有该模块的官方文档页，本卡只以源码与仓库内测试为据；未确认产品与 CANN 配套范围，保持 `draft`、空平台，未导入、运行或做性能实验。实际执行的 BatchNorm 内核约束见[原生BatchNorm的OpAPI](../../guides/torch_npu_native_batch_norm_opapi_execution.md)，同为 contrib 模块的对照卡见[Focus模块](contrib_focus.md)。

## int32 计数缓冲的语义与收益声明

`_NormBase` 覆盖上游 `torch.nn.modules.batchnorm._NormBase`，类 docstring 明确声明改动目的：把 batchnorm 的 `num_batches_tracked` 从 int64 改为 int32 以提升 batchnorm 性能（`_batchnorm_with_int32_count.py:15-18`）。实现上仅计数缓冲的构造 dtype 变化：`register_buffer('num_batches_tracked', torch.tensor(0, dtype=torch.int32))`（:42），`running_mean`/`running_var` 仍按上游默认 FP32 zeros/ones（:40-41），affine 参数构造与上游一致（:33-38）；构造器先以仅 `num_features` 调用上游基类再手工补齐属性并 `reset_parameters()`（:27-47）。收益声明只覆盖计数缓冲本身，不承诺端到端时延改善；forward 全部委托 `F.batch_norm`（:95-100），落到哪个内核由当时的派发决定。

## 计数路径与 momentum=None 的宿主回读

`_BatchNorm.forward` 训练态对计数做非原地自增 `self.num_batches_tracked = self.num_batches_tracked + 1`（:69）；`FastSyncBatchNorm.forward` 用原地 `add_(1)`（:289）并以 `self.num_batches_tracked.item()` 取值（:291）。两者在 `momentum=None`（累积平均）时都把计数张量读回宿主计算平均因子（`1.0 / float(...)` 或 `.item()`，:70-73、:290-293），该路径每次前向触发一次计数读回；默认 `momentum=0.1` 时不发生该读回。int32 计数的失效边界是 2^31 次自增后的回绕：超过后累积平均因子失真，而框架 `nn.BatchNorm*` 的 int64 计数没有该边界。与框架模块互载 state_dict 时，计数缓冲按现有 buffer 的 dtype 做 copy_ 收窄（int64→int32）或扩宽，需在混用检查点时单独核对该缓冲的值域。

## FastSyncBatchNorm 的同步门控与回退

`FastSyncBatchNorm` 的同步判定为 `bn_training and self.training and torch.distributed.is_available() and torch.distributed.is_initialized()`（:318-323），且输入必须是 `is_cuda or is_npu`（:326-327）；进程组默认 WORLD，`world_size > 1` 才真正同步（:328-332）。不满足任一条件时整体回退 `F.batch_norm`（框架 BN 路线，:335-345），满足时走框架 `torch.nn.modules._functions.SyncBatchNorm.apply`（:349-359）。`num_batches_tracked` 在训练态被强制要求非 None（:287-288）。转换辅助 `convert_sync_batchnorm` 只把 `torch.nn.modules.batchnorm._BatchNorm` 实例换成框架 `torch.nn.SyncBatchNorm`（:396-412）：Fast 系列的 `_BatchNorm` 继承自本文件的 `_NormBase`，不是框架 `_BatchNorm` 的实例，不会被该辅助转换；框架模块被转换后计数缓冲按引用带过去，但后续自增走框架 int64 逻辑。

## 维度检查与错误码包装

各模块的维度门槛不同：`FastBatchNorm1d` 要求 2D/3D（:132-135）、`FastBatchNorm2d` 要求 4D（:168-171）、`FastBatchNorm3d` 要求 5D（:204-207）、`FastSyncBatchNorm` 要求至少 2D 且通道维非零（:260-270）。`running_mean`/`running_var` 非 Tensor 时抛 RuntimeError（:89-94）。这些报错统一追加 `ops_error(ErrCode.VALUE/TYPE)` 错误码后缀，检索日志时应按错误码而非仅按报错前缀定位。

## 再导出壳与暴露面

`batchnorm_with_int32_count.py` 是 7 行再导出壳，docstring 自述「This file will be discarded.」（:1-6），语义全部在 `_` 前缀实现文件中；两个导入路径（`torch_npu.contrib` 顶层与 `torch_npu.contrib.module`）解析到同一批对象（contrib/__init__.py:7-8、contrib/module/__init__.py:15-16）。仓库内测试从两个路径重复导入同名类并对比「快/慢」实现：断言输出 `assertRtolEqual` 且 `slow_time > fast_time`（test 文件 :136-194，`@SupportedDevices(['Ascend910A', 'Ascend910P'])`）。这些是仓库内测试的期望断言，不是本文运行的验证结果；设备注解只约束测试面，不构成产品支持声明。

## Evidence

- [batchnorm_with_int32_count 实现](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/_batchnorm_with_int32_count.py)（primary）：全文 1-420。
- [再导出壳](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/batchnorm_with_int32_count.py)（implementation）：全文 1-7。
- [contrib 顶层暴露](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/__init__.py)（implementation）：7-8。
- [contrib.module 暴露](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/contrib/module/__init__.py)（implementation）：15-16。
- [仓库内测试期望](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/contrib/test_batchnorm_with_count_int32.py)（implementation）：6-22、136-208。

## 发布版本 对照（f3ecfe4a）

本节结论来自发布版本 孪生文件的逐文件比对（比对口径：sha256 → 去空白 → 全空白折叠 token → 注释剥离 token）。

### 等价绑定（结论对发布版本 直接适用）

- `torch_npu/contrib/module/batchnorm_with_int32_count.py`（再导出壳）：主线与发布两版本 逐字节一致。
- `torch_npu/contrib/module/_batchnorm_with_int32_count.py`：同一 `is_cuda/is_npu` 校验 token 块在发布版整体移位（主线 :325-327 → 发布 :273-275，语义不变；420 行 → 419 行）。int32 计数语义、momentum=None 宿主回读、同步门控/回退与 convert 辅助范围结论均适用发布版本，行号锚按各 pin 文件核对。

### Evidence（发布版本 补充）

- [发布孪生 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/_batchnorm_with_int32_count.py)（release-twin-binding）：diff 级全文对照（校验块移位，语义不变）。
- [发布孪生 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/contrib/module/batchnorm_with_int32_count.py)（release-twin-binding）：主线与发布两版本 逐字节一致。


（本节静态比对，未运行/未编译；结论按文件分列，未列出的文件未比对。）
