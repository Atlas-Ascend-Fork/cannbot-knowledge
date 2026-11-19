---
type: Guide
title: GE外部分配器：按流共享feature内存与释放时机
description: 区分stream注册、固定和可刷新图内存、容量复用及引用计数，解释图销毁与NPU缓存分配器释放的边界。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/AllocatorManager.cpp
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/AllocatorManager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/memory/Allocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/memory/Allocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/static_npu_graph_executor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/static_npu_graph_executor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/dynamic_npu_graph_executor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/dynamic_npu_graph_executor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/memory/Allocator.h
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/third_party/ascend/include/metadef/external/ge/ge_allocator.h
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/concrete_graph.cpp
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/memory/util/object_allocator.h
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/memory/util/link.h
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/memory/util/link_node.h
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/memory/Allocator.h
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/memory/util/object_allocator.h
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/memory/util/link.h
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/memory/util/link_node.h
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/third_party/ascend/include/metadef/external/ge/ge_allocator.h
  role: constraint
created_at: '2026-11-10T11:48:48Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE外部分配器：按流共享feature内存与释放时机

## 固定版本与审阅范围

定向核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的外部分配器与静态/动态图调用点。AllocatorManager及memory/Allocator.cpp的所述核心逻辑在两版一致；主线额外保留GE管理图内存的关闭分支。

这里只静态读选定路径及随仓GE MemBlock头文件，没有导入、编译、设备、并发或显存实验；不展开NPUCachingAllocator全部实现。平台范围未知，保持draft与空平台。

## 注册表按stream绑定allocator

EnsureAllocatorRegistered用mutex保护注册表，按void* stream查找；已注册直接返回原allocator，否则创建NpuAllocator(stream)，向Session注册成功后才写入表。它不是每次Run都新建一个分配器，也不是只按模型名或图ID隔离图内存。

NpuAllocator::Malloc把size和保存的stream_交给NPUCachingAllocator::MallocBlock，再用GetBlockPtr/GetBlockSize包装成NpuMemBlock。Free最终调用FreeBlock并归还包装对象到对象池，不能由此直接断言显存立即归还设备驱动。容量、保留引用、分配器统计与设备已分配显存需分别观察。

## feature/fixed池按容量共享块

MallocFeatureMemory按is_fixed选择fixed_mem_pool_或feature_map_mem_pool_；遍历std::set中的第一个GetSize()足够的块，直接AddCount并返回，否则才Malloc新块并加入池。集合存的是指针，这不是按容量排序的best-fit，也没有在复用前要求use count为0或检查空闲标志。

因此该层复用包含同一allocator中多个持有者共享同一内存块，不能把它当成每张图独占的工作区。引用计数只说明块还有多少持有，不保证不同执行在该地址上可无序重叠。静态/动态执行器又限制同一实例后续使用首次stream；对重叠、嵌套和多线程执行需要结合真实流顺序验证。

随仓MemBlock从count=1开始，AddCount递增，Free在递减到0时才回调allocator.Free。FreeFeatureMemory先确认块属于所选池，未找到直接返回；找到后Free并在count为0时从池删除。它不是按图名无条件释放所有共享feature内存。

注册表mutex与Malloc/Free内部包装对象池mutex不能替代整个共享池的并发合同：本层feature/fixed集合遍历和MemBlock普通计数没有同一套完整锁保护。本卡不据此宣称已复现竞态，也不认证任意并发使用安全。

## 静态图的常量与feature生命周期

首次静态Run分配const memory并设置SetGraphConstMemoryBase；const块由独立持有者及deleter管理。feature memory则按summary.GetFeatureMemoryBaseRefreshable区分：

- 不可刷新时首次用MallocFeatureMemory取得池中块，后续指针非空就复用，不重复UpdateGraphFeatureMemoryBase。
- 可刷新时每次用普通Malloc分配并UpdateGraphFeatureMemoryBase，成功运行尾部调用Free并清空本地指针。

因此一次运行后仍看到常驻feature占用可能是不可刷新共享块或底层allocator保留，不能只看free日志判定泄漏或完全释放。可刷新块的成功尾部释放也不是异常路径的完整恢复证明；需要检查失败发生位置和对象销毁，不从正常尾部推导任何错误都已清理。

静态析构和动态析构会遍历注册allocator，尝试FreeFeatureMemory释放各自持有的池引用，再清空本地指针。动态执行器首次设置的fixed feature块也来自fixed池；图实例销毁、共享计数归零和底层缓存归还驱动是不同事件。

