---
type: Guide
title: vLLM Ascend GDN310P数值验收：Golden、状态观察与覆盖缺口
description: 为310P GDN选择数值验收层，区分V310算子直调、Torch绑定和参考函数，核对Golden递推、输出与state及测试覆盖，避免将局部证据当整链路结果。
aliases:
- GDN310P数值验收
- test_recurrent_gated_delta_rule_v310
- aclnnRecurrentGatedDeltaRuleV310GetWorkspaceSize
- test_h_state_correctness
- test_v_new_correctness
tags:
- task.implementation
- topic.model_adaptation
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/310p/single_node/ops/singlecard_ops/test_recurrent_gated_delta_rule_v310.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/e2e/nightly/310p/single_node/ops/singlecard_ops/test_chunk_gated_delta_rule_fwd_h_vllm_aclnn.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/recurrent_gated_delta_rule_v310/recurrent_gated_delta_rule_310_torch_adpt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding_meta.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/fla/gdn_310.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/_310p/ops/fla/chunk_gated_delta_rule.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/_310p/ops/test_chunk_gated_delta_rule_310.py
  role: evidence
created_at: '2026-10-31T12:00:40Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-11-04T02:53:33Z'
---

# vLLM Ascend GDN310P数值验收：Golden、状态观察与覆盖缺口

## 任务与证据边界

为310P新GDN模型适配或优化选择数值验收时，先确认测的是参考函数、CANN算子、Torch绑定还是完整模型。固定Ascend ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，主来源test_recurrent_gated_delta_rule_v310.py178行；另读chunk NPU测试160、适配头53、生产/参考Python全文，并有界核对Torch binding与Meta。6份全文、2个有界范围仅作数据，7个测试函数都未执行；没有NPU结果，保持draft/空平台。

这是验收选择与覆盖分析，本Guide的分析范围不包含完整Host/Device算子。需要kernel算法、tiling、内存与分派时，继续读同ceac的[310P recurrent算子](../../operators/aclnn/transformer/attention/vllm_ascend_recurrent_gated_delta_rule_v310_310p.md)、[310P chunk H算子](../../operators/aclnn/transformer/attention/vllm_ascend_chunk_gated_delta_rule_fwd_h_310p.md)和[310P chunk O算子](../../operators/aclnn/transformer/attention/vllm_ascend_chunk_fwd_o_310p.md)。这些已有源码卡补充各自已读实现，并不证明EXEC_NPU_CMD外部运行时、实际安装ABI或硬件执行已验收。固定Native/配对版本沿[框架记录](../../concepts/frameworks/vllm_ascend.md)核对；执行前提沿[310P接入](../integration/vllm_ascend_310p_gdn_execution_contract.md)，padding场景沿[310P诊断](../../runbooks/precision/vllm_ascend_310p_gdn_padding_readiness.md)。

## 四层证据分别记录

| 层次 | 已读固定来源 | 能观察什么，以及缺什么 |
|---|---|---|
| CPU参考 | test_chunk_gated_delta_rule_310.py三个函数 | reference shape/dtype、FP32 state、TND/BTHD；norm被mock，不测生产AscendC |
| chunk h的Torch绑定 | test_chunk_gated_delta_rule_fwd_h_vllm_aclnn.py三个函数 | h/v_new局部正确性与非有限值；不测完整WY→h→o和final state |
| recurrent CANN直调 | test_recurrent_gated_delta_rule_v310.py一个参数化函数 | 输出和touched state对Golden；绕过Torch schema/Meta/Python wrapper |
| 集成与图 | C++ adapter/schema/Meta及实际模型调用者 | 目前只有静态合同，仍须在目标栈验证state副作用、capture和连续步结果 |

固定CPU参考的三个函数为test_chunk_gated_delta_rule_310_output_shape_and_dtype、test_chunk_gated_delta_rule_310_varlen_path、test_chunk_gated_delta_rule_310_varlen_tnd_path；最后一项只比较参考函数的TND/BTHD一致性。

不能将一个层次的通过写成另一个层次已经通过。参考用V12也不能放宽生产chunk的NPU/FP16/V>=128且整除128前提；recurrent的64维fixture属于另一个算子。更多通用选择方法见[测试证据指南](vllm_ascend_test_evidence_selection.md)。

## recurrent直调测了哪些输入

test_recurrent_gated_delta_rule_v310的三组(batch,mtp,Nk,Nv,Dk,Dv,slots)为(1,1,8,16,128,128,444)、(2,2,8,16,128,128,444)、(4,2,4,4,64,64,32)。它们是测试点，不是完整支持范围。

每请求qlen恒为mtp且为正，accepted恒为1，indices来自randperm前T项、互不重复。q/k在CPU归一化后转FP16；value、beta、state为FP16，g为非负随机FP32。它没有覆盖真实gating常见的负g、accepted>1、accepted0/None、PAD、ragged或重复state索引。

## Golden递推与状态观察

golden将q/k/v/beta/state转FP32，clone原state，q乘scale=Dk^-0.5。g存在则用exp(g)，不存在则用1；每请求初态选indices[seq_start+accepted_i-1]，accepted缺省时取首token索引。

按value head映射到q/k head：head//(Nv//Nk)。每token先令S乘衰减，再算prediction=sum(S×k)、delta=(v-prediction)×beta，更新S+=delta外积k；将S写到indices[t]，输出sum(S×q)。这些顺序和state的[V,K]布局必须与调用者一致，不能只比最后输出shape。

