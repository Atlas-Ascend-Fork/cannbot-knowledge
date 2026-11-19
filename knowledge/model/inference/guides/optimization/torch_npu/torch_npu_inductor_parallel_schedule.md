---
type: Guide
title: 950DT Inductor并行调度：CV分组、流依赖与策略接入
description: 记录推理和图下沉前提、分组日志、生成物与内部自定义策略接口。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/parallel_schedule.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/parallel_schedule.png
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/parallelism_strategy_base.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/parallelism_strategy_framework.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/parallelism_strategy_default.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/parallelism_strategy_cv.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/utils/schedule_node_utils.py
  role: implementation
created_at: '2026-11-09T15:23:53Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# 950DT Inductor并行调度：CV分组、流依赖与策略接入

## 固定范围与启用条件

依据TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf内部parallel_schedule说明，面向950DT及PyTorch2.9示例，当前只适用于推理且需开启图下沉。不是任意版本、训练、A2/A3或PR支持承诺。ENABLE_PARALLEL_SCHEDULER默认False，大小写不敏感的true启用，1不启用；Python Wrapper及小图阈值等独立限制仍见[资源指南](torch_npu_inductor_compile_resources_and_passes.md)。

## 融合后分组与完成依赖

在Kernel Fusion后标记Cube/Vector/Scalar等计算单元，按收敛算法及CV策略将可并行且组间单元不同、组内同类的子图分流；没有数据依赖不代表生成器必分到不同流，配置开启也不证明真实设备重叠。

可观察cv parallel group len和CUBE/VECTOR/MAIN组日志，并检查output_code.py的stream/event定义。示例main_event先在主流记录，Cube组等待该事件后消费前序输出，工作区及kernel传入组stream；片段没有展示所有结束/回收路径，不能复制片段就宣称任意依赖和Tensor寿命已正确。关闭后无该分组日志/生成物是其对照线索，不是所有程序不得出现任何Stream/Event。

## 自定义策略是源码接入

来源示例继承ParallelStrategyBase并实现assign_parallel_groups(nodes)，返回组名到BaseSchedulerNode列表的字典；在_inductor/__init__.py的启用分支导入策略，用register_custom_parallel_strategy("custom", CustomParallelStrategy)注册后调用parallel_scheduler。相对导入和修改初始化文件属于该版本内部源码示例，不是独立公共API或可在任意应用中直接复制的注册配方。

已查看架构图将CommonParallelStrategy、CVParallelStrategy与自定义策略放在计算单元分析后，再交ParallelismCodegen分流；图中pre/joint/post自定义Pass入口是另一层。自定义返回的分组仍需保证拓扑、依赖及资源正确，不由基类继承自动获得安全并行。

分别核对软件/图模式、分组日志、生成事件、实际时间线和稳态数值/耗时。本文未修改上游初始化文件、注册策略或运行NPU。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/parallel_schedule.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/parallel_schedule.png)（primary）

## 本地策略注册与阈值读取的真实行为

补充固定主线ac0e1564的base/framework/default/CV及schedule_node_utils五个完整本地模块，共456行；对应发布f3ecfe4精确路径Git树为空，只说明路径不同，不否定其它发布并行方案。前文文档的950DT/推理/图下沉条件保留，策略函数自身不会重复验证所有这些入口条件，也不覆盖整个Wrapper或Runtime。

ParallelStrategyBase只声明assign_parallel_groups抽象方法，__init__中的name注解不实际赋值。register_custom_parallel_strategy把传入对象放入dataclass，全局同名项直接覆盖；execute时取strategy_cls()，因此既有示例传类，不是任意实例都可直接工作。每次ParallelGroupingStrategy初始化重写default为CVParallelismStrategy，但不清已有custom；选择只优先名为custom的键，否则default，注册其它名字不意味着会被当前驱动选中。

源码直接os.environ.get("PARALLEL_SCHEDULER_NODES_MIN",20)，没有int转换：未设置时len(nodes)≤20返回空dict；设置任何普通环境字符串后，这里的int与str比较会进入类型错误路径，CV中的同名环境值再做//5也有字符串算术边界。文档“阈值20”不能改写成这个本地入口已健壮解析自定义数字。未执行该错误路径，不把它当设备运行故障证明。

is_multi_stream只有ENABLE_PARALLEL_SCHEDULER转小写等于true且wrapper是NPUPythonWrapperCodeGen才True，不读取一般硬件流能力。它不验证其它依赖和生命周期；返回True不等于已经生成并实际并行执行。

## 默认分支分组与前驱关系来源

默认策略构建name/node顺序和前驱表，从最后一个恰有两个前驱的收敛节点取两路祖先集合；没有收敛或没有该二路节点时返回空list，空输入返回空dict，类型注解不保证所有失败路径同一返回类型。前驱helper先使用非空mpi_node.pred_nodes；否则合并已知名称的ancestors、reads与unmet_dependencies，不是无条件遍历所有别名或跨图依赖。

make_disjoint按列表先到优先保留共享祖先，后续集合剔除已见项；不是把共享节点都移到主流。各路按原图顺序只保留从首项开始的连续前缀，遇第一个间隙就截断。再逆向查第二路对第一路的依赖，find_first_overlap返回第一路末端优先的匹配索引；调用者用if index判断，因此索引0不会进入截断分支。这里不是完整的任意依赖证明。

非空两路按MIX_01/MIX_02保存，余节点进入MAIN；successors辅助表不作为这里另一套最终调度验证。它是分组启发式，不负责在此插真实event或认证Tensor存储存活。

## CV分类与选段是启发式

CV给节点写compute_unit：CATLASSTemplateBuffer识为CUBE，node包装递归剥开，带非空snodes的融合节点先识VECTOR，multioutput可跟第一输入；其余结合Kernel名、op_overload、类名和data类名找conv/mm/matmul/linear等子串识CUBE，Pointwise/Reduction结合origins区分norm/softmax与MLP_VECTOR，add/激活等亦可判MLP_VECTOR，无法识别为UNKNOWN。名称匹配不是设备性能计数器，也没有把任意多输出各分支分别分类。

先用默认分组，少于3组就返回空dict；从前两组各提首条Cube连续链（允许夹一个MLP_VECTOR后接Cube）及首条以Vector/MLP_VECTOR开头、后续可含Scalar的链，再选原始节点列表中最长连续段。两路Cube和Vector分别取原列表长度较大者，平手偏第一路；融合节点子数只在后续阈值计数时展开，选择“大组”时不是统一按Kernel数或运行耗时排序。

两最终段之间只检查各自末节点到另一段首节点的前驱关系，不能由这两个端点检查宣称所有内部数据依赖、事件或别名均已认证。未设置环境时子组最小计数20//5=4；任何一组太小或端点判有依赖，则Cube和Vector都清空，所有节点回MAIN，但仍返回CUBE/VECTOR/MAIN三个键。空组字典存在不证明分流发生。

extract_special_groups的类型注解列三个返回列表：空group分支实际返回三个空列表，非空末尾返回Cube与Vector两个，而调用方解包两个；现默认分组到达len(groups)>=3时前两MIX组非空，不能由这个局部差异认定正常路线必失败，也不能把返回形状说成始终相同。最长连续段平手保留较早段，未找到段返回空。上述失败路径和计数只是Host策略静态行为，没有运行调度或重叠性能实验；最终仍要结合生成物和时间线验收。
