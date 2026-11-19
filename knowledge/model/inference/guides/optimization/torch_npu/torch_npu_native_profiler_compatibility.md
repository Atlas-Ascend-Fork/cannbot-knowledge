---
type: Guide
title: 原生torch.profiler的NPU兼容入口：指南与支持清单冲突
description: 保留≥2.12原生NPU示例与events/key_averages明确排除的同提交差异，避免用示例覆盖支持矩阵。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/ascend_pytorch_profiler_user_guide.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/ascend_pytorch_profiler_user_guide.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-profiler.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-profiler.md
  role: constraint
created_at: '2026-11-09T16:20:25Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 原生torch.profiler的NPU兼容入口：指南与支持清单冲突

## 固定来源与草稿原因

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf。中英文长指南都写原生torch.profiler可把CUDA字段改NPU，要求torch与torch_npu≥2.12.0；同提交2.14原生清单又要求改用NPU形式名称，并明确排除部分示例方法。尚无可合并的完整接口/产品合同，本卡draft、platforms为空，不回推26.0/PyTorch2.8。

## 两种说明不能直接合并

| 证据 | 原文给出的边界 |
| --- | --- |
| 两语言用户指南 | 直接使用torch.profiler.profile/ProfilerActivity.NPU、schedule、handler，例子结束后调用events与key_averages |
| 2.14原生清单总述 | 使用已支持Profiler API须替换为NPU形式名称，例如torch_npu.profiler.profile |
| 2.14英文events/key_averages | A2/A3/950DT均明确Not Supported，中文没有这两项；缺项与明确排除不同 |
| 2.14采集入口 | 中文仅列A2/A3、英文明确950DT不支持，不能用新指南无产品表把全流程扩到950 |
| 原生2.14参数说明 | use_cuda移除、以activities选择，with_modules弃用，动态图模块跟踪用with_stack；专用TorchNPU指南仍单列with_modules |

新指南中的≥2.12是所述兼容入口门槛，不表示其中所有报告方法、所有产品和全部选项组合都已确认。七版本旧清单的细分见[基础采集指南](torch_npu_profiler_capture_schedule.md)，不能把torch.autograd.profiler的同名方法支持移到torch.profiler。

## 示例实际做了什么

TinyModel例子使用8步，schedule为wait1/warmup1/active3/repeat1，每步先NPU同步再profiler.step，输出事件与按输入shape汇总的报告。这只是采集和报告流程演示；每步同步改变异步流水，不能用其step耗时报告正常模型吞吐。record_shapes/profile_memory/stack/modules全部打开也会改变观测开销。

示例只有import torch，依赖真实环境完成NPU后端自动加载/注册；不构成无需torch_npu安装或任意自动加载配置可运行的保证。用户指南里保留的CUDA命名、transfer_to_npu和旧训练脚本注释也不能代替明确的后端/设备检查。

## 当前可消费结论

保留命名空间、版本、有效采集活动与具体方法的区别。专用torch_npu.profiler采集路线、旧原生清单的NPU适配名称及本例现代原生兼容路线分别核对；没有实现/运行证据前不发布一段已验证的统一替换脚本，也不将任何一侧文档静默视为已作废。

以上为静态来源核对，未导入PyTorch、采集events、执行key_averages或验证设备。实际部署应比较同负载与所需报告，确认产物和数值后再评价开销；来源称可执行不等于已在本卡验证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/ascend_pytorch_profiler_user_guide.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/ascend_pytorch_profiler_user_guide.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/native_api/pytorch_2-14-0/torch-profiler.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/native_api/pytorch_2-14-0/torch-profiler.md)（constraint）
