---
type: Guide
title: Inductor AscendC矩阵Lowering：布局、Bias与高维回退
description: 完整核对mm/addmm/bmm/baddbmm的实际门控、零K、输入物化、Bias形状和reshape回退信息，区分模板与最终CV融合。
tags:
- task.implementation
- topic.graph_execution
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/mm_lowering.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/common.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/utils.py
  role: implementation
created_at: '2026-11-11T05:08:52Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Inductor AscendC矩阵Lowering：布局、Bias与高维回退

固定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的完整mm_lowering.py及所列布局helper。Soc.A5为Ascend950系列（包含旧称Atlas A5）的本地枚举门控，_is_matmul_supported_on_soc在current_soc=None时同样返回True，这个未知分支不构成设备支持证明。保持draft/空平台，未运行上游。固定发布7c6c754bed00c86ffaaa2a45cb7ac2724f058013没有此具体路径，其他矩阵实现另计。

## 共同门控与输入准备

四个default overload使用type_promotion_kind=None注册，guard登记F三浮点类型；lowering本体检查A/B dtype相同，随后仍调用promote_types确定输出。模块的helper没有独立再次检查A/B是否属于F或两者device一致，这些条件需结合外部入口。disable_canfuse、SoC不通过、K无法证明相等时回原ATen；bmm还比较batch元素总数。_simplify_expr先用图sizevars，异常再sympy.simplify；等零接受整数0或is_zero=True。

_is_degenerate_matmul_shape要求m和n**同时**可证明为1，虽然日志reason写degenerate_m_or_n_one，不能据名字说任一维1就回退。此检查先于零K。无Bias的mm/bmm在K可证明0时返回常量0 Pointwise；addmm/baddbmm遇零K回原带Bias操作，保留原alpha/beta。addmm/baddbmm仅alpha==beta==1.0走本路径，其余原参数回退。

_prepare_matmul_input先读layout/size/stride；AttributeError/NotImplementedError时realize并尝试unwrap_storage_for_input，unwrap异常返回None，随后相同两类访问异常也None，其他getter异常不在这层统一吞掉。_is_supported_matmul_metadata要求offset可证明0，且非1维没有零stride；再接受contiguous、末两轴矩阵transpose，或enable_load_transpose下的batch轴contiguous permutation。一般transpose、slice offset和expand不因此自动接受。

contiguous检查要求size/stride同秩，忽略size1轴的stride，再按行主序累计；矩阵transpose helper检查末两轴stride为1与size[-2]，外部非1轴连续。batch helper要求至少3维且同秩，去1轴后重建物理连续排列；等于原顺序或纯矩阵转置返回False。_freeze_materialized_input_layout只对ComputedBuffer复制为含真实offset的FixedLayout，其他IR对象保持原形；真正物化/拷贝量由外部实现和运行结果决定。

## Bias向量与显式Add

Bias向量形状须非空、末维等于N，前导维全为1；addmm最大秩2，baddbmm最大秩3。_prepare_matmul_bias先把Bias view为[N]再准备物理输入，同时准备original_bias供回退；try只覆盖view和首次squeezed布局准备，所捕获异常才回None，随后original_info=_prepare_matmul_input(original_bias)在try外，仍可能传播该helper未捕获的RuntimeError等异常。注释称零拷贝，代码只是委托view与布局helper，本次没有测量或证明所有输入都无分配。

向量Bias放进MatMulBias/BatchMatMulBias属性输入，inputs顺序[A,B,bias_attr]，input_layouts保逻辑布局；fallback_inputs却保[bias_original,A,B]，与原ATen签名一致，不能按属性输入顺序回退。Bias非向量时构造无Bias MM/BMM模板再add(result,bias)，其fallback_op为mm/bmm；这不表示所有非向量Bias已最终融合。这里没有额外检查Bias dtype与A完全相同或对Bias再执行A/B同样的_supported_metadata门控，仍需下游合同。

A/B以及存在的原Bias回退对象在模板前realize，并固定ComputedBuffer物理layout；InputsKernel.unwrap_storage后，模板保存input_layouts、has_bias、fallback_op、fallback_inputs、fallback_input_layouts。输出为contiguous FixedLayout。两个模板继承TemplateBuffer、make_kernel_render=None，没有普通body；生成时有无合格epilogue决定CV或原生调用，见[中央生成/回退](torchair_inductor_ascendc_schedule_codegen_wrapper.md)。

## 高维batch恢复的证明链

_infer_highdim_batch_matmul_layout只从A/B当前均3D的view查unwrap_view；原base都必须大于3维、秩一致且逐batch维相等，当前flat batch等于base batch乘积，矩阵末两维逐项一致。返回logical A/B/output和flat A/B尺寸。_unwrap_view_size只保护unwrap_view调用，后续base.get_size仍可能传播异常。

恢复还要求当前FX节点是bmm/baddbmm，唯一user是reshape/view/_unsafe_view，位置args[0]恰为该节点，输出Tensor meta形状等于logical_out_size。没有这个完整证据则保持flat路径。真正bmm/baddbmm本体的rank检查是>=3；没有在这里替任意外部调用补齐所有rank、batch轴或广播规则。

通过恢复时对A/B unwrap到高维base，比较batch尺寸乘积、K、退化与布局后，用logical_out_size生成模板；否则输出[batch_product,M,N]。bmm保存fallback_kind=reshape_bmm_reshape。baddbmm若不是向量Bias，还要求原Bias当前是flat输出形状的3D view，其高维base恰等于logical输出形状，才unwrap Bias；不能匹配就回原操作。

baddbmm的fallback_kind按向量Bias选择reshape_baddbmm_reshape或reshape_bmm_reshape，后者仍在模板外加Bias。上下游的reshape消费者、保存的原参数与codegen中的flatten/reshape必须共同核对，不能把模板存在等同整个reshape链已经消失。

诊断log_mm_fusion_fallback记录具体reason和可安全取得的size/stride/dtype/device，诊断getter异常标unavailable；日志不是设备执行结果。[中央融合决策](torchair_inductor_ascendc_fusion_decisions.md)继续约束共享输入、额外输入布局、broadcast、归约与vector compute。

## 完整本地实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/mm_lowering.py)（primary）：1–946。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/lowering/common.py)（implementation）：155–220。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/common/utils.py)（implementation）：273–317。
