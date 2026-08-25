---
type: "Runbook"
title: "AICPU launcher 缺 OP_ATTR_NAMES 编译错"
description: "无属性 regbase 算子的 ADD_TO_LAUNCHER_LIST_AICPU 调用若照搬 AICORE 写法省略 OP_ATTR_NAMES()，AICPU 宏会把第二个形参位（op::FVector<std::string>&，属性名向量）错绑到 OP_INPUT(...)，触发引用类型不匹配编译错。判别=build.sh --pkg 编译期报 invalid initialization of reference of type 'op::FVector<std::basic_string<char> >&' from expression of type 'op::OpInput<...>'，定位行紧随算子名后缺 OP_ATTR_NAMES()。AICORE 变体无该形参位，省略合法，二者宏签名不可互换。"
tags: ["task.debugging", "topic.compilation", "topic.implementation.api_layer.aicpu_api"]
status: stable
sources: []
created_at: "2026-08-18T08:27:33Z"
updated_at: "2026-08-24T00:00:00Z"
platforms: ["950"]
---

# AICPU launcher 缺 OP_ATTR_NAMES 编译错

## 现象

在为 SoftplusGrad（无属性 broadcast regbase 算子）补完 `op_api/softplus_grad.cpp` 后执行 `bash build.sh --pkg --ops=softplus_grad --soc=ascend950 --vendor_name=softplus_grad_nn -j8`，编译阶段在 `op_api/softplus_grad.cpp:44` 报错：

```
error: invalid initialization of reference of type 'op::FVector<std::basic_string<char> >&' from expression of type 'op::OpInput<const aclTensor*, const aclTensor*>'
```

即宏期望第二个参数是 `op::FVector<std::string>&`（属性名向量），而实际传入的是 `OP_INPUT(gradOutput, self)`（`OpInput<...>`）。当时代码状态：

```cpp
auto ret = ADD_TO_LAUNCHER_LIST_AICPU(SoftplusGrad, OP_INPUT(gradOutput, self), OP_OUTPUT(out));
```

## 适用场景

- **工程形态**：算子仓 op_api 层 AICPU launcher 注册（regbase 算子，ops-registry-invoke 流程）。
- **API 路径**：`ADD_TO_LAUNCHER_LIST_AICPU(<OpName>, OP_ATTR_NAMES(...), OP_INPUT(...), OP_OUTPUT(...), OP_ATTR(...))`；对照 `ADD_TO_LAUNCHER_LIST_AICORE` 形参表无属性名向量位。
- **验证过的平台与 CANN 版本**：Ascend 950（dav-3510 / arch35），CANN 9.1.0。
- **适用粒度**：`operator_family`（所有无属性 regbase 算子的 AICPU launcher 均适用）。
- **路线优先级**：`diagnostic_only`——本卡只给判别方法与根因解释；补 `OP_ATTR_NAMES()` 的逐字 after 代码与修后 clean 闭环未从 trace 恢复。
- **不适用或未验证场景**：AICORE 变体不需要 `OP_ATTR_NAMES`（同仓 sigmoid AICORE 不带该宏可编译，已对比）；非 regbase（旧式 L0 API）算子的 launcher 写法不同，未验证；a2/a3 未在本 trace 上板验证。

## 根因

`ADD_TO_LAUNCHER_LIST_AICPU` 宏的形参表第二个位置固定是属性名向量 `op::FVector<std::string>&`，由 `OP_ATTR_NAMES(...)` 宏产生；而 `ADD_TO_LAUNCHER_LIST_AICORE` 宏的形参表无该位置。两个变体的宏签名不同：AICPU 强制要求 `OP_ATTR_NAMES()`（无属性时传空 `OP_ATTR_NAMES()`），AICORE 不要求。无属性算子若照搬 AICORE 写法省略 `OP_ATTR_NAMES()`，AICPU 宏会把后续 `OP_INPUT(...)` 绑定到 `FVector<std::string>&` 形参，触发引用类型不匹配的编译错。

机制链（不跳步）：无属性 regbase 算子 → op_api 照搬 AICORE 写法省略 `OP_ATTR_NAMES()` → AICPU 宏第二形参位 `FVector<std::string>&` 错绑 `OP_INPUT(...)`（`OpInput<...>`）→ 引用类型不匹配 → 编译期 `invalid initialization of reference` 报错。

## 判别方法

**触发条件**（tool_observed 失败症状）：无属性 regbase 算子 op_api 补完后 `bash build.sh --pkg --ops=<op> --soc=ascend950` 在编译阶段报：

