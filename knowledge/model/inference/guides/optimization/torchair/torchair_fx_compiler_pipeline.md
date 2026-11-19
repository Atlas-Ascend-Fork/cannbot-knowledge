---
type: Guide
title: FX编译管线：优化次序、AOT与执行回退
description: 按固定快照解释TorchAir后端入口、FX改写、GE/ACL构图、AOT分阶段包装和代码工件回退的实际条件。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/custom_aot_functions.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/custom_aot_functions.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/run_eagerly.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/run_eagerly.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/data_dump_eager.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/data_dump_eager.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/debug_config.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/debug_config.py
  role: implementation
created_at: '2026-11-10T10:21:36Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# FX编译管线：优化次序、AOT与执行回退

## 固定版本与阅读入口

全文核对TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的npu_fx_compiler.py，以编译控制流为范围。产品矩阵未知，保持draft与空平台；未导入上游、运行FX/AOT、生成并执行代码、加载缓存或调用设备。

本卡用于判断优化开关实际走哪条路线、在哪个阶段构图，以及保存代码的能力边界；不替代具体算子的IR和kernel支持矩阵。结构化元数据版本差异见[ValuePack与容器](torchair_fx_value_pack_metadata.md)。

## 后端构造和AOT入口

get_npu_backend使用CompilerConfig或传入配置并检查支持条件；主线还初始化debug logging。默认decompositions先被调用方字典update，之后再执行add_npu_patch；所以不能把自定义字典概括为最终最高优先级。返回的是_npu_backend的partial，尚未完成某张模型图的编译。

_npu_backend先_process_send_recv，再处理kwargs选项、取得compiler，最后进入_compile_graph_with_aot，公共入口is_cache=False。主线还尝试安装确定性级别guard，ImportError只警告跳过；发布快照没有同一安装分支，不能由调用入口推导两版有相同guard。

_process_send_recv只识别精确的npu_define._send/_recv目标。CANN版本8.6检查失败在此记录ERROR而非raise；GE且此类节点数大于1时改为StableRDFS并设置warning过滤，其他模式不强制同一拓扑策略。这个局部条件不能推广成所有通信图均有顺序或无死锁保证。

## AOT分阶段包装、分区和缓存路径

编译闭包按阶段包装参数静态标记、输入自定义属性恢复及debug phase；backward有独立包装路线。GE跳过mark_static；其他模式在Torch版本满足条件时按AOT固定参数索引给Tensor写_torchair_is_parameter，越界/非Tensor只记debug，旧版本警告。写标记不等于已经证明零拷贝或复用收益。

输入dim_gears、_dynamo_static_input_type及Parameter身份先收集，索引以i-len(inputs)从末尾定位；编译阶段恢复再调用guard_gears_shape。主线_get_arg_pos_to_source收集参数、buffer与输入来源，并按AOT私有元数据函数签名适配full_args_descs；该输入来源映射只在导出路线设置，不能泛化成所有前后向参数都有命名映射。

正常AOT路线中joint_graph开关可提前进入aot_module_simplified_joint并带output_loss_index；否则构造forward、backward、inference compiler和分区函数，最终调用aot_module_simplified。分区配置启用npu_fx_pass时先joint_graph_passes再default_partition；关闭时直接默认分区。keep_inference_input_mutations取配置布尔值。

is_cache路径初始kwargs使用调用方bw_compiler或None、inference_compiler=None、default_partition及keep_inference_input_mutations=True，与普通路线不同。这里只审阅入口分支，不据此断言所有训练图缓存已被完整支持；调用方、工件兼容性和实际执行还需另证。

## FX优化顺序决定开关如何生效

核心顺序是自定义post_grad_custom_pre_pass、可选remove_noop_ops、recover_view_inplace；max-autotune模式另跑_optimize_sym_input；随后按配置应用pattern passes，再无条件把view.default改为reshape.default，最后自定义post_grad_custom_post_pass。不能把关掉某个pattern开关理解为全部图改写都关闭。

模块导入remove_noop_ops时临时将Inductor compile_threads置1，finally恢复原值，目的是避免导入时异步池warm up；不是持续改变整个编译线程数。导入失败则保留None并在使用处警告跳过。

