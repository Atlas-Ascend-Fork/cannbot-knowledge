---
type: Guide
title: GE算术转换：类型提升与舍入边界
description: 区分算术与选择转换的精度顺序、两版截断除法、符号与掩码补充入口及out别名缺口，逐项保留拒绝重载。
tags:
- task.implementation
- topic.graph_execution
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/add.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/add.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sub.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sub.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/rsub.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/rsub.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/mul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/mul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/div.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/div.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/floor_divide.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/floor_divide.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/remainder.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/remainder.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/pow.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/pow.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/addcdiv.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/addcdiv.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/addcmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/addcmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/neg.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/neg.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/abs.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/abs.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/reciprocal.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/reciprocal.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/rsqrt.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/rsqrt.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sqrt.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sqrt.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/exp.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/exp.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/expm1.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/expm1.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/log.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/log.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/log10.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/log10.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/log1p.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/log1p.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/log2.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/log2.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/clamp.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/clamp.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/clamp_min.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/clamp_min.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/round.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/round.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/ceil.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/ceil.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/floor.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/floor.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/maximum.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/maximum.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/minimum.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/minimum.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/where.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/where.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sign.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sign.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sgn.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sgn.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/isinf.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/isinf.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/nan_to_num.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/nan_to_num.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/check_platform.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_sym_log2.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_sym_log2.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/bitwise_right_shift_.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/bitwise_right_shift_.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/tril.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/tril.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/triu.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/triu.py
  role: implementation
created_at: '2026-11-10T06:58:25Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE算术转换：类型提升与舍入边界

## 固定版本与证据强度

依据TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c和发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013的准确Converter、导入绑定及辅助函数。逐个审阅主线全部非空源码，发布版以完整AST比对、全部AST差异和注释差异复核；不把语法相同写成字节相同。两个快照分开管理，不推导与任意TorchNPU主线配套。

本文是构图层静态合同，未执行上游代码、smoke、GE编译、NPU数值或性能测试；没有覆盖整卡的产品矩阵，保持draft和空平台。declare_supported列出的shape、dtype、混合类型及标量仅是声明/测试输入候选，不是运行通过记录，也不是完整输入域或硬件支持表。Meta规格、显式Cast、GE后续类型处理及实际kernel仍需分别核对。

dtype_promote按调用方指定的target_dtype处理：GE Tensor在dtype不同时插Cast，torch.Tensor也仅在类型不同时转Cast，非Tensor转对应dtype的Const；它本身不计算PyTorch公共类型，也不自动把所有输入扩成相同shape。单输入返回对象，多输入返回tuple。需要动态运行值时不能拿Python标量Const替代；广播与真实数值正确性不由此函数独立证明。

## 加减乘与系数的计算顺序

add.Tensor和add.Scalar在alpha为非Tensor且等于1时，先按meta_outputs.dtype处理两个输入，再发Add；其他情况将alpha也转相同dtype并发AxpyV2。alpha是Tensor时即使样例数值为1也不走Python常量快捷分支。这个分支只说明IR选择，源码“better performance”注释不构成当前模型收益证据。

sub.Tensor先在other原dtype中构造alpha常量并Mul（alpha!=1时），之后才把self/other按输出dtype提升并Sub；不能等同于“先将所有输入提升到输出精度再乘alpha”。sub.Scalar是无条件RuntimeError壳，其“before pytorch 2.1.0”消息不表示在较新版本自动启用。rsub.Tensor按相反操作数顺序Sub，非1系数先乘self。

rsub.Scalar按is_arch35()分流：浮点输出FP32/FP16/BF16且alpha非Tensor时，用取负系数的Axpy；INT8/INT32/INT64输出用AxpyV2，alpha先按输出dtype转换并与同dtype的-1相乘；其他类型用Mul再Sub。非该分支调用Sxpy并传原alpha，不能未经核对Sxpy合同就将其替换为另一种运算。辅助判定读取当前设备名字子串：发布版识别Ascend910_95、Ascend950，主线另外识别Ascend350；仅捕获ImportError，不是通用SoC枚举、所有设备错误回退或任意产品能力证明。

