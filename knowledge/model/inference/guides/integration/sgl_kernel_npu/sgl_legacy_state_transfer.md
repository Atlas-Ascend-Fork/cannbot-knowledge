---
type: Guide
title: SGL旧Torch路径的KV与状态传输接入
description: 识别kvcacheio四个Torch绑定的构建实现，区分整页KV、Mamba和direct槽位搬运的检查、空V风险与异步错误边界。
tags:
- task.implementation
- topic.data_movement
- topic.kv_cache
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/cmake/legacy_kernels.cmake
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/CMakeLists.txt
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/kvcacheio.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/transfer_kv_dim_exchange/op_host/transfer_kv_dim_exchange.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/transfer_mamba_state/op_host/transfer_mamba_state.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/transfer_state_dim_exchange/op_host/transfer_state_dim_exchange.cpp
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/data_move/torch_adapter.cpp
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/data_move/transfer_utils.h
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/data_move/transfer_kv_dim_exchange.cpp
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_transfer_state_direct.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_transfer_mamba_state.py
  role: evidence
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_transfer_kv_dim_exchange.py
  role: evidence
created_at: '2026-11-09T05:59:57Z'
updated_at: '2026-11-09T05:59:57Z'
platforms: []
aliases:
- sgl_kernel_npu.kvcacheio
- transfer_state_all_layer_direct_lf_pf
- transfer_state_per_layer_direct_pf_lf
---

# SGL旧Torch路径的KV与状态传输接入

## 适用范围与先决核对

本卡用于对接`sgl_kernel_npu.kvcacheio`和旧`torch.ops.npu`搬运绑定，补充构建身份及原生检查差异。[KV整页API](/model/inference/apis/sgl_kernel_npu/sgl_kv_dim_exchange.md)、[Mamba API](/model/inference/apis/sgl_kernel_npu/sgl_mamba_state_transfer.md)与[direct状态API](/model/inference/apis/sgl_kernel_npu/sgl_direct_state_transfer.md)已经维护新operators接口契约，本卡不把这些更强的约束检查当成旧构建已实现的保证。

同一固定提交保留两套注册/源码：根Torch构建经`csrc/CMakeLists.txt`的分支包含`cmake/legacy_kernels.cmake`，使用`csrc/pytorch_extensions.cpp`及`sglang::npu_kernel`下的旧Host实现；独立新构建使用`csrc/data_move/torch_adapter.cpp`，宏选择`sglang::data_move`下的实现。符号同名，实际加载的共享库决定行为，不能仅凭Python入口或源文件存在识别实现。两个构建都存在不代表可同时加载重复注册。

Python包装会把TransferDirection枚举转为整数H2D=1/D2H=2、TransferFlag.FAST2D转为2；raw Torch调用传整数，所有参数由调用方提供，无impl选择和自动参考回退。固定源码快照未与SGLang发布wheel建立版本绑定，本文保留为静态接入边界，平台尚未定位。

## 四个底层入口与布局

```python
# torch.ops.npu下的原始签名；均返回None并修改目标缓冲。
def transfer_kv_dim_exchange(device_k, host_k, device_v, host_v,
                             device_indices, host_indices, page_size, direct, flags): ...

def transfer_mamba_state(device_buf, host_buf, device_indices, host_indices, direction): ...

def transfer_state_per_layer_direct_pf_lf(src, dst, src_indices, dst_indices, layer_id, flags): ...

def transfer_state_all_layer_direct_lf_pf(device_states, host_states,
                                        device_indices, host_indices, flags): ...
```

| 入口 | 数据流与索引粒度 | 接入前必须明确的区别 |
| --- | --- | --- |
| KV dim exchange | NPU `[L,D,P,A,C]`与Host `[H,L,P,A,C]`双向搬整页；P=page_size | 索引长度相同且是P倍数，每组只读首token索引再整除P得到页号；不是逐token gather。raw签名的方向参数叫direct，Python包装叫direction。 |
| Mamba state | 设备`[L,D,*state]`与Host`[H,L,1,*state]`双向搬全部层 | 每对索引直接表示slot，不除page_size；宽度为state总字节，按紧凑层/槽位pitch计算。 |
| per-layer direct pf_lf | Host`[H,L,1,*state]`→设备单层`[D,*state]` | 仅H2D，src_indices是Host slot、dst_indices是设备slot，layer_id选择Host层；双侧连续递增的索引run可合成二维copy。 |
| all-layer direct lf_pf | 设备分量列表`[L,D,*state]`→配对Host列表`[H,L,1,*state]` | 仅D2H，列表可承载不同dtype/形状分量，各索引必须同时落在所有分量容量内，一次备份全部层。 |

direct的Python旧名称为`transfer_state_*`；新operators公开函数名为`transfer_kv_*`，但新adapter仍注册相同`torch.ops.npu.transfer_state_*`名字。不能按名称中的kv/state推导索引是否按页换算。

## 旧KV与Mamba不能继承新实现的保证

