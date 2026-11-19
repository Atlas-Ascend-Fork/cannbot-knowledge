---
type: Guide
title: FXRT推理运行时：独立后端、view回退与图执行边界
description: 说明随TorchNPU发布的FXRT导入入口和局部实现，保留view禁用开关的实际生效范围与未闭合产品合同。
tags:
- task.optimization
- topic.graph_execution
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/README_CN.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/README.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/fx_backend.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/executor.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/executor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/mempool.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/mempool.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/op_runner.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/op_runner.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/kernel_capture/kernel_capture_executor.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/kernel_capture/kernel_capture_executor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/kernel_capture/utils/graph_capture_manager.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/kernel_capture/utils/graph_capture_manager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/config/ascend/aclgraph.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/config/device/ascend/aclgraph_conf.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/config/device/ascend/aclgraph_conf.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/pybind/fxrt/pybind_aclgraph_config.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/builder/kernel_capture/kernel_capture_builder.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/builder/kernel_capture/kernel_capture_builder.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/builder/builder.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/builder/builder.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/utils/utils.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/utils/utils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/utils/async.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/pybind/fxrt_torch/pybind_torch.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/ir.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ir/graph.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ir/graph.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/fxrt/test_fxrt_basic.py
  role: example
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/pipeline/pipeline_executor.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/pipeline/pipeline_executor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/builder/pipeline/pipeline_builder.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/builder/pipeline/pipeline_builder.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/pipeline/async_task_queue.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/pipeline/async_task_queue.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/pipeline/async_task_queue_manager.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/pipeline/async_task_queue_manager.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/pipeline/lock_free_ring_queue.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/kernel_launch_group/kernel_launch_group_executor.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/kernel_launch_group/kernel_launch_group_executor.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/builder/kernel_launch_group/kernel_launch_group_builder.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/builder/kernel_launch_group/kernel_launch_group_builder.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/kernel_launch_group/memory_cache/memory_cache.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/kernel_launch_group/memory_cache/memory_cache.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/utils/exception.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/utils/exception.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/utils/spinlock.h
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/common/common.h
  role: implementation
created_at: '2026-11-09T16:51:39Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FXRT推理运行时：独立后端、view回退与图执行边界

## 固定来源与范围

固定TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的双语FXRT README、包入口，以及fx_backend.py的view开关和后端入口局部。README没有完整产品/软件配套矩阵，本卡draft、platforms为空，不回推发布版，也不从torch.compile可调用推导训练/反向支持。本次未导入、构建或执行FXRT。

## 构建与导入是独立选择

FXRT随TorchNPU wheel发布于torch_npu/fxrt，没有单独发行包；构建可用--disable_fxrt排除。nanobind为文档所述额外构建期依赖，不据此推定运行期无需TorchNPU/CANN或原生库。--python=3.10只是源码示例，仍核对当前构建清单和实际依赖。

仅import torch_npu不加载FXRT；from torch_npu.fxrt import backend后以torch.compile(fn, backend=backend)接入其自有IR/GraphExecutor。包入口在顶层名fxrt下加载并镜像torch_npu.fxrt.*，两名称指向同一模块树；若先已有fxrt模块会沿现有项，不能与另一个同名安装包随意混装。register_fx_wrapper另需调用者明确请求，导入本身不自动接管Inductor codegen。

## view优化和对照开关

README示例用两份(2,8)输入，相加后view(4,-1)、relu，旨在说明view零拷贝和时延/内存复用，不是所有reshape/stride/alias关系都合法的证明，也没有模型吞吐测量。

FXRT_DISABLE_VIEW_OPS文档列permute/transpose/t/movedim/split/chunk的逗号列表或all。局部实现对token strip/lower、去空项；按最终映射的Op及目标别名选中回退，当前显式非view回退表只有permute_view、split_with_size_view、split_tensor_view。没有回退项时打印ignored并保留view，**all不等于关闭所有view优化**；view/reshape/slice等名字出现在映射表也不保证可禁用。比较前核对实际lowering和日志，不能仅凭环境值宣布零拷贝已关闭。

## 入口实现中的边界

后端入口在构建GraphExecutor前做布局恢复、copy消除和分解、注册映射钩子及精度配置，处理placeholder/get_attr/call_function/call_method/output；call_module分支明确抛NotImplementedError。不能把torch.compile前端可能做的变换与本入口直接接收任意节点混同。

