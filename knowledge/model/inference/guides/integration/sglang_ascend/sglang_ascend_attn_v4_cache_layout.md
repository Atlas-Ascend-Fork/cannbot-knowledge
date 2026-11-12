---
type: Guide
title: SGLang Ascend V4缓存：PA_ND压缩页、混合字节与状态ring
description: 区分SWA/C4/C128的NPU物理页、950混合FP8/BF16/scale行、indexer独立缓冲及压缩state生命周期。
tags:
- task.implementation
- topic.attention
- topic.memory
- topic.kv_cache
- topic.precision
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/dsv4_memory_pool.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/attention/ascend_dsv4_backend.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/hardware_backend/npu/dsv4/dsv4_allocator.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/static_kv_storage.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/deepseek_v4_memory_pool.py
  role: implementation
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/kv/router.py
  role: implementation
created_at: '2026-11-08T12:07:56Z'
updated_at: '2026-11-08T12:10:40Z'
platforms: []
aliases:
- DSV4NPUTokenToKVPool
- PA_ND C128
- Ascend 950 V4 cache
---

# SGLang Ascend V4缓存：PA_ND压缩页、混合字节与状态ring

## 布局与路由

NPU V4只接受原生KVLayoutV4，拒绝CUDA的V4.1 packed布局及不兼容的HiSparse C4类。SWA/C4/C128缓存按PA_ND形状[pages,kernel_page,1,D]保存共享K/V，不能把CUDA字段或压缩layer_id直接用于所有NPU buffer。

C4 kernel page为原始global page/4，与full页共享page id；C128是独立页族，kernel page由c128_page_size指定，必须正数且为16倍数。SWA访问使用当前PP stage的局部layer id，因为不同ratio的compress_layer_id可能重号。

## 950混合字节行

pre-950保持BF16 NoPE+RoPE；950行包含FP8 NoPE、BF16 RoPE和每64个NoPE一份E8M0 scale，字节数为nope+2*rope+ceil(nope/64)，再按128字节对齐。默认448+128+7字节补齐到640；外层dtype为FP8不代表全部字节都是同类浮点值。写入通过kv_compress_epilog，quant_group64、quant_mode2、roundscale=True、layout1；空输入no-op。

C4 indexer另有native PA_ND buffer：早于950为INT8 K/FP16scale，950为FP8 K/FP32scale。模型K与index K不能共享其scale布局。读取前等待layer transfer完成，防止异步传输未就绪。

## 压缩状态与所有权

compressor state是FP32固定ring，不由paged token allocator分配，只支持ratio4/128。C4按SWA物理页寻找状态；C128按request slot和绝对position，950还要求request bank容量覆盖全部请求ring。location0在显式state中是合法行，负sentinel映射至最后一个清零正dummy；不能把所有0当无效，也不能把负地址交给无符号硬件偏移。ONLINE_C128无原生实现而拒绝。

PD导出区分C4 KV/indexK/scales、SWA/state和独立C128页族；950 C4 state按请求行单独导出，发送/接收ring大小可不同并按逻辑token映射。此处只保留布局与状态归属，传输调度另看PD知识。

建议核对实际storage字节数、每层pointer stride、C4/C128 page id空间和request回收后state清零，再比较跨压缩边界输出。本次未执行布局dump或传输测试，不能从源码推断带宽收益或产品支持矩阵。

## 调用依赖补充

StaticKVStorage对NPU V4另注册AscendStateType.DSV4_C128；arch35再注册DSV4_C4_STATE，让P/D按逻辑位置独立映射本地ring，不能与pre-950共享SWA state布局混用。NextN draft state有独立位置组件，要求SWA-only、与target相同映射及几何；不混入target异构state字段次序。

KVLayerRouter只决定sub-pool/part/layer对应，不拥有allocation生命周期。read等待layer-wise load-back，store选择owner full_loc或非owner swa_loc，物理标志继续传递；不能用“路由成功”代替异步恢复已完成。基类clear_unaccepted_c128_draft_states明确清除未接受draft行，因为下次跨128组压缩可读到拒绝候选；C4会在读取前覆盖自己的候选槽。NPU派生pool仍需遵守此接受后清理协议。
