---
type: Guide
title: vLLM Ascend Indexer FP8 epilog：块内尺度、原位页写与padding边界
description: 沿IndexerCompressEpilogV2的Host与单/多行Device核对128元素FP8尺度、分离K/FP32-scale区、uint8
  page stride和原位cache发布；识别-1跳写、UB分行、队列与overflow control静态风险，保留生成ACLNN和真机数值验证边界。
tags:
- task.implementation
- task.debugging
- topic.attention
- topic.kv_cache
- topic.precision
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/indexer_compress_epilog_v2/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/indexer_compress_epilog_v2/op_host/CMakeLists.txt
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/indexer_compress_epilog_v2/op_host/indexer_compress_epilog_v2_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/indexer_compress_epilog_v2/op_host/indexer_compress_epilog_v2_proto.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/indexer_compress_epilog_v2/op_host/indexer_compress_epilog_v2_tiling.cpp
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/indexer_compress_epilog_v2/op_host/indexer_compress_epilog_v2_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/indexer_compress_epilog_v2/op_kernel/indexer_compress_epilog_v2.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/indexer_compress_epilog_v2/op_kernel/indexer_compress_epilog_v2_base.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/indexer_compress_epilog_v2/op_kernel/indexer_compress_epilog_v2_multi_row.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/attention/indexer_compress_epilog_v2/op_kernel/indexer_compress_epilog_v2_single_row.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding_meta.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/device_op.py
  role: constraint
created_at: '2026-11-03T04:54:41Z'
updated_at: '2026-11-03T04:54:41Z'
platforms: []
aliases:
- IndexerCompressEpilogV2
- IndexerCompressEpilogV2SingleRow
- IndexerCompressEpilogV2MultiRow
- VFProcessDynamicBlockQuant
- indexer_compress_epilog_v2_npu
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend Indexer FP8 epilog：块内尺度、原位页写与padding边界

## 框架执行facet与范围

新模型把压缩后的Indexer K发布到共享页，或切换FP8后出现scale错位、padding污染和图地址问题时，沿本卡核对。固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文读取indexer_compress_epilog_v2族10文件1159行，并有界读取Torch/Meta与DeviceOperator实际调用。复用root实际“压缩缓存”结果、全文对照[模型Indexer接线](vllm_ascend_v4_indexer_contract.md)，保留其权重、Hadamard和多流owner，本卡补实际cache writer。

OpDef只注册ascend950，不能由同名类默认socVersion或通用FP16输入推导A2/A3可用。CANN版本、生成ACLNN bridge、完整模型和SDK行为未闭合，保持draft/空平台；未执行上游、UT、编译、JIT、NPU、数值或性能测试，不作为完整Operator验收。

## 发布到同一backing，不返回量化K

Torch schema为可写indexer_compress_cache加只读x/slot_mapping，返回void；实际传cache.stride(0)为block_stride。Meta直接return，不分配、不校验cache内容。cache dtype声明UINT8，x为FP16/BF16，slot为INT32；cache输入/输出同名且IgnoreContiguous，但这不开放任意内轴view。

当前DeviceOperator的FP8分支单独量化query；K非None时，把indexer_full_cache.view(uint8)、原始压缩K和slot交给fused epilog，内部一并写K及scale。组合函数仍返回原kv和None scale，多流part1同样返回(kv,None)，part3为空操作。None是“不再单独写scale”的协议，不是没有反量化scale；调用者不要再量化/覆盖同一页，或把返回原kv当实际量化cache内容。

Q的torch_npu动态量化不在该kernel内，K已完成的Hadamard/压缩/norm也来自上游；本epilog只做块量化与scatter。不能用主KV量化格式替代Indexer K的128元素scale块，也不能把fp32 scale区当E8M0、FP16或每tensor一个值。

## 物理页布局与offset单位

Host只接受layout2；cache为四维且第三轴1，cacheBs取第二轴、cacheD取第四轴；D来自x末轴，scaleCol=ceil(D/128)。行数T由slot_mapping所有维相乘取得。非零block_stride需至少cacheBs*cacheD，为0则用此紧凑块大小；Torch传入的是UINT8 view的stride(0)，在该dtype下单位为字节。

对flat slot s，block=s/cacheBs、row=s%cacheBs：K写offset=`block*blockStride+row*D`，FP32 scale写offset=`block*blockStride+cacheBs*D+row*scaleCol*4`。每块先集中存全部K行，再集中存全部scale行，不是每行D字节后紧挨自己的4字节scale；物理cacheD必须容纳整个协议，不能仅看到shape末轴就按逐行交错存储解释。

