---
type: Guide
title: GE Converter 构图：TensorSpec、类型、常量与控制边
description: 区分图 Tensor 与 Meta 描述，说明 Cast/Const/Clone 和 dependencies 对存储及执行次序的作用。
tags:
- task.optimization
- topic.graph_execution
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ge/tensorspec.md
  role: primary
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ge/Cast.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ge/Clone.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ge/Const.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ge/datatype.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ge/format.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ge/tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/graph_failed_cases.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py
  role: supporting
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ge/tensorspec.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ge/Cast.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ge/Clone.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ge/Const.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ge/tensor.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ge/datatype.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ge/format.md
  role: constraint
- resource: https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md
  role: constraint
created_at: '2026-11-09T02:51:24Z'
updated_at: "2026-11-14T08:44:18Z"
platforms:
- a2
- a3
- '950'
---

# GE Converter 构图：TensorSpec、类型、常量与控制边

## 版本与范围

依据 TorchAir 固定发布子模块 `7c6c754bed00c86ffaaa2a45cb7ac2724f058013`。该提交属于 ascend_26_0_pt28 的固定来源组合；不是所有历史或主线版本的通用契约。本卡选取来源支持的 A2/A3 推理范围，其他产品和特殊参数另行核对。

## 对象层次

torchair.ge.Tensor 是图中输入/输出描述，可查询 index、dtype、rank；TensorSpec 是 Meta 得到的输出规格，另有 size。它们不是已经在设备上求值的普通 torch.Tensor，不能在 Converter 里读取其运行时数据作为 Python 分支条件。

DataType 是 GE dtype 枚举，Format 是存储布局枚举，不能把两者数字编码或 torch dtype 混用。枚举中存在 FP8/FP4/NZ 不等于目标硬件和每个算子都支持，实际类型与格式仍由算子契约决定。

## 构图节点

ge.Const(v,dtype=None,node_name=None,readable=True) 在构图时固化值；有精确类型需求时显式 dtype，不依赖宽泛的“默认整型”说明。readable 只控制图上记录值的可读属性，不让常量变为动态输入。

ge.Cast(x,dst_type=...) 生成类型转换节点；ge.Clone(x,dependencies=[...]) 返回图上的 TensorMove 拷贝节点。对于 out-of-place 算子的 Converter，需要独立存储时不能直接返回原输入；反之也不能为消除拷贝而破坏别名/原地语义。

dependencies 是控制边列表，要求节点在指定依赖后执行，不是额外数值输入或 record_stream 生命周期标记。图内节点名必须唯一。以 Clone 在 indices/updates 后执行为例，它确保拷贝发生顺序，但原始数据是否可能被其他节点改写仍需完整图依赖核验。

## 核验

比较 Meta 的 shape/dtype、GE 节点顺序和输出结构；覆盖共享存储、原地更新和多次调用。Constant 的值、输入的符号维度与设备数据分别检查，避免在构图阶段把动态量固化。

- [原生自定义节点接口](../../../apis/torchair/ge_custom_op.md)


## 验证边界

分别核对实际软件版本、配置生效日志/图结构、输出与存储语义，再比较同输入的稳态耗时。本文为固定文档和静态接口审阅，没有执行上游代码、NPU 数值或性能实验。

- [软件栈来源与适用性](../../../concepts/frameworks/ascend_software_stack_baselines.md)

## 推导不一致的诊断入口

出现 dtype 冲突、输出字节数不足或集合通信后的 Transpose rank 错误时，先比较 Meta/GE 的首个规格分歧，再选择 Cast、Reshape 或修复 Meta；不要只按末端报错节点添加转换。

- [dtype、AllGather shape 与输出存储案例](ge_shape_dtype_failure_diagnosis.md)

## 主线 TensorSpec.size 的静态条件

固定主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的 TensorSpec 实现先保存 Meta 的符号 size，只有能把每一维转换成固定整数时才提供 size；动态规格访问 size 会抛出断言。rank 来自符号维度数量，不代表每维已知。贡献说明中的“不要从输入 Tensor 读取 shape”与 TensorSpec 静态 size 属性应分别理解，不能用它把 dynamic=True 的符号形状强制整数化。

dtype/rank/size 在实现中是属性，不是文档占位类中示意的可执行方法签名；按实际接口读取。本文仅静态查看实现，不把能构造 TensorSpec 或枚举包含某 dtype 视为硬件运算支持证据。

## 主线构图接口与常量类型

TorchAir主线 `92e1e967bd35ebc37a442b4a969730bf3cf77a3c` 的Cast、Clone、Const、Tensor、DataType与Format页面保留上述构图契约；主线总览列A2/A3/950推理。这是前端图描述的范围，仍不能把枚举中列有FP4、FP8或某个Format当作目标算子支持证明。

