---
type: Guide
title: TorchNPU Profiler的FLOPs Hook、注册与观测作用域
description: 限定Python目标/既有别名覆盖、注册覆盖、重入和MSTX范围的诊断含义。
tags:
- task.optimization
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_flops_hook.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_flops_registry.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_flops_formulas.py
  role: implementation
created_at: '2026-11-11T07:41:04Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU Profiler的FLOPs Hook、注册与观测作用域

## 主线实现与覆盖范围

依据PyTorch固定主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`，完整读取_flops_hook.py、_flops_registry.py及_flops_formulas.py，共754行。发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的这三个精确路径Git树无条目，仅说明这些路径无同名实现，不否定发布的其它FLOPs能力。平台未知，未导入或执行Hook、公式、MSTX、采集或设备实验。

现有[Kineto关键启停链](../../../apis/torch_npu/profiler_kineto_profile.md)只在主线with_flops且tx_enabled时调用安装/卸载；本卡补被调实现，不把with_flops或安装成功当成全部算子、编译图、反向和产品均已统计。

## 15个默认Python目标，不是所有Kernel

_build_target_ops先import公式模块使装饰器登记，再按get_npu_flop_targets解析module:attr.path。缺冒号、import触发ImportError或中间属性缺失时警告并跳过；最后属性是否存在留给install检查。内部并非遍历设备Kernel或自动为任意新算子生成公式。

固定默认目标为torch.mm/bmm/matmul/addmm、torch.nn.functional.linear及10个torch_npu入口：npu_fusion_attention、npu_fused_infer_attention_score、npu_all_gather_base_mm、npu_transpose_batchmatmul、npu_grouped_matmul、npu_quant_matmul_gelu、npu_grouped_matmul_swiglu_quant_v2、npu_alltoallv_gmm、npu_gmm_alltoallv、npu_block_sparse_attention。默认列表没有相应attention grad/v3等入口，不能把相近名称自动归入；框架或设备的其他统计入口独立。

register_npu_flop默认名字取target冒号后路径，未提供可用target才取函数名；默认和外部各一字典。外部同名后注册覆盖并报错日志，get_flop_func优先外部。get_npu_flop_targets仅合并非None target，外部非None覆盖默认；外部只给同名公式但target=None时，目标表仍可能来自默认，而实际取公式优先外部。没有在此把所有注册输入验证成公共稳定插件协议。

## 安装修改既有模块属性，恢复不是所有引用扫描

FlopsHookManager用类级字典保存原函数、目标和额外引用；已_installed时install直接return，不根据新target_ops增量更新。默认15目标中缺末端函数只告警跳过；只要实际patch了至少一个目标，_installed就True，并不表示15个全部存在。

对每个目标先getattr、造wrapper并setattr替换，再扫描当前sys.modules快照中**同一个属性名且对象身份等于原函数**的引用，逐个重绑。不同别名名、容器成员、闭包、以后才导入的引用、原生/编译调度不会因此自动全覆盖；安装扫描和改属性本身也有Host成本，没有在此测量。模块getattr异常被引用扫描跳过。

install循环内部异常会_restore后重新抛；目标表构造发生在该try前。_restore把所记录目标和额外引用写回原函数，清字典并_installed=False，uninstall直接调用它。没有锁、实例引用计数或完整回滚失败保护，也不自动恢复未被记录的任意引用；外层启停的异常清理边界仍按Kineto卡。

## 范围标记、重入与失败

wrapper用threading.local.in_hook避免同线程内部调用再次计数：已在Hook中便直接原函数，外层计算期间也置True。这能抑制嵌套重复标记，不是全图/跨线程的统一去重或精确训练计算图核算。

先get_flop_func并计算；非None且>=0时，MSTX domain='mfu_flops'，消息为“flops-op_name”。因此0也可标记，负数/None不标记；公式、比较或range_start在内部try里失败时警告，随后仍调用原函数。缺标记不能直接当算子没执行，也不能补成0 FLOPs。公式在原函数之前求值，依赖输入shape/列表，不读取真实执行指令数量。

标记开始后才调用原函数；finally对正整数range_id调用range_end，然后清线程标记。原函数异常通常仍经过此收尾，但若range_end本身传播异常，后面的in_hook=False也可能被跳过；没有独立第二层finally保证它。本文不执行故障或据此声称已观测到泄漏。

计数公式的int(shape)、输入序列转换和部分tolist可能增加Host操作或数据提取；重入抑制不消除这些成本。MSTX范围还包住Python包装和算子下发，不能将range名里的理论工作量除以任意Host范围耗时就称设备MFU。形状公式和实际吞吐的边界见[Attention/GEMM估算](torch_npu_profiler_attention_gemm_flops_estimates_and_throughput.md)。

## Evidence

- [固定主线源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_flops_hook.py)（1–153行，完整本地模块）
- [固定主线源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_flops_registry.py)（1–56行，完整本地模块）
- [固定主线源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/_flops_formulas.py)（1–545行，完整本地模块）
