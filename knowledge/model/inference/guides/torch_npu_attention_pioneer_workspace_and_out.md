---
type: Guide
title: 发布AttentionPioneer：外部workspace、out复用与准备期分配
description: 核对内部Pioneer的普通/out/max-workspace/infer-output路径，区分字节与元素计数、storage基址及仍存在的执行准备成本。
tags:
- task.optimization
- topic.memory
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AttentionPioneerKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/update_op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/OpPreparation.cpp
  role: implementation
created_at: '2026-11-10T12:23:48Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 发布AttentionPioneer：外部workspace、out复用与准备期分配

## 固定内部入口与审阅范围

本卡定向审阅OpPlugin发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的内部AttentionPioneer准备/调用链，以及固定发布TorchNPU`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的workspace分配helper。主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`无同路径AttentionPioneerKernelNpuOpApi.cpp，仅记录准确tree差异，不据此否定主线其他入口。

所读范围覆盖输出分配函数、default/out/max-workspace/infer-output及包装宏，未展开前半文件全部输入布局、分页与valueD推导helper，也没有读底层AttentionPioneer kernel。本卡不定义完整支持矩阵；整卡平台未知，保持draft与空平台，未执行上游、图编译、设备或并发实验。

它与[稀疏KV量化Pioneer](optimization/torchair/torchair_ge_kv_quant_sparse_attention_lowering.md)是不同准确入口；名称相近不能互相移用HiF8、稀疏格式或返回协议。公共FIA仍按[npu_fused_infer_attention_score](../apis/torch_npu/npu_fused_infer_attention_score.md)核对。

## 四个入口做的工作不同

| 准确入口 | 本地动作 |
| --- | --- |
| _npu_attention_pioneer | 构造attention_out与softmax_lse，再用普通EXEC_NPU_NO_FORMAT_CHECK_CMD调用aclnnAttentionPioneer。 |
| _npu_attention_pioneer.out | 返回传入的两个输出引用；workspace为None时仍用普通宏，为Tensor时走外部workspace宏。所选函数没有调用输出shape构造helper来替调用方重建/resize两个输出。 |
| _npu_attention_pioneer_get_max_workspace | 先构造输出Tensor，再调用aclnnAttentionPioneerGetMaxWorkspaceSize，随后实际申请并返回workspace Tensor。 |
| _npu_attention_pioneer_infer_output | 直接调用输出构造helper并返回Tensor，不执行AttentionPioneer计算；它不是只返回shape元组的无分配查询。 |

Schema把out的attention_out/softmax_lse标为可写别名并原样返回。调用方应保持正确shape、dtype、设备、存储容量及生命周期；不能因out签名存在就宣称任意输入输出别名组合可用。预分配可以减少这里显式创建输出的路径，收益仍需连同kernel内部准备、workspace与存活缓冲测量。

## max-workspace返回的Tensor不是字节数标量

EXEC_GET_MAX_WORKSPACE_CMD取GetMaxWorkspaceSize符号，通过参数转换/大小查询得到uint64大小，释放转换参数并销毁executor，不调用实际AttentionPioneer执行入口；缺这个准确符号会报错，没有本宏的旧实现回退。

普通执行的workspace helper把该类workspace大小用于按字节分配。然而本接口拿到大小B后调用的是：

```text
apply_tensor_without_format({B}, query.options().dtype(query.dtype()))
```

因此返回的是长度B、dtype沿用query的Tensor，不是包含一个整数B的Tensor，也不是无条件UINT8[B]。若query元素占e字节，这个包装请求的Tensor数据容量为B*e；不能将workspace.numel与workspace.numel*element_size混为同一单位。比如FP16 query会按2B字节申请该Tensor；这里只说明前端分配算式，没有测量实际allocator对齐/缓存或整体峰值。

若输出构造/查询先失败，也不应仅凭get_max_workspace的名字认为已经拿到可供任意shape复用的容量。本卡来源未覆盖底层GetMaxWorkspaceSize的完整最大值域，不能把一次查询外推成任意后续batch/布局/并发的全局上界。

