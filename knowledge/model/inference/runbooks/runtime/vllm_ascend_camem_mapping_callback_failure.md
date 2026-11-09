---
type: Runbook
title: vLLM Ascend CaMem 映射/回调失败：VA、physical handle与GIL边界
description: 按 camem_allocator.cpp 的 my_malloc、my_free、python_create_and_map、python_unmap_and_release
  定位映射/释放失败，区分回调账本、VA预留、physical handle、Python状态与原始CANN错误。
tags:
- task.debugging
- task.testing
- topic.memory
- topic.reinforcement_learning
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/camem_allocator.cpp
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device_allocator/camem.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/device_allocator/cumem.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/device_allocator/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/device_allocator/test_camem.py
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/sleep_mode.md
  role: supporting
created_at: '2026-10-29T21:37:30Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
updated_at: '2026-10-29T21:37:30Z'
---

# vLLM Ascend CaMem 映射/回调失败：VA、physical handle与GIL边界


## 触发与固定范围

CaMem初始化不可用、Expected a tuple of size 4、aclrtMallocPhysical/aclrtMapMem/aclrtUnmapMem报错、释放回调异常、sleep/wake后显存或tensor状态不符。固定Ascend ceac与原生v0.32接口。整项设备支持集合未知，保持draft/空平台；本卡只蒸馏Host C/Python桥，不宣称完成Device算子或真实CANN验证。

本次没有构建/导入扩展、分配NPU/CPU备份、制造OOM、运行回调或复现错误。保留原始CANN错误与阶段，不从静态风险推出所有环境必现故障。

## 三个资源和四字段handle

my_malloc先按设备allocation granularity将请求size向上对齐，aclrtReserveMemAddress保留VA，再分配保存aclrtDrvMemHandle的Host指针。C++把(device,alignedSize,d_mem,p_memHandle地址)送入Python malloc回调记账，最后create_and_map才申请physical内存并映射到已保留VA。

create_and_map设置PINNED/device/HBM巨大页等属性，调用aclrtMallocPhysical再aclrtMapMem；unmap_and_release先aclrtUnmapMem，再aclrtFreePhysical。sleep用这条释放physical资源而保留VA的路径；真正my_free还会aclrtReleaseMemAddress并free Host handle指针。VA稳定、physical已申请、tensor内容有效是不同事实，不能从地址没变推导权重仍在。

ensure_context只在未取得当前context时尝试创建/设置；这里未逐个检查这几项API返回，也未以代码保证已有context必属于传入device。Worker通常按自身NPU运行，跨设备新框架需核对当前context/设备与handle，不能把这个helper当通用上下文验证器。

## 先按调用阶段归因

| 阶段 | 观察的固定实现 | 故障取证重点 |
| --- | --- | --- |
| reserve/Host handle | 先保留VA并malloc handle存储 | 是否已取得地址/handle、实际对齐大小；非通用任意size校验 |
| Python malloc callback | 先登记pointer_to_data，再最终map | callback成功不证明physical已创建；callback失败或map失败没有完整通用回滚闭包 |
| physical/map | 两步分别可能抛std::runtime_error，OOM含明确错误文本 | 失败发生在Malloc还是Map、先前资源仍有哪些，不能只重置Python flag |
| Python free callback | Ascend先pop账本/清备份，再NPU同步并返回handle | 同步/回调失败时账本与实际资源可不同步，记录原始异常而非只看条目是否消失 |
| C++ my_free | 解析回调四tuple，再unmap/free physical/release VA/free Host指针 | 多步非事务；中途失败不证明后续阶段已执行 |

my_free使用自身参数中的device/size和回调的指针；源码中的recv_device/recv_size相等仅是注释，没有对应断言。四tuple解析不验证任意地址所有权、大小上界或该handle确由此实例分配；标准调用方的正确handle协议与手工裸指针调用分别对待。

## GIL、引用与错误传递不能由Python外层try代替证明

py_init_module只检查两个对象可调用，并把引用借存到全局；不INCREF管理它们。原生父类强持有bound callback属性，加上Ascend singleton，是已读寿命链的一部分。初始化另一个独立allocator实例或提前释放callback持有者不能被视为与当前实现等价。

my_malloc正常获取GIL、构造tuple、调用Python并释放GIL，再map；Python callback失败分支打印错误并返回nullptr。my_free在无有效四tuple或PyArg_ParseTuple失败的early return之前，当前源码没有执行正常路径末尾的PyGILState_Release。部分临时Python对象也没有在所读桥中成对DECREF。它们是源级清理边界，不是已测的死锁/泄漏规模或发生频率。

Python导出的python_create_and_map/python_unmap_and_release直接调用C++ helper，本桥没有显式把所有std::runtime_error转换为PyErr的统一catch。真实PyTorch pluggable allocator/CPython/CANN ABI如何传播异常需目标环境验证；不能假定Python的finally一定覆盖每个底层失败，更不能用mock抛出的Python异常替代真实跨ABI故障。

Python memcpy调用在此路径没有消费返回值来推进状态，代码还传入自身构造的dest_max；具体返回/异常约定与边界是否符合安装CANN未在本批验证。诊断保留传入的字节数/地址/方向、实际结果或异常，不把函数返回到上层当作普遍的成功证明。

## 与allocator状态和生命周期对齐

sleep的is_asleep finally、wake的map后清False、CPU备份清除和free时pop发生在不同阶段，见[CaMem接入](../../guides/integration/vllm_ascend_camem_allocator_lifecycle.md)。重复sleep不会改已睡项策略；不通过强改flag、删映射文件或仅empty_cache宣称恢复。

日志中的逻辑usage和sleep freed采样也有不同范围；额外HCCL/ACL图清理及其他进程内存不全属于这个桥。回调/physical状态未证实时停止“可继续使用该tensor”或“已释放”的结论，先恢复到目标环境验证过的完整生命周期；本卡没有执行修复操作。

## 验证信号与剩余边界

记录版本/扩展路径、调用rank/NPU/context、完整四handle、请求/对齐大小、VA/physical步骤、callback账本、备份/flag和原始错误码。分别验证正常malloc/free、offload/discard/选择性wake及每个失败边界，明确异常是否真正回到Python和资源是否可再次受控处理。

已读UT中有mock透传、NPU同步分支及NPU存在才运行的真实分配测试定义；本次未执行。CANN/torch_npu ABI、引用/GIL、并发callback、进程退出、全部硬件与模型仍未闭合，不能因来源、Lint或检索通过宣称内存安全与性能已验证。
