---
type: Guide
title: 实验Triton clone折叠：布局判定、转置救援与动态提示
description: 保存连续尾段/救援成本、符号及提示投票、逐tile访存与UB估算、lazy回退和bet键边界。
tags:
- task.optimization
- topic.compilation
- topic.memory
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/rescue_rules.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/lowering.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/npu_header.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py
  role: implementation
created_at: '2026-11-11T08:26:31Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---


# 实验Triton clone折叠：布局判定、转置救援与动态提示

## 固定的两层局部合同

针对TorchNPU主线ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf的rescue_rules完整本地规则，以及所列lowering、codegen和config调用段。第一层按源布局决定保留lazy clone还是尝试materialize；第二层按实际/模拟tile判断访存形态。没有导入模块、执行规则、生成kernel、运行模型或验证注释中的布局样本与加速数字；平台未知，保持draft和空平台。

完整读取规则不等于完整审阅lowering914行、header1171行或外部Triton PtrAnalysis。初次header证据仅核轴顺序与UB估算，本轮增补下文所列Line 2收集、promotion选择、真实优先序消费者及WARN/strict逻辑；其余header、完整跨层和设备校验仍独立。

## npu_clone的真实早退与失败行为

npu_clone先取得上游clone结果，再检查clone_policy，非法值抛ValueError。None/fold-all直接保留结果；memory_format不是torch.contiguous_format也直接保留，即使设置materialize-all也受这个格式门槛限制。contract模式下布局不可得、或动态布局且clone_contract_dynamic关闭，仍直接折叠；可证明row-major也保留上游结果。

其余布局调用fold_verdict，传配置中的max_swaps和min_axis；构建符号substrate失败或判定抛Exception转为materialize理由。若得到fold，就尝试记录布局bet并返回lazy结果；否则调用fallback_handler(aten.clone.default)尝试实体化。该调用再抛异常时也会DEBUG记录并返回原lazy结果。因此“怀疑一律materialize”不是整个入口的保证，materialize判定也不是外部复制已经成功的证明。

## 判定顺序：连续尾段优先，再看救援成本

trailing_run从末维往前，size为1的轴跳过，只有stride等于累计run才继续乘size，首个不匹配就停止。fold_verdict先判断run*itemsize是否达到min_run_b，默认32字节；达到则直接fold。未达到才进入_rescue_feasible，默认max_swaps=2、min_axis=8、min_mouth_b=8字节。

救援路径先剔除可证明长度<=1或stride=0的轴，并按tile维顺序解释剩余轴。judge_permute稳定地按stride降序排序，再反转为inner_first；相等stride保留原槽顺序，不按名字额外排序。它依次区分少于两活轴的degenerate、布局顺序已一致且末轴stride=1的contig、identity-tail、最小stride非1的tail失败，以及重新排序后连续轴数没有严格增加的失败；只有连续轴数严格增加才给rescue。

contig是这套局部分类的返回标签，identity分支没有再逐轴验证完整dense stride乘积。不能把标签升级成任意Tensor布局的通用连续性认证。count_contiguous_axes本身则从expected=1沿指定inner-first序逐项比较stride，成功才累计乘length。

_rescue_feasible在rescue基础上要求读侧mouth达到阈值；按布局置换的错位轴数减非平凡循环数计算swap成本并限于max_swaps；每个错位轴都须达到min_axis，没有对stride=1轴额外豁免。这些是静态/提示驱动的成本门槛，不是实际转置次数、设备吞吐或UB分配的实测结果。

## 符号谓词与example-shape二次决策

IntSubstrate直接使用整数比较。SizevarsSubstrate借助statically_known_equals/leq/gt/geq，不能证明大小关系时gt返回None，稳定排序据此抛UndecidableOrder；其余谓词有各自False/None回退，不以自行增加的动态shape guard代替未知关系。

threshold_ge先尝试证明，失败后只有clone_dynamic_hint_tier开启才以optimization_hint的整数值投票。fold_verdict遇why含undecidable，也可在该开关开启时把整组size/stride换为example-shape提示值，再用整数规则重判；失败则materialize。关闭提示层才不会走这两种提示决策，因此不能把默认配置下所有fold结果都称为对整个动态范围的形式证明。

min_lb通过外部表达式转换/shape_env.bound_sympy取下界，主要进入理由字符串；不能用日志展示的下界替代实际threshold_ge的证明或hint分支。调用方对判定异常的处理与规则内部的局部异常范围不同，不能假定任何依赖缺失都会由每个helper吞掉。

