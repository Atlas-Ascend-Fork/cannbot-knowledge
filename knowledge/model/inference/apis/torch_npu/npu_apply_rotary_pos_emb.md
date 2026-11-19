---
type: API
title: npu_apply_rotary_pos_emb：Q/K 原地旋转与平台分支
description: 区分原地 RoPE 与 rotary_mul，明确 A2/A3 和 950DT 的布局、维度及旋转模式差异。
tags:
- task.lookup
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-apply_rotary_pos_emb.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-apply_rotary_pos_emb.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ApplyRotaryPosEmbNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ApplyRotaryPosEmbNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/apply_rotary_pos_emb.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/apply_rotary_pos_emb.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AutogradErrorFallback.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_autograd_error_fallback.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/Version.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/CMakeLists.txt
  role: implementation
created_at: '2026-11-09T02:09:29Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# npu_apply_rotary_pos_emb：Q/K 原地旋转与平台分支

## 版本与范围

公开产品契约依据ascend_main_candidate的固定主线OpPlugin，中英文一并核对；另区分发布提交已存在的schema/C++和Python暴露证据，不能据实现存在推定26.0.0组合支持所有参数。主线软件配套尚未确认。

## 接口与语义

以下是固定来源的接口声明：

```text
torch_npu.npu_apply_rotary_pos_emb(query, key,  cos, sin, *, layout='BSND', rotary_mode='half') -> (Tensor, Tensor)
```

Eager融合query/key两路RoPE并原地更新它们，返回(query_out,key_out)；图转换器会先复制Q/K，其别名与副作用另见下文。保留旧 Q/K 值的调用方需自行处理别名与生命周期；不能按 npu_rotary_mul 的独立输出语义替换。四个输入为同 dtype 的 FP16/BF16/FP32、ND。

## 参数与组合限制

- A2/A3：不支持空 Tensor，Q/K 的 D 为 64 或 128，只支持 BSND 四维或 TND 三维、rotary_mode="half"。BSND 的 B/S、TND 的 T 必须对应相等；Q/K 的 N 可不同，cos/sin 的 N 必须为 1。Q/K 的 D 相等，cos/sin 的 D 相等。
- 950DT：支持空 Tensor、D≤1024，布局增加 SBND/BNSD；Q/K 除 N 外的维度相同，cos/sin 的 D 相等且不大于 Q/K 的 D，cos/sin 的 B 与 Q/K 相等或为 1、N 为 1。
- 950DT 的 half/interleave 要求末维被 2 整除，quarter 要求被 4 整除。不能把这些模式和布局回推到 A2/A3。
- 本卡没有覆盖来源的其他硬件分支，也没有把主线新增入口视为已存在于发布组合。

## 验证与模型关联

在调用前保存独立参考值，分别比较 Q/K 的数值和原地更新效果；覆盖不同 Q/K 头数、布局及部分旋转维度时逐项核对平台分支。 本次为文档与静态调用核对，未运行算子或测量性能。

