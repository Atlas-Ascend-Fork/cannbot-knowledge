---
type: Guide
title: Inductor 融合精度检查：版本范围、阈值与诊断产物
description: 说明 beta 检查工具只列 PyTorch 2.7.1/2.9.0，区分工具改变编译策略与模型正常运行性能。
tags:
- task.debugging
- topic.precision
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/INDUCTOR_ASCEND_CHECK_ACCURACY.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/INDUCTOR_ASCEND_CHECK_ACCURACY.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/other/INDUCTOR_ASCEND_CHECK_ACCURACY.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/other/INDUCTOR_ASCEND_DUMP_FX_GRAPH.md
  role: primary
created_at: '2026-11-09T06:01:51Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# Inductor 融合精度检查：版本范围、阈值与诊断产物

## 固定版本与证据

依据 PyTorch/TorchNPU 固定主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的环境变量文档，按所列产品和选项限制使用，不推导发布组合具备全部功能。只读来源审阅，未运行上游代码或设备实验。

## 功能范围

INDUCTOR_ASCEND_CHECK_ACCURACY 默认未配置，1 开启。固定主线文档明确仅 PyTorch 2.7.1 和 2.9.0、Inductor 的 Triton/DVM 模式可用；不是对该主线 PyTorch2.14 或 GE/npugraph_ex 的支持承诺。产品表列 A2/A3/950，本卡以这些范围记载该文档契约，不混同实际安装验证。

工具捕获融合节点的 FX 子图，在相同输入下比较 Eager 和融合输出，并生成诊断/独立用例。Triton 模式还会将 split_reductions=False，改变编译策略，因此调试运行的性能不能与默认编译直接混比。

## 阈值与失败记录

默认 rtol：FP32 和其他类型 1.3e-6、FP16 1e-3、BF16 1.6e-2；atol 均 1e-5。INDUCTOR_ASCEND_CHECK_ACCURACY_RTOL_ATOL 可给统一 rtol/atol；分 dtype 调整在相应模式配置实现，不能把一个阈值自动当作所有业务的验收标准。

失败记录含 kernel、输出索引、不匹配数量/比例、最大绝对和相对误差、阈值与 dump_path；Triton 路线将数据及 FX 文件保存到该路径。无额外输出是来源的成功表现，但仍需确认检查实际开启、路径及版本，不能仅以“无告警”证明全部模型精度。


## 核验

保存解释器、包版本、设备、完整配置及首次生效时机，在新进程中做单项对照。检查数值与实际路径，再分别比较首次启动、稳态时间和资源开销；调试配置关闭后复测。

## 容差解析与字符串开关不能按统一布尔理解

同提交Triton config.py的容差解析按逗号拆项、去空白，rtol/atol键大小写不敏感，格式或float转换失败只告警并跳过，重复合法键以后者为准；只给一个键时另一个沿用默认。解析层没有非负性检查，不据“可解析”认定负阈值或溢出成非有限的数字是合法业务验收条件。

check_accuracy等字段保留os.environ字符串，dump_fx_graph使用字符串的真假值：例如非空"0"也可能使这一配置分支成立并关闭split_reductions。这里只陈述源码配置分支，不推断全部校验消费者均以相同方式处理、不建议用这种写法关闭功能，也不扩大本卡文档限定的PyTorch2.7.1/2.9与Triton/DVM支持范围。取空值、导入时机和后续消费者需分别确认，本次没有导入或运行校验。

## 内置调试页不覆盖公开版本门槛

内部CHECK_ACCURACY与DUMP_FX_GRAPH页只列950DT，默认未设/空关闭，示例1/true/yes启用；前者开启会连带dump，AOTI_ASCEND_DEBUG_KERNEL也可触发dump。调试会增加编译时间与文件/磁盘开销，单独开启dump不等于执行了数值比较。

这些短页没有重复公开环境页的PyTorch2.7.1/2.9及Triton/DVM限制，不能把省略解释为支持所有新版本，也不能据文字的“关闭”忽略前文原始字符串0仍可能为真的源码分支。文档合法值、配置表达式和后续消费者是不同证据层。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/api/environment_variable/inductor/INDUCTOR_ASCEND_CHECK_ACCURACY.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/api/environment_variable/inductor/INDUCTOR_ASCEND_CHECK_ACCURACY.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/config.py)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/other/INDUCTOR_ASCEND_CHECK_ACCURACY.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/other/INDUCTOR_ASCEND_DUMP_FX_GRAPH.md)（primary）
