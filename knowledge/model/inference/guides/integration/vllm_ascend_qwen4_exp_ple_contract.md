---
type: Guide
title: vLLM Ascend Qwen4Exp PLE：短卷积 prefill、状态写回与图兼容
description: 按3164核对PLE新Triton prefill的真实state stride、请求二分、token map、FP32累积和舍入，以及旧分块Conv1D fallback与ALLOW_INTERNAL_FORMAT作用域。
aliases:
- ple_conv_prefill _ple_conv_writeback_kernel
- Qwen4Exp PLE ALLOW_INTERNAL_FORMAT
- PLE short convolution prefill state stride
tags:
- task.implementation
- topic.model_adaptation
- topic.model_serving
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/models/qwen4_exp/ple.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/vllm_ascend/ops/triton_ple.py
  role: implementation
created_at: '2026-11-03T06:32:28Z'
updated_at: '2026-11-04T03:05:17Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Qwen4Exp PLE：短卷积 prefill、状态写回与图兼容

7d9e有PLE预填充说明和分块常量变化，见[7d9e运行时差异](vllm_ascend_7d9e_runtime_delta_contract.md)的PLE节；以下旧版公式与资源分析保留其源码版本，分块变小不直接构成性能收益证据。

固定 vLLM Ascend `3164adc8fe75892fbf7f99f524bb72fddf1e6efd` 新增程序，完整 AST 程序投影已读，不执行 upstream import、JIT、NPU、真实模型或性能测试。Native私有类与CANN二进制仍须按安装版本成对验证；保持draft、空平台，不将实验类名当全硬件支持。

## 新旧 prefill 入口

PLE dispatcher只有prefill调用Ascend `ple_conv_prefill`，decode/spec转Native。新kernel按token×channel2048 tile，8warps，使用query_start_loc二分定位请求，optional token_indices映射实际输入/输出；state `[slots,C,window]` 用真实三轴stride，state_len=(K-1)*dilation。NULL_BLOCK_ID不读历史并输出零卷积贡献，fresh state也不读旧值；合法state ID范围、query边界与token map由caller保证，wrapper没有遍历device索引做bounds校验。

卷积FP32累积后**先cast residual dtype再回FP32做SiLU**。FUSE_RESIDUAL先与residual按该dtype相加舍入，再与outer_residual用FP32相加后store；不能直接拿全FP32 conv+两residual参考要求位一致。conv launch先读全历史，第二writeback launch按request写最后state_len个元素；短query可将旧state尾和本轮输入拼接，空query不改state，null不写。目的state需唯一且storage寿命覆盖两个launch，不能依程序顺序解决同launch的重复slot。

代码保留current_platform.is_arch_support_pdl条件下的CUDA gdc内建；Ascend运行需平台明确返回适用值，不能把源码分支存在当NPU支持CUDA PDL。T=0、无请求、invalid映射与异步connector需要完整caller单独核对。

## 旧 Native 方法存在时的 fallback

若upstream仍有 `_short_conv_dilated_prefill_batched` 才幂等替换；新版本删除该私有方法不会因此import失败。旧路径先按请求pad输入并拼历史，再以每4请求一组做depthwise dilated Conv1D、inplace SiLU，直接gather到compact输出。分块限制的是conv中间结果，不消除全batch packed/history分配。masked invalid state在index_copy_时仍可能指向row0，需遵守caller null/唯一slot协议，不能据mask宣称完全不访问池。

`_short_conv` wrapper先等connector，然后临时关闭ALLOW_INTERNAL_FORMAT，finally恢复原值，避免PLE dilated F.conv1d落到不能capture的legacy ACLop Conv2D。选项是进程级，局部finally不提供跨线程隔离；setter缺失只warn，不能保证此环境已切到graph-safe kernel。ModelSlim的PLE embedding显式选unquantized，其余quant config走原方法。

## Agent 验收

先锁定Native方法/dispatcher版本、状态布局与NULL值、输入顺序、token map、dilation、历史flag与connector事件。逐项比较短/长请求、重复/空边界、K与C尾、fresh/stateful、null slot、spec拒绝后重算和state padding；重放检查新元数据与真实stage舍入。注释的图兼容动机不是本次capture、memcheck或性能实测。
