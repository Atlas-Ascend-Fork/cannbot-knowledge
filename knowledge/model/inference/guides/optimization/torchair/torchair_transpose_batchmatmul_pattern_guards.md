---
type: Guide
title: 转置BatchMatmul融合的实际匹配条件
description: 补完整独立包双版BMM转置规则，核对四类模式、128元素对齐、轴范围和真实注册状态。
tags:
- task.optimization
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/batch_matmul_transpose.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/patterns/batch_matmul_transpose.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/batch_matmul_transpose.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/pattern_util.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_util.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/batch_matmul_transpose.py
  role: implementation
created_at: '2026-11-10T12:59:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 转置BatchMatmul融合的实际匹配条件

## 固定版本与入口

本卡定向审阅TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c的batch_matmul_transpose规则及注册入口，按函数对照发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013和主线独立npugraph_ex包。同一规则函数去掉文档字符串及日志表达式后的AST对照一致；这不意味着两个包管理器、精确上游matcher或设备支持完全相同。未运行上游、构图或设备测试，保持draft与空平台。

普通TorchAir由pattern_fusion_pass控制post-grad调用，所用版本比较结果达到2.6且mode不是max-autotune时注册这组规则；独立包同阶段由其config.pattern_fusion_pass控制，在所读注册入口没有同一mode条件。共享manager和跨模式已注册状态见[量化Pattern守卫](torchair_add_rmsnorm_quant_pattern_guards.md)，不把“本次不注册”推导成逐次apply必然屏蔽已有规则。

## 只搜索四种具体图形态

按注册顺序先放含输入转置的两类，再放直接bmm与输出view类：

| 搜索链 | 替换perm_x1 |
| --- | --- |
| transpose(x1)→expand→view→bmm→view→transpose | [1,0,2] |
| transpose(x1)→expand→bmm→transpose | [1,0,2] |
| bmm→transpose | [0,1,2] |
| bmm→view→transpose | [0,1,2] |

替换只调用npu_transpose_batchmatmul.default(x1,x2,perm_x1=...)，其余perm、bias、scale和batch_split_factor不在这里构造新值。它不是量化scale或切分输出的自动融合规则，也没有把权重转置等任意排列加入同一搜索。注册先后不替代上游重叠匹配和用户数等实际约束。

## Meta和范围检查如何收窄匹配

额外检查先定位bmm，读取其第一个输入的Meta Tensor，以shape[0]为B、shape[2]为K。匹配节点中transpose.int数量至少2时按输入转置场景检查1<=K×B<65536；否则只检查K<65536。这里的B/K来自进入bmm的Meta，不应直接拿最外层原x1的未转置维度套算。

随后逐个bmm实参要求Meta val是Tensor、dtype属于FP16/BF16/FP32，并要求shape[2]能被128整除；通常分别对应两矩阵的K与N，单位是元素而非字节。该检查比[算子API](../../../apis/torch_npu/npu_transpose_batchmatmul.md)的部分公开对齐条件更窄，不能因API可调用就认定pattern会命中，也不能用pattern的128规则改写所有直接调用的合法范围。

每个匹配到的view或expand都调用上游same_meta比较输入输出，返回False即拒绝。这组模式只允许其Meta比较所接受的中间变换，并非任意reshape/broadcast消除；本卡未展开same_meta全部字段，不能把它说成已证明真实Storage、stride与别名完全无变化。

该guard没有单独枚举输入rank、BMM所有shape关系或任意符号条件，而是直接取Meta和维度索引。上游规范化、合法bmm图与算子自身条件仍要满足；未知Meta/符号表达式不保证总是安全返回False，所读函数没有统一异常回退。

## transpose检查没有完整实现注释中的限制

_check_transpose_args要求两个维度参数是Python int，再拒绝任一值大于1。它没有在这个函数中检查非负、两维不同，或精确枚举(0,1)/(1,0)。搜索pattern又对维度使用Ignored，替换的输出排列却来自融合算子默认参数。

因此不能把注释“只支持0或1”转述为这里已经验证完整的合法轴交换，更不能按局部True结果手工扩大到同轴或任意负轴变换。是否有前序Noop消除、轴规范化或其他matcher条件阻止某个候选，必须按精确图与上游版本另核；本卡没有复现错误替换，也没有证明所有这些输入都会命中。

## 融合命中与算子收益分别验收

规则注册要求torch_npu已加载，使用FakeTensor样例仅用于注册；默认fwd_only路线与stream/scope检查由各包manager决定，见[融合控制总览](torchair_fx_pass_and_fusion_controls.md)。没有匹配不等于整图退回Eager，命中也不证明所有布局都免拷贝。

排查时保留四类实际链、输入Meta、K/N的128对齐、B/K取值位置、transpose参数和same_meta结果，再核对替换后perm与输出shape、数值和真实时间线。直接算子版本/产品、NZ及scale输出类型差异仍以API卡为准，本卡不新增支持平台、verified或性能数字。

## Evidence

- [主线TorchAir规则](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/batch_matmul_transpose.py)：14–163、166–317；[发布规则对照](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/patterns/batch_matmul_transpose.py)：14–173、176–386。
- [主线独立包规则对照](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/batch_matmul_transpose.py)：14–163、166–317，仅选定函数静态对照。
- [TorchAir注册入口](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/patterns/pattern_util.py)：18–38；[独立包入口](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/pattern_util.py)：20–37。
- [TorchAir FX调用阶段](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/npu_fx_compiler.py)：381–384；[独立包调用阶段](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/npu_fx_compiler.py)：369–372。

## 独立包发布源码与完整注册对照

完整审阅独立包主线317行及发布386行BMM转置规则，包含所有嵌套guard、四个搜索构造、样例与注册顺序。完整版本差异是格式及不插值日志写法等，不改变上文所列本地判断；发布独立包URL现在独立绑定，不再仅凭普通TorchAir发布文件代指它。

所读替换仍只传perm_x1，四个注册器按manager对象lru_cache，普通注册helper没有额外请求skip_duplicates=True。样例FP16 (1,1,1)用于FakeTensor追踪，不是通过128元素对齐extra_check的验收用例。isinstance(dim,int)也接受Python bool，而非负与互异条件仍没有在该函数补齐；本卡不据这种静态缺口宣称已实际命中错误替换。

完整文件覆盖不关闭外部same_meta、Torch matcher或npu_transpose_batchmatmul设备实现；准确输入Meta、负轴/同轴是否被其他阶段消掉、动态shape和多流仍需各自证据。

## 完整本地实现证据

- [固定实现 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/npugraph_ex/npugraph_ex/patterns/batch_matmul_transpose.py)（implementation）：1–317。
- [固定实现 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/npugraph_ex/npugraph_ex/patterns/batch_matmul_transpose.py)（implementation）：1–386。
