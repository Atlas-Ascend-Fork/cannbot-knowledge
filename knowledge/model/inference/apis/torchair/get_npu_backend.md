---
type: API
title: torchair.get_npu_backend：获取 GE 图编译后端
description: 获取传给 torch.compile 的 GE 后端，说明 CompilerConfig、custom_decompositions 与配置生效时机。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/torchair/get_npu_backend.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/quick_start.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/quick_start.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/SECURITY_README.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/SECURITY_README_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/SECURITY_README.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/CONTRIBUTING_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/CONTRIBUTING.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/get_npu_backend.md
  role: constraint
created_at: '2026-11-08T11:58:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 获取 GE 图编译后端

## 接口和返回值

```python
torchair.get_npu_backend(*, compiler_config=None, custom_decompositions={})
```

返回可作为 `torch.compile(..., backend=...)` 参数的编译后端。compiler_config 是 CompilerConfig 实例；省略时采用 TorchAir 默认配置。custom_decompositions 用字典指定算子分解，改变前端看到的计算表达。

## 使用顺序

导入匹配的 torch、torch_npu、torchair，完成模型和输入的设备放置，设置 CompilerConfig，再构造 backend 并交给 torch.compile。构造成功不等于所有目标算子都有 Converter；实际成图与执行仍须触发并核验。

## 边界和验证

本文对应固定 TorchAir 主线；不把默认 GE 配置转换为 npugraph_ex options。对相同输入比较 Eager 和编译输出，并保存后端、动态形状选项和编译日志。没有执行 NPU 编译或精度测试。

## 版本入口

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)：来源快照、部署配套和实际运行验证分别核对。

## GE快速入口与torch.compile参数层次

主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 和发布 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013` 的GE quick_start都通过CompilerConfig.mode="max-autotune"选择GE（默认即此模式），再get_npu_backend后显式传给torch.compile。这里的mode属于TorchAir配置对象，不等于torch.compile(mode=...)；两份快速页均将该入口的torch.compile mode/options标为暂不支持，不能把另一个npugraph_ex入口的options直接移入。

torch.compile的fullgraph默认False、dynamic默认None；需要整图或明确动态追踪时应显式设置，不因图后端被选中便宣称已经fullgraph。disable=True走单算子，backend默认inductor也不是自动选择TorchAir。快速页按torch_npu后torchair导入并让模型/输入到同一NPU；构造backend与触发编译/执行分开核验。

示例中的patch_for_hcom为可选旧兼容步骤，主线实际实现仍会修改全局函数，不能对所有新版本照抄；[通信入图契约](../../guides/optimization/torchair/collective_communication_graph_contract.md)保存其限制。主线快速页新增死锁检测及多流并行模式导航，只是配置入口索引，不表示默认都已开启或相互兼容。本次未运行快速示例。

## 根接口摘要与返回层次

两快照安全声明的签名使用custom_decompositions复数，参数解释却写custom_decomposition单数；按实际签名消费，不把两拼写当别名。get_compiler返回编译器组件，get_npu_backend返回交给torch.compile的后端，不能因组件函数存在就把它直接当完整后端、所有配置和运行生命周期。

这几页将正式接口限定为有文档的Python入口，内部C++动态库符号不直接服务用户。发布贡献样例遗漏CompilerConfig导入并额外构造一次未保存的compile结果，主线英文改为tng.CompilerConfig且仅保留实际赋值；这些示意不作为无需触发模型调用即已完成图编译的证据。

## Evidence

- [docs/zh/ascend_ir/api/torchair/get_npu_backend.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/torchair/get_npu_backend.md)（primary）
- [docs/zh/overview.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/quick_start.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/quick_start.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/SECURITY_README.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/SECURITY_README_en.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/SECURITY_README.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/CONTRIBUTING_en.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/CONTRIBUTING.md)（constraint）

- [完整页复核来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/get_npu_backend.md)（constraint）
