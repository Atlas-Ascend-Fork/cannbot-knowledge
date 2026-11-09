---
type: Guide
title: vLLM Ascend Compressor执行：压缩边界、FP32状态与双架构投影
description: 核对Compressor metadata槽位与arch32/arch35执行链：投影/Gate+APE、跨步FP32状态页、按通道压缩softmax、RMSNorm/RoPE；区分Host允许值、实际模板、full-load与cycle未选分支及输出shape/容量风险。
tags:
- task.implementation
- task.debugging
- topic.attention
- topic.kv_cache
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor_metadata/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor_metadata/op_host/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor_metadata/op_host/compressor_metadata_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor_metadata/op_host/compressor_metadata_tiling.cpp
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor_metadata/op_host/compressor_metadata_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor_metadata/op_kernel/compressor_metadata.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor_metadata/op_kernel/compressor_metadata.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding_meta.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/attention/dsa_v1.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/README.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_host/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_host/arch32/compressor_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_host/arch32/compressor_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_host/arch35/compressor_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_host/arch35/compressor_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_host/compressor_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_host/compressor_proto.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch32/compressor_block_cube_full_load.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch32/compressor_block_cube_perf.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch32/compressor_block_vec_full_load.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch32/compressor_block_vec_perf.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch32/compressor_comm.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch32/compressor_kernel.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch32/compressor_kernel_full_load.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch32/compressor_kernel_perf.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch32/compressor_template_tiling_key.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch32/compressor_tiling_data.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch32/compressor_tools.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch32/compressor_vector_comm.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch32/rms_norm.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch32/rope.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch32/soft_max.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch35/compressor_block_cube.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch35/compressor_block_cube_full_load.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch35/compressor_block_vec.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch35/compressor_block_vec_full_load.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch35/compressor_comm.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch35/compressor_kernel.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch35/compressor_kernel_full_load.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch35/compressor_template_tiling_key.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch35/compressor_tiling_data.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch35/compressor_tools.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch35/vf/vf_add.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch35/vf/vf_mul.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch35/vf/vf_rms_norm.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch35/vf/vf_rope.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/arch35/vf/vf_softmax.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/compressor/op_kernel/compressor.cpp
  role: implementation
created_at: '2026-11-03T04:51:43Z'
updated_at: '2026-11-03T06:01:54Z'
platforms: []
aliases:
- CompressorMetadataKernel
- CompressorMetadataTilingFunc
- compressor_metadata_out
- BuildCompressedPrefix
- WriteInvalidTile
- CompressorKernelPerf
- CompressorKernelFullLoad
- CompressorBlockVector
- SoftmaxDnVF
- stateCacheStrideDim0
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Compressor执行：压缩边界、FP32状态与双架构投影

## 框架适配责任

新压缩模型把cache请求边界转成压缩输出的RoPE与slot，或在固定graph容量下处理实际请求少于bucket时，核对本卡。固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，完整读取compressor_metadata族7文件908行的程序结构（去注释投影，未声称原始全文），并有界读取真实Torch/Meta及Python caller。复用root实际“压缩缓存”查重，阅读全文[压缩器接线](vllm_ascend_compressor_state_cache_contract.md)后，将本Host/AIV执行facet独立成卡，保留其模型权重、FP32状态和V4/V4.1范围。

本组件只生产compressCos、compressSin和slotMapping，不做Compressor投影、softmax池化、norm、KV量化或存储。OpDef注册910b、910_93和950；没有本卡整链公开支持表、CANN版本或运行结果，保持draft/空平台，未执行上游导入、UT、JIT、编译、NPU、数值或性能测试，不宣称完整Operator闭包。

## Torch输出和caller缓存寿命

普通compressor_metadata要求正num_compressed_tokens，分配同输入dtype的`[N,1,1,D]` cos/sin，以及INT32 `[N]` flat或`[N,2]` block-offset槽；out版本返回caller给定的三个原位buffer，schema用a!/b!/c!标别名。Meta只分配符号shape，不运行Device边界计算或请求值校验。

Torch检查RoPE二维、同shape/dtype、非空，cu/start一维、页表二维，block_size/ratio/actual requests正且各表容量足够。out检查输出末轴D、首轴N、cos/sin同shape/dtype及slot格式；允许rank>=2不等于任意中间轴布局都被kernel实现。Device实际按`outputRow*D`紧凑地址写，建议保持普通入口的单例中间轴或明确二维连续view，不能据rank检查将`[N,2,D]`当完整输出。