## 外部workspace少一处内部申请，仍然构建executor

out提供workspace时，C++传workspace.storage().data作为地址，容量传numel*element_size。这里使用Storage基址，没有使用Tensor的逻辑起始data_ptr，也没有把非零storage_offset加到地址上。不要把切片、偏移视图或任意非连续Tensor当作等价的workspace缓冲；应以明确的起始地址、连续区域、设备和足额容量建立外部分配合同。

两个外部workspace宏版本仍分别查询aclnnAttentionPioneer及GetWorkspaceSize符号，转换参数并生成executor，再调用执行入口。GetWorkspaceSize写入的是fake_workspace_size，本宏没有把它与外部传入容量比较，也没有按它自动扩容。因此“外部Tensor已提供”不是本地校验已证明容量足够。

普通执行宏会在本次workspace_size非零时调用unsafe_empty_workspace；外部版本跳过这一处内部workspace申请，但保留参数转换、GetWorkspaceSize、确定性设置及实际调用。它不是可跳过全部Host准备的已缓存executor回放，也不因名字含UPDATE就证明算子任务参数已原地更新。

宏按静态GetTaskQueueEnable结果选择V1/V2：V1先完成转换与查询，再把调用闭包交给RunOpApiV2；V2把相关转换/查询放在该闭包内。两者都只捕获外部裸地址和容量等值，不能由所选代码证明任意异步队列会自动持有调用方workspace Tensor。共享buffer的保活、流顺序与并发隔离需要另行验证，本次未展开完整队列/allocator生命周期。

## 输出推导本身也可能申请临时Tensor

infer_attention_out_shape先按query申请临时Tensor，再按layout分支申请目标shape；construct_fia_output_tensor_experimental随后又为最终attention_out申请Tensor。因此普通入口、infer_output和get_max_workspace都不是零分配的shape辅助函数；具体临时存活、allocator复用和峰值没有在本次测量，不能简单把调用次数乘输出大小当作真实常驻占用。

选定构造层要求num_heads>0，将num_key_value_heads=0用于局部推导时替换为num_heads。query为INT8时，输出dtype取query_rope.dtype（若Optional有值），否则FP16；其他query按其dtype分配。softmax_lse_flag=False仍返回定义的FP32[0]空Tensor，True则分配LSE形状Tensor。所选Meta默认入口复刻这些类型/开关分配，但不校验外部workspace的地址、容量或生命周期，也不提供运行支持认证。

实际传给ACLNN的num_key_value_heads仍是入口原值，不把局部shape推导的0替换写成所有后端参数已统一。所选代码另有query_rope或key_rope存在时要求CANN>=8.1.RC1的guard，helper对版本判断缓存；报错里的greater than不应改为严格大于该版本。没有RoPE不等于任意更低版本已经有AttentionPioneer符号。

此内部入口没有暴露公共FIA的全部量化尺度、共享前缀或调精度参数；许多对应ACLNN输入在包装中为未定义Tensor、模式固定0或pse_type=1。不能按底层长参数列表推导这些功能均可由本Schema配置。

## 复用验收按完整调用链计量

先区分推导输出、申请workspace、准备/执行out和正常分配调用，分别记录返回Tensor的numel、element_size、storage基址、offset、总容量、流和存活引用。固定同一合法输入合同，比较普通路径与预分配路径的数值、分配事件、Host准备、队列和端到端耗时；改变shape或并发复用时重新验证容量域。

本卡没有执行这些实验，也没有发布平台支持、精度或性能数字；静态证据只说明哪些前端工作可被复用、哪些仍保留，不能替代目标环境验收或新增verified。


## Evidence

- [固定实现来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/AttentionPioneerKernelNpuOpApi.cpp)（primary）：209–610。

- [固定实现来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/update_op_api_common.h)（implementation）：21–178。

- [固定实现来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（implementation）：445–509,536–584。

- [固定实现来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：5952–5966。

- [固定实现来源 5](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）：1725–1765。

- [固定实现来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）：416–422。

- [固定实现来源 7](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/OpPreparation.cpp)（implementation）：410–446。
