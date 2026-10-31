# Device 管理 API

Device 指定、查询与 Reset 相关接口。

- [aclrtSetDevice](aclrt_set_device.md)：为当前线程指定运算 Device。
- [aclrtResetDevice](aclrt_reset_device.md)：释放 Device 资源（需 SetDevice 配对）。
- [aclrtResetDeviceForce](aclrt_reset_device_force.md)：强制释放 Device 资源。
- [aclrtGetDevice](aclrt_get_device.md)：获取当前线程 Device ID。
- [aclrtGetDeviceCount](aclrt_get_device_count.md)：获取 Device 数量。
- [aclrtGetRunMode](aclrt_get_run_mode.md)：获取运行模式（Host/Device）。
- [aclGetDeviceCapability](acl_get_device_capability.md)：查询对应 Device 的硬件规格大小。
- [aclplatformGetDeviceInfo](aclplatform_get_device_info.md)：查询 AI 处理器型号的硬件信息。

- [aclrtGetDeviceInfo](aclrt_get_device_info.md)：获取指定 Device 的指定属性；attr 为 aclrtDevAttr 枚举，内部分两条路径，可映射为 (moduleType, infoType) 的走向 rtGetDeviceInfo，其余走 Misc 分支，未识别的 attr 返回 ACL_ERROR_RT_PARAM_INVALID。

- [aclrtDeviceCanAccessPeer](aclrt_device_can_access_peer.md)：查询两个 Device 之间是否支持 P2P 数据交互；ACL 层先拒绝 deviceId 等于 peerDeviceId，并把 peerDeviceId 转成物理 ID 再查询，芯片未开放 P2P、离线模式或无有效 Context 时会直接报错而不是返回 0。
- [aclrtDeviceEnablePeerAccess](aclrt_device_enable_peer_access.md)：开启当前 Device 到指定 peer Device 的单向 P2P 数据交互；flags 必须为 0，ACL 层取当前 Device 并把 peerDeviceId 转成物理 ID 后调用 rtEnableP2P，Device 级单向生效。
- [aclrtDeviceGetHostAtomicCapabilities](aclrt_device_get_host_atomic_capabilities.md)：查询指定 Device 与 Host 之间支持的原子操作详情；capabilities 为位掩码数组，实现先把数组清零再按 operations 索引填充，不支持（拓扑非 UB 或驱动不支持查询）时返回成功但数组保持全 0。
- [aclrtDeviceGetLimit](aclrt_device_get_limit.md)：获取当前进程的 Device 资源限制；ACL 层要求 value 非空且 limit 在 [0,4]，查询的是进程内瞬时配置（不一定等于已生效值），不支持的资源类型返回 ACL_ERROR_RT_FEATURE_NOT_SUPPORT。
- [aclrtDeviceGetP2PAtomicCapabilities](aclrt_device_get_p2p_atomic_capabilities.md)：查询同一 AI Server 内两个 Device 之间支持的原子操作详情；实现先清零 capabilities 再按 operations 索引填充，仅当两 Device 拓扑为 HCCS/SIO/HCCS_SW/UB 时视为支持，拓扑查询失败会直接报错。
- [aclrtDeviceGetStreamPriorityRange](aclrt_device_get_stream_priority_range.md)：查询 Stream 优先级的取值范围；固定实现直接返回常量（最低 7、最高 0），允许传入空指针并跳过对应输出，不向硬件发起查询。
- [aclrtDeviceSetLimit](aclrt_device_set_limit.md)：设置当前进程的 Device 资源限制（SIMT 栈空间、Printf 维测空间等）；ACL 层校验 limit 在 [0,4] 且 value 不超过 UINT32_MAX，内部固定用 Device0 设置，不支持的资源类型返回 ACL_ERROR_RT_FEATURE_NOT_SUPPORT。
