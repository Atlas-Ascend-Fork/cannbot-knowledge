---
type: Guide
title: vLLM Ascend SK缓存写入：原位stride、dtype门禁与Host调度
description: 沿scatter_cache、Torch原位schema、aclnnScatterNdUpdateSk和arch22/950 Host核对目标view、indices与updates连续化、FP8能力、空输入、索引宽度、UB与workspace；区分950 PA覆写与直接SK调用，保留重复slot、Device模板和图执行边界。 3164固定delta将SIMD排序判定延后至已验证平台核数可用的DoOpTiling阶段。
aliases:
- aclnnScatterNdUpdateSkGetWorkspaceSize
- ScatterNdUpdateSkArch22Tiling.HandleViewStride
- ScatterNdUpdateSkTilingRegbase.HandleNonContiguousCase
- BaseDeviceAdaptor.scatter_cache
- A5DeviceAdaptor._scatter_cache
tags:
- task.implementation
- task.debugging
- topic.kv_cache
- topic.memory
- topic.graph_execution
status: draft
sources:
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_host/op_api/aclnn_scatter_nd_update_sk.cpp
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_host/op_api/aclnn_scatter_nd_update_sk.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_host/op_api/scatter_nd_update_sk.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_host/op_api/scatter_nd_update_sk.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_host/scatter_nd_update_sk_def.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_host/scatter_nd_update_sk_infershape.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_host/scatter_nd_update_sk_tiling.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_host/scatter_nd_update_sk_tiling.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_host/scatter_nd_update_sk_tiling_arch35.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_host/scatter_nd_update_sk_tiling_regbase.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_host/CMakeLists.txt
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_kernel/scatter_nd_update_sk.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_kernel/scatter_nd_update_sk_apt.cpp
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_kernel/arch35/scatter_nd_update_struct.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_kernel/arch22/scatter_nd_update_hp.h
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/tests/ut/attention/test_cache_store.py
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/torch_binding_meta.cpp
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/device_op.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/vllm_ascend/device/hardware_profile.py
  role: constraint
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_kernel/arch22/scatter_nd_update.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_kernel/arch22/scatter_nd_update_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_kernel/arch22/scatter_nd_update_large_index.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_kernel/arch22/scatter_nd_update_linear_index.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_kernel/arch22/scatter_nd_update_no_sort.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_kernel/arch35/indices_sort_utils.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_kernel/arch35/load_store_utils.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_kernel/arch35/scatter_nd_update_common.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_kernel/arch35/scatter_nd_update_deterministic_simd.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_kernel/arch35/scatter_nd_update_deterministic_simt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_kernel/arch35/scatter_nd_update_simd.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_kernel/arch35/scatter_nd_update_simd_mask.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_kernel/arch35/scatter_nd_update_simt.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_kernel/arch35/scatter_nd_update_simt_sort.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2/csrc/moe/scatter_nd_update_sk/op_kernel/arch35/sk_math_util.h
  role: implementation
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/moe/scatter_nd_update_sk/op_host/scatter_nd_update_sk_tiling_arch35.cpp
  role: primary
- resource: https://github.com/vllm-project/vllm-ascend/blob/3164adc8fe75892fbf7f99f524bb72fddf1e6efd/csrc/moe/scatter_nd_update_sk/op_host/scatter_nd_update_sk_tiling_regbase.h
  role: implementation
created_at: '2026-11-03T02:12:16Z'
updated_at: '2026-11-03T06:29:45Z'
platforms: []
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      framework:
      - vllm
---

# vLLM Ascend SK缓存写入：原位stride、dtype门禁与Host调度

## 适配任务与证据范围

新模型的KV、indexer量化scale或状态cache写入，需要保证更新落在原始backing，并保留未选中行、物理页padding和storage_offset。本卡固定Main ceac1a2bdff3139ca8fbd1a60b3a9befd68cadf2，全文读取SK全部Host/API及数据结构、两份CMake、两份Device dispatcher和cache_store UT；另读Torch/schema/Meta、DeviceAdaptor与硬件能力片段，以及arch22 HP写入的205–272行。

其余HP、LargeIndex、arch35 SIMT/SIMD/排序/确定性模板及公共runtime没有闭包；本卡只生产框架Guide。未导入或执行上游、UT、编译、NPU、图或性能实验，保持draft/空平台，不把Host支持列表当真实硬件全组合验证。

[非连续KV设计](vllm_ascend_non_contiguous_kv_cache.md)解释allocator物理页与逻辑view；这里接着核对具体写入接口。[DSV4 KV计划](vllm_ascend_dsv4_kv_plan_contract.md)维护不同cache/slot格式，不能将其所有writer都替换成本文的SK。

## Python入口先确定实际callee