```
error: invalid initialization of reference of type 'op::FVector<std::basic_string<char> >&' from expression of type 'op::OpInput<...>'
```

报错点落在 `op_api/<op>.cpp` 的 `ADD_TO_LAUNCHER_LIST_AICPU` 调用行，且算子名后紧跟的不是 `OP_ATTR_NAMES(...)` 而是 `OP_INPUT(...)`。

**可执行探针**：
1. 对 `--pkg` 构建输出 grep 编译错误关键字：`bash build.sh --pkg --ops=<op> --soc=ascend950 ... 2>&1 | grep -E "Error|error|FAIL" | head -20`。
2. 命中 `invalid initialization of reference of type 'op::FVector<std::basic_string<char> >&'` 即锁定本坑；定位报错行，确认其紧邻 `ADD_TO_LAUNCHER_LIST_AICPU` 调用。
3. 读该行 `ADD_TO_LAUNCHER_LIST_AICPU` 的实参序列：若算子名后第二个 token 是 `OP_INPUT(...)` 而非 `OP_ATTR_NAMES(...)`，即确认缺失属性名向量位。
4. 对照同仓无属性算子（如 sigmoid）的 AICPU/AICORE 两种写法：AICPU 带 `OP_ATTR_NAMES()`、AICORE 不带——确认两变体宏签名不可互换。

**原始观测**（Ascend950，CANN 9.1.0，SoftplusGrad op_api 重建）：
- `bash build.sh --pkg --ops=softplus_grad --soc=ascend950` 编译阶段在 `op_api/softplus_grad.cpp:44` 报 `invalid initialization of reference of type 'op::FVector<std::basic_string<char> >&' from expression of type 'op::OpInput<const aclTensor*, const aclTensor*>'`（来源平台：950；证据等级：tool_observed）
- 对照同仓 sigmoid：`ADD_TO_LAUNCHER_LIST_AICPU(Sigmoid, OP_ATTR_NAMES(), OP_INPUT(self), OP_OUTPUT(sigmoidOut))` 带 `OP_ATTR_NAMES()`，`ADD_TO_LAUNCHER_LIST_AICORE(Sigmoid, OP_INPUT(self), OP_OUTPUT(sigmoidOut))` 不带——两变体签名不同（来源平台：950；证据等级：tool_observed）

**机制解释**（根因分析，属 interpretation）：`ADD_TO_LAUNCHER_LIST_AICPU` 宏形参表第二位固定为 `op::FVector<std::string>&`（属性名向量，由 `OP_ATTR_NAMES(...)` 产生），`ADD_TO_LAUNCHER_LIST_AICORE` 形参表无该位。无属性算子若照搬 AICORE 的省略写法，AICPU 宏会把 `OP_INPUT(...)` 绑到 `FVector<std::string>&` 形参，`OpInput<...>` 与引用类型不匹配触发编译错。修复方向是在算子名后紧跟 `OP_ATTR_NAMES()`（无属性时传空），AICORE 调用保持不变。

## 预防

- 无属性 regbase 算子写 AICPU launcher 时，**始终**在算子名后紧跟 `OP_ATTR_NAMES()`；不要照搬 AICORE 的省略写法。
- AICPU 与 AICORE 两个 launcher 宏签名不同，不可互换写法；以同仓无属性算子（sigmoid）为模板。

## 验证信号

- `bash build.sh --pkg --ops=softplus_grad --soc=ascend950` 编译阶段在 `op_api/softplus_grad.cpp:44` 报 `invalid initialization of reference of type 'op::FVector<std::basic_string<char> >&' from expression of type 'op::OpInput<...>'`（来源平台：950；证据等级：tool_observed）
- 同仓 sigmoid 的 AICPU 调用带 `OP_ATTR_NAMES()`、AICORE 调用不带，对照确认两变体宏签名不同（来源平台：950；证据等级：tool_observed）

## 坏实践

- 把 AICORE 的省略 `OP_ATTR_NAMES` 写法直接套到 AICPU 变体上，导致 `FVector<std::string>&` 形参错绑 `OP_INPUT`。

## 误诊

无。

## 失效边界

- Ascend 950 / CANN 9.1.0 实测；其他平台与 CANN 版本未验证，推断可迁移（宏签名属 regbase 框架稳定接口）。
- 若 CANN 后续统一 AICPU/AICORE 宏签名，本卡可能失效。