## 主线GE自管内存分支

主线NpuConcreteGraph::Create识别内部选项torchair.disable_external_mem_base，值等于字符串1时设标志，并从传给GE的compile选项中移除。静态执行器据此跳过外部const和feature基址准备，但仍为运行stream注册allocator；动态执行器首次跳过外部fixed feature基址设置。发布快照没有这组分支，不能将其作为发布版配置配方。

这个标志改变的是对应图内存基址管理，不是关闭所有Torch/NPU分配、用户输出缓冲或Host复制；也不代表已经证明某种融合模式在目标环境可用。它是内部实现入口，本卡不把它新增为通用公开调优开关。

验证显存优化时同时记录执行器类型、实际stream、const/feature/fixed各自大小、refreshable标志、共享块地址/计数及输出存活引用，再比较稳定负载下峰值和稳态占用。这里没有给出节省比例或设备支持认证。

- [动态执行器I/O与所有权](torchair_cpp_dynamic_executor_inputs_and_output_ownership.md)
- [静态输出分配与同步](torchair_cpp_static_executor_host_outputs.md)

## Evidence

- 两版AllocatorManager.cpp、memory/Allocator.cpp的注册、Malloc/Free、feature/fixed池逻辑；固定源SHA和定向范围见入库清单。
- 两版static_npu_graph_executor.cpp与dynamic_npu_graph_executor.cpp的内存准备、成功尾部与析构调用点。
- 主线memory/Allocator.h的池类型、随仓ge_allocator.h的MemBlock计数，以及concrete_graph.cpp的内部标志解析；不表示底层分配器或整个GE执行栈全文审计。

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/AllocatorManager.cpp)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/AllocatorManager.cpp)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/memory/Allocator.cpp)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/memory/Allocator.cpp)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/static_npu_graph_executor.cpp)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/static_npu_graph_executor.cpp)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/dynamic_npu_graph_executor.cpp)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/dynamic_npu_graph_executor.cpp)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/memory/Allocator.h)（constraint）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/third_party/ascend/include/metadef/external/ge/ge_allocator.h)（constraint）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/concrete_graph/concrete_graph.cpp)（constraint）

## 完整Host对象池的容量不等于显存容量

本节补双版memory/Allocator.cpp、Allocator.h、三个util头文件及随仓ge_allocator.h的完整本地合同。主线六文件合682行；发布同样682行。Link、LinkNode和GE接口两版逐字节相同，其他三个文件的完整raw差异只有include次序或格式；不把本地定义相同推成任意外部头文件/构建环境都等价。原执行器与AllocatorManager来源仍按既有定向范围，不因读完辅助头文件提升整个GE或TorchNPU分配器资格。

NpuAllocator默认用kMemBlockPoolSize=10240初始化ObjectAllocator<NpuMemBlock>，保存stream，禁止复制/移动；NpuMemBlock额外持有NPUBlock handle，GE基类保存地址、块容量与allocator引用。这10240是Host包装槽的预分配目标，不是预留10240个设备块，更不是显存字节数或严格并发分配上限。

ObjectAllocator构造逐项new(nothrow) Element，成功才入空闲链，失败项没有自动补齐。Alloc/AllocMem先弹空闲链，耗尽再new Element；GetAvailableSize只反映当前空闲链的计数。析构只删除仍在空闲链里的Element，没有另外遍历所有已借出槽位；不能把对象池析构视作已自动回收全部活跃设备块。

Element以union复用LinkNode和sizeof(T)字节的缓冲。Alloc和AllocMem只给原始存储，不构造T；New才在AllocMem上placement new。Free显式调用T析构再FreeMem回空闲链，FreeMem本身不析构。这个模板没有锁，NpuAllocator仅在包装的Alloc/Free处加allocator_mutex；free-list的复用不替代前文feature/fixed共享池的计数及流顺序合同。

## 包装失败与引用归零后的观察边界

Malloc先调用NPUCachingAllocator::MallocBlock，返回nullptr才直接退出；成功后在ObjectAllocator::Alloc给出的地址placement new NpuMemBlock。源码中的mem_block==nullptr判断位于这个构造之后，没有先显式检查Alloc返回地址。包装存储获取失败不能笼统描述成“必定安全记录日志并返回”，本函数的这条后置失败分支也没有显式FreeBlock回滚语句；没有注入分配失败或执行构造测试。

