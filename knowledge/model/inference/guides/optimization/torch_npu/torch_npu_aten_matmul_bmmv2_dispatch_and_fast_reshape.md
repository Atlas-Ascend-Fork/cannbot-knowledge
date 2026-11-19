---
type: Guide
title: torch_npu ATen 层 matmul bmmV2 分发与免拷贝 reshape
description: 主线与发布两 pin 的 matmul→npu_bmmV2 fp16 门控分发规则、mv 后免拷贝 fast reshape 三条件与 get_storage_size 物理存储尺寸链；并给出 matmul_backward 的掩码/空输入语义：mask两假与undefined grad返回未定义对、零元素梯度为zeros_like分配、输入无原地改写（测试断言）。
tags:
- task.optimization
- topic.compute.composite
- topic.data_movement.layout_transform
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/MatmulByBmmV2KernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/MatmulByBmmV2KernelNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/NpuFastReshape.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/NpuFastReshape.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/StorageSizeNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/StorageSizeNpu.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/InnerNpuNativeFunction.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/interface/EnvVariables.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/interface/EnvVariables.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionRegister.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionRegister.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npu_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/StorageDescHelper.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/StorageDescHelper.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/FormatHelper.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MatmulKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MatmulKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MvKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MvKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ReshapeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ReshapeKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ReshapeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ReshapeKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/reshape_opt.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/NpuUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MatmulBackwardKernelNpu.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_matmul_backward_empty.py
  role: example
created_at: '2026-11-12T09:23:14Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# torch_npu ATen 层 matmul bmmV2 分发与免拷贝 reshape

## 固定版本与证据

本文依据 PyTorch/TorchNPU 两个固定 pin（主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`、发布 `f3ecfe4a7ef7395754da7ca2e35661a7132b519b`）的 torch_npu C++ 源码静态阅读；调用链闭合需读 op-plugin 侧调用点，本文引用的 op-plugin 快照分别为主线 `d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布 `dedc316708372c9a8bfde4527abd2a94b74840f5`；独立主线来源不表示软件组合已兼容。全部为只读静态口径：未编译、未执行任何算子、未做任何性能测量；`npu_bmmV2` 算子本体（op-plugin `BmmV2KernelNpu.cpp`，355 行）不在本卡来源范围，属 op-plugin 算子本体范围，本文只闭合 torch_npu 导出面到该 custom op 入口的链路。

三个 torch_npu 实现文件（`MatmulByBmmV2KernelNpu.cpp`、`NpuFastReshape.cpp`、`StorageSizeNpu.cpp`）在两 pin 均存在且全文读完：语义逐分支相同，diff 仅为函数大括号换行与缩进格式差异；声明头 `InnerNpuNativeFunction.h` 两 pin 字节相同（sha256 一致）。这是同源小改，不是行为分叉，下文规则对两 pin 同时成立。

## matmul→npu_bmmV2 分发链（fp16 门控）

入口在 op-plugin ACL ops 面（aclops）`MatmulKernelNpu.cpp`：`matmul`/`matmul_out` 先做 int8 拒绝（两 pin 同），再进 `matmul_opt_nocheck`（两 pin 均 :25 定义）。`matmul_by_bmmV2` 本体在 torch_npu `MatmulByBmmV2KernelNpu.cpp`（主线 :8-37，发布 :8-38，`InnerNpuNativeFunction.h:16` 导出）。

| 实际门槛 | 动作 | 失败/版本边界 |
| --- | --- | --- |
| 两侧张量都在 NPU 且均为 `kHalf`（fp16），且 `env::CheckBmmV2Enable()` 为真 | 走 `matmul_by_bmmV2` 按 dim 组合分发（下表） | 任一条件不满足走默认路径（对照见下节）；`out` 变体用 `out.set_(res)` 回写 |
| `CheckBmmV2Enable()` 读取 option `bmmv2_enable`，仅当值为字符串 `"1"` 为真，默认 `"0"` | 注册经 `REGISTER_OPTION_INIT_BY_ENV(bmmv2_enable)`（主线 EnvVariables.cpp:160、发布 :37），env 名是键名大写化 `BMMV2_ENABLE`，**无** `TORCH_NPU_` 前缀 | 有效写法是 `BMMV2_ENABLE=1`；本固定源码内该 option 只经上述注册链按这个无前缀 env 名读取，其他命名写法未做全树核查，不断言是否被读取 |
| Python 面 `torch_npu.npu.set_option({"bmmv2_enable": "1"})` | `npu_config.py:52-77` 校验后整表转发 `torch_npu._C._npu_setOption`（Module.cpp:1641 字典→map→`c10_npu::option::SetOption`） | `_option_map` 之外的键校验直接放行（返回 True），不因未列出而拒绝；`CheckBmmV2Enable` 每次调用实时 `GetOption`（非 static 缓存），运行期改 option 后的调用按新值判断——这是源码结构直读，未做运行验证 |
| 输入含 0 维（dim=0） | 前五档与后两档都不命中 | `AT_ERROR`（"both arguments to matmul need to be at least 1D"） |

