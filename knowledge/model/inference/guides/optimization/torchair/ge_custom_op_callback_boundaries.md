---
type: Guide
title: GE 零交付件回调：布局、动态输出与进程边界
description: 区分 Python/C++/Triton 回调的类型和输出能力，明确布局不保真、连续化写回及编译产物不可跨进程迁移。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/custom_op_graph/custom_op_zero_delivery.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
created_at: '2026-11-09T04:41:52Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
---

# GE 零交付件回调：布局、动态输出与进程边界

## 版本和前置条件

依据 TorchAir 固定主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c`，限定 A2/A3 的 GE max-autotune 路线，不推导发布基线具备该能力。“零交付件”仅指无需额外交付 GE Converter/回调和 OPP 包，实际算子仍必须存在。

Schema-based 算子需要 Schema、PrivateUse1 实现、Meta；已有原生 Converter 或 GE IR 时优先走已有实现。需要 SuperKernel、分核或原生融合时仍选择原生适配路线。

## Schema 和动态输出

支持 Tensor、Optional Tensor、Tensor 列表、常见标量/字符串/部分枚举及其列表；Dict 和未知 Schema 类型不支持。Tensor 列表输入数在构图时记录，Tensor 列表输出数由 Meta 确定；标量在构图中成为常量形式，执行时再恢复，不应据此推导任意动态 Python 值均可无重编译改变。

|能力|Python 定义算子的回调|C++ 定义算子的回调|
|--|--|--|
|out 参数与 Tensor[] 返回组合|Tensor[] 必须排在所有固定返回之后，写别名标注正确|文档同时支持列表返回在固定返回之前的组合|
|实际输出 shape 超出 Meta 规格|写回时报错|按实际 shape 分配内存|
|qint8/quint8/qint32、float8_e5m2/e4m3fn/e8m0|输入或输出映射报错|文档提供对应映射能力，仍需实际算子支持|
|hifloat8|PyTorch 无对应 dtype，不能映射|同样不支持，应使用原生 Converter|

以上是两条回调机制的差别，不是任意量化算子或硬件支持声明。In-place 写回还依赖 Schema 的 alias 能匹配被修改输入，不能把普通视图别名当作自动保真的能力。

## 布局和存储语义的失效边界

回调包装只保留数据地址、storage shape 和 dtype；不恢复原始 stride、storage offset 及普通输入输出共享 storage 的关系。回调中呈现连续 stride，storage_offset 为 0，输入输出的普通存储别名不保真。按 storage_offset 选择分支、硬编码列主序步长或依赖转置视图共享存储的算子，可能与 Eager 不一致。

输出写回 GE 前会 contiguous。逻辑值相同不证明后续依赖特定布局的消费者仍正确；应联合验证生产者与消费者，并覆盖非连续输入、带偏移切片、视图和原地更新。若语义依赖这些属性，优先原生适配。Schema mutation 的回写机制与普通视图别名是不同层次，不能相互替代。

## Triton 的独有限制

支持 functional 调用：kernel 写入新建输出 Tensor，可以通过 triton_op/wrap_triton 或普通 Python 函数直接启动 jit kernel 被捕获。直接写输入指针、mutates_args 非空的 mutation HOP 会在编译时拒绝。Triton 复用 Python dtype 映射，**没有可切换的 C++ 回调路线**；不能用 Schema-based 算子的 C++ 能力为它绕过类型限制。

## 临时产物与部署

自动生成的 GE 原型、动态库和 Python 回调保存在进程临时目录：TMPDIR、TEMP、TMP 依次选择，默认 /tmp；每个进程首次编译创建自己的目录，同进程多图复用。动态库引用在执行期保留，产物不持久交付，也不生成 custom_opp run 包。

编译和执行必须在同一进程；不能将图产物迁移到其他进程执行，多进程部署需各自调用 torch.compile。GE Dump 显示合成节点名，Profiler 显示回调下发的原始 kernel 名，二者是包含关系，性能分析应核对设备 kernel，而非按图节点名字直接匹配耗时。

- [自定义算子整体接入与原生路线](../../integration/torchair/custom_operator_graph_contract.md)
- [Converter 实现与类型提升](torchair_converter_implementation.md)

本文仅静态审阅，没有编译临时代码、加载动态库或执行设备实验。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/custom_op_graph/custom_op_zero_delivery.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）
