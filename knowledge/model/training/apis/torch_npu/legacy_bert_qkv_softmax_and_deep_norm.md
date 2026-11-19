---
type: API
title: Bert旧训练入口组：QKV-LN前向、相对位置掩码softmax、注意力softmax与DeepNorm
description: 记录四个无文档页的Bert/Megatron时代训练注册入口的host检查、输出合同、反向链路、Meta差异与主线与发布两版本版本边界（含qkv前导检查的&&与||语义差异）。并含npu_fused_attention_qkv_grad 双 ACE 命令反向。
tags:
- task.lookup
- topic.attention
- topic.compute.normalization
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/FusedAttentionLnQKV.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/DeepNormKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/DeepNormBackwardKernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DeepNormKernelOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DeepNormBackwardKernelOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/AttnSoftMaxBackwardKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_v1r11_ops/test_fused_attention_ln_qkv.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_masked_softmax_with_rel_pos_bias.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_attn_softmax.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_deep_norm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_deep_norm_backward.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/core_tests/test_fake_tensor.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/FusedAttentionLnQKV.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/DeepNormKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/DeepNormBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DeepNormKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DeepNormBackwardKernelOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AttnSoftMaxBackwardKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/derivatives.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_v1r11_ops/test_fused_attention_ln_qkv.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_masked_softmax_with_rel_pos_bias.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_attn_softmax.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_deep_norm.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_deep_norm_backward.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/core_tests/test_fake_tensor.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/FusedAttentionQKVGradKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/FusedAttentionQKVGradKernelNpu.cpp
  role: implementation
created_at: '2026-11-12T07:02:00Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Bert旧训练入口组：QKV-LN前向、相对位置掩码softmax、注意力softmax与DeepNorm

## 版本与范围

本卡覆盖 OpPlugin 两固定 pin（主线 d84e9b1d6a558e5f27973cd4329f62968e46fdda、发布 dedc316708372c9a8bfde4527abd2a94b74840f5）中四个无官方文档页的 torch_npu 注册入口：`npu_fused_attention_layernorm_qkv_fwd`、`npu_masked_softmax_with_rel_pos_bias`、`npu_attn_softmax_`/`npu_attn_softmax_backward_`、`npu_deep_norm`/`npu_deep_norm_backward`。主线与发布两版本 的 docs/zh 与 docs/en 全树检索均无这些入口的页面（负向核实）；六个 schema 的 yaml 登记原文在主线与发布两版本 逐字相同，均无 exposed 标注，但官方用例均直接以 `torch_npu.*` 形式调用（绑定生成机制未审阅）。相邻层已有的覆盖只链接不重复：contrib 模块层与 qkv_grad 反向链见 [contrib_bert_fused_attention](contrib_bert_fused_attention.md)，masked_softmax 的 torchair 图消费见 [GE 自定义激活 lowering 卡](../../../inference/guides/optimization/torchair/torchair_ge_custom_activation_lowering.md)，aclnnDeepNorm(Grad) 与 aclnnMaskedSoftmaxWithRelPosBias 的设备层见文末链接。全部为静态源码与官方用例审阅，未执行任何上游或设备测试；本卡不归属任何模型，不承诺整模型训练收益。

## npu_fused_attention_layernorm_qkv_fwd：Bert withLN 前向底层

```text
npu_fused_attention_layernorm_qkv_fwd(x, kernel_query, kernel_key, kernel_value, gamma, beta,
    bias_query=None, bias_key=None, bias_value=None, seq_len=128, num_heads=12, eps=1e-05) -> Tensor[]
```

仅 `acl_op: all_version` 注册（无 op_api 路径），实现为 aclops 旧 ACE OpCommand（FusedAttentionLnQKV.cpp 全 72 行已读）。

