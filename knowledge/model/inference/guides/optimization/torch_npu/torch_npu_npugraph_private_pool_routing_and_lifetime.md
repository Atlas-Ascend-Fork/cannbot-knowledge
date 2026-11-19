---
type: Guide
title: NPUGraph私有池：选池路由、共享引用与延迟回收
description: 对照两版原生图捕获链，区分路由撤销、图引用归零、缓存释放与池对象销毁，并说明scope优先级及失败清理边界。
tags:
- task.implementation
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUGraph.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUGraph.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/MemPool.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Graph.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUGraphsUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/MemPool.h
  role: implementation
created_at: '2026-11-10T14:49:47Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# NPUGraph私有池：选池路由、共享引用与延迟回收

## 版本、入口与范围

定向核对PyTorch主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf与发布快照f3ecfe4a7ef7395754da7ca2e35661a7132b519b的NPUGraph捕获/结束/reset及默认NPU缓存分配器。主线Graph.cpp把capture_begin、capture_end、reset和pool直接绑定到此C++类，因此不是仅有未接通的辅助实现。自定义替换分配器、ACL内部算法、条件子图及Host缓存分配器基类算法不在本卡范围；未知整卡平台，保持draft与空平台，未执行捕获或测量内存。

[内存池与clone](../torchair/npugraph_ex_memory_pool_and_clone.md)解释Python选项，[Tree训练代际](../../../../training/guides/torch_npu_npugraph_training_lifecycle.md)解释输出跨代保护；它们不能替代下列底层所有权计数。

## 共享token、选池路由与活跃捕获分开记录

两版capture_begin对非零pool token要求二元组中仅一项非零，然后采用该id；未指定时得到第一项非零的新id。主线调用MemPool::graph_pool_handle(false)，发布版临时构造MemPool并读取id；已读发布版构造函数只生成id。主线graph_pool_handle也只生成token，不能把拿到token当作已经预分配显存。

主线beginAllocateToPool创建PrivatePool或要求旧池use_count>0后加一，再登记(pool id, stream filter)。get_pool在每次malloc的尺寸round之后按scope**逆序**找第一个filter匹配项，然后在该私有池small/large中选块；没有匹配项则使用默认池。主线NPUGraph filter要求该stream查询出的capture id与本图capture_id相同，辅助查询在不支持捕获/系统未初始化时返回空。

发布版beginAllocateToPool同样创建/增引用并登记filter，但get_pool按登记**正序**搜索；其图filter直接要求ACL捕获状态ACTIVE且model_ri相等。不能将主线嵌套scope的优先级套用到发布版，也不能把“在别的stream申请”直接归入这张图的池。

主线allocation_scopes_负责路由，num_active_captures_另在ACL CaptureBegin成功后增加、CaptureEnd返回后减少；路由非空本身不证明正在设备捕获。发布版hasCapturesUnderway直接返回captures_underway非空。这一区别会影响[申请重试与回收](torch_npu_allocator_retry_gc_and_oom.md)及[跨流释放](torch_npu_allocator_stream_reclaim_and_lazy_order.md)的门控，不能由池存在推导捕获状态。

## capture_end撤路由，reset释放一个使用引用

| 阶段 | 默认NPU缓存分配器中的实际变化 |
| --- | --- |
| beginAllocateToPool | 新池use_count初始1；共享活池增加1；登记路由。 |
| endAllocateToPool | 只删除匹配路由，未递减use_count，也未释放私有池。 |
| 图reset且has_graph_exec为真 | 调用releasePool减1，再请求销毁图；不能简化为capture_end后显存立即归还。 |
| releasePool使use_count到0 | 将池加入graph_pools_freeable，允许后续回收处理其可释放缓存。 |
| 回收私有池且npuMalloc_count到0 | 才从graph_pools和freeable表删除池对象。 |

PrivatePool的use_count是这层所有权/使用引用，**不是Tensor数或显存字节数**。共享图尚有引用时，清掉其中一个图不会让池满足freeable条件；即使图引用全无，仍存活Tensor占据的块、未完成事件或切分关系也可能阻止底层分配完全释放。

