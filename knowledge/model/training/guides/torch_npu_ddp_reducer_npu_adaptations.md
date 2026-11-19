---
type: Guide
title: DDP Reducer 的 NPU 适配：物理元素数、梯度格式对齐与桶视图拷贝
description: 固定 reducer 在 NPU 上的差异点：NZ 语义的 physical_numel、grad 与参数格式不一致时的 npu_format_cast、copy_memory_ 桶拷贝与单设备事件计时，区分它与非 NPU 语义。
tags:
- task.implementation
- topic.parallelism
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/reducer.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/reducer_npu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/default_comm_hooks.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/default_comm_hooks.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/default_comm_hooks.hpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/reducer.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/distributed/reducer_npu.cpp
  role: implementation
created_at: '2026-11-13T04:24:55Z'
updated_at: '2026-11-14T01:56:26Z'
platforms: []
---

# DDP Reducer 的 NPU 适配：物理元素数、梯度格式对齐与桶视图拷贝

## 固定版本与范围

静态审阅 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的 `reducer.cpp`（2024 行）NPU 差异点、`reducer_npu.cpp`（NPU Timer）与 `default_comm_hooks.cpp`。发布版本 未逐行比对；与上游 PyTorch c10d reducer 的逐函数 diff 未做（上游不在本卡固定版本内），本卡只固定读到的 NPU 侧行为。未运行分布式训练或性能实验，保持 `draft`、空平台。通信钩子的文档面见[DDP 通信钩子](torch_npu_ddp_communication_hooks.md)，HCCL 侧承重分支见[ProcessGroupHCCL 剩余分支](torch_npu_hccl_collective_entry_residual_branches.md)。

## 桶拷贝前的格式对齐

`mark_variable_ready` 拷贝梯度进桶视图前（reducer.cpp:335-367）：若 `grad` 与 `variable` 的 `npu_desc_.npu_format_` 不一致，先 `npu_format_cast(grad, variable 的格式)` 再拷贝——桶视图格式跟随参数存储格式，格式不匹配的梯度不会静默按 ND 解释。拷贝统一走 `NPUNativeFunctions::copy_memory_`：无 comm_hook 且梯度不 requires_grad 时用 `grad.mul(1./div_factor_)` 边除边拷（源码注释：省一次全参数扫描）；带 comm_hook 时只拷不除（除法由钩子负责）；`create_graph=True` 时仅告警不同步高阶梯度，仍拷贝。`gradient_as_bucket_view_` 生效且 grad 已是桶视图别名时零拷贝直通。

## 梯度回写与未定义梯度的重建

`finalize_backward` 侧（:1240-1256）：参数未用时保持 grad 不动；grad 未定义时按参数的 sizes/options **和 npu_format_** 用 `OpPreparation::ApplyTensorWithFormat` 重建，再 `copy_memory_` 从桶视图拷回；已定义则直接拷回。因此 bucket 重建出的梯度会继承参数的物理格式，而不是默认 ND。

## physical_numel 与 NZ 语义

匿名空间的 `physical_numel`（:43-51）按 `npu_desc_.storage_sizes_` 连乘而非 sizes：NZ 等带 padding 格式的物理元素数大于逻辑元素数，桶容量与 `check_grad_layout` 相关判断以物理数为准。把 DDP 桶容量配置（bucket_bytes_cap）换算成元素数时应意识到这一口径差；本卡未逐行核对所有调用点，使用前按 `physical_numel` 的引用处复核。

## 事件计时只在单设备模块启用

构造函数（:115-126）：NPU 设备上仅当模块参数不是多设备时才 `TimerRegistry()->Create` 计时器；多设备模块不建 NPU Timer。`reducer_npu.cpp` 的 `NpuTimer::record` 在设备 guard 下记录 NPUEvent；`measureDifference`（:25-50）只在 `debug_level()==Detail` 时计算，事件未创建/未记录时返回 nullopt（no-sync 或未 backward 的迭代会缺事件），计算前对两事件 synchronize。DDP 日志里的 backward_compute_end/backward_comm_start 等时间戳来自这条链，多设备模块或非 Detail 级别下缺时间戳是预期行为，不是采集故障。

## 桶重建与默认通信钩子

`rebuild_buckets` 使用 `c10d_npu::compute_bucket_assignment_by_size`（:1601）重排桶索引（NPU 命名空间包装，签名与上游同构，本卡未比对实现差异）。`default_comm_hooks.cpp`（:13-49）实现 AllReduceCommHook（先除 world_size 再 allreduce，源码注释：FP16 下先除避免溢出）与 FP16CompressCommHook（压 FP16 allreduce 后回拷 FP32）；钩子体与上游 c10d 语义一致，NPU 侧仅错误码包装，未见额外 NPU 分支。钩子接口的文档约束仍以通信钩子卡为准。

## 优化判断

排查 DDP 慢/梯度格式问题时：先确认梯度与参数格式是否一致（不一致会在每次 mark_variable_ready 触发一次 format_cast）；`gradient_as_bucket_view=True` 可消除拷贝但改变梯度存储别名契约；桶重建后梯度格式继承参数格式。本卡不含任何带宽/时延数字，未审阅 reducer 全部 2024 行的逐行语义（sparse 梯度、find_unused 参数扫描等沿用上游逻辑的部分未逐行核对该仓是否改动）。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/reducer.cpp)（primary）：43-51（physical_numel）、115-126（单设备 Timer 门）、335-367（格式对齐与 copy_memory_）、1240-1256（梯度回写重建）、1601（compute_bucket_assignment_by_size 调用行）。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/reducer_npu.cpp)（primary）：全文 1-96（NpuTimer record/measureDifference）。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/distributed/default_comm_hooks.cpp)（implementation）：13-49（AllReduce/FP16Compress/_AllReduceBySum 钩子体；文件实际 51 行，原记 16-60 超出行数）。

## 发布版本 对照（f3ecfe4a）

卡内涉及的 5 个发布孪生文件已做真实机械比对（sha256 → 去空白 → token → 注释剥离 token → 语义 diff 五级），结论分述如下。

### 已绑定（等价/无行为差异）

- `torch_npu/csrc/distributed/default_comm_hooks.cpp`：全空白折叠后逐字节等价（重排版）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/distributed/default_comm_hooks.hpp`：全空白折叠后逐字节等价（重排版）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/distributed/reducer.cpp`：注释差异等价（代码 token 流相同；2024 行 vs 2162 行为换行排版差异）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。
- `torch_npu/csrc/distributed/reducer_npu.cpp`：全空白折叠后逐字节等价（重排版）。发布来源条目已入 frontmatter（release pin f3ecfe4a）。

### 版本边界（发布版本 行为不同，按 pin 分述）

- **`torch_npu/csrc/distributed/reducer.hpp`**：Reducer 句柄类型为两版差异。
  - 主线 `grad_accumulators_` 为 `std::vector<c10::intrusive_ptr<torch::autograd::Node>>`、`hooks_` 为 `std::vector<std::pair<uintptr_t, c10::intrusive_ptr<torch::autograd::Node>>>`（:243、:247）。
  - 发布版两处均为 `std::shared_ptr`（:252、:256）；文件其余 intrusive_ptr 用法两版一致。
  - 对本卡结论的影响：本卡所述格式对齐/Timer/桶视图结论不受直接影响，但 DDP Reducer 的 autograd 节点句柄持有类型两版不同，跨版本内存/生命周期结论需按 pin 分别核对。

（本节静态比对，未运行/未编译；结论按文件分列，未列出的文件未比对。）