这里没有充分校验x总元素数与T*D一致、cacheD容纳D+4*scaleCol、slot范围、正block ID或任意内stride。调用者必须检查真实共享backing和几何。warmup调用构造小dummy cache只是profiling路径源码，不能拿它当真实有效slot和scale容量的通用示例。

## 每128元素FP8动态尺度与特殊值

Device将FP16/BF16转FP32，按最多128元素组做绝对最大值，正常有限非零组scale=amax/448，再除scale并用CAST_RINT转E4M3FN。scale按FP32保存。代码按64-lane分两半折叠处理128组及最后不足128的尾部，不把组内scale误当整行D共享一个值。

实现显式生成0/Infinity、用比较掩码处理非有限中间值；零scale没有统一加epsilon的语句，对除法产生NaN的元素会选择原输入。不能把简化finite公式扩成NaN/Inf、全零、极小值及所有舍入模式已经满足另一后端契约。新格式接入时分别比较量化字节、scale与反量化结果，不能只看dtype相同。

## Host分行和实际两条Device路径

Host按T/AIV估算每核行数，增加rowFactor直至双缓冲x、FP8输出、FP32 scales和INT32索引scratch超过UB。x行对齐16个half，量化K对齐32字节，scale对齐8个float；rowFactor1选key20020单行，其余选20021多行。POD保存D、cacheBs、scaleCol、首/尾核行数与loop/尾行因子、rowFactor及blockStride，workspace声明32字节。

本Host没有展示完整coreNum/空T/不足容纳一行UB的拒绝：rowFactor可能退0，而后有取模/分行运算。不要把空slot数组或任意大D当自动no-op；在真实入口先拒绝/按框架专门空路径处理，并记录实际key、core、rowFactor及UB资源。这里只报告静态风险，未执行确认故障。

多行路径先逐行过滤slot=-1，把有效x紧凑放UB并保留原slot列表，按validIdx量化后逐slot写回；压紧的是临时计算行，不能重排上游真实请求索引。无效行不清cache，目标原字节保留，因此不能依赖padding行把旧KV或scale自动归零。重复有效slot也没有全局去重/冲突仲裁，caller应保证写入责任。

单行路径在读取slot前已AllocTensor；slot=-1时直接continue，所读分支没有相应FreeTensor。单/多行不能只因数学公式相同便视作相同队列寿命，连续padding和混合padding必须定向验证，不能将这份源码未执行的风险写成已确认NPU死锁。

entry检查workspace及GetUserWorkspace均非空，缺失时直接return、不交付cache写入；输出参数indexer_compress_cache_out未在body使用，实际写输入cache地址。已有输出别名/原位schema是接入条件，单独分配另一个out地址不能令kernel自动写到它。

## 队列、control与构建边界

x队列VECIN和K/scale队列VECOUT通过EnQue/DeQue/FreeTensor衔接MTE与Vector，三组按深度2分配，多行另有INT32 slot scratch。公共CopyIn/Out使用DataCopyPad，明确字节长度与burst；scale经ReinterpretCast写UINT8页。源里存在手写S_MTE3等flag，不能删除队列/同步后以shape一致宣布相同实现。

Init将FLOAT_OVERFLOW_MODE_CTRL置0；entry保存旧值，但命中两条key后在恢复语句之前return。因此不能声称正常路径已有显式恢复；该control是否由kernel边界/SDK隔离还需实际栈确认，尤其与相邻算子/图复用时取证。不要未经验证把后续算子差异都归因于此处。

CMake将Host/注册加入aclnn构建，关闭自动同步并保留movemask/relocatable选项；proto的infer shape/dtype直接成功，没有填写或检验输出。生成桥、编译模板宏DTYPE_X/DTYPE_INDEXER_COMPRESS_CACHE与安装产物身份仍需核对，源文件存在或Meta成功不证明实际binary包含可执行路线。

## Agent验收与未闭合内容

先对齐缓存页K/scale区域、uint8 block stride、x/slot行数、有效slot唯一性和上游旋转/压缩完成依赖；再按单/多行、尾128组、-1连续padding、全零/非有限输入与页边界检查真实字节/数值/内存。最后与QLI读取尺度的ABI和多流事件对齐，测选择前准备及整体时延。完整Q量化、Compressor数值、主Indexer TopK、外部AscendC primitive和图/stream执行仍未完成运行验证，本卡不据10源已读外推整个Indexer族完成。
