---
type: Guide
title: vLLM Ascend CaMem 接入：池标签、CPU备份、选择性唤醒与分配所有权
description: 沿 CaMemAllocator、AllocationData 与 pointer_to_data 接入sleep，区分 weights/kv_cache、自定义tag、is_asleep、CPU备份和逻辑usage，核对原生v0.32父类与NPU覆写差异。
tags:
- task.implementation
- task.debugging
- topic.memory
- topic.reinforcement_learning
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device_allocator/camem.py
  role: primary
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/device_allocator/cumem.py
  role: implementation
- resource: https://github.com/vllm-project/vllm/blob/5df63a7203cdb9328d824a27b682e77c7b9928be/vllm/device_allocator/__init__.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/camem_allocator.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/worker/worker.py
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/platform.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/docs/source/user_guide/feature_guide/sleep_mode.md
  role: supporting
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/device_allocator/test_camem.py
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
aliases:
- CaMem Level2
---

# vLLM Ascend CaMem 接入：池标签、CPU备份、选择性唤醒与分配所有权


## 任务、固定版本与范围

新模型/RL框架要释放推理显存、分阶段恢复权重/KV，或遇到sleep后读到无效内容、选择性wake遗漏自定义状态。固定Ascend `ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2` 与原生vLLM v0.32.0 `5df63a7203cdb9328d824a27b682e77c7b9928be`；两个提交不自动证明全部wheel/torch_npu/CANN组合兼容。整项平台未取得证据，保持draft/空平台。

本卡是Host分配器与调用接口知识，未编译、导入上游、创建MemPool、调用CANN或运行CPU/NPU测试。NPU映射、图和分布式结果要另做目标环境验证。

## 能力声明、池入口与回调寿命

AscendPlatform.is_sleep_mode_available和is_cumem_allocator_available直接声明True，后者为了早期ModelConfig校验避免导入扩展。真实CaMem模块仍须导入vllm_ascend_C及取得库路径；camem_available和get_instance门禁、NPUPluggableAllocator实际初始化各有失败阶段，不能把平台声明当扩展已加载或所有设备可用。

CaMemAllocator继承CuMemAllocator，但get_instance是进程singleton；C扩展只存全局回调引用，多个独立实例会覆盖回调归属。固定父类__init__把self._python_malloc_callback/self._python_free_callback绑定到强引用属性，避免临时bound-method对象被回收；动态绑定的free回调使用Ascend覆写，在返回handle前同步对应NPU。

use_memory_pool(tag)设置current_tag，创建NPUPluggableAllocator/MemPool并持有引用，退出时恢复原tag。它只覆盖该上下文中的分配，不意味着模型所有元数据/外部库/通信/图内存均被这套池管理。PYTORCH_NPU_ALLOC_CONF包含精确字符串expandable_segments:True时当前Ascend构造拒绝；原生新父类的临时配置改写/trim行为不能直接套到此覆写。

Worker.load_model在启用sleep时要求allocator.get_current_usage()==0，再进weights池；错误原文为Sleep mode can only be used for one instance per process. 加载期间暂时把torch.npu.empty_cache替成空操作以绕过pluggable池限制。该路径同时覆盖所述Runner加载lane，不是任意模型并发创建都可复用同singleton的保证。

KV通过initialize_kv_cache的kv_cache_allocation_context只包装backing分配，持久元数据和zeroing bookkeeping留在可丢弃KV池之外。文档overview的weight单数不作为API tag，实际Worker和阶段接口用weights/kv_cache。自定义模型必须核对实际分配上下文与访问寿命，不能靠buffer名称猜tag。

## AllocationData与容量口径

AllocationData包含handle、tag、cpu_backup_tensor和is_asleep。handle为(device,aligned_size,address,physical-handle指针整数)的Ascend四字段约定；pointer_to_data按虚拟地址记账，malloc回调在C++最终physical map之前登记。

