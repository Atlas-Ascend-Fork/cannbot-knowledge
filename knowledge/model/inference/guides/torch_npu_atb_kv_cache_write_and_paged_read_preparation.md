---
type: Guide
title: ATB KV Cache写读：槽位、NZ配置、长度与输出
description: 聚合双Cache/SISO写入与分页读取，区分两套格式模式数字、长度校验和out路线，并保存完整测试中的参考与别名边界。
tags:
- task.optimization
- topic.memory
- topic.data_movement
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/ReshapeAndCachAtb.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/ReshapeAndCacheSisoAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/PagedCacheLoadAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/infer_op_params.h
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_api_docs.py
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_reshape_and_cache.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_reshape_and_cache_siso.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_paged_cache_load.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/ReshapeAndCachAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/ReshapeAndCacheSisoAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/PagedCacheLoadAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/infer_op_params.h
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_api_docs.py
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_reshape_and_cache.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_reshape_and_cache_siso.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_paged_cache_load.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_ops.py
  role: implementation
created_at: '2026-11-11T04:11:18Z'
updated_at: '2026-11-14T01:59:28Z'
platforms: []
---

# ATB KV Cache写读：槽位、NZ配置、长度与输出

固定OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`和发布`dedc316708372c9a8bfde4527abd2a94b74840f5`。所列CPP逐对完整非注释token一致，完整测试AST亦相同；均是静态审阅，没有导入/运行上游、加载ATB库或执行设备、编译、捕获、数值和性能验收。整卡产品与完整配套未确认，保持draft、空平台，无新增verified。

[ATB执行生命周期](torch_npu_atb_paged_attention_execution_lifecycle.md)解释ParamSetter的contiguous、按请求转换ND、CPU clone、直接输出描述符和每次Setup/工作区/捕获分派。format_trans请求不能直接计为一次物理复制，Input准备也不代替调用方Output对象的连续性与别名合同。

## 写入Cache：双Cache和SISO使用不同配置

`atb::_npu_reshape_and_cache`在PrivateUse1注册，key/value为输入，key_cache(a!)/value_cache(b!)为可写输入，slot_indices为索引，返回()。入口guard key设备，ReshapeAndCacheParam.compressType固定UNDEFINED(0)；仅当K与V Cache的实际NPU格式都为FRACTAL_NZ时选K_CACHE_V_CACHE_NZ(2)，否则选K_CACHE_V_CACHE(0)。一边NZ一边非NZ也落后者，本地没有混合格式拒绝或把两份Cache显式转ND的分支，实际组合仍由ATB合同决定。

其槽位顺序为key(True)、value(True)、key_cache(默认False)、value_cache(默认False)、slot_indices(True)，两个Output依次为同一key_cache/value_cache。读取格式选择参数不等于重排Cache；Input缓存的默认标志也不能按key/value的True复制。

`atb::_npu_reshape_and_cache_siso`同样guard key设备，固定compressType=0、kvCacheCfg=K_CACHE_V_BYPASS(1)；输入依次key(True)、key_cache(True)、slot_indices(True)，输出原key_cache，schema为Tensor(a!)且返回()。它没有按key_cache实际格式选择NZ模式的本地分支。

两版固定参数头声明compressType非0仅支持Atlas 800I A2推理产品，K_CACHE_V_BYPASS(1)也有相同局部产品条件；本卡入口不启用压缩，SISO实际启用bypass。整卡平台仍不由局部字段条件自动补全。两入口共用ReshapeCacheOperation，专用hash写compressType/kvCacheCfg，随后RunAtbCmd；本次key/value/slot内容仍经VariantPack提交。

## 分页读取的输出分配与长度模式

`atb::npu_paged_cache_load`和`.out`均注册PrivateUse1；Python ATB_API_LIST绑定torch_npu.atb。普通重载按context_lens计算int32 num_tokens，再分别申请[num_tokens,key_cache.size(2),key_cache.size(3)]和[num_tokens,value_cache.size(2),value_cache.size(3)]，options各取对应Cache。不是把value尾维一律取key尾维，也没有在本地显式申请NZ输出。

| cumsum | 普通重载的本地计数 |
| --- | --- |
| False（schema默认） | 对每项执行.item<int32_t>()，检查非负、累加前num_tokens≤INT32_MAX−该值，再累加。循环变量为int，未在这里补全所有rank/numel范围检查。 |
| True | 非空取context_lens[-1].item<int32_t>()，空取0；这个分支没有同样的逐项负值/单调性/首项0检查。 |

这些读取发生在创建局部OptionalDeviceGuard之前，不能漏记成只有底层搬运成本。.out重载直接接收key(a!)/value(b!)并返回两引用，没有前述num_tokens求和/输出分配/负数与累加溢出检查；不能把普通重载的校验套给out重载。两者仍需要实际长度模式、batch与块表/Cache容量一致。

两重载只检查key_cache实际格式来生成动态接口的int8 kv_cache_cfg：FRACTAL_NZ→0，其它→1；这不是上节ReshapeAndCacheParam的ND0/NZ2枚举。value_cache格式没有在这里独立判定，不能由key的模式自动证明两者布局兼容。

has_seq_starts仅在Optional有值且Tensor defined时为True，seq_starts对象本身仍作为宏实参提交。调用顺序为key_cache、value_cache、block_table、context_lens、key、value、seq_starts、kv_cache_cfg、cumsum、has_seq_starts，guard取key_cache设备，随后EXEC_ATB_CMD(AtbPagedCacheLoad)。动态转换、每次workspace/hash与捕获路线复用[动态ATB调用准备](torch_npu_atb_mla_preprocess_and_ring_preparation.md)，不套用ParamSetter的格式标志或CPU clone规则。

## 固定读取文档与形状辨析

所选两版文档除空白一致，描述将分页Cache按block_table/context_lens搬运、拼接成连续K/V；chunked prefill/prefix cache的Ring MLA消费者先读Cache、乘升维矩阵再调用Ring，不从该流程推导所有模型使用相同变换。

文档列K/V Cache为ND FP16/BF16/INT8的[numBlocks,blockSize,numHeads,headSizeK/V]，各numHeads×headSize需32B对齐；块表为INT32 ND [batch,blockIndices]，context_lens为INT32 ND [batch]或[batch+1]的长度/累加和，seq_starts为可选INT32 ND [batch]起始位置。输出文档的value shape误写headSizeK，而本地分配取value_cache.size(3)；样例亦用K尾维512、V尾维64，不能把误写扩成两尾维必须相等。

固定文档只列ND，但局部包装另有FRACTAL_NZ模式映射；这两种证据范围分别保留，不能由内部模式数字宣布所有NZ/dtype组合已获文档或运行确认。seq_starts的准确单位和非对齐偏移效果按所配动态操作合同核验，不能仅由offset名称推导。

## 完整写入测试：ND、NZ与参考别名

两版test_atb_reshape_and_cache.py完整AST相同。cal_nd克隆两Cache，按slot//block_size与slot%block_size写入对应token，负slot跳过；普通用例14 token、head1、blockSize16、numBlocks53535，K/V headSize各独立随机取1..255，FP16，slot从有效非负空间无放回抽样。参考支持负slot分支不代表该用例实际覆盖负数，也不认证底层负slot合同。

cal_nz把K按INT8时32元素、其它dtype时16元素分tile，V固定16；block_size取Cache shape第2轴，按slot拆block/offset后逐tile写入。实际NZ用例K head512 INT8、V head64 BF16，Cache形状分别[53535,16,128,32]与[53535,4,128,16]，再npu_format_cast(...,29)后调用；不能把类字段block_size16直接代替该NZ参考从shape取得的128。

该helper先clone value_cache，却又令value_expect_nz=value_cache并修改它；随后测试才把value_cache送上NPU。因这个可见别名，V设备初值已经含参考写入，不能只据此断言独立隔离验证了V写入行为。本卡没有运行或修复测试，也没有声称发现已复现的设备错误。

两版SISO测试完整AST相同。参考只clone并更新key_cache、同样跳过负slot；用例16 token、head16、blockSize16、numBlocks8、headSize随机1..255、FP16和非负无放回INT32 slot。三条写入设备用例均标注Ascend910B，没有capture/性能计时或未列混合格式组合验证。

## 完整读取测试：参考的offset与设备范围

两版test_atb_paged_cache_load.py完整AST相同。三个dataclass分别保存gather参数、测试配置与PreparedData。_create_mla_cache实际生成[NBlocks,blockSize,entrySize] FP16；_prepare_data按低秩512与RoPE64拼entrySize576，生成每请求0..512长度、INT32累积长度首项0、随机块排列和0..256的INT32 seq_starts，再split/view成head1的K/V Cache。文档/注释写HEAD轴，实际初始参考Cache为上述三维；split/view并不自动证明Cache无准备拷贝。

_gather_cache_torch先检查源/目的dtype相同，块表/累积长度及提供的seq_starts为INT32；逐batch按累积起止计算长度，0长度跳过，整块与尾块分开复制。它用seq_starts//blockSize选择块表起始列，没有再使用块内余数。该参考路径本身不足以证明任意token级非对齐offset语义，实际动态算子合同仍须核验。

两个设备测试均batch8、blockSize16、numBlocks1024、最大长度512，cumsum保持默认False，seq_starts均提供。一个传预分配[totalTokens,1,512]/[totalTokens,1,64] out，另一个接收新输出；均拼回576维与expected比较。输入生成、参考gather和expected都在device='npu'，不是独立CPU真值；SupportedDevices标注Ascend910B，未在本次运行。没有cumsum=True、缺省seq_starts、负值/溢出异常或NZ读取的直接测试设计，不能把CPP局部检查或参考存在当作这些路径的运行覆盖。

## 固定证据

- [来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/ReshapeAndCachAtb.cpp)（primary）：1–69。
- [来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/ReshapeAndCacheSisoAtb.cpp)（implementation）：1–47。
- [来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/PagedCacheLoadAtb.cpp)（implementation）：1–113。
- [来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/infer_op_params.h)（constraint）：451–491。
- [来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h)（implementation）：134–148。
- [来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_api_docs.py)（constraint）：618–669。
- [来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_reshape_and_cache.py)（example）：1–108。
- [来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_reshape_and_cache_siso.py)（example）：1–42。
- [来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_paged_cache_load.py)（example）：1–294。
- [来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_ops.py)（implementation）：11–45、103–132。
- [来源 11](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/ReshapeAndCachAtb.cpp)（implementation）：1–66。
- [来源 12](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/ReshapeAndCacheSisoAtb.cpp)（implementation）：1–53。
- [来源 13](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/PagedCacheLoadAtb.cpp)（implementation）：1–96。
- [来源 14](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/infer_op_params.h)（constraint）：450–490。
- [来源 15](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/OperationCacheCompute.h)（implementation）：140–156。
- [来源 16](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_api_docs.py)（constraint）：619–670。
- [来源 17](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_reshape_and_cache.py)（example）：1–108。
- [来源 18](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_reshape_and_cache_siso.py)（example）：1–42。
- [来源 19](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_paged_cache_load.py)（example）：1–294。
- [来源 20](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_ops.py)（implementation）：11–42、102–131。
