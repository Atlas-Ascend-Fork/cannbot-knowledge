---
type: Runbook
title: vLLM Ascend ECCPU 初始化失败或mmap残留：能力探针、注册与关闭顺序
description: 按 AscendECCPUWorker、supports_eccpu_offload 与 CANN编译探针排查pinned mmap/batch
  DMA拒绝，区分正常shutdown保留、构造失败cleanup和通用copy fallback。
tags:
- task.debugging
- task.testing
- topic.multimodal
- topic.memory
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/ec_transfer/ec_connector/cpu/worker.py
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/ec_transfer/ec_connector/cpu/connector.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/ec_transfer/ec_connector/cpu/__init__.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/distributed/ec_transfer/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/CMakeLists.txt
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/setup.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/envs.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/ec_transfer/ec_connector/cpu/worker/__init__.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/ec_transfer/ec_connector/cpu/ec_shared_region.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/ec_transfer/ec_connector/cpu/common.py
  role: constraint
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/distributed/ec_transfer/ec_connector/factory.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ec_transfer/test_worker_mock.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ec_transfer/test_registration.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/distributed/ec_transfer/test_connector.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/encoder_cache_cpu_offload.md
  role: supporting
created_at: '2026-10-29T20:09:01Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T20:09:01Z'
---

# vLLM Ascend ECCPU 初始化失败或mmap残留：能力探针、注册与关闭顺序


## 信号与固定范围

启用ECCPUConnector后初始化报requires both API、mmap注册失败、batch copy异常，或关闭后/dev/shm残留。固定Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 与其所需原生vLLM v0.32.0的Host生命周期；文档以能力而非完整产品表限定，保持draft/空平台。本次没有构建、导入上游模块、调用CANN或复现故障。

## 先确认实际工厂类和版本

Ascend插件register_connector加载global patch后注册EC替换，ECConnectorFactory中ECCPUConnector应解析为AscendECCPUConnector，后者_make_worker返回AscendECCPUWorker。模块名/配置名相同不证明这一替换已在每进程发生。

_replace_cpu_connector只在原生CPU模块本身或其父路径缺失时捕获ModuleNotFoundError并返回False，嵌套依赖缺失会继续抛出；返回False还会使该注册函数不继续替换Mooncake。原生有NIXL配置不等于Ascend支持跨节点；不要把lazy注册成功当成NPU扩展能力已就绪。

## supports_eccpu_offload是构建能力门禁

_pin_shared_region先调用supports_eccpu_offload，只有CANN_MEMCPY_BATCH_ASYNC和CANN_HOST_REGISTER_V2_PINNED均编进扩展才为True。CMake用实际结构成员和API模式探测headers/link环境；这不是运行时每台设备的完整鉴定。

VLLM_ASCEND_ENABLE_BATCH_MEMCPY由setup.py转成CMake变量：未设才auto-detect，字符串1强制启用，其他显式值走关闭分支。强制关闭会让ECCPU拒绝，即使系统安装较新CANN；运行后只改环境变量也不会改已有二进制。强制开启不补齐不存在的headers/ABI，仍要核对真正构建与加载的扩展、CANN库和torch_npu版本。

通用swap_blocks_batch对某些路径有逐次aclrtMemcpyAsync fallback，D2D也走该循环，但ECCPU先过双能力门禁，正常H2D/D2H应进入batch路径。不能把通用fallback解释为ECCPU会静默降级pageable/单次复制。文档Linux>5.10是CANN pinned mmap前提；MADV_POPULATE_WRITE不支持时的逐页预触警告又是另一件事，不表示已经放弃pin。

## 注册探针与地址生命周期

register_pinned_host_mmap要求CPU、contiguous、非空tensor和4KiB对齐地址，以numel*element_size注册ACL_HOST_REG_PINNED。进程内mutex+地址到size映射拒绝重复注册；unregister要求同地址仍在表中且size未变，CANN成功后才删除记录。该表不是跨进程的共享文件引用计数，也不验证任意Tensor一定由目标MAP_SHARED文件拥有。

每个worker的虚拟映射须独立注册；同一文件名、blocks.is_pinned属性或CANN符号存在都不能代替实际注册结果。预算还需按实际block size取整，覆盖至少一块、tmpfs容量、creator/follower与预触页。ECSharedRegion打开同名文件只等待至少目标size，没有验证模型/shape身份，不能把残留旧文件直接当兼容缓存。

swap_blocks_batch的CPU int64指针/长度数组与payload本身分开；标准DescriptorBufferPool提供一维连续缓冲，但C++这里只检查CPU/dtype/长度等，未对任意手工地址、步长、负长度建立完整通用验证。按[搬运接线](../../guides/integration/vllm_ascend_eccpu_transfer_pipeline.md)维持描述符和event生命周期，保留batch fail_index、方向和当前NPU流信息，不据提交返回就释放源/目标。

## 正常关闭与构造失败不是同一条路径

| 路径 | 固定实现次序 | 排障含义 |
| --- | --- | --- |
| 正常Worker.shutdown | 等全部inflight end_event，再Ascend backend全NPU synchronize、unregister，最后region.cleanup | event/sync/unregister异常会在cleanup之前传播，不能当作已经解除映射 |
| _shutdown_transfer_backend | _mmap_pinned为False则返回；为True时同步和unregister成功后才清False | unregister失败会保留True，代码容许后续受控重试；没有证明每次重试都安全成功 |
| Ascend构造super失败 | except尝试backend shutdown，finally若_region已存在仍调用region.cleanup | 不受“正常shutdown失败必保留mmap”概述完整覆盖；要按失败阶段核对，不把所有异常一概归类 |
| region构造本身失败 | self._region尚未成功赋值时外层未必取得region对象 | 文件/fd/注册的实际清理要回到构造阶段取证，不能假定总有完整worker可shutdown |

region.cleanup由creator负责unlink，随后删除blocks view、关闭mmap/fd；其他进程自己的映射与DMA不是由这个对象统一退役。关闭失败残留应保留原异常、creator身份、inflight事件和注册状态，先确认无异步使用再采取目标环境处置，不能仅按文件名强行清理来宣称修好。

## 测试证据与验收

上游test_worker_mock.py定义了双能力拒绝/注册失败清理、NPU event回收、方向映射、提交失败不释放描述符、event→NPU sync→unregister→cleanup顺序及unregister失败保留标记的mock断言；registration测试还覆盖optional模块缺失与嵌套导入错误。它们是已读测试定义，本次未执行，也不证明真实DMA、CANN注册或正常/异常所有分支已被穷尽。

保存实际类/版本、compile flags/probe、映射地址/size/文件身份、原始错误、event与注册/关闭阶段，并验证同媒体冷/热输出一致。能力不满足、注册未成功、完成回报缺失或关闭状态不清时，不声明offload可用或释放完毕；性能要分encode节省、copy与启动注册成本，另在目标硬件验证。
