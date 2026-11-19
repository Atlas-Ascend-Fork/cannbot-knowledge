---
type: Guide
title: AddRMSNormCast融合的多输出与view守卫
description: 补完整独立包双版Cast规则，保留八类搜索、输出重排、view检查和注册生命周期。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/add_rms_norm_cast.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/patterns/add_rms_norm_cast.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/add_rms_norm_cast.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_pass_manager.py
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/pattern_util.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_util.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/add_rms_norm_cast.py
  role: implementation
created_at: '2026-11-10T12:59:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# AddRMSNormCast融合的多输出与view守卫

## 固定来源与注册位置

本卡定向审阅TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的AddRMSNormCast pattern、独立npugraph_ex对应规则及入口，对照发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的普通TorchAir规则。普通两版规则函数在去掉文档字符串与日志表达式后AST一致；独立包的guard/搜索结构相同，注册体另有下述差异。静态对照不是上游matcher或数值等价验证，未运行上游、构图或设备，保持draft与空平台。

两主线入口均由各自pattern_fusion_pass控制post-grad应用，在所用torch.__version__比较达到2.6时注册cast规则；普通TorchAir的cast注册位于mode!=max-autotune分支之外。不能套用同一文件中转置BatchMatmul/静态量化的mode限制，也不与npu_fx_pass的joint RMSNorm规则混为同一阶段。共享manager和检查层次见[量化Pattern守卫](torchair_add_rmsnorm_quant_pattern_guards.md)。

## 搜索需要原精度、残差与FP32三个输出

手工MultiOutputPattern取npu_add_rms_norm的第0输出y、第2输出xOut，以及y的FP32转换结果。AddRMSNorm节点要求_users=2，y的getitem也要求_users=2；它不是任意只保留cast结果的链都能套用的通用RMSNorm替换。其他中间值还有消费者时需遵守具体用户数和matcher规则，不能删掉用户仍需的统计量。

转换准确识别两种target：npu._npu_dtype_cast.default的FP32参数，或aten._to_copy.default的dtype=torch.float32；各有直接转换与先view([-1,Ignored()])再转换的变体，再区分显式epsilon与默认epsilon，共注册八种组合。任意名称相似的to、额外device/layout参数或其他输出dtype不由这段搜索自动认证。

替换从融合算子接回(y_cast,y,统计项,xOut)，再按搜索顺序返回(y,xOut,y_cast)。有view的版本还取融合y.size(-1)，对y_cast重新view(-1,h)，返回该view；没有view的版本直接返回y_cast。融合没有把搜索端保留的低精度y、残差和输出形状恢复自动抹掉，也不能把融合接口的四个物理输出原序当成该pattern的三输出。融合输出的具体dtype、产品与统计冲突复用[算子API](../../../apis/torch_npu/npu_add_rms_norm_cast.md)，GE映射见[归一化lowering](torchair_ge_layer_group_rms_norm_lowering.md)。

## view额外检查验证了什么

只有带view的变体传入_pattern_extra_check。它寻找匹配中的aten.view与AddRMSNorm第一输入，要求view的shape参数是list/tuple；从输入tensor_meta取尾维，再读取view_args[1]的meta.val（若有）或其字面值。返回表达式先依赖该值的truthiness，再比较str(view_arg_val)==str(x1_last_dim)。

这里没有检查该维度节点确实是对y执行size(-1)，也没有做符号代数、stride、Storage或完整reshape元素数证明；直接访问第二项本身也依赖搜索已给定相应形状结构。注释中“dimension argument恰为-1”不能转述成函数实际验证了sym_size的轴参数。零值、Meta缺失和符号值的布尔化必须按准确图核对，不从注释保证任意异常输入都会安全False。

不带view的变体不使用这项额外维度检查，仍经公共manager的stream以及独立包特有scope检查。这个区别不意味着直接变体绕过所有dtype/shape/设备约束；所读pattern函数没有补齐融合算子的全部支持表。

## 独立包的去重注册差异

普通TorchAir以scalar_workaround的epsilon样例2e-6注册，独立包改用manager中的DEFAULT_EPSILON，其值仍为2e-6；独立包八种注册均另传skip_duplicates=True。该值是trace工作参数，不是把实际模型epsilon无条件改成2e-6的证明，显式epsilon替换仍接收同名参数。

独立manager仅在所用版本比较达到2.7.0时向上游register透传skip_duplicates，旧分支不传。因此不能从pattern文件设置True就断言所有Torch版本都执行相同去重机制，也不能把去重成功当作替换数值或设备支持已验证。两个包各有lru_cache注册及各自manager，不据函数名相同推定共享同一规则实例。

未命中时这条pattern不替换，不代表整图回Eager；检查和注册异常没有在这些函数中统一捕获为安全回退。排障应保存准确cast target、三个输出及用户数、view_args与tensor_meta、epsilon和注册版本分支，核对替换后的输出顺序/shape，再验证数值、实际拷贝与性能。本卡没有新增verified或收益数据。

## Evidence

- [主线普通规则](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/add_rms_norm_cast.py)：15–106、109–185；[发布规则对照](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/patterns/add_rms_norm_cast.py)：15–50、53–225。
- [主线独立包规则](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/add_rms_norm_cast.py)：15–106、109–189；[epsilon与去重消费者](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_pass_manager.py)：14–16、89–143。
- [普通注册入口](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/pattern_util.py)：18–38；[独立包注册入口](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_util.py)：20–37。
- [普通FX阶段](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)：381–384；[独立包FX阶段](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py)：369–372。

## 独立包双版完整文件对账

完整读取独立npugraph_ex包主线189行和发布229行Cast规则，含全部搜索构造、嵌套search/replace、Meta检查及注册分支。两版完整差异主要是格式、文档和无插值日志写法，逐项保留实际行为，补充的是准确发布独立包来源，而不是将普通TorchAir文件名代作证据。

八种组合均保留前述用户数和(y,xOut,y_cast)顺序，显式epsilon仍交替换函数；FakeTensorMode中的样例是FP16 (1,1,2)输入和长度2的gamma，没有指定真实NPU设备，也没有实际执行该trace。初始化按manager对象lru_cache，首次缺torch_npu的跳过也会被缓存；不能以稍后导入torch_npu就断言该进程自动重注册。

不带view没有这一项尾维extra_check，带view的truthiness与字符串比较也没有独立证明size(-1)轴、任意符号或Storage布局。额外检查、manager守卫、完整算子支持和设备数值仍按不同层验收；本次完整文件覆盖只关闭两份本地定义和控制流。

## 完整本地实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/add_rms_norm_cast.py)（implementation）：1–189。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/add_rms_norm_cast.py)（implementation）：1–229。
