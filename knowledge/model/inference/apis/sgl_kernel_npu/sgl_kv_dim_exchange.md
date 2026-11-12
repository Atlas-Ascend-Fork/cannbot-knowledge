---
type: API
title: SGL KV整页换维传输与异步流所有权
description: 说明 transfer_kv_dim_exchange 的层页布局互换、首token确定页号、配对indexer/scale和同步要求。
tags:
- task.implementation
- topic.kv_cache
- topic.data_movement
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/data_move/transfer_kv_dim_exchange.md
  role: primary
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
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/data_move/transfer_kv_dim_exchange.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/data_move/transfer_kv_dim_exchange.py
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-09T11:06:19Z'
platforms:
- a2
- a3
- '950'
aliases:
- transfer_kv_dim_exchange
---

# SGL KV整页换维传输与异步流所有权

## 调用入口

```python
from sgl_kernel_npu.operators.data_move import TransferDirection, TransferFlag, transfer_kv_dim_exchange

def transfer_kv_dim_exchange(device_indices, host_indices, device_k, host_k, device_v, host_v, device_index_k=None, host_index_k=None, device_index_k_scale=None, host_index_k_scale=None, page_size=128, direction=TransferDirection.H2D, flags=TransferFlag.FAST2D, *, impl='auto'): ...
```

## 布局和传输粒度

公开data_move接口默认auto=aclrt，按页在NPU与连续锁页CPU缓存间双向搬运。设备KV `[L,D,P,A,C]` 以层为首维，主机 `[H,L,P,A,C]` 以页为首维；P=page_size默认128。每组选中页搬运全部层，未选页不变。

device_indices/host_indices是成对int64 token索引，数量为P的整数倍；每组只有首token用于计算页号，其余值不独立寻址。不能用这接口实现同一页内任意token gather。

## 可选分量和物理约束

可只传K，V用空Tensor；参与V的层数、页数、P、head数和dtype与K一致，head_dim可不同。indexer key可选，但主机/设备须成对；indexer scale为FP32，设备可 `[L,D,P,1]` 或 `[L,D,P,1,1]`，主机为 `[H,L,P,1,1]`。

各源目标分量dtype和页形状匹配。主机须连续且锁页；设备页内可稠密转置，但页/层pitch紧凑。aclrt提交前检查全部页索引，失败直接上抛。

## 异步、参考和验证

direction默认为H2D，也支持D2H；flags默认为FAST2D。返回None，原地写目标，在当前NPU流提交异步二维复制。读取目标或复用源前必须同步该流，函数返回不表示传输完成。

torch_native独立复用gather/scatter逻辑，将物理页存储适配为槽位，不调用aclrt。验证覆盖非顺序页、两方向及可选indexer/scale；同步后按物理字节和换维布局检查所选页与未写哨兵。这里是Runtime复制集成契约，不是AscendC Device算子实现。

## HOST地址与检查细节

Python将TransferDirection.H2D/D2H分别转为1/2，TransferFlag.FAST2D转为2；包装读取枚举的.value，raw整数不属于相同的Python调用约定。原生flags判断为(flags & 2)==2，不据其它位推导额外复制模式。Torch符号为 `torch.ops.npu.transfer_kv_dim_exchange`。

设每页有效payload为s=P*heads*head_dim*element_size字节、层数L、设备页容量D。每个选中页的一次二维复制width=s、height=L，设备行pitch=D*s，Host行pitch=s；K/V的s可不同。以各Tensor.data_ptr()为base，设备页起点为device_base+device_page*s，Host页起点为host_base+host_page*L*s。复制不转换dtype或payload内部逻辑维顺序。稠密转置检查按size>1的payload维stride排序，依次要求stride=1及前面维度大小乘积，保证物理稠密，而非把转置变回逻辑连续。

索引须一维INT64、等长，长度为P倍数；先.cpu().contiguous()再由Host验证，NPU索引因此可能带来D2H及Host同步，不能把payload异步等同整个函数完全不阻塞。每P项只校验和消费首项，floor(first/P)定位页；没有要求first被P整除的检查，组内其余P-1项既不寻址也不逐值校验。

V仅在设备、Host两侧都非空时参与，一侧为空会跳过。可选indexer key/scale也仅在两侧都非None时额外提交，单侧提供会跳过；四维设备scale先unsqueeze(-1)，Host scale保持五维。主K/V先提交，辅助项随后才检查，辅助检查失败不会回滚主数据。所选Q页主payload为Q*L*(sK+sV)，可选分量另计，不将同一字节的源读、目标写双计为payload。

## 固定HOST构建与异步所有权

本节对应固定提交的 `csrc/data_move` 新HOST实现：CMake标为HOST执行单元，2201/3510构建族；公开auto选择aclrt，失败不自动回退torch_native。独立subset wheel必须实际包含相应注册符号。同名旧构建的差异见[旧Torch传输接入](/model/inference/guides/integration/sgl_kernel_npu/sgl_legacy_state_transfer.md)。固定CI使用CANN9.1.0，不据此保证任意安装包ABI。

原生实现直接取当前NPU流，没有切换设备的DeviceGuard；提交前由调用方保证当前设备与所有设备payload一致。源内未见payload的record_stream或异步保活回调：读取目标、覆盖源、复用或释放Host/NPU缓冲前，必须等待实际提交流完成，或建立等价的完成事件依赖。索引只用于Host生成地址，提交后不会作为异步payload继续读取；索引和数据缓冲的保活要求不同。

每次aclrtMemcpy2dAsync返回码会立即检查；第k次提交失败时前k-1次可能已排入流，既无回滚也无事务保证。重复目标和存储别名须单独处理，不能将Host提交顺序推广为跨流原子覆盖保证。宽度、pitch均以字节计，底层Runtime/DMA参数上限仍须遵守实际部署版本。源码未提供本次带宽或延迟实测。

## 固定来源与验证状态

- [data_move/transfer_kv_dim_exchange.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/data_move/transfer_kv_dim_exchange.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