- 实际门槛（C++ host 实检 28–36 行）：① `seq_len != 0 && num_heads != 0`（主线；发布为 `||`，见「版本边界」），VALUE 错误；② `x.dim() >= 2`，PARAM 错误；③ `x.size(0) % seq_len == 0 && x.size(1) % num_heads == 0`，PARAM 错误，错误文案同时点名两个整除要求。
- 动作：三个可选 bias 缺省时经 `value_or_else` 变为未定义 Tensor 原样下发；六输出按序 `(norm, query_output, key_output, value_output, mean, variance)`：norm 与 x 同形；q/k/v 以 kernel_query/key/value 的 options 按 `(x.size(0)/seq_len, num_heads, seq_len, x.size(1)/num_heads)` 分配；mean/variance 以 kernel_query 的 options 按一维 `[x.size(0)]`、ND 格式分配；attr epsilon 由 double 下转 float 后以单次 OpCommand `AttentionLnQKV` 下发九输入六输出。
- 官方用例（test_v1r11_ops，Bert-large 口径）：x=(12288,1024) half、三权重 (1024,1024) half 转置+连续+格式29，seq_len=512、num_heads=16，输出 q/k/v 形状 (24,16,512,64)；golden 为 `native_layer_norm` + `F.linear` + `npu_confusion_transpose((0,2,1,3), (24,512,16,64), False).npu_format_cast(29)`，q/k/v 断言容差 prec16=0.003，norm/mean/variance 默认容差。
- 静态不一致（未运行裁定）：第六输出源码命名 variance，golden 却取 `native_layer_norm` 的 rstd（1/std，非方差）；mean/variance 分配为一维 `[x.size(0)]` 而 golden 的 mean/rstd 形状为 `(M,1)`。本卡按用例对照口径记录，不裁定设备侧真实语义与断言判定结果。
- 失败/消费边界：host 只做上述三道检查，bias/权重形状与 dtype 不在 host 拦截；该 schema 是 contrib withLN 变体反向链中 qkv_grad 的前向对应底层，模块层合同、一次校验与 keep_prob 默认见 contrib 卡，本卡不重复。

## npu_masked_softmax_with_rel_pos_bias：相对位置偏置掩码 softmax

```text
npu_masked_softmax_with_rel_pos_bias(x, atten_mask?, relative_pos_bias, scale_value=1.0, inner_precision_mode=0) -> Tensor
```

`op_api: all_version` + gen_opapi 注册；无手写 host cpp。

- 注册层合同：gen_opapi 声明 out 的 `size: x`、`dtype: x`，exec 按 schema 参数序把 `(x, atten_mask, relative_pos_bias, scale_value, inner_precision_mode)` 透传给 `aclnnMaskedSoftmaxWithRelPosBias`；host 包装由 codegen 按该声明生成（生成器模板与生成代码未审阅），Meta 仅 `empty_like(x)`。已读的 yaml 输出/exec 声明与该 Meta 函数均不含显式额外校验；codegen 生成的 host 包装与框架/schema/SDK 层行为未完整审阅，不据此断言所有 host/Meta 路径都不会拒绝非法输入。
- 官方用例（Ascend910B）：五维 x=(1,2,3,4,4)、relative_pos_bias=(1,1,3,4,4)、atten_mask=(1,2,1,4,4)，golden 为 `softmax(x+atten_mask+relative_pos_bias, dim=-1)`；mask/bias 对 x 的广播按 golden 隐含发生在 aclnn 内，源码声明不是任意 mask 广播或相对位置布局的支持矩阵。FakeTensor 用例（(96,2,2,32,32) 系五维）在 requires_grad 输入下仅断言 `res.shape == x.shape`——合法输入的形状断言，不证明 Meta 或生成 host 无检查。
- 失败/边界：`scale_value`、`inner_precision_mode` 未被任何用例覆盖，取值语义未在知识库登记；torchair 图消费口径（默认 scale=1.0、precision_mode=0，可选 mask 原样透传）见 GE 卡，设备层接口语义见文末 ops/ascendc 链接。

## npu_attn_softmax_ 与 npu_attn_softmax_backward_：注意力 softmax 原地对

```text
npu_attn_softmax_(Tensor(a!) self) -> Tensor(a!)
npu_attn_softmax_backward_(Tensor(a!) self, Tensor grad_output, Tensor values) -> Tensor(a!)
```

前向：`op_api: all_version` + gen_opapi 注入 `dim=(int64_t)-1`，exec `aclnnSoftmax(self, dim, self)`——self 同时是输入与输出，原地覆盖为末维 softmax 结果，无手写 host cpp。

反向：`op_api: all_version`，手写 opapi C++（AttnSoftMaxBackwardKernelNpuOpApi.cpp 全 36 行已读）。