Python get_or_compute_compressor_metadata要求cache_group_key，在当前ForwardContext.additional_kwargs按group memo结果；同子步各层复用，reset函数在复合forward下一子步前清缓存。key未显式拼ratio或每个tensor地址，caller必须保证同group当前子步的请求边界、页表、ratio与backing一致，不能跨子步沿用旧tuple。真实设备metadata readiness与cache/state分组等待仍由既有接线卡管理，memo命中不是当前stream数据已就绪证明。

## Host门禁与实际POD

输出cos/sin首轴N和末轴D正、shape/dtype一致；输入RoPE为同shape `[ropeRows,D]`。cu长度至少2，actualNumReqs正、小于cu长度，且不超过startPos与页表行数。kvBlockSize在(0,INT32_MAX]、cmpRatio在(0,UINT32_MAX]，slot格式只接受1/2。输出slot必须与N和格式匹配。Host不读取cu值验证全局单调/末值、start值或页ID真实物理范围，dtype元数据约束也不能替代这些值验证。

Host与Device POD依相同顺序保存14个uint32：numRows、numReqs、actualNumReqs、ropeRows、ropeDim、kvBlockTableStride、kvBlockSize、slotMappingFormat、cmpRatio、usedCoreNum、tileRows、ropeRowBytes、ropeRowBytesAligned、slotCols。块表stride来自shape[1]，不是任意torch stride；输入AutoContiguous/生成bridge的实际拷贝和布局仍需运行栈核对。

FP32/FP16/BF16 key分别1/2/3，Device entry只按这三项实例化CompressorMetadataKernel<T>，声明AIV_ONLY，没有Cube计算；未知key没有显式写输出分支。手工伪造POD或放宽Host dtype不产生新kernel。

## Device按跨边界计行，不按本步token数取整

每个AIV先把actual requests的startPos与actual+1个cu值复制到UB，再以MTE2_S事件等候scalar可读。请求r的token数为cu[r+1]-cu[r]。当start>=0且长度>0时，其完成压缩行数为：

`floor((start+len)/ratio)-floor(start/ratio)`。

否则该请求贡献0。按请求生成前缀后，总有效行数截到输出容量N。N不足会截断，不自动扩容或报错；调用者应预留真实跨边界数量，不能只用`floor(len/ratio)`，例如start3、len1、ratio4会完成一行。

每核按ceil(totalRows/blockNum)取得连续有效行区间，先找到对应请求，再按请求段执行。该行的压缩位置=`floor(start/ratio)+请求内完成行序号`；RoPE读取位置=`compressedPos*ratio`，是原始压缩组起点，不是组尾、当前token position或压缩slot自身。cu用于本步请求行数，startPos是绝对前缀，混用会同时污染RoPE和缓存位置。

prefix累计用uint32，再经INT32 UB存取，Host没有证明所有累计和都不溢出；negative start或非正长度被视为无贡献，不应把静默跳过当正确请求语义。新框架仍需验证实际值与scheduler、缓存可见长度一致。

## 分页切tile与失效输出

每个请求段再次按tileRows和当前KV块剩余行数切tile，保证单tile不跨KV页。块表索引为`req*tableWidth+compressedPos/kvBlockSize`；块offset为`compressedPos%kvBlockSize`。块表列越界、block ID负数、flat最终slot超过INT32_MAX，或该tile最后RoPE位置越过ropeRows，整tile转失效路径，不只跳过最后一行。

flat槽写`blockId*kvBlockSize+offset`，block-offset写`[blockId,offset]`。后者可以避免flat乘法编码，但仍需下游正确识别block ID；Host/Device这里没有检查正block ID是否真的属于所分配物理页池。结果合法形状不是物理cache可写范围证明。

失效tile和有效区之后的padding都写cos=1、sin=0；flat槽为-1，block-offset为`[-1,kvBlockSize-1]`。第二列不是0，但第一列已经无效；消费者必须按协议屏蔽block=-1，不能只检查offset在范围内。单位RoPE不代表该行真实有效，不能把padding压缩输出写进缓存。

## UB账、搬运与同步停止点

令R=align32((actualReqs+1)*4)，A=align32(D*sizeof(T))，Tn=tileRows，S=slotCols。实际缓冲含三份R的prefix/start/cu，align32(Tn*S*4)的slot、align32(Tn*4)的块表scratch，以及cos/sin各两份Tn*A队列。没有额外GM workspace，Host写workspaceSize=0；这不代表输入连续化、输出或生成executor从不分配。

