---
type: Guide
title: vLLM Ascend共享Kernel helper：模板命中、布局搬运与mask/PSE约束
description: 核对固定Main common/kernel的空通用模板、V220条件回写、固定资源常量、ND/NZ与大stride分支、L1/L0/Fixpipe单位和精度、SIMD mask及Dropout/PSE偏移；为新模型内核复用和无输出/尾部错误诊断提供集成边界。追加utils目录的IPC flag协议、HCCL资源视图、同步等待与fallback/tiling/log副本差异，避免同名头跨目录误用。
aliases:
- AsdopsBuffer
- HardwareInfo
- gm_to_l1
- l0c_to_gm
- l1_to_l0_a
- PseAlibiComputeOffset
- PseInnerAlibiCreate
- ComputeDropOffset
- SyncCollectives.WaitOneRankPartFlag
- SyncCollectives.GetChunkRecvLen
- Moe.CommArgs
tags:
- task.implementation
- task.debugging
- topic.model_adaptation
- topic.data_movement
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/common_func.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/dropmask.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/gm_to_l1_iterator.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/gm_to_ub_iterator.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/hardware.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/iterator.h
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/l0c_to_gm_iterator.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/l0c_to_l1_iterator.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/l0c_to_ub_iterator.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/l1_to_bt_iterator.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/l1_to_fb_iterator.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/l1_to_l0_iterator.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/l1_to_ub_iterator.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/layout.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/mem.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/mma.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/pse.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/simd.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/common/include/kernel/util.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/utils/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/utils/inc/error/ops_error.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/utils/inc/fallback.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/utils/inc/fallback_comm.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/utils/inc/kernel/comm_args.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/utils/inc/kernel/data_copy.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/utils/inc/kernel/moe_distribute_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/utils/inc/kernel/sync_collectives.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/utils/inc/kernel/util.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/utils/inc/log/inner/dfx_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/utils/inc/log/ops_log.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/utils/inc/tiling/data_copy_transpose_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/utils/inc/tiling/tiling_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/utils/inc/tiling/tiling_templates_registry.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/utils/inc/tiling/tiling_type.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/utils/src/fallback_comm.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/common/kernel_utils/block/block_mmad_pingpong_tla_preloadA_l1B.hpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/common/kernel_utils/vector/regbase.hpp
  role: implementation
created_at: '2026-11-03T05:34:00Z'
updated_at: '2026-11-03T06:26:40Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---
# vLLM Ascend共享Kernel helper：模板命中、布局搬运与mask/PSE约束

## 复用前证明实际模板实例

本文提取固定Main `ceac1a2`的`csrc/common/include/kernel`20个共享头，覆盖其Device helper实际实现；它们没有独立Host入口，不构成完整Operator或任意模型/平台支持证明。源码中MLA preprocess另有同名`op_kernel/kernel`目录，不能见到相同include字符串就认定解析到本卡这套文件；真实caller、include顺序和模板参数是复用前置证据。

iterator.h的gm_to_l1、l1_to_l0_a/b、其v1变体、l0c_to_gm/l1等通用构造函数为空；mma.h主模板的两种构造也为空，仅IsTransposeA=false的偏特化调用Mmad。未命中实现仍可能通过C++编译，表现为没有搬运或乘法。Agent应记录ArchTag、dtype、转置、源/目的layout及实际偏特化，而不是把模板名字存在当作自动fallback。

| 选择点 | 固定源码的实际边界 |
|---|---|
| HardwareInfo | ArchType列V220/V200/M200，但通用模板返回同一组固定值：UB192KiB、L1 512KiB、L0A/B64KiB、L0C128KiB、L2 192MiB；不是平台查询或全设备容量证明 |
| AsdopsBuffer | 在本地memory position的地址0构造LocalTensor视图，GetBuffer按uint8 tensor的字节offset再reinterpret；没有TPipe分配、重叠检测或越界保护 |
| 编译宏 | C220_VEC只初始化UB视图，C220_CUBE初始化Cube侧视图；其他非clang分支才全初始化。不能假定每种编译方式都有同样有效的tensor槽位 |
| MMA | false转置特化转发m/n/k与initC到Mmad；bias重载构造C2视图。true转置主模板不会替caller做转置 |
| INT32→INT32 GM回写 | V220/ND特化仅在`__DAV_C220_CUBE__`内调用Fixpipe，外面没有else计算；不能推广为所有编译目标都执行 |