运行闭包设置设备上下文并更新输入，再executor.run和to_torch；参数与非参数Tensor根据example_value记录，graph_key为executor身份，向输入更新传静态化提示。这些局部调用不证明任意动态shape、地址或别名都可安全重放，也不宣称全部GraphExecutor/算子实现已审阅。

FXRT_DEV_DUMP_IR只精确1开启，将原FX图与FXRT图追加到当前目录graph_{pid}.txt；分布式已初始化时含rank。文件名不含完整模型/环境身份，多图可追加同文件，dump开销与业务性能分开。未创建文件或读取真实产物。

## 执行模式的实际选择与开关时机

以下补充只绑定同一主线提交，覆盖26份完整实现/测试文件及fx_backend.py入口3211..3293；产品和配套合同仍未知，保持draft、空平台，不将本轮推广到发布快照或全部FXRT算子。

GraphExecutor.BuildExecutor按Base、Pipeline、GroupLaunch、AclGraph顺序覆盖选择，实际优先级为AclGraph > GroupLaunch > Pipeline > Base。TASK_QUEUE_ENABLE仅精确字符串0禁用Pipeline，未设置时该判断为开启；FXRT_KERNEL_LAUNCH_GROUP_NUM只要非空就选择GroupLaunch，字符串0在这里也不是关闭，合法组数还须核对该builder。FXRT_ENABLE_ACLGRAPH只精确on开启，而且IsAclGraphEnabled首次调用后缓存结果；应在首次相关调用前设定，运行中改环境不保证切换已有executor。

Python GraphExecutor.build的opt_graph调用被注释，仅调用build_executor；后端前面的Python布局恢复、copy消除和分解仍实际发生，不能从build的“Optimize”注释推导C++ PassManager自动运行。普通Builder把每个OpRunner的isDynamicShape硬编码为true，Executor.Run没有用传入isDynamic分流，故不能只传is_dynamic=False就宣称免除逐算子推形/工作区开销。

## 捕获窗口、缓存命中和分段限制

config.ascend.aclgraph.begin_capture先在pool_id为(-1,-1)时取torch.npu.graph_pool_handle，再设置全局InCapture标记；end_capture只清除标记，不代替FXRT_ENABLE_ACLGRAPH开关。KernelCaptureExecutor每次先等待launch任务下发，再按当前ShapeKey查缓存：命中直接重放，结束捕获窗口后仍可重放；未命中且InCapture为false时执行Pipeline.Run(true)，并非自动捕获新shape。

首次捕获会DeepCopy图并另建OpRunner，普通节点/输出与属性复制，Op_End终端节点及inputs/parameters仍共享；这不是冻结所有权重和输入的快照。默认useFullGraphMode为true；创建过额外capture stream但实际fullgraph捕获使用当前stream，以容纳custom call。分配前后回调接TorchNPU NPUCachingAllocator的beginAllocateToPool/endAllocateToPool，update stream另用于任务更新。

GraphCaptureManager拒绝设备类型与期望上下文不符、以及Launch后才更新输出shape的算子；只比较设备名称不能当作多卡ordinal一致性的完整校验。set_op_capture_skip按算子名忽略大小写做完整相等比较，skip算子在fullgraph中走可更新task group，不是任意Python/eager图断点。TorchCallOp/PythonCallOp在普通捕获段等待下发，但进入需要更新的single-op分支会明确报不支持；不能把custom call加skip列表当作通用修复。

piecewise的LaunchAllKernelsWithCapture函数体仅return true，没有实际捕获；私有useFullGraphMode分支的存在不等于可交付的分段能力。RecordGraphOutputKernelInfo、RecoverGraphOutputKernelInfo、UpdateFixAddressBeforeReplayGraph等仍为占位，CheckParameterNotChange固定返回true，IsNonFixedInputInReplay固定false；不能借这些函数名宣称自动校验权重、恢复输出地址或处理任意变化KV。

HasCapturedGraph仅检查shape键是否存在；CreateCaptureGraph已插入缓存后，捕获失败的bool返回值在executor调用处没有逐项判定，也没有展示完整回滚。源码路径不能当作失败后可安全重试/重放的保证。重放代码先ExecuteCaptureGraph，再在update stream更新各single-op task并记录event；该顺序不构成任意输入和当前次任务更新立即生效的证明，需用真实变化输入验证。

