---
type: Guide
title: ATB前缀注意力：双长度、压缩掩码与输出准备
description: 对照Prefix V2、qlens和PrefixEncoder三条准确入口，区分Q/KV长度、SelfAttentionParam与动态宏、掩码分支、Meta和测试证据范围。
tags:
- task.optimization
- topic.attention
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/SelfAttentionPrefixAtbV2.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/SelfAttentionQlensAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/SelfAttentionPrefixEncoderAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/infer_op_params.h
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_api_docs.py
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_flash_attention_qlens.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_flash_attention_prefix_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_selfattention_prefix_encoder.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/core_tests/test_atb_fake_tensor.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/Utils.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/SelfAttentionPrefixAtbV2.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/SelfAttentionQlensAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/SelfAttentionPrefixEncoderAtb.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/infer_op_params.h
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_api_docs.py
  role: constraint
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_flash_attention_qlens.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_flash_attention_prefix_v2.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_selfattention_prefix_encoder.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/core_tests/test_atb_fake_tensor.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/Utils.h
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_ops.py
  role: implementation
created_at: '2026-11-11T03:58:47Z'
updated_at: '2026-11-14T01:59:28Z'
platforms: []
---

# ATB前缀注意力：双长度、压缩掩码与输出准备

固定OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`和发布`dedc316708372c9a8bfde4527abd2a94b74840f5`。三个CPP文件逐对完整非注释token一致，均以TORCH_LIBRARY_FRAGMENT(atb)声明并在PrivateUse1注册，所选文档仅空白差异；本卡保留各条调用路线，未导入/编译/加载上游、执行测试或验证设备性能。产品与完整ATB配套尚未确认，保持draft、空平台与无新增verified。

## 三条入口的长度和输出分别核对

| 准确atb注册 | 长度实参/本地准备 | 输出与调用路线 |
| --- | --- | --- |
| `_npu_flash_attention_prefix_v2.out` | SymInt[] seq_len为Q长度、context_lens为KV总长度；均以asIntArrayRefUnchecked接at::tensor(...,at::kInt) | 调用方Tensor(a!) out，返回同一引用；SelfAttentionParam+RunAtbCmd |
| `_npu_flash_attention_qlens` | seq_len/context_lens直接为Tensor，包装层不按列表重新创建 | 调用方Tensor(a!) out，返回()；SelfAttentionParam+RunAtbCmd |
| `npu_self_attention_prefix_encoder`及`.out` | SymInt[] seqlen/kv_seqlen分别为Q/KV长度；均创建INT32 Tensor | 普通入口按query.sizes()/options申请新输出；out入口直接提供output并返回引用；EXEC_ATB_CMD(AtbSelfAttentionPrefixEncoder) |

两个列表入口的at::tensor调用只有dtype，没有显式query.device；不能从query建立DeviceGuard推导长度Tensor被分配到query设备。它们没有先做真正动态SymInt范围检查的本地分支，也没有校验每个长度、数组长度、batch、Q总token与KV块容量一致。测试中的两个长度序列按请求保存Q和KV实际长度，不是把累积token末位置协议自动移入此入口。

Python绑定把qlens放API_LIST→torch_npu._npu_flash_attention_qlens，另两条放ATB_API_LIST→torch_npu.atb。返回值、参数名字、列表/Tensor形式和out别名以各自准确schema为准，不由同为prefix或FIA相关推导可互换。

## Prefix V2与qlens的完整固定参数

二者都以query建立OptionalDeviceGuard；headNum/kvHeadNum取num_heads/num_kv_heads，qkScale取scale_value。固定头文件中前二者是int32_t、qkScale是float，接口int64/double赋值有对应窄化。共同固定字段如下，不能套用普通PA_ENCODER(3)场景：

| 字段 | 本地固定值 |
| --- | --- |
| calcType | PREFIX_ENCODER(4) |
| kvcacheCfg / scaleType | K_CACHE_V_CACHE(0) / SCALE_TYPE_TOR(0) |
| quantType / outDataType | TYPE_QUANT_UNQUANT(0) / ACL_DT_UNDEFINED |
| qScale / batchRunStatusEnable / isTriuMask | 1 / False / 1 |
| clampType / clampMin / clampMax | UNDEFINED(0) / 0 / 0 |
| inputLayout / mlaVHeadSize | TYPE_BSND(0) / 0 |
| cacheType / windowSize | CACHE_TYPE_NORM(0) / 0 |

Prefix V2从int直接cast kernel_type/mask_type，schema默认kernel=1、mask=3、num_kv_heads=0、num_heads=0、scale=1；num_heads=0是schema默认，并非文档允许的实际模型头数。qlens则固定KERNELTYPE_HIGH_PRECISION(1)和MASK_TYPE_NORM_COMPRESS(3)，没有kernel/mask选择参数。头声明中kvHeadNum=0采用Q头数，非零使用实际KV头数；GQA约束仍需按相应文档核验。

两者共享SelfAttentionParam类型化Operation缓存和SelfAttentionOperation，再RunAtbCmd。专用缓存与公共ParamSetter规则复用[FlashAttention家族准备](torch_npu_atb_flash_attention_family_preparation.md)和[ATB执行生命周期](torch_npu_atb_paged_attention_execution_lifecycle.md)，不把缓存Operation当作长度/Cache数据不再提交。

## 压缩掩码决定实际槽位

Prefix V2在mask=3时输入依次为Q、K Cache、V Cache、block_table、mask、Q长度Tensor、KV长度Tensor，共7槽；mask=4或5再追加Optional slopes为第7号槽。所有Input均使用默认format_trans=False。slopes=None在需要该槽的分支仍保持空描述位置，不通过删除槽位改变顺序。

其它mask值没有本地填充VariantPack的分支，但函数仍取Operation并RunAtbCmd；不要把enum cast或“没有局部TORCH_CHECK”当成其它mask已经支持，也不要只据空pack直接宣称所有实际运行必然报某一种错误。所选文档只声明3/4/5且kernel必须1；新主线SDK枚举另有kernel2，并未因此增加本前缀文档的允许组合。

qlens固定相同7槽顺序，format_trans=True仅在Q、block_table、seq_len和context_lens；K/V Cache和mask使用默认False。两个长度Tensor可以沿公共CPU clone分支准备；请求格式转换不保证发生物理复制。Output仍直接使用调用方out，不能据Input会contiguous推导任意非连续out可写回。

两条包装都没有按out参数重新申请/resize结果；out的shape/dtype/容量及输入连续化成本要与实际参数一起记录。

## 固定Prefix V2文档的约束与可见差异

文档把Q定义为ND FP16/BF16的[sum Q tokens,heads,headSize]或二维hidden形式；KV为ND分页Cache、K/V shape一致，blockSize必须128、K/V headSize≤128、blockSize×headSize≤128×128，headSize需16对齐。PrefixCacheLen=KV长度−Q长度且要求128对齐；Q/KV头数须满足headNum>0、headNum≥kvHeadNum及整数倍关系。

block_table为INT32 ND [batch,maxBlockNum]，需覆盖最大KV长度所需块数。原文另写item value<maxBlockNum；numBlocks与每请求maxBlockNum的角色不同，本地包装未做此边界校验，不应把这一句自行改写成任意Cache索引安全证明。

mask仅压缩：NORM_COMPRESS给[128,128]，ALIBI_COMPRESS及SQRT给[256,256]或[head,seqLen,128]，FP16/BF16 ND；slopes声明FP32 ND [head]。文档签名一行把seq_len/context_lens写成Tensor，参数正文称int数组，而CPP schema是SymInt[]，这三处分别保留。样例slopes又按headSize构造并使用若干未在示例内定义的长度变量，不能把它当成已运行的完整脚本或用它覆盖正文[head]约束。

文档另外要求qScale=1、isTriuMask=1、无clamp、BSND、无MLA，kernel=HIGH_PRECISION且KV计算内部使用FP32；这些是该固定文档的场景声明，不是本次误差界或实测精度结论。

## PrefixEncoder动态入口不等同SelfAttentionParam分支

两个重载的mask_type map准确键为mask_type_norm_compress→3、mask_type_alibi_compress→4、mask_type_alibi_compress_sort→5、mask_type_causal_mask→9，默认最后一项。sort是该字符串map的实际拼写，不按另一个接口的SQRT名称擅自替换。get_op_mode用optional默认值精确查表，未知字符串TORCH_CHECK；map接受键并不独立证明所配执行库支持所有模式。数值9传给动态AtbSelfAttentionPrefixEncoder，不能强行解释成SelfAttentionParam的mask枚举（其所读声明0..8）。

普通入口先guard query设备、申请query同shape/options的output，再解析模式；非法模式不代表此前没有申请。两重载把qk_scale显式转float，先创建KV长度Tensor再Q长度Tensor，但传宏的顺序始终Q长度在前、KV长度在后：query/key/value/block_tables/mask/seqlen_tensor/kv_seqlen_tensor/slopes/mask_type/q_headnum/kv_headnum/qkScale_float/output。

所选文档只声明当前支持默认causal字符串，mask/slopes默认不必给，并列Q长度≤KV长度及差值128对齐；它把此函数描述成MLA、提到分离qnope/qrope输入，但实际本地schema只有query/key/value，不据这段描述添加未出现的输入或改成另一MLA算子。out重载不在本地复制普通重载的分配/尺寸逻辑。

此入口的执行宏转换、动态符号、每次工作区和hash范围复用[动态ATB调用路线](torch_npu_atb_mla_preprocess_and_ring_preparation.md)。宏路线没有ParamSetter的format_trans开关，不把前两条的True/False和CPU clone规则直接套到它；输出转换与写回边界亦沿对应宏核验。

## Meta与直接测试的准确范围

PrefixEncoder的所选Meta函数仅返回torch.empty_like(query)。两版FakeTensor用例设query=[4×128,28,128] FP16、KV=[64,128,28,128]、长度[32]×4，调用头数28/4后只断言输出shape/dtype等于query。长度总数与query首维在这个fixture里并不一致；Meta成功的设计只反映输出推形，没有证实真实设备长度/分页合同合法。

Prefix V2所选完整直接测试方法两版AST相同：单batch BF16、Q头12/KV头1、headSize128、Q长度128/KV长度512、blockSize128/numBlocks1024，调用mask5/kernel1，slopes显式转FP32；长度实参构造成CPU INT32 Tensor。CPP schema仍是SymInt[]，该测试写法本身不认证任意设备Tensor能作为列表参数。测试调用共享生成/参考/比较helper并断言结果；这些约958行文件中的其它helper不在本卡全文阅读范围，未把所选方法提高为整文件完成或实测成功。

PrefixEncoder所选三完整设备测试两版AST也相同，均标注Ascend910B但明确因旧CANN版本而skip。前两分别为BF16带尾部和FP16整块、batch2、Q/KV头4/2、headSize128、Q/KV长度差256；第三batch92、Q/KV头28/4、headSize128，前91请求长度127、末请求8099且Q/KV等长。三个都走默认模式、未传mask/slopes。这里只覆盖这些直接调用参数与skip，长参考/量化/生成helper继续开放。

## qlens完整参考测试：两种长度不要互换

两版test_atb_flash_attention_qlens.py完整AST相同。三个dataclass封装生成配置、参考输入和生成结果；配置默认prompt2、Q/KV头32/32、head/block128、block数64，实际用例改KV头16。类常量MAX_SEQ_LEN=1024、SCALE_TYPE=0，另预生成不小于1且小于2的rand_list仅供可切换scale分支。

生成器每请求KV总长度1024，局部名context_lens却是从128..896按128倍数抽取的“前缀长度”，Q长度=1024−该值；最后传包装的context_lens来自结果seq_lens，即1024总KV长度。Q首维为sum(Q长度)，块表每请求8个随机有效Cache块号；Q/K/V/参考输出为BF16，长度和块表为INT32。参考mask为[1,1024,1024]上三角乘−10000。

完整参考逐请求按block_table与block_size收集KV，Q按query_lens切分；group_matmul按Q头/KV头的整数分组逐头乘法后拼接。ref_masked_attention先缩放Q，按KV总长−Q长对齐mask最后Q行；减row_max后转FP32做exp/sum归一化，概率转BF16后与V相乘并恢复Q轴顺序。参考默认scale=1/sqrt(headSize)，SCALE_TYPE=1分支才乘rand_list系数，当前设备用例使用默认0。

实际测试参数为prompt2、Q/KV头32/16、headSize/blockSize128、block数64；输入Cache/Q/块表上NPU，长度保留CPU，压缩mask是BF16 [128,128]上三角0/1，调用后assertRtolEqual。它带unittest.skip("skip case")及Ascend910B标注，因此只作完整静态参考。这里没有capture/task更新、非因果替代模式或性能测量，不能从跳过测试、Meta或版本token相同推出运行verified。

## 固定证据

- [来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/SelfAttentionPrefixAtbV2.cpp)（primary）：1–105。
- [来源 2](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/SelfAttentionQlensAtb.cpp)（implementation）：1–84。
- [来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/atb/SelfAttentionPrefixEncoderAtb.cpp)（implementation）：1–116。
- [来源 4](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/third_party/atb/inc/infer_op_params.h)（constraint）：36–44、522–668。
- [来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_api_docs.py)（constraint）：72–119、403–474。
- [来源 6](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_meta_registrations.py)（implementation）：31–34。
- [来源 7](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_flash_attention_qlens.py)（example）：1–238。
- [来源 8](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_flash_attention_prefix_v2.py)（example）：915–955。
- [来源 9](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_custom_ops/test_atb_selfattention_prefix_encoder.py)（example）：959–1002、1004–1047、1049–1095。
- [来源 10](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/core_tests/test_atb_fake_tensor.py)（example）：130–149。
- [来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/atb/Utils.h)（implementation）：81–91。
- [来源 12](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/atb/_atb_ops.py)（implementation）：11–45、103–132。
- [来源 13](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/SelfAttentionPrefixAtbV2.cpp)（implementation）：1–106。
- [来源 14](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/SelfAttentionQlensAtb.cpp)（implementation）：1–75。
- [来源 15](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/atb/SelfAttentionPrefixEncoderAtb.cpp)（implementation）：1–68。
- [来源 16](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/third_party/atb/inc/infer_op_params.h)（constraint）：39–47、522–667。
- [来源 17](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_api_docs.py)（constraint）：72–119、403–474。
- [来源 18](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_meta_registrations.py)（implementation）：31–34。
- [来源 19](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_flash_attention_qlens.py)（example）：1–238。
- [来源 20](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_flash_attention_prefix_v2.py)（example）：905–945。
- [来源 21](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_atb_selfattention_prefix_encoder.py)（example）：949–992、994–1037、1039–1085。
- [来源 22](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/core_tests/test_atb_fake_tensor.py)（example）：130–149。
- [来源 23](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/atb/Utils.h)（implementation）：81–91。
- [来源 24](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/atb/_atb_ops.py)（implementation）：11–42、102–131。
