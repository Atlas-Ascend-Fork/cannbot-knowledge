---
type: Guide
title: GE旋转与KV缓存融合：函数化拷贝及输出顺序
description: 核对RoPE量化的Eager/GE模式分歧、QKV缓存功能化整块拷贝、返回顺序、Meta占位与别名边界。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dequant_rope_quant_kvcache.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dequant_rope_quant_kvcache.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_qkv_rms_norm_rope_cache.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_qkv_rms_norm_rope_cache.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rope_quant_kvcache.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rope_quant_kvcache.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QkvRmsNormRopeCacheNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DequantRopeQuantKVCacheKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RopeQuantKVCacheKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QkvRmsNormRopeCacheNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DequantRopeQuantKVCacheKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RopeQuantKVCacheKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_rope_quant_kvcache.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_qkv_rms_norm_rope_cache.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_npu_rope_quant_kvcache.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_qkv_rms_norm_rope_cache.py
  role: example
created_at: '2026-11-10T09:30:27Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE旋转与KV缓存融合：函数化拷贝及输出顺序

## 固定版本与证据范围

固定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013。所选主线完整非空源码、发布完整AST/注释差异已审阅；这批成对Converter的差异为说明字符串、导入顺序、等价异常字符串写法，计算映射不变。QuantMax的同路径仅主线存在，缺路径不推导发布软件缺能力。

本卡限定静态构图及对应OpPlugin Eager/Meta的迁移合同，整卡平台矩阵未知，保持draft与空平台；未执行上游、GE编译、真机精度/别名/通信或性能实验。Support只是候选，警告和注释不是本次复现。IR参数与真实kernel、调度及外围函数化需分别核对。

## 两条RoPE量化入口共用DequantRopeQuantKvcache

npu_dequant_rope_quant_kvcache.default传x/cos/sin、k/v cache ref、indices、scale/offset以及weight_scale/activation_scale/bias；npu_rope_quant_kvcache.default也调用DequantRopeQuantKvcache，但显式把后三项设None。两者均将size_splits设属性、input_layout映射layout，并透传kv_output/cache_mode。

quant_mode仅按==0映射static，其余全部dynamic，没有完整枚举范围检查。默认input_layout=BSND、kv_output=False、cache_mode=contiguous。局部函数没有统一Cast、完整shape/scale/offset/缓存索引检查或额外TensorMove，不能仅凭ref参数名认证原地写回、缓存一致性、所有布局或量化精度。

## QKV/RMSNorm/RoPE缓存融合的功能化顺序

npu_qkv_rms_norm_rope_cache.default直接QkvRmsNormRopeCache，传qkv/q_gamma/k_gamma/cos/sin/index/q_out/k_cache/v_cache；可选k/v scale与offset、qkv_size/head_nums、epsilon、cache_mode、is_output_qkv原样映射。默认epsilon=1e-6、cache_mode=PA_NZ、is_output_qkv=False，不能继承上一组contiguous默认布局。

功能化准确入口npu_qkv_rms_norm_rope_cache_functional.default先分别TensorMove(q_out)、TensorMove(k_cache)、TensorMove(v_cache)，再将这些副本传同一GE节点。接回out0..out5后，**返回(out3,out4,out5,out0,out1,out2)**，而普通入口原序返回GE结果。不能按位置把两个入口输出混用，也不能为减少搬运删掉隔离副本。

本层没有额外解释六项输出的完整物理ABI、qkv_size/head_nums关系或所有缓存模式支持，Meta也未在函数内用来对全部输出Cast。是否实际写回、如何消费返回缓存、并发更新与性能收益须结合调用方和kernel核对，不能从融合名或函数化名独立认证。

## Eager、Schema和Meta的交叉检查

