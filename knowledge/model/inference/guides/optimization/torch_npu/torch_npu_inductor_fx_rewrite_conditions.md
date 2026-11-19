---
type: Guide
title: 950DT Inductor图改写：GEMM、转置与切片合并
description: 记录四个默认关闭的POST Pass、形态匹配、规模阈值和数值差异。
tags:
- task.implementation
- topic.graph_execution
status: stable
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/TORCHINDUCTOR_ENABLE_FUSED_MATMUL_RELU.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/TORCHINDUCTOR_ENABLE_GRAD_MATMUL_TRANSPOSE_OPT.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/TORCHINDUCTOR_ENABLE_GROUPED_MATMUL_FUSION.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/TORCHINDUCTOR_ENABLE_MULTI_SLICE_CONCAT.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/overview.md
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/ascend_custom_passes/ascend_graph_pass.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/fx_passes/ascend_custom_passes/ascend_graph_pass.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/utils/check_op_util.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/fx_passes/utils/check_op_util.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/utils/get_binary_fold_result.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/_inductor/fx_passes/utils/get_binary_fold_result.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/fx_passes/utils/symbolic_shape_util.py
  role: implementation
created_at: '2026-11-09T15:10:31Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- '950'
---

# 950DT Inductor图改写：GEMM、转置与切片合并

## 固定来源与共同开关

依据TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的四份内部特性页，各自仅列950DT，不扩大950PR或A2/A3，也不回推26.0/PyTorch2.8。仅静态审阅，未运行改写、编译或设备实验。**固定源码对照：四份特性文档与四个Pass均为主线独有，发布pin（f3ecfe4a/TorchNPU 26.0.0）无docs/feature/graph_optimization目录、ascend_graph_pass.py（668行）亦无这四个Pass——本卡全部Pass结论不可外推发布版，分节见「两版差异边界」**。

下列环境变量默认未配即关闭，大小写不敏感的1/true/yes/on/y启用，其余关闭。四个Pass都在POST、FxPassLevel.LEVEL1注册，使能后仍可由SHUT_DOWN_FX_PASS_LIST关闭。DEBUG注册日志可帮助确认是否注册，不证明图匹配、实际替换或性能已改善；未启用不注册、推理/训练都不执行对应Pass，而反向转置Pass的实际用途限训练。

| 环境变量后缀（前缀TORCHINDUCTOR_ENABLE_） | 注册函数 | 改写 |
| --- | --- | --- |
| FUSED_MATMUL_RELU | fused_matmul_relu_pass | 把matmul与ReLU融合到npu_fused_matmul |
| GRAD_MATMUL_TRANSPOSE_OPT | grad_matmul_transpose_opt_pass | 反向输出permute(mm(lhs,rhs),[1,0])变为mm(rhs.T,lhs.T) |
| GROUPED_MATMUL_FUSION | grouped_matmul_fusion_pass | 同一cat之前独立小GEMM合为npu_grouped_matmul |
| MULTI_SLICE_CONCAT | multi_slice_concat_pass | 固定宽度、常量偏移的列切片cat改为npu_ext::multi_slice_concat |

## Matmul与ReLU的严格形态

支持relu(addmm)、两层view包住的relu/addmm、relu(mm+bias)及无bias的relu(mm)。AOT拆出的三维linear可落入view形态，但实际matmul输入与权重仍必须二维、rank相同且不广播；所有输入dtype一致且仅FP16/BF16。有bias时为一维连续，替换节点须单用户。不满足保持原图，不能因外层原始linear三维就扩大实际Kernel输入rank。

POST阶段addmm权重已是(K,N)，直接对应算子x2，无需另插transpose/reshape；无bias仍保持None。融合对应aclnnFusedMatmul的relu类型，减少独立pointwise下发和中间结果搬运，不是公开算子完整参数手册或收益测量。

## 反向转置与独立GEMM合并

转置优化只匹配反向图直接作为输出的permute(mm(...),[1,0])，当前只处理方阵输出，保持M/N/K以约束改变操作数的性能风险；不改写任意中间transpose或非方阵。

