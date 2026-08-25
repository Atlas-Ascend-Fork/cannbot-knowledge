# 同步控制

- [核间同步](inter_core_sync/index.md)：核间同步场景中向调度模块上报本核前置pipe流水任务已完成，与CrossCoreWaitFlag配对使用，通过flagId控制核间同步。
- [任务间同步](inter_task_sync/index.md)：任务间同步接口索引页，包含SetNextTaskStart与WaitPreTaskEnd。
- [核内同步](intra_core_sync/index.md)：从框架获取并占用一个MutexID，与ReleaseMutexID配合使用，获取的MutexID可传入Mutex::Lock/Unlock接口用于流水同步。
- [同步控制](sync_control.md)：同步控制接口集合，涵盖系统同步概述、核内同步、核间同步和任务间同步。
- [系统同步能力概述（同步控制）](system_sync_overview.md)：在编程中，同步是指协调多个执行单元（如线程、进程等）对共享资源的访问顺序和时机来确保程序的正确性。如果没有同步来严格控制执行顺序，则会出现结果不一致、行为不可预测等多种问题。