## 输入静态化的缓存键和边界

Python入口以id(executor)作为graph_key，根据example_value标记Parameter，并传非Parameter Tensor下标。C++每图缓存只初始化一次下标分区；参数和非Tensor直接更新，其他Tensor在捕获时clone，已有且dtype/device/size/stride一致则copy_，重放时只向原缓存copy_(non_blocking=True)。无ACLGraph时全部直接更新；未捕获过的尺寸键没有静态Tensor缓存时也直接更新，再由executor走前述miss路径。

BuildGraphInputShapeKey把选中Tensor的所有尺寸连续用“-”连接，**没有每Tensor边界、rank、dtype、stride、device、标量或Parameter身份**。例如两个Tensor尺寸(2,3)+(4,)与(2,)+(3,4)都会得到2-3-4；这只是静态代码推导的键碰撞示例，未做设备复现。仅“尺寸键命中”不证明结构、布局或参数一致。重放分支没有重复NeedRecreateStaticTensor的元数据检查，直接copy_也不能替代图合法性校验；改变参数对象/地址、非Tensor标量、输入分区或dtype/stride时应视为需重新建立合同和验证的变化，不把缓存命中当正确性结论。

GraphExecutor析构尽力调用clear_graph_input_static_cache(id(self))并吞掉清理异常；该函数只移除对应输入缓存，不能把它当成所有图、私有内存池和捕获资源的完整释放接口。

## 内存生命周期、view别名与输出复制

Builder先创建OpRunner，再把ref输出指向输入Storage，然后记录延迟更新点与Storage释放点：输入/参数Tensor在第一个有效consumer前Update；按Storage指针共享身份逆序寻找最后consumer；图输出Storage先保护，输入/参数终端拥有的Storage不安排内部释放。这样才能让view与别名共享生命周期，不应按节点个数独立释放每个Tensor。当前实现主要依据已建图的执行顺序，不能从这一分析推导任意并发和跨流生命周期都已验证。

OpRunner对TorchCallOp跳过内部输出分配；其他需分配的Storage若仍拥有数据则报Memory leak。ref元数据同步只有shape相同才复制stride和storageOffset；需要Launch且涉及特殊format会报错，shape不同的view路径须自身维护元数据。普通Executor的代码顺序为Update/InferShape/Allocate/CalcWorkspace/AllocateWorkspace/FreeMemory，再按NeedLaunch发射；捕获段则Launch后FreeMemory。这里只记录下发与释放调用顺序，分配器复用和异步依赖还须结合实际stream验证，不能从FreeMemory名字推导设备已同步。

mempool.h里另有MAX_MEM_SIZE=4GiB的旧MemoryPool及TensorDataRecycler；本轮审阅的BuildExecutor→Builder/OpRunner路径采用Storage和Allocator，并非由该常量限制模型大小。旧MemoryPool.Free也只是重置node.output，没有执行所存freeFunc；不能根据同名类和常量给出FXRT最大显存或释放策略。

Torch桥输入更新时使用已带偏移的data_ptr，将IR storageOffset设0，NPU记录真实format/stride/storageShape；剩余可访问字节为storage.nbytes-offsetBytes，非空时拒绝偏移达到/超过容量，零元素单独处理。不能用逻辑numel直接覆盖有padding或view偏移的物理存储范围。

to_torch仅接受base format输出。引用外部Storage的输出会复制；捕获/重放中的自有输出也复制Storage，普通自有输出则转移所有权并由PyTorch deleter接管。复制覆盖Storage大小，可能大于view逻辑元素数；view内部零拷贝并不意味着跨FXRT→Torch输出零拷贝或保持与原输入的Python别名关系。NPU走当前stream异步D2D，空Tensor另分配空/empty_strided形式。

## 桥接类型、私有接口和现有测试

当前FromTorchDType/ToTorchDType映射只列FP16、BF16、FP32、FP64、Complex64、INT8/16/32/64、UINT8和BOOL；不在表中的类型明确走Unsupported分支。不能由某个设备算子可处理低精度，就推导这个Torch桥已开放FP8/FP4输入。CPU和PrivateUse1为该设备转换表列出的入口。