资源常量l2BW=5/hbmBW=1只是源码启发式比例，不是实测带宽；bias/fix buffer等常量也不能代替目标SoC查询。更改资源分区时，offset、padding及同时存活的数据块必须一并重算。

## 搬运布局、tail和大stride分支

共同单位来自32B block和512B fractal，按sizeof(dtype)换成元素数；部分API参数又窄化成uint16。caller必须区分逻辑有效尺寸、对齐尺寸、tensor offset、block gap和实际buffer容量，不把65536统一解释成每个接口的字节上限。通用原则见[ND/NZ随路变换](../../../../ops/ascendc/guides/data_movement/nd_nz_transform_and_block_placement.md)。

| helper路线 | 实际地址组织 | 接入检查 |
|---|---|---|
| GM ND→L1 ND | 一段DataCopy，长度ceil(nTileActual*dTileActual / BLOCK_SIZE) | 不按dVal逐行走stride；调用者须确保tile本身连续且末块可读 |
| GM NZ→L1 NZ | 每个D分块搬nTileActual，src gap=nTileCeil-nTileActual | gap<65536用多burst，否则逐D块算GM/L1偏移，目标紧密排列 |
| GM ND→L1 NZ | dVal<65536使用Nd2NzParams；大stride逐行复制 | 大分支为GM[i*dVal]和L1[i*BLOCK_SIZE]，仍须正确nTileCeil目的fractal stride |
| GM ND→L1 ZN | 小stride同样使用Nd2NzParams | 大stride循环中源/目的基址未加i偏移，不能直接当作NZ那条已验证逐行fallback；这是静态差异，未复现数值故障 |
| UB NZ→GM NZ | 逆向分D块回写，目的gap按nTileCeil-nTileActual | 大gap走逐块offset；未实现任意布局变换 |
| GM/UB及UB/GM align包装 | 转发DataCopyExt/Pad参数，长度和gap为对应重载单位 | GM→UB的isPad=false，传入left/right不等于填0；UB→GM并不消费这些padding数，尾部由caller裁剪 |

L1→L0的ZN/NZ/ZZ/VECTOR实现依不同偏特化调用LoadData或LoadDataWithTranspose，循环次数常用`tile/block`整除，目的gap可能传`dstStride-1`。tile对齐、非零stride及重复次数范围必须在Host/caller证明；这些helper没有自己的任意tail处理。INT8 NZ转置B走专用LoadDataWithTranspose，不能用FP16的fractal宽度代替。

L1→bias table按64B块、L1→fix buffer按128B块上取整。L0C→L1的INT32→half用VDEQF16及deqTensor；L0C→UB的对应特化用VDEQ16。L0C→GM在FP32→FP16/BF16、INT32→FP16或无量化回写间选择不同Fixpipe模式，C220和非C220使用不同参数结构。若没有正确准备dequant资源或输出布局，存在helper重载也不能补全精度合同。

## SIMD wrapper依赖外部mask和同步

simd.h将Add/Mul/Div/Exp/Sub/Max/Min/Sqrt/Log、广播与归约转发到AscendC基础API，多数使用`<...,false>`并传mask占位0，不在wrapper设置完整有效mask或PIPE屏障。caller须确认其前后mask模式、repeat与stride；wrapper返回不意味着跨MTE/Vector数据已经可见。common.h的SET_FLAG/WAIT_FLAG/PIPE_BARRIER只是直接宏展开，没有自动事件分配或生命周期管理。

conv_v仅FP32→BF16显式RINT，其他类型默认CAST_NONE；convr_v统一RINT。WholeReduceMax在C220_VEC分支才显式传ReduceOrder，其他分支用API默认。不能把这两组转换/归约一概视为相同舍入和输出顺序。

common_func的常量版CeilDiv在加法溢出时返回原dividend，运行时版在除0/溢出时返回类型最大值；util.h另一个CeilDiv除0却返回0。RoundUp也可能在溢出/align0时原样返回。应在使用这些值分配UB、算loop或地址前检查不变量，不能把“helper没有抛错”视为尺寸合法。

## Dropout布尔mask与bit mask是不同存储协议

ComputeDropOffset按B、N2、G、S1/S2块索引及vecCoreOffset合成逻辑元素偏移。boolMode经BoolCopyIn按字节mask搬入；另一条按8bit/byte换算GM偏移和S2跨度。非8对齐bit offset、S2尾部及batch/group分片必须由caller核准，不从函数名推断所有bit起点都安全。

BoolCopyIn对常规stride选择DataCopy或DataCopyPad，paddingValue设1；特别的totalS2Size=32/alignedSize=64还把UB目标gap改1。大源gap使用Ext参数。bit分支的padding设置不同，不能将mask尾部统一按0处理。

