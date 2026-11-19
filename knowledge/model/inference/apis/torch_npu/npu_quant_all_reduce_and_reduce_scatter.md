---
type: API
title: npu_quant_all_reduce/npu_quant_reduce_scatter：发布独有量化集合通信的Eager合同
description: 成组记录两入口的host检查矩阵（world_size 2/4/8、H 1024..8192且128对齐、BS整除、FP8/FP4枚举）、输出分配与wrapper标签、Meta分层缺口，及950双卡官方测试的静态证据与疑点。
tags:
- task.lookup
- topic.parallelism
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantAllReduceKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantReduceScatterKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: header
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_quant_all_reduce.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_quant_reduce_scatter.py
  role: example
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h
  role: supporting
created_at: '2026-11-12T07:01:42Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# npu_quant_all_reduce/npu_quant_reduce_scatter：发布独有量化集合通信的Eager合同

## 版本与范围

本卡依据 OpPlugin 发布 pin `dedc316708372c9a8bfde4527abd2a94b74840f5` 的两份包装全文（各144/140行逐字阅读）、Schema 登记（op_plugin_functions.yaml 6314–6318）、发布 Meta 注册（846–903）与两份官方测试全文。两个 schema 均为发布独有：主线 pin `d84e9b1d6a558e5f27973cd4329f62968e46fdda` 的 yaml、Meta 注册与 `op_plugin/ops/opapi/` 目录经全 pin 定向 rg 均零命中，`test_custom_ops/` 亦无同名用例；负向证据即上述定向 rg 零命中，不据缺席推断主线全局能力。Schema 登记 `op_api: [v2.6, newest]`，仅为注册证据，不是 CANN 最小版本或设备支持证明；无官方 API 文档页、无 `derivatives.yaml` 反向接线。图消费（GE converter 的 check_dtype/FP4 拒绝差异）与 Eager/Meta 对比已由[torchair GE 集合通信指南](../../guides/optimization/torchair/torchair_ge_collective_lowering.md)覆盖；本卡是 torch_npu API 层的专门合同卡，补齐检查顺序、错误类别、输出分配与测试证据，并链接相邻的[量化矩阵乘归约散射](npu_quant_mm_reduce_scatter.md)同族入口。全部结论为静态源码阅读，未执行任何上游代码。

## 接口与共同签名

```text
npu_quant_all_reduce(Tensor x, Tensor scales, str hcom, int world_size, *,
    str? reduce_op='sum', int? output_dtype=None, int? x_dtype=None, int? scales_dtype=None) -> Tensor
npu_quant_reduce_scatter(Tensor x, Tensor scales, str hcom, int world_size, *,
    str? reduce_op='sum', int? output_dtype=None, int? x_dtype=None, int? scales_dtype=None) -> Tensor
```

`reduce_op` 为 keyword-only 可选**字符串**（包装内 `value_or("sum")` 缺省 sum，字符串指针直传 ACLNN）；`output_dtype/x_dtype/scales_dtype` 三个覆盖参数才是 keyword-only 可选整数枚举；`hcom` 为通信域名字符串。

## 实际门槛（Eager TORCH_CHECK 矩阵）

| 检查项 | 事实（两入口共同，除非注明） | 错误类别 |
| --- | --- | --- |
| x/scales 定义 | 两者都必须 `defined`，None 直接拒绝 | PARAM |
| x 维度 | 仅 2 维 (BS,H) 或 3 维 (B,S,H)；且逐维非空（2 维查 size(0)/size(1)，3 维查前三维） | PARAM |
| x_dtype 枚举 | 显式提供时必须 ∈ {INT8, HIFLOAT8, FLOAT8_E5M2, FLOAT8_E4M3FN, FLOAT4_E1M2, FLOAT4_E2M1}；**报错文字只列 int8/hifloat8/float8_e4m3fn/float8_e5m2，漏写两种 FP4** | VALUE |
| world_size | 仅 {2, 4, 8}；报错含集合原文 | VALUE |
| BS 轴整除 | 令 BS=B（2维）或 B*S（3维），必须 BS % world_size == 0；**AllReduce 也强制此检查**，不能按数学 AllReduce 无需切分推导任意 BS | PARAM |
| H 轴 | 尾维 ∈ [1024, 8192] 且 %128 == 0；**两个入口都做 128 对齐检查** | PARAM |
| scales 维度 | 仅 2/3/4 维且逐维非空；报错文字称 TG QuantMode 需与 x 同 rank、MX QuantMode 多一维，但**代码未逐项实现 x/scales 对应轴或分组尺寸检查** | PARAM |
| scales_dtype 枚举 | 显式提供时必须 FLOAT 或 FLOAT8_E8M0 | VALUE |
| output_dtype | **本地无白名单/不校验**（≠整条路径无校验）：源码注释自述缺少 bfloat16 的类型定义、为不影响正常功能而不做本地检查；传入值仍进入 `GetAclDataType(int)`→`convert_to_scalar_type`→分配链，非法值可能在后续 dtype 解析/转换/分配处被拒（本层未穷举该行为），不能断言任意整数都能到达 SDK | 无本地检查 |

两份包装的检查顺序不同（AllReduce 先 BS 整除再 H，ReduceScatter 反之），失败集合相同，仅首个报错信息因输入而异。所有检查为 host 侧 fail-closed `TORCH_CHECK`，带 `OPS_ERROR` 类别码。

## 动作与分配