主线Const实现拒绝以GE Tensor作为常量值。dtype=None时，torch.Tensor按自身dtype推导，其他值先经数组类型推导；并非文档“默认为整型”可概括所有输入。需要固定精度时显式指定DataType，并核对生成的Const描述与数值。不能把图中动态Tensor直接包装成Const来绕开Converter的动态值约束。

Cast的dst_type为关键字参数；Cast和Clone的dependencies传GE Tensor控制依赖。文档类定义中的index/dtype/rank示意不应当作普通设备Tensor的方法调用。来源示例的省略函数与装饰器仍需真实Converter上下文，不是独立可运行脚本。

## 固定文档枚举的准确编码

以下只记录两快照页面相同的图描述编码。DT_UNDEFINED/FORMAT_UNDEFINED用于未定义状态，DT_MAX是边界标记；不可将它们作为普通数值类型使用。未列出的整数不自行补名，枚举存在仍不构成算子、设备或布局转换支持证明。

### DataType编码

|成员|编码|成员|编码|
|--|--|--|--|
|`DT_FLOAT`|0|`DT_FLOAT16`|1|
|`DT_INT8`|2|`DT_INT16`|6|
|`DT_UINT16`|7|`DT_UINT8`|4|
|`DT_INT32`|3|`DT_INT64`|9|
|`DT_UINT32`|8|`DT_UINT64`|10|
|`DT_BOOL`|12|`DT_DOUBLE`|11|
|`DT_STRING`|13|`DT_DUAL_SUB_INT8`|14|
|`DT_DUAL_SUB_UINT8`|15|`DT_COMPLEX64`|16|
|`DT_COMPLEX128`|17|`DT_QINT8`|18|
|`DT_QINT16`|19|`DT_QINT32`|20|
|`DT_QUINT8`|21|`DT_QUINT16`|22|
|`DT_RESOURCE`|23|`DT_STRING_REF`|24|
|`DT_DUAL`|25|`DT_VARIANT`|26|
|`DT_BF16`|27|`DT_UNDEFINED`|28|
|`DT_INT4`|29|`DT_UINT1`|30|
|`DT_INT2`|31|`DT_UINT2`|32|
|`DT_COMPLEX32`|33|`DT_HIFLOAT8`|34|
|`DT_FLOAT8_E5M2`|35|`DT_FLOAT8_E4M3FN`|36|
|`DT_FLOAT8_E8M0`|37|`DT_FLOAT4_E2M1`|40|
|`DT_FLOAT4_E1M2`|41|`DT_MAX`|42|

### Format编码

|成员|编码|成员|编码|
|--|--|--|--|
|`FORMAT_UNDEFINED`|-1|`FORMAT_NCHW`|0|
|`FORMAT_NHWC`|1|`FORMAT_ND`|2|
|`FORMAT_NC1HWC0`|3|`FORMAT_FRACTAL_Z`|4|
|`FORMAT_NC1HWC0_C04`|12|`FORMAT_HWCN`|16|
|`FORMAT_NDHWC`|27|`FORMAT_FRACTAL_NZ`|29|
|`FORMAT_NCDHW`|30|`FORMAT_NDC1HWC0`|32|
|`FORMAT_FRACTAL_Z_3D`|33|`FORMAT_NC`|35|
|`FORMAT_NCL`|47|—|—|

DataType发布页示例的 `from torch_npu, torchair` 是不完整Python导入语句，主线已改为import；类定义中的省略方法也不是可以直接执行的接口实现。精确编码用于读图与定位，业务配置优先使用枚举名称，避免与torch.dtype或NPU format编号混淆。

## Evidence

- [固定来源 1](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ge/tensorspec.md)（primary）
- [固定来源 2](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ge/Cast.md)（constraint）
- [固定来源 3](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ge/Clone.md)（constraint）
- [固定来源 4](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ge/Const.md)（constraint）
- [固定来源 5](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ge/datatype.md)（constraint）
- [固定来源 6](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ge/format.md)（constraint）
- [固定来源 7](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/ascend_ir/api/ge/tensor.md)（constraint）
- [固定来源 8](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/overview.md)（constraint）

- [补充固定来源](https://gitcode.com/Ascend/torchair/blob/7c6c754bed00c86ffaaa2a45cb7ac2724f058013/docs/zh/appendix/cases/graph_failed_cases.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/python/torchair/ge/_ge_graph.py)（supporting）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ge/tensorspec.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ge/Cast.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ge/Clone.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ge/Const.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ge/tensor.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ge/datatype.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/ascend_ir/api/ge/format.md)（constraint）

- [增补固定来源](https://gitcode.com/Ascend/torchair/blob/92e1e967bd35ebc37a442b4a969730bf3cf77a3c/docs/zh/overview.md)（constraint）