本节另审阅OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`与发布`dedc316708372c9a8bfde4527abd2a94b74840f5`的三份缓存包装、对应Schema与Meta函数。三份C++在两个快照间仅有排版差异，以下分支两版均存在；不据此证明TorchAir与OpPlugin主线已配套运行。

### 量化模式只使用明确约定的0和1

RoPE和Dequant-RoPE两个Eager包装均先设`static`，仅`quant_mode==1`改为`dynamic`；GE Converter却按`==0`选`static`，其他值均为`dynamic`。因此从源码推导，若误传2，Eager将传static、GE将传dynamic；这是非法/未证明枚举的静态分歧，尚未运行复现，也不是新增mode2能力。集成层应显式限定0/1，不能借“非0”概括Eager动态量化条件。

Dequant入口在C++和Meta都要求x为INT32，RoPE入口不做同样的前置dtype检查。二者最后都调用`aclnnDequantRopeQuantKvcache`；RoPE把weight_scale、activation_scale和bias传未定义Tensor。融合名不意味着FP16输入会自动补做INT32累加结果的反量化，相关尺度和数据编码仍要与选中入口对齐。

### 输出分配依据与缓存别名

两个RoPE包装返回`(Q,K,V,原k_cache,原v_cache)`，没有在本层clone缓存。C++以**V cache**的第2/3轴为KV头数和D，令Q头数为`size_splits[0]/D`的整数商，D为0时取0；x为二维时Q为`[x0,Nq,D]`，三维时为`[x0,x1,Nq,D]`。K/V可选额外输出沿相同规则，dtype/device取cos的options；`kv_output=False`时两项为`[0]`空Tensor，缓存两项仍返回原引用。

Meta公共helper却以**K cache**的第2/3轴推导这些形状，只检查K cache四维；C++前置检查的是V cache四维。合法输入应先保证K/V缓存维度一致、Q split能整除D、全部split与实际QKV内容匹配；局部整数除法和成功Meta推导不证明这些条件完整成立。C++还先访问`size_splits[0]`再校验长度，不应把空列表交给该局部检查兜底。

两版RoPE Schema将k_cache/v_cache写成普通Tensor，未像QKV入口用`Tensor(a!)`等明确标注mutation；C++和Meta又把原cache作为返回项。这里记录的是声明与实现的别名审计入口，不据此断言图优化、并发写回或函数化已经正确。验收必须观察缓存实际写入、原对象是否保持/改变以及返回值消费，不能把第五项返回看成新缓存副本。

### QKV功能化的额外拷贝与返回合同

QKV普通Schema明确q_out、k_cache、v_cache分别是`Tensor(a!)`、`Tensor(b!)`、`Tensor(c!)`，C++将它们直接交给`aclnnQkvRmsNormRopeCache`。普通入口只返回三个量化前的可选输出；更新后的Q和缓存由输入对象承载。功能化入口则**无条件完整clone这三个Tensor**，在副本上调用同一ACLNN，并返回`(Q_before,K_before,V_before,Q_copy,K_cache_copy,V_cache_copy)`。这与前述GE六输出重排对应，不能把前三项误作更新后缓存。

`is_output_qkv=False`只关闭三个before输出的分配，不关闭functional的三次clone。评估Decode收益时，按三个输入的`numel*element_size`估算显式逻辑拷贝量，另外计入输出、工作区及allocator行为；缓存容量增长可能增加这部分成本，而实际缓存更新token数没有在该clone分支中作切片。GE里的TensorMove也需核查实际优化结果，不能由静态节点名直接断言最终一定发生相同字节搬运。保留输入的功能化语义若是调用方要求，就不能直接删除拷贝；可用原地入口的场景先核对graph capture、别名和缓存生命周期，再测端到端收益。

### QKV未请求输出时的Meta占位差异

开启`is_output_qkv`时，C++和Meta均按`[qkv.size(0),head_nums[i]*qkv_size[3]]`分配三个before输出，dtype与qkv相同。关闭时C++将三个对象设为**未定义的`at::Tensor()`**，Meta却返回三个`torch.empty([])`，即0维标量形状占位，既不是`[0]`空Tensor，也不是已计算的Q/K/V。functional的最后三项Meta为empty_like，不能用来认证真实clone内容或别名。

该差异是静态观察，不预断Python桥接后一定出现哪种异常。集成时不消费已关闭的before输出；若图编译、输出树或缓存重放依赖这些槽位，应分别检查Eager对象、FakeTensor/Meta输出结构与实际GE结果。不要把Meta中的标量槽当成有意义的模型输出。

## 完整Host实现的局部检查与格式边界

完整prepare_before_quant仅检查qkv_size长度为4、head_nums长度为3以及qkv为二维；即使is_output_qkv=False也先做这些检查。它按head_nums[0..2]*qkv_size[3]构造三个before输出形状，没有在此验证头数之和与qkv尾宽、缓存实际维度、gamma、epsilon和索引值。QKV普通/functional都使用EXEC_NPU_NO_FORMAT_CHECK_CMD下传ACLNN；宏名不构成所有格式合法或运行通过的证明。

两个RoPE包装按上述V cache形状分配、将input_layout/cache_mode的string_view.data cast为char*传递，offset等可选参数在本地不填默认数值；Dequant额外三项可选尺度/bias与普通RoPE的未定义占位占相同ACLNN位置。完整三份主线CPP与对应发布CPP在C++续行消解后的全部非注释token及全部注释一致，所述Host合同可复用；没有把调用的ACLNN实现算作已阅读。

## RoPE测试的量化乘法、参考缓存与skip边界

两版221行RoPE测试原始字节相同，两个Ascend910B方法均有unittest.skip。静态参考先按size_splits拆Q/K/V，以cos尾宽推导头维，对Q/K做半轴旋转[-后半,前半]再乘cos/sin；V不做旋转。quant_update_scatter以key.float()*scale可选加offset再round，随后**再round并裁剪到[0,10]**才写缓存；这不是完整INT8[-128,127]量化参考，不能推广为接口的通用量化范围。

helper包含ifpa=True时按索引展平scatter的分支，但golden_compare的两次调用均使用默认False，按每个batch的起始索引写连续序列。两个方法只取x三维、128尾宽、单token，分别BF16的Q/K/V各一头及FP16的Q两头/KV一头；随机缓存由[0,1)浮点数转INT8，初始基本为0。它们比较Q和两份缓存，未数值比较K/V可选输出，调用也未开启kv_output。golden_compare在NPU调用之后继续接收原in_k_cache/in_v_cache对象，没有先保留独立的调用前缓存快照；不能据此证明未更新槽位或原地别名的隔离正确。

## QKV测试的RMSNorm、PA_NZ写回与参考精度

312行QKV测试的主线与发布完整AST相同，所有原文差异仅行尾空白。参考将QKV、gamma、cos/sin转FP32，按head_nums拆分；对Q/K分别做x/sqrt(mean(x²)+epsilon)*gamma和全D旋转，V保持拆分值。K/V若有scale则除scale，可选加offset，有scale时round并clamp[-128,127]；与上一份RoPE参考乘scale的约定不能互换。

PA_NZ scatter将cache解释为[block_num,head,D/32,block_size,32]，索引为负时跳过，否则按index//block_size和index%block_size逐32通道块写回。reference保留Q、K在量化前以及原V的before结果，最后固定将Q/before转FP16、cache转INT8；不能借helper存在input_dtype参数推广到所有dtype。生成器只为PA_NZ建立cache和index，quant_mode仅控制INT8缓存及可选scale，不是额外传入此QKV算子的量化枚举。

唯一方法同样有unittest.skip和Ascend910B装饰器，选B=72/S=2、头数16/1/1、D=128、11898个block、block_size=128、FP16、量化缓存及is_output_qkv=True。custom helper调用普通原地入口，搬回被写入的Q/cache与三个before，末尾reset Dynamo；没有执行functional或证明其三次clone可删除。该方法先调用supported_op_exec，Scatter通过reshape视图就地写入CPU k_cache/v_cache，随后才把同一缓存交custom_op_exec并转NPU，设备路径起始缓存已带参考写入结果；没有独立保留原始调用前cache，未更新槽位及参考隔离也不能由此证明。这是静态测试代码边界，没有运行复现。Q/cache以prec=0.001比较；before先核shape/dtype并尝试相同相对误差，失败时仅要求最大绝对差≤1。BF16/其他精度分支、is_output_qkv=False、offset、非PA_NZ及负索引全范围没有由这个skip方法得到运行验收。没有导入测试、分配这些大缓存、执行Dynamo或新增verified。

## 优化验证

先限定量化模式0/1，再核对FX准确入口、布局与cache_mode、indices、size_splits/qkv_size/head_nums和返回消费顺序；区分RoPE的五项返回与QKV普通三项、functional六项。用非均匀输入核对未请求输出的占位、原缓存/副本和未更新槽位，验证量化误差、缓存ABI与并发行为，再按相同缓存容量及token数对照Eager/GE耗时、峰值内存和完整Decode收益。本文没有执行这些实验，也没有将静态分歧记为设备故障复现。

- [RMSNorm与融合返回顺序](torchair_ge_layer_group_rms_norm_lowering.md)
- [视图复制与别名边界](torchair_ge_view_copy_lowering.md)

## 准确映射清单

仅列所选文件实际注册，有构图分支不证明全部参数或产品可用；未声明的其他重载不作能力否定。

| 文件主题 | 准确入口 |
| --- | --- |
| npu_dequant_rope_quant_kvcache | `torch.ops.npu.npu_dequant_rope_quant_kvcache.default` |
| npu_qkv_rms_norm_rope_cache | `torch.ops.npu.npu_qkv_rms_norm_rope_cache.default`、`torch.ops.npu.npu_qkv_rms_norm_rope_cache_functional.default` |
| npu_rope_quant_kvcache | `torch.ops.npu.npu_rope_quant_kvcache.default` |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dequant_rope_quant_kvcache.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_dequant_rope_quant_kvcache.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_qkv_rms_norm_rope_cache.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_qkv_rms_norm_rope_cache.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rope_quant_kvcache.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_rope_quant_kvcache.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）

- [OpPlugin包装补充来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QkvRmsNormRopeCacheNpuOpApi.cpp)（implementation）
- [OpPlugin包装补充来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DequantRopeQuantKVCacheKernelNpuOpApi.cpp)（implementation）
- [OpPlugin包装补充来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RopeQuantKVCacheKernelNpuOpApi.cpp)（implementation）
- [OpPlugin包装补充来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [OpPlugin包装补充来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）
- [OpPlugin包装补充来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QkvRmsNormRopeCacheNpuOpApi.cpp)（implementation）
- [OpPlugin包装补充来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DequantRopeQuantKVCacheKernelNpuOpApi.cpp)（implementation）
- [OpPlugin包装补充来源 8](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RopeQuantKVCacheKernelNpuOpApi.cpp)（implementation）
- [OpPlugin包装补充来源 9](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）
- [OpPlugin包装补充来源 10](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

## 完整OpPlugin范围

- [DequantRopeQuantKVCacheKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/DequantRopeQuantKVCacheKernelNpuOpApi.cpp)（implementation）：完整本地文件1–108。
- [RopeQuantKVCacheKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/RopeQuantKVCacheKernelNpuOpApi.cpp)（implementation）：完整本地文件1–108。
- [QkvRmsNormRopeCacheNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QkvRmsNormRopeCacheNpuOpApi.cpp)（implementation）：完整本地文件1–169。
- [DequantRopeQuantKVCacheKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/DequantRopeQuantKVCacheKernelNpuOpApi.cpp)（implementation）：完整本地文件1–92。
- [RopeQuantKVCacheKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/RopeQuantKVCacheKernelNpuOpApi.cpp)（implementation）：完整本地文件1–91。
- [QkvRmsNormRopeCacheNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QkvRmsNormRopeCacheNpuOpApi.cpp)（implementation）：完整本地文件1–105。
- [test_npu_rope_quant_kvcache.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_npu_rope_quant_kvcache.py)（example）：完整本地文件1–221。
- [test_npu_qkv_rms_norm_rope_cache.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_npu_qkv_rms_norm_rope_cache.py)（example）：完整本地文件1–312。
- [test_npu_rope_quant_kvcache.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_base_ops/test_npu_rope_quant_kvcache.py)（example）：完整本地文件1–221。
- [test_npu_qkv_rms_norm_rope_cache.py dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_qkv_rms_norm_rope_cache.py)（example）：完整本地文件1–312。
