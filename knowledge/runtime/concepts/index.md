# 概念

CANN Runtime 核心层的架构与机制概念卡，基于固定来源提交的源码核验（设计文档作导读，冲突以源码为准）。

- [Runtime 分层架构与进程/对象模型](layered_architecture.md)：API/Feature/Core/Driver 四层结构、rt*/aclrt*/aclmdlRI* 三类接口前缀，Runtime 单例→Device→Context→Stream 对象模型；Primary Context 与 Device 按 [Device][TS] 维护，"每个设备一个 Primary Context"仅为单 TS 简化。
- [Stream SQ/CQ 异步执行与任务回收机制](stream_sqcq_async_mechanism.md)：按平台、发送回收模式与绑定状态区分等待路径，说明 Stars 的 SQ head 轮询、关注任务回收及正常 Event 的 CQE。
- [Context 线程关联与 Primary Context 引用计数模型](context_thread_binding_model.md)：默认/用户两类 Context 形态、经 TLS（curCtx_/curRef_）的线程关联、Primary Context 按 [Device][TS] 引用计数复用，以及 6 态生命周期状态机与 USER/INTERNAL 访问模式。
- [Device 生命周期、资源池与回收线程](device_lifecycle_and_resources.md)：Device 的 Init→Start→Stop 生命周期（接口纯虚、RawDevice 实现）、每 Device 持有的 Engine/MemoryPool/EventPool/DeviceSqCqPool/TaskFactory 资源池，以及按 Device 粒度运行的任务回收线程。
- [Memory 分配策略、拷贝语义与虚拟内存模型](memory_allocation_model.md)：说明分配策略、内存池、虚拟内存与 IPC 共享，区分锁页 Host 内存异步下发和非锁页 Host 内存同步回退。
- [Task 任务类型、资源管理与下发回收模型](task_management_model.md)：以 TaskInfo 承载的五类任务、Device 粒度（TaskFactory→TaskAllocator）与 Stream 粒度（TaskResManage）两层资源管理、按驱动版本注册的处理函数，以及 Alloc→填充→组 SQE→下发→回收生命周期。
- [Event 跨流与跨进程同步机制](event_synchronization_model.md)：Event 在 Stream 记录位置、其他 Stream 等待实现跨流同步，支持 Host 阻塞 Synchronize、状态查询、计时与 IPC 跨进程同步，Event Flag 决定创建分支与同步行为。
- [Kernel 二进制加载与执行模型](kernel_program_loading_model.md)：BinaryLoader→Program（ElfProgram/PlainProgram）→Kernel→KernelTable 的注册查找体系、按名称与按标识/tilingKey 两种查找、Program::Load2Device 设备加载，以及由 Program 基地址计算设备侧函数地址。

- [ACL Graph（流捕获）](aclgraph/index.md)：共 6 张知识卡，覆盖 ACL Graph 的捕获-执行分离模型与架构、单流/级联流捕获、捕获模式与状态机、跨流 Event/Notify 同步、TaskGroup 与模型更新，以及 IF/WHILE/SWITCH 条件控制流。