Host以每行`4*A+4*S+4`估计可用UB，并预留16KiB与对齐空间，tileRows限512和DataCopy block count上界4095。used cores取AIV数与ceil(N/64)的最小值，至少1；不是每请求一个核。UB不足或行/请求字节宽超UINT32时拒绝，改变ropeDim、dtype或actual请求数会改变tile计划。

有效RoPE每行搬运D*sizeof(T)字节，源stride为(ratio-1)*rowBytes，写回为紧凑输出；UB右侧按32字节补齐。scalar读块ID等MTE2_S，scalar写槽等S_MTE3，Duplicate初始化等V_MTE3，输出后等MTE3_S再释放本地tensor。源码关闭自动同步，必须保持这些实际flag/搬运顺序；本卡不声称已验证所有SDK版本的pipe可见性、DMA尾块、异步graph或跨stream正确性。

## Agent验证顺序

先对齐cache group/子步、cu与绝对start、ratio和真实N容量；再核RoPE原始组起点、flat/block-offset slot及负页哨兵，分别覆盖跨压缩边界、请求空行、N截断、页尾tile、无效块表与RoPE末端。最后对照实际Compressor/缓存writer的数值和写入范围。下面补齐Compressor族40文件19,558行的程序结构、同族完整差异及README；生成ACLNN bridge、安装SDK、数值/性能及并发graph运行仍未验证。


## Compressor与metadata的职责接缝

Compressor本体把低精度X分别投影为KV和Gate；Gate加APE，再沿每个压缩组的token轴、对每个D通道分别做softmax，以权重乘KV后沿该轴求和，最后逐输出行RMSNorm与末64维RoPE。它不是对head维做attention softmax。coff=2合并相邻组的两套投影；序列首部缺历史时KV补0、score补负无穷，不能用未初始化cache替代这个边界。

本次完整程序投影覆盖arch32/arch35的Host、入口、Cube/Vector、分片迭代器和VF，并逐份读取full-load差异；重复程序用同SHA基准及完整新增/删除映射复用。原始注释未逐字全读，来源表以program_body_complete记录，不将[1,N]范围当作raw FULL。README产品表列A3与950、排除A2；这只是一份固定源码说明，不能扩大本卡platforms或证明任意CANN/固件组合可用。

## Host允许值与可选模板矩阵

| 项目 | arch32 Host/执行代码 | arch35 Host/执行代码 | 适配时的实际停止点 |
|---|---|---|---|
| X与权重 | Host有FP16/BF16、TH/BSH路径 | Host限制BF16、TH | 两份模板选择列表都只列TH、BF16；Host分支存在不等于可生成其余key |
| 压缩率 | 常规2/4/8/16/32/64/128；DAY0_SCOPE另限4/128及三种典型组合 | 2/4/8/16/32/64/128 | 两者D仅128/512，H为1024–10240且512对齐，RoPE维64 |
| rotary/cache | Host有half/interleave，cache仅1 | rotary仅interleave；Device含cycle代码，Host/cache列表仍仅1 | 模板仅rotary=2、cache=1；不能因为helper有half/cycle实现就开放这些配置 |
| kernel模板 | 普通PERF、EMPTY_X，以及full-load实现/Host选择代码 | 普通实现、EMPTY_X与full-load代码 | 模板声明选择0/1，未列FULL_LOAD=2；BSH/full-load分支的实际生成与路由待核 |
| 小工作量 | Device SetBaseSize可进一步缩M、拆D | Device SplitK在M并行不足时拆H并在Vector加回部分和 | 优化配置改变中间GM与归约次序，不能复用另一架构的数值或内存估计 |

状态shape为[blockNum,blockSize,2*coff*D]，Wkv/Wgate为[coff*D,H]，APE为[ratio,coff*D]，normWeight为[D]。TH的cu为B+1前缀且必须从0单调、seqUsed在[0,cu差]，start为非负绝对token起点；Host主要验证shape/dtype，不读取所有值保证这些条件。迭代器把若干INT32值转uint32；负数、全空batch、错乱前缀不能依赖Device自行修正。部分循环寻找下一个非空请求并回绕，必须保证其工作配额与有效请求一致。

state_block_table在OpDef/Proto标可选，但Host按实际cache模式要求，Proto也读取这些required shape。不能从“optional”推导传None被完整支持。arch32要求stateCacheStrideDim0至少覆盖完整页跨度；arch35移除此检查，执行地址仍乘该stride，未获得任意stride的安全性证明。block_size范围1–1024来自Host/README；物理正页ID、页表列与backing容量还需caller证明。

## 输出分配与状态副作用

