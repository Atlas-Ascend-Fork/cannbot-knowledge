---
type: Optimization
title: frozen_parameter：固定权重输入地址的前提与转换顺序
description: 区分 npugraph_ex 主线与 GE 发布版的固定地址入口，说明稳定地址、Parameter 转换顺序和离线导图互斥。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/frozen_parameter.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/frozen_parameter.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/dynamo_export.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/graph_failed_cases.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/graph_failed_cases.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/frozen_parameter.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/frozen_parameter.md
  role: constraint
created_at: '2026-11-08T11:58:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# 固定权重输入地址

## 决策与配置

推理中权重类输入地址实际保持不变、下发开销可见时，可评估 npugraph_ex 的 `options={"frozen_parameter": True}`；默认 False。它减少固定输入地址相关的下发处理，不表示参数内容或模型状态可以任意改变。

来源还说明 PyTorch 2.6.0 及以上经 mark_static_address 标记的稳定地址输入可参与此机制。KV Cache 是否满足条件要按实际存储和调用检查，不能仅因其名称为 cache 就标记稳定。

## 设备转换顺序

来源示例要求先把普通 Tensor 移至 NPU，再包装成 torch.nn.Parameter；相反顺序的设备转换可能丢失 Parameter 类型，使优化前提不成立。应核对实际输入的类型和 data_ptr，而非只看初始化代码。

## 验证与回退

覆盖重复调用、权重更新/切换以及 KV 存储调整，确认地址契约仍成立，并比较输出和下发耗时。无法保持地址时关闭 frozen_parameter 并重新编译相应图；不要继续使用旧缓存。本卡描述固定主线，未测得性能收益。

## 版本入口

- [软件栈来源与适用性](../../concepts/frameworks/ascend_software_stack_baselines.md)：来源快照、部署配套和实际运行验证分别核对。

## GE 发布分支的对应配置

在固定发布子模块 7c6c754bed00c86ffaaa2a45cb7ac2724f058013 的 A2/A3 GE 路线中，对应开关是 config.experimental_config.frozen_parameter=True，默认 False；Parameter 或 PyTorch≥2.6 的 mark_static_address 输入仍要求真实地址稳定，设备转换顺序相同。它不是 npugraph_ex options 的配置入口，且不能与 dynamo_export 同时启用。

RefData 处理输入原地更新，与地址固定分别核对，见[GE 原地输入](../../guides/optimization/torchair/ge_refdata_and_mutated_inputs.md)。本节不把发布版 GE 范围扩展到本卡主线 npugraph_ex 的其他硬件，也不从主线行为反推发布支持。

## GE 发布版的非连续参数案例

固定发布子模块的 A2/A3 案例中，开启 frozen_parameter 后与 Eager 精度不一致，关闭后恢复。比较 GE/Eager Dump 和 Python runtime inputs 日志，发现输入 Parameter 为 contiguous=False；该案例需要在建立固定地址前把对应参数转为连续存储。

这只是已定位原因之一，不表示开关相关精度差异都由非连续输入造成。contiguous() 可能更换存储；须重新确认 Parameter 身份、地址及所用缓存，不能先捕获旧地址再无条件替换。先逐阶段比较真实输入，见[入图失败与推导偏差](../../guides/optimization/torchair/ge_shape_dtype_failure_diagnosis.md)。

## GE主线案例与布局转换

TorchAir主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的入图案例仍记录frozen_parameter与非连续Parameter相关的精度问题。定位先比较开关前后GE/FX输入Dump和runtime inputs中的contiguous信息，再确认目标参数的真实布局；不能把这个案例推广为所有量化或转置权重都应无条件contiguous。格式准备可能改变算子的布局前提，也可能换存储，须在固定地址和缓存建立前完成并重新检查输出。

这只是主线案例依据，不把GE配置入口与npugraph_ex options合并；两后端的开关、软件配套和已运行证据仍分别核对。

## GE主线的正式开关页

主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的GE frozen_parameter页与发布页保留相同参数契约：config.experimental_config.frozen_parameter默认False；Parameter或PyTorch≥2.6的mark_static_address输入都需要真实地址保持稳定。主线总体产品含950，本节仅补齐其GE文档依据，不把npugraph_ex的options对象用于GE。

文档的普通Tensor先到NPU再包装Parameter示例，不是说任意Module.to都会破坏全部已注册参数；对具体传入图的Tensor检查真实类型、地址和布局。固定地址不是冻结内容，也不替代RefData的写回协议。优化目标是减少下发相关开销，仍需同负载对比，不从示例或接口存在推导固定收益。

## Evidence

- [docs/zh/npugraph_ex/basic/frozen_parameter.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/npugraph_ex/basic/frozen_parameter.md)（primary）
- [docs/zh/overview.md](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）

- [补充来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/advanced/frozen_parameter.md)（constraint）

- [补充来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/torchair/dynamo_export.md)（constraint）

- [补充来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [补充固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/graph_failed_cases.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/appendix/cases/graph_failed_cases.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/advanced/frozen_parameter.md)（constraint）

- [完整页复核来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/npugraph_ex/basic/frozen_parameter.md)（constraint）
