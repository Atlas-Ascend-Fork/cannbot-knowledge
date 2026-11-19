---
type: Guide
title: Inductor AscendC benchmark：检查对象、数值边界与性能口径
description: 区分重编译FX检查与实际artifact采集，补充NaN/Inf、复数及聚合指标的局限。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/precision_check_design.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/precision_check_design_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/manuals.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/manuals_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/precision_check.py
  role: implementation
created_at: '2026-11-09T18:28:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Inductor AscendC benchmark：检查对象、数值边界与性能口径

## 固定来源与草稿范围

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c双语精度设计、手册和precision_check.py的比较函数局部。硬件范围未为整套调试能力闭合，保留draft/空platforms。未运行生成脚本、反序列化输入、调用编译产物或做数值实验；阈值是来源当前实现，不从外链推导最新通用标准。

## 三种模式测的不是同一个对象

| 模式 | 实际检查/测量对象 |
| --- | --- |
| --check | 从FX上下文重建Eager片段，并与重新torch.compile所得结果比较；不是编辑后的当前artifact二进制验收 |
| --bench | 相同重建片段的Eager/Graph对照，通过profiler CSV按step汇总设备Kernel Duration |
| --profile（默认） | 真实async_compile_artifacts执行与采集；没有数值参考，采集成功不等于精度通过 |

--e2e使用生成时内联的asc_graph副本，从AscIR重走Codegen；之后只编辑旁边asc_graph.py不改变已生成脚本。它可与三模式组合，但不会把--check自动变为当前artifact的逐位检查。发布旧手册使用位置参数e2e，主线已改--e2e，不照抄跨版本命令。

PrecisionContext保存FX代码、输入元数据和输出顺序，BenchmarkSpec将图生成与写文件分离。提取要求节点依赖可序列化、call_function目标可表达、有足够参数/元数据；输出优先按真实OUTPUT关系选择，缺失时叶节点回退。提取失败会仅生成profile路径，不等于设备Kernel必有错误，也不能把缺少检查按钮解释成已通过。

## 输入、环境与数值覆盖

随机输入保留shape/stride/dtype，动态符号按当时hint具体化；一个hint和随机分布不覆盖业务输入、mask、极端值、别名或全部动态范围。脚本在import torch前回写生成时TORCHINDUCTOR_*，固定ascendc后端并排除缓存根等不应复用项；命令行同名值优先，差异会stderr告警。保留这份配置身份再比较，不能只看输出文件名相同。

来源比较通常将expected/actual转float64并flatten：CosineSimilarity>0.99、RelativeEuclideanDistance<0.05、KL<0.005三项同时满足才通过，RMSE/MAE>1.1只是警告。欧氏分母使用actual平方和；KL分别按自身min/max归一化、clamp后归一成分布，常量范围分支保持原值，不是逐元素误差上界或任务精度标准。

源码的特殊分支必须一并保留：空expected直接通过；量化Tensor先dequantize；非浮点且非复数按元素精确比较。NaN位置、Inf位置及符号必须相同才排除这些位置继续算指标，全部同位置非有限可通过并带NOTE；**这样的通过不能证明模型没有NaN/Inf**。两边近零范数的cosine视1、单边近零视0，actual近零时欧氏距离返回0，不能单看一个指标。

复数虽然进入浮点比较分支，随后to(float64)不能完整保留虚部；不能把该函数的通过作为完整复数精度保证。函数局部没有独立shape/dtype完全一致的前置断言，compare_outputs还用zip并跳过非Tensor，不能据布尔通过证明输出结构、数量、布局和全部非Tensor结果都相同。业务验收须独立核对这些合同，再选合适数值指标。

## 性能解释与复现成本

--bench读取最近ascend_pt中的Step Id与Duration(us)，按step累加Kernel时长，最多展示10步，Ratio=Eager/Graph。多流重叠时Kernel时长之和不是关键路径或端到端时延；Avg与示例2.18x仅说明该来源输出口径，不作本模型收益。默认profile设计11轮、skip首轮后10轮采集，和PGO候选选优的采集窗口不同。

同一固定输入重复执行可能逐步提高L2命中；冷编译、首次运行、稳态设备与端到端时间分开记录。修改Codegen时--profile --e2e看产物路径，--check看重建FX的数值，不把其中之一替代另一个。异常、缺失输出和仅profile降级都保留上下文；本次只静态摄取，没有新增verified证据。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/precision_check_design.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/precision_check_design_en.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/manuals.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/manuals_en.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/precision_check.py)（implementation）