mul.Tensor的两个GE bool Tensor先转UINT8计算Mul，再按Meta输出转换；self为FP16/BF16 Tensor而other为非Tensor时改用Muls属性再处理输出dtype。mul.Scalar则直接按Meta处理两个输入后Mul，不自动共享前一个函数的全部快捷分支。两版mul的AST差异只有说明字符串改注释及排版，所审阅计算分支相同。

addcdiv.default和addcmul.default把self、tensor1、tensor2及value一并转Meta输出dtype，再交Addcdiv/Addcmul；有单个GE节点不表示设备只启动一次、任意融合成立或所有整型及非有限值语义均已验证。

## 除法、余数与幂的版本边界

| 准确分支 | 静态实现与需要核对的边界 |
| --- | --- |
| div.Tensor、div.Scalar | 两输入按Meta输出dtype处理，再RealDiv。不能用输入整数类型推断输出仍为整数。 |
| div.Tensor_mode | floor走FloorDiv；主线trunc直接TruncateDiv。发布版trunc先RealDiv，输出dtype为INT64/BOOL/INT16时还经FP32 Cast→Trunc→Cast回原dtype，其余直接Trunc。此差异可能影响精度和图结构，不能将两版截断路径当成相同；本次未测试误差。其他rounding_mode值与None都进入RealDiv，函数本层没有完整字符串合法性校验。 |
| floor_divide.default | 输入按Meta转换，再FloorDiv；Scalar和out壳直接拒绝。不能从Tensor_mode接收Python标量推定准确的Scalar overload也实现。 |
| remainder.Tensor | 仅输入dtype不同时按Meta转换，再FloorMod；相同类型不在本层强制再转Meta。Scalar与Scalar_Tensor分别明确转换两个参数，再FloorMod；负数、零除数和广播按真实调用验收。 |
| pow.Tensor_Tensor、Tensor_Scalar、Scalar | 底数和指数一并按Meta输出dtype处理，再Pow；不是所有Python标量幂/复数/输出重载共享的实现。整数指数的提升及大整数精度不能由统一Cast认证。 |

## 一元函数、裁剪和输出对象

| 入口 | 此快照Converter的显式处理 |
| --- | --- |
| neg.default、sign.default | 分别直接Neg、Sign；未在本层统一按Meta Cast。 |
| abs.default | UINT8直接返回输入对象，其余Abs；不能因数值无变化忽略图中输出与输入的别名关系。 |
| reciprocal.default | bool和UINT8/INT8/INT16/INT32/INT64先Cast到FP32再Reciprocal；其余直接Reciprocal，并非所有类型均以Meta输出dtype选择计算精度。 |
| sqrt.default、rsqrt.default | sqrt先按Meta处理输入再Sqrt；rsqrt直接Rsqrt，不据函数名字推导相同提升规则。 |
| exp.default、expm1.default、log.default、log1p.default | exp仅显式处理bool的Meta转换；其余入口分别直接Exp/Expm1/Log/Log1p，不把本层缺Cast等同于底层最终结果已确认。 |
| log2.default、log10.default | 调用Log并分别设base=2/10；不是在Python中计算输入数值。 |
| floor.default、ceil.default、round.default | floor/ceil先Floor/Ceil再把输出转Meta dtype；round直接Round，decimals overload明确未实现。 |
| clamp.default、clamp.Tensor | min和max都None时拒绝；缺少的界限从输入原dtype生成，之后self及两界限按Meta dtype处理，再ClipByValueV2。整数INT8/UINT8/INT16/INT32/INT64用iinfo极值，其他类型用正负inf。未在本层显式检查min<max，不据此覆盖[文档能力表](torchair_aten_constraint_review.md)的限制。 |
| clamp_min.default | 上界取输入原dtype的最大值，再转Meta；准确clamp_min.Tensor仍是拒绝壳，不能由clamp.Tensor推导它也实现。 |
| maximum.default、minimum.default | maximum按Meta处理后Maximum；minimum对bool输出直接Mul，对UINT8/INT16先转INT32计算Minimum再转回，其余按Meta后Minimum。此bool分支与mul.Tensor的UINT8中转不同，不能互相代换。 |
| where.self | 仅self/other dtype不同时按Meta转换，condition原样传SelectV2；所有标量where overload、单输入where.default和self_out都拒绝。不根据文档只提“动态单输入”就断定此准确内置单输入Converter的静态路径实现。 |
| sgn.default | 原码仅以dtype==28触发“complex”拒绝消息，其余Sign；这个整数判定不构成覆盖所有复数枚举的类型检查证据。 |
| isinf.default、nan_to_num.default | IsInf与NanToNum直接调用；后者将nan/posinf/neginf（含None）原样作为属性交给GE，不在此层认证所有默认替换值或dtype。 |