BaseDeviceAdaptor.scatter_cache仅对var[N,D]、indices[T,1]、updates[T,D]、两数据Tensor同dtype及INT32/INT64索引尝试优化，其他形状把原三个对象交给通用npu_scatter_nd_update_。行cache门禁不等于SK全部shape支持表。

Base的SK选择还要求精确能力位和已注册符号。普通数据只接受INT8/FP16/BF16/FP32；E4M3FN/E5M2另需SCATTER_ND_FP8_CACHE_STORE。目标内行必须stride(1)=1、stride(0)>=D；非连续目标另需SCATTER_ND_STRIDED_CACHE_STORE。不为目标调用contiguous，避免写入临时副本而原cache未更新。

950的A5DeviceAdaptor覆写`_scatter_cache`：目标连续且PA符号和dtype满足时，使用npu_scatter_pa_cache，updates reshape为[T,1,D]并连续化，indices展平并连续化，目标view为[N,1,1,D]。原flat slot仍是一行一block的编号；已有storage_offset随view保留。目标不连续或符号缺失时退回通用scatter，**不会再自动调用Base的SK**。因此950具有SK/FP8能力位，不代表这个高层入口实际执行SK。

Base对950的strided SK能力也保持关闭；直接调用torch.ops._C_ascend.npu_scatter_nd_update_sk或某些设备辅助方法则绕过这个高层门禁。底层Host可表达stride，不能据此绕过已存在的兼容限制。选中算子后抛出的错误直接传播，没有catch后重试通用scatter；部分写入失败后不能靠盲目重试宣告原子恢复。

## Torch与ACLNN：目标原位，输入可能复制

Torch schema是`npu_scatter_nd_update_sk(Tensor(a!) var, Tensor indices, Tensor update)->()`。返回None，修改var；C++把var.strides()显式作为aclnn参数传入。Meta是void no-op，没有验证shape、stride、dtype或索引值，fake执行成功不是实际写入检查。

ACLNN第一阶段先检查非空指针、var/indices的dtype及var与updates同dtype。随后任一输入为空Tensor就返回workspace=0的空executor；这里的空Tensor与空指针不同，dtype检查仍先执行。

非空路线对var只做SetStorageShape(GetViewShape)，保持其原始目标；indices与updates分别通过Contiguous进入L0。因此“目标零拷贝”不等于无输入复制、无workspace或整个调用零分配。Host后续读取修正后的storageShape，不能改回使用可能已被torch_npu压成一维的originShape。

L0把同一个self作为输入和输出，属性顺序为strides、use_locking；第一阶段固定传use_locking=False。OpDef声明顺序必须与launcher一致，不能按属性名称以为二进制会自动匹配类型。这个布尔值不能为重复slot、跨stream或跨调用提供锁保证。

第二阶段把workspace/executor交给CommonOpExecutorRun及指定stream。workspace/executor生命周期、完成事件、跨stream消费和图回放仍需外部runtime合同；第一阶段成功不代表设备写入完成。当前Host CMake使用aclnn_exclude收集自定义实现并启用cce-auto-sync，不能以该编译选项证明所有图同步已闭合。

## dtype声明必须逐层求交集

ACLNN接受FLOAT/FP16/BF16/BOOL/INT64/INT32/INT16/INT8及E4M3FN/E5M2，索引为INT32/INT64，updates必须同var dtype。OpDef顶层还列出UINT8/HIFLOAT8，但该ACLNN检查不接受它们；不能取最宽的一张表宣称公共入口支持。

arch22配置不注册FP8，950使用独立apt入口并继承其顶层声明。arch35 dispatcher把所有1字节数据的compute type映成INT8，这是位模式搬运的接线，不是把FP8数值量化为INT8。完整设备模板未读完，仍需按实际调用验证全bit-pattern、NaN payload和未选行，不能从sizeof相同推导所有路径都正确。

FP8、量化NoPE与scale的真实打包另由各模型writer维护；SK不会替调用者做scale计算、payload拼接、slot换算或cache dtype归一化。不要用数值to(INT8)代替同itemsize view，或把一张scale cache的dtype门禁搬给另一种payload。

## arch22：只把明确的行间隔视作view

Host从indices末维取indexDim，索引前缀的var维度乘积为totalLength，后缀乘积为scatterLength，indices前缀乘积为indexRow。新的调用者应主动保证标准scatter shape关系、rank上限、索引坐标及updates行宽；这个arch22路径没有arch35同样完整的shape一致性检查，不能用缺少拒绝代替支持。

HandleViewStride默认连续；只有strides属性长度等于var rank才读取。非索引尾轴中size>1的维度必须连续，首轴实际stride严格大于连续期望时设置view标志并记录varStride0Elements。它没有承诺任意轴转置、overlap、负stride或错误长度都正确拒绝；高层行cache门禁的stride>=D与内行连续条件应保留。

