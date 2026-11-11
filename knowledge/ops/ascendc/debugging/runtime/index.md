# 运行时调试（runtime-debug）

- [Host Runtime 故障排查的证据纪律与错误码分流](evidence_discipline_and_error_routing.md)：从最早失败 Host 调用开始；返回码只定检查方向；先保存 aclGetRecentErrMsg 等不重现证据；连续失败不只保留最后一个；161/561 系错误码分流取证。
- [Host Runtime 专题：Event 零超时语义、MemcpyAsync 返回边界与资源生命周期](runtime_topics_event_memcpy_lifecycle.md)：Event timeout=0 返回 107000 实测语义、ExWithFlag 创建限制与复用错轮成对检查、MemcpyAsync 按锁页/非锁页分配族二分返回边界、部分初始化失败只清理已取得所有权的对象。