## tile访存健康与UB字节只是模型

tile_chain按order依次消耗xb：未知length吃当前余量，已知length取min(length,max(1,remaining))，之后余量整除并至少保留1，不因余量用尽提前停止。它没有在本地给任意零/负长度做通用合法性校验，调用方应提供符合实际tile合同的输入。

judge_load对没有活轴返回scalar/health=False，单轴只有stride=1才为contig/True。多轴contig时mouth为最后活轴长度乘元素字节、ub_B为各活轴乘积乘字节；rescue时用最内存储轴宽度作为mouth，其他轴乘积为D，ub_B=2*D*ceil32(mouth)，表示copy+transpose双缓冲及每行32字节对齐。其他情况no-rescue/False，UB记None。

health=True本身没有在judge_load里与设备容量比较，也不验证真实编译器是否采用同样缓冲。ub_budget_b另尝试读取设备属性helper，任意异常退到196608字节；这是本地回退值，不是所有设备的容量承诺。

所列header片段按divisor降序构造judge所需slot顺序、另按升序构造默认greedy链；用1024/2048/4096、一个夹在4096..8192的合成rung及formula候选并集扫描。_judge_all把相同slot顺序、各load系数和tile长度交judge_load，_violations片段把各load的ub_B求和与预算比较。完整header其余部分仍独立；本轮另补下文的本地解析/采用逻辑，估算仍不能替代真实UB编译结果。自动调优候选的其他过滤另按对应实现核对。

## bet键和可观察性不等于完整覆盖

bet_key过滤活的(length,stride)，可用resolve将其换为提示表示；转换失败保留原对。返回键是(buffer name,frozenset(live pairs))，对排列不敏感，但frozenset会合并重复对，不能照搬docstring把它描述成保留重复次数的multiset。buffer名用于区分相同布局的不同来源，不是跨任意别名对象的内容身份。

_record_fold_bet把理由存到V.graph._npu_clone_fold_bets，创建/记录过程任意Exception都会忽略；它不强制每个fold都形成可用记录。config初值为clone_policy=contract、clone_contract_dynamic=True、max_swaps=2、min_axis=8、pointwise_tile_contract=True、clone_dynamic_hint_tier=True、clone_contract_check=log，实际会话patch值另核。此处只记录check开关声明，不在未展开的header尾部上新增严格检查成功承诺。

排查clone优化时应分别记录原memory_format、布局来源、policy早退、整数或hint判定、fold/materialize实际结果、tile轴顺序、逐load估算与真实生成/设备表现。规则里的注释性能和研究样本不是本次运行证据，减少复制也不能单独推导完整数值、别名和性能验收已完成。

## 固定来源

- [固定来源 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/rescue_rules.py)：1–461；完整本地判定模块，外部依赖另计。
- [固定来源 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/lowering.py)：679–705、708–795；仅所列有界内容。
- [固定来源 3](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/npu_header.py)：395–399、473–493；仅所列有界内容。
- [固定来源 4](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)：312–344、471–471；仅所列有界内容。

## Line 2的实际入口与被分析load集合

本轮只扩充同一固定主线的本地落地，不重读或重复建立rescue_rules的461行数学规则。codegen_range_tree在_npu_linearize为假时委托上游；所列linearize分支对非loop、非reduction的tree调用自定义header。header的所列门槛是已有优先序为空、pointwise_tile_contract为真、balanced_target为假且free_tile_nodes至少两个；进入helper后再排除scalar odometer轴，剩不足两个或没有load行都回空字典。

此前的input-stride优先序在reduce_xblock_by_input_stride开启、inside_reduction且可取得完整stride映射时可能已建立，会挡住该入口。这里的Line 2 gate没有另加not inside_reduction检查，不能仅据注释的“pointwise”标签推导所有归约上下文都已被独立排除。config声明input-stride开关True、pointwise_tile_contract=True、balanced_target=0；运行态值另核。