INT32索引的key为10/11；INT64且可用INT32线性地址为20/21；INT64的大地址为30。totalLength<=2^31−1用于线性索引选择，<=2^24−1另决定Host sortFlag。Device dispatcher的10/11均进HP，20/21也均进HP，30进LargeIndex；**Host算了sortFlag不代表当前dispatcher真的执行旧排序算法**。

HP分indices到核，行更新优先双buffer、32字节对齐，行能放下时每批最多256行，过宽则按列切片并降到一行。index tile按UB余量对齐到32并最多4096行。Host仍保存旧scatter/linear及HP多组字段，不能把每个字段都当作当前key的活跃执行路径。

workspace为平台LibApi工作区，加按8行对齐的indexRow×4字节线性索引区，再按sortFlag增加同样大小的区。当前HP入口即使不实际使用旧排序路径，Host仍按该公式预留；这不是实测峰值或可直接删除的冗余。dispatcher遇workspace或user workspace空指针直接返回，不能以无异常证明写入已完成。

## 950：shape、地址宽度与调度分开判断

950顶层明确转ScatterNdUpdateSkTilingRegbase。Host读取修正后的view shape和显式strides；indices至少二维，index tuple宽为1–7，var rank不得小于tuple宽，updates必须匹配indices前缀及var未索引后缀。var/updates dtype一致；推导的shape和固定数组容量仍须由调用者保持有效，不能用输出infershape仅复制var shape证明全部输入合法。

连续目标的地址范围取逻辑numel。非连续路线只接受tuple宽<=4，并要求非索引尾轴连续；用`sum((var_dim−1)*stride)`的索引轴贡献加完整afterAxis，得到outputStorageShapeSize。该数用于设备地址守卫，不是真实allocation查询；必须另核正stride、storage_offset、非重叠和backing容量。高层950仍不为strided目标选SK。

UB先扣32KiB供Dcache/编译栈，要求剩余可用；多路tile再按32字节、双buffer及256字节保留区划分。context deterministic=1且索引行数>1时选择确定性路径；否则row bytes>=128可选SIMD，再按重复度、每核索引数和mask条件细分；小行的高重复度可走SIMT排序。这里的路由启发式不是实测最佳参数，也不说明重复slot最终由哪条更新获胜。

key100要求indices/update元素数分别<UINT32_MAX且目标跨度<INT32_MAX，否则key200。它与indices Tensor本身的INT32/INT64是两个维度；大地址可能要求64位offset，即使输入索引是INT32。Device dispatcher还结合目标跨度和tiling flags选SIMT/SIMD及确定性模板，不能只记录一个key复现行为。

950固定预留16MiB workspace；确定性路径再加(varStorageInAxis+indicesAxis+1)个INT32或INT64元素，选择条件与key地址范围一致。不可照搬arch22按indexRow的公式。实际executor还可能包含输入连续化，最终申请量应取真实第一阶段返回值。

## PAD、重复slot与图的边界

已读arch22 HP写入片段对负的线性索引跳过整行，不把-1改成0；其余线性化、LargeIndex及arch35模板没有完整审阅，不能把局部负值guard当作所有多维负坐标、正越界或任意PAD编码的证明。静态slot形式应按具体writer保留，不能用Host boolean过滤改变capture形状。

arch22 dispatcher明确说明HP跨核重复索引写入不确定；普通key并未消费950的确定性调度合同。新模型应避免活跃行重复slot，或取得实际选中实现的明确重复更新语义，不能把use_locking=False、排序标志或一个deterministic开关当通用最后写入规则。

cache_store UT使用Mock/CPU替身定义了平台路由、原对象/原存储、非连续输入、偏移/row-gap、缺符号回退、错误不重试、FP8按字节比较，以及SFA/indexer携带自身slot和gather后全行的断言。PAD过滤发生在替身writer中；这些定义不能证明真实SK/PA/通用算子、负值守卫、跨stream或ACL graph已通过。本次未执行该UT。

## Agent的接入验收与性能诊断

固定模型writer和真实callee，记录var shape/stride/storage_offset/backing范围、indices shape/dtype/完整slot数量、updates shape/dtype/连续性、SoC、实际key和全部活跃flags、UB与第一阶段workspace。高层优化条件不满足时保留原输入交给已支持路径，不做目标contiguous、任意截行或把PAD重定向到活跃slot。

先比较更新行、未选行、padding和别名可见性；FP8比较bytes并覆盖NaN编码，分别核对INT32/INT64和大offset、空输入、row-gap/column-gap、重复/负/边界slot。再加入图/eager、跨stream完成与cache消费者，正确后才区分输入连续化、Host tiling、workspace和设备搬运开销。失败时保留部分写入现场与算子返回，不用吞错重试或只比输出shape接受优化。