`matmul_by_bmmV2` 的 dim 组合规则（两 pin 同一分支序）：

| dim 组合（tensor1×tensor2） | 实际动作 |
| --- | --- |
| 1×1 | `tensor1.dot(tensor2)` |
| 2×1 | 先 `tensor2.unsqueeze(-1)` 把向量升为列向量再 `tensor1.mm(...)`，最后 `squeeze_(-1)`（主线 :13-14、发布 :14-15） |
| 1×2 | `unsqueeze(0)` 后 `mm` 再 `squeeze_(0)` |
| 2×2 | `tensor1.mm(tensor2)` |
| ≥3 ×（1 或 2） | 把 batch 折进第一维：`reshape({-1, size(-1)})` 后 `mm`，再 `_unsafe_view` 回目标形状（主线 :19-31） |
| （1 或 2）× ≥3 | `custom_ops::npu_bmmV2(tensor1, tensor2, {})` |
| 双方 ≥1 维且任一 ≥3（即 ≥3×≥3） | `custom_ops::npu_bmmV2(tensor1, tensor2, {})` |
| 其余（0 维等） | `AT_ERROR` |

注意该函数自身不检查 dtype 与设备：fp16+NPU+option 三重门槛在 aclops 调用方（主线 MatmulKernelNpu.cpp:29-31、发布 :30-35）完成，两 pin 的 gate 结构相同。前五档分支即使在该门控内也只走 `dot`/`mm`（与默认路径同类型算子）；真正换成 `npu_bmmV2` 的只有后两档 batch 组合。

默认路径（门控关闭或 dtype/设备不满足）对照：`≥3×(1|2)` 同样折维走 `mm`；`(1|2)×≥3` 在 aclops 默认路径改为转置内二维后递归 `matmul_opt_nocheck(t2_T, t1_T)` 再转置回（主线 :63-83）；`≥3×≥3` 默认路径走 expand+`bmm`（主线 :84-127）。即开启门控只改变两类 batch 组合的算子选择，不改变低维组合，也不承诺数值或性能差异——静态阅读不含任何收益宣称。

版本与实现面边界：`MatmulKernelNpuOpApi.cpp`、`MvKernelNpuOpApi.cpp`（opapi 面）在本固定提交内 rg `matmul_by_bmmV2|npu_fast_reshape_` 零命中（negative evidence）——本分发链只存在于 ACL ops（aclops）实现面；同一算子走 opapi/aclnn 分发时不经此门控。op-plugin 主线内 rg `matmul_by_bmmV2` 仅命中两个 aclops 文件：前向 `MatmulKernelNpu.cpp`（上文）与反向梯度 `MatmulBackwardKernelNpu.cpp:116-119`——后者以同型 fp16+NPU+`CheckBmmV2Enable` 门控对 `grad` 与另一输入转置相乘计算 `grad_self`/`grad_other`，门控不满足仍回落 `npu_matmul_backward`；反向路径仅覆盖主线 pin，发布 pin 未比对。aclops 与 opapi 的选择由既有分发模式机制决定，不在本卡重述。

## 免拷贝 fast reshape 与物理存储尺寸链

