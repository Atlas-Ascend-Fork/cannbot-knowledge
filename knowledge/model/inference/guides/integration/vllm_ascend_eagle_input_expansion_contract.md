---
type: Guide
title: vLLM Ascend EAGLE输入展开：接受边界、shift映射与固定缓冲容量
description: 沿MRv1调用、Torch包装、Host推形和CopyAndExpandEagleInputsKernel核对bonus与并行草稿槽、rejected/masked两种mask、shift隐状态映射和单核固定UB容量，定位形状可推而数据范围不匹配的适配问题。
aliases:
- npu_copy_and_expand_eagle_inputs
- CopyAndExpandEagleInputsKernel.ProcessOneRequestShiftTrue
- CopyAndExpandEagleInputsKernel.ProcessOneRequestShiftFalse
- InferShape4CopyAndExpandEagleInputs
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.speculative_decoding
- topic.data_movement
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/copy_and_expand_eagle_inputs/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/copy_and_expand_eagle_inputs/op_host/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/copy_and_expand_eagle_inputs/op_host/copy_and_expand_eagle_inputs_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/copy_and_expand_eagle_inputs/op_host/copy_and_expand_eagle_inputs_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/copy_and_expand_eagle_inputs/op_host/copy_and_expand_eagle_inputs_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/copy_and_expand_eagle_inputs/op_host/copy_and_expand_eagle_inputs_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/copy_and_expand_eagle_inputs/op_kernel/copy_and_expand_eagle_inputs.cpp
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding_meta.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/v1/spec_decode/llm_base_proposer.py
  role: constraint
created_at: '2026-11-03T05:59:11Z'
updated_at: '2026-11-03T05:59:11Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend EAGLE输入展开：接受边界、shift映射与固定缓冲容量

## 调用链和证据边界

固定Main ceac1a2，完整技术代码阅读此算子7份构建/Host/Device来源，另读Torch包装855–887及3203–3211注册、Meta651–678及1833注册、MRv1 proposer1800–1898调用片段。共享来源原owner保留。本文聚合草稿输入展开，不替代[DSpark块布局](vllm_ascend_dspark_block_markov_contract.md)或[草稿权重basis对齐](vllm_ascend_draft_quarot_alignment.md)，也不由算子名推断所有EAGLE/MTP/MRv2均调用它。

MRv1调用以query_start_loc[1:]-1为query_end_loc，再减各请求拒绝数，传入bonus next_token_ids；调用方按其net_num_new_slots_per_request算输出长度，并按pass_hidden_states_to_model选择shift。返回后拷入预分配图缓冲；仅shift为真时用hidden-state mapping将target hidden散射回填，并用masked mask选择parallel drafting hidden。所读片段没有闭合Native基类如何定义extra/net槽数，因此接入新草稿必须验证这一恒等式，不能仅复用同名字段。

## 包装层、推形和实际数据是三种保证

五个输入OpDef均为ND/INT32，六个输出中token/position/new indices/hidden mapping为INT32，两个mask为INT8；源码配置仅ascend910b和ascend910_93。Torch包装未在本函数加入完整rank/dtype/contiguous/长度校验，实际调用必须满足OpDef与Device合同；空平台状态保留，没有硬件实测。

| 量 | 实际来源与含义 |
| --- | --- |
| T | target_token_ids.size(0)，真实target输入槽总数 |
| R | query_start_loc.size(0)-1，请求数 |
| P | num_padding_slots_per_request，包含bonus槽及额外并行草稿槽 |
| D | 推形公式T+(P-shift)*R；实际Torch输出按显式total_draft_tokens分配 |
| 新token索引 | R*P长，每请求指向bonus和其后P-1并行草稿槽 |
| 隐状态映射 | T长，只有shift路径实际写入；普通路径不计算映射 |

Torch真实包装用zeros分配六个输出，将T而非D作为ACLNN算子的total_input_tokens属性。Meta却按target输入options创建empty，整数输出可继承输入dtype；Meta通过不证明真实OpDef的INT32合同，也不意味着零初始化或mask/映射数据有效。Host推形按P/shift推D，tiling则读取已有输出shape定D；caller传入的显式D须与上述公式及请求边界一致。

