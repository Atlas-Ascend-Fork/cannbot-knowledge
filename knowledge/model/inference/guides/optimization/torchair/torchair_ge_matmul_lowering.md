---
type: Guide
title: GE矩阵乘：系数融合、转置与量化边界
description: 核对GE矩阵乘系数、转置和反向限制，并对照量化Matmul/GMM的Eager NZ分派、Meta输入和输出结构。
tags:
- task.implementation
- topic.graph_execution
status: draft
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/addmm.py
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/addmm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/baddbmm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/baddbmm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/bmm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/bmm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/matmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/matmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/matmul_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/matmul_backward.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/mm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/mm.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_linear.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_linear.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_batch_gather_matmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_batch_gather_matmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_quant_matmul_dequant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_quant_matmul_dequant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_quant_grouped_matmul_dequant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_quant_grouped_matmul_dequant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantGroupedMatmulDequantNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantGroupedMatmulDequantNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_quant_grouped_matmul_dequant.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/dynamic_output_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/dynamic_output_ops.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_apis.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_apis.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul.py
  role: implementation
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul.py
  role: implementation
created_at: '2026-11-10T09:04:08Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# GE矩阵乘：系数融合、转置与量化边界

## 版本与证据范围

固定TorchAir主线92e1e967bd35ebc37a442b4a969730bf3cf77a3c与发布快照7c6c754bed00c86ffaaa2a45cb7ac2724f058013。十组主线文件完整非空源码及发布完整AST/注释差异已审阅；五组AST相同，五组有差异，其中matmul的高rank分支是实际构图变化，其他为声明、等价布尔/range写法或文字。

本卡说明Converter及新增专节中的对应OpPlugin Eager/Meta合同，平台矩阵未知，保持draft与空平台。未执行上游、GE编译、NPU精度/梯度或性能实验；Support候选不代表通用产品支持。精度选择、融合和稀疏/量化数据格式还需核对对应IR及kernel。

## addmm的三个构图分支

函数先对非GE Tensor的alpha/beta用float比较0和1，再把mat1/mat2/self及alpha/beta提升为meta_outputs.dtype。Tensor形式系数不会在这些Python标志中被判为0或1，不能以样例值裁掉运行分支。

| 条件 | 图中操作与限制 |
| --- | --- |
| alpha被判为0 | 直接Mul(self,beta)，不创建MatMul；本层没有把self显式广播至矩阵乘输出shape，也没有独立的beta==0忽略self分支，需核对广播bias与特殊数值场景，不能只由数学公式推导完整语义。 |
| 提升后的self为FP16/BF16且rank1；或rank2、首维1且第二维等于mat2第二维 | 将self作为MatMulV2的bias；beta非1时先Mul(self,beta)，alpha非1时先Mul(mat1,alpha)，再MatMulV2(mat1,mat2,self,None)。rank1判断没有在本函数额外比较通道长度，rank2依赖symsize的Python比较；不由此认证任意动态bias。 |
| 其余 | MatMulV2(mat1,mat2,None,None)，按Meta类型映射改写mm_res.desc.dtype，然后**始终Mul(mm_res,alpha)**；beta为0直接返回该结果，为1再Add(self)，其他为AxpyV2(mm_res,self,beta)。源码注明FP32需要保留Mul，不能为消除小算子就任意删去或移入MatMul。 |

融合分支的beta==0仍先构造self*beta并作为bias，不能套用非融合分支跳过self的节点规则。系数乘在输入、bias或乘积后具有不同舍入位置；静态分支存在不证明收益或全值域数值等价已验证。

ge_dtype_to_ge_proto_dtype是_ge_dtype_to_ge_proto_dtype的导入别名，进行GE枚举到ProtoDataType映射，未知类型ValueError；它本身不生成数值Cast。主线比发布辅助函数多UINT16、UINT64、INT4映射，只是类型翻译分支差异，不给addmm自动增加这些kernel能力。

## baddbmm与普通矩阵乘不共享提升规则

baddbmm.default先以原batch1/batch2构造BatchMatMul，再分别Mul(乘积,alpha)和Mul(self,beta)，之后才把两项提升为Meta dtype并Add。没有addmm的零/一系数裁剪或bias融合，也没有在BatchMatMul之前统一输入dtype的同样逻辑；不能从最终Cast推导中间矩阵乘按目标精度计算。