`npu_fast_reshape_`（`NpuFastReshape.cpp`，主线 def :10/三条 restriction 注释行 :17/:21/:25/刷新 :31-33，发布 def :10/注释行 :18/:22/:26/刷新 :33-34；`InnerNpuNativeFunction.h:21` 导出）在两 pin 的固定消费者只有一个：op-plugin aclops `MvKernelNpu.cpp` 的 `mv`/`mv_out`（主线 :27-41、发布 :28-42）。链路：`mv` 用 `OpCommand` 名 `MatMul`（`transpose_x1` 按源是否尾两维转置、`transpose_x2=false`）把 `{N,1}` 结果写进 result（主线 :32-40），随后 `npu_fast_reshape_(result)`（:41）刷新元数据，调用方再做 `squeeze_(1)` 视图收尾（视图操作本身不搬数据）；`npu_fast_reshape_` 自身不搬数据的依据见下表与语义边界。

| 门槛（任一不满足直接 return，无报错） | 动作 |
| --- | --- |
| 张量 `is_contiguous()` | `StorageDescHelper::ReflushDescBySelf`（StorageDescHelper.cpp:227-231）：把 `base_sizes_`/`storage_sizes_`/`base_strides_` 全部改写为当前 sizes/strides |
| `FormatHelper::IsBaseFormatType`（FormatHelper.cpp:122-131；非 NPU storage 的普通 StorageImpl 直接视为基础格式） | `InferFormat::GuessBaseFormat` 猜测基础格式后 `npu_format_cast_` 到该格式 |
| `numel == GetMemorySize(tensor)` 且 `!MetaDataAreMatch(&tensor)`（StorageDescHelper.cpp:12-16 比较 desc 的 base sizes/strides 与当前值；GetMemorySize :291-295 取 `npu_desc_` 的物理存储元素积） | 元数据改写（`ReflushDescBySelf`）本身不分配、不搬数据；其后还调用 `npu_format_cast_`，其不搬数据的依据见语义边界（复用既有卡同 pin 固定源码契约） |

语义边界：三道 guard 通过后，`ReflushDescBySelf` 只改写 NPU 存储描述符元数据、不分配不搬数据；尾部 `npu_format_cast_(tensor, GuessBaseFormat(sizes))` 的真实分支本卡未逐行读——本调用源经 guard 2 限定为 base 格式、目标为 base 格式，按既有卡 [torch_npu out 准备的 resize 与格式分支](torch_npu_out_preparation_resize_and_overlap.md) 在同 pin 固定源码（`FormatCastKernelNpu.cpp` 主线全文 1–469、发布定向 24–80/200–263）已核的契约：目标格式与当前 `npu_format_` 相同即原对象返回；源与目标都是 base 格式时 `format_cast_as_base_format` 只重写 `origin_format_`/`npu_format_` 两个描述字段，不移动数据、不换存储——因此该函数在这个入口组合下不搬数据，此结论为复用既有卡固定源码契约，未做运行验证。`GetMemorySize` 参与的是 NPU 物理存储尺寸（内部格式下可能大于逻辑 numel），逻辑 numel 相等是进入条件而非结论。opapi 的 `MvKernelNpuOpApi.cpp` 无此调用（negative evidence），与 matmul 链同边界。

`get_storage_size`（`StorageSizeNpu.cpp`，主线 :8-15、发布 :8-16）返回 `npu_desc_.storage_sizes_` 各项连乘（物理存储元素数，非逻辑 numel；先 `torch_check_npu`）。两个固定消费者（均在 op-plugin，两 pin 结构相同）：`OpUtils.cpp` 的 `is_transpose_last_two_dims`（仅 2/3 维，比对 stride/size 与 base desc，主线 d84e9b1d :88-107），以及 `npu_reshape_out` 的 d2d 拷贝字节来源（aclops `ReshapeKernelNpu.cpp` 与 opapi `ReshapeKernelNpuOpApi.cpp` 的 `can_refresh=false` 分支：`copy_d2d_by_memcpy(out, self, get_storage_size(out))`）。`can_refresh=true` 分支只调 `StorageDescHelper::SetDesc`。torch_npu 侧 `reshape_opt.cpp:14` / `reshapeV2_opt.cpp:18` 以 `can_refresh=false` 调用，`NpuUtils.cpp:130`（`metadata_convert_match`）以 `true` 调用；该连续化优化框架整体见既有 contiguous 卡，本卡不重复展开。

## 版本边界汇总

