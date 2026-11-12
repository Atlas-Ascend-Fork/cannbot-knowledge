---
type: API
title: SGL Mamba状态的双向全层槽位搬运
description: 说明 transfer_mamba_state 的直接槽位索引、层槽位互换、紧凑pitch与异步同步边界。
tags:
- task.implementation
- topic.data_movement
- topic.memory
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/data_move/transfer_mamba_state.md
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
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/data_move/transfer_mamba_state.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/data_move/transfer_mamba_state.py
  role: implementation
created_at: '2026-11-08T11:03:33Z'
updated_at: '2026-11-09T11:06:19Z'
platforms:
- a2
- a3
- '950'
aliases:
- transfer_mamba_state
---

# SGL Mamba状态的双向全层槽位搬运

## 调用入口

```python
from sgl_kernel_npu.operators.data_move import TransferDirection, transfer_mamba_state

def transfer_mamba_state(device_buf, host_buf, device_indices, host_indices, direction=TransferDirection.H2D, *, impl='auto'): ...
```

## 语义与布局

设备device_buf `[L,D,*state]`、连续锁页host_buf `[H,L,1,*state]`，根据一一对应的int64 device_indices/host_indices搬全部层。direction默认H2D，可选D2H；不按页大小转换索引，不能与KV token页索引混用。未选槽位不变，函数返回None并原地改目标。

state可一维或多维，源目标dtype与槽位字节数必须一致。设备槽位内部允许稠密转置，但槽位和层pitch都紧凑；各槽位非负且小于对应容量。aclrt提交前检查全部索引，错误向调用方上抛。

## 生命周期与验证

auto选aclrt，在当前NPU流提交异步二维复制。结果消费、主机源复用或设备源覆盖前须等待提交流。torch_native独立按层gather/scatter或全层换维，保持同一物理字节顺序，不调用aclrt；其重复目标按输入序写入，不能据此推断原生冲突顺序。

用带层号/槽位号可辨识内容分别做H2D、D2H，覆盖稠密转置state和不连续槽位；同步后核对所选数据及未选哨兵。与直接全层备份接口相比，本接口是单分量双向入口，且不允许设备层pitch留空。

## HOST地址与检查细节

实际绑定 `torch.ops.npu.transfer_mamba_state`，方向枚举由Python.value转为H2D=1/D2H=2。设s=prod(device_buf.shape[2:])*element_size、层数L、设备槽容量D。一次slot二维copy为width=s、height=L，设备行pitch=D*s、Host行pitch=s；设备起点device_base+device_slot*s，Host起点host_base+host_slot*L*s。选中N对槽位payload为N*L*s。

payload维按非单例维stride排序，验证物理稠密；槽pitch和层pitch须紧凑。该路径核对两侧slot字节数，而非逐个证明尾维shape完全相同，复制也不作内部转置或dtype变换。应按文档布局准备配对state，不能由相同numel推导任意strided view可用。

两索引须一维INT64、等长；共享helper以page_size=1逐槽校验全部非负和范围后才提交，不与KV每P项只读首项混同。索引.cpu().contiguous()后供Host读取，NPU索引可能引入D2H/同步；payload在流内异步不表示整个调用完全不阻塞。

## 固定HOST构建与异步所有权

本节对应固定提交的 `csrc/data_move` 新HOST实现：CMake标为HOST执行单元，2201/3510构建族；公开auto选择aclrt，失败不自动回退torch_native。独立subset wheel必须实际包含相应注册符号。同名旧构建的差异见[旧Torch传输接入](/model/inference/guides/integration/sgl_kernel_npu/sgl_legacy_state_transfer.md)。固定CI使用CANN9.1.0，不据此保证任意安装包ABI。

原生实现直接取当前NPU流，没有切换设备的DeviceGuard；提交前由调用方保证当前设备与所有设备payload一致。源内未见payload的record_stream或异步保活回调：读取目标、覆盖源、复用或释放Host/NPU缓冲前，必须等待实际提交流完成，或建立等价的完成事件依赖。索引只用于Host生成地址，提交后不会作为异步payload继续读取；索引和数据缓冲的保活要求不同。

每次aclrtMemcpy2dAsync返回码会立即检查；第k次提交失败时前k-1次可能已排入流，既无回滚也无事务保证。重复目标和存储别名须单独处理，不能将Host提交顺序推广为跨流原子覆盖保证。宽度、pitch均以字节计，底层Runtime/DMA参数上限仍须遵守实际部署版本。源码未提供本次带宽或延迟实测。

## 固定来源与验证状态

- [data_move/transfer_mamba_state.md](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/data_move/transfer_mamba_state.md)
- [构建架构与产品映射](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md)及[SDK架构表](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/cmake/architectures.json)。文档arch22对应本版本2201构建族A2/A3，arch35对应3510的950；具体子接口限制以上文为准。

本卡为固定提交的公开API契约蒸馏，未展开Host/Tiling/Device全链路。本次知识提取未执行编译、真机、数值或性能测试；上游报告的支持和用例结果不代表本次复测。