fixture的assert_close比较out，以及state_npu[touched]与Golden对应行；rtol=3e-3、atol=2e-3、equal_nan=True。它没有检查未选pool行保持不变，也没有独立拒绝NaN/Inf；相同位置的NaN可被equal_nan放过。后续真实验收应分别保存输出、所有选中state和未选哨兵行，并单列finite检查。

## ctypes入口不等于Torch入口

测试文件导入阶段会设置NPU编译模式并ctypes.CDLL加载库；知识阅读不能通过导入该模块完成。源码按ASCEND_HOME_PATH或默认toolkit根，在custom_transformer vendor、lib64和aarch64/lib64找libnnopbase/libcust_opapi；本次没有解析或加载实际库。

mk按shape/stride、offset0、format2、data_ptr构造aclTensor，dtype map仅含FP16/FP32/int32，None传null。fixture并没有证明任意view的storage范围可用；aclDestroyTensor虽声明，创建句柄的清理未在这段测试实现中出现。

call_v310先调用aclnnRecurrentGatedDeltaRuleV310GetWorkspaceSize，检查返回0，按需在query device分配uint8 workspace；再用当前NPU stream执行aclnnRecurrentGatedDeltaRuleV310、检查0并synchronize。workspace存活到本次同步后，不是一般异步、多stream或多device生命周期证明。

这条直调绕过Python的norm、dtype转换、padding索引处理和Torch注册。若以后直调与Torch结果不同，先分别核输入变换、参数顺序、schema和输出/state归属，不能直接归因为kernel或性能退化。

## chunk h的Golden与局限

test_h_state_correctness和test_v_new_correctness仅覆盖B1、Hg=Hv=1或2、T128、K/V128。k/w/u与初态为缩小幅度的FP16，g为负FP32；w/u由fixture直接构造，不来自完整生产WY准备。

cpu_reference在FP32计算v_new=u-W@h，再按exp(g_last-g_i)累加K与修正value，按exp(g_last)推进历史state。它保存初态及每chunk后的NT+1份参考快照。

C++ chunk_gated_delta_rule_fwd_h_vllm分配h_out[B,HV,NT,K,V]，NT来自chunk indices对数或ceil(T/chunk64)。test_h_state_correctness以min(NT+1,h_out实际chunk轴)比较，且索引固定batch0；不能据此声称NT+1历史和最终state都已比较。wrapper设置output_final_state=False，测试也没有检验返回final state。

两项correctness将每段flatten为double后要求cosine>=0.99；两路norm都为0时自定义返回1，一路为0返回0。cosine对整体缩放不敏感，应另核幅值、绝对/相对误差及近零向量。test_no_nan单独检查h/v_new无NaN和Inf，但仍不覆盖最终state或输出o。

## Torch schema、真实输出和Meta分开核对

53行adapter以mutable Tensor引用接state，按value shape/options分配输出，将double scale转float，再经EXEC_NPU_CMD调用CANN。它本身不验证所有dtype、padding或stride，macro与CANN完整行为未在此闭合。

固定310P schema写的是Tensor state，没有Tensor(a!) state这样的写入标记；C++ mutable参数与E2E state断言表达了state推进预期。这是需要在实际compiler/graph中复核的静态边界，不是本次复现的图错误，也不提供跨版本的强制修法。

npu_recurrent_gated_delta_rule_310_meta只按value.sym_sizes和options返回empty_symint，不做数值和state推进。chunk_gated_delta_rule_fwd_h_vllm_meta镜像B/HV/NT/K/V及final-state options；chunk indices是IntArrayRef，长度参与NT计算，不是从Tensor数据求动态shape。

实际h/v_new wrapper分配zeros，Meta仅给empty shape；final state options优先沿initial_state，缺省沿h。output_final_state=False时C++返回未定义Tensor，不应仅凭声明推断普通Python返回值和所有下游均已验证。

Meta存在不能代替实际state副作用、alias、符号shape和capture/replay验证。通用接入要求见[ACLNN指南](../integration/vllm_ascend_custom_aclnn_binding.md)，已有图lowering经验仍按其后端和版本使用。

## 为目标模型补齐验收矩阵

先在实际允许的shape/dtype范围内补输入：多batch/GVA、真实负g与长衰减、fresh/history、varlen/空段、合法accepted变化、PAD/NULL、strided state、连续两步和未选行。参考和真实算子分开记录，非法输入的拒绝也按各自guard判断，不通过删除guard扩支持。

从CANN直调到Torch wrapper，再到完整prefill/recurrent、eager/graph与模型checkpoint逐层比较；每层检查输出值、state前后、finite、误差分布、实际进入的算子以及同步/所有者。记录失败发生在哪一层，恢复匹配权重与完整state后重测，避免单独清cache隐藏跨步差异。

最终交付保存硬件/软件与commit、参数矩阵、随机seed、测试入口、Golden来源、输出/state/未选行断言、finite与误差、执行结果和剩余缺口。没有真实运行就标未执行；数值与状态通过后才进入[性能基准](../optimization/vllm_ascend_benchmark_workflow.md)和端到端模型质量验收。本卡没有吞吐、时延或Agent A/B结论。