- 两 pin 三个实现文件与 `bmmv2_enable` option 注册（`REGISTER_OPTION_INIT_BY_ENV` + `REGISTER_OPTION_BOOL_FUNCTION`）均存在：主线 EnvVariables.cpp:160-161、发布 :37-38；语义相同，格式不同。
- option 注册表机制（OptionRegister.cpp:60-92）：`env` 类型注册把键名大写化后 `getenv` 读初值；`GetOption`（:103-105）对未注册键返回 `nullopt`。本 key 无 callback，无惰性重放。
- `custom_ops::npu_bmmV2`/`npu_reshape_out` 的声明头 `torch_npu/csrc/aten/CustomFunctions.h` 为构建期生成（torchnpugen 模板 + op-plugin `op_plugin_functions.yaml` 的 custom op 声明，两 pin yaml 均含 `npu_bmmV2(Tensor self, Tensor mat2, int[] output_sizes)` schema）；固定源码树内无该头文件实体。
- `torch_npu.npu.set_option` 的 `_check_compile_option` 对未列入 `_option_map` 的键一律放行（npu_config.py:36-50 `return True`），因此 `bmmv2_enable` 可经该入口写入；这是源码直读，未运行验证。
- 静态口径：本文所有"生效/不生效"均为固定提交源码的分支结构结论；不在来源范围的实现包括 op-plugin `BmmV2KernelNpu.cpp` 算子本体、`npu_format_cast_` 真实 cast 分支细节（不搬数据结论复用既有卡同 pin 契约，见免拷贝 fast reshape 节）、`InferFormat::GuessBaseFormat` 内部实现。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/MatmulByBmmV2KernelNpu.cpp)（primary）：全文 1–41。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/MatmulByBmmV2KernelNpu.cpp)（primary）：全文 1–42。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/NpuFastReshape.cpp)（primary）：全文 1–37。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/NpuFastReshape.cpp)（primary）：全文 1–39。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/StorageSizeNpu.cpp)（primary）：全文 1–19。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/aten/common/StorageSizeNpu.cpp)（primary）：全文 1–20。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/common/InnerNpuNativeFunction.h)（implementation）：全文 1–26（两 pin 字节相同；wc -l 25，末行无换行）。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/interface/EnvVariables.cpp)（implementation）：160–161。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/interface/EnvVariables.cpp)（implementation）：37–38。
- [固定来源 10](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionRegister.h)（implementation）：107、109–121、123–130。
- [固定来源 11](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/core/npu/register/OptionRegister.cpp)（implementation）：60–92、103–105。
- [固定来源 12](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/npu/Module.cpp)（implementation）：1641–1671、2344。
- [固定来源 13](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/npu_config.py)（implementation）：5–9、14–50、52–77。
- [固定来源 14](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/StorageDescHelper.cpp)（implementation）：12–16、227–231、291–295。
- [固定来源 15](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/StorageDescHelper.h)（implementation）：18、29、64。
- [固定来源 16](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/FormatHelper.cpp)（implementation）：122–131。
- [固定来源 17](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MatmulKernelNpu.cpp)（implementation）：26–131（gate、默认路径与尾 TORCH_CHECK）、139–171（int8 拒绝与注册包装）。
- [固定来源 18](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MatmulKernelNpu.cpp)（implementation）：25–40（gate 段逐行读：def :25、gate :30-35；release 版共 169 行，其余段未逐行读）。
- [固定来源 19](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MvKernelNpu.cpp)（implementation）：全文 1–77。
- [固定来源 20](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/MvKernelNpu.cpp)（implementation）：与主线 raw diff 全文等价（仅格式差异）+ 关键行 :42 复核。
- [固定来源 21](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/ReshapeKernelNpu.cpp)（implementation）：全文 1–41。
- [固定来源 22](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/aclops/ReshapeKernelNpu.cpp)（implementation）：全文 1–52（仅格式展开差异）。
- [固定来源 23](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ReshapeKernelNpuOpApi.cpp)（implementation）：全文 1–41。
- [固定来源 24](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ReshapeKernelNpuOpApi.cpp)（implementation）：与主线 raw diff 全文核对等价（仅换行/缩进格式差异，完整 diff 级核对）；aclops 版 release 亦全文核对（52 行）。
- [固定来源 25](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）：88–107。
- [固定来源 26](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/contiguous/reshape_opt.cpp)（implementation）：全文 1–28（wc -l 27，末行无换行）。
- [固定来源 27](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/NpuUtils.cpp)（implementation）：118–140（含 metadata_convert_match :123-138）。
- [固定来源 28](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MatmulBackwardKernelNpu.cpp)（implementation）：110–125（零元素早退 :110-114、fp16+NPU+`CheckBmmV2Enable` 门控 :116-117、`matmul_by_bmmV2` 反向两调用 :118-119、`npu_matmul_backward` 回落尾部 :123-125；其余行不在来源范围，发布 pin 未比对）。

相关既有卡（去重边界，未重写）：

- [torch_npu contiguous 描述符缓存与 clone 门](torch_npu_contiguous_descriptor_cache_and_clone_gate.md)：reshape_opt 所在连续化优化框架与拷贝分支。
- [torch_npu out 准备的 resize 与格式分支](torch_npu_out_preparation_resize_and_overlap.md)：`npu_format_cast_` 真实分支（同格式原对象返回；base→base 只重写描述字段不搬数据）与 resize 换存储语义——本卡免拷贝 fast reshape 结论复用其同 pin 固定源码契约。
- [torch_npu dtype cast 后端分配与别名](torch_npu_dtype_cast_backend_allocation_and_aliases.md)：dtype cast 的后端分配与别名行为及 `empty_with_format` 的 `GetMemorySize` 字节账，与本文的 format cast 是不同入口。
- [inductor Triton matmul kernel 家族](torch_npu_inductor_triton_matmul_kernel_family.md)：编译层的矩阵乘生成，与本文 ATen 层互不推导（该卡边界原文明确）。
- [torch_npu 布局选项](../../../apis/torch_npu/layout_options.md)：`MM_BMM_ND_ENABLE` 等 mm/bmm 布局开关是另一机制，与 `bmmv2_enable` 无注册关系。

## matmul_backward 的掩码与空输入语义（测试增补）

上文反向梯度小节闭了fp16+NPU+`CheckBmmV2Enable`门控与零元素早退的行锚；本节按主线`MatmulBackwardKernelNpu.cpp`实读与主线合同测试补齐**掩码/空梯度语义**。测试`test/test_base_ops/test_matmul_backward_empty.py`（70行，`torch.testing`框架`instantiate_device_type_tests`，仅主线pin）逐条断言：

| 场景 | 包装行为（主线MatmulBackwardKernelNpu.cpp 95–114） | 测试断言 |
| --- | --- | --- |
| mask[0]与mask[1]同假 | 返回两个未定义Tensor（无计算） | 输出为(undefined, undefined) |
| grad未定义（None） | 无计算直接返回 | 输出(None, None) |
| grad/self/other任一numel==0 | 按mask返回`zeros_like(self)`/`zeros_like(other)`（:110-114） | **零元素梯度得到的是分配零而非空张量**，且与CPU参照等值 |
| 输入变异 | 全程无原地改写 | 输入`_version`前后不变 |
| 执行模式 | 参数化jit_compile False/True × allow_internal_format=False | 两模式行为一致（模式无关断言） |

测试另有前置拒绝条件：`TORCH_NPU_USE_COMPATIBLE_IMPL=1`或`FORCE_ACLNN_OP_LIST`含`matmul_backward`时`assertNotEqual/NotIn`直接失败——这是**测试前提注记**（兼容实现旁路存在），不进入本卡行为结论。空输入zeros_like语义与上文"零元素早退"互补：早退不是跳过输出分配，而是生成与输入同形的零张量；训练图含空梯度路径时仍会产生分配。发布pin的matmul_backward未比对（与上文边界一致）；测试未执行，数值等价未验证。

### matmul_backward 空输入证据

- [test_matmul_backward_empty.py d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_matmul_backward_empty.py)（example）：全文70行；13组空shape参数化×mask四组合×jit两态。
- [MatmulBackwardKernelNpu.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/aclops/MatmulBackwardKernelNpu.cpp)（implementation）：95–135；dim>0 TORCH_CHECK、mask两假返回、零元素zeros_like早退、bmmV2门控与npu_matmul_backward回落（已列于上文固定来源28的行段为110–125，本节补95–109）。
