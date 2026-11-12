---
type: API
title: SGL目标分布树采样的兄弟遍历与拒绝概率临时区
description: 说明tree_speculative_sampling_target_only的真实树指针、两类接受阈值、清零draft scratch、残差抽样及调用方索引与并发约束。
tags:
- task.implementation
- topic.speculative_decoding
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/sample/tree_speculative_sampling_target_only.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/sample/__init__.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_tree_speculative_sampling_target_only.py
  role: evidence
created_at: '2026-11-09T12:42:57Z'
updated_at: '2026-11-09T12:42:57Z'
platforms: []
aliases:
- tree_speculative_sampling_target_only
---

# SGL目标分布树采样的兄弟遍历与拒绝概率临时区

## 接口和可变数据

```python
from sgl_kernel_npu.sample import tree_speculative_sampling_target_only

tree_speculative_sampling_target_only(
    predicts, accept_index, accept_token_num, candidates,
    retrive_index, retrive_next_token, retrive_next_sibling,
    uniform_samples, uniform_samples_for_final_sampling,
    target_probs, draft_probs,
    threshold_single=1.0, threshold_acc=1.0, deterministic=True,
)
```

函数返回None并原地写predicts、accept_index、accept_token_num与draft_probs。B请求、N树节点（含root）、D最大树深度：candidate及三个`retrive_*`均int64 `[B,N]`，target概率为FP32 `[B,N,V]`，uniform为FP32 `[B,N]`、final uniform为FP32 `[B]`。predicts为一维int32池，accept_index为int32 `[B,D]`且`1<=D<=N`，计数为int32 `[B]`。`retrive_index`映射flat输出槽，child/sibling存请求内节点号，`-1`终止。

`draft_probs`与target同shape/FP32，是可变拒绝概率scratch：Host每次先`zero_()`，接受核记录拒绝兄弟的target概率，最终只消费选定概率行。它不是经典链算法的提案分布；提供真实draft概率也会被覆盖。代码拒绝两个Tensor的`data_ptr()`完全相等，但该检查不证明任意不同起始地址的存储区间不重叠，caller仍须保证完整分离及没有其他错误alias。

所有实际消费Tensor要求连续、device与target相等；没有额外检查device.type。B=0在初始rank检查后早返，不做后续验证或scratch清零。非空batch要求N>0；V、token/index设备值、树无环与概率有限/非负/归一化均没有完整检查。此源码和专属测试未固定具体NPU产品矩阵/CANN版本，保留平台未定位草稿；不能据可导入内核推翻上层worker的支持守卫。

## 逐层兄弟接受

初始概率行/root节点为0，最后输出槽来自root的retrive_index，coin来自uniform第0列；root写入accept_index。每层先沿child下降，再按sibling依次尝试，层内从0累计这些候选token在当前target行的概率`prob_acc`。每个候选按`coin<=prob_acc/threshold_acc`或`target_prob_single>=threshold_single`接受，包含等号；它没有读取真实draft分布，也不等于经典拒绝的`coin*q<p`。

两个阈值均检查`[0,1]`，threshold_acc转float后取`max(value,1e-9)`；0不会直接作为除数。threshold_single=0在合法非负概率域中可令第一个尝试的候选立即满足单点条件；因此不能把两个阈值都设0理解为禁用接受。`deterministic`被丢弃，不控制随机数生成或并行模式；随机输入由caller提供。

接受后将token写到上一已接受槽，记录当前retrive_index，概率行切到当前节点号，并换用该节点uniform；同一层停止继续兄弟。拒绝时将该token的target概率写入当前行scratch，再沿sibling移动。无child或无兄弟被接受时路径停止。每层兄弟循环上限N仅防无限迭代，并不验证树结构；重复token可能重复进入累计概率、scratch却是同位置赋值，不能据此宣称非法重复候选自动去重。

计数a不含root，accept_index有效前缀长a+1，尾部未清理。predicts按flat retrive槽存后继token与最终bonus；caller须保证非负容量、int32可表示的返回槽号、请求间无写冲突和合法无环child/sibling。除`-1`外的负指针、越界节点或候选token不会由shape检查自动过滤。D可小于N，输出跨度确为D；不能照搬另一个线性greedy核固定N跨度的限制。

## 临时区与最终抽样

Host先通过外部Torch `zero_`初始化整个FP32 `[B,N,V]`scratch，再分配int64 metadata `[B,2]`和FP32 block_sums `[B,ceil(V/2048)]`，依次launch接受、分块和、抽样三个Triton节点。metadata有效载荷`16*B`字节，块和`4*B*ceil(V/2048)`字节；scratch本身为`4*B*N*V`字节，不能只按接受深度估算峰值内存。Torch清零的实际实现不在这个Git模块中固定，不宣称全部Device节点源码闭包。

最终行残差为`max(target_probs-rejected_scratch,0)`；拒绝token的记录值等于该处target，因此这些词元残差为0。分块节点使用2048词元tile、核数限制及grid stride，每个尾块masked load明确补0；最终每请求读取2次幂补齐的块和，计算块CDF和total，选择块后重读该块target/scratch重建残差，再做局部CDF。块号与局部回退和[经典链接口](sgl_chain_rejection_sampling.md)相同：CDF比较`<=`，局部越界优先所选块最后正残差，否则词表最后token。全零残差不报错而产生`V-1`；V=0、非法uniform与零质量不是经过验证的正常采样域。

两层FP32归约/扫描在CDF边界附近可能与单次参考扫描选到不同token；不能因给了deterministic=True就承诺不同后端逐位随机结果。临时metadata/block_sums、mutable scratch及输出池须在异步执行中保活，避免其他stream并发清零或写同槽。源码只顺序提交，没有独立跨stream event；Torch/Triton运行时负责匹配的流顺序与分配器回收。设备核数helper为无参数cache，切换current_device不自动重新读取。

## 验证与上层边界

专属测试定义B2/N6/D4/V20的非线性树与拒绝scratch逐位比较，阈值组合(1,1)/(0,0)/(0.5,0.8)；另有B1/4/17、N2/5、V20/32000/151552的线性特例，刻意把最终uniform放在高质量token CDF区间中点，避免把归约误差边界当算法错误。测试还提供可选perf计时函数，其存在不表示本次有测速结果。

本次仅阅读源码与测试定义，没有执行上游代码、编译、真机、数值、图捕获或性能测试。核验须同时比较有效接受前缀、计数、flat预测槽、拒绝scratch、最终分布及下一轮状态；不能仅看当前token。上层[Eagle树接入](../../guides/integration/sglang_ascend/sglang_ascend_spec_tree_verify.md)与[DFlash能力守卫](../../guides/integration/sglang_ascend/sglang_ascend_spec_dflash_sampling_boundary.md)仍分别有效；内核提供target-only原语不等于NPU DFlash已开放非greedy模式。
