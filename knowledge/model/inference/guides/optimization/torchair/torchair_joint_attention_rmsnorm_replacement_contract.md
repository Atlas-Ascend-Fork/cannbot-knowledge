---
type: Guide
title: Joint图Attention、RMSNorm与RoPE替换的实际边界
description: 完整补独立包两版joint规则与RoPE注册，区分训练/推理、mask窗口、缓存和通用manager守卫。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/npu_fx_passes/joint_graph_passes/npu_fusion_attention.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/npu_fx_passes/joint_graph_passes/npu_rms_norm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/npu_fx_passes/joint_graph_passes/npu_fusion_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/npu_fx_passes/joint_graph_passes/npu_rms_norm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/npu_fx_passes/joint_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/experimental_config.py
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph_passes/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph_passes/npu_fusion_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph_passes/npu_rms_norm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph_passes/npu_rotary_mul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph_passes/__init__.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph_passes/npu_fusion_attention.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph_passes/npu_rms_norm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph_passes/npu_rotary_mul.py
  role: implementation
created_at: '2026-11-10T12:46:34Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# Joint图Attention与RMSNorm替换的实际边界

## 版本与所读调用链

本卡定向审阅TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的npu_fx_pass接入、joint pattern初始化与Attention/RMSNorm替换函数，并对照发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的相应规则。两版所列规则函数在去掉文档字符串和日志表达式后的静态AST对照一致；这项对照不验证上游matcher、数值或完整运行等价。入口和全局patch细节按所列主线范围说明，没有运行上游、注册规则或调用设备，保持draft与空平台。

## npu_fx_pass与post-grad融合不是同一个开关

主线experimental_config.npu_fx_pass默认False，pattern_fusion_pass默认True。合并分解表后add_npu_patch仅在npu_fx_pass为真时调用npu_patch_fx_pass；后者清空上游joint_graph.patterns、Inductor分解表及额外随机分解表，再用当前分解表填回并替换joint_graph.lazy_init。它修改的是进程共享对象，不是只给当前GraphModule附一份私有规则。

实际joint_graph_passes在启用该配置的分区函数中位于default_partition之前；推理compiler包装及joint compiler包装也有对应调用。AOT路径和整体顺序复用[FX管线](torchair_fx_compiler_pipeline.md)，不能把post-grad pattern_fusion_pass=True当成这些joint规则已启用。

lazy_init按注册表调用初始化函数；Attention/RMSNorm初始化各有lru_cache(None)，没有torch_npu模块时返回。局部缓存和外层init_once_fakemode意味着注册不是每次模型执行重做；所读patch没有同步清这些初始化缓存，不能仅凭再次构造backend就断言共享规则表已重新完整注册。这里不把静态状态边界写成已复现的多后端故障。

## Attention只注册所列training pattern

第一种搜索表达式是Q×K.transpose(2,3)/sqrt(head_dim)，加attention_mask，沿末维以FP32 softmax后转回Q dtype，dropout的p固定0，再乘V。替换取Q的num_heads，以BNSD调用npu_fusion_attention，仅保留第0输出，keep_prob固定1、scale为1/sqrt(head_dim)、pse和padding_mask为None。它不是任意Attention、非零dropout或任意layout的自动融合规则。

第二种搜索从三维Q/K/V做view与transpose，设置num_key_value_heads=num_heads，带position_ids/cos/sin的半维旋转表达式，再执行同样Attention，最后transpose、contiguous、reshape回三维。替换保留这些RoPE表达式和末尾布局恢复，只把Attention部分换成融合接口；不能据此认为RoPE、输出contiguous及所有中间存储均已消失，也不泛化为任意GQA或KV-cache结构。

两种替换都将原加性attention_mask转为bool；两者都把pre_tockens设为三维hidden_size或num_heads×head_dim、next_tockens设0。这里的窗口参数不是从KV长度通用推导，bool转换也不保留任意浮点bias幅度。注册传入extra_check=_return_true，局部没有再验证mask内容只由0/屏蔽值组成、窗口等价或任意相对位置偏置语义。因此，这段改写不能用作“所有加性mask均与融合接口数值等价”的证明，应固定实际mask含义和序列窗口独立核对。

候选注册使用training_graph，兼容别名为joint_fwd_bwd；本文件没有另一次inference_graph注册。RMSNorm则显式注册两者。这个差异只说明本地注册路线，不据此否定推理图中所有其他Attention融合。样例的BF16 QKV、固定shape、head_dim=128以及部分FP32/BF16 mask/cos/sin组合是初始trace输入与scalar_workaround，不是完整shape/dtype支持矩阵。实际matcher重追踪和合法性依赖精确上游版本，本卡未展开。

## RMSNorm的FP32统计与输出选择

RMSNorm搜索先记输入dtype，将hidden_states转FP32，计算pow(2).mean(-1,keepdim=True)，乘rsqrt(variance+epsilon)，再转回输入dtype并乘weight。替换调用npu_rms_norm(hidden_states,weight,epsilon)[0]，只返回归一化结果，不把rstd作为新增可见输出。

