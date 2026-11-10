---
{
  "type": "Runbook",
  "title": "fx_converter ExecuteAlloc 的 AdoptedDrainGuard 多流读者释放竞态：drain 前 aclrtSynchronizeStream 修复 fallback 中间态被缓存分配器复用导致的非确定性 MTE/SIGBUS",
  "description": "GE ModelV2 执行器（StructuredTopological）多流并行调度时，ExecuteAlloc 返回即触发 AdoptedDrainGuard 清空 adopted ledger，未被收割为模型输出的 fallback 中间态提前归还 torch 缓存分配器，跨流读者可能读到复用后的内存，产生非确定性设备 MTE/宿主 SIGBUS。修复是在 drain 之前对调用方流执行 aclrtSynchronizeStream（执行器把子流合流记录在该流上，等待即覆盖全部子流）。修复与其余缺陷修复共同落地后，最终 rerun9 全部 271 个 AF kernel launch 成功且无宿主崩溃。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "910"
  ]
}
---

# fx_converter ExecuteAlloc 的 AdoptedDrainGuard 多流读者释放竞态：drain 前 aclrtSynchronizeStream 修复 fallback 中间态被缓存分配器复用导致的非确定性 MTE/SIGBUS

## 适用场景

- 框架/栈：torch-npu（fxrt bridge，torch_npu 2.13.0+git6a32e81 自建 wheel）+ fx_converter（fxrt 仓 `fx_converter/src/api/fx_converter_api.cc`）+ GE ModelV2 执行器（ge-om2-dynamic-experiments 13b06c5768c9 本地构建）；CANN 9.2.0（`${CANN_INSTALL_ROOT}`）。
- 平台：Atlas 910B3（8 卡，`ASCEND_RT_VISIBLE_DEVICES=2`），aarch64，npu-smi 26.1.0.b050。
- 工作负载：动态 T5（t5-v1.1-xxl）经 torchair/_inductor_npu_ext + AutoFuse 的 rt2 模式（T5_RUN_MODE=rt2，runner=ModelV2Runner），AUTOFUSE_FLAGS="--enable_autofuse=true;--autofuse_enable_pass=matmul,reduce,concat;"。
- 缺失信息：该修复在私有 fxrt/fx_converter 工作区（${LOCAL_PATH_1}）上验证，未在其它 CANN/GE 版本上复验。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

路径补充：。按本地环境设置变量，保留文中的相对路径关系。

路径补充：`${CANN_INSTALL_ROOT}` 为当前环境实际使用的 CANN 安装根目录，按本地安装设置。

## 触发与观测

图执行阶段出现**非确定性**宿主 SIGBUS（Bus error, core dumped，run 间结果不同）与设备侧 MTE（`RuntimeError: npuSynchronizeDevice:torch_npu/csrc/core/npu/NPUStream.cpp:737 NPU function error: SUSPECT REMOTE ERROR, error code is 507057`，事件 2088/2123；plog 中 `EZ9999 ... the error is aicore error ... error code = 0x800000 ... MTE accesses an invalid GM address`）。SplitDiag 统计显示单次执行物化 565 个 fallback 中间态（288 个 67108864 字节 + 144 个 167772160 字节，约 42GB，事件 2728）——这些 buffer 未被收割为模型输出，其生命周期完全由 adopted ledger 管理。

## 探针与操作

修复前 `ConverterSession::ExecuteAlloc`（fx_converter_api.cc，事件 2681 读取的原文）：

```
  NoteFallbackExecuteBoundary();
  // Adopted fallback storages not harvested as model outputs (graph
  // intermediates) are released when this execute returns, on every exit path.
  struct AdoptedDrainGuard {
    ~AdoptedDrainGuard() { fx_converter::AbiDrainAdoptedOutputs(); }
  } adopted_drain_guard;
```

配套机制：`AbiNoteAdoptedOutput` 把 (addr, owner) 记入 thread_local 的 `g_adopted_ledger`；`AbiDrainAdoptedOutputs()` 直接 `g_adopted_ledger.clear()`，释放 owner 引用、最后引用析构时销毁 bridge 结果（torch 缓存分配器回收内存）（事件 2675）。

修复（事件 2705，写入 `fx_converter_api.cc` 的原文，已用 reader 复核）：

