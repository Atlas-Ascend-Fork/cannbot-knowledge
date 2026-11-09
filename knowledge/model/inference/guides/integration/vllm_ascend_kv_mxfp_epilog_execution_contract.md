---
type: Guide
title: vLLM Ascend主KV MXFP epilog：BF16尺度、紧凑token与六路执行
description: 串接KvCompressEpilogV2的BF16输入、FP8/FP4分组尺度、2D与分页紧凑payload，解释六个key、有效slot过滤、尾nibble/scale防覆盖、UB复用与control恢复；区分主KV
  BF16-scale、Indexer FP32/E8M0和旧608字节格式。
tags:
- task.implementation
- task.debugging
- topic.kv_cache
- topic.precision
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_compress_epilog_v2/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_compress_epilog_v2/README.md
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_compress_epilog_v2/kv_compress_epilog_v2_torch_adpt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_compress_epilog_v2/op_host/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_compress_epilog_v2/op_host/kv_compress_epilog_v2_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_compress_epilog_v2/op_host/kv_compress_epilog_v2_proto.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_compress_epilog_v2/op_host/kv_compress_epilog_v2_tiling_arch35.cpp
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_compress_epilog_v2/op_host/kv_compress_epilog_v2_tiling_arch35.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_compress_epilog_v2/op_kernel/kv_compress_epilog_v2.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_compress_epilog_v2/op_kernel/kv_compress_epilog_v2_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_compress_epilog_v2/op_kernel/kv_compress_epilog_v2_kernel.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_compress_epilog_v2/op_kernel/kv_compress_epilog_v2_layout_2d.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_compress_epilog_v2/op_kernel/kv_compress_epilog_v2_layout_4d.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_compress_epilog_v2/op_kernel/kv_compress_epilog_v2_quant_fp4_g16.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_compress_epilog_v2/op_kernel/kv_compress_epilog_v2_quant_fp4_g32.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/kv_compress_epilog_v2/op_kernel/kv_compress_epilog_v2_quant_fp8.h
  role: implementation
created_at: '2026-11-03T04:58:09Z'
updated_at: '2026-11-03T04:58:09Z'
platforms: []
aliases:
- KvCompressEpilogV2
- KvCompressEpilogV2Layout4dCommon
- VFProcessMxFp8FullRowPerf
- VFProcessMxFp4Group16RowBatchPerf
- VFProcessMxFp4RowBatchPerf
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend主KV MXFP epilog：BF16尺度、紧凑token与六路执行

## 框架格式、cache writer与完整算子分开

新模型迁移MXFP KV、扩大物理页stride或检查FP4尾部覆盖scale时，沿本卡核对写端实际byte layout。Main固定ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文读取本族16文件2465行，包括Host、两种layout和三种量化body。复用root实际“压缩缓存”查重，全文读[DSV4旧KV计划](vllm_ascend_dsv4_kv_plan_contract.md)后独立成执行facet；它的608字节NoPE/RoPE接口与本族不是同一格式。

OpDef注册ascend950，README追溯移植源但本卡只分析Main固定版本，未另行执行原项目。保持draft/空平台，CANN栈及完整上下游不作已验证声明；未导入上游、运行UT、编译、JIT、NPU、数值或性能测试，不宣称完整Operator闭包。[KV格式总览](vllm_ascend_kv_quant_format_contract.md)保留更广量化配置边界。

## 入口只接受三种组合

Torch把mode去首尾空白、转小写，只接受mxfp8_bf16和mxfp4_bf16，转换为Host模式2/4。x必须非空连续二维BF16，D<=8192且整除group；slot连续一维INT32/INT64、行数与x相等。x_scale保留但必须恰为1.0，不是可用的任意激活预缩放旋钮。

| 模式 | group | cache声明dtype | 数据/scale格式 |
|---|---|---|---|
| MXFP8 BF16尺度 | 32 | E4M3FN或E5M2 | D个FP8字节，D/32个BF16尺度 |
| MXFP4 BF16尺度 | 32 | UINT8 | D/2个packed E2M1字节，D/32个BF16尺度 |
| MXFP4 BF16尺度 | 16 | UINT8 | D/2个packed E2M1字节，D/16个BF16尺度 |

这是BF16 scale协议，不是Indexer的E8M0分组格式或[Indexer FP8 epilog](vllm_ascend_indexer_fp8_epilog_execution_contract.md)的FP32尺度；名称含MXFP也不意味着可以互换标准MX字节布局。cache dtype只解释data区，底层buffer还保存BF16 scale字节。

## 2D与4D的物理写入不同

layout由cache rank决定：2D要求连续`[cacheRows,rowCapacity]`；4D为`[blocks,blockSize,1,rowCapacity]`，第三维1、末轴stride1，实际block_stride由cache.stride(0)传Host。Host允许0时按紧凑块推导，4D stride必须非负、至少blockSize*rowCapacity且32字节对齐。内层任意strided view并未开放。

每token的dataCol为D或D/2，scaleBytes=2*(D/group)，tokenStride=dataCol+scaleBytes；kvCacheCol=align32(tokenStride)。2D每行容量至少kvCacheCol，写slot*rowCapacity处共kvCacheCol字节，quant body将payload后padding置0；rowCapacity更宽的尾部不会因此全部清零。

4D先拆block=slot/blockSize、pos=slot%blockSize，写`block*blockStride+pos*tokenStride`，每token紧凑排列data再BF16 scales。即使shape末轴rowCapacity更大，也不按pos*rowCapacity放token；多余容量成为块内预算而不是自动逐tokenpadding。D512时FP8-g32为544字节，FP4-g16为320字节，FP4-g32为288字节；不能套用旧608字节或TurboQuant槽。

