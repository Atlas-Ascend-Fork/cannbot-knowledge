---
type: API
title: SGL直接槽位状态的全层备份与单层恢复
description: 区分 direct_lf_pf 的D2H全层备份和 direct_pf_lf 的H2D单层恢复、直接索引与异步缓冲生命周期。
tags:
- task.implementation
- topic.data_movement
- topic.memory
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/data_move/transfer_kv_all_layer_direct_lf_pf.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/data_move/transfer_kv_per_layer_direct_pf_lf.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/data_move/transfer_utils.h
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/data_move/torch_adapter.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/data_move/CMakeLists.txt
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/.github/workflows/pr-test-kernels.yml
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/data_move/_types.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/data_move/transfer_state_dim_exchange.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/data_move/transfer_kv_all_layer_direct_lf_pf.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/data_move/transfer_kv_per_layer_direct_pf_lf.py
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-09T11:06:19Z'
platforms:
- a2
- a3
- '950'
aliases:
- transfer_kv_all_layer_direct_lf_pf
- transfer_kv_per_layer_direct_pf_lf
---

# SGL直接槽位状态的全层备份与单层恢复

## 调用入口

```python
from sgl_kernel_npu.operators.data_move import TransferFlag, transfer_kv_all_layer_direct_lf_pf

def transfer_kv_all_layer_direct_lf_pf(device_states, host_states, device_indices, host_indices, flags=TransferFlag.FAST2D, *, impl='auto'): ...

from sgl_kernel_npu.operators.data_move import TransferFlag, transfer_kv_per_layer_direct_pf_lf

def transfer_kv_per_layer_direct_pf_lf(src, dst, src_indices, dst_indices, layer_id, flags=TransferFlag.FAST2D, *, impl='auto'): ...
```

## 两个固定方向入口

| API | 方向/输入 | 目标和粒度 |
| --- | --- | --- |
| transfer_kv_all_layer_direct_lf_pf | D2H；设备分量列表，每个 `[L,D,*state]` | 主机配对分量 `[H,L,1,*state]`；每对索引备份全部层，可同时搬temporal/conv等不同shape或dtype分量。 |
| transfer_kv_per_layer_direct_pf_lf | H2D；主机 `[H,L,1,*state]`、layer_id | 设备单层视图 `[D,*state]`；只恢复指定层。 |

槽位索引均为成对int64 `[N]`，直接寻址、不按page_size换算；各项非负并在对应容量内。允许离散索引和重复读源。layer_id必须在主机层范围内。

## 物理布局与流

主机分量须连续且锁页，每对源目标dtype和state shape一致；设备槽位内部可稠密转置，但槽位pitch等于实际槽位字节数。全层备份的层pitch允许留空，但不能小于整层槽位数据大小。aclrt先验证全部分量和索引，再在当前NPU流提交异步FAST2D复制。

auto=aclrt；两个函数返回None并原地写目标，读取目标或复用源之前同步提交流。不能用返回None判断复制完成。

## 参考与验证

torch_native独立使用index_select/index_copy_和层/槽位换维，按物理存储解释稠密转置。该参考对重复目标按输入顺序覆盖；应显式验证目标冲突是否满足使用场景，不能把参考覆盖顺序直接推广为原生并发保证。

测试时覆盖多个状态分量、层间pitch、转置稠密state、离散槽位和未选槽位保留；分别同步H2D/D2H后核对字节。此卡只记录复制包装契约，不宣称完成底层Runtime源码闭包。

## HOST索引、pitch与分量边界

公开函数的实际Torch绑定分别是 `transfer_state_all_layer_direct_lf_pf` 和 `transfer_state_per_layer_direct_pf_lf`，名称不含kv。Python将TransferFlag.FAST2D.value传为2；原生要求(flags & 2)==2，不给其它位赋予额外模式。

两个direct入口均把索引.cpu().to(INT64).contiguous().reshape(-1)，不同于KV/Mamba严格的一维INT64检查；调用方仍宜传非负整数槽位。空索引可在完整payload校验前返回，不能以空调用成功证明buffer满足合同。全层入口仍先检查分量列表非空、两列表数量一致。

全层D2H先校验所有分量，用各分量最小槽容量作为共同索引边界；复制高度取第0分量L0，其余分量只须有足够层覆盖L0。若其余分量层数更大，只复制其前L0层，按“全部层”使用时应让各分量层数一致。第j分量槽字节s_j，width=s_j、height=L0，设备行pitch为真实stride(0)*element_size，Host行pitch为stride(1)*element_size=s_j；payload合计sum_j(N*L0*s_j)。设备层pitch可以留空但不得重叠，不能把所有分量的真实stride替成紧凑L*D公式。

单层H2D的源地址为host_base+host_slot*host_slot_pitch+layer_id*host_layer_pitch，目的为dst_base+device_slot*device_slot_pitch。dst槽payload物理稠密，slot pitch=s。按原顺序仅当源、目标槽都同时比上一项加1才合并；不排序、不去重，任一侧离散或重复即切段。每段一次copy，width=s、height=段长、Host行pitch跨过同槽其余层，设备行pitch=s。合并减少提交数，payload仍为N*s；全层D2H不使用此run合并器。

全层入口没有额外证明不同分量位于同一个device index，调用方应保证同卡及正确当前设备；每分量是NPU Tensor不构成跨卡传输支持。非空输入的全量参数校验先行，也不能消除后续ACL提交可能部分成功的边界。

## 固定HOST构建与异步所有权

本节对应固定提交的 `csrc/data_move` 新HOST实现：CMake标为HOST执行单元，2201/3510构建族；公开auto选择aclrt，失败不自动回退torch_native。独立subset wheel必须实际包含相应注册符号。同名旧构建的差异见[旧Torch传输接入](/model/inference/guides/integration/sgl_kernel_npu/sgl_legacy_state_transfer.md)。固定CI使用CANN9.1.0，不据此保证任意安装包ABI。

原生实现直接取当前NPU流，没有切换设备的DeviceGuard；提交前由调用方保证当前设备与所有设备payload一致。源内未见payload的record_stream或异步保活回调：读取目标、覆盖源、复用或释放Host/NPU缓冲前，必须等待实际提交流完成，或建立等价的完成事件依赖。索引只用于Host生成地址，提交后不会作为异步payload继续读取；索引和数据缓冲的保活要求不同。

每次aclrtMemcpy2dAsync返回码会立即检查；第k次提交失败时前k-1次可能已排入流，既无回滚也无事务保证。重复目标和存储别名须单独处理，不能将Host提交顺序推广为跨流原子覆盖保证。宽度、pitch均以字节计，底层Runtime/DMA参数上限仍须遵守实际部署版本。源码未提供本次带宽或延迟实测。

## 固定来源与验证状态

- [data_move/transfer_kv_all_layer_direct_lf_pf.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/data_move/transfer_kv_all_layer_direct_lf_pf.md)
- [data_move/transfer_kv_per_layer_direct_pf_lf.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/data_move/transfer_kv_per_layer_direct_pf_lf.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
