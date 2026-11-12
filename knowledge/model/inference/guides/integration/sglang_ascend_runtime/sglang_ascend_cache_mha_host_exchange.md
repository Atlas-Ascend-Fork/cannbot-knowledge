---
type: Guide
title: SGLang MHA HiCache的Ascend全层搬运与布局守卫
description: 说明MHA Host池kernel_ascend仅支持page_first_direct、首层触发全层H2D、D2H逐buffer分组和连续多层设备缓冲区要求。
tags:
- task.implementation
- topic.memory
- topic.data_movement
status: draft
sources:
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/pool_host/mha.py
  role: primary
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/pool_host/common.py
  role: supporting
- resource: https://github.com/sgl-project/sglang/blob/dadff253c0aa8c7456b351cb9d2c282a8e513958/python/sglang/srt/mem_cache/pool_host/base.py
  role: supporting
created_at: '2026-11-08T12:04:34Z'
updated_at: '2026-11-08T12:27:46Z'
platforms: []
---

# SGLang MHA HiCache的Ascend全层搬运与布局守卫

kernel_ascend分支要求page_first_direct，其他布局抛ValueError。它使用设备连续多层K/V与Host page-first视图，通过transfer_kv_dim_exchange换维搬运；CUDA的k_data_ptrs/v_data_ptrs数组不参与这条路径。

load_to_device_per_layer虽按层调用，在host_layer_id==0时即遍历_npu_transfer_buffers搬运全部层，后续层调用不重复搬运。buffer_info各自返回K/V，按设备层数切出Host相应layer区间；D2H备份也遍历同组并指定D2H方向。因此不能把方法名解释成每次只传一层，也不能把多buffer组当成一块无边界内存。

非draft层号先按target_layer_num过滤。启动、池组装和controller事件必须保证首个有效层触发以及计算消费前的依赖；仅调用底层copy不能证明上层恢复生命周期闭合。该实现没有按每层分段重叠的AscendC分支，不可把MLA稀疏copy的优化直接推广为MHA默认行为。

验收应覆盖多buffer组、首层/后层、空集合、完整页索引与不同K/V几何，检查恢复后attention精度和传输是否重复。回退需要同时改IO后端与匹配布局，而不是仅换kernel_ascend字符串。

## 证据与验证边界

本卡记录固定提交的NPU分支实现合同，来源没有为本机制提供完整产品验收矩阵，保留草稿和未定位平台；源码路径存在不证明任意昇腾型号可用。本次知识摄取未执行上游代码、编译、模型推理、真机、数值或性能测试。

## Host内存分配和退出

ALLOC_MEMORY_FUNCS按设备type字符串分派，NPU用torch.empty(pin_memory=...)，不是cudaHostRegister。alloc_with_pin_memory实际忽略传入allocator对象，不能认为换storage allocator必然改变这一路的物理分配。HostKVCache.destroy的显式unregister只针对CUDA/HIP，NPU pin-memory由Torch管理；退出仍需等待传输消费者。