Free的dynamic_cast只区分能否视为NpuMemBlock，nullptr或其他类型就记录并返回；它没有在这个函数另外验证块来自当前这个allocator实例。成功路线先FreeBlock(handle)，然后在锁内调用对象池Free销毁包装并回链。调用者须遵守实际归属与借用合同，不能把类型转换成功理解为已完成任意跨池归属验证。

随仓ge::MemBlock从count=1开始，AddCount/SubCount是普通size_t加减；SubCount本身不作零检查，Free另先检查count>0，只在减到0时回调保存的allocator.Free(this)。MallocAdvise的默认实现忽略建议地址并直接调用Malloc；MemBlock::SetSize只是写容量字段，未在这个方法重新分配设备内存。

将这条链连回FreeFeatureMemory：block->Free在归零时可以已经进入NpuAllocator::Free、执行NpuMemBlock析构并把同一槽位回空闲链，外层随后仍调用block->GetCount来决定erase并记录日志。这里明确保留“回调销毁在先、旧包装方法读取在后”的静态生命周期边界；不能只看Host内存槽还留在对象池就认证对象寿命仍有效。没有复现并发、分配错误或设备故障，也没有修改上游实现。

## intrusive链表是非拥有容器，不能增加未实现的不变式

Link用指针偏移构造环形sentinel，空表头尾均指向sentinel，size单独保存在num_。front/back在空表返回nullptr；正/反迭代器保存当前节点和下一步节点，前后置递增分别返回相应位置，解引用没有空值保护，也不取得节点所有权。链指针虽声明volatile，这些文件没有std::atomic或内部mutex。

push_front/back连接节点并增加num_，Iterator重载直接委托相同操作；pop_front先判begin==end，非空才erase并返回被摘节点。Link::remove在LinkNode::remove更新前后邻居后减计数；裸LinkNode::remove不更新任何Link的num_，也不把自己的指针清空。erase只对空指针Iterator早返回，没有单独把end sentinel或外部节点排除；不能把这些低层方法视为带成员归属、重复摘除或并发合法性验证的通用容器API。

clear只反复摘除节点，不delete用户节点。move赋值先reset目标，再concat来源；reset只重置头尾和num_，不删除原节点。concat把来源尾接到目标sentinel、将来源首的prev设为目标sentinel，再连接目标旧尾的next并累加计数，最后reset来源。因此目标原来非空时，这段代码没有把来源首的prev设为目标旧尾，不能宣传为已证明普通双向拼接的全部前后链接不变式。

当前ObjectAllocator用到的是push/pop/empty/size路径；完整读取其他链表接口，是说明本地实际合同和边界，不等于模型热路径一定执行concat、move或任意erase，也没有由这些辅助函数推出显存节省或吞吐收益。验证时分别记录设备块地址/容量、Host空闲槽数、实际持有计数和释放/归还时点，再按前文真实执行器路线观察；没有运行这些实验或新增verified。

## 完整对象池与接口源码证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/memory/Allocator.cpp)（implementation）：1–117；完整本地文件，被调外部实现另计。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/memory/Allocator.h)（constraint）：1–59；完整本地文件，被调外部实现另计。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/memory/util/object_allocator.h)（implementation）：1–83；完整本地文件，被调外部实现另计。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/memory/util/link.h)（implementation）：1–300；完整本地文件，被调外部实现另计。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/torchair/npu_graph_executor/memory/util/link_node.h)（implementation）：1–47；完整本地文件，被调外部实现另计。
- [固定实现 6](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/third_party/ascend/include/metadef/external/ge/ge_allocator.h)（constraint）：1–76；完整本地文件，被调外部实现另计。
- [固定实现 7](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/memory/Allocator.cpp)（implementation）：1–117；完整本地文件，被调外部实现另计。
- [固定实现 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/memory/Allocator.h)（constraint）：1–59；完整本地文件，被调外部实现另计。
- [固定实现 9](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/memory/util/object_allocator.h)（implementation）：1–83；完整本地文件，被调外部实现另计。
- [固定实现 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/memory/util/link.h)（implementation）：1–300；完整本地文件，被调外部实现另计。
- [固定实现 11](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/torchair/npu_graph_executor/memory/util/link_node.h)（implementation）：1–47；完整本地文件，被调外部实现另计。
- [固定实现 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/third_party/ascend/include/metadef/external/ge/ge_allocator.h)（constraint）：1–76；完整本地文件，被调外部实现另计。