```
  NoteFallbackExecuteBoundary();
  // Adopted fallback storages not harvested as model outputs (graph
  // intermediates) are released when this execute returns, on every exit path.
  // The ModelV2 executor may schedule kernels on multiple internal streams; a
  // host-side release before those streams complete lets the Torch caching
  // allocator reuse the memory under a pending cross-stream reader (device MTE,
  // nondeterministic). Synchronize the caller's stream before draining: the
  // executor records its sub-stream joins onto this stream, so waiting here
  // covers them all.
  const auto drain_sync_ret = (stream != nullptr) ? aclrtSynchronizeStream(reinterpret_cast<aclrtStream>(stream))
                                                  : ACL_SUCCESS;
  if (drain_sync_ret != ACL_SUCCESS) {
    RT_GLOG(WARNING) << "ExecuteAlloc: pre-drain stream sync failed, ret=" << drain_sync_ret;
  }
  struct AdoptedDrainGuard {
    ~AdoptedDrainGuard() { fx_converter::AbiDrainAdoptedOutputs(); }
  } adopted_drain_guard;
```

构建与部署：`bash build.sh -m -j 64 -p .../python` 后 pip force-reinstall fx_converter wheel（build 19，事件 2711/2712 显示 Successfully built=1）。

## 机制与判别

- 结论：AdoptedDrainGuard 在 ExecuteAlloc 返回时清空 adopted ledger，未收割为模型输出的 fallback 中间态随即归还 torch 缓存分配器；ModelV2 执行器为多流并行调度（StructuredTopological），跨流读者可能尚未执行，读复用后的内存产生非确定性设备 MTE/宿主 SIGBUS。（诊断见事件 2683：`AdoptedDrainGuard` 在 `ExecuteAlloc` 返回时释放所有 fallback 中间态（torch 缓存分配器复用），但 ModelV2 执行器是**多流并行调度**（StructuredTopological），跨流读取者可能尚未执行 → 读复用后的内存 → 非确定性 MTE/SIGBUS。）
- 结论：在 AdoptedDrainGuard 析构（drain）之前对调用方流执行 aclrtSynchronizeStream，可保证执行器子流合流后再释放 fallback 中间态；本轨迹内该修复与其余缺陷修复（FreeMemory 去重/关闭图内 frees、bridge 异常提取）共同落地后，rerun9 全部 271 个 AF kernel launch 成功，进程以 Python 异常（SUSPECT REMOTE ERROR 507057）而非 SIGBUS 收敛。
- 可区分的解释分支：同样的 MTE 症状还存在一个**确定性**成分——pc 恒为 0x124400333e28 的 aicore 错误在所有配置（含关闭全部 frees）下复现（事件 3212 观测 pc start 恒定），轨迹内判定其自最早原版配置即存在、与提前释放无关。因此"非确定性、随调度变化的 MTE/SIGBUS"指向本竞态，"恒定 pc、全核复现的 MTE"指向独立的设备侧 kernel 缺陷。
- 未验证推断：多流读者未完成导致复用读破坏的机制来自源码阅读与症状归纳（事件 2683），轨迹内没有逐 kernel 的直接证据（如对该 buffer 的并发读写 trace）；"执行器把子流合流记录在调用方流上"亦来自源码注释性论断，未单独实验验证。

## 验证信号

- 事件 2712：修复后 fx_converter build 19 "Successfully built"=1，wheel 已安装（单次构建）。
- 事件 3209（rerun9）：进程以 `npuSynchronizeDevice ... SUSPECT REMOTE ERROR, error code is 507057` 的 Python 异常结束，不再出现 Bus error/core dumped（对比修复前事件 2088 的 `Bus error (core dumped)`、事件 2774 的 EXIT=135 Bus error）。
- 事件 3212（rerun9）：`grep -ac "AFLaunchDiag"` = 271，即 271 个 AF kernel 全部 launch；aicore error 的 `pc start: 0x124400333e28` 恒定复现（该确定性 MTE 为独立遗留问题）。
- 证据等级：均为本机（910B3, CANN 9.2.0, 私有 fxrt/GE 构建日志中的客观 grep 观测，单次运行 rerun9）；**混杂变量**——rerun9 之前同批落地的还有 #10（WirePendingFrees 去重 + 关闭图内中间态 frees）与 #12（bridge 异常提取）修复，无法把最终收敛单独归因到本修复。

## 适用与失效边界

- 适用：GE ModelV2 执行器多流调度 + fx_converter torch fallback adopted storage 生命周期管理的组合；症状为非确定性 MTE/SIGBUS 且与 fallback 中间态释放时序相关。
- 代价：每次 ExecuteAlloc 返回前强制同步调用方流，牺牲该点的异步性（本轨迹未量化性能影响）。
- 不适用/边界：恒定 pc 的确定性 aicore MTE（本轨迹遗留，需 aic_err_detail_dump 工具链定位故障 kernel 名）；`stream == nullptr` 的 legacy 路径（走 ExecuteSync，本身已同步）。
- 回退条件：若后续 executor 改为保证 drain 前自行 join 全部子流，该同步可去除；若同步失败仅告警（RT_GLOG WARNING）不阻断执行，需关注吞掉同步错误的场景。