ComputeDropMask为bool和bit分别计算maskLastAxis，bit路线不满足32B相应对齐时使用DROPOUT_MODE_BIT_MISALIGN。keepProb直接转给AscendC DropOut，没有在本头校验范围或处理除0；hasDrop=false时copy/compute模板均为空操作，也不会复制src到dst。

## PSE/ALiBi要保留位置、广播与临时量寿命

PseInfo区分完整S1*S2、1*S2广播、BN/N slope和编码ALiBi。PseComputeOffset包含batch/head/group、S1块及vecCoreOffset、S2起点；pseBSize=1时batch偏移归0。1*S2分支用累计s2SizeAcc定位batch，不能替换成固定s1*s2跨度。

完整bias/slope执行逐元素Add，1*S2路线按S1广播；广播把S2拆成至多64个FP32元素的256B操作，再把S1 repeat拆成至多255。代码中block/repeat常量按FP32定义，泛型T并不自动重新计算所有单位。非对齐copy分支不自动初始化完整padding，后续computeSize不能越过真实有效区或依赖未写尾部。

编码ALiBi只在块与下三角相交时计算；TND与非TND用不同row/column回绕和threshold，readS2Size还受pseS2Size-k截断。qStartIdx/kvStartIdx会进入slope位移，不能在prefix、chunk或多请求复用时一律置0。

slope路径把辅助FP16索引图cast后加`kv位置-q位置`，取绝对值，可选sqrt，再乘负slope；BN slope另按batch索引。部分函数仅needCast=true时执行这些步骤，类型不同却needCast=false可能不填最终dst；必须按实际调用组合证明，而不是把needCast当作任意可关优化。

PseInnerAlibiCreate仅对inner两类型生成FP16辅助图，每行用CreateVecIndex后通过V_MTE3写GM，再MTE3_V/MTE3_S等待才复用UB/推进标量。把辅助图缓存跨图重放或改tile时，要保存其尺寸、生成完成和读者寿命。这里没有自动完成整个Attention的缩放、softmax、dropout或最终回写；outer mul/add的枚举也不能证明caller数学顺序。

## 新kernel复用时的最小证据

保留实际include路径、模板实例和编译宏，列出每条GM/L1/L0/UB边的shape、dtype、format、offset单位、tail和padding；随后核对mask状态、精度转换、事件及资源同时存活范围。用坐标编码输入检查大stride、非整块tail、转置和多head/group位置，再验证真实SoC数值与性能。本次未构建或运行上游/NPU；共享helper源码已提炼，具体Host/POD/launch、外部基础API实现和完整CV/VV Operator闭包继续待补。

## utils与common同名头：先固定include解析结果

追加范围是`csrc/utils`19份剩余源。对照已完整读过的common基体，完整审阅全部技术代码差异；没有将同名视为二进制ABI相同。utils的dropmask、pse和transpose tiling POD三份与common的归一技术代码相同，作为重复实现skip，复用前文语义；这不证明两个库由同一目标编译或共享全局状态。

| utils与common的差异 | 对适配/诊断的影响 |
| --- | --- |
| utils BoolCopyIn没有common的源gap大于UINT16_MAX时Ext搬运分支 | 不能将common的大stride处理能力搬到utils；需核对实际DataCopyParams字段范围与caller门禁 |
| utils fallback普通GE→ACL dtype映射没有FLOAT8_E4M3FN分支 | 该类型落普通映射默认FP16，不能由common新增FP8映射推出utils正确；矩阵专用转换是另一条API |
| utils fallback_comm直接include runtime/base.h | 不含common的rt_external_base.h可用性回退；SDK头布局变化要分别核对 |
| utils tiling registry仅按op_type注册 | 没有common新版按SoC二级registry，能力应由模板IsCapable/caller保证 |
| utils指定priorities遍历 | 非SUCCESS继续尝试其他priority；一般遍历则只在GRAPH_PARAM_INVALID时继续。不能把一般分派错误退出规则套给显式priority列表 |
| utils tiling枚举 | layout只有BSND/SBND/BNSD/TND，没有common新增NTD_TND；枚举/结构体不能跨版本直接强转 |

两套fallback的共享风险仍见[GE/ACLNN fallback](vllm_ascend_ge_aclnn_fallback_contract.md)：静态符号缓存、普通Tensor storage shape/ND视图、矩阵格式转换、转换对象及workspace寿命要按实际重载检查。utils读取GetPlacement但没有据此另造存储；不能把该局部变量视为完成Host/Device拷贝。两套source目录、命名空间和宏日志不同，查到同名GET_TILINGKEY/ConvertType并不证明命中相同实现。

