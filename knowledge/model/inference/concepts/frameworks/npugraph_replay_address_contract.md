---
type: Concept
title: NPUGraph 捕获重放：静态地址、输入拷贝与安全子图
description: 说明底层 NPUGraph 重放与 torch.compile 后端的区别，固定地址输入更新和安全子图捕获的职责。
tags:
- task.design
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/npugraph.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/npugraph.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/npugraph.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/npugraph.png
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/compilation_backend/npugraphs.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/torch_compile/compilation_backend/npugraphs.md
  role: constraint
created_at: '2026-11-08T11:58:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- agnostic
---

# NPUGraph 的捕获与重放契约

NPUGraph 将一串设备 Kernel 捕获为可重复提交的执行单元，主要减少逐 Kernel 的 CPU 启动开销。捕获后的结构、操作序列和所用地址保持稳定；重放时新输入需要写入捕获使用的存储，而不是仅把 Python 变量重新指向另一 Tensor。

固定主线说明限定仅支持 aclnn 算子入图。选择安全子图时，需要确认实际执行的算子实现满足该范围；Eager 可以执行并不能单独证明可被 NPUGraph 捕获。

底层 NPUGraph 类允许调用方手动管理流和捕获边界；graph 上下文简化捕获；make_graphed_callables 可以封装安全子图，并处理其输入地址变化时的拷贝。动态分支可留在图外选择已经捕获的子图，不能因此宣称子图内部支持任意动态控制流。

固定来源还说明对部分算子的动态参数有专门更新机制；只有已支持的 Handler 路径才可使用，不能将其外推为所有参数均可动态变化。纯动态 shape、频繁 CPU/NPU 同步和变化的图结构需要特别审查。

验证时比较首次捕获、多次重放与 Eager，核对 data_ptr、输入内容与输出。底层手工捕获、图化 callable 和 npugraph_ex 编译后端有不同交付件与支持范围。本文只表达固定主线的机制，不声称已在某硬件或发布组合执行。

## 版本入口

- [软件栈来源与适用性](ascend_software_stack_baselines.md)：来源快照、部署配套和实际运行验证分别核对。

## 图示和训练子图示例的含义

中英文NPUGraph图逐字节相同，已查看：逐算子CPU launch间隙与BuildGraph后单次LaunchGraph的紧凑设备任务对照是机制示意，没有测量数值。手工NPUGraph及graph上下文示例使用静态存储，新数据copy_入捕获地址；重新赋值Python变量不更新旧地址内容。

make_graphed_callables训练例先创建三个Linear和SGD，再图化安全模块，前向/反向使用固定子图并按支持路径处理输入地址变化。分支条件的item留在图外仍可能带来CPU/设备同步；它只是选择预捕获的分支，不使图内出现任意动态控制流。auto_dispatch_capture_handlers只更新已有Handler支持的动态参数，不等于任意动态shape可捕获。

来源的10次加法、1000元素与训练10步是历史示例，不是本机结果或性能数据。底层捕获只支持aclnn的限制、输出存储与Autograd生命周期、Level2队列互斥及编译后端自己的合同仍须分别满足。

## npugraphs编译入口的固定形状约束

固定中英文用户专页将backend="npugraphs"定义为Dynamo FX图到NPUGraph/ACLGraph的自动捕获重放入口；需要手工流、分区域或安全子图控制时才选前文底层API。这不是TorchAir独立npugraph_ex，也不代表所有底层API参数都成为该后端options。

页面明确捕获后batch_size/序列长度等形状固定且所有算子必须走aclnn；其options表同时列triton.cudagraphs、trace.enabled、enable_shape_handling、npu_backend，表名本身不能取消固定形状约束或证明每项被该后端正确消费。当前ShapeHandling局部门控与文档例子差异见[分档草稿](../../guides/optimization/torch_npu/shape_handling.md)。

该页建议动态形状考虑Inductor reduce-overhead Tree：多种输入分别捕获/缓存再路由，不表示已捕获的一张静态图可任意改shape。样例的1000次前向、未使用的fixed_target及“消除开销”文字不证明完成训练、零CPU成本或达到某种加速；输入地址、模型状态和依赖仍独立核验。

## Evidence

- [docs/zh/developer_notes/npugraph.md](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/developer_notes/npugraph.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/developer_notes/npugraph.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/figures/npugraph.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/figures/npugraph.png)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/zh/user_guide/torch_compile/compilation_backend/npugraphs.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/docs/en/user_guide/torch_compile/compilation_backend/npugraphs.md)（constraint）
