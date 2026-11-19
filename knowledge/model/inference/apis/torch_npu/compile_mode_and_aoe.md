---
type: API
title: NPU编译控制：JIT查询、模式设置与AOE图路径
description: 区分JIT布尔含义、设备默认和950查询范围，保留AOE目录行为及外部配置边界。
tags:
- task.lookup
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-is_jit_compile_false.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-is_jit_compile_false.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-is_jit_compile_false.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-set_aoe.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-set_aoe.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-set_aoe.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-set_compile_mode.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-set_compile_mode.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-set_compile_mode.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/npu_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npu_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/blacklist.md
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/blacklist.md
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/blacklist.md
  role: constraint
created_at: '2026-11-09T19:31:30Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# NPU编译控制：JIT查询、模式设置与AOE图路径

## 固定版本与证据范围

文档固定为OpPlugin发布dedc316708372c9a8bfde4527abd2a94b74840f5及主线d84e9b1d6a558e5f27973cd4329f62968e46fdda，区分发布中文与主线中英文。发布配对TorchNPU为f3ecfe4a7ef7395754da7ca2e35661a7132b519b；补充的独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf不视为与OpPlugin main已配套。

产品逐接口、参数和版本消费；主线新增950DT不回推发布、不扩到950PR。旧Atlas产品保留来源身份，不由其名字推定其他型号。以下为静态审阅，没有导入上游、加载库、操作设备、采集或性能测试，知识卡stable不代表运行verified。


## 三个入口

```text
set_compile_mode(jit_compile=False) -> None
is_jit_compile_false() -> bool
set_aoe(dump_path) -> None
```

set_compile_mode页面的`jit_compile=bool`是简写伪默认；所查两份npu_config.py实际默认False。参数True开启JIT，False关闭，发布页分别称非二进制/二进制模式。文档设备缺省策略为A2/A3训练False、旧Atlas训练/推理True，不与函数省略实参的False混为一谈。设备已初始化时setter先synchronize，再写jitCompile选项，不能把它当无同步开销的标志赋值。

is_jit_compile_false在懒初始化后查询，True表示JIT关闭；主线说明950DT默认关闭且该查询总True。但**set_compile_mode的主线产品表仍未列950**，不能由查询支持生成950开JIT配方。AOE页单独新增950DT，dump_path是算子图的输出目录，不是调优完成、收益或缓存命中的证明；目录不存在时封装尝试安全创建，类型/系统错误分别抛出。

## set_option的实际边界

同目录set_option文档仅指向外部调优指南，不自动摄取那份外链。两固定npu_config.py要求dict，会将值转str并原地写回；MM_BMM_ND_ENABLE的enable/disable还会先改变Python布局标志。已列ACL_PRECISION_MODE仅allow_fp32_to_fp16/must_keep_origin_dtype，ACL_OP_SELECT_IMPL_MODE为high_performance/high_precision，ACL_AICORE_NUM数字1..32，ACL_OP_DEBUG_LEVEL为0..4，缓存模式disable/enable/force；这些是该封装局部校验，不能当全体CANN版本、产品或所有未知键的合法表。

未登记键通过本层检查不证明底层支持。ACL_OP_SELECT_IMPL_MODE、ACL_OPTYPELIST_FOR_IMPLMODE会告警不建议配置；部分本地标志先改、随后其他键失败，函数没有整体回滚保证。图/算子编译缓存与AOE完整参数另按对应固定指南核对。

## 二进制黑名单附录的准确含义

OpPlugin发布中文及主线中英文blacklist附录以torch.npu.set_option传入NPU_FUZZY_COMPILE_BLACKLIST；一个名字示例为DynamicGRUV2，多个名字以逗号分隔，如DynamicGRUV2,DynamicRNN。名称要按实际算子路径替换；这是二进制编译选择的配置写法，不是禁用全部Kernel、不支持算子通用修复或性能保证。它与jit_compile全局模式和TorchAir捕获分别核对。

原生[LSTMCell提示与实际算子名](../../../training/guides/torch_npu_native_recurrent_constraints.md)已有冲突，不能因本附录重复示例便将DynamicGRUV2认定为已验证的LSTMCell修复。当前没有应用选项或运行上游示例。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-is_jit_compile_false.md)（constraint）
- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-is_jit_compile_false.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-is_jit_compile_false.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-set_aoe.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-set_aoe.md)（primary）
- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-set_aoe.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-set_compile_mode.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/torch_npu-npu/（beta）torch_npu-npu-set_compile_mode.md)（primary）
- [固定来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/torch_npu-npu/(beta)torch_npu-npu-set_compile_mode.md)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/npu_config.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npu_config.py)（implementation）

- [固定来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/docs/zh/custom_APIs/blacklist.md)（primary）

- [固定来源 13](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/zh/custom_APIs/blacklist.md)（constraint）

- [固定来源 14](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/docs/en/custom_APIs/blacklist.md)（constraint）