UB内data段按32字节对齐，4D输出时若dataCol对齐可一次搬整个token；否则把data和scale分别搬到紧凑GM位置，丢掉UB两段之间的对齐空隙。只复制UB整行或只按shape做view会改变packed ABI，尤其小D与FP4尾组必须核对。

## 六个真实key与slot过滤

| layout | FP8-g32 | FP4-g32 | FP4-g16 |
|---|---|---|---|
| 连续2D | 2000 | 2001 | 2002 |
| 分页4D | 2100 | 2101 | 2102 |

entry逐key实例化对应layout薄壳，FP8模板还接cache dtype；FP4两种group均为独立量化body。旧KvCompressEpilogV2Kernel壳未在入口实例化，头中“Verified”和注释“基线等价”不是本次测试结果；本卡已读它以划清实际Route，源表按未实例化参考skip，不把它计成可达执行。

LoadRows先排除slot<0或slot>=cacheRows，再压紧有效x和slot列表。全无有效行时先归还x队列再continue；无效slot保持原cache字节，不能用padding清历史KV。有效slot重复时没有跨core冲突仲裁，caller需保证写入唯一性和所有权。entry要求workspace及GetUserWorkspace非空，否则直接返回；cache_out不在body内独立写入，实际原位更新输入cache地址。

每核承担ceil(batchRows/AIV)附近的连续输入段，首尾核/最后loop保存独立行数。Host逐candidate估UB，至少一行装不下明确报错，区别于其他epilog未充分处理rowFactor0的实现；不能用一个算子门禁推断同目录所有算子都相同。

## FP8：round_scale改变的是执行和尺度链

每32元素求amax，先取max(amax,1e-4)，再除448或57344。round_scale=False走VFProcessMxFp8基线，按未向上二次幂化的尺度归一化、clamp到对应FP8范围，CAST_RINT转FP8，scale以BF16写出。不能把保存的BF16 scale误认为FP32中间scale没有舍入误差。

round_scale=True走FullRow三阶段：BF16幅值位级amax写scratch；逐组scale向上取2的幂、写BF16输出，并把FP32 scale存回同一scratch；最后按lane>>5收集每组FP32 scale，Div/clamp/Cast写FP8。phase2逆序处理chunk，避免FP32扩写覆盖尚未读的uint16 amax。两个LocalMemBar连接Vector store与load，不能改为正序后仍宣称同一alias寿命。

该幅值位归约的等价说明明确以有限输入为前提；NaN/Inf、极小值与SDK转换规则需实际对照。1e-4 floor、power-of-two rounding与Indexer直接amax/448不同，不因最终dtype相同就复用其参考阈值或误差承诺。

## FP4：BF16指数位链与精确nibble尾部

g32把BF16指数域按组归约，g16先取16元素幅值amax再提指数。两者用0x7F80指数掩码、0x0100偏置计算共享scale位，处理全零、非有限与特殊倒数情形，再以BF16 reciprocal因子乘输入，CAST_RINT转packed E2M1。scale存完整BF16位，不是一个E8M0字节。不要把这条位链简化成同FP8的浮点amax/448。

g32的scale链与amax同寄存器阶段完成，写halfScale scratch后用一个LocalMemBar交接数据阶段；数据按实际valid元素分开even/odd转换和nibble对写入，尾拍不应扩写到scale/pad区。g16为amax、整行scale链、数据乘/转换三阶段，两个LocalMemBar；E2B_B16广播16组尺度、128元素一拍，不可拿g32的块广播步长替代。

round_scale只分流FP8；当前FP4 g16/g32的两layout wrapper并未按该属性选择另一算法。硬件CAST_RINT的ties-to-even意图不等于本次已验证所有半值/非有限行为，名称Perf/Verified也不提供精度或性能记录。

## UB、同步和control寿命

两layout共有深度2 x/output队列与slot scratch，FP8另保FP32 group-scale scratch，FP4保uint16 halfScale scratch；2D还分配32字节padding buffer，4D直接拷payload。Host预算保留更一般的scale/FP4临时空间，是规划上界，不应当作每条当前thin-wrapper实际都分配同一套基线buffer。

x按16个BF16对齐，输出按32字节，group scratch按32字节；g16 Host额外预算按candidate*ceil(D/64)*32等估算。记录rowFactor/used cores与实际UB后再调大D或batch，不把KV低比特节省直接推成临时UB同倍率节省。

LoadRows通过EnQue/DeQue交接输入，量化阶段通过本地barrier处理alias，输出队列再交给DataCopyPad，FreeTensor结束本轮使用；自动同步编译选项关闭。entry保存overflow control，在各key完成Process后统一恢复，区别于命中分支提前return的Indexer epilog；未知key不写输出。源码顺序不替代外部AscendC、pipe、跨stream和graph实际验证。

## 接入和停止点

新模型先冻结mode/group、scale实际dtype、page tokenStride/blockStride和同一storage owner，再核INT32/INT64 slots、越界/全padding、重复写与上下游依赖。分别检查D32/非32-byte dataCol、小尾拍、D512主例、最大D、FP8两round_scale、FP4两group、zeros/subnormal/NaN/Inf和ties；对照cache有效区与未写哨兵。之后再接对应Attention reader并测端到端内存/时延。

本卡已读本族可见Host与Device，但生成ACLNN入口、外部primitive细则、主Attention读端、完整Compressor及真实平台栈仍需闭合。产品支持、数值、资源和性能没有通过一次源码阅读变成实测结论；本次知识提取未执行编译、真机、数值或性能测试。