Device入口接收stateCacheOut却未将它传入计算类，真正写回的是输入stateCache；框架schema、别名与生命周期应按原位副作用处理，不能另给output tensor便认为输入不会变化。低精度cmpKV只写实际完成的压缩行；EMPTY_X入口直接返回，没有通用清零。固定容量padding是否被初始化必须由caller/后续metadata掩码闭合。

静态源中存在需要实证的shape接缝：README把cmpKV末轴写D，但Proto输出末轴取X的H，Host主要验证输出rank/dtype，Device按D紧凑写。TH Host还以默认seqSize重算cgSize，不能把这个字段直接当实际压缩行数。Agent应记录真实Torch分配shape/stride、executor推导与有效行数，验证padding/越界；本卡不宣称已经重现内存错误，也不擅自替上游修复。

## 状态页、跨组历史与输出坐标

普通路径先遍历cu定义的输入长度进行Cube投影，Vector再按seqUsed截取参与压缩/状态更新的有效部分。一个请求的完成行数仍为floor((start+seqUsed)/ratio)-floor(start/ratio)，不能将输入总T、ceil的中间组数和输出完成行数混用。TH输出按请求完成行紧凑拼接；BSH代码使用每请求容量及padding定位，这不解除TH-only模板限制。

连续页模式的状态地址单位是FP32元素：pageId*stateCacheStrideDim0 + pageOffset*(2*coff*D) + stateIdx*(coff*D) + channel，其中stateIdx=0是KV、1是加APE后的score。跨页分段搬运；写状态遇pageId=0跳过，读路径仍可读页0。页0应是协议中的有效占位/预置空间，不能把0同时当“读取不需要backing”。没有负页或上界通用检查，INT32负页转为uint64尤其需要Host前置拒绝。

当前组头不完整时从历史状态补齐；coff=2还读取前一压缩组，当前调用内跨Cube工作块的历史通过双缓冲GM tail cache或当前投影/UB补齐。不能只保存最终压缩KV代替FP32投影/Gate状态。arch35 cycle代码改成每请求一个物理块、按token modulo blockSize环绕，且只保存后续所需尾部；它是未被当前cache=1模板选择的代码边界，不是本快照已启用的新缓存后端。

RoPE的输入在本体已是“压缩完成行”的cos/sin序列；metadata负责从原始position采出它们。本体按紧凑压缩输出坐标读取，因此不能再乘一次ratio。归约后的FP32结果先RMSNorm，再旋转最后64维，非旋转前缀保留后转低精度；arch32最终Cast为CAST_RINT，arch35 VF也使用RINT、NO_SAT。FP32状态不等于全FP32推理：输入/权重、Cube乘加与最终输出各有独立dtype/舍入边界。

## 双架构内存、同步与数值诊断

arch32 PERF的X L1为2×128KiB、权重L1为4×64KiB，L0A/B各2×32KiB、L0C为2×64KiB；投影同时产生KV/Gate的FP32 GM中间结果。arch35普通代码改权重L1为2×128KiB、L0C为4×64KiB，LoadDataV2并按M/N/K尾块分片，SplitK部分和由Vector归约。full-load另有拆K和短BSH特化，不能把这些buffer数字当任意key可运行的资源保证。

GM workspace包含双缓冲的两份投影、coff=2尾部KV/score cache与FP32压缩中间结果，另外Host添加SDK workspace。Vector的32/64KiB scratch、输入输出队列及APE/norm缓存也占UB；Arch35用VF加法/softmax/乘加，队列布局与arch32不同。调ratio/coff/D/M或K拆分时，应重新核对每条队列、整组token容量及跨核部分和，不能只看输出大小估算峰值。

Cube以MTE2→MTE1→M→FIX各事件复用L1/L0，FIX发布投影后Vector等相应跨核flag；Vector消费完归还slot。压缩阶段完成后在有实际输出且到nSize组边界时SyncAll，再做RMSNorm/RoPE；全部事件收尾仍有wait。绕过空核参与、提前释放workspace或漏等旧slot可能破坏流水线。arch32和arch35的跨核flag基数、L0C槽数不同，不可直接复制事件常量。

arch32用列max/sub/exp/sum/div与ColumnSum，arch35 VF为8/16/32/64/128/256/512列分别分派，压缩组按4组展开并处理余组。AddVF仅col<=64或128/256/512有分支，MulReduce VF同样只有枚举宽度；未列宽度没有通用fallback。VF softmax先写exp到UB，再以LocalMemBar保证后续load可见；输入全无效、NaN/Inf、epsilon非正的完整策略没有由Host stub证明。模型适配需独立比对跨步切分、coff重排、K拆分归约、极端分数与长序列内存，源码审阅不提供精度阈值或性能收益结论。