分组融合保持各GEMM操作数，但grouped累加方式不同，结果接近而非逐位一致。少于8分支的cat不合并；单次最多32组，更多组分成多次调用；行数4096上限只在行数静态时检查，不能把动态batch当作已受同一静态阈值保护。来源记录宽GEMM合并约慢12%、超过32组后每组2.18到6.90微秒等实测背景，解释其启发式，不作为本地测量或通用预测。

## 切片合并的容量与Lowering

切片cat路线通过一次固定宽度搬运减少原aclnnCat要求连续导致的Slice拷贝及带mask切片的where。开关同时控制对应Inductor lowering注册；不满足严格形态回到aten.cat。来源文档列每串切片≤64、不同源Tensor≤32、跨段同时活跃行mask≤4；这些文档数字不能直接代替同提交源码Pass的默认参数、连续run切分和实际Lowering边界，具体差异见后文。

该Pass仅数据搬移，来源称不改数值；这不等于其他GEMM改写也逐位一致。逐项保存实际FX形态、注册与替换记录、dtype/shape、数值及关闭调试后的稳态耗时，开启变量本身不证明命中。

## 默认开启清单不等于每个Pass都已匹配

内部图优化概述以pad_slice_fold消除常量pad后只取原范围的slice为例；这类推理改写与本卡四个显式开关分开。带ignore_inference_check的训练例外、默认关闭集合及dtype_optimal阶段冲突见[注册与资源指南](torch_npu_inductor_compile_resources_and_passes.md)，不把全部PRE/POST列表都当作训练路径已支持。

## 增补：Pass工具面的检查与折叠实现

同一主线提交下补齐fx_passes/utils三个工具（P2对账批次，静态阅读，未运行）。`check_op_util.py`维护两组op集合：`DTYPE_INSENSITIVE_OPS`（unsqueeze/squeeze/expand/permute/view/reshape/slice/select/cat/split/gt.Scalar/lt.Scalar/logical_not等纯布局或比较op）与`CAST_OPS`（npu._npu_dtype_cast、aten.to.dtype、prims.convert_element_type），并按schema规范化（normalize_function/normalize_module）检查cat的dim等参数——供改写Pass判断"该op是否对dtype敏感、是否已有显式cast"的公共依据。`get_binary_fold_result.py`在FX节点meta（val/tensor_meta/example_value）之上做二元常量折叠：经`symbolic_shape_util`的has_free_symbols/materialize_shape/statically_known_eq/geq/gt判断形状可静态比较后折叠二元运算，MAX_INT64为上界哨兵；折叠只消费FX元数据，不触发真实Tensor计算。`symbolic_shape_util.py`提供free symbol检测、shape物化与静态已知比较（statically_known_*）的基础谓词。三者是本卡各改写Pass与[编译资源与Pass定界](torch_npu_inductor_compile_resources_and_passes.md)所述pass框架的共享工具；工具存在不扩大任何Pass的匹配条件，本增补不新增verified。**两版工具面差异见「两版差异边界」——symbolic形状折叠为主线独有**。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/TORCHINDUCTOR_ENABLE_FUSED_MATMUL_RELU.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/TORCHINDUCTOR_ENABLE_GRAD_MATMUL_TRANSPOSE_OPT.md)（primary）
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/TORCHINDUCTOR_ENABLE_GROUPED_MATMUL_FUSION.md)（primary）
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/TORCHINDUCTOR_ENABLE_MULTI_SLICE_CONCAT.md)（primary）

- [增补固定来源](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/docs/feature/graph_optimization/overview.md)（primary）

## 主线GEMM融合的实参、别名与延迟缓存

以下只补固定ac0e1564主线ascend_graph_pass.py的所列重点范围，没有逐项摄取该4387行文件的其它fold/embedding实现，也不推回发布或扩大文档950DT产品表。完整注册与推理/训练调用规则见[编译资源与Pass定界](torch_npu_inductor_compile_resources_and_passes.md)。