它在training_graph与inference_graph各注册一次，epsilon通过scalar_workaround提供样例1e-5；替换函数显式接收epsilon，不能从这个样例推定模型epsilon被无条件改成1e-5或接口默认值。这里没有LayerNorm减均值模式、任意统计轴或额外统计输出的同一规则；融合算子和反向支持见[GE层组与RMS归一化](torchair_ge_layer_group_rms_norm_lowering.md)。

这些规则直接使用上游register_replacement与patterns，不经过post-grad _PatternPassManager的stream一致性包装，不能把[公共Pattern管理器](torchair_fx_pass_and_fusion_controls.md)的局部守卫自动套到joint规则上。未命中规则不等于整图回Eager；替换或初始化报错也没有在所读函数中统一捕获成安全回退。

Attention/RMSNorm计数器在replacement Python函数体中递增，不能作为实际训练步的设备调用次数或收益。定位时保留精确revision、两个开关、AOT阶段、原FX表达式与替换后mask/窗口/输出布局，再核数值、反向与性能；本卡没有新增verified或收益数字。

## Evidence

- [主线Attention规则](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/npu_fx_passes/joint_graph_passes/npu_fusion_attention.py)：17–24、31–202；[发布规则对照](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/npu_fx_passes/joint_graph_passes/npu_fusion_attention.py)：35–54、57–86、90–158、161–221。
- [主线RMSNorm规则](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/npu_fx_passes/joint_graph_passes/npu_rms_norm.py)：16–23、30–87；[发布规则对照](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/npu_fx_passes/joint_graph_passes/npu_rms_norm.py)：34–44、47–89。
- [joint注册与lazy init](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/npu_fx_passes/joint_graph.py)：6–23；[共享patch](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/__init__.py)：384–405、455–462。
- [编译阶段调用](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)：823–836、862–877、1067–1076；[开关默认值](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/configs/experimental_config.py)：21–29。

## 独立npugraph_ex两版完整规则与RoPE补充

另完整审阅独立包两版joint_graph.py、joint_graph_passes/__init__.py及Attention/RMSNorm/RotaryMul三个模块；范围由下列完整来源精确限定，未执行导入、torch.empty、注册或替换。Attention和RMSNorm的实际表达式、mask转bool、窗口、输出顺序及training/inference分支与前文逐项对照，不从同名或样例推定任意产品/数值等价。

独立joint注册装饰器将同名key直接覆盖到dict并返回函数；lazy_init由外部init_once_fakemode包装，导入包后按dict迭代调用初始化函数。包__all__用pkgutil枚举邻近模块名，但显式导入仍只有Attention、RMSNorm和RotaryMul，不能据枚举列表写成所有插件均已自动执行。各初始化lru_cache在首次没有torch_npu时也会缓存返回结果，源码没有因随后才导入该模块自动清缓存的分支。

RoPE搜索为q*cos+rotate_half(q)*sin，rotate_half将末维前后两半重排为[-x2,x1]再cat；替换调用npu_rotary_mul(q,cos,sin)，保留其返回对象。样例形状为(2,4,8,16)，q需梯度、cos/sin不需梯度，同时向training_graph与inference_graph注册，extra_check为上游_return_true；没有局部另加全部shape/旋转约定/梯度合法性校验。

Attention第一组样例BF16 QKV与FP32 mask，第二组QKV仍BF16、mask/cos/sin按FP32或BF16枚举，head_dim=128；RMSNorm样例shape(4,2048,4096)和weight4096未显式指定dtype，交torch.empty当前默认，epsilon样例1e-5。这些只是初始trace候选，不能变成完整dtype/shape矩阵。计数器在replacement Python函数体中递增，非每步设备Kernel计数。

这10文件直接使用Torch原始register_replacement和joint patterns，未走独立post-grad manager的stream/确定性/控核一致性包装。前文的公共manager守卫不能机械套在joint注册体；真正接入、匹配、反向和数值继续按所用软件栈验证。

## 完整本地实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph.py)（implementation）：1–24。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph_passes/__init__.py)（implementation）：1–7。
- [固定实现 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph_passes/npu_fusion_attention.py)（implementation）：1–202。
- [固定实现 4](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph_passes/npu_rms_norm.py)（implementation）：1–86。
- [固定实现 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph_passes/npu_rotary_mul.py)（implementation）：1–88。
- [固定实现 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph.py)（implementation）：1–22。
- [固定实现 7](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph_passes/__init__.py)（implementation）：1–7。
- [固定实现 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph_passes/npu_fusion_attention.py)（implementation）：1–220。
- [固定实现 9](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph_passes/npu_rms_norm.py)（implementation）：1–87。
- [固定实现 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/_utils/npu_fx_passes/joint_graph_passes/npu_rotary_mul.py)（implementation）：1–88。