expm1.out和nan_to_num.out没有无条件报错，但将局部变量out重新赋为新GE结果，并未读取传入out。**本层“有返回值”不足以证明PyTorch out写回、对象身份与别名合同**；如外围函数化/输出绑定负责写回，仍需按真实图单独核对，不能把这两项简单列为完整out支持。其余直接拒绝重载逐项列在下表。

## 优化与排错使用方法

先保存准确FX overload、两个操作数dtype及Meta输出dtype，再比较生成图的Cast、Const、Axpy/Muls、RealDiv/TruncateDiv和Clip节点顺序。构图节点减少只作为候选解释；实际收益需结合目标版本的融合结果和性能测量。验证应包含混合整浮点、bool、标量与Tensor系数、反向减法、正负除数/非整商、大整数、非有限值、广播以及out别名。本次未执行这些实验。

通用开发方法见[Converter开发](torchair_converter_implementation.md)，比较/逻辑规则见[GE比较与逻辑转换](torchair_ge_comparison_lowering.md)，纯占位文件另见[GE未实现overload](torchair_ge_unimplemented_overloads.md)。

## 精确overload与直接拒绝清单

每格使用完整torch.ops标识；有构图分支仍须满足上文条件。拒绝栏仅指实际选中此内置Converter后的无条件异常，不否定高层函数可以经分解、其他overload或其他后端执行。两快照本表身份和直接拒绝类型相同；字符串中的旧PyTorch版本提示只保留为诊断消息，不当作当前兼容矩阵。