融合算子解析用lru_cache(maxsize=1)，主线is_ascend950为假或npu_fused_matmul.default缺失时返回None；缺失结果也会缓存，不是每次Pass调用重新发现新注册。匹配只认aten.addmm.default、mm.default、add.Tensor与relu.default。addmm要求3个位置实参且alpha/beta为1；mm要求2个位置实参；mm+bias可交换两侧，但alpha须1，内部mm单用户且2位置实参。

mm到add之间只要发现任意被判为写的call_function就拒绝，不做这一步的精确别名消歧。判写包括triton_kernel_wrapper前缀、名字末尾下划线、Schema写别名；Schema读取异常按写处理，遍历不能确认先后也拒绝。它是保守图内窗口检查，不等于完整运行时别名验证。

元数据按val/example_value/tensor_meta顺序取首个带dtype/shape的对象；FP16/BF16同dtype、二维输入以及一维同dtype且可证明连续的bias是本地显式条件，bias连续性不确定即拒绝。它不另外逐项校验所有K/N、device和bias长度，只能在可信原图合同下使用。可剥一层单用户view，融合节点插在被替换的mm/addmm/add前，bias与fused_op_type用kwargs，复用旧Meta，再删relu/执行公共收尾；不是把权重重排成另一布局。

## 分组GEMM的bucket不只看分支数量

grouped_matmul_fusion只处理二维输出且列拼接dim=1的cat。候选只认无kwargs的mm/addmm（即使显式alpha=1的kwargs也会拒绝）、只被这个cat消费，重复输入Node去重。各x/weight/输出均二维，K、M、N和存在的bias长度用静态相等检查，同dtype；bucket键为rows和N的字符串、dtype及是否有bias，字符串相同还要重新证明输出shape静态相等。不同组K可以不同，不是要求全部权重等形。

达到每bucket min_groups=8后，按最多32组估算调用数，再均匀分配batch，避免短尾；80组示例得到27/27/26，而非32/32/16。这里的14%来自源码注释的背景测量，不是本地性能结果或通用预测。max_rows=4096只拒绝可静态判断的过大行数，SymInt行数不受这条数值上限完整保护。

每次发射group_type=-1、split_item=0，保留bias列表并取原节点meta['val']作为各getitem输出Meta；各成员原位置替换，不改变cat中的其他输入顺序，成员无需相邻。动态符号无法静态证明时不强配bucket；函数没有在此为所有Meta缺项或中途失败提供事务恢复。分组算子解析同样缓存缺失None。

## 反向转置依赖输出stride合同

grad_matmul_transpose_opt需要唯一output、user_visible_output_idxs和original_output_strides元数据且长度匹配，以及可取得FakeMode。仅改可见输出中的二维permute(mm(...),[1,0])，permute和mm各单用户，mm左操作数本身也必须是二维permute。lhs/rhs/result的val须二维NPU Tensor，结果dtype限FP16/BF16/FP32，输出静态方阵，lhs原始底层输入与rhs连续，而旧转置结果不连续。

源码先在FakeMode尝试rhs.T@lhs.T，异常时跳过；成功可抵消已有二维转置，再建立新mm并更新匹配输出位置的original_output_strides，然后删旧permute/mm。它有意放宽匹配输出的stride约束，不是只做代数替换而保持所有旧stride元数据。重复输出位置分别更新，不改任意中间transpose；没有在本组执行FakeMode或梯度实验。

## SliceCat源码参数与文档阈值分开核对

同提交multi_slice_concat_pass的函数默认max_segments=128、max_sources=32、max_masks=4、aclnn_copy_free_inputs=32；前述来源文档的64仍保留为文档声明，不能单用128宣称底层Kernel接受所有128段组合。列cat的输入数≤32直接保留原cat，行cat没有这条总数gate，但要求各输入二维且rows静态相等，run内width相同。

普通segment要求placeholder源二维、dtype与cat一致、rows相等、最后宽度静态。列slice以普通整数边界规范化（bool拒绝），负数按limit偏移并截断到范围，正宽度须匹配自身Meta；位置step只接None/1，这条函数没有同样读取任意kwargs step的完整防御。row mask必须可追溯为[rows,1] BOOL，沿view/reshape/expand/clone最多检查5轮；只接where(mask, 同dtype零full, slice)的清零形态。