Recipes 中的[调用位置](https://gitcode.com/cann/cann-recipes-infer/blob/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/bailing_2_5/models/modeling_bailing_moe_v2_5.py#L1391)仅作为接口依赖线索；它不证明本卡的平台、软件组合或所有执行分支已验证。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)
- [独立 RoPE 输出接口](npu_rotary_mul.md)

## 完整双语与发布实现的适用边界

主线中英文的公开产品页确认A2/A3、旧Atlas推理系列与950DT；950家族在本卡仅指DT，不能扩到PR。旧Atlas推理不支持BF16。四个输入dtype相同；TND为三维，其他公开布局为四维。旧Atlas/A2/A3只支持half、BSND或TND、D为64或128且不支持空输入；950DT增加SBND/BNSD、interleave/quarter、D≤1024和空Tensor。950的cos/sin末维相等且不大于Q/K末维，B可为1以广播，half/interleave按2整除、quarter按4整除；不将部分旋转、空输入和新布局回推旧产品。

公开文件名apply_rotary_pos_emb没有npu前缀，但实际Python接口仍是npu_apply_rotary_pos_emb。固定发布提交已有同名schema与C++包装，schema默认layout='BSH'，没有主线新增的exposed字段；主线schema改为'BSND'并标exposed=[v2.7,newest]。这仅证明实现已存在，不能由缺发布公开页断言实现不存在，也不能由schema存在证明发布Python入口的暴露状态、硬件或配套版本。

两个C++均将BNSD/SBND/TND映射为3/2/4，其余字符串一律落到1，连拼写错误也没有单独拒绝；图转换器则显式只接受BSH/BSND/SBND/BNSD/TND。调用前使用公开合法布局，不能用Eager未报错建立任意字符串别名。C++接受half/quarter/interleave，但缺aclnnApplyRotaryPosEmbV2时退到不接收rotary_mode的V1；该降级未检查是否为half，不保证保留用户指定的旋转配对。

## Eager原地、Meta占位与图复制

两个固定C++都直接传入query/key并返回std::tie(query,key)，没有另分配输出。schema却未标注Tensor别名，Meta返回两个独立empty_like；不能由FakeTensor的独立占位推断真实Eager不修改输入。两个固定TorchAir转换器先对Q/K分别执行TensorMove，再调用GE ApplyRotaryPosEmb，返回GE结果；因此本卡的原地说明限定Eager，图路径没有建立输入别名或原地副作用的一致保证。

公开样例中的打印成功不是本仓的运行记录；文档没有单独给出所有训练或图分支能力，转换器存在也不扩充公开产品限制。保留Q/K供后续计算时，必须按实际执行路径核对生命周期和输入是否被复用。本次只读固定快照。

## Evidence

- [固定 OpPlugin 接口文档](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu/torch_npu-apply_rotary_pos_emb.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu/torch_npu-apply_rotary_pos_emb.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ApplyRotaryPosEmbNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ApplyRotaryPosEmbNpuOpApi.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/apply_rotary_pos_emb.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/apply_rotary_pos_emb.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

## 主线无反向实现的抛错边界

主线 [d84e9b1d6a558e5f27973cd4329f62968e46fdda 的 AutogradErrorFallback.cpp](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AutogradErrorFallback.cpp)（全 17 行读毕）为 `npu_apply_rotary_pos_emb` 注册 PyTorch 内置 `autogradNotImplementedFallback`（`AutogradPrivateUse1` dispatch key 上的 boxed 内核；源注释自述对任意算子 schema 通用、无需匹配各自签名）。实际门槛与动作：前向照常执行；仅当对依赖本算子输出的张量调用 `.backward()` 时抛 `RuntimeError`，源注释给出的文案模式是 `derivative for 'npu::xxx' is not implemented`，主线[官方用例](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_autograd_error_fallback.py)只断言 "not implemented" 子串，完整文案未运行核对。用例以 `requires_grad` 叶子张量进入前向构造依赖，且仅声明在 A5 / Ascend950 验证、其它机型自动跳过。

版本门槛：该注册包在 `#if VERSION_BETWEEN(V2R7, VERSION_NEWEST)` 编译保护内。主线 [Version.h](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/Version.h) 定义 `V2R7=6`、`VERSION_NEWEST=V2R16`，`CURRENT_VERSION` 由构建期 PyTorch 版本以 `V<major>R<minor>` 注入（[CMakeLists.txt](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/CMakeLists.txt)），即仅 PyTorch ≥2.7 且不超过 2.16 枚举上限的构建注册该 fallback；源注释解释为低版本未注册该算子，与本卡上文 exposed=[v2.7,newest] 的口径一致，低于 2.7 的主线构建没有该注册。

失败与版本边界：该注册只覆盖 `npu_apply_rotary_pos_emb` 单 schema，[npu_rotary_mul](npu_rotary_mul.md) 不在注册列表，不能据本节推断其反向状态。
发布 dedc316708372c9a8bfde4527abd2a94b74840f5 没有该文件，且全仓不含任何 `autogradNotImplementedFallback` 注册（rg 负向核实），发布组合下反向缺失的行为未由本节建立。本节为静态阅读，未运行反向。
