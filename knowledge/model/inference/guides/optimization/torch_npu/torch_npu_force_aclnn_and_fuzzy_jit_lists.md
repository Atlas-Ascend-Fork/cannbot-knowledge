---
type: Guide
title: TorchNPU FORCE_ACLNN_OP_LIST 与 NPU_FUZZY_COMPILE_BLACKLIST：名单解析与消费面
description: 固定主线源级核对两个环境变量名单的逗号解析、单例集合语义、jit 默认关闭规则及消费面；FORCE_ACLNN 的消费发射点在本仓 torchnpugen
  代码生成模板，生成物运行时路由在 pin 外。
tags:
- task.optimization
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/ForceAclnnList.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/ForceAclnnList.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/ForceJitCompileList.cpp
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/ForceJitCompileList.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/interface/EnvVariables.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpParamMaker.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpParamMaker.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/utils.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torchnpugen/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/ForceAclnnList.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/ForceAclnnList.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/ForceJitCompileList.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/ForceJitCompileList.h
  role: implementation
created_at: '2026-11-13T05:22:15Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU FORCE_ACLNN_OP_LIST 与 NPU_FUZZY_COMPILE_BLACKLIST：名单解析与消费面

## 固定版本与范围

固定 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`，整读 ForceAclnnList.cpp/.h、ForceJitCompileList.cpp/.h，定向阅读 EnvVariables.cpp 的注册钩子与 CheckJitDisable、OpParamMaker.cpp/.h 的名单消费点，并核对 `torchnpugen/utils.py` 代码生成模板中的 `IsForceAclnnOp` 消费发射点（主线与发布 f3ecfe4a7ef7395754da7ca2e35661a7132b519b 两 pin 均核）。静态阅读，未执行名单相关编译或运行验证。`FORCE_ACLNN_OP_LIST` 设置后的实际算子路由发生在 torchnpugen 生成的绑定代码运行时（生成物不在 pin 内），该边界在文末如实分列。

## 两个名单的解析契约

`FORCE_ACLNN_OP_LIST` 经 `REGISTER_OPTION_HOOK` 调 `ForceAclnn::RegisterOp`；`NPU_FUZZY_COMPILE_BLACKLIST` 调 `ForceJitCompileList::RegisterJitlist`。两者解析相同：非空才处理，按逗号切分，逐 token 插入 `std::set<std::string>`，空 token 跳过，尾段单独补插；集合即单例成员（`GetInstance` Meyers 单例），重复项由 set 去重。**名单是 op 名的精确字符串匹配，无通配符、无大小写归一、无前后缀语义**；`NPU_FUZZY_COMPILE_BLACKLIST` 注册后 `DisplayJitlist` 对每个成员打一条 `ASCEND_LOGI`（"use Just-In-Time compile"），可据此确认名单实际生效内容。两个名单互不联动：进 fuzzy blacklist 不影响 aclnn 名单，反之亦然。

## jit 默认关闭与名单的消费链（pin 内）

`env::CheckJitDisable()` 的真实语义：`jitCompile` 选项为 "disable" 时真、"enable" 时假；**未设置时 SocVersion ≥ Ascend910B1 默认为真（即默认关闭 JIT 编译）**，旧平台默认假。这解释了名单的实际用途——910B1+ 默认关闭 JIT 的环境下，`NPU_FUZZY_COMPILE_BLACKLIST` 是「按算子恢复 JIT」的白名单：

- `OpParamMaker.cpp`：aclop 执行时若 `Inlist(name) && CheckJitDisable()`，先 `AclSetCompileopt(ACL_OP_JIT_COMPILE, "enable")` 临时打开 JIT，执行完成后由同文件的后续路径恢复 "disable"。即名单成员在全局关闭 JIT 时仍走即时编译。
- `OpParamMaker.h`：构造执行参数时若 `!Inlist(opName) && CheckJitDisable()`，置 `params.isJitDisable = true`，非名单成员显式携带 jit 关闭标记。
- 名单只影响 aclop 即时编译路径的开关切换，不改变 aclnn 路线、不改变编译缓存（缓存行为见[ACL Op 编译缓存](torch_npu_aclop_cache_and_contiguous_views.md)）。

## FORCE_ACLNN 的消费发射点与边界

pin 内静态契约：`ForceAclnn` 单例保存集合并提供 `IsForceAclnnOp(op_name)` 成员查询；`FORCE_ACLNN_OP_LIST` 是唯一注册入口。消费发射点在本仓（pytorch pin）的代码生成模板：主线 `torchnpugen/utils.py:354-356` 把 `f'at_npu::native::ForceAclnn::GetInstance().IsForceAclnnOp("{op_name}")'` 存为 `force_aclnn`，在生成的 PrivateUse1 绑定模板中于四处（:535/:549/:560/:573）产出 `if (({force_aclnn} || at_npu::native::env::CheckJitDisable()){tensor_check_str}) { ...op_api_impl_name(...) } else { ...impl_name(...) }` 分派——**名单成员（以及 jit 默认关闭判定）在生成代码里把算子从常规实现切到 op_api（aclnn）实现**；发布 pin 同一发射点在 `torchnpugen/utils.py:294`（模板消费 :489/:503/:514/:527，两版机制一致）。op-plugin 两个 pin（d84e9b1d/dedc3167）全树 grep 无 `IsForceAclnnOp`/`ForceAclnn` 命中（`FORCE_ACLNN` 仅 test_matmul_backward_empty.py 断言字符串），其 aclnn 装载走 `libaclnn_*.so` 特性库，与该名单无关。真正的 pin 外边界是：torchnpugen 生成的绑定代码与运行时按 `IsForceAclnnOp` 结果选择执行路径的行为发生在生成物/CANN 侧，pin 内只能读到发射模板，「设置该变量后某算子实际走 aclnn」仍须在目标环境验证。

## 验证与失效边界

定向验证：名单拼错 op 名时行为不变（精确匹配）、fuzzy 名单成员在 910B1+ 默认 jit 关闭下是否出现即时编译日志、`DisplayJitlist` 输出与变量值一致、`jitCompile` 显式设置后名单语义变化。本卡未执行上述实验。名字近似但不完全匹配的算子不会被命中，这是最常见的配置失效方式；两个名单在进程内首次设置后无移除接口，改名需重启进程。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/ForceAclnnList.cpp)（primary），读取范围 1–51 全文。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/ForceAclnnList.h)（implementation），读取范围 1–42 全文。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/ForceJitCompileList.cpp)（primary），读取范围 1–64 全文。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/utils/ForceJitCompileList.h)（implementation），读取范围 1–29 全文。
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/interface/EnvVariables.cpp)（implementation），读取范围 160–205、265–273。
- [固定来源 6](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpParamMaker.cpp)（implementation），读取范围 285–300（含 368 的恢复点定位）。
- [固定来源 7](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/framework/OpParamMaker.h)（implementation），读取范围 285–300。
- [固定来源 8](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torchnpugen/utils.py)（primary），读取范围 354–356、525–580（IsForceAclnnOp 消费发射点；另核 :535/:549/:560/:573 四处模板消费）。
- [固定来源 9](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torchnpugen/utils.py)（implementation），读取范围 294、480–535（发布 pin 同一发射点，模板消费 :489/:503/:514/:527）。

## 发布 pin 对照（f3ecfe4a）

本节结论来自发布 pin 孪生文件的逐文件比对（比对口径：sha256 → 去空白 → 全空白折叠 token → 注释剥离 token）。

### 等价绑定（结论对发布 pin 直接适用，行号锚不同）

- `torch_npu/csrc/framework/utils/ForceAclnnList.cpp`、`ForceAclnnList.h`、`ForceJitCompileList.h`：全空白折叠后逐字节等价（仅重排版）。
- `torch_npu/csrc/framework/utils/ForceJitCompileList.cpp`（64 → 67 行）：注释差异等价（代码 token 流相同）。名单解析契约、单例/set 语义、DisplayJitlist 日志行为结论对发布 pin 直接适用。
- 消费发射点 `torchnpugen/utils.py` 的发布侧对照已见上文「FORCE_ACLNN 的消费发射点与边界」（发布 :294/:489-527，机制与主线一致）。

### Evidence（发布 pin 补绑）

- [发布孪生 1](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/ForceAclnnList.cpp)（release-twin-binding）：全空白折叠等价。
- [发布孪生 2](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/ForceAclnnList.h)（release-twin-binding）：全空白折叠等价。
- [发布孪生 3](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/ForceJitCompileList.cpp)（release-twin-binding）：注释差异等价。
- [发布孪生 4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/csrc/framework/utils/ForceJitCompileList.h)（release-twin-binding）：全空白折叠等价。


（本节静态比对，未运行/未编译；结论按文件分列，未列出的文件未比对。）
