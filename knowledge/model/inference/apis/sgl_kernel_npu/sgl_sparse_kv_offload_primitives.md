---
type: API
title: SGLang稀疏KV卸载的注册内存、索引拷贝与槽位查找
description: 解释create_shm_tensor/free_shm/unidex_copy_inplace/slot_map_lookup的CPU与设备地址区分、逻辑行字节合同和进程内异步生命周期。
tags:
- task.implementation
- topic.kv_cache
- topic.memory
- topic.data_movement
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/sparsity_driven_kv_offload/ops.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparsity_driven_kv_offload/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparsity_driven_kv_offload/unidex_copy/op_host/unidex_copy.cpp
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparsity_driven_kv_offload/slot_map_lookup/op_host/slot_map_lookup.cpp
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparsity_driven_kv_offload/shm_allocator/shm_allocator.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparsity_driven_kv_offload/shm_allocator/shm_allocator.h
  role: header
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparsity_driven_kv_offload/shm_allocator/shm_allocator_op.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/legacy_kernels.cmake
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_shm_allocator.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparsity_driven_kv_offload/unidex_copy/op_kernel/unidex_copy_kernel.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/sparsity_driven_kv_offload/slot_map_lookup/op_kernel/slot_map_lookup_kernel.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/utils/torch_helper.h
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_unidex_copy.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_slot_map_lookup.py
  role: evidence
created_at: '2026-11-08T11:03:56Z'
updated_at: '2026-11-10T07:03:17Z'
platforms: []
---

# SGLang稀疏KV卸载的注册内存、索引拷贝与槽位查找

## 边界与入口

本模块只提供Kernel层原语，不含SGLang runtime cache manager或稀疏attention适配器。来源声明进程内注册内存生命周期、多进程每进程绑定单一NPU的部署模式；未给独立芯片支持表，故平台未定位、保持draft。

```python
from sgl_kernel_npu.sparsity_driven_kv_offload import (
    create_shm_tensor, free_shm, unidex_copy_inplace, slot_map_lookup)
create_shm_tensor(shape, dtype, device_id=0, name="")
free_shm(device_id=0)
unidex_copy_inplace(src,dst,src_index,dst_index,valid_mask,
                   src_address_ndims,dst_address_ndims,block_dim=8,
                   src_ptr=None,dst_ptr=None)
slot_map_lookup(slot_map,req_indices,topk_indices,block_dim=0)
```

## 注册内存所有权

`create_shm_tensor`调用原生注册分配后返回 `(host_tensor,host_ptr,dev_ptr)`；Tensor是CPU视图，dev_ptr是NPU可见地址，不能混用两个地址。shape逐维转int，拒绝负维和总字节数<=0。包装dtype覆盖FP16/BF16/FP32/FP64、有符号8/16/32/64位整数、uint8和bool；BF16/FP16只借uint16作ctypes位视图。

`free_shm`释放当前进程的整个原生分配表，不是Tensor逐对象析构，也不是按device分区释放：实现遍历全部条目，用调用时传入的同一个device_id注销后detach Host映射并清表，不按条目记录的device_id过滤。来源明确只支持每进程绑定单一NPU的部署；不要在一个进程中混合多设备分配并期待free_shm只释放指定设备。

CPU Tensor经ctypes.from_address和torch.frombuffer建立视图，没有为原生映射建立独立的逐Tensor释放器。保留Tensor不阻止free_shm解除映射；释放前必须完成所有使用这些地址的NPU工作，并停止CPU视图访问，释放后Tensor及host_ptr/dev_ptr都失效。free_all不等待流，也忽略halHostUnregister的错误并始终返回0；因此“无异常”不能证明每个注册注销成功。

## 原生分配、名称与环境分支

Torch控制入口为 `shm_allocator_create_and_register(int size,int device_id,str name)->(int,int)` 与 `shm_allocator_free_all(int device_id)->()`；size单位字节，返回Host地址和设备可见地址两个整数，不是NPU Tensor。size须正、device_id须非负。两入口没有Tensor参数，在legacy的SGL_KERNEL_ENABLE_A3_ONLY_OPS门控下注册CatchAll实现；该构建开关默认用于A2/A3家族、950关闭，不能仅因Python模块可导入就认为当前wheel具备绑定，或据此证明完整产品支持。

空name由进程内原子计数生成；显式name是进程内表的键。新分配使用shmget(IPC_PRIVATE)/shmat，立即IPC_RMID并清零，最后一个attachment解除时回收。它不是可凭相同字符串跨进程attach的命名共享池。同名且字节数相同会直接复用现有地址和内容，不重新清零，也不校验本次请求device_id；同名不同字节数返回ret=-6。因此shape/dtype变化即使总字节相同也需要调用方核对数据解释，不能靠名称证明布局一致。

默认mode为AUTO，先读取SOC_VERSION，仅未设置时才读取ASCEND_SOC_VERSION；区分大小写的Ascend910_93或910_93前缀选择HOST_SVM_MAP_DEV，其他值或两变量均未设置时选择HOST_MEM_MAP_DEV_PCIE_TH。该分支不探测实际硬件；C头文件另有shm_set_mode，但公共Python/Torch接口没有暴露该设置。EnsureAclDevice可能初始化ACL或切换当前设备，没有保存并恢复先前设备的逻辑。

