---
type: Guide
title: Inductor AscendC前后置FX改写：scatter_nd现代化、Pad消解与三组融合折叠
description: 逐条记录run_pre_grad_custom_pass与run_post_grad_custom_pre_pass的触发条件、改写形态与守卫，覆盖legacy
  scatter替换、pad+slice消除、embedding批量融合、GMM ReLU折入act_type和bmm+bias折入baddbmm。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/passes/inductor_custom_passes.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/__init__.py
  role: implementation
created_at: '2026-11-13T04:23:15Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Inductor AscendC前后置FX改写：scatter_nd现代化、Pad消解与三组融合折叠

## 固定版本与证据范围

本卡固定TorchAir主线`92e1e967bd35ebc37a442b4a969730bf3cf77a3c`的`experimental/_inductor_npu_ext/python/inductor_npu_ext/passes/inductor_custom_passes.py`（923行全文）。该文件仅主线存在；发布扩展只有`passes/auto_functionalize_legacy_ops.py`单一pre-grad入口，其形态由[包与调试](torchair_inductor_ascendc_package_and_debug.md)的导入期一节承载，本卡不重复。整卡平台未知，保持draft与空平台；未导入上游、未执行pass、未验证数值或融合产物。

## 挂载点与总开关

`run_pre_grad_custom_pass`固定执行scatter_nd替换与pad消解两步；`run_post_grad_custom_pre_pass`先无条件执行embedding批量融合，再按`config.enable_gmm_fuse`（TORCHINDUCTOR_ASCENDC_DEBUG=gmm）与`config.enable_matmul_fuse`（未设nomatmul）分别叠加GMM ReLU折叠与bmm bias折叠。两入口由`__init__._load_npu_passes`注册进`inductor_config.pre_grad_custom_pass`/`post_grad_custom_pre_pass`；已被占用时只告警不覆盖。每个pass改写成功后统一`graph.lint()`并按需`eliminate_dead_code()`。

## pre-grad：scatter_nd现代化与pad消解

`_replace_legacy_npu_scatter_nd_update_pass`把`torch.ops.npu.npu_scatter_nd_update_`替换为`modern::npu_scatter_nd_update_`自定义算子（原地签名`Tensor(a!)`，NPU实现转发原op，Meta为空）。目的写在docstring：让AOT能对它自动函数化、Inductor融合后再re-inplace。`torch_npu.py`测试桩在无设备环境以`torch.library.Library("npu","FRAGMENT")`定义同名op兜底，不是产品注册。

`_pad_slice_fold_pass`处理`torch._C._nn.pad`：仅当pad是单维右侧填充（从后向前映射，其余维零填充，多维或左侧填充直接跳过），且全部消费者是对`__getitem__`切片、切片区间落在该维原始长度内（`slice_end<=input_shape[pad_dim]`、step为1或None）时，把每个切片的输入直接改回原张量并删除pad节点——填充区完全落在切片捕获范围之外，pad是空白计算。

## post-grad一：embedding批量融合（Pattern C）

`_batch_embedding_fusion_pass`把同一权重的多次`aten.embedding.default`+同型reduce合并为单次`reshape→embedding→reduce`：

- 分组键为（权重节点标识，权重第二维D，索引的符号化shape键）。权重必须2维且无SymInt维；只收默认参数调用（padding_idx=-1、无scale_grad_by_freq/sparse）。
- 索引必须来自同一父张量同维连续`slice`，且这些slice按start排序后无重叠完整覆盖该维（`N*L==dim_size`，各段等长L）；父维长度必须静态。
- 每个embedding的唯一使用者必须是同一种`keepdim=False`、沿该维的reduce（sum/mean/amax/amin的dim_IntList族或prod.dim_int）。
- 改写：父索引reshape为`[...,N,L]`，一次embedding后沿新增维reduce，再按原顺序对reduce结果逐个`select`接回原使用者；若下游select链满足「全部单引用、同一cat、在cat末维按序连续出现」，则进一步折叠为一次flatten reshape直接进cat（`_try_collapse_select_chain_into_cat_reshape`，要求select轴为倒数第二维）。
- 全部fake shape推演在fake_mode内试算，任一异常即整组放弃保持原图。

## post-grad二：GMM ReLU折入act_type

`_grouped_mm_relu_to_act_type_pass`仅处理`torch.ops.npu.npu_grouped_matmul(.default/.List)`且`split_item∈{2,3}`（单输出模式）：输出`[0]`的全部直接消费者必须是ReLU（`aten.relu`或`relu_`，两种别名语义不同不得混折，故要求整组恰好一种）；out-of-place多级ReLU还要求单链（多分支会合并原本独立的结果缓冲，改变别名可见性）。原`act_type`必须为缺省或0时才置1并删除ReLU节点。GMM的GE侧lowering见[GroupedMatmul](torchair_ge_matmul_lowering.md)，本卡只记FX层折叠条件。

## post-grad三：bmm+bias折入baddbmm

`_bmm_add_bias_fold_pass`把`bmm(a,b)+bias`改写为`baddbmm(bias,a,b)`（beta/alpha均为1的数学等价）：bmm必须2个位置参数无kwargs、输出单引用且唯一使用者是`add.Tensor`（alpha=1）；bias形状须为可广播向量`[n]/[1,n]/[1,1,n]`且末维与bmm输出末维**可证明**相等、前导维**可证明**为1——动态shape下只接受结构恒等或`statically_known_true`可证（hint不参与，宁可漏判不可误判）；bmm与bias的dtype必须一致且落在`{fp16,bf16,fp32}`融合能力集合（集合外折叠无融合收益）。不满足任一条件保持原图，由batch轴广播epilogue门禁决定是否拆kernel。

## 边界

三组折叠的收益判断（「拆开反劣于整算子fallback」类注释）是主线源码立场，本卡未运行对照实验验证。embedding融合的符号shape键把同表达式的SymInt按字符串分组，不同表达式但运行时相等的索引不会合并；pad消解不处理列表式`slice`调用或非getitem消费者。`eliminate_dead_code`只在改写发生时执行，不能当作通用DCE。本卡不覆盖同文件之外的scheduler级融合，后者见[融合决策](torchair_inductor_ascendc_fusion_decisions.md)。

## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/passes/inductor_custom_passes.py)（primary）：1–923完整读取（pass挂载51–63、scatter替换28–48、embedding融合66–107/369–794、GML折叠110–211、bmm折叠275–366、pad消解797–856、meta工具859–923）。

- [固定实现来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/config.py)（implementation）：门控变量定义区（enable_gmm_fuse/enable_matmul_fuse由TORCHINDUCTOR_ASCENDC_DEBUG派生）。

- [固定实现来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/python/inductor_npu_ext/__init__.py)（implementation）：`_load_npu_passes` 107–135（注册与占用告警）。
