---
type: Guide
title: 普通归约与累加扫描：dtype、空输入和别名临时对象
description: 聚合Sum/Mean/Prod/Cumsum的输出dtype选择、cumsum同对象out临时写回、sum空输入zeros快捷及命名维版本范围。
tags:
- task.optimization
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/CumsumKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SumKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MeanKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ProdKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/SumKernelNpuOpApi.cpp
  role: primary
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/CumsumKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SumKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MeanKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ProdKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/SumKernelNpuOpApi.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp
  role: implementation
- resource: https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp
  role: implementation
created_at: '2026-11-11T10:45:33Z'
updated_at: '2026-11-11T10:45:33Z'
platforms: []
---

# 普通归约与累加扫描：输出dtype、空输入和别名临时对象

sum、prod和cumsum的默认输出类型选择不同于mean；cumsum的同一Tensor out会先做临时结果再copy_，sum的空输入zeros快捷只属于functional。这些准备分支应与归约/扫描本体分别定位。

本卡聚合OpAPI的sum与内部sum_common、mean、prod及cumsum。sum_common位于utils/custom_functions/opapi，外层SumKernel的转发还未包含实际dtype和空输入处理。

| gate | 行为 | 可见准备成本 |
|---|---|---|
| cumsum_out的self.is_same(out) | SDK写tmp，再copy_到out | 按self申请临时结果与一次copy_请求 |
| sum functional任一self size为0 | 返回按归约shape申请的zeros | 仍先做兼容、shape与dtype准备，随后zeros请求 |
| mean functional | 申请结果后调用本地mean_out | out内再次准备dim/shape与检查 |
| dtype缺省且命中整数提升分支 | sum/prod/cumsum选Long输出 | 输出类型/存储需求可能与原self不同，未在此先cast self |

[公开Torch归约范围](torch_npu_native_torch_index_reduce_scope.md)与[Tensor方法范围](torch_npu_native_tensor_index_reduce_scope.md)保留产品/版本类型矩阵，包括特定产品sum dtype与cumsum限制；本卡中的参数透传不扩大该矩阵。

## functional默认dtype和out dtype不是同一规则

| 入口 | 局部输出/算子dtype选择 |
|---|---|
| sum、prod functional | 指定dtype优先；否则isIntegralType(...,true)时选Long，其他保持self dtype |
| cumsum functional | 指定dtype优先；否则浮点或复数保持self选项，其他按Long申请；再转换结果dtype为传给SDK的ACL枚举 |
| mean functional | 指定dtype或self dtype，没有上述整数默认Long分支 |
| sum_common out、prod_out | 指定dtype或传入result自身dtype，并以该选择检查输出 |
| cumsum_out | 传给SDK的ACL dtype为指定dtype或out自身dtype；输出检查的实参是self.sizes() |
| mean_out | 指定dtype优先，否则defined out dtype，再否则self dtype；但check_tensor实际dtype实参仍取out.scalar_type() |

这些选择改变输出申请与SDK参数，主体仍将原self传入，没有统一先self.to(dtype)。尤其mean_out的dstType与检查实参、cumsum_out的ACL枚举与实际临时Tensor选项要分别跟踪；输出类型选择不直接给出内部累加器精度。

## cumsum的同一Tensor out会额外申请并复制

两版cumsum_out兼容检查和check_tensor之后计算dtype_new，仅在self.is_same(out)时申请apply_tensor_without_format(self)临时对象，向aclnnCumsum传self、dim、dtype_new和该tmp，再out.copy_(tmp)。这不是直接原地扫描，返回out引用也不代表没有临时结果或写回。

这里判断is_same，不是任意storage部分重叠检测；不同view但共享storage不自动命中。tmp按self申请，局部没有按dtype_new再改tmp选项，需核对实际dtype组合的SDK验证/转换。非is_same分支直接传out；两种分支结束都propagate_names(out,self)。

functional则按上表选择并申请结果、执行aclnnCumsum，再传播names。默认整型/Bool申请Long时仍须核具体发行支持；独立的aclnnCumsumV2 Kernel实现不是这里旧aclnnCumsum入口的证据。

## sum的空输入快捷只在functional内部实现

外层整数dim列表sum/sum_out把缺省dim换为空IntArrayRef，再调用sum_common_nocheck/sum_out_common_nocheck；全轴sum传空列表、keepdim=false。内部仍执行DO_COMPATIBILITY(aclnnReduceSum,相应旧ACL表达式)，nocheck名字不代表完全无检查或不做兼容分派。

functional先计算归约shape和输出dtype，再扫描self的所有size：任一size==0，直接请求at::zeros(output_size,self.options().dtype(out_type))返回，不进入本地后面的EXEC_NPU_CMD(aclnnReduceSum)。判定不只检查被归约轴；零维Scalar的size列表为空也不是这个循环命中的零长度维度。

