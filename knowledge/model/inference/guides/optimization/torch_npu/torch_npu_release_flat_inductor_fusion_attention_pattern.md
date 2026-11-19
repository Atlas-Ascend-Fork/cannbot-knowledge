---
type: Guide
title: torch_npu 发布版 Inductor fusion attention 图模式注册链（release-only register_fa_pass）
description: 记录发布 pin 扁平 npu_fusion_attention_graph.py 中 register_fa_pass 的 BNSD fp32 模式注册全链（joint_fwd_bwd/fwd_only、dropout 部分化、scale 流动）、与主线迁移版共享前缀的等价性验证，及主线删除该注册并改走 fav3 分区 pass 的负证据。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/npu_fusion_attention_graph.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/__init__.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/pattern_match/npu_fusion_attention_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/pattern_match/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/fav3_partition_pass.py
  role: implementation
created_at: '2026-11-12T08:00:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu 发布版 Inductor fusion attention 图模式注册链（release-only register_fa_pass）

## 固定版本与适用范围

发布 pin（f3ecfe4a）default（Triton）分支的接线链：`_inductor/__init__.py:34` 导入并在 `:152` 调用 `register_fa_pass()`（在 `:109` `_register_npu_inductor_decompositons()` 之后，`:112` 注释明确要求 fx pass 注册放在 decomp 注册之后，调用序相符）→ 扁平 `npu_fusion_attention_graph.py:160-256` 在 fake mode 下把一条 fuse_attention 模式注册进 torch `_inductor.fx_passes.joint_graph` 的 patterns → 命中后经 `:157` 注入的 `torch_npu.npu_fusion_attention_graph` 属性进入 `NpuGraphAttentionFunction` 与 `torch.ops.npu_graph.npu_fa`。本卡覆盖发布版接线链中的 FA pass 一环（其余 patch 归各专卡）；mlir/dvm 分支不调用该函数。算子定义、scale 位置/关键字分支、Meta 布局与 19 输入对 26 槽 backward 的差异已由[主线版图桥卡](torch_npu_inductor_graph_attention_bridge.md)建卡，本卡不重写，只记录 release 侧注册链与两 pin 差异。纯静态阅读，未运行任何编译或模式匹配；draft、platforms 为空。

## 模式注册表（实际门槛 → 动作 → 失败/版本边界）

| 实际门槛 | 动作 | 失败/版本边界 |
| --- | --- | --- |
| `@init_once_fakemode`（`:160-161`），torch pattern_matcher 首次物化时执行一次 | 构造并注册下述模式对 | 函数仅存在于 release；主线迁移版已删除（见负证据节） |
| 模式 `_npu_fusion_attention_graph_pattern_1`（`:168-175`） | `q/k/v = input.permute(0,2,1,3)`；`dropout(matmul(q,k.transpose(-2,-1)).div(inv_scale_factor).softmax(-1), p=dropout_p) @ v` | 输入按 BSHD 理解（示例 `(2,4,8,16)` fp32、`requires_grad=True`、device `'npu'`，`:195-201`） |
| 替换 `_npu_fusion_attention_graph_replacement_1`（`:177-191`） | `counters["inductor"]["fuse_attention"] += 1`；`head_num=query.size(2)`；`input_layout="BNSD"`；q/k/v `transpose(1,2)` 回 BNSD；`scale=inv_scale_factor`；`keep_prob=1.0-dropout_p`；取返回 `[0]` | inv_scale_factor 是模式中的除数；`pse/padding_mask/atten_mask` 置 None（本模式不匹配带掩码变体） |
| dtype 循环仅 `torch.float`（`:201`） | 每个候选注册两个变体 | `_half` 后缀分支（`:217-218`）与 `_bs1` 分支（`:220-221`）在该 dtype/示例下不触发：fp32 只注册 `_npu_fusion_attention_graph_pattern_1_training` 与 `..._inference` 两个名字；其他 dtype/layout 不由本文件注册 |
| training 变体（`:223-231`） | `register_replacement(search_fn/replace_fn/example_inputs, trace_fn=joint_fwd_bwd, pass_dicts=joint_graph.patterns, scalar_workaround={"dropout_p": 0.113377})` | 反向路径依赖 `NpuGraphAttentionFunction.backward`；其 26 槽返回对 19 输入签名的数量不一致见图桥卡，本卡不重复数值/派发结论 |
| inference 变体（`:243-251`） | workaround 必须恰为 `{"dropout_p"}`（`:234-235` 否则 ValueError），经 `partialize_and_update_signature`（torch `fx_passes.fuse_attention` 上游助手）把 pattern/replacement 的 `dropout_p` 固定为 0.0 后按 `fwd_only` 注册 | 仅去除 dropout 维度的标量 workaround；不改变替换函数其他语义 |
| `TOKEN_MAX = 2147483647`（`:162`） | 定义后未使用（全文静态检查） | 记录为冗余常量，不推断预留语义 |

