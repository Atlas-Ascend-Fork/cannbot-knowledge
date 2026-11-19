---
type: Guide
title: AddRMSNorm量化融合的匹配守卫与输出重排
description: 补完整独立包双版量化规则与注册差异，保留静态Meta、动态flatten及输出顺序边界。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/add_rms_norm_quant.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/add_rms_norm_dynamic_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/patterns/add_rms_norm_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/patterns/add_rms_norm_dynamic_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/pattern_util.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/pattern_pass_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/add_rms_norm_dynamic_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/add_rms_norm_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/add_rms_norm_dynamic_quant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/add_rms_norm_quant.py
  role: implementation
created_at: '2026-11-10T12:46:34Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# AddRMSNorm量化融合的匹配守卫与输出重排

## 版本与范围

定向审阅TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的静态/动态AddRMSNorm量化pattern、注册入口与管理器，并对照发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013对应规则函数。两版所列规则在去掉文档字符串和日志表达式后的AST对照一致；主线入口/共享manager细节按本卡固定范围说明，不自动推广独立npugraph_ex包。没有运行上游matcher、替换图或设备算子，保持draft与空平台。

本卡补[融合控制总览](torchair_fx_pass_and_fusion_controls.md)尚未展开的真实guard，不把文档候选约束、Python检查通过和融合算子硬件支持视为同一层。

## 注册门槛与已有规则的生命周期

主线_optimize_fx在pattern_fusion_pass为真时调用_apply_pattern_passes，随后仍执行view转reshape。pattern_util在所用torch.__version__比较结果达到2.6时注册动态量化、flatten变体和cast；静态AddRMSNormQuant只在本次mode不是max-autotune时注册。

这里的mode条件约束新增注册，不是对已注册规则的逐次屏蔽：pattern_util持有进程全局manager，_pattern_manager只在首次创建，apply_pass对整个pass_dict执行；所列注册函数另用lru_cache缓存。所读代码没有在进入max-autotune前删除先前注册的静态规则。因此跨模式复用同进程时，应检查manager已有状态，不能只看本次if就证明这次apply绝无该规则；本卡未运行跨模式复现。

公共manager先调用stream一致性检查，再调用extra_check；False会拒绝这次替换。它默认按fwd_only/inference_graph注册，这与npu_fx_pass的joint规则不同。异常没有在这些局部函数中被统一改写为False或整图Eager回退。

## 静态量化的检查比注释更具体

静态搜索把npu_add_rms_norm的第0输出接npu_quantize，axis固定-1，注册的div_mode为True；分别覆盖有/无显式epsilon、有/无保留x_out。替换调用npu_add_rms_norm_quant，保留量化结果与需要的残差；不会新增未被搜索图要求的中间统计量。

_pattern_extra_check实际读取Meta并检查：

| 项目 | 实际局部条件 |
| --- | --- |
| x1/x2 dtype | 两者同为FP16，或两者同为BF16 |
| 输入尾轴 | 第二个残差输入非标量，尾轴元素数×element_size须为Python int且能被32整除 |
| npu_quantize输出编码 | node.args[3]须为1或12；这里是算子编码，不是torch.dtype对象 |
| gamma/scales | 两者shape相等 |
| 非None zero_points | 只显式拒绝UINT8/INT8 dtype |

注释称zero_points只支持INT32/BFLOAT16，但这个函数实现的是拒绝两类dtype，没有按注释做完整白名单，也没有比较zero_points.shape；日志中的“gamma, zero_points or scales shape”不等于三者shape都经过检查。它同样没有在这个guard中补齐融合算子的全部gamma/scales dtype与数值条件。通过该函数不能扩展算子支持范围；缺失Meta或不符合预期参数结构也不能由这些直接索引推断必然安全跳过。

无x_out的手工pattern要求AddRMSNorm节点_users=1，只取归一化输出再量化；需要保留x_out的搜索则返回对应残差。中间值还有其他消费者时，要按实际多输出pattern与上游matcher约束判断，不能仅为减少节点数删除其使用者。

## 动态量化保留哪个输出、是否带平滑scale

直接变体把smooth_scales传给npu_dynamic_quant，替换改传融合算子的smooth_scale1，并固定output_mask=[True,False]，只量化第一路。搜索/替换对应返回(yOut,xOut,scale1Out)，无残差变体对应(yOut,scale1Out)；有epsilon的版本显式转交该参数。不能把融合算子5个物理输出直接按原组合接口的位置返回。

