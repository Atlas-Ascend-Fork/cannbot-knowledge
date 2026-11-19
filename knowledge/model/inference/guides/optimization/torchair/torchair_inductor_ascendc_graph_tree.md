---
type: Guide
title: Inductor AscendC 图下沉：Tree、静态地址、代际与输出寿命
description: 解释Inductor分区到NPUGraph Tree的复用边界，并核对设计与独立固定PyTorch源码的差异。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/inductor_af_graph_sinking_summary.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/inductor_af_graph_sinking_summary_en.md
  role: constraint
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_graph_tree.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_graph_tree_state.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/NPUGeneratorImpl.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_graph_tree.py
  role: implementation
created_at: '2026-11-09T18:28:49Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Inductor AscendC 图下沉：Tree、静态地址、代际与输出寿命

## 固定设计与独立实现身份

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c双语图下沉设计，并局部对照PyTorch独立主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf。两快照没有配套证明；下列源码差异是版本核对结果，不是推荐把两主线装在一起。整套实验功能硬件未闭合，故draft/空platforms，未捕获、重放或运行模型。

## 入口、分区和Tree

设计使用Inductor+npu_backend=ascendc+triton.cudagraphs=True，与TorchAir旧GE reduce-overhead和独立npugraph_ex区分。AscendC加载路径避免套用若干Triton专属patch；should_partition临时修改GPU_TYPES再恢复只是局部门控，不是线程安全或任意CPU操作可捕获的证明。

Dynamo产生的GraphModule、Inductor分区、NPUGraph节点是三个层次。CPU标量、device copy、条件或动态结构等可使某些分区保留inline/eager；一次torch.compile不保证全模型成为一个NPUGraph。编译先生成分区函数和Runner，运行时惰性完成warmup、record及replay；分支、形状、静态指针和liveness变化可产生新节点，不保证模型永远只热身一次。

Tree用共享pool、root/child路径和输出弱引用管理多个捕获节点。Warmup节点执行Eager，Record建立图，Replay复用；新分支前需恢复对应allocator checkpoint。来源的“分支占用近似最大分支”解释复用意图，不是任意保留输出、并发或分配器下总内存恒等于最大分支。

## 三类输入与地址合同

普通非静态输入在capture分配pool buffer，replay前把新数据批量拷贝到该地址；静态参数/Buffer或显式标记的输入可直接引用原地址，祖先图管理的输出也可沿pool地址传递。Python变量不重新分配、偶然同data_ptr或相同shape都不自动把普通输入变为静态。

设计把“静态输入内容不可变”说得过强。对照固定PyTorch _graph_tree.py，静态检查比较data_ptr；非静态输入走_foreach_copy_，重叠布局另有存储拷贝路径。**固定地址不等于数据内容必须恒定**：原地址上正确保序的原地更新与替换Tensor/存储不同，后者可能触发重录或不变量失败；修改常量假设、依赖或别名仍需另核。不能以地址检查代替数学或并发正确性。

ForeachCopy是普通输入进入捕获buffer的潜在成本，静态标记只在真实地址/生命周期契约成立时考虑，不以减去一次拷贝为由强行标记。固定PyTorch还将不透明自定义对象排除tensor-copy及指针检查，与Tensor静态性分别处理。

## Generation与逻辑迭代

设计一处称每调用增加generation，案例又归因新编译，不能把两句合成通用计数规则。固定PyTorch读取非零MarkStepBox负计数，否则读取Dynamo GenerationTracker.generation；这里没有读取上游Dynamo的增量实现，不断言“每次模型调用”或“每次编译”必增。

torch.compiler.npugraph_mark_step_begin用于标记真实逻辑迭代边界；同一轮多个compiled函数有依赖时按整个逻辑轮次安排，不能给每个相连子图盲目插标记。需要跨代持有的输出应在失效/复用前clone到独立存储，并核对后续消费；已经被覆盖后再clone无法恢复旧值。仅在程序开始调用一次也不能标识以后每轮新迭代。

对照源码的manager字典位于threading.local并按device索引，另有进程级capture锁；不把设计“同设备共享”泛化为全部Python线程无条件同一manager。固定PyTorch还存在代际输出克隆配置和pending backward条件，本文只引用所读局部，不穷举整个Tree实现或覆盖训练生命周期。

## 图内更新、随机状态与观测边界

设计用handler、capture dispatch、update plan连接FA等更新；算子有handler、在本环境实际注册、被计划识别、capture成功和replay更新是不同层。文中6类预留/4类可用是当时环境描述，不证明当前固定PyTorch与TorchAir配套支持全部组合。事件用于约束更新与重放次序，不能为减少开销直接删除。

设计描述特定defer条件（auto_dispatch_capture、有plan且非launch-blocking）下重放后更新；独立固定PyTorch Node.run局部则先resolve/update、copy再run_graph，之后让update_stream等待当前流。两版本的时序分别记录，不能拼成同一条已验证流程。