- 实际门槛：wrapper 本地无显式 TORCH_CHECK；但 aclnn 调用前有 values 转置、`op_infer::matmul_output_size` 形状推导与无格式输出分配，形状/布局错误可能在 helper/框架层先于 aclnn 失败，并非全部推迟到 SDK。
- 动作（两次 aclnn 组合，非融合反向内核）：① `cube_math_type = get_cube_math_type_with_passthrough()`（源注释 "allow dicrease precision"，源内拼写如此）；② values 转置 `(-2,-1)` 后与 grad_output 做 `aclnnMatmul`，输出形状经 `op_infer::matmul_output_size` 推导、无格式分配；③ 以 matmul 结果为 grad、self 为 softmax 输出调 `aclnnSoftmaxBackward(matmul_result, self, dim=-1, self)`，原地写回并返回 self。
- 调用合同（官方用例）：先 `npu_attn_softmax_(logits)` 原地得到 softmax 输出，再 `npu_attn_softmax_backward_(该缓冲, grad_output, values)` 原地覆写为对 logits 的梯度；golden 用 softmax→matmul→`output.backward(grad_output)` 链对照，B=10、q_s=kv_s=4096、H=128。self 先后被两个入口原地覆写，保留中间值需自行克隆。
- 失败/边界：backward 不在 derivatives.yaml（`npu_scaled_masked_softmax` 是另一入口的接线），意味着 backward 须由调用方显式调用/手动衔接——这只是缺 derivatives 接线的静态事实，不证明该入口永不参与 autograd 图或不支持高阶导；aclnnSoftmax/aclnnMatmul/aclnnSoftmaxBackward 为公共 aclnn，知识库不重复登记其设备语义。

## npu_deep_norm 与 npu_deep_norm_backward：DeepNorm 残差+LN 融合

```text
npu_deep_norm(x, gx, beta, gamma, alpha=0.3, epsilon=1e-06) -> (mean, rstd, y)
npu_deep_norm_backward(dy, x, gx, gamma, mean, rstd, alpha=0.3) -> (dx, dgx, dbeta, dgamma)
```

两 schema 均 `acl_op`+`op_api` 双注册：opapi 实现先过 `DO_COMPATIBILITY(aclnnDeepNorm(Grad), acl_op 回落表达式)`——该宏在 aclnn 函数或其 GetWorkspaceSize 符号任一缺失时触发，aclnn-only 模式（设备仅支持 aclnn）下直接抛 NOT_SUPPORT 错误，不回落；仅非 aclnn-only 模式才回落到 aclops 的 ACE OpCommand `DeepNorm`/`DeepNormGrad`（两个回落与主路径的输出合同同构）。

- 语义（官方用例 golden）：`new_x = alpha*x + gx`；mean 在最后 gamma.rank 个尾轴上求（golden 归约区间 `range(x.rank−gamma.rank, x.rank)`——x.rank−gamma.rank 是归约起始轴序，即保留的前 `param_dim` 维个数，不是尾轴个数）、`rstd = 1/sqrt(var+epsilon)`；`y = (new_x−mean)*rstd*gamma + beta`。
- 输出合同（C++ host 实检，两实现同构）：y 与 x 同形同 dtype；mean/rstd 强制 FP32，形状为 x 的前 `param_dim` 维保留、尾维压 1（用例 x=(2,3)、gamma=(3,) 时为 (2,1)）；反向 dx/dgx 同 x/gx 形，dbeta/dgamma 按 gamma 尺寸强制 FP32 分配。反向不接收 epsilon，统计量必须来自前向保存的 mean/rstd。
- 自动微分接线（derivatives.yaml，主线与发布两版本 逐字相同）：`output_differentiability: [false, false, true]`——仅 y 可微，mean/rstd 不可微；公式 `x, gx, beta, gamma: npu_deep_norm_backward(grad, x, gx, gamma, result0, result1, alpha)`，result0/result1 即前向保存的 mean/rstd；version [v2.1, newest]。官方 backward 用例经 requires_grad + `y.backward(dy)` 走通整条接线并核对四梯度（静态读码结论）。
- Meta 与 C++ 差异：fwd Meta 与 C++ 同构（mean/rstd FP32 广播形、y 同形）；backward Meta 返回 `empty_like(x/gx/gamma/gamma)`，dbeta/dgamma 复用 gamma 的 dtype，而 C++ host 强制 FP32 分配——gamma 非 FP32 时两者口径不同，不能据 Meta 推断真实梯度 dtype。FakeTensor 用例断言 mean/rstd 形状 (2,1)。
- golden 反向链要点：`pd_x = alpha * pd_gx`（alpha 项在链式中保留）、pd_beta 仅由 dy 求和、pd_gamma 按 `(new_x−mean)*rstd` 加权求和；与 ops/ascendc 的 [OL-411 runbook](../../../../ops/ascendc/runbooks/precision/ol_411_ops_whose_inputs_are_forward_pass_derived_statis.md) 以 deep_norm_grad 为锚记录的“mean/rstd 必须来自前向真实统计”口径一致。