flatten变体不带smooth_scales，手工MultiOutputPattern要求AddRMSNorm与DynamicQuant各有两个使用者，包含归一化输出→aten.view→DynamicQuant、scale输出→view([-1,1])及残差。替换先对原始shape调用融合算子，再对yOut执行flatten(0,1)，对scale1Out执行view(-1,1)，并保留xOut。融合不意味着这两个输出形状恢复节点被删除。

## flatten额外检查只是部分形状证据

_check_view_shape寻找AddRMSNorm输入、第0输出和直接作用于该输出的aten.view；读取tensor_meta，要求输入与归一化输出rank相同，view_size为list/tuple，且长度等于输入rank减1。首维若是有name的图节点，只检查名字以mul开头；否则在输出rank至少2时，检查首维等于原前两维乘积。

它没有逐项证明剩余view维度、乘法节点的精确操作数、任意stride/storage及全部符号代数等价。因此注释里的“等价flatten(0,1)”是目标语义，不能把这个局部guard写成对任意reshape的完整等价证明。命名、tensor_meta、用户数或实际图结构变化都可能使融合不命中，甚至触发未捕获的检查错误；不应据此直接归因融合算子不支持。

排障时分别保存mode与manager状态、改写前后target/参数、Meta与view_size、x_out/scale消费者、stream标签，再核对融合接口及数值和实际搬运。独立包还有自己的scope检查，详见[设计与管理器边界](npugraph_ex_standalone_design_contracts.md)；本卡没有设备收益或新增verified。

## Evidence

- [主线静态量化规则](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/add_rms_norm_quant.py)：15–66、86–241；[发布规则对照](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/patterns/add_rms_norm_quant.py)：15–63、83–231。
- [主线动态量化规则](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/add_rms_norm_dynamic_quant.py)：15–62、65–162、165–273；[发布规则对照](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/patterns/add_rms_norm_dynamic_quant.py)：15–66、69–162、165–292。
- [注册入口](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/pattern_util.py)：15–38；[管理器注册与apply](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/pattern_pass_manager.py)：14–18、65–140；[FX阶段](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)：372–384。

## 独立包完整量化规则与入口差异

另完整审阅独立npugraph_ex两版静态量化和动态量化共4模块；旧段中普通TorchAir的mode注册条件保持各自版本身份。独立pattern_util本地没有同一mode判断，会按顺序调用静态量化注册函数；此事实不改写普通包的分支，也不证明跨进程共享同一个manager。

静态规则分别为缺省/显式epsilon与不保留x_out两种手工pattern，注册入口的div_mode均为True，axis固定-1；替换不把搜索dtype原值作为另一个输出dtype选择传入。 无x_out的手工CallFunction只列y/scales/zero_points/dtype/-1，没有传div_mode，所接收闭包参数也未在该函数消费且extra_check未核它；不能从入口传True推导手工搜索已独立限定div_mode=True，上游默认值归一与匹配行为未在本组运行或闭合。无x_out手工pattern的AddRMSNorm _users=1，带残差搜索保留残差，显式epsilon按参数传递。_get_inputs的N=2、D=16、FP16样例及zero_points构造只是FakeTensor trace材料；其中zero_points的构造shape不作为真实融合guard已检查全部shape的证明。

动态普通组4注册覆盖有/无epsilon、有/无残差，smooth_scales改传smooth_scale1并只量化output_mask第一路；flatten组2手工pattern不带smooth_scales，并保留量化输出flatten与scale view。两版都没有把动态flatten extra_check扩成任意reshape完整证明：只认首维mul名字或前两维乘积，不逐项检查其余维度；直接索引view_size[0]和Meta仍可能传播未捕获错误。

两组完整本地检查、实际输出与前文逐项对应，默认epsilon来自独立manager常量2e-6，skip_duplicates仍受manager版本分支影响。这里不新增融合算子硬件、任意量化数值或性能保证。

## 完整本地实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/add_rms_norm_dynamic_quant.py)（implementation）：1–282。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/add_rms_norm_quant.py)（implementation）：1–241。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/add_rms_norm_dynamic_quant.py)（implementation）：1–298。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/add_rms_norm_quant.py)（implementation）：1–231。