| 入口 | 类型和节点选择 |
| --- | --- |
| bmm.default | 任一输入DT_INT8时RuntimeError；两输入按Meta dtype提升，然后BatchMatMul。 |
| mm.default | 任一输入DT_INT8时RuntimeError；直接MatMul(self,mat2,None)，没有本地Meta提升。 |
| matmul.default主线 | 任一输入DT_INT8时RuntimeError；任一rank>=3时两输入按Meta dtype提升并BatchMatMul，否则直接MatMul且无同样提升。 |
| matmul.default发布版 | 同样拒绝INT8，但之后始终MatMul，没有主线的高rank BatchMatMul分支；主线新增的Support声明不替代真实运行验证。 |
| npu_linear.default | 实际注册在torch.ops.npu命名空间；input/weight任一INT8时RuntimeError，直接MatMul(input,weight,bias,transpose_x1=False,transpose_x2=True)，没有统一Meta提升。报错中误写aten命名空间不能据此改变真实注册目标。 |

这些普通入口对INT8的准确拒绝不等于量化专用入口也被拒绝；不对所有dtype作平台或计算精度推断。

## matmul反向仅接受完整mask

matmul_backward.default要求mask长度2且两项都True，其他直接NotImplementedError。它为self/other的最后两轴交换构造INT64置换，然后grad_self=BatchMatMul(grad,Transpose(other))，grad_other=BatchMatMul(Transpose(self),grad)，原序返回。

本层没有为rank<2向量输入单独处理，也没有把广播batch维的梯度显式归约回原shape；三项数据输入和两个输出未按各Meta单独Cast。不能由该公式认证所有torch.matmul广播、向量或部分梯度场景。发布版与主线只在range列表构造写法不同，计算分支一致。

## LoRA与量化映射的参数只做透传

npu_batch_gather_matmul.default映射到AddLora(y,x,weightA=weight_a,weightB=weight_b,indices=indices,...)，不要按Pythonweight_b在前的签名把两权重对换。layer_idx默认0、scale默认0.001、y_offset默认0、y_slice_size默认-1；本层没有独立的越界、列表、dtype或输出别名校验，不能仅凭融合名认证稀疏选择、原地改写或收益。

npu_quant_matmul_dequant.default直接QuantMatmulDequant(x,quantized_weight,weight_scale,...)；npu_quant_grouped_matmul_dequant.default多传group_list并调用QuantGroupedMatmulDequant。bias、x_scale、x_offset、smooth_scale均原样传递，quant_mode默认pertoken并映射为x_quant_mode属性，没有本地完整的模式、分组边界、量化scale形状或数据格式检查，也没有显式前后Cast。

这两条映射不能替代完整量化配方：先确认实际权重编码、scale/offset含义、group_list合同与kernel支持，再测精度和性能；不能把默认字符串扩展成所有量化模式都可用。

## 量化Matmul/GMM的Eager与Meta补充