InferShape用int64_t读取Int槽属性，tiling使用int32_t指针读取多个Int属性并窄化为uint32字段。生成API的真实属性表示、负值和大值范围要核对，不能从C++输入int64_t推断任意64位数量均安全。所读Host并没有完整检查各query边界、T/R/P/D关系、正值域和动态未知shape。

## 两种shift布局的精确差别

令某请求start=s、next start=n、query_end=e，拒绝数为max(n-e-1,0)。这使e按当前调用方表示最后一枚有效token，而不是独立于上游语义的任意exclusive end。

| 项 | shift=False | shift=True |
| --- | --- | --- |
| 有效复制数量V | max(e-s+1,0) | max(e-s,0) |
| 输入起点 | s | s+1 |
| 输出起点 | s+r*P | s+r*(P-1) |
| 请求输出长度 | V+P+rejected | V+P+rejected |
| hidden-state mapping | 不写，真实包装留下零 | 对原请求n-s个输入槽，写outputStart+j |

每行先复制V个token，positions从target_positions[s]起逐个+1，并非复制整段原positions。然后放一枚next token作为bonus，随后P-1枚parallel_drafting_token_id；这些新草稿位置的masked mask为1，bonus和有效token为0。最后的拒绝槽放padding_token_id、position0、rejected mask1而masked0。两种mask用途不同，不能用masked代替拒绝屏蔽，或把padding token值单独作为有效性判断。

shift路径在n==e且还有后继请求时少写最后一个槽，避免覆盖后继段；最后一个请求还会把实际写尾与D之间的差额清零。shift为真时输入读取按T裁剪，裁剪后不足的复制位置重复最后一个已读token，若没有可读token填0；这不是自动修复错误query边界。shift=False只对局部读索引夹到请求最后一个token，空请求仍可能产生-1读取，不能将max(…,0)当作完整空请求支持。

## 单核执行与固定UB是适配门禁

Host虽然查询core数，usedCoreNum固定1、key固定1、全部请求在一核顺序处理。不能用硬件核数或kernel类支持多core分配的代码推断本版本已并行分摊。Device入口忽略workspace，构建使用cce-auto-sync=on，copy helper另在搬运前后加PIPE_ALL；未提供事件重叠或带宽收益实测。

每请求input、output IDs/positions、hidden mapping按4096元素固定分配，两个INT8 mask也按4096，new-token indices按64个INT32；全部请求的start/end/next token元数据另外按R分配。Host未见P≤64、请求输入/输出/tail≤4096或总体UB容量校验。Agent应先证明这些界限和同时存活的元数据量，再考虑放大draft宽度、长prefill或请求数，不能把常量误解成全模型合法上限。

输入DataCopy按8个INT32即32B向上取整，连仅取target_positions[s]一项也会读整块；目标UB有对齐空间不证明GM尾部额外元素可读。caller需证明存储padding/读取范围或另作合法tail搬运。输出用DataCopyPad按实际字节数写回，但局部填充循环没有自动裁到固定UB大小；输出GM的D也不会限制本地循环。

R=0时正常应使D=0并由调用方正确处理；shift路径若R=0而D>0，尾部逻辑仍取myNumReqs-1，不能声称任意空输入都安全。负P或负数量进入uint32字段也不是合法fallback。对图复用应同时保存T/R/P/shift、边界数组、D、实际buffer容量、mask及mapping消费条件；只比较token输出shape会漏掉隐状态或拒绝槽错位。

## 后续验证应围绕消费者建立

优先使用两请求、接受数不同的坐标编码输入验证四类槽及position；分别覆盖shift真假、P=1/多槽、部分/全拒绝、相邻边界和最后尾部。随后核对hidden mapping只在shift为真消费，图预分配buffer容量与D一致，以及大R/4096/64边界和GM末块读取。这里仅给源码支持的核对顺序，本次没有执行这些测试、上游代码、NPU、图或模型；生成ACLNN接口、外部DMA语义和数值/性能仍未构成完整Operator闭包。