## 版本边界（主线与发布两版本）

- 六个 schema 的 yaml 登记原文（含默认值、acl_op/op_api/gen_opapi 声明与 exec 参数序）在主线与发布两版本 逐字相同；derivatives 接线与三个 Meta 函数亦逐字相同（逐区域 raw 对比）。
- 唯一语义差异在 FusedAttentionLnQKV.cpp 首道检查：主线 `seq_len != 0 && num_heads != 0`，发布 `seq_len != 0 || num_heads != 0`。发布仅在两者同时为 0 时拒绝；恰一个为 0 时会通过首道检查并进入下一道整除检查（对 0 取模），失败形态未运行确认；主线任一为 0 即报 VALUE 错误。跨版本脚本不要依赖任一边界。
- 其余实现文件主线与发布两版本 为格式差异（缩进重排/空行），注释与空白归一后 token 流逐字相等；官方用例除行尾空白外相同，其中 test_npu_attn_softmax.py 与 test_fused_attention_ln_qkv.py 主线与发布两版本 完全相同；主线 FakeTensor 的 deep_norm 用例比发布多一条 `result_mean.shape` 断言。差异均不影响主线与发布两版本 的行为结论，唯 qkv 首道检查除外。

## 失效边界

- 全部为静态阅读：本卡所有结论来自两固定 pin 的源码与官方用例文本；官方用例（SupportedDevices 标注 Ascend910B 或无标注）未运行，SupportedDevices 不构成本卡验证；无任何设备/CI 执行记录。
- gen_opapi 两个入口（masked_softmax、attn_softmax_ 前向）的 host 包装由 codegen 生成，本卡只按 yaml 声明记录 out/exec 合同，未审阅 codegen 模板与生成代码。
- AttentionLnQKV/DeepNorm/DeepNormGrad 三个 ACE 算子与 aclnnSoftmax/aclnnMatmul/aclnnSoftmaxBackward 的设备侧语义不在本卡；aclnnDeepNorm(Grad) 与 aclnnMaskedSoftmaxWithRelPosBias 的 A2/A3 设备层见 [deep_norm](../../../../ops/ascendc/operators/aclnn/nn/norm/deep_norm.md)、[deep_norm_grad](../../../../ops/ascendc/operators/aclnn/nn/norm/deep_norm_grad.md)、[masked_softmax_with_rel_pos_bias](../../../../ops/ascendc/operators/aclnn/nn/norm/masked_softmax_with_rel_pos_bias.md)。
- qkv 用例 golden 的 variance/rstd 命名与一维/(M,1) 形状不一致未运行裁定；发布 qkv 取模失败形态未运行确认。
- torch_npu Python 绑定生成机制未审阅，无 exposed 标注与 `torch_npu.*` 可调用性之间的关系不裁定。

## npu_fused_attention_qkv_grad 双命令反向

前向 `FusedAttentionLnQKV.cpp` 已在本卡核对；本节补其反向 `FusedAttentionQKVGradKernelNpu.cpp`（83 行，主线与发布两版本 去空白等价）。`npu_fused_attention_qkv_grad(grad_output_query/key/value, query/key/value_kernel, hidden_states, grad_output_ln)` 返回 7 个梯度，两条 ACE 命令：`AttentionQKVGradX`（输入 grad_output_ln + 三个 grad_output + 三个 kernel，输出 grad_hidden_states，`trans_a=false`/`trans_b=true`）与 `AttentionQKVGradW`（输入 hidden_states + 三个 grad_output，输出三个 grad_w_* 与三个 grad_b_*）。分配合同：grad_hidden_states 以 `ACL_FORMAT_FRACTAL_NZ` 请求（`apply_tensor_with_format(hidden_states, ACL_FORMAT_FRACTAL_NZ)`），grad_w_* 按 kernel 同形，grad_b_* 按 `{kernel.size(0)}` 且 ND。query/key/value_kernel 各自 dim≥1 的 TORCH_CHECK。消费面：torch_npu 主线与发布两版本 `contrib/function/fused_attention.py`。设备侧两命令数值语义与 NZ 布局代价未测。

证据：

- [FusedAttentionQKVGradKernelNpu.cpp 主线与发布两版本](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/FusedAttentionQKVGradKernelNpu.cpp)（implementation）：全文 83 行；发布去空白等价。
