---
{
  "type": "Runbook",
  "title": "fx_converter fallback 生命周期排查：ExecuteAlloc 入口同步未建立 scope-exit drain 的完成顺序",
  "description": "T5/GE ModelV2 多流执行中出现MTE与SIGBUS，轨迹怀疑fallback adopted storage提前释放。尝试在NoteFallbackExecuteBoundary之后、AdoptedDrainGuard定义之前插入aclrtSynchronizeStream；原始函数上下文表明这位于ExecuteAlloc入口、本次图执行之前，不能等待本次尚未提交的kernel。因此该补丁是未闭合路线，不能作为有效drain前同步修法。联合修改后的单次rerun9记录271次launch且无宿主SIGBUS，但仍以507057退出，无法隔离本补丁贡献。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "910"
  ]
}
---
# fx_converter fallback 生命周期排查：ExecuteAlloc 入口同步未建立 scope-exit drain 的完成顺序

## 适用场景

- 框架/栈：torch-npu（fxrt bridge，torch_npu 2.13.0+git6a32e81 自建 wheel）+ fx_converter（fxrt 仓 `fx_converter/src/api/fx_converter_api.cc`）+ GE ModelV2 执行器（ge-om2-dynamic-experiments 13b06c5768c9 本地构建）；CANN 9.2.0（`${CANN_INSTALL_ROOT}`）。
- 平台：Atlas 910B3（8 卡，`ASCEND_RT_VISIBLE_DEVICES=2`），aarch64，npu-smi 26.1.0.b050。
- 工作负载：动态 T5（t5-v1.1-xxl）经 torchair/_inductor_npu_ext + AutoFuse 的 rt2 模式（T5_RUN_MODE=rt2，runner=ModelV2Runner），AUTOFUSE_FLAGS="--enable_autofuse=true;--autofuse_enable_pass=matmul,reduce,concat;"。
- 缺失信息：该尝试来自私有 fxrt/fx_converter 工作区（${LOCAL_PATH_1}）；未验证有效完成顺序，亦未在其它 CANN/GE 版本上复验。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

路径补充：`${CANN_INSTALL_ROOT}` 为当前环境实际使用的 CANN 安装根目录，按本地安装设置。

## 触发与观测

图执行阶段出现**非确定性**宿主 SIGBUS（Bus error, core dumped，run 间结果不同）与设备侧 MTE（`RuntimeError: npuSynchronizeDevice:torch_npu/csrc/core/npu/NPUStream.cpp:737 NPU function error: SUSPECT REMOTE ERROR, error code is 507057`，事件 2088/2123；plog 中 `EZ9999 ... the error is aicore error ... error code = 0x800000 ... MTE accesses an invalid GM address`）。SplitDiag 统计显示单次执行物化 565 个 fallback 中间态（288 个 67108864 字节 + 144 个 167772160 字节，约 42GB，事件 2728）——这些 buffer 未被收割为模型输出，其生命周期完全由 adopted ledger 管理。

## 探针与操作

尝试前 `ConverterSession::ExecuteAlloc`（fx_converter_api.cc，事件 2681 读取的原文）：

```
  NoteFallbackExecuteBoundary();
  // Adopted fallback storages not harvested as model outputs (graph
  // intermediates) are released when this execute returns, on every exit path.
  struct AdoptedDrainGuard {
    ~AdoptedDrainGuard() { fx_converter::AbiDrainAdoptedOutputs(); }
  } adopted_drain_guard;
```

配套机制：`AbiNoteAdoptedOutput` 把 (addr, owner) 记入 thread_local 的 `g_adopted_ledger`；`AbiDrainAdoptedOutputs()` 直接 `g_adopted_ledger.clear()`，释放 owner 引用、最后引用析构时销毁 bridge 结果（torch 缓存分配器回收内存）（事件 2675）。

未闭合的同步尝试（事件2705补丁，2706仅确认写入）：以下保留原始代码与注释，注释中的完成保证并未成立。原始2681函数上下文显示：此处在 `ExecuteAlloc` 入口，后面才构建输入并执行图。

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

- 候选机制：AdoptedDrainGuard 在 ExecuteAlloc 返回时清空 adopted ledger，未收割为模型输出的 fallback 中间态会释放owner引用，最后引用销毁时才可能归还缓存分配器；ModelV2 执行器为多流并行调度（StructuredTopological），跨流读者可能尚未执行，读复用后的内存产生非确定性设备 MTE/宿主 SIGBUS。（诊断见事件 2683：`AdoptedDrainGuard` 在 `ExecuteAlloc` 返回时释放所有 fallback 中间态（torch 缓存分配器复用），但 ModelV2 执行器是**多流并行调度**（StructuredTopological），跨流读取者可能尚未执行 → 读复用后的内存 → 非确定性 MTE/SIGBUS。）
- 明确失效点：上面同步发生在guard定义之前、图提交之前；guard析构仍然只调用drain。入口同步最多等待此前已提交的工作，不能建立本次子流读者完成后再释放的顺序。即使执行器会把子流join记录到调用流，也必须核实join与等待发生在本次提交之后；该补丁未提供这条保证。
- 单次联合观测：rerun9中有271次AF launch记录，无宿主SIGBUS，但仍返回Python错误507057。固定pc或非确定性症状可指导排查，不能独自证明是两个互不相关的缺陷，也不能证明生命周期风险已修复。
- 未验证推断：多流读者未完成导致复用读破坏的机制来自源码阅读与症状归纳（事件 2683），轨迹内没有逐 kernel 的直接证据（如对该 buffer 的并发读写 trace）；"执行器把子流合流记录在调用方流上"亦来自源码注释性论断，未单独实验验证。

## 验证信号

- 事件 2712：尝试后 fx_converter build 19 "Successfully built"=1，wheel 已安装（单次构建）。
- 事件 3209（rerun9）：进程以 `npuSynchronizeDevice ... SUSPECT REMOTE ERROR, error code is 507057` 的 Python 异常结束，不再出现 Bus error/core dumped（对比修复前事件 2088 的 `Bus error (core dumped)`、事件 2774 的 EXIT=135 Bus error）。
- 事件 3212（rerun9）：`grep -ac "AFLaunchDiag"` = 271，即 271 个 AF kernel 全部 launch；aicore error 的 `pc start: 0x124400333e28` 恒定复现（设备故障仍存在，独立性未证实）。
- 证据等级：均为本机（910B3, CANN 9.2.0, 私有 fxrt/GE 构建日志中的客观 grep 观测，单次运行 rerun9）；**混杂变量**——rerun9 之前同批落地的还有 #10（WirePendingFrees 去重 + 关闭图内中间态 frees）与 #12（bridge 异常提取）修复，无法把宿主故障形态的变化单独归因到本尝试。

## 适用与失效边界

- 适用：GE ModelV2 执行器多流调度 + fx_converter torch fallback adopted storage 生命周期管理的组合；症状为非确定性 MTE/SIGBUS 且与 fallback 中间态释放时序相关。
- 代价：该尝试在ExecuteAlloc入口等待调用流，可能影响此前工作的异步性；它并非每次返回前的同步，性能影响未量化。
- 证据边界：没有逐buffer读写trace、实际子流join时序或修正后的设备验收；`stream == nullptr` 路径也需按实际执行器行为分别核对。现有入口补丁不能作为已验证的生命周期修复采用。
- 后续验证方向（未实施）：先确定最后一个读者、join记录与drain的真实时序，以及异常/提前返回路径的所有权。再设计完成依赖与错误传播，并分别回归设备正确性、内存回收和性能；本页不提供或宣称已验证的替代补丁。