本节另核对OpPlugin主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`与发布`dedc316708372c9a8bfde4527abd2a94b74840f5`。两版Grouped包装去空白后相同，普通Matmul的生成配置和所述Meta分支也一致；不把共同已有的NZ路线记成主线新增能力。发布组合为ascend_26_0_pt28，主线软件配套未知，以下静态对照不证明两个组织快照已经组合运行。

### 浮点激活、量化权重与固定转置

`npu_quant_matmul_dequant`的Schema生成配置明确指定`aclnnQuantMatmulDequant`、`trans=true`，输出按`[x.size(0),weight_scale.size(0)]`和x dtype分配。本次读取的是构建生成配置，没有运行生成器或编译产物，不将缺少独立同名C++文件解释成API不存在。

`npu_quant_grouped_matmul_dequant`的手写Eager包装同样固定`trans=true`，按`[x.size(0),weight_scale.size(1)]`和x dtype分配。它识别真实storage中的FRACTAL_NZ、NZ_C0_4、NZ_C0_16，选择`aclnnQuantGroupedMatmulDequantWeightNZ`；其余选普通`aclnnQuantGroupedMatmulDequant`。NZ分支先缓存符号可用性检查，缺失时提示升级CANN，本函数没有自动转ND或回退其他GMM实现。符号存在仍不证明设备、shape与精度组合可用。

两版GE Converter本身没有NZ符号分派，也没有显式传transpose_weight；所调用生成GE接口的默认`transpose_weight=True`与Eager固定值一致。不要把Converter没有Transpose节点解释成权重按[K,N]读取，或将C++的运行库符号检查当作GE构图检查。

### Meta限定的窄shape/dtype合同

| 入口 | Meta输入与轴关系 | 输出 |
| --- | --- | --- |
| 普通Matmul-Dequant | x为FP16[M,K]；INT8权重[N,K]；FP32 weight_scale[N]，K与N分别对应 | FP16[M,N] |
| GroupedMatmul-Dequant | x为FP16[M,K]；INT8权重[G,N,K]；FP32 weight_scale[G,N]，x.K=W.K、两个scale轴对应G/N | FP16[M,N] |

Grouped Meta最后一条K比较实际读取权重shape[2]，报错文字却写shape[1]；定位时看表达式。它不通过List[Tensor]分配多个结果，不能套用`npu_grouped_matmul`的split_item和输出列表协议，也不能把scale换成打包INT64或E8M0后仅凭同形状推导合法。

两版Meta都将结果device设为meta，且没有在该函数检查group_list内容/完整dtype、可选bias及激活量化参数的全部约束。生成GE IrDef另列group_list INT64、bias INT32、x_scale/x_offset FP32、smooth_scale FP16；这是IR声明，不替代真实输入值、分组和kernel验收。C++包装没有同样的逐项FP16/INT8/FP32前置检查，不代表Eager允许任意其他类型。quant_mode缺省pertoken、None或其他字符串也不能仅由Optional签名认定为可运行模式。

### 参考与性能验收

主线选定Grouped测试只有两个方法，均无条件skip；名称分别为动态pertoken和静态pertensor，目标装饰器写Ascend310P。参考先构造[G,K,N]，调用前真实transpose(1,2).contiguous()为[G,N,K]，group_list样例[7,29,31,64]按累计边界切M；这些是该参考的表示，不是完整产品支持表或所有分组表示的证明。两用例均无真实NZ验收，装饰器不能证明NZ分支在310P已运行。

迁移时先区分本组浮点激活量化融合与`npu_quant_matmul`的已量化输入协议，逐项对齐权重转置、scale轴、group_list和有效token区；再分别验证pertoken/pertensor、可选平滑、bias和offset。测量应包含激活量化、权重准备/格式转换、完整GMM和输出反量化，不能只用单一ACLNN名声称消除了全部中间开销。本次没有运行测试、GE或设备实验，没有新增verified。

## 验证与关联

按FX准确重载检查rank、Meta dtype、alpha/beta类型与值、bias广播和symsize、是否生成Mul/MatMulV2/BatchMatMul、反向mask和广播归约；再核对量化与LoRA参数的实际ABI。out拒绝的“before pytorch 2.1.0/might be supported”报错只是该快照文字，不是版本承诺。本文没有执行上述实验。

- [Converter实现与类型提升](torchair_converter_implementation.md)
- [ATen文档层精度限制](torchair_aten_constraint_review.md)

## 准确注册与拒绝重载

表中有构图分支仍受正文条件限制；不能从单个文件的重载清单推导其他后端或高层模块的完整能力。

| 主题 | 有构图分支的准确入口 | 无条件拒绝入口及异常 |
| --- | --- | --- |
| addmm | `torch.ops.aten.addmm.default` | `torch.ops.aten.addmm.out` (RuntimeError) |
| baddbmm | `torch.ops.aten.baddbmm.default` | `torch.ops.aten.baddbmm.out` (NotImplementedError) |
| bmm | `torch.ops.aten.bmm.default` | `torch.ops.aten.bmm.out` (NotImplementedError) |
| matmul | `torch.ops.aten.matmul.default` | `torch.ops.aten.matmul.out` (NotImplementedError) |
| matmul_backward | `torch.ops.aten.matmul_backward.default` | 无无条件拒绝壳；仍受正文参数边界限制 |
| mm | `torch.ops.aten.mm.default` | `torch.ops.aten.mm.out` (NotImplementedError) |
| npu_linear | `torch.ops.npu.npu_linear.default` | 无无条件拒绝壳；仍受正文参数边界限制 |
| npu_batch_gather_matmul | `torch.ops.npu.npu_batch_gather_matmul.default` | 无无条件拒绝壳；仍受正文参数边界限制 |
| npu_quant_matmul_dequant | `torch.ops.npu.npu_quant_matmul_dequant.default` | 无无条件拒绝壳；仍受正文参数边界限制 |
| npu_quant_grouped_matmul_dequant | `torch.ops.npu.npu_quant_grouped_matmul_dequant.default` | 无无条件拒绝壳；仍受正文参数边界限制 |

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/addmm.py)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/addmm.py)（implementation）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/baddbmm.py)（implementation）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/baddbmm.py)（implementation）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/bmm.py)（implementation）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/bmm.py)（implementation）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/matmul.py)（implementation）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/matmul.py)（implementation）
- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/matmul_backward.py)（implementation）
- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/matmul_backward.py)（implementation）
- [固定来源 11](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/aten/mm.py)（implementation）
- [固定来源 12](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/aten/mm.py)（implementation）
- [固定来源 13](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_linear.py)（implementation）
- [固定来源 14](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_linear.py)（implementation）
- [固定来源 15](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_batch_gather_matmul.py)（implementation）
- [固定来源 16](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_batch_gather_matmul.py)（implementation）
- [固定来源 17](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_quant_matmul_dequant.py)（implementation）
- [固定来源 18](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_quant_matmul_dequant.py)（implementation）
- [固定来源 19](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_quant_grouped_matmul_dequant.py)（implementation）
- [固定来源 20](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_quant_grouped_matmul_dequant.py)（implementation）
- [固定来源 21](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 22](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/converter_utils.py)（implementation）
- [固定来源 23](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 24](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/utils.py)（implementation）
- [固定来源 25](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py)（implementation）
- [固定来源 26](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/ge/_ge_graph.py)（implementation）

## 补充实现证据

- [固定来源 1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/QuantGroupedMatmulDequantNpuOpApi.cpp)（implementation）

- [固定来源 2](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/QuantGroupedMatmulDequantNpuOpApi.cpp)（implementation）

- [固定来源 3](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 4](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）

- [固定来源 5](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定来源 6](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/python/meta/_meta_registrations.py)（implementation）

- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_quant_grouped_matmul_dequant.py)（implementation）

- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/npu_quant_grouped_matmul_dequant.py)（implementation）

- [固定来源 9](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [固定来源 10](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)（implementation）

- [固定来源 11](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/test/test_base_ops/test_quant_grouped_matmul_dequant.py)（example）

## 普通GMM的GE输出列表如何确定

这里是普通`npu_grouped_matmul`，与前文`QuantGroupedMatmulDequant`的单Tensor结果分开。两版`ge_apis`在raw API之后导入dynamic_output_ops；普通GMM的default/List Converter把split_item及已处理的输入送入这层包装。包装器的输出数量规则相同：

| split_item | `size_of_y`来源 |
| --- | --- |
| 0或1，group_list非None | `group_list.symsize[0]`，读取第一维规格，不读取边界Tensor的内容 |
| 0或1，group_list为None | `len(x)`，本地不是`len(weight)` |
| 2或3 | 固定1，仍返回列表 |
| 其他值 | 保持初始化的0；本包装器没有显式非法值报错分支 |

该规则只说明本地构图行为，不放宽公开GMM的列表长度、分组与split_item约束；尤其文档按合法输入描述的输出数量，不能替代这里的实际取值表达式。raw `_GroupedMatmul`按`range(... + size_of_y)`逐项添加y描述符和GE Tensor，再返回列表，并不根据运行后数值重新增长列表，也没有在这段代码验证数量为正。输出数量与Tensor内部动态shape是不同合同。

两版包装在tuning_config为None时改为`[0]`；它没有独立校验x/weight/分组数量一致性。原始GroupedMatmul IR、后续[量化转置与NZ图检查](torchair_ge_quant_matmul_graph_rewrites.md)及设备Kernel仍各有职责。本节仅静态核对输出数量和实际调用，未运行GMM或推导收益。

## 实现来源

- [固定实现1](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/dynamic_output_ops.py)：25–100。
- [固定实现2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/dynamic_output_ops.py)：24–68。
- [固定实现3](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_apis.py)：13–15。
- [固定实现4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_apis.py)：13–15。
- [固定实现5](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)：90181–90189。
- [固定实现6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/auto_generated_ge_raw_ops.py)：79391–79399。
- [固定实现7](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul.py)：409–437。
- [固定实现8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/python/torchair/_ge_concrete_graph/ge_converter/custom/grouped_matmul.py)：333–340。