utils TilingBase按shape/attrs→platform→IsCapable→op tiling→library tiling→workspace→PostTiling→SetTilingKey执行，IsCapable为false才返回GRAPH_PARAM_INVALID。Reset仅更新context，不清除全部成员；复用对象须由具体模板保证旧tiling/资源状态不会残留。registry指定priority用map下标取得函数，没有自行证明所请求priority必已注册；缺失priority不能直接当成无害跳过。transpose helper的4D数组索引、H/N整除和十进制tiling key规则与[ONNX/tiling桥接](vllm_ascend_onnx_ge_tiling_bridge.md)相同，仍不提供rank/除0/溢出自动校验。

## IPC同步flag：地址、epoch与可见性必须共同匹配

`Moe::CommArgs`容纳384 rank槽，peerMems、send/recv counts和displacements均是调用者提供的固定数组；常量区划为首2MiB flag、100MiB数据、两组ping-pong、32B对齐和最多48core，不是平台实际查询或所有集群拓扑的支持证明。batch/hidden/topk/shared/expert字段没有全部缺省初始化，不能把零初始化部分数组推广到整个对象。

SyncCollectives以每flag四个INT64即32B为单位，inner区域从shareAddrs[rank]起，outer紧随`blockNum*4`个INT64。eventID以及rank/block必须与分配容量匹配，类本身不做越界、rankSize一致性或共享地址初始化检查。CalEventIdByMulBlockNum只计算multiplier*blockNum+targetCore，没有资源注册。

flag合成是`uint32(magic)<<32 | int64(value)`。等待同时检查高32位magic一致以及完整值达到阈值，不能只比较eventID，也不能重用旧epoch导致ABA式误通过；负value符号扩展等输入域需由caller限制。SetFlag只设置暂存的第一个INT64，但传输32B，其余槽不是额外有效状态；调用者至少提供实际DMA长度的UB空间，不能按GetWithOffset的逻辑1元素估算完整scratch。

SetFlag先等MTE3_S、MTE2_S，再写标量并经S_MTE3发布，最后等MTE3_S；读取经MTE2_S后才GetValue。把这些依赖删除或把标量写入等同于跨rank可见，会破坏协议。WaitOneRankPartFlag记住已通过前缀，后续只拷贝未完成后缀，隐含已通过flag不会倒退/被并发覆盖；多阶段复用必须以epoch和生命周期证明这个条件。

普通WaitInner/Outer/AllRank循环没有超时、取消或重试。Check接口只读一次，适合caller自己调度；并不代替后续同步。跨rank轮询按(rank+r)%rankSize错峰读，仅是地址顺序选择，没有证明拓扑带宽收益。GetChunkFlag严格匹配完整值时返回WAIT_SUCCESS常量；GetChunkRecvLen则要求magic一致且低32位非0，返回低32位长度。timeout是轮询次数乘MAX_WAIT_ROUND_UNIT，不是微秒；负值、溢出保护命中或0可能在第一次未满足读后就返回。超时返回最后读到的原flag，caller不能把任何非零返回当成成功或有效长度。

## 原子状态、HCCL资源视图与诊断时间

CpGM2UB/CpUB2GM把指针包装成uint8 tensor，所以size是字节；CopyUB2UB的calCount按T元素，二者不能互换。SetAtomicOpType只为ADD/MAX/MIN设置对应状态，default清空，MUL分支为空；它不会实现乘法原子，也不会在该分支清除先前ADD/MAX状态。原子模式恢复、事件与buffer不重叠均由真实调用链负责。

moe_distribute_base主要冻结HCCL通信资源结构：rank、window、remote resource、topology、AICPU notify、AiRMA队列和dataplane capability是外部生产的数据，不是本头自动初始化/注册。硬编码的长度、padding、sizeof字段和version都要与实际HCCL生产端一致；不能仅因C++结构能编译就推断跨SDK ABI兼容。

GetDataplaneMode缺capability默认AICPU，仅当bitmap bit0x04存在才选AIV；没有将HOST位解码为HOST，也没有消费capabilitySize完成边界校验。cacheWriteThrough将首尾按cache line向下对齐并用包含末端的循环清理；即使length=0也触及包含起点的cache line，不宜把它当作任意零长no-op。GetCurrentTimestampUs用固定GetSystemCycle()/50，RecordRankCommDuration仅把时差的INT32写到每rank INT64槽低32位；时钟换算、溢出和累加解释要与实际设备/消费者核验，不是实测跨设备计时基线。