继承的get_current_usage累计所有handle大小，包括is_asleep项；它是逻辑账本字节，不是物理HBM占用或当前可释放字节。源代码的free NPU采样、整个进程HBM与这份统计分别记录，不能看到sleep后usage未降就判泄漏，也不能看到记录消失就宣称CANN已退役。

## offload、discard与选择性wake

| 操作 | 固定实现动作 | 消费边界 |
| --- | --- | --- |
| sleep(offload_tags) | 同步当前NPU；匹配tag逐项建pinned CPU字节备份/D2H，所有未睡项尝试unmap/release | 未匹配项丢内容；默认参数是default tag，Worker Level1显式传weights，Level2传空tuple |
| discard(tags) | 对所选已映射项按handle设备同步，再unmap/release，不备份 | 不将别的tag统一睡眠；已睡且有备份时不能靠discard改为无备份策略 |
| wake_up(tags) | 对选中的已睡项在保留VA上create/map，有CPU备份再H2D并清备份 | 没备份只恢复空内容的分配，不自动恢复模型/KV数值；不是清零承诺 |

重复sleep/discard不改变已睡项的offload/discard策略，只检测冲突并warning。第一次Level1后权重已有CPU备份，后续不同offload_tags不能被当成已重新执行Level2策略；要先按真实状态恢复或重建。

Ascend wake只处理tags=None或data.tag in tags。原生v0.32父类还会唤醒不在DEFERRABLE_TAGS中的其他tag，Ascend覆写没有这条额外条件；新模型自定义workspace/default tag不能照搬原生选择性wake假设。tags=[]在Ascend不恢复任何项，但日志使用tags or all，可能显示all；以restore_count和逐项状态为准，不以该文本认定全醒。

Python sleep在unmap调用的finally里设is_asleep=True；wake在map返回后、H2D之前清False。异常可留下“已标睡但退役未证实”或“已映射但备份恢复未证实”的中间态。这是Python控制流；真实C++/CANN异常是否安全转成Python异常未验证，不能声称所有底层失败均会经过这些finally。详细探针见[映射与回调排障](../../runbooks/runtime/vllm_ascend_camem_mapping_callback_failure.md)。

## Worker内容保留与Level2阶段

Level1清临时saved参数/buffer记录，只备份weights池；Level2先按sleep_preserve_parameter_names的fnmatch模式保存发送方可能省略的非CPU参数，并保存named_buffers。无匹配pattern会抛ValueError；并非任意私有对象、未命名张量或模型全部状态都自动保留。

wake仅在tags=None或含weights时恢复这些参数/buffer；只醒kv_cache不能提前消费权重备份。Level2按weights→外部重新加载/更新全部所需权重→kv_cache继续；分配映射恢复本身不证明外部权重完整、版本一致或新架构可在原模型对象内任意替换。

固定Worker实际wake顺序为allocator→按KV tag重注册transfer buffer→恢复保留参数/buffer→额外清理manager的HCCL/图恢复→最终设备同步。额外清理中的锚点、MoE runtime和图阶段见[HCCL/图恢复](vllm_ascend_sleep_hccl_graph_recovery.md)，不能把文档概述顺序当作这条调用链的逐行顺序。

## 退出和验收

release_pools先移除/释放MemPool引用并gc，同时强持有allocator wrappers，再释放wrappers；atexit调用该路径。它是特定Python所有权次序，不等于所有活动tensor、captured graph、外部CANN handle和进程都已清理。原生父类保存每tag的pool列表并有CUDA graph池/trim接口，Ascend覆写是每tag一份tuple；继承方法存在不证明全部原生CUDA/ROCm路径已在NPU接通。

验收按每tag记录分配VA/handle/对齐大小、CPU备份、睡眠/映射/内容状态及真实HBM，再对比Level1输出和Level2权重版本。320行test_camem定义混合mock与NPU条件测试，覆盖选择性custom tag、回调同步、重复release等；本次未执行，不把条件fixture或上游断言当作本环境NPU结果。
