---
type: API
title: SGLang Markov贪心投影与选择的舍入合同
description: 说明markov_greedy_step_triton的投影shape、FP32/FP16/BF16舍入、NaN并列规则与batch16至31的Torch分支。
tags:
- task.implementation
- topic.compute.ordering
- topic.precision
status: stable
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/docs/api/zh/operators/sample/markov_greedy_step_triton.md
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/operators/sample/markov_greedy.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/README.md
  role: supporting
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/sample/markov_greedy.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/torch_native/sample/markov_greedy.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/implementation/triton/utils/triton_utils.py
  role: implementation
created_at: '2026-11-08T11:03:54Z'
updated_at: '2026-11-09T15:06:40Z'
platforms:
- a2
- a3
- '950'
---

# SGLang Markov贪心投影与选择的舍入合同

```python
from sgl_kernel_npu.operators.sample import markov_greedy_step_triton
markov_greedy_step_triton(*, base_logits, prev_embeds, w2_weight, impl="auto")
```

文档声明Triton/Torch reference在arch22/arch35（A2/A3、950）支持，auto为Triton别名；注册不等于全芯片验收。输入同一NPU，`base_logits:[B,V]`、`prev_embeds:[B,H]`、`w2_weight:[V,H]`；V>0，logits与weight列stride=1，投影输入和weight须为兼容浮点类型，覆盖FP32/FP16/BF16。返回同设备新建 `[B]` int64词表索引，B可为0。

计算是 `(base_logits + linear(prev_embeds,w2_weight)).argmax(-1)`，须保留投影及加法的数据类型舍入；不能把中间全提升FP32视作无条件等价。并列取最小索引，NaN优先且选首个NaN。

Triton后端仍使用Torch线性投影，后接Triton加法归约；batch为16至31时投影后的加法/argmax也走Torch。函数名带triton不代表整条路径全为单一Triton Kernel或完全融合。

验证应对比独立Torch实现，覆盖16/31及邻近batch分支、低精度舍入、NaN与并列；测试入口 `tests/python/operators/sample/test_markov_greedy_step_triton.py`。本次未执行NPU、数值或性能测试。

## 固定Triton后端的投影与归约分发

公共wrapper仅把三个Tensor交给所选backend；Triton实现用assert检查二维、同device、V>0、shape相容、base/weight列stride1，未自行实现矩阵投影。B=0在F.linear之前返回新空int64 Tensor；所有B>0先调用框架F.linear得到bias，投影dtype舍入保留。固定仓没有该框架节点的CANN Host/Tiling/Device绑定，以下是自有后处理源码事实，不能称整个入口已source_closed或仅由纯Vector组成。

| batch域 | 实际节点与映射 | 资源/精度边界 |
|---|---|---|
| 1..15 | F.linear→partial→combine，parts=ceil(V/4096)；partial task=row*parts+part，以min(vectorCores,B*parts)程序持久步进 | vals[B,parts] FP32和idxs[B,parts] INT32共8B*parts字节；输出8B字节；bias另由框架分配 |
| 16..31 | F.linear→Torch add→Torch argmax | 不调用自有归约Kernel；源码注释称A3该域更快，是上游选择依据，本次未复测 |
| >=32 | F.linear→row kernel；min(vectorCores,B)程序，row=pid+j*numPrograms | FP32 step tile4096，FP16/BF16 step tile8192，再min(nextPower2(V))；INDEX_TILE=min(tile,2048)，multibuffer=False；不分配partial vals/idxs |

STEP_DTYPE取torch.promote_types(base.dtype,bias.dtype)，映射只覆盖FP16/BF16/FP32。每次_load_step_logits都将base/bias各自升FP32相加，显式cast STEP_DTYPE再升FP32归约；这保留加法舍入，源码特别说明Triton-Ascend3.2的隐式BF16 add不能保证该舍入。不能把投影、加法和选择全部提前提升成一个FP32公式。

partial每4096词表块对有效列做传播NaN的maximum，按best为NaN选NaN位置、否则选相等值，再min有效词表索引；写FP32 vals/INT32 idxs。combine以nextPower2(parts)向量加载有效分片，padding值−inf、索引2147483647，仍按NaN优先及最小索引归约，转INT64写结果。两launch在同current stream顺序执行，临时Tensor须由框架allocator覆盖异步寿命；不推定物理UB等于逻辑向量长度之和。

row路线先扫全部词表tile求best与首个获胜tile：只有严格更大或从非NaN首次变NaN才更新，跨tile并列保留较早tile；第二次只重读获胜tile，每次最多2048索引块并min，降低比较/选择/归约逻辑工作集。全−inf时best_start保留0，第二遍仍选首个有效列。row地址先转int64；索引哨兵/partial idxs仍INT32，Host未设V上限，不能由最终INT64输出推导任意巨大V安全。

_markov_launchers以(device,B,V,每个base/bias的dtype、rowstride、data_ptr%16)缓存编译launcher；key不持有具体输入Tensor，warmup后保存launcher，调用时重新取current stream并传新指针。get_device_properties为无参数@cache，首次读取current NPU的AIC/AIV数量，跨设备同进程调用可能复用首次core值；launcher的device key不消除该独立helper缓存边界。固定源码未提供这些缓存的清理/线程同步或图捕获验收保证。显式torch_native则直接执行完整Torch参考表达式。