## 构建和日志也是可诊断性的条件

utils CMake创建tiling/proto两个INTERFACE头目标；BUILD_OPEN_PROJECT增补不同experiment SDK include并设置OP_TILING或OP_PROTO、[Custom]日志标签，非open构建才安装到include/ops_adv/utils。这个目标本身没有编译fallback_comm.cpp；实际链接与include优先级仍须看消费目标，不能把目录存在等同于进程已经加载。

OPS_ERR_IF要求condition类型恰为bool，命中后执行显式EXPR；不是自动抛异常。VECTOR/CUBE错误分别报E89999/E69999，普通OPS_LOG_E报EZ9999且触发inner错误上报；WITHOUT_REPORT不报。日志受Alog级别控制，包含文件、行、子模块、线程和op信息，长日志受16000字节临时区及MSG_LENGTH分段。找不到输出时先核对编译定义、级别和真实include，而不是假定Host没有执行。

本节只完成共享helper的源码语义生产；尚未证明某个模型/MC2调用已完整消费这些类，没有执行上游、通信、图或NPU。基础DMA/cache/事件API、实际HCCL资源ABI和通信数值/性能仍属于后续Operator/CV/VV闭包。

## MoE局部CATLASS preload-A/L1-B与Regbase双寄存器

追加完整技术代码阅读MoE common的BlockMmadTla预载变体532行和Regbase147行。它们与前述公共iterator不是同一实现，也不补齐外部CATLASS/TLA/TileCopy/TileMmad的CV闭包。本次未展开外部模板或执行编译/数值测试。

MmadPingpongTlaPreloadAL1B缺省L1A/B、L0A/B各两stage，L0C一stage。static_assert要求L1/L0静态tuple、M/N tile一致、L0_K≤L1_K及各资源stage总字节不超ArchTag容量；UnitFlag开启时L0C只能一stage。输出layout仅RowMajor，或half/BF16/float的zN；CATLASS_ARCH2201另对M/N/K按相应dtype位数检查32B对齐。这些是模板约束，不是动态实际shape和所有硬件资源查询。

构造在AIC侧划分L1A/B字节区、L0A/B/C视图及event ID。preSetFlags为L1槽发布MTE1_MTE2、L0槽发布M_MTE1、非UnitFlag的C发布FIX_M；finalWaitFlags成对等待，UnitFlag+RowMajor还切换MMLayoutTransform并恢复。析构为空，不自动执行finalWaitFlags；真正caller须成对安排初始化、退出与异常资源寿命。

算子只从GM预载A，B的GM→L1拷贝在本变体中没有执行；inner直接从传入tensorB取L1→L0 tile。虽然仍建L1B槽、tensorTileB及相关事件，但这些局部对象不代表数据已被填充。caller必须先证明B已经在所需L1布局就绪，不能把此变体当普通GM A×GM B的全套双缓冲GEMM。

每个K-L1块预取下一A槽，L0按M/K/N循环加载A/B、在首K项initC，后续累加，释放对应MTE事件并滚动stage。UnitFlag非末次为0b10、末次0b11，非UnitFlag另用M_FIX/FIX_M围住回写；2201与3510用不同TileCopy输出别名。未定义其他架构输出分支，不能由模板ArchTag可填任意类型推断所有分支均完整。

需要保留两个caller核验点：AtlasA2的实际M=1会把局部mL1Actual调16，GM A tile却仍按原M取，复制/padding/copy-out职责不能忽略；多K-L1块时B取tile坐标只见kL0Idx*L0_TILE_K，没有加kL1Idx全局偏移，而所建下一B tile未消费。因此任意K>L1_TILE_K的B推进不能由循环名证明正确，须对照实际调用/K域或修正实现后再测。本卡不把静态疑点当已复现错误。

Regbase helper把一个half/BF16寄存器按ZERO/ONE两半转FP32，计算Mul/Mins/Exp/Sub/Add/Compare/Select后再合并；FP32→half的两半均CAST_ROUND，但一半ZEROING、另一半MERGING，调用顺序是先ONE再ZERO，以保留已填一半。它与其他头的RINT/TRUNC不是同一舍入合同。LoadIn广播根据是否float选择B16/B32分布；StoreUnAlignOut会调用Post收尾，但mask、copyNum、有效tail以及跨MTE屏障仍由caller提供，不会自动验证UB范围。