_optimize_sym_input以placeholder.meta['val']辨别符号标量与FakeTensor维度，通过str(sym)==str(dim)匹配，插入aten.sym_size并替换原符号输入的uses，仍保留原placeholder，再lint/recompile。它不是任意符号代数等价化简，也不意味着输入签名已删除该参数。

_valid_graph对AIR scope按栈匹配，对superkernel名称作配对检查并允许不同嵌套次序；缺少成对标记或残留会抛错并提示graph break。通过这些标记检查不表示所有算子、shape和设备能力都已验证。

## 构图、Eager回退与两种后端

_get_compiled_gm在fx_summary.enabled、fx_summary.skip_compile均打开且max-autotune时返回Eager包装的原gm；配置data_dump时返回Eager dumper。其他模式可警告但不能据此认定走同一回退。主线lite模式在临时上下文中导入Lite Converter，发布版直接导入；持久注册与线程局部标志的区别见[注册生命周期](torchair_ge_registration_prims_lowering.md)。

_gen_compiled_gm在TorchNPU已导入且FX含npu_weight_quant_batchmatmul时直接把config.experimental_config.enable_view_optimize设False；此处没有自动恢复原配置。ACL original图dump阶段可能在常规构图前提前返回插入保存节点的图，不应把它当作正常优化完成。

之后在no_dispatch下deepcopy图并找mutated inputs：GE创建GeConcreteGraph，主线先prescan_and_compile_custom_ops并传参数来源；ACL创建AclConcreteGraph并带custom_pool和mutated inputs，未知模式ValueError。然后优化FX、验证标记、保存FX，运行_NpuGraphConverter构图（garbage_collect_values=False），可选dump，再optimize_graph_without_runtime。

debug.run_eagerly会输出警告及FX对比，但只有GE分支返回fx_graph；ACL继续具体图路线。不能把这一debug开关概括为所有模式都停止构图并运行Eager。名为without_runtime的优化步骤也不是整个编译入口从不涉及运行资源的保证。

## 首次调用、生成代码与保存工件

_CompiledFxGraph首次调用时初始化并缓存run_kernel：reduce-overhead/npugraph_ex尝试get_code，字符串经_compile_py_code编译为模块kernel，非字符串走可调用对象；有execution_kernel属性时再选该属性，其他模式使用runner。后续复用run_kernel不等于任意输入均无需guard或重编译。

get_code在没有codegen接口时警告并返回runner；codegen(...enable_cache=True)返回None也回退runner，否则可打印/转储代码。dump_artifacts要求runner.codegen，保存版本号0.1与代码；load_artifacts只显式检查该版本号，再编译代码并以config=None包装。0.1相同不能替代完整软件栈、硬件和输入合同兼容核验。

_compile_py_code通过ModuleType、compile和exec建立模块；这里只读源码，未调用该函数。TORCH_COMPILE_DEBUG=1时_dump_codegen以锁和0600权限写output_code.py并附main调用，主线使用缓存的debug path，发布版使用当时phase path；这只是转储位置差异，不是可移植、可信或完整复现实验的证明。graph_id为模块内递增计数，也不是跨进程唯一工件身份。

## 应用与验证

排查优化未生效时先核对精确快照、mode、summary/data_dump/debug开关、view优化配置是否被输入图改写、实际FX pass顺序、AOT阶段及codegen回退，再追具体后端。若需性能、确定性、分布式顺序、缓存复用或精度结论，须在匹配栈独立验证；本卡没有运行这些实验。

- [FX Pass与融合配置](torchair_fx_pass_and_fusion_controls.md)
- [GE元数据辅助与占位](torchair_ge_metadata_support_helpers.md)
- [通信图保留与进程组元数据](torchair_ge_collective_lowering.md)

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py)（implementation）

## 独立npugraph_ex的AOT消费者不能套用集成路线

本节补同一固定双版的独立npugraph_ex/npu_fx_compiler.py关键入口和AOT阶段；前文集成python/torchair管线的证据保持原样。这里只审所列函数，不把两个大模块的其余优化器、执行器或外部AOT实现提升为已覆盖。