旧KV Host检查K非空、K/Host同为五维、层数与P匹配、索引数量和方向/FAST2D位；V双方非空才进入部分维度检查。它没有像新`transfer_utils.h`那样统一检查NPU/CPU归属、锁页、dtype、payload稠密性、紧凑pitch和所有索引后再提交。调用方须预先保证源目标dtype/page shape一致、设备与主机物理布局紧凑、Host连续锁页以及所有页号有效非负。

旧KV先把索引转CPU，再在页循环中检查页号上界并立即提交copy，未检查原token索引非负；后面的非法页可能在前面页已提交后才抛异常。KV/Mamba旧实现也忽略aclrtMemcpy2dAsync返回码，不能把函数正常返回解释为每条复制已被接受或数据已完整写入。

空V存在明确的版本内差异：kvcacheio为K-only/Indexer/scale调用传`torch.empty(0)`，但旧KV实现仍无条件读取`device_v.sizes()[4]`后才判断是否拷V，存在越界取维的静态风险。新`csrc/data_move/transfer_kv_dim_exchange.cpp`用numel条件保护该读取。源码中的K-only测试定义不能消除旧实现差异；在确认实际库修正/使用新实现并定向验证前，不将旧构建的空V路径视为已确认可用。

旧Mamba检查非空、最少维数、层数、dtype、总state字节、方向和逐slot范围，但不验证同一物理布局合同；相同numel或slot_bytes不足以保证strided view可正确按预定pitch复制。它也在循环中验证并立即复制，晚发现非法slot不具备整批回滚。目标布局不满足紧凑pitch时应先构造连续staging，再按上层池的真实stride恢复。

## direct状态入口的更强检查

旧direct实现与上述KV/Mamba不同：非空索引时先验证全部分量和索引，再提交异步copy，并检查每次ACL返回码。Host必须为CPU连续锁页Tensor；设备为NPU、每对dtype和state形状一致，Host页维固定1。设备slot内部允许稠密维度转置、slot stride必须等于state元素数；全层D2H允许设备层间留空，但层pitch不得重叠，per-layer H2D目标是紧密slot的单层视图。

direct索引先`.cpu().to(Long).contiguous().reshape(-1)`；建议调用方仍提供语义明确的int64向量，不能把这一转换解释为任意浮点/多维索引语义。空索引在数量与FAST2D检查后直接返回，早于完整payload校验。全层列表须非空且成对，数量不一致被拒绝。

这两个入口只接受含FAST2D位的flags；未提供隐式方向切换。全部验证先行仅保证校验错误前未提交本批copy；后续ACL提交失败仍可能发生部分分量已提交的情况，不是事务。重复目标或别名覆盖应在调用层排除或单独验证，不能由Host循环存在推导通用冲突语义。

## 接入步骤、验证与回退

1. 记录安装包、加载共享库及构建入口，确认四个所需raw符号实际存在；只导入kvcacheio不证明所有注册符号存在。依据目标数据选择整页KV或直接slot语义。
2. 在调用前统一核对所有分量的dtype、shape、stride、容量与索引，KV特别检查完整page分组及空V实现；Mamba/direct核对L和slot映射。不要用Host容量或KV命中页数代替混合状态完整性。
3. 在指定NPU流提交，记录完成事件，并在读取Host目标、覆盖设备源或复用Host源前等待事件。索引`.cpu()`可能有Host同步，接口本身没有返回可供上层自动等待的事件。
4. 用含层号、slot/page号的可区分数据做双向/round-trip和未选哨兵验证。发生参数或提交错误时保留相关缓冲并处理已提交流，丢弃/重建可能部分写入的目标；不把重试当原子回滚。需要上层分支或staging时见[SGLang Mamba Host池](/model/inference/guides/integration/sglang_ascend_runtime/sglang_ascend_cache_mamba_host_exchange.md)。

固定测试目录中direct用例定义了多分量、离散索引、单层恢复、连续run、稠密转置和拒绝非dense/越界/未锁页的检查；Mamba测试有逐元素/未选槽位断言。KV部分旧用例只比较sum，后续scale用例才按层/页逐元素检查，应按实际断言强度消费。测试文件存在不代表这些测试在目标构建或本次会话运行通过。

本次仅静态读取接口、原生Host、包装及测试定义，未执行上游代码、构建、真机、数值或性能测试。本卡不包含完整Device算子实现，复制延迟与带宽需另行测量。

## Evidence

- [旧Torch签名与绑定](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/pytorch_extensions.cpp#L50)：50–65行签名、314–321行PrivateUse1绑定。
- [旧KV实现](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/transfer_kv_dim_exchange/op_host/transfer_kv_dim_exchange.cpp#L28)：67行空V维度读取、75–103行边检查边提交及忽略返回码。
- [旧Mamba实现](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/transfer_mamba_state/op_host/transfer_mamba_state.cpp#L34)：字节和紧凑pitch计算、逐slot校验并提交。
- [direct检查与提交](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/transfer_state_dim_exchange/op_host/transfer_state_dim_exchange.cpp#L208)：两固定方向入口、全量校验、run合并与ACL错误检查。
- [新adapter命名](https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/csrc/data_move/torch_adapter.cpp#L24)：同名raw符号映射到新的data_move实现。
