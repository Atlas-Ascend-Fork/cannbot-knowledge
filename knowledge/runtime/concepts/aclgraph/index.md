# ACL Graph（流捕获）

ACL Graph 特性的概念卡：将 Stream 任务序列捕获为可复用图、下沉 Device 执行以减少 Host 下发开销。基于固定来源提交的源码核验（设计文档作导读，冲突以源码为准）。

- [ACL Graph 捕获-执行分离模型与整体架构](overview.md)：捕获-构建-执行三阶段分离、价值与收益、核心对象（CaptureSession 捕获入口/CaptureModel/Stream captureStatus/级联流/TaskGroup/Notify）。
- [ACL Graph 单流捕获与级联流机制](stream_capture_mechanism.md)：说明捕获期任务记录、级联流的资源容量限制，以及 Software SQ 的按需绑定、回放复用与条件释放。
- [ACL Graph 捕获模式与状态机](capture_modes_and_status.md)：说明不安全操作的限制范围、结束捕获的线程约束，以及 Stream 和 CaptureModel 两级状态判定。
- [ACL Graph 跨流捕获与 Event/Notify 同步](cross_stream_and_events.md)：通过 Event 把多流织入同一图、捕获期 Event 处理与 captureEvents_，以及执行期 Notify 的执行前/后同步。
- [ACL Graph TaskGroup 任务组与模型更新](task_group_and_update.md)：区分任务组更新与模型级参数修改，说明 CanUpdate 条件及 UPDATING 经 aclmdlRIUpdate 转为 READY 或 FAULT 的顺序。
- [ACL Graph 条件控制流（IF/WHILE/SWITCH）与子模型](conditional_control_flow.md)：CondHandle 持 device 条件值与子模型列表、子模型共用 Notify、资源随父模型管理，以及条件任务 SQE 结构。
