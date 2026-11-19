---
type: Guide
title: TorchNPU跨卡复制：P2P缓存、双向启用与流依赖
description: 对照两版P2P控制器和D2D调用方，区分能力缓存、连接计数、警告标志与IPC事件或同步流屏障。
tags:
- task.optimization
- topic.memory
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUPeerToPeerAccess.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUPeerToPeerAccess.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUMacros.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUPeerToPeerAccess.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUPeerToPeerAccess.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUMacros.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/CopyKernel.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/CopyKernel.cpp
  role: implementation
created_at: '2026-11-11T05:30:07Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU跨卡复制：P2P缓存、双向启用与流依赖

固定PyTorch主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf和发布f3ecfe4a7ef7395754da7ca2e35661a7132b519b，完整读取两版NPUPeerToPeerAccess.cpp/h与NPUMacros.h，定向读取两版copy_d2d完整函数。产品、拓扑与部署配套待核，保持draft、空平台；没有导入、构建设备库、启用P2P或运行复制/计时。Host↔设备复制已有[独立调用链](torch_npu_host_device_copy_execution.md)，本卡补此前未覆盖的跨卡控制器与D2D流依赖，不认证全部copy_分派、dtype/format回退或ACL内部实现。

## 缓存保存的是本地能力/启用结果

NpuP2pCtrl由函数静态get_instance首次构造，保存device_count，创建N×N状态向量和每设备连接计数。初始非对角为-1，主线名UNKNOWN、发布拼作UNKONWN；对角直接为COPY_ALLOWED=1且不计连接。拒绝状态为COPY_NOT_ALLOWED=0。方法先要求缓存已初始化、源和目标在[0,N)，然后读source→dest和反向两个位置；已知状态直接返回其bool值，不重新查拓扑或更新调用方flag。

状态表和连接计数没有在这两个完整文件中用mutex包围，不能从静态单例构造的初始化规则推导后续所有并发更新已受保护。这里也没有动态刷新设备数量、清空失败缓存或断开后递减连接数的公开方法；不能把首次探针结果当作运行期持续监测。

## 旧枚举范围的连接计数门控

两版只在GetSocVersion()<Ascend910_9391时检查连接限制，先看source计数，再看dest。达到C10_P2P_ACCESS_MAX_NPUS时，把双向缓存置拒绝，枚举该受限设备已有允许连接并记错误，然后返回False；这个分支没有把引用flag改成True。注释说A3及后续不再有此限制，本卡只记录所读枚举比较，不从该注释生成完整产品/驱动支持表。

NPUMacros.h两版都定义C10_P2P_ACCESS_MAX_NPUS=8，另有C10_COMPILE_TIME_MAX_NPUS=32；后者不是当前实际device_count，也不表示所有设备对可建立P2P。同一头还按Windows共享库、GNU可见性及C10_NPU_BUILD_MAIN_LIB选择C10_NPU_EXPORT/IMPORT/API，并令TORCH_NPU_API为C10_NPU_API别名。导出宏和编译上限不提供硬件访问能力，不能与运行时P2P探针互换。

## 双向探针、启用和部分失败

未命中缓存且未因计数拒绝时，两版都先分别调用aclrtDeviceCanAccessPeer查询source→dest及dest→source。任一结果为0则双向缓存拒绝、flag=True并返回False。两方向都报告可达，才用各自源设备的NPUGuard和flag值0依次调用aclrtDeviceEnablePeerAccess；两次checked调用都返回后，才双向置允许并各自增加计数。

这个顺序不等于原子事务：第二次启用失败时，文件没有撤销第一次启用的回滚代码，最终缓存/计数写入也尚未执行。能力查询、启用返回、缓存状态与复制完成分别记录；没有把所有错误写成自动回退成功。

## copy_d2d没有用bool返回值决定是否继续

调用方guard源设备，取得源/目标当前流。跨设备时先用warning_flag=False调用get_p2p_access，但没有读取它的bool返回值，只在flag为真时记警告。因此计数拒绝、已缓存的拒绝、首次双向能力拒绝和成功并非都能从一条warning_flag恢复；没有警告也不证明该次调用已经新启用了P2P。

源码注释说同一OS中即使enable失败Tensor也可copy；实际本地控制流在得到False时仍继续后续复制，并没有由这个False选择显式CPU中转。不能把注释或继续派发当成所有环境必然复制成功，真实ACL、拓扑和所调用dtype路径仍需验收。

## 复制前后是两段流依赖

跨设备复制前，先保证目标当前流的先前工作与源流中的copy有顺序关系；正常同dtype复制后，再让目标流等待源流中的copy。所读同dtype路径调用copy_d2d_dtype，未在这里展开其内部kernel/布局算法。

| 固定版本条件 | 复制前 | 同dtype复制后 |
| --- | --- | --- |
| 发布IsSupportIpcEvent为真 | 在目标流record事件，再在源流block | 在源流record事件，再在目标流block |
| 主线IsSupportIpcEvent为真且SoC不等于Ascend950 | 同上 | 同上 |
| 对应其余分支 | guard目标设备并同步目标流，然后回源设备 | 同步源流 |

主线对Ascend950系列（包含旧称Atlas A5）对应的精确Ascend950枚举排除IPC事件路线，注释限定单进程多设备D2D。这里是精确不等比较，不把它改成所有后续SoC均排除，也不据发布版没有该条件认证发布与该产品配套。流事件记录/等待和阻塞Host同步有不同开销，non_blocking参数没有取消这里由跨设备分支选择的依赖。

若dtype不同，copy_d2d在前半段依赖处理后调用npu_dtype_cast_并立即return，不会继续执行本函数下半段同dtype后置依赖。注释说dtype cast会调用copy；其完整递归/分派消费者未在本卡闭合，不能把表中后置协议无条件套到所有dtype转换。

同设备分支跳过P2P与跨卡依赖。优化评估保存准确包/SoC/拓扑、两个设备与当前流、缓存首次或命中状态、dtype及真实同步测量，再区分探针、Host等待与设备数据搬运。本文没有把允许状态、无警告或接口存在写成吞吐/数值/并发验收。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUPeerToPeerAccess.cpp)（primary），读取范围 1–120。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUPeerToPeerAccess.h)（implementation），读取范围 1–40。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/NPUMacros.h)（implementation），读取范围 1–34。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUPeerToPeerAccess.cpp)（implementation），读取范围 1–119。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUPeerToPeerAccess.h)（implementation），读取范围 1–42。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/core/npu/NPUMacros.h)（implementation），读取范围 1–34。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/CopyKernel.cpp)（implementation），读取范围 297–359。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/CopyKernel.cpp)（implementation），读取范围 281–341。