私有_fxrt_torch.adopt_external_device_buffers以整数地址、context和回调跨ABI移交外部分配的NPU输出；它不由fxrt包公开导出，也不是量化/重排接口。只有context与free_fn均非零的分支建立拥有权，其余按非拥有包装；回调地址由调用方保证，失败清理按本地分支处理。注释的“恰好一次/全部或无”承诺不代替所有from_blob/包装失败路径的实际验证，本次没有调用此接口。

test_fxrt_basic仅一个MLP前向测试，Linear16→32→8、FP32默认输入(4,16)，模型eval与no_grad，同一输入调用编译结果两次并和eager比较；缺FXRT包时整类skip。文件没有设置FXRT_ENABLE_ACLGRAPH或捕获窗口，第二次cached compiled graph不等于ACLGraph重放测试。没有该机制的动态输入、捕获失败恢复、KV地址替换、数值分布或吞吐/显存证明，本次也没有执行测试。

后续验收须固定产品、TorchNPU/CANN与构建选项，分开检查Base/Pipeline/ACLGraph实际模式，记录捕获首轮与重放开销；用不同值及尺寸分区、stride、dtype、参数/KV变化验证键和地址前提，核对别名与输出复制，比较数值和峰值显存。未知产品维持草稿，不能把静态审阅和通过知识库检查记为verified。

## Pipeline的主机下发和重入等待

同一主线的PipelineBuilder先SetupOpRunners、Initialize，再用TorchNPU注册的launchOpFunc下发bind_device、每个需要Launch的算子和尾部launch_kernels_finish任务。推形、输出/工作区分配和释放调用仍在调用线程逐算子执行，不要把普通Pipeline与GroupLaunch首次记录阶段的独立infer_queue/launch_queue混为一谈。缺少launchOpFunc时报设备不支持该executor，没有在这里自动回落Base。

同一个executor用waitLastRunFinish标记限制前次下发尚未结束时重入：先自旋1000次，再条件变量等待最多1000ms，超时调用WaitLaunchTaskFinish并清标记。这个1000ms是主机重入等待阶段的阈值，不是设备kernel执行超时。尾部任务只表示相关下发队列任务推进，不能代替数值结果可见性、设备同步或任意多线程并发调用同一图的保证。

内部AsyncTaskQueue容量8192、多生产者/单消费者、默认暂停；满时自旋等待，暂停时Push失败，关闭后也不接受任务。Wait压入一个Wait任务，等待该主机任务被处理，不直接执行设备同步。worker捕获std::exception后保存第一个异常、丢弃已排队的非Wait任务，并执行Wait任务以释放等待方；WaitAll等路径再CheckException取出并清除后重抛。这不是失败任务重试或图执行事务回滚，不能把队列已空当成算子全部成功。运行队列空时也有自旋行为，线程CPU占用须与推理耗时分别评估。

## GroupLaunch的参数、分组和实际生效条件

被选中后，builder要求FXRT_KERNEL_LAUNCH_THREAD_NUM和FXRT_KERNEL_LAUNCH_GROUP_NUM均为不带前导0的十进制正整数字符串，不接受空、负数、空白或0。总组数必须至少线程数；parallelSliceNum采用整数除法，实际组数为thread_num×floor(group_num/thread_num)。例如线程3、组8实际分成6组，不是8组。再按OpRunner执行序连续切片，最后一组吸收余数；组数大于算子数时可出现空组，源码没有给出这个配置更快的证据。

builder发现CPU设备算子直接报错，不会自动混合执行。通信、异构输出和需force resize算子的串行分类仍是TODO，serialLaunchOps初始为空；尽管executor有串行event和main stream代码，不能据此认定这些算子已经被正确识别到串行路径。

RecordGraphInputs只记录graph.inputs及其中编译时HasDynamicShape的Tensor。每次更新输入后，只有这些动态输入的shape与上次一致且非空，CheckInputShapeChange才可能返回false。**动态输入列表为空时固定返回true，意味着静态图每次都重新记录，不能据“静态shape”推定走并行缓存。** 标量Tensor的空shape也触发重新记录；其他标量值、dtype、stride、参数和KV地址不在这项变化检查内。