## Device补充：地址合法性不等于逐坐标合法性

本节补读剩余15份arch22/arch35辅助模板：完整声明、分支与调用结构投影，加表内列出的原始地址、排序、mask和搬运片段；sk_math_util逐行全文。前文“未完整审阅”记录的是原Host卡证据边界，本次仍没有完整Operator、运行时或所有模板实例的验证。

arch22的view地址使用`i0×varStride0Elements + rest×scatterLength + tileOffset`，连续路径则用linearIndex×scatterLength。LargeIndex对每维负值立即返回−1，再按当前核的线性范围筛选；它没有逐维正上界检查，只验证最终线性地址。混合非法坐标可能线性化成合法行，不能把最终offset有效等同每个tuple都合法，也不能推广为Python负索引语义。

旧LinearIndex路径先用INT32向量累加，再在排序分支把索引转FP32排序、转回INT32，并携带原update位置；这解释了Host精度阈值的重要性。旧sorted writer逆向遍历相邻重复线性索引并只写一次，NoSort/LargeIndex则按各自核内范围复制。当前dispatcher仍主要走HP或LargeIndex；这些旧模板存在不能证明真实选中路径具备相同重复更新规则。

arch35的普通SIMT多维路径逐坐标检查负值与outputShape边界，再按stride写入；一维路径单独按`0<=idx<varInAxis`判断。SIMD、SIMT-sort和确定性公共路径通常先把tuple乘stride累加成flat offset，再检查flat范围；这几条并不自动拥有相同的逐维保护。新writer应事先保证完整tuple合法，覆盖负值抵消、单维正越界、大offset及row-gap，不能只用全负PAD的成功样例代替。

## Device补充：排序启发式与确定性mask分开

IndexStatisticInt32/Int64根据行宽选择位移，再使用FNV式hash与直方图估计聚集程度，maxScore按行数归一化；0.01阈值决定某些tile是否排序。它是调度启发式，不是精确重复ID计数，也不提供所有核/调用的唯一slot保证。普通SIMT-sort从每个sorted唯一组挑一个代表；SIMD-mask用本核UB mask跳过已处理行，不能将这些局部去重当跨核“最后一条输入获胜”。

确定性路线另在GM workspace初始化mask，并记录每条输入的flat目标；有效代表通过atomic_max竞争原始行号。SIMT/SIMD writer只有当mask记录值等于自身输入行号时才写，CalcMask前后均有SyncAll。排序分支先选组内代表，再竞争全局mask；组内相同key的顺序、代表选择与实际模板实例仍应核对，不能只从atomic_max推导任意重复模式的完整last-write证明。

确定性SIMD按行处理，源码的循环边界由indicesFactor/idxLoopSize共同确定；接入时应保留真实tiling字段，验证多行tile覆盖，不能由类名推定全部输入行都已写。确定性SIMT按update元素和sliceSize还原原始行，写入前同时核flat范围和获胜mask。sliceSize为0时直接返回；workspace分为mask和varIdx，二者的初始化、跨度与偏移不能套用普通scatter工作区。

load_store_utils还定义FP16/BF16/FP32寄存器加载与多种整数/浮点存储转换，其中部分路径经FP32或FP16中间值；这些通用函数的存在不证明SK主写入调用了它们，更不能据此改变前文FP8按位搬运的协议。sk_math_util提供32字节UB块和条件向量寄存器宽度以及整除/对齐辅助；除数与整数范围仍由实际tiler保证，不是运行时总是安全的前提。

接入Agent应区分真实SoC/key、是否直接SK、地址类型、排序flag、确定性flag和实际callee；对合法tuple先检查选中行、未选行、byte payload与跨tile重复，再验证图和跨stream生命周期。上述均为固定源码接口/Device选段知识，未执行上游、编译、NPU、数值或性能实验。

## 固定3164增量：SIMD排序决策的资源初始化顺序

比较ceac与3164adc8fe75892fbf7f99f524bb72fddf1e6efd的两个Host delta，UpdateSimdSortDecision从CalculateDerivedParams移到DoOpTiling，在GetPlatformInfo已初始化并验证totalCoreNum之后才计算ceil(indicesAxis/totalCoreNum)。判据仍为SIMD非确定性分支、indicesAxis>varInAxis且每核估计indices>64；SIMT的比例排序门禁没有因此合并成同一判据。

这个修订解决决策使用平台核数的时序问题，不是把排序强制打开，也不改变caller的重复索引覆盖/非确定性语义。框架适配或回移补丁时要连同header新增方法声明与调用位置一起移植；不能只复制新函数后仍在平台信息未就绪时调用。本次仅delta审阅，未做目标SDK编译或NPU验证。
