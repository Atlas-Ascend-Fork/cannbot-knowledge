---
type: API
title: create_npu_tensors：分离部署中的 Device 地址包装
description: 说明同 shape/dtype 的 KV 地址转 Tensor 列表，明确地址有效性与内存所有权核验。
tags:
- task.lookup
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/llm_datadist/create_npu_tensors.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/llm_datadist/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/llm_datadist/create_npu_tensors.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/llm_datadist/_tensor_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/llm_datadist/llm_datadist.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/llm_datadist/_tensor_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/llm_datadist/llm_datadist.cpp
  role: implementation
created_at: '2026-11-09T02:51:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# create_npu_tensors：分离部署中的 Device 地址包装

## 版本与范围

依据 TorchAir 固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`。该提交属于 ascend_26_0_pt28 的固定来源组合；不是所有历史或主线版本的通用契约。发布部分选取A2/A3；主线A2/A3与950的限定范围见后文，不回推发布版。

## 接口

`torchair.llm_datadist.create_npu_tensors(shape:List[int],dtype:torch.dtype,addresses:List[int])->List[torch.Tensor]` 用一组已有 Device 地址创建 NPU Tensor 列表，主要用于分离部署中 shape/dtype 相同的 KV Cache。

## 使用边界

来源明确仅限大模型分离部署场景，不能把它当作通用设备内存分配器。addresses 必须来自实际 Device 内存；文档示例 [1,2,3,4] 是占位，不是可以直接执行的地址。

Python 入口仅转交底层 _create_npu_tensors，文档没有承诺这些 Tensor 自动取得原内存所有权或延长外部缓存生命周期。调用方需核对目标设备、地址范围、大小与 shape/dtype 对应关系，并按分配方的真实协议管理释放，不能由“返回 Tensor”推定可任意释放外部存储。

应在分配方和消费方分别检查同一 KV 内容、地址和使用生命周期，再接入图捕获或跨进程传输。

- [KV 存储和捕获地址](../../concepts/frameworks/npugraph_replay_address_contract.md)


## 验证边界

分别核对实际软件版本、配置生效日志/图结构、输出与存储语义，再比较同输入的稳态耗时。本文为固定文档和静态接口审阅，没有执行上游代码、NPU 数值或性能实验。

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)

## 主线类型检查与空释放函数

固定主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的本节文档/实现已核对，主线总览覆盖A2/A3与950PR/950DT；发布 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013` 的A2/A3条件仍独立保留，不回推发布版950或两仓主线配套。

主线页移除了发布页显式A2/A3产品段，产品范围按主线总览与本接口分离部署限制一起理解；这不是发布版产品支持被追溯修改。Python接受shape/addresses的list或tuple且元素为int，dtype需在固定映射中，非零底层状态转为RuntimeError。

Python映射含bool、uint8/int8、int16/uint16、int32/uint32、int64/uint64、BF16、FP16/32/64、complex64/128；不含FP8、FP4、量化qint类型或complex32。C++映射虽另有ComplexHalf，不表示Python入口也接受该类型。dtype能被包装也不保证后续模型算子都支持它。

C++为每个地址构造PrivateUse1 Tensor，按shape和itemsize计算连续存储字节数，storage_offset=0；不接收stride参数，不能按此接口无损表达任意转置/偏移视图。DataPtr的deleter为空函数，不释放原外部地址，也不会自动持有分配方对象；这是对已有Device内存的包装，不为每个地址分配并复制KV内容。

底层并未在这里校验外部地址是否具有所需容量、属于当前设备或仍然存活。分配方需维持正确设备上下文和内存生命周期，消费者使用结束再按真实分配协议释放。Tensor对象存在、dtype/shape合法或包装返回成功，都不能替代这些条件；示例整数地址仅占位。本次未创建或解引用任何设备指针。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/llm_datadist/create_npu_tensors.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/llm_datadist/__init__.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/llm_datadist/create_npu_tensors.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/llm_datadist/_tensor_utils.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/llm_datadist/llm_datadist.cpp)（implementation）
## 发布版dtype映射收窄：uint16/32/64双侧缺席

发布`7c6c754bed00c86ffaaa2a45cb7ac2724f058013`的Python `_TORCH_DTYPE_TO_GE_TYPE`相对主线删除了`torch.uint16/uint32/uint64`三项映射，C++ `ToScalarType`同位删除`kUint16/kUint32/kUint64`（主线两者均含，见上文主线小节）。发布版传入这三个dtype时，Python层`_data_type_from_torch`先以`ValueError: unsupported dtype`拒绝并列出支持键表；即便绕过Python，C++查表落空返回`Undefined`，`AsTorchTensor`整批返回`kFailure`空列表，Python再转`RuntimeError`。两侧缺口一致，不是只在一层收窄。

主线支持的三类无符号dtype在发布版对`create_npu_tensors`不可用；跨pin迁移分离部署代码时应按目标pin的映射表核对，不能把主线映射当两pin通用。本节为发布侧静态事实，未构造uint16张量做运行验证。

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/llm_datadist/_tensor_utils.py)（implementation）：1–57完整读取；与主线diff确认仅删uint16/32/64三映射及注释排版。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/llm_datadist/llm_datadist.cpp)（implementation）：1–73完整读取；与主线diff确认`ToScalarType`删`kUint16/kUint32/kUint64`三行、其余为include顺序与排版。