<!-- cannbot:related:start -->
## 相关

- [AICPU（OpDef）](../../apis/utils_api/prototype_register_management/op_def/aicpu.md)（`exemplifies`）：《AICPU launcher 缺 OP_ATTR_NAMES 编译错》的任务是“无属性 regbase 算子的 ADD_TO_LAUNCHER_LIST_AICPU 调用若照搬 AICORE 写法省略 OP_ATTR_NAMES()，AICPU 宏会把第二个形参位（op::FVector<std::string>&，属性名向量）错绑到 OP_INPUT(...)，触发引用类型不匹配编译错。判别=build.sh --pkg 编译期报 invalid initialization of reference of type 'op::FVector<std::basic_string<char> >&' from expression of type 'op::OpInput<...>'，定位行紧随算子名后缺 OP_ATTR_NAMES()。AICORE 变体无该形参位，省略合法，二者宏签名不可互换。”。《AICPU（OpDef）》具体提供“设置AI CPU的配置信息：包括算子输入输出的名称、支持的数据类型、数据格式等信息。”，它直接用于AICPU launcher 的 OP_ATTR_NAMES 形参、属性定义和 AICPU 原型。
- [ExtendCfgInfo](../../apis/utils_api/prototype_register_management/op_aicpu_def/extend_cfg_info.md)（`exemplifies`）：ExtendCfgInfo 与《AICPU launcher 缺 OP_ATTR_NAMES 编译错》的实质衔接是：ExtendCfgInfo 属于 OpAICPUDef 的扩展键值配置，AICPU 编译材料与 launcher 属性缺失故障说明该配置进入生成和加载阶段的位置。
- [KernelSo](../../apis/utils_api/prototype_register_management/op_aicpu_def/kernel_so.md)（`exemplifies`）：《KernelSo》说明配置AICPU算子实现文件编译生成的动态库文件的名称。；《AICPU launcher 缺 OP_ATTR_NAMES 编译错》说明无属性 regbase 算子的 ADD_TO_LAUNCHER_LIST_AICPU 调用若照搬 AICORE 写法省略 OP_ATTR_NAMES()，AICPU 宏会把第二个形参位（op::FVector<std::string>&，属性名向量）错绑到 OP_INPUT(...)，触发引用类型不匹配编译错。判别=build.sh --pkg 编译期报 invalid initialization of reference of type 'op::FVector<std::basic_string<char> >&' from expression of type 'op::OpInput<...>'，定位行紧随算子名后缺 OP_ATTR_NAMES()。AICORE 变体无该形参位，省略合法，二者宏签名不可互换。。二者在KernelSo、FunctionName、OpkernelLib和UserDefined共同确定AICPU实现动态库及入口符号的注册合同上存在可执行的直接衔接。
- [OpAICPUDef](../../apis/utils_api/prototype_register_management/op_aicpu_def/op_aicpu_def.md)（`exemplifies`）：《AICPU launcher 缺 OP_ATTR_NAMES 编译错》的任务是“无属性 regbase 算子的 ADD_TO_LAUNCHER_LIST_AICPU 调用若照搬 AICORE 写法省略 OP_ATTR_NAMES()，AICPU 宏会把第二个形参位（op::FVector<std::string>&，属性名向量）错绑到 OP_INPUT(...)，触发引用类型不匹配编译错。判别=build.sh --pkg 编译期报 invalid initialization of reference of type 'op::FVector<std::basic_string<char> >&' from expression of type 'op::OpInput<...>'，定位行紧随算子名后缺 OP_ATTR_NAMES()。AICORE 变体无该形参位，省略合法，二者宏签名不可互换。”。《OpAICPUDef》具体提供“OpAICPUDef算子定义接口索引。”，它直接用于AICPU launcher 的 OP_ATTR_NAMES 形参、属性定义和 AICPU 原型。
- [OpAttrDef](../../apis/utils_api/prototype_register_management/op_attr_def/op_attr_def.md)（`exemplifies`）：《AICPU launcher 缺 OP_ATTR_NAMES 编译错》的任务是“无属性 regbase 算子的 ADD_TO_LAUNCHER_LIST_AICPU 调用若照搬 AICORE 写法省略 OP_ATTR_NAMES()，AICPU 宏会把第二个形参位（op::FVector<std::string>&，属性名向量）错绑到 OP_INPUT(...)，触发引用类型不匹配编译错。判别=build.sh --pkg 编译期报 invalid initialization of reference of type 'op::FVector<std::basic_string<char> >&' from expression of type 'op::OpInput<...>'，定位行紧随算子名后缺 OP_ATTR_NAMES()。AICORE 变体无该形参位，省略合法，二者宏签名不可互换。”。《OpAttrDef》具体提供“OpAttrDef算子属性定义接口索引。”，它直接用于AICPU launcher 的 OP_ATTR_NAMES 形参、属性定义和 AICPU 原型。
- [OpAttrDef](../../apis/utils_api/prototype_register_management/op_attr_def/op_attr_def_functions.md)（`exemplifies`）：《AICPU launcher 缺 OP_ATTR_NAMES 编译错》的任务是“无属性 regbase 算子的 ADD_TO_LAUNCHER_LIST_AICPU 调用若照搬 AICORE 写法省略 OP_ATTR_NAMES()，AICPU 宏会把第二个形参位（op::FVector<std::string>&，属性名向量）错绑到 OP_INPUT(...)，触发引用类型不匹配编译错。判别=build.sh --pkg 编译期报 invalid initialization of reference of type 'op::FVector<std::basic_string<char> >&' from expression of type 'op::OpInput<...>'，定位行紧随算子名后缺 OP_ATTR_NAMES()。AICORE 变体无该形参位，省略合法，二者宏签名不可互换。”。《OpAttrDef》具体提供“class OpAttrDef {”，它直接用于AICPU launcher 的 OP_ATTR_NAMES 形参、属性定义和 AICPU 原型。
- [OpkernelLib](../../apis/utils_api/prototype_register_management/op_aicpu_def/opkernel_lib.md)（`exemplifies`）：OpkernelLib 与《AICPU launcher 缺 OP_ATTR_NAMES 编译错》的实质衔接是：OpkernelLib 在 OpAICPUDef 固定 CUSTAICPUKernel，必须与 KernelSo、Engine、FunctionName 和 AICPU OpDef/launcher 生成链一致。
- [UserDefined](../../apis/utils_api/prototype_register_management/op_aicpu_def/user_defined.md)（`exemplifies`）：《UserDefined》说明配置该算子是否为用户自定义算子，AICPU自定义算子的userDefined仅支持配置为“True”，若开发者没有配置的情况下，该参数会被默认设置为“True”。；《AICPU launcher 缺 OP_ATTR_NAMES 编译错》说明无属性 regbase 算子的 ADD_TO_LAUNCHER_LIST_AICPU 调用若照搬 AICORE 写法省略 OP_ATTR_NAMES()，AICPU 宏会把第二个形参位（op::FVector<std::string>&，属性名向量）错绑到 OP_INPUT(...)，触发引用类型不匹配编译错。判别=build.sh --pkg 编译期报 invalid initialization of reference of type 'op::FVector<std::basic_string<char> >&' from expression of type 'op::OpInput<...>'，定位行紧随算子名后缺 OP_ATTR_NAMES()。AICORE 变体无该形参位，省略合法，二者宏签名不可互换。。二者在UserDefined是AICPU注册属性，与KernelSo、FunctionName、OpkernelLib、OpAICPUDef及编译/launcher合同共同生效上存在可执行的直接衔接。
- [AI CPU算子编译](../../guides/programming_guide/compilation_and_execution/operator_compilation/ai_cpu_operator_compilation.md)（`related`）：《AICPU launcher 缺 OP_ATTR_NAMES 编译错》的任务是“无属性 regbase 算子的 ADD_TO_LAUNCHER_LIST_AICPU 调用若照搬 AICORE 写法省略 OP_ATTR_NAMES()，AICPU 宏会把第二个形参位（op::FVector<std::string>&，属性名向量）错绑到 OP_INPUT(...)，触发引用类型不匹配编译错。判别=build.sh --pkg 编译期报 invalid initialization of reference of type 'op::FVector<std::basic_string<char> >&' from expression of type 'op::OpInput<...>'，定位行紧随算子名后缺 OP_ATTR_NAMES()。AICORE 变体无该形参位，省略合法，二者宏签名不可互换。”。《AI CPU算子编译》具体提供“与AI Core算子只需一个.asc文件即可编译生成可执行文件不同，AI CPU算子需要同时包含.aicpu文件（核函数定义）和.asc文件（通过内核调用符调用核函数）才能编译生成可执行文件。”，它直接用于AICPU launcher 的 OP_ATTR_NAMES 形参、属性定义和 AICPU 原型。
<!-- cannbot:related:end -->