设计称RNG Fill只在capture前且replay产生相同随机序列；固定PyTorch NPUGeneratorImpl.cpp已经按capture_id管理状态，setup_for_replay填seed和offset，replay_prologue在非零wholegraph_increment时推进全局offset。因而不能把“仅capture一次Fill”或“每轮相同随机数”写成当前主线保证；随机流可重放的状态管理与每轮数值完全相同是不同目标。

Kimi K3/DSpark场景中来源记录保留hidden跨compiled函数触发代际问题，13次调用计数、4.48/4.17ms及1.91x/1.64x仅是该环境观测，没有本地或配套硬件复测，不作为收益预测。--check的固定输入/少轮次与阈值也不覆盖全部业务shape、分支或训练。日志aclgraph/npugraph拼写按实际注册项核对，不擅自作为别名；保存Tree状态、地址、输出寿命与时间线共同定位。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/inductor_af_graph_sinking_summary.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/experimental/_inductor_npu_ext/docs/design/inductor_af_graph_sinking_summary_en.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_graph_tree.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_graph_tree_state.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/csrc/aten/NPUGeneratorImpl.cpp)（implementation）

## 真实输入staging：初始化同步、残余重叠与指针检查

补读固定PyTorch主线ac0e1564与发布f3ecfe4a的完整输入申请、复制与replay方法，以及相关局部字段/不变量分支；不展开整个Tree捕获、manager选择或外部Storage helper。本段补前述总览中的输入成本，两快照独立描述。

两版_allocate_and_copy_recording_inputs都先torch.npu.synchronize，再让录制流wait_stream当前流，在指定device与已有私有pool上下文内准备输入：非静态Tensor调用上游static_input申请；静态Tensor沿用原对象，随后调用本地批复制。主线非Tensor允许int、Generator或CustomClassBase，发布只允许int；这不等于本地接受任意Python对象。构造器接着clear传入inputs容器，因此这个内部入口会消费并修改调用方传入的容器。

| replay复制阶段 | 主线 | 发布 |
| --- | --- | --- |
| 选择 | 仅non_static_input_idx中的Tensor；先按expanded_dims索引dst，普通foreach路径再索引src，残余重叠委托使用原dst/src | 相同基本选择 |
| 索引后dst仍有内部重叠 | _debug_has_internal_overlap结果非0时，委托上游copy_strided_storage_，并清该src槽 | 没有这条单独委托路径 |
| 其他Tensor | 收入两列表，先将src槽设为None，最后非空时_foreach_copy_ | 直接收入列表并清src槽，再_foreach_copy_ |

这组复制先修改源容器，再执行最终foreach；复制若抛错没有本地事务回滚。主线Storage helper的实现未在这里展开，不能只按注释把任意布局的字节范围、padding或别名都判为已证明正确。expanded维度如何索引及static_input的具体分配由上游helper负责，本组仅确认真实调用，不补造零拷贝保证。

主线将is_custom_class_obj判中的opaque索引加入static_input_idxs，以免进入Tensor复制；非管理静态指针列表排除它们，另以tensor_static_input_idxs组织Tensor指针检查。静态指针快照只对相应Tensor取data_ptr，其他位置为None。发布没有同一opaque补充，主要合并用户静态索引与Tree管理输入。

### 主线默认走重录判据，不能把旁边旧注释当当前开关

主线构造器把rerecord_if_static_inputs_change直接设True；发布取inline_inbuilt_nn_modules或cudagraph_support_input_mutation。check_static_inputs_are_stable仅当此标志为False才比较非管理静态指针并抛错。另一个已读不变量分支在标志为True且指针不同的时候返回StaticInputIdxMismatch：主线用tensor_static_input_idxs，发布用static_input_idxs。它提供“不匹配”结果，不能单独证明外层一定成功重录或任意地址变化都安全。

两版run_first_inputs直接取recording_outputs、清该字段并返回，要求传入输入容器已空；它不是每次再启动完整replay。普通run先检查静态稳定性、复制输入、run_graph、重建输出并清new_inputs，按fast_path_cudagraph_asserts作后检查，按force_cudagraph_sync额外全NPU同步，最后复位static_inputs_stable。主线还在复制前提交已纳管的ACLGraph更新，并在提交成功时于replay后让update_stream等待当前流；发布所读run没有这段更新交接。更新helper与输出重建沿前文及训练生命周期卡，本次不重新扩张资格。

因此“命中图”仍可能有输入复制和可配置全同步，首次输入申请又有单独同步/pool准备。应同时观察有效静态索引、指针变化、残余重叠、输入容器所有权与同步开关，而不只计NPUGraph.replay耗时；未执行捕获、复制或设备实验。

## 固定实现来源

- [_graph_tree.py ac0e156](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/npu/_graph_tree.py)（implementation）：102–102、982–982、1017–1102、1129–1132、1215–1326、1932–1966、2016–2035。
- [_graph_tree.py f3ecfe4](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/npu/_graph_tree.py)（implementation）：776–779、814–884、911–914、992–1079、1634–1666、1708–1722。