独立get_npu_backend仍按默认decompositions→调用方update→add_npu_patch的顺序合并，再返回partial；主线另先_init_debug_logging。主线独立_npu_backend先尝试安装确定性级别guard，只有ImportError被警告跳过，安装调用本身抛错不在这个except处理；随后建默认配置、处理kwargs选项、处理send/recv、取得compiler，最后以is_cache=False进入AOT。发布对应入口没有这段安装代码。这是固定局部消费者，未证明任何安装组合的确定性或兼容性。

两版独立_process_send_recv仅在_send和_recv目标都存在且图中至少一个精确目标命中时检查CANN8.6.0；版本不满足只记ERROR，没有在此raise。它没有前文集成GE路线的StableRDFS改写，不能因为出现相同函数名就推定独立ACL图也被设置了该拓扑策略。

## 静态输入与自定义属性的恢复范围

独立_mark_static_inputs_attr满足源码版本门控后，用Dynamo/AOT输入数量计算fixed arguments，再取static input indices；只有索引小于AOT输入数且对应项为Tensor才写_torchair_is_parameter。它没有按GE模式提前返回的分支；也没有在这个属性赋值中证明免复制、跨流存活或参数地址可任意改变。

_get_inputs_custom_attr收集_dynamo_static_input_type和Parameter身份，位置记为i-len(example_inputs)的负索引；没有把所有已存在的_torchair_is_parameter属性或任意Tensor私有字段都复制一遍。_set_inputs_custom_attr直接按这些索引setattr，本函数没有额外索引边界校验。这个收集/恢复块也不包含集成路线中的dim_gears收集与guard_gears_shape调用，不能把注释“Gears等”补成已经实现的字段流程。

forward和inference经_create_stage_compiler组合：调用时先由debug phase包装进入，自定义属性恢复后再进_wrap_compiler做静态标记，最后调用底层compiler。正常路线的backward只用wrap_compiler_phase包同一compiler，没有走这个_create_stage_compiler链。不能把前向的属性恢复和静态标记无条件套到所有后向调用。

## 独立主线与发布的分区、mutation配置不同

两版_compile_graph_with_aot均先建立相同cache初始kwargs：forward阶段包装、调用者bw_compiler或None、inference_compiler=None、default_partition和keep_inference_input_mutations=True。is_cache=True就保留这些值；仅依据这个入口不能认证训练缓存支持。

| 所列独立正常路线 | 主线92e1e967 | 发布7c6c754 |
| --- | --- | --- |
| backward和inference | 替换为backward phase包装及独立inference阶段包装。 | 同样替换。 |
| partition_fn | 本函数继续保留初始default_partition，没有在这个正常分支按npu_fx_pass覆盖。 | 替换为_get_partition_fn；npu_fx_pass为真时，先调用本地_npu_joint_graph_passes再default_partition。 |
| keep_inference_input_mutations | 本函数继续保留True，没有在这个正常分支读取对应配置覆盖。 | 显式取experimental_config.keep_inference_input_mutations的bool值。 |
| inference的_wrap_compiler | 只做静态标记后调用compiler。 | npu_fx_pass为真时先做_npu_joint_graph_passes，再标记静态输入。 |

发布_npu_joint_graph_passes委托外部Inductor joint_graph_passes；这里没有把它的所有内部优化效果作为本组新事实。两版本地正常AOT块都没有实现注释“Joint Graph Strategy Early Return”所暗示的提前返回；最后直接调用aot_module_simplified，不应把集成管线的joint_graph开关路线迁移到这个注释上。外部AOT实际分区及其他调用者仍独立验收。

主线条件图递归替换流事件的已审消费者见[条件图流事件合同](npugraph_ex_cond_stream_event_closure_and_scope_keys.md)；本节不重复扩其资格。以上差异用于定位同名配置为何在不同包/版本没有相同行为，没有执行AOT、属性写入、分区、通信、梯度或设备实验，也没有新增verified。

## 有界独立AOT源码证据

