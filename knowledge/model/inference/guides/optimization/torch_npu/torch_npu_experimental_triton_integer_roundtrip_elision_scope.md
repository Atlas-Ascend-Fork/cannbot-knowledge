---
type: Guide
title: 实验Triton整数往返消除：窗口追溯、值域与改图边界
description: 核对实验Triton整数往返消除的dtype与窗口门槛、未检查值域和改图/安装异常边界。
tags:
- task.optimization
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/fx_passes.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/overrides.py
  role: implementation
created_at: '2026-11-11T08:20:32Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---


# 实验Triton整数往返消除：窗口追溯、值域与改图边界

## 固定优化与数值前提

本文依据TorchNPU主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`实验Triton的_elide_int_float_int_roundtrip_pass、完整嵌套helper、ElideIntFloatIntPass及安装器，只另读config开关和overrides的所列调用片段。发布`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`的三个精确路径均无Git条目，不据此断言发布没有同类优化。各模块保持有界资格，没有运行FX/FakeTensor、数值转换、改图或设备；产品与配套未知，保持draft、空平台。

优化试图把整数来源经过浮点转换、view/slice/scatter等路径后再转回整数的输出，改成直接从原整数来源slice/reshape。**dtype与窗口追溯并不是数值无损证明**：源码没有检查Tensor实际取值、范围或浮点精度。docstring只用f32的`|value| < 2**24`说明整数可精确往返的一个前提，却又在实际白名单允许float16、bfloat16、float32、float64，并未给前三者统一建立值域检查。

因此不能把embedding ID、整数dtype相同或开关默认True当作任意ID、任意浮点中间类型都无损的证据。跳过原浮点路线可能保留原路线已经舍入掉的信息；这里只记录固定实现和应核对的数值前提，不认证模型精度或删除了注释示例中的全部26个kernel。

## 从哪些节点开始追溯

开关ncfg.elide_int_float_int在pass入口再次检查，config声明默认True。外层只扫描call_function且target精确为prims.convert_element_type.default、输出目标dtype在白名单的节点；它没有把所有aten.to/_to_copy的整数输出都当相同入口。整数白名单为int8/int16/int32/int64/uint8/bool；浮点白名单为float16/bfloat16/float32/float64。

输入必须是FX Node，输出meta['val']必须有shape且非标量。_val/_dtype只读metadata；_size_on尝试把指定shape维转int，失败回None。没有metadata或不能取得某些所需尺寸时相应路径放弃，不产生运行时值域guard。

_trace从输出转换的源节点携空窗口开始，逐节点反向走一条来源路径，每次调用最多64个while步骤。只有已经跨过至少一次整数→浮点转换，且到达dtype**精确等于最终整数目标**的整数节点，才返回该来源及其坐标窗口。它不把不同整数宽度间的往返也消除；其它不认识的运算直接结束追溯，不越过普通算术表达式猜测等价。

## 支持的路径按实际坐标处理

| 路径 | 本地处理与限制 |
| --- | --- |
| prims.convert_element_type | 仅当源dtype为白名单整数、输出为白名单浮点时跨过并记saw_float；其它转换不作为透明边。 |
| aten._to_copy | 未给dtype或dtype等于源时透传；整数→浮点时记saw_float；其它dtype变化放弃。这不是对设备/布局/复制副作用的完整验证。 |
| aten.copy / clone | copy跟随args[1]的源值，clone跟随args[0]；没有在此独立确认copy两侧所有shape/dtype/broadcast条件，也未证明复制与整数视图的alias合同一致。 |
| slice | 只接受step=1，取得输入轴尺寸，把当前输出窗口按slice起点平移回输入坐标；缺尺寸或窗口超出结束位置时放弃。 |
| select | 把删掉的轴插回窗口坐标，后续轴号加1，并给选中轴固定[index,index+1)窗口。 |
| slice_scatter | 当前读窗全在写入区则转到src并减去scatter起点；全在区外则跟随base；跨边界则放弃，step也必须为1。 |
| view/reshape/squeeze/unsqueeze | 仅允许插入/移除size=1轴：非1轴数量、顺序和尺寸一一对应；真实轴合并/拆分不支持，size=1输出轴上的窗口被丢弃。 |

_norm对边界执行int转换，负边界加size后裁剪到[0,size]，None回0。**s_dim/sel_dim/sc_dim本身没有在这些分支统一转成非负轴号**；窗口使用的是所读轴号，而最终构造按range(src_rank)遍历。不要因此宣称已完整处理任意负轴、异常slice参数、动态符号或所有空窗口语义；这些条件仍要结合真实生成FX图核对。

这组路径描述的是局部值来源和坐标模型，不含数据扫描、浮点精度证明、通用stride等价或独立的mutation/alias分析。没有越过未知算术不等于对所有被接受图都已完成完整等价性验证。

## 新节点、FakeTensor metadata与失败范围

追溯成功后按源rank逐轴插入aten.slice，对全范围窗口可跳过，再按输出meta中的具体int形状决定是否追加aten.reshape。若创建了新节点，就要求原整数metadata有fake_mode，在该模式内逐步求slice/reshape metadata并填m.meta['val']；这里没有执行真实输入数值校验。

仅当replacement和被替换节点的metadata都非None时，显式比对dtype和shape；不匹配会删除新建节点并跳过。构建/metadata传播的try捕获Exception，尝试逆序清理made；清理自身异常被忽略。它没有统一事务回滚所有改动，也没有保证清理失败后图必定恢复原状。

更早的_trace调用、_norm的int转换、部分shape比较不在这个构建try内；不能概括为“任意不支持或异常都会安全跳过”。成功后replace_all_uses_with和erase原节点也在该try之外。至少改写一处才eliminate_dead_code并graph.lint，后者是上游pass自身代码，并不是本次摄取运行过lint/改图或数值测试。

替换后浮点链只有在失去其它使用者且死代码清理允许时才会被删除；不能按一次整数输出替换就宣称整条浮点路径、所有复制或全部列提取kernel已消失。新路径使用slice/reshape，完整storage alias、后续mutation与输出协议仍需模型图层面的证据。

## 安装顺序与开关的两个时点

overrides导入安装器，并在apply_npu_overrides中其它所列patch之后调用它。本卡只核到该调用，不保证前面的patch总能成功或整个后端已经加载。

安装器先get_custom_graph_passes读取已有post_grad_custom_post_pass；已有项中只要有一个不属于CustomGraphPass，就直接返回，不改造第三方raw callable或给它伪造uuid。否则复制原链，只有未含ElideIntFloatIntPass且开关为真时才追加；另按类身份去重追加TeSourcePinPass，再写回非空链。TeSourcePinPass本体与指纹范围在下节补充；外部缓存采用与所有缓存正确失效并不由局部安装器保证。

ElideIntFloatIntPass.__call__进入上述pass，运行时再次读开关；uuid把本文件交get_hash_for_files，并以开关repr作为extra。因此安装时关闭会阻止新追加，调用时关闭会让已安装pass直接返回；安装器不会因后续关闭开关而主动从原链移除已有实例。uuid返回式也不等于本次验证了跨进程缓存命中、失效或实际模型收益。

使用此优化时保留原始整数值域、浮点中间dtype、最终整数dtype、实际FX节点/窗口、FakeTensor形状和后续alias/mutation关系，再比较优化前后的结果与稳态表现。源码中的DIFM示例只是动机；本次没有运行模型或建立新的verified记录。

## 源码缓存指纹的实际范围

本轮另核TeSourcePinPass及_te_source_digest完整本体。__call__只pass，不改图；uuid调用_te_source_digest。默认base取当前fx_passes.py的abspath所在目录，os.walk搜集名称以`.py`结尾的文件；root字符串包含`__pycache__`时清空dirs并跳过。它按文件后缀和路径收集，不检查是否真的import过，也不是只收集本次图用到的函数。

另外，仅当base父目录下decomposition.py是文件时将其加入。文件路径列表排序后，以extra="te-source"交给外部get_hash_for_files；这里没有自行实现或审阅该helper的文件读取、哈希算法、缺失/权限异常及缓存策略。自定义base会同时改变遍历根和这个父目录，不能只将它理解为替换一份待哈希文本。

这覆盖的是所列树中**磁盘文件**，不是进程已加载函数对象、字节码或运行时monkeypatch状态。改磁盘不等于当前进程自动重新加载代码；目录外的普通_inductor文件（除显式加入的decomposition.py）、C++/共享库、环境、模型权重和设备状态也没有在这里一并收集。os.walk默认错误处理、外部helper及上游缓存采用仍有各自边界，不能由局部源码推导任意改动都必然触发正确重编译。

docstring将其用途描述为给FxGraphCache补充后端源码状态，并说后端配置由device_custom_config等外部机制入键；本卡没有把这段注释当作完整配置入键链已经审阅的证据。安装器中第三方非CustomGraphPass项仍会让整个安装提前返回，所以“source pin不受elide开关控制”也必须服从前面的类型门槛。关闭elide本身不阻止追加source pin，后续切换开关则不会主动移除已有实例。

排查修改源码后缓存结果不变时，先核实际安装链、加载位置、遍历到的路径、磁盘与进程代码是否一致以及上游缓存行为；不以本地uuid定义或文件固定commit替代运行验证。

## Evidence

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/fx_passes.py)：1–391,457–487行；仅所列完整pass/helper或有界调用，不提升整个模块资格。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)：135–136行；仅所列完整pass/helper或有界调用，不提升整个模块资格。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/overrides.py)：25–29,87–95行；仅所列完整pass/helper或有界调用，不提升整个模块资格。

### 本轮补充证据

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/fx_passes.py)：15–25,394–487行；仅补充源码指纹本体及实际调用，未重新资格化旧整数追溯内容。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/overrides.py)：25–29,87–104行；仅补充源码指纹本体及实际调用，未重新资格化旧整数追溯内容。