支持dtype的本地白名单包含FP16/BF16/FP32/FP64、UINT8、INT8/16/32/64、BOOL，排除打包亚字节和复数。它不代表所有后端产品都支持这些类型。相邻可识别segment组成run，遇不支持项或源/mask/段数上限就结束当前run并开启下一段，不是只要总数超限整图都保持原样；只有至少2段且静态copy_cost之和≥2才值得折叠，完整连续源cost=0，部分切片或mask切片cost=1，这只是启发式成本。

构造器取源和mask的val，在源FakeMode内调用本地参考进行plan检查，异常跳过，再发射npu_ext::multi_slice_concat；参考检查数组长度、源索引、二维、正width/非负offset、静态越界和mask索引/二维列宽，不能扩写成对任意动态shape及所有设备的完整校验。run从后向前替换以保顺序，剩余cat保持或只剩一项时消去。它不在本组实现设备Kernel或其额外容量限制。

## pointwise下沉的数值保护

sink_pointwise_cat只合至少3个相邻、唯一出现且单用户、同源列slice上相同链的分支；仅cast的链留给SliceCat，最多最终一次舍入cast，FP16/BF16升FP32不计舍入。支持convert、clamp/min/max、abs、neg、add、mul及where的数据侧，数据dtype限FP16/BF16/FP32。零阈值clamp直接排除，源码注释说明其NPU signed-zero等价尚未通过，不把它写成已验收。

其他Tensor参数在拼接维必须广播不变，shape静态等价；FakeMode中的cat和目标pointwise成功才改图，捕获KeyError/RuntimeError/TypeError后跳过。通过pending列表继续处理内部链，不引入stack/split。这些守卫说明“减少下发”成立的局部形态，不能由开关启用推定任意逐点链都已移动或数值逐位相同。

## 两版差异边界（发布f3ecfe4a对照，静态diff）

固定源码对照：

- **ascend_graph_pass.py（主线4387行→发布668行；U0实测100 hunks、+136/−3855）**：发布版仅含4个注册Pass——`cat_slice_cat_fold_pass`、`fold_four_op_pass`、`fusion_attention_v3_pass`、`view_fold_pass`（另含fold_*助手与局部`match`辅助函数）；本卡四表Pass（fused_matmul_relu_pass/grouped_matmul_fusion_pass/multi_slice_concat_pass/grad_matmul_transpose_opt_pass）、sink_pointwise_cat、`_GmmMember`及全部`_FMM_/_GMM_/_MSC_/_IOTA_`常量（共117个顶层符号）均**主线独有**；发布pin无`docs/feature/graph_optimization`目录（四份特性文档亦主线独有）。**本卡Pass全部结论限定主线；发布版4个通用fold Pass的18处fold_*体差异未逐项闭合，引用发布行为以其文件为准。**
- **check_op_util.py（270行→220行）**：`DTYPE_INSENSITIVE_OPS`/`CAST_OPS`两版都在（集合体差异）；发布缺`is_single_user`/`match`/`normalize_dim`助手。`check_cat_op`发布版只读位置实参（单参回`True,0`、否则`True,node.args[1]`），主线kwargs优先（`node.kwargs["dim"]`→`args[1]`→默认0）——本卡「按schema规范化…检查cat的dim等参数」的kwargs兼容路径为主线行为；发布版`cat(dim=…)`形态经该助手取不到dim。24公共符号21个AST一致，5符号体差异。
- **get_binary_fold_result.py（322行→242行）**：`MAX_INT64`哨兵两版都在；折叠引擎分叉——主线经`symbolic_shape_util`（has_free_symbols/materialize_shape/shapes_statically_equal，含「广播dim无法物化则放弃折叠」注释论证）并以`propagate_fake_tensor`沿图传播元数据；发布无symbolic_shape_util.py文件，遇SymInt形状直接放弃折叠（`any(isinstance(s, torch.SymInt))`→None），形状比较用`node_meta.shape == val_meta.shape`直比、无fake传播。**本卡对get_binary_fold_result的symbolic形状描述为主线行为；发布版为无符号支持的简化折叠。**
