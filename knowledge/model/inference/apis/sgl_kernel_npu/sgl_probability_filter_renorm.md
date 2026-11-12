---
type: API
title: SGL采样概率过滤、打包键还原与RN重归一化
description: 区分top-k与top-p的FP32输入、阈值转换、双排序和原地临时值过滤，保留精确键上界、分母下限及外部Torch核心边界。
tags:
- task.implementation
- topic.speculative_decoding
- topic.memory
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/sample/probability.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/sample/__init__.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/__init__.py
  role: constraint
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_speculative_probability.py
  role: evidence
created_at: '2026-11-09T12:37:30Z'
updated_at: '2026-11-09T12:37:30Z'
platforms: []
aliases:
- top_k_renorm_prob
- top_p_renorm_prob
- filter_and_renorm
---

# SGL采样概率过滤、打包键还原与RN重归一化

## 入口与适用范围

```python
from sgl_kernel_npu.sample import top_k_renorm_prob, top_p_renorm_prob
from sgl_kernel_npu.sample.probability import filter_and_renorm

top_k_renorm_prob(probs, top_ks)
top_p_renorm_prob(probs, top_ps)
filter_and_renorm(probs, sorted_values, sorted_indices, thresholds, cumulative=None)
```

固定源码只提供打包键Triton路径，没有环境变量选择或scatter回退。两个公开入口要求NPU上的FP32二维`probs[R,V]`，`1<=V<=2**23`，先执行`contiguous()`；不连续输入可能复制，连续输入可复用原存储。它们没有检查有限值、非负性或每行和为1，调用方仍须保证概率语义。R=0在阈值转换之后返回同shape的空Tensor。包初始化仍会加载`libsgl_kernel_npu.so`，不能由本文件只有Python/Triton推定缺少原生库也能正常导入。

本页保留公开调用和本仓两个Triton阶段的可复核机制。源码与专属测试没有明确整接口的具体NPU产品矩阵，故保持平台未定位草稿。Torch排序、求和、cumsum是核心计算，其实际NPU实现版本没有在此文件中固定；不能用这份接口卡冒充完整多Kernel源码闭包，也不能从其他采样测试的CI矩阵外推本接口验收。

## 阈值与筛选顺序

Python数值被构造成设备端`[R]` Tensor；零维Tensor先转目标device/dtype再`expand(R)`，可能为stride0；一维Tensor必须长度R，转换不保证原本步长变成1，Triton按实际`thresholds.stride(0)`取值。其他rank或长度抛出`ValueError`。

| 入口 | 阈值转换与裁剪 | 过滤规则 |
|---|---|---|
| `top_k_renorm_prob` | 转`torch.long`，再限制到`[1,V]` | 按原生降序sort结果的排名`j>=k[r]`置零。浮点阈值的整数转换发生在裁剪之前。 |
| `top_p_renorm_prob` | 转FP32，再限制到`[0,1]` | 先对原生降序sort值做原生inclusive cumsum，严格按`cumulative[r,j]-value[r,j]>p[r]`置零。 |

top-p必须保留inclusive cumsum减当前值的实际舍入次序，不能替换为另一种exclusive scan并宣称逐位等价。概率相同的token保留哪个取决于原生概率sort返回的排列，本接口没有另加稳定tie规则。合法非负概率下p=0保留首个正概率项，p=1的行为仍以实际FP32累计与上述比较为准；全零行输出全零。

`filter_and_renorm`是较弱的内部接口：调用方直接提供连续、同设备且相互一致的排序值、排列、可选累计值，以及已转换/裁剪的阈值。它不重跑公开输入校验，也不重建排序；`cumulative is not None`才选择top-p。`sorted_values`会原地改写，不能和需要保留的输入错误别名。正常公开调用用独立sort结果作临时值，原始probs不写。

## 打包键与两阶段还原

逻辑链为`概率降序sort → 过滤并编码 → 过滤值求和及分母限幅 → 键升序sort → 按原token序还原并RN除法`。top-p还在过滤前执行cumsum。两次sort与中间求和都是实际计算节点，不是仅靠两个Triton launch完成整个算子。

本仓Triton阶段以2048个元素为tile，`NB=ceil(V/2048)`，grid为`min(R*NB, num_vectorcore)`，每program以grid stride循环处理tile，行地址转int64后计算。所有末tile读写都有`offset<V`掩码，load有明确`other=0`。

1. `_filter_encode_kernel`按上表规则将过滤后的排序值写回`sorted_values`，再生成FP32键`key=2*token_id+(filtered_value!=0)`。每个原始token ID在合法sort排列中恰有一次。
2. 原生`sorted_values.sum(-1,keepdim=True).clamp_min_(1e-20)`生成分母。必须保留过滤值的排序后求和顺序与`1e-20`下限；极小行质量低于下限时，结果不保证行和为1。
3. 对键作原生升序sort，按返回的`.values`取有序键。因为相邻token的键区间互不重叠，位置j得到`2*j`或`2*j+1`；`V<=2**23`令最大键`2*V-1<=2**24-1`，所有编码整数均可被FP32精确表示。
4. `_restore_kernel`从原始probs按词表顺序读取值；有序键等于`2*j`则归零，否则保留原值，再用`tl.div_rn(value, denominator)`输出。不能将该除法改为倒数乘法而保留本接口的逐位契约。

编码以“过滤值是否为零”保存保留信息；原本为零的概率即使排名被保留，重归一化后仍为零。NaN、负值或非概率输入未被公共入口拒绝，但不属于上述概率语义推导。键排序避免最终按排列做全词表scatter，不等于没有全词表临时内存或没有外部排序workspace。

## 内存、设备与图边界

显式`keys`和`output`各有`4*R*V`字节有效Tensor载荷；还有概率排序值/索引、top-p累计值、分母、阈值及键排序结果。源码只访问键sort的values，不能由此断言框架不分配其indices或workspace。各框架算子的临时空间、物理UB、Triton寄存器分配和流间回收契约均未由这份源码给出。

`get_device_properties()`是无参数`functools.cache`，首次读取current_device的核数，之后不按device区分缓存。多设备进程须核对首次缓存与实际输入设备；本入口没有额外device guard。公开入口返回新output，不返回中间排序值；直接调用内部接口的临时值所有者须保证异步执行期间有效，具体分配器/stream追踪仍由匹配Torch运行环境负责。

专属测试定义了先warmup、同步，再固定shape与地址捕获`torch.npu.NPUGraph`，随后对原输入地址`copy_`新概率并replay的比较。它没有证明动态shape、替换输入storage或重放时改变Python阈值可被图自动接收。图支持也取决于所用Torch原生sort/cumsum/reduction实际捕获实现。

## 测试证据与复核信号

`test_speculative_probability.py`定义共享同一次概率排序排列的参考比较，使用`rtol=0, atol=0`避免两次独立sort的tie歧义；覆盖R7/216、V4/97/2051/154880/248320、均匀/零/单点/极小质量行、阈值标量及逐行形式。另有CPU零维阈值到NPU转换、非连续输入/stride2阈值、裁剪、空batch、非法rank/dtype/device/V及固定地址图重放用例。

复核时应同时检查输出、原输入未变、内部排序值确实被过滤、端点阈值、分母下限和相同sort排列；不能只检查行和或放宽容差掩盖RN差异。这些是固定来源的测试定义，本次没有执行上游测试、编译、图捕获、真机或性能测量，也未记录verified事件。Torch核心版本未固定和具体产品矩阵未确认的边界保持显式。