- [固定入口 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：825–996、1009–1081；仅所列独立包函数，不提升整个编译器、集成包或外部AOT/Pass实现资格。
- [固定入口 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/npu_fx_compiler.py)（implementation）：695–942；仅所列独立包函数，不提升整个编译器、集成包或外部AOT/Pass实现资格。

## joint AOT包装器的实际状态回写

两固定版 `_utils/custom_aot_functions.py` 的joint helper负责把联合前后向图的输出写回参数、buffer和用户输入。它在普通AOT入口之外有自己的运行协议；本节静态核对完整本地模块，未导出图或执行编译。

| 阶段 | 实际行为 | 使用时核对 |
| --- | --- | --- |
| 参数/buffer | named_parameters与named_buffers均remove_duplicate=False，再按名字合并、pytree展平并捕获tuple | 后续forward复用这些对象引用，不每步重查模型；不是权重数据深拷贝 |
| 联合导出 | aot_export_module(trace_joint=True, output_loss_index=...) | helper虽然接收decompositions形参，这次调用没有传它，也没有在其余函数体消费 |
| 输出分组 | 先按buffers_to_mutate数量划出回写区，再取user_outputs数量，余下作为梯度区 | 只比较梯度数量与图输出数量，并非逐名/shape校验所有输出 |
| buffer回写映射 | 用range(num_mutated_inputs)与参数之后的buffer输入位置zip | 不在此按signature.buffers_to_mutate中的具体buffer名字重新查找；不是任意部分buffer变更都已逐名映射的证明 |
| 运行 | compiler先接FX图和full_args，必要时make_boxed_func；运行时将输出赋给buffer.data、参数.grad或用户输入.grad | grad是直接赋值，未在这里做已有grad累加；多项赋值失败没有整组回滚 |

梯度索引先覆盖params_and_buffers_flat中requires_grad为真的项，再覆盖展平用户args中requires_grad项；代码直接访问该属性，没有为任意Python标量逐项加类型保护。计算梯度映射时展平用户args，但compiler和forward的full_args只把原args/runtime_args外层extend进去，不能据此认定任意嵌套输入结构都采用同一展平协议。

disable_amp在构造包装器时读取一次当前autocast状态，随后透传给外部call_func_with_args；这是传入标志的时点，不替代外部运行helper的完整AMP合同。forward返回用户输出位置组成的list，并附上mod.zero_grad/named_parameters/named_buffers便捷属性，不是完整nn.Module接口复刻。

私有call_func与_graph_output_names导入只在ImportError时切换备用路径。注释列举减少pytree、参数读取与AOT缓存开销的目标，不是本次性能测量；调优时记录实际输入结构、buffer写回、梯度覆盖与额外对象分配。

## 实现来源

- [固定实现1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/custom_aot_functions.py)：1–124。
- [固定实现2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/custom_aot_functions.py)：1–124。
- [固定实现3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)：44–44、1136–1147。
- [固定实现4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/npu_fx_compiler.py)：50–50、973–983。
## run_eagerly 与 data_dump_eager 同句约束的实现分野

`ascend_ir/features/basic/run_eagerly.md` 与 `data_dump_eager.md` 两页使用同一句使用约束「开启该功能后，GE图模式相关的功能配置均不生效」（两页各自的第 9 行；run_eagerly.md 两 pin 字节一致，data_dump_eager.md 两版仅转义与行尾空白差异），两处实现的兑现位置和程度不同：

- data_dump：`_get_compiled_gm` 在进入 `_gen_compiled_gm` 前直接返回 dumper 包装（主线 707–716/发布 625–631），后端构造、FX 优化、转换与无运行时优化整体跳过——约束完整兑现；更早的 fx_summary 分支（主线 696–705/发布 615–623）可再提前。
- run_eagerly 的编译期检查位于 `_gen_compiled_gm` 尾部（主线 791–800/发布 690–697）：GeConcreteGraph/AclConcreteGraph 构造、`_optimize_fx`（主线 776/发布 677）、`graph.save_fx_graph`（778/679）、`_NpuGraphConverter` 转换（780–782/681–682）与 `optimize_graph_without_runtime`（789/688）都已执行之后，仅 max-autotune 返回 `graph.fx_graph` 替换最终 GE 编译执行；reduce-overhead/npugraph_ex 在编译返回层仍返回 concrete_graph（前文既有结论）。
- 回退对象的身份：`graph.fx_graph` 即 `save_fx_graph(optimized_gm)` 保存的 `_optimize_fx` 后 FX 图（fx2ge_converter.py 主线 1878–1882、发布 1490–1494：属性直接返回 `_fx_graph`，`save_fx_graph` 原样存储传入模块）。GE 分支的 Eager 对照发生在 FX 优化改写之后（pattern passes、view→reshape 等），不是绕过全部图变换的原始基线。
- 硬门槛：`graph.fx_graph` 为空时直接 `raise RuntimeError('When using debug.run_eagerly=True, the FX graph should not be None.')`（主线 797–798/发布 694–695）——开启 run_eagerly 不保证回退成功。
- ACL 模式的兑现发生在运行时而非编译返回层：`_DebugConfig.as_dict` 把 `run_eagerly` 写入选项字典（debug_config.py 主线 116–119/发布 115–118；`OptionValue.value` 把 True 读作字符串 "1"），经 fx2acl 序列化进入 aclgraph 选项后由 `AclGraph.__call__` 首查——命中即跳过 capture/replay 走 `fx_run_eagerly`、叠加静态算子缓存时先 `run_eagerly_compile`。该 ACL 运行时行为（含 `'1'` 精确比较）已由[集成 ACL 图 IO 与重捕获](torchair_integrated_aclgraph_io_recapture_and_output_clone.md)承载，本节只补它与这句文档承诺的连接。
- 边界：该句约束对 run_eagerly 的兑现是「跳过图模式执行」，不是「图模式相关配置不参与」——两分支的转换期仍受配置影响（如 npu_weight_quant_batchmatmul 触发的 enable_view_optimize 改写）；data_dump_eager 页同句约束才是编译流程整体跳过。两版行为同构，无版本边界。

## 来源与复核范围

- [新增来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/run_eagerly.md)（constraint）：1–27 全文读取（使用约束 9、参数表 23–27）。
- [新增来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/run_eagerly.md)（constraint）：与主线 diff 字节一致。
- [新增来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/features/basic/data_dump_eager.md)（constraint）：1–60 全文读取（使用约束 9；参数与产物的逐项配对由[FX Eager数据Dump](../torch_npu/torchair_fx_eager_dump_execution_and_coverage.md)承载）。
- [新增来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/features/basic/data_dump_eager.md)（constraint）：与主线仅 37/45/47/54 行转义与行尾空白差异。
- [新增来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：窗口 1878–1882（`fx_graph` 属性 1878–1879、`save_fx_graph` 1881–1882）。
- [新增来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/fx2ge_converter.py)（implementation）：窗口 1490–1494（同构）。
- [新增来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/debug_config.py)（implementation）：窗口 108–119（`_DebugConfig` 110 起、`as_dict` 116–119）；`OptionValue.value` 的 "1"/"0" 读取语义由配置卡既有结论承载。
- [新增来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/configs/debug_config.py)（implementation）：窗口 108–118（run_eagerly 110、as_dict 115–118；发布 `_DebugConfig` 无 deadlock_check 项，主线有，与本节无关）。
- 本卡既有 npu_fx_compiler.py 两 pin 来源补读窗口：主线 690–716、760–802（分支序 fx_summary 696–705 → data_dump 707–716 → `_gen_compiled_gm` 内 776/778/780–782/789 → run_eagerly 791–800）；发布 609–631、676–699（对应 615–623/625–631、677/679/681–682/688、690–697）。跨卡复核阅读（ACL 运行时消费端，锚点登记在[集成 ACL 图 IO 与重捕获]卡来源内，不在本卡重复）：debug_config `as_dict` 值经 fx2acl_converter.py 主线 375 调用消费、run_eagerly=='1' 分支主线 401/发布 366，AclGraph `__call__` 主线 926–929/发布 824–827（全树 rg + 窗口实读核对）。全部为静态读取，未 import/运行上游。