这条return仍在兼容检查、shape推导和dtype选择之后，并调用zeros。sum_common out没有同样早返，检查输出后仍执行SDK调用；非空functional则申请结果再执行。两个入口都保留原dim/keepdim及选中dtype。

## mean会进入自己的out实现，prod分轴与全轴API不同

mean functional先做兼容检查、准备dim/输出shape/dtype并申请结果，随后调用op_api::mean_out(self,原dim,keepdim,dtype,result)。out函数重新进行兼容、dim与shape准备并check_tensor后执行；定位时应保留这些重复准备位置，实际查找/设备启动次数仍取决于宏与缓存。

mean未指定dim时get_dimlist_for_tensor构造0..rank-1，显式dim则原样取其列表；不含dim的mean重载把空列表交给有dim入口。共用shape helper将空维度列表视作全部轴，keepdim决定置1还是删除。shape/dimlist完整规则复用[方差与标准差](torch_npu_variance_std_correction_and_cpu_roundtrips.md)同字节来源，不重新提升整个utility文件。

prod带整数dim的functional/out调用aclnnProdDim，并用单dim列表的prod_npu_output_size；不带dim的functional调用aclnnProd，用空dim列表及keepdim=false推导全轴结果，本组没有对应全轴out实现。prod和mean没有sum_common functional的统一零size返回zeros分支，空归约身份值与NaN按所选算子核对。

## 版本声明与模型优化验收

两版上述主体准备规则相同，主线新增命名维编译保护：cumsum.dimname_out、mean两种names重载、sum两种DimnameList重载均在!VERSION_BETWEEN(V2R13,VERSION_NEWEST)范围，Schema限定[v2.1,v2.12]；发布没有相同保护且这些Schema为all_version。

两版普通cumsum与prod所列Schema为all_version；mean.dim/out、sum.IntList_out/dim_IntList为[v2.1,newest]，mean无dim与sum无dim为all_version。主线另外在sum无dim/IntList_out/dim_IntList三项声明dvm，发布没有；本卡不据此推导DVM内部执行与Eager相同，或用注册标签作任何产品保证。

评估模型中归约与mask/位置累加时，记录准确重载、显式dtype、out dtype/设备及is_same关系、dim/keepdim、零长度维度和实际后端。验证数值、shape/dtype、别名与梯度，再分开观察默认Long输出、临时copy_、zeros早返与本体成本；减少dtype宽度或申请时须保留溢出、精度和空输入语义。

## 来源与验证状态

OpPlugin分别固定主线`d84e9b1d6a558e5f27973cd4329f62968e46fdda`、发布`dedc316708372c9a8bfde4527abd2a94b74840f5`。本卡来自静态源码审阅，未执行上游、SDK、设备、数值或性能测试；未知产品与安装组合保持draft、空平台，没有verified记录。

## Evidence

- [CumsumKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/CumsumKernelNpuOpApi.cpp)（primary）：1–71。
- [SumKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/SumKernelNpuOpApi.cpp)（primary）：1–61。
- [MeanKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/MeanKernelNpuOpApi.cpp)（primary）：1–102。
- [ProdKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/ops/opapi/ProdKernelNpuOpApi.cpp)（primary）：1–79。
- [SumKernelNpuOpApi.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/custom_functions/opapi/SumKernelNpuOpApi.cpp)（primary）：1–64。
- [op_plugin_functions.yaml d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/config/op_plugin_functions.yaml)（implementation）：1922–1932、3490–3508、4032–4042、5009–5030。
- [KernelNpuOutputSize.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：77–113、127–142、1048–1056、1424–1426；其中57已读同字节范围：77–113、127–142。
- [OpUtils.cpp d84e9b1](https://gitcode.com/Ascend/op-plugin/blob/d84e9b1d6a558e5f27973cd4329f62968e46fdda/op_plugin/utils/OpUtils.cpp)（implementation）：206–213；其中57已读同字节范围：206–213。
- [CumsumKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/CumsumKernelNpuOpApi.cpp)（implementation）：1–73。
- [SumKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/SumKernelNpuOpApi.cpp)（implementation）：1–64。
- [MeanKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/MeanKernelNpuOpApi.cpp)（implementation）：1–94。
- [ProdKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/ops/opapi/ProdKernelNpuOpApi.cpp)（implementation）：1–81。
- [SumKernelNpuOpApi.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/custom_functions/opapi/SumKernelNpuOpApi.cpp)（implementation）：1–64。
- [op_plugin_functions.yaml dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/config/op_plugin_functions.yaml)（implementation）：1863–1873、3388–3406、3920–3930、4852–4870。
- [KernelNpuOutputSize.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/KernelNpuOutputSize.cpp)（implementation）：80–110、127–143、896–906、1267–1270；其中57已读同字节范围：80–110、127–143。
- [OpUtils.cpp dedc316](https://gitcode.com/Ascend/op-plugin/blob/dedc316708372c9a8bfde4527abd2a94b74840f5/op_plugin/utils/OpUtils.cpp)（implementation）：204–211；其中57已读同字节范围：204–211。