| 文件主题 | 有构图分支的准确入口 | 无条件拒绝的准确入口及异常 |
| --- | --- | --- |
| add | `torch.ops.aten.add.Tensor`、`torch.ops.aten.add.Scalar` | NotImplementedError：`torch.ops.aten.add.out`、`torch.ops.aten.add.Scalar_out`、`torch.ops.aten.add.str`、`torch.ops.aten.add.int`、`torch.ops.aten.add.complex`、`torch.ops.aten.add.float`、`torch.ops.aten.add.int_complex`、`torch.ops.aten.add.complex_int`、`torch.ops.aten.add.float_complex`、`torch.ops.aten.add.complex_float`、`torch.ops.aten.add.int_float`、`torch.ops.aten.add.float_int`、`torch.ops.aten.add.default` |
| sub | `torch.ops.aten.sub.Tensor` | RuntimeError：`torch.ops.aten.sub.Scalar`、`torch.ops.aten.sub.out`、`torch.ops.aten.sub.Scalar_out`、`torch.ops.aten.sub.int`、`torch.ops.aten.sub.complex`、`torch.ops.aten.sub.float`、`torch.ops.aten.sub.int_complex`、`torch.ops.aten.sub.complex_int`、`torch.ops.aten.sub.float_complex`、`torch.ops.aten.sub.complex_float`、`torch.ops.aten.sub.int_float`、`torch.ops.aten.sub.float_int`、`torch.ops.aten.sub.default` |
| rsub | `torch.ops.aten.rsub.Tensor`、`torch.ops.aten.rsub.Scalar` | NotImplementedError：`torch.ops.aten.rsub.Tensor_out`、`torch.ops.aten.rsub.Scalar_out` |
| mul | `torch.ops.aten.mul.Tensor`、`torch.ops.aten.mul.Scalar` | RuntimeError：`torch.ops.aten.mul.out`、`torch.ops.aten.mul.Scalar_out`、`torch.ops.aten.mul.int`、`torch.ops.aten.mul.complex`、`torch.ops.aten.mul.float`、`torch.ops.aten.mul.int_complex`、`torch.ops.aten.mul.complex_int`、`torch.ops.aten.mul.float_complex`、`torch.ops.aten.mul.complex_float`、`torch.ops.aten.mul.int_float`、`torch.ops.aten.mul.float_int`、`torch.ops.aten.mul.default` |
| div | `torch.ops.aten.div.Tensor`、`torch.ops.aten.div.Scalar`、`torch.ops.aten.div.Tensor_mode` | AssertionError：`torch.ops.aten.div.Scalar_mode`、`torch.ops.aten.div.out`、`torch.ops.aten.div.out_mode`、`torch.ops.aten.div.Scalar_out`、`torch.ops.aten.div.Scalar_mode_out`、`torch.ops.aten.div.int`、`torch.ops.aten.div.complex`、`torch.ops.aten.div.float`、`torch.ops.aten.div.default` |
| floor_divide | `torch.ops.aten.floor_divide.default` | NotImplementedError：`torch.ops.aten.floor_divide.Scalar`、`torch.ops.aten.floor_divide.out` |
| remainder | `torch.ops.aten.remainder.Tensor`、`torch.ops.aten.remainder.Scalar`、`torch.ops.aten.remainder.Scalar_Tensor` | RuntimeError：`torch.ops.aten.remainder.Tensor_out`、`torch.ops.aten.remainder.Scalar_out`、`torch.ops.aten.remainder.Scalar_Tensor_out`、`torch.ops.aten.remainder.int`、`torch.ops.aten.remainder.float`、`torch.ops.aten.remainder.int_float`、`torch.ops.aten.remainder.float_int`、`torch.ops.aten.remainder.default` |
| pow | `torch.ops.aten.pow.Tensor_Tensor`、`torch.ops.aten.pow.Tensor_Scalar`、`torch.ops.aten.pow.Scalar` | NotImplementedError：`torch.ops.aten.pow.Scalar_out`、`torch.ops.aten.pow.Tensor_Scalar_out`、`torch.ops.aten.pow.Tensor_Tensor_out`、`torch.ops.aten.pow.int`、`torch.ops.aten.pow.complex`、`torch.ops.aten.pow.float`、`torch.ops.aten.pow.int_float`、`torch.ops.aten.pow.float_int`、`torch.ops.aten.pow.float_complex`、`torch.ops.aten.pow.complex_float`、`torch.ops.aten.pow.Scalar_Scalar`、`torch.ops.aten.pow.int_to_int` |
| addcdiv | `torch.ops.aten.addcdiv.default` | NotImplementedError：`torch.ops.aten.addcdiv.out` |
| addcmul | `torch.ops.aten.addcmul.default` | NotImplementedError：`torch.ops.aten.addcmul.out` |
| neg | `torch.ops.aten.neg.default` | NotImplementedError：`torch.ops.aten.neg.out`、`torch.ops.aten.neg.int`、`torch.ops.aten.neg.float`、`torch.ops.aten.neg.complex`、`torch.ops.aten.neg.Scalar` |
| abs | `torch.ops.aten.abs.default` | RuntimeError：`torch.ops.aten.abs.out` |
| reciprocal | `torch.ops.aten.reciprocal.default` | NotImplementedError：`torch.ops.aten.reciprocal.out` |
| rsqrt | `torch.ops.aten.rsqrt.default` | NotImplementedError：`torch.ops.aten.rsqrt.out` |
| sqrt | `torch.ops.aten.sqrt.default` | RuntimeError：`torch.ops.aten.sqrt.out`、`torch.ops.aten.sqrt.int`、`torch.ops.aten.sqrt.float`、`torch.ops.aten.sqrt.complex`、`torch.ops.aten.sqrt.Scalar` |
| exp | `torch.ops.aten.exp.default` | RuntimeError：`torch.ops.aten.exp.out`、`torch.ops.aten.exp.int`、`torch.ops.aten.exp.float`、`torch.ops.aten.exp.complex`、`torch.ops.aten.exp.Scalar` |
| expm1 | `torch.ops.aten.expm1.default`、`torch.ops.aten.expm1.out` | NotImplementedError：`torch.ops.aten.expm1.int`、`torch.ops.aten.expm1.float`、`torch.ops.aten.expm1.Scalar` |
| log | `torch.ops.aten.log.default` | RuntimeError：`torch.ops.aten.log.out`、`torch.ops.aten.log.int`、`torch.ops.aten.log.float`、`torch.ops.aten.log.complex`、`torch.ops.aten.log.Scalar`、`torch.ops.aten.log.int_int`、`torch.ops.aten.log.float_float`、`torch.ops.aten.log.complex_complex`、`torch.ops.aten.log.int_float`、`torch.ops.aten.log.float_int`、`torch.ops.aten.log.int_complex`、`torch.ops.aten.log.complex_int`、`torch.ops.aten.log.float_complex`、`torch.ops.aten.log.complex_float`、`torch.ops.aten.log.Scalar_Scalar` |
| log10 | `torch.ops.aten.log10.default` | NotImplementedError：`torch.ops.aten.log10.out`、`torch.ops.aten.log10.int`、`torch.ops.aten.log10.float`、`torch.ops.aten.log10.complex`、`torch.ops.aten.log10.Scalar` |
| log1p | `torch.ops.aten.log1p.default` | NotImplementedError：`torch.ops.aten.log1p.out`、`torch.ops.aten.log1p.int`、`torch.ops.aten.log1p.float`、`torch.ops.aten.log1p.Scalar` |
| log2 | `torch.ops.aten.log2.default` | NotImplementedError：`torch.ops.aten.log2.out` |
| clamp | `torch.ops.aten.clamp.default`、`torch.ops.aten.clamp.Tensor` | RuntimeError：`torch.ops.aten.clamp.out`、`torch.ops.aten.clamp.Tensor_out` |
| clamp_min | `torch.ops.aten.clamp_min.default` | NotImplementedError：`torch.ops.aten.clamp_min.Tensor`、`torch.ops.aten.clamp_min.out`、`torch.ops.aten.clamp_min.Tensor_out` |
| round | `torch.ops.aten.round.default` | NotImplementedError：`torch.ops.aten.round.decimals`、`torch.ops.aten.round.out`、`torch.ops.aten.round.decimals_out`、`torch.ops.aten.round.int`、`torch.ops.aten.round.float`、`torch.ops.aten.round.Scalar` |
| ceil | `torch.ops.aten.ceil.default` | RuntimeError：`torch.ops.aten.ceil.out`、`torch.ops.aten.ceil.int`、`torch.ops.aten.ceil.float`、`torch.ops.aten.ceil.Scalar` |
| floor | `torch.ops.aten.floor.default` | NotImplementedError：`torch.ops.aten.floor.out`、`torch.ops.aten.floor.int`、`torch.ops.aten.floor.float`、`torch.ops.aten.floor.Scalar` |
| maximum | `torch.ops.aten.maximum.default` | NotImplementedError：`torch.ops.aten.maximum.out` |
| minimum | `torch.ops.aten.minimum.default` | RuntimeError：`torch.ops.aten.minimum.out` |
| where | `torch.ops.aten.where.self` | RuntimeError：`torch.ops.aten.where.ScalarOther`、`torch.ops.aten.where.ScalarSelf`、`torch.ops.aten.where.Scalar`、`torch.ops.aten.where.default`、`torch.ops.aten.where.self_out` |
| sign | `torch.ops.aten.sign.default` | NotImplementedError：`torch.ops.aten.sign.out` |
| sgn | `torch.ops.aten.sgn.default` | RuntimeError：`torch.ops.aten.sgn.out` |
| isinf | `torch.ops.aten.isinf.default` | NotImplementedError：`torch.ops.aten.isinf.out`、`torch.ops.aten.isinf.float`、`torch.ops.aten.isinf.complex` |
| nan_to_num | `torch.ops.aten.nan_to_num.default`、`torch.ops.aten.nan_to_num.out` | 无无条件拒绝壳；仍有输出别名等边界 |