## scale 的实际流动（补图桥卡的调用路径证据）

替换函数把模式除数 `inv_scale_factor` 以 **关键字** `scale=` 传入 `torch_npu.npu_fusion_attention_graph`；`npu_fusion_attention_graph`（`:146-154`）以 19 个**位置实参**调 `NpuGraphAttentionFunction.apply`；`forward`（`:102-107`）再以 **kwargs**（`pse=pse, scale=scale, ...`）调 `torch.ops.npu_graph.npu_fa`，该调用只有 5 个位置实参，**不触发** `npu_fa` 实现中 `len(args) > 8` 时对 `args[8]` 取倒数的分支（`:24-30`）——即 FA pass 这条链上 `inv_scale_factor` 原样进入 `torch_npu.npu_fusion_attention` 的 `scale` 形参。位置调用取倒数分支、`except IndexError` 不可达性与 ZeroDivisionError 行为见图桥卡。`torch_npu.npu_fusion_attention` 算子本体对 `scale` 的语义（乘子还是除数）未在本链内核对：两条调用形态约定不同，不能从本文件单点断言哪条正确，使用时按实际 CANN 版本的算子语义核对。

## 两 pin 共享前缀等价性验证（静态文本处理）

主线迁移版 `fx_passes/pattern_match/npu_fusion_attention_graph.py`（171 行）与 release 扁平版（257 行）除 release 末尾 `register_fa_pass` 块（`:160-257`，主线无对应）外全文件 raw diff 比对：差异仅为字面重排——schema 字符串拆成相邻字面量（`ast.literal_eval` 拼接后逐字节相同，两个 define 均验证）、`backward` 返回 tuple 换行重排（两 pin 均为 26 项、`grad_pse` 位于第 6 槽）、`saved_tensors` 解包换行；`forward` 参数两 pin 均为 19 个。等价只覆盖两 pin 的该前缀，不外推到其他版本。

## 主线缺席与替换证据（negative evidence）

- 迁移版文件中 `register_fa_pass`、`init_once_fakemode` rg 零命中：**这条命名注册链（release 扁平文件的 `register_fa_pass` 函数及其 fake-mode 注册）在主线迁移版中被删除**，仅保留 op 定义/autograd Function/属性注入——rg 只证明该 exact 注册链缺席，不证明主线整体 SDPA→npu_fa 融合能力缺席。
- 主线 `fx_passes/pattern_match` 包（`__init__.py` 仅 re-export `npu_fusion_attention_graph`）在主线 torch_npu 全树 rg 零 importer：npu_graph 库定义与 `torch_npu.npu_fusion_attention_graph` 属性注入在主线无已知加载者（与图桥卡"未闭合调用者"结论一致，本卡以全树 rg 补硬证据）。
- 主线 default Triton 后端加载块（`__init__.py:284-296, 315-325`）改为调用 `register_fav3_partition_pass()`（`:321`）：对 FA v3 TND+dropout 路径做 ACLgraph 捕获分区改写，**不做融合替换**，机制与 release 的 pattern replacement 完全不同，边界见[fav3 捕获分区卡](torch_npu_fav3_capture_partition_proxy.md)。
- 因此该注册链（此文件/函数与 `_inductor/__init__.py:34/:152` 加载链）是 release-only；"SDPA 模式 → npu_fa 融合替换"整体能力是否在主线以其他形式存在，本卡未证明，不做"主线全部缺席"断言；也不据此对任何版本的注意力性能或精度做承诺。

## 失效边界与静态口径

- 结论只覆盖 release pin default 分支与主线 pin 的对照；同一 torch 上游版本下两 pin 的实际模式命中行为未运行验证。
- 模式只按 fp32/BNSD 形状示例注册；带 pse/atten_mask、非 fp32、BSB/SBH 输入或其他 fuse_attention 变体不由此文件覆盖。
- 与[发布版扁平接线卡](torch_npu_release_flat_inductor_autotune_wiring.md)（`:152` 处接线行）与[主线 runtime 补丁链卡](torch_npu_inductor_runtime_cached_autotune_patches_and_fasta.md)边界互补；与[发布版分解表面卡](torch_npu_release_flat_inductor_decomposition_surfaces.md)的 `:112` 顺序约束互链。