新分配注册失败时会detach并删除新表项，Torch层将非零ret转为RuntimeError；ret=-1/-2可来自不同阶段，不能只凭该数值确定唯一根因。Python的dtype到ctypes映射在原生分配后执行，若随后遇到不支持dtype等封装异常，没有自动free该条目的处理；应在分配前核对受支持dtype，并按进程级所有权安排清理，不能在仍有其他活跃分配时随意free_all。

## 逻辑行拷贝

address_ndims须满足 `1<=n<tensor.dim()`；前n维乘积是逻辑行数，后续维乘积乘element_size得到每行字节。src/dst行字节和dtype必须一致；三个index/mask Tensor的numel一致。包装调用 `torch.ops.npu.unidex_copy` 后返回同一个dst，属于原地写入。

原生绑定进一步要求src_index/dst_index为一维int64、valid_mask为一维bool或uint8，三者位于同一NPU；src、dst及索引/mask均连续。未覆盖地址的src/dst也须位于该NPU。每行字节须为正且不超过32 KiB，src_rows和dst_rows均为正，二者各乘行字节须不超过uint32上限；提供原始指针也不豁免连续性、dtype、shape元数据和uint32寻址边界。

src_ptr/dst_ptr可覆盖Tensor地址，例如使用注册Host内存的设备可见地址；Tensor仍提供逻辑shape/dtype来计算行字节，不能以相同numel推断不同dtype或行布局等价。实际Kernel先检查mask非零，再检查两侧行号非负且不越界；不合法映射安静跳过，原dst行不变。合法任务按uint8完整搬运W字节，无dtype转换，UB对齐不扩大有效输出。重复dst或src/dst重叠没有atomic/冲突排序或memmove保证，不能仅由容量检查推定安全。

max_copy=0在原生Host全部参数检查后早返，零行数或零行字节仍拒绝。分核的`maxCopy+blockNum-1`是uint32中间加法，极限值仍可能溢出，单个参数可表示不等于所有中间运算安全。Host记录索引/mask及非raw一侧Tensor的current stream，raw侧没有自动持有注册分配；也没有DeviceGuard自动切到索引设备。实际launch helper捕获的是转换后的指针/标量，不是这些Tensor对象，caller须按Host排队与设备执行契约保活，并使current NPU、元数据与注册地址所属设备一致。完整字节账与两槽FIFO实现见[UniDex A3源码卡](../../operators/direct/nn/index/sgl_unidex_copy.md)。

## 槽位查找与数据流

slot_map_lookup要求slot_map、req_indices、topk_indices均为同一NPU上的连续int32 Tensor，slot_map/topk_indices为二维、req_indices为一维。slot_map各维和batch须为正，列数为8的倍数；topk_indices固定宽度2048，首维须等于req_indices长度；slot_map两维乘积及batch*2048均须不超过UINT32_MAX，Host对这两项uint32寻址上限显式拒绝超界值。它分配与topk_indices同shape/device的int32 token_on_device与device_token_pos，再由原生绑定写入，返回二元组。命中经设备slot取KV，miss经注册Host KV，经unidex_copy汇成选中TopK缓冲；命中判定和位置结果必须配合使用，不能把任意位置值直接当有效slot。

非法req或topk token输出miss的0/-1；合法索引的position保留map原值，命中值实际是`min(slot+1,1)`。因此map须以-1表示miss，合法槽值还需避免int32加1溢出；任意负值都代表miss的解释并未由本实现保证，例如slot=-2将产生hit=-1，转bool反而为真。Host不读回检查map值域。block_dim=0使用平台AIV核数，显式正值不得超过该数；caller仍须保证当前设备与Tensor一致。64项tile、32B行读取、sentinel及双槽事件协议见[SlotMap A3源码卡](../../operators/direct/nn/index/sgl_slot_map_lookup.md)，不据此扩大本API未知整组产品范围。

## 验证入口

`tests/python/sgl_kernel_npu/test_shm_allocator.py` 只定义size=0与device_id=-1两个错误分派用例，用于检查无Tensor参数的入口可达；它没有正向分配、同名复用或释放验证。`test_unidex_copy.py`另定义对齐/非对齐行、raw覆盖、注册H2D/D2H、空mapping和错误索引dtype，并在释放前同步；`test_slot_map_lookup.py`定义不同block_dim、非法索引、固定TopK与dtype拒绝。slot测试只用-1和常规正槽，不能据其reference的`slot>=0`泛化实现值域。

上游 `scripts/sparsity_driven_kv_offload/test_unidex_shm.sh` 提供索引拷贝正确性及smoke benchmark入口，另有两个sweep脚本。应先验证地址类型、逻辑行字节、mask及释放时机，再接cache manager。本文未执行这些脚本、编译或NPU数值/性能测试；两份独立源码卡只闭合各自静态实现，不替代本API整组部署与注册驱动的运行验收。