## 符号Log2、右移与三角掩码的补充入口

另核对同两固定快照的四组完整源码，AST均相同。torch._sym_log2仅当Torch属性可访问且非None时注册：捕获ImportError/AttributeError后跳过；有绑定时直接ge.Log(self,base=2)。不能把兼容跳过当全局API能力否定，也不能据Tensor注解认证所有Python符号标量输入已支持。

torch.ops.aten.bitwise_right_shift_.Tensor直接RightShift(self,other)，没有本地额外Assign或统一Meta提升；带下划线及Schema的Tensor(a!)不足以独立证明原地别名正确，需要外围函数化验证。准确Tensor_Scalar重载仍无条件NotImplementedError，不能从Tensor版本推导标量版本可用。

torch.ops.aten.tril.default和torch.ops.aten.triu.default分别直传Tril/Triu及diagonal属性，默认0，没有本地额外Cast、rank或diagonal值域完整检查。tril.out为NotImplementedError，triu.out为RuntimeError；BOOL/FP16等Support只给候选，不构成所有布局、动态轴或产品实测表。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/add.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/add.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sub.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sub.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/rsub.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/rsub.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/mul.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/mul.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/div.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/div.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/floor_divide.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/floor_divide.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/remainder.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/remainder.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/pow.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/pow.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/addcdiv.py)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/addcdiv.py)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/addcmul.py)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/addcmul.py)（implementation）
- [固定来源 21](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/neg.py)（implementation）
- [固定来源 22](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/neg.py)（implementation）
- [固定来源 23](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/abs.py)（implementation）
- [固定来源 24](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/abs.py)（implementation）
- [固定来源 25](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/reciprocal.py)（implementation）
- [固定来源 26](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/reciprocal.py)（implementation）
- [固定来源 27](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/rsqrt.py)（implementation）
- [固定来源 28](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/rsqrt.py)（implementation）
- [固定来源 29](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sqrt.py)（implementation）
- [固定来源 30](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sqrt.py)（implementation）
- [固定来源 31](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/exp.py)（implementation）
- [固定来源 32](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/exp.py)（implementation）
- [固定来源 33](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/expm1.py)（implementation）
- [固定来源 34](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/expm1.py)（implementation）
- [固定来源 35](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/log.py)（implementation）
- [固定来源 36](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/log.py)（implementation）
- [固定来源 37](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/log10.py)（implementation）
- [固定来源 38](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/log10.py)（implementation）
- [固定来源 39](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/log1p.py)（implementation）
- [固定来源 40](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/log1p.py)（implementation）
- [固定来源 41](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/log2.py)（implementation）
- [固定来源 42](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/log2.py)（implementation）
- [固定来源 43](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/clamp.py)（implementation）
- [固定来源 44](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/clamp.py)（implementation）
- [固定来源 45](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/clamp_min.py)（implementation）
- [固定来源 46](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/clamp_min.py)（implementation）
- [固定来源 47](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/round.py)（implementation）
- [固定来源 48](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/round.py)（implementation）
- [固定来源 49](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/ceil.py)（implementation）
- [固定来源 50](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/ceil.py)（implementation）
- [固定来源 51](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/floor.py)（implementation）
- [固定来源 52](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/floor.py)（implementation）
- [固定来源 53](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/maximum.py)（implementation）
- [固定来源 54](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/maximum.py)（implementation）
- [固定来源 55](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/minimum.py)（implementation）
- [固定来源 56](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/minimum.py)（implementation）
- [固定来源 57](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/where.py)（implementation）
- [固定来源 58](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/where.py)（implementation）
- [固定来源 59](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sign.py)（implementation）
- [固定来源 60](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sign.py)（implementation）
- [固定来源 61](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/sgn.py)（implementation）
- [固定来源 62](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/sgn.py)（implementation）
- [固定来源 63](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/isinf.py)（implementation）
- [固定来源 64](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/isinf.py)（implementation）
- [固定来源 65](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/nan_to_num.py)（implementation）
- [固定来源 66](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/nan_to_num.py)（implementation）
- [固定来源 67](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 68](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_utils/check_platform.py)（implementation）
- [固定来源 69](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 70](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 71](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_utils/check_platform.py)（implementation）
- [固定来源 72](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/_sym_log2.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/_sym_log2.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/bitwise_right_shift_.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/bitwise_right_shift_.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/tril.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/tril.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/triu.py)（implementation）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/triu.py)（implementation）