shape变化分支先清旧trace、将部分输出/工作区指针置空，再用infer_queue做推形/CalcWorkspace、launch_queue分配输出并记录内存/Launch，等待两个主机队列后合并trace。shape不变分支分配合并缓存块及图输出、设置缓存指针，然后并行下发，完成event衔接后释放本次缓存块。这里缓存的是内存位置关系，**不是所有中间device地址跨次永久不变**；也不是ACLGraph执行图缓存。

## 内存trace、多流顺序与尚未闭合的路径

MemoryCache按device context、原地址排序合并重叠区间，记录每个kernel输出和workspace相对合并块的offset。相邻但不重叠的区间仍分成两块；每块重新分配size+1024字节，这个余量本身不代表显式执行了1024字节地址对齐。SpinLock只保护相应指针更新，不证明整个executor、全局stream资源或缓存变更都可任意并发使用。

每个dispatch线程使用自己的stream；相邻分组之间的events串联执行顺序，另用event把串行算子/main stream与尾部default stream衔接。主机可以并行下发，并不代表组间有依赖的设备kernel能无序并行或必然获得计算吞吐收益。streams/events/queues为静态容器，首次非空后不按新executor的线程数和设备重新创建，跨配置/多图场景仍需另行核验。

本提交存在会影响路径采用的静态不一致，均未做设备复现：

- RecordMemory的Tuple分支先CHECK_IF_FAIL(!value->IsTensor())，随后却调用ToTensor；按该宏“不为真即异常”的定义，常见Tensor tuple项会在该条件处失败，不能把普通多输出Tuple当作已闭合支持。
- workspace trace记录的index为0，而SetOutputAndWsCacheMemory的workspace分支要求index!=0，条件相反；有workspace的缓存路径不能仅据设计注释认定可用。
- 记录阶段只AllocateMemory输出，没有调用AllocateWorkspaceMemory；若CalcWorkspace给出正workspaceSize，RecordMemory仍尝试记录workspace地址，MemoryCache.AddKernelMemoryTraceBlock要求非空。除非具体算子另有有效指针来源，不能把这条路径当成通用workspace初始化方案。
- Tuple图输出和输入缓存都明确不支持嵌套Tuple；输出保护使用Tensor指针集合，而一般Builder生命周期分析使用Storage身份，view/别名的组合边界必须单独验证。

本文依据18份相关实现及common.h宏、环境解析的所列范围说明运行期行为，不据此声称设备验证。现有basic MLP没有设置GroupLaunch环境；参数合法、缓存键相同或存在多流代码均不能替代真实模式、非零workspace、多输出/别名、通信顺序、数值和性能验证。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/README_CN.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/README.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/__init__.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/fx_backend.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/executor.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/executor.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/mempool.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/mempool.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/op_runner.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/op_runner.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/kernel_capture/kernel_capture_executor.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/kernel_capture/kernel_capture_executor.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/kernel_capture/utils/graph_capture_manager.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/kernel_capture/utils/graph_capture_manager.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/config/ascend/aclgraph.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/config/device/ascend/aclgraph_conf.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/config/device/ascend/aclgraph_conf.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/pybind/fxrt/pybind_aclgraph_config.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/builder/kernel_capture/kernel_capture_builder.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/builder/kernel_capture/kernel_capture_builder.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/builder/builder.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/builder/builder.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/utils/utils.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/utils/utils.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ops/utils/async.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/pybind/fxrt_torch/pybind_torch.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/python/fxrt/ir.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ir/graph.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/ir/graph.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/test/fxrt/test_fxrt_basic.py)（example）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/pipeline/pipeline_executor.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/pipeline/pipeline_executor.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/builder/pipeline/pipeline_builder.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/builder/pipeline/pipeline_builder.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/pipeline/async_task_queue.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/pipeline/async_task_queue.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/pipeline/async_task_queue_manager.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/pipeline/async_task_queue_manager.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/pipeline/lock_free_ring_queue.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/kernel_launch_group/kernel_launch_group_executor.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/kernel_launch_group/kernel_launch_group_executor.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/builder/kernel_launch_group/kernel_launch_group_builder.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/builder/kernel_launch_group/kernel_launch_group_builder.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/kernel_launch_group/memory_cache/memory_cache.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/executor/kernel_launch_group/memory_cache/memory_cache.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/utils/exception.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/utils/exception.cpp)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/runtime/utils/spinlock.h)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/fxrt/fxrt/src/common/common.h)（implementation）