release_cached_blocks只处理freeable私有池；普通segment仅对没有前后切分邻居的缓存块执行底层释放，扩展段走unmap等路线。主线显式传pool id时跳过其他私有池并同步目标池事件；发布版本卡所读函数没有这个pool参数，先处理全局事件和默认缓存，再遍历freeable池。两版均等待npuMalloc_count归零才移除池。普通块释放与缓存合并的具体阶段沿用上述第14批两卡，不将freeable误读成立即aclrtFree。

主线releasePool另有force-uncached且非capture-context时的同步/回收分支；“减引用通常不直接做全池释放”不能扩大为所有配置下均无同步开销。

## 失败清理有版本和执行点边界

主线CaptureEnd返回后先markCaptureEnd、清捕获登记、撤Device/Host路由，再检查ACL返回码；发布版先检查CaptureEnd返回码，成功后才撤Device路由。主线显式清理顺序覆盖这个返回码检查点，不是任意capture_begin、filter、登记校验或reset失败都能自动恢复的事务保证。两版reset源码都提示捕获中途失败可能留下不完整状态；本卡没有执行故障注入或证明内存泄漏。

主线另向PrivateUse1 Host allocator转交同pool id的begin/end/release，并显式拒绝pin_memory_expandable_segments捕获；所查发布版这段NPUGraph没有对应Host调用。Host基类的私有池算法与配套ATen版本未在本卡闭合，不据这些调用承诺完整Host捕获兼容。

诊断图内存时记录pool id、共享图数量、成功结束/reset位置、仍保留输出和跨流消费者，再区分Tensor活跃块、池缓存与底层预留。重放顺序、跨图数据依赖和保留数值仍须独立核对；共享池本身不认证并发安全或内存总量等于最大分支。

## 主线MemPool对象的完整所有权入口

本次补齐固定主线MemPool.h/cpp全文。构造默认allocator=nullptr、is_user_created=True、use_on_oom=False、no_split=False；用户池用{0, uid_++}，图内部池用{uuid_++, 0}，两个atomic计数都从1开始，保留{0,0}作为未提供池的标记。构造按current_device保存device，调用createOrIncrefPool并移交传入shared_ptr；可选地启用use_on_oom和no_split。对象本身只保留id/device/标志，不保留另一份allocator成员；不能用拿到id或共享指针入参推定已经预分配设备内存。

graph_pool_handle只增加对应计数并返回token，没有构造MemPool，也没有调用createOrIncrefPool；这与真正构造对象的所有权行为不同。id/device getter返回已存值，use_count委托该device/id的getPoolUseCount，不统计Tensor数量或显存字节。

析构依次setUseOnOOM(false)、releasePool、emptyCache(id)。旧的use_count==1断言只在注释中，说明与图共享时计数可能更高，不能按这段注释声称当前仍强制独占；emptyCache请求也不证明所有活跃Tensor和池对象立即销毁，仍受前文默认分配器的引用及块状态约束。这里没有额外的本地事务回滚包装，外部调用行为分别核对。

头文件禁止复制，move构造和move赋值使用default声明；本地没有自定义“移动后将旧id置为无效”的函数。仅凭这些声明不认证任意C++移动用法的生命周期安全，也不把atomic ID生成当成共享池的并发执行保证。固定发布快照在这两个独立路径没有文件；发布旧MemPool定义在前述NPUCachingAllocator来源核对，图token入口在NPUGraph来源核对，不能据路径缺失说发布版没有内存池功能。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUGraph.cpp)（primary）：240–378、429–490、520–532。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp)（implementation）：783–812、980–1001、1034–1050、1229–1236、2264–2307、2324–2373、2410–2441、2732–2756、3182–3228、3248–3295、3366–3395、4074–4088。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUGraph.cpp)（implementation）：41–47、161–262、308–353。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUCachingAllocator.cpp)（implementation）：805–823、2094–2158、2431–2455、2752–2777、3500–3517、3855–3883。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/MemPool.cpp)（implementation）：5–37、62–67。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Graph.cpp)（implementation）：778–806、818–820。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUGraphsUtils.cpp)（implementation）：5–12、29–41。

- [MemPool完整原生定义](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/MemPool.cpp)（implementation）：全文1–69，补齐构造、析构、getter、token与所有权声明。

- [MemPool完整原生定义](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/MemPool.h)（implementation）：全文1–46，补齐构造、析构、getter、token与所有权声明。