collector只看kernel.loads._lines的字符串或对象.line中含tl.load的行。_npu_extract_load_addr从字面tl.load(开始以括号深度找到第一个参数边界，再找顶层加号后的地址，最多去一层完整外括号；_npu_load_ptr_token取加号前token。它们是生成子集的文本扫描，不是完整Triton语法、引号/注释/多行或任意指针表达式解析器。

解析失败的行直接跳过；随后以free-axis符号做sympify，只有各轴系数均为整数才纳入。某轴出现在表达式里却抽不到非零线性系数（如隐藏于div/mod），也会整条load跳过。**这些load既不参与promotion、UB求和，也不加入bet匹配与最终健康检查**，不是一条解析失败就证明其它load或整核都安全。没有纳入任何load则返回空字典。

指针token通过input/output buffer表还原buffer名（input映射优先），元素字节按共享指针类型表，未知回4；该metadata构造try失败可保留已收集的部分表。布局长度/divisor通过optimization_hint再int化，不可得则None；它不为完整动态范围新建形式证明。default greedy按divisor升序、未知最后；judge slot按降序、未知也最后。若没有被分析load在最后slot上系数>=2，就提前返回，后续验证也不执行。

## promotion只搜索一个前置轴，模型检查与真实资源有别

候选XB仍是1024/2048/4096、一个夹在4096..8192的合成容量rung与公式候选并集。_npu_formula_xblocks重建正的x/y/z提示和指针signature，向外部_pw1d_formula_configs传num_load及min_elem_per_thread=1，取其XBLOCK集合；没有x或任何异常回空集合。该helper的esz形参未被函数体消费，也不携带全部原始metadata，不能把并集当作全部真实autotune配置已严格逐项复现；公式body本轮未展开。

对每个XB按给定chain模拟tile，再给所有**纳入分析的load**调用judge_load。_violations把health=False的(load,XB)收集为集合，并把各load的ub_B（None按0）求和与budget比较；不是最终kernel全部缓冲、store、scratch或真实编译器分配的完整资源统计。公式XB没有被合成rung上限裁剪，字面4096也始终参与这组模型检查。

若default在全部代表XB下既无健康失败也无预算超限，直接返回空字典。否则仅从default将其挤到tile=1、hint长度>=2且某load系数为1的轴中取候选，按(长度,名称)排序。逐个把**一个轴**提到chain首位，其余轴保留default相对顺序；只有所有所判load在全部XB都健康且无模型UB超限，才采用首个成功trial并返回rank字典。它不搜索任意多轴联合排列，也不通过设备基准挑最快者。

所读消费者将rank用作_bal_nodes的_ordered排序key；未命中rank的轴排后。rank改变的是greedy分配优先序，不就地重排_block_def_nodes的定义列表；scalar-odometer等排除条件仍独立。完整后续tile表达式/发射与执行没有在本轮扩成整文件资格。没有可行trial时保留default并回空字典，不能把“试过promotion”写成一定已经改善访存。

## WARN/strict检查是一方向的bet核对

_verify只有真正被调用才校验clone_contract_check是否为None/log/strict/off，非法值报ValueError；前述空load、预过滤、default完全健康等早退可绕过它。off只跳过诊断，不关闭此前的trial搜索或rank采用；要关入口应核pointwise_tile_contract及实际gate，不将两个开关混用。

对于每个不健康的被分析load/XB，None/log/strict都会调用warning；只有buffer/layout键匹配到Line 1 bet且check为strict时才抛RuntimeError。strict下未匹配的失败也仅告警。键仍经共享bet_key，length提示None/假值按0送入活性规则，解析不到buffer名或维度被忽略都可能影响匹配；不匹配不是对Line 1全部bet的反向验收。

**UB超限只用于拒绝trial，不是这里单独触发WARN或strict的条件。** 例如只有预算超限而health均True时，最终_verify没有不健康load可报；不能把没有WARN、没有raise或check=off推成预算和全核load都通过。该函数也没有围住整个流程的统一except，局部解析/提示失败的回退不能泛化成任意依赖、judge、配置或日志异常都静默返回default。

这轮增补闭合的是所列本地选择和诊断路径。验收应同时记录被跳过/纳入的load、pointer/buffer身份、hint值、default/trial链、XB集合、health与UB两类结果、rank实际消费者、bet命中和check模式，再独立核最终生成与真实设备数值/性能；未增加verified。

## Line 2新增有界证据

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/npu_header.py)（implementation）：199–278,319–348,351–557,560–578,595–642,762–809行；仅本轮列出的完整helper/调用片段，不提升整个header/codegen/config资格。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)（implementation）：120–120,334–344,379–379行；仅本轮列出的完整helper/调用片段，不提升整个header/codegen/config资格。
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py)（implementation）：4101–4133行；仅本轮列出的完整helper/调用片段，不提升整个header/codegen/config资格。