| 事项 | npu_quant_all_reduce | npu_quant_reduce_scatter |
| --- | --- | --- |
| 输出 shape 分配 | 与 x 物理 shape 完全一致；2 维仍 2 维、3 维仍 3 维 | 恒为 2 维 `[BS/world_size, H]`；3 维输入把 B*S 合并扁平化，不保留 batch/sequence 分界 |
| dtype 分配 | 缺省 BF16；显式 `output_dtype` 经 `GetAclDataType(int) → convert_to_scalar_type` 接入分配 | 同左 |
| reduce_op | `value_or("sum")` 缺省 sum，字符串原样传 ACLNN | 同左 |
| hcom | 字符串指针直传 `aclnnQuantAllReduce/aclnnQuantReduceScatter`；**world_size 不作为 ACLNN 实参**，仅参与本地检查/输出分配；包装不创建进程组、不核对 hcom 实际成员数 | 同左 |
| wrapper | `make_wrapper(x, x_dtype)`/`make_wrapper(scales, scales_dtype)` 给张量打逻辑 dtype 标签供 aclnn 识别，**不执行数值量化或位打包**；显式提供覆盖时有字宽守卫（op_api_common.h 738–754）：覆盖枚举经 `GetAclDataType` 解析后取 `GetAclDataTypeItemSize`，`TORCH_CHECK` 张量实际 `itemsize` 与之相等（fail-closed PARAM，报错含两侧 dtype/itemsize）才打标签；不提供覆盖时不做量化 dtype 白名单检查，仅把真实 dtype 转为 ACL 类型，真实 dtype 非法时仍可能在转换处失败 | 同左 |

执行入口分别为 `EXEC_NPU_CMD(aclnnQuantAllReduce, x_wrapper, scales_wrapper, group_ptr, reduce_op_ptr, output_tensor)` 与 `aclnnQuantReduceScatter` 同构调用。

## Meta 与 C++ host 实检的分层

发布 Meta 注册（846–903）只做三件事：x/scales 非 None（TYPE）、world_size ∈ {2,4,8}（VALUE）、输出 shape/dtype 推导（output_dtype 经同一枚举映射，缺省 bf16）。它**不检查**维度、非空、H 范围、BS 整除与 dtype 矩阵。两个附加静态缺陷：

- `npu_quant_reduce_scatter_meta` 的 shape 只在 `x.dim()==2/3` 分支里赋值，其他维度触发未绑定局部变量 `size` 的 `UnboundLocalError`（`NameError` 子类），而非干净报错；非整除 BS 被 `//` 静默截断。
- `npu_quant_all_reduce_meta` 完全不查维度（`size = x.size()`）。

因此 Meta 成功或图构图通过不能作为 Eager 可用证明；反向 Eager 拒绝也不由 Meta 复现。

## 官方测试与静态疑点

两份测试均为 `@SupportedDevices(['Ascend950'])` + `skipIfUnsupportMultiNPU(2)`，hccl 双卡，注释标注 T-G 量化：all_reduce 用 x int8 `[8,128,8192]`、scales fp32 `[8,128,64]`；reduce_scatter 用 `[8,32,5120]` 与 `[8,32,40]`——scales 尾维恰为 H/128，是 T-G 128 元素分组的用例级证据。静态疑点（均未执行，不作行为结论）：

- 参考金标 `torch.mul(x.to(int8), scales.to(float32))` 中 x 与 scales 尾维 8192 vs 64/5120 vs 40 **不满足广播**；两份金标构造按形状不可直接执行，用例仅能作形状与调用方式的示意。
- reduce_scatter 金标还按扁平行号切 3 维张量（`out[index*i:index*(i+1), :]`，index=128 远超 dim0=8），切法本身错位。
- 调用传 `output_dtype=0`（ScalarType 枚举 0 即 uint8），金标却转 float32；哪一侧运行时生效未验证。

## 失败与版本边界

- 所有门槛均在 host 侧 fail-closed；不满足时报 `OPS_ERROR(PARAM/VALUE)` 类别，不静默降级、不回退 CPU。
- FP4（E1M2/E2M1）在本层按 x 物理 shape 检查 H 并分配输出，**没有把打包 H 恢复两倍逻辑 H 的处理**；FP4 的完整位打包/尺度协议需另证。
- Eager 与 GE 两层检查集合不同：GE converter 的 `check_dtype` 不接受 FP4 且拒绝 INT8/HiF8 配 E8M0 scales，Eager 无此配对拒绝——详见 torchair 指南卡，不能把任一层局部未拒绝当作 kernel 全矩阵支持。
- 本层无 `aclnnQuantAllReduce/aclnnQuantReduceScatter` 的设备语义（scale 施加点、量化域归约、输出 dtype 保障）来源；`ops/ascendc` 无对应设备卡。
- 版本边界：仅发布 pin 存在此二 schema；主线 pin 同名注册、Meta 与测试均零命中（定向 rg 核实）。发布配套 ascend_26_0_pt28 的组合验证不在本卡范围。无运行验证，无模型归属与整模型收益承诺。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantAllReduceKernelNpuOpApi.cpp)（primary，1–144 全文逐字阅读）

- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantReduceScatterKernelNpuOpApi.cpp)（primary，1–140 全文逐字阅读）

- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（header，6314–6318 两 schema 登记）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation，846–903 两 Meta 函数）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_quant_all_reduce.py)（example，1–111 全文逐字阅读）

- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/test/test_custom_ops/test_npu_quant_reduce_scatter.py)（example，1–112 全文逐字阅读）

- [固定来源 7](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/op_api_common.h)（supporting，738–758 `make_wrapper` helper：显式覆盖的 itemsize 字宽守卫与无覆盖时真实 dtype 转换路径）
