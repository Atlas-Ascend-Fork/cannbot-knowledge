---
type: API
title: SGL经典链拒绝采样的真实提案分布与残差抽样
description: 说明chain_speculative_sampling_triton的严格接受比较、线性输出跨度、三阶段临时区和最终残差CDF，区分被忽略的树及阈值参数。
tags:
- task.implementation
- topic.speculative_decoding
- topic.memory
- topic.precision
status: draft
sources:
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/sample/chain_speculative_sampling.py
  role: primary
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/sample/__init__.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/python/sgl_kernel_npu/sgl_kernel_npu/utils/triton_utils.py
  role: implementation
- resource: https://github.com/sgl-project/sgl-kernel-npu/blob/dda6d36b0cdb4081e102d14c0a2fb276fc416e69/tests/python/sgl_kernel_npu/test_chain_speculative_sampling.py
  role: evidence
created_at: '2026-11-09T12:42:57Z'
updated_at: '2026-11-09T12:42:57Z'
platforms: []
aliases:
- chain_speculative_sampling_triton
---

# SGL经典链拒绝采样的真实提案分布与残差抽样

## 调用与数据域

```python
from sgl_kernel_npu.sample import chain_speculative_sampling_triton

chain_speculative_sampling_triton(
    predicts, accept_index, accept_token_num, candidates,
    retrive_index, retrive_next_token, retrive_next_sibling,
    uniform_samples, uniform_samples_for_final_sampling,
    target_probs, draft_probs,
    threshold_single=1.0, threshold_acc=1.0, deterministic=True,
)
```

入口原地写三个输出buffer、返回None。设B为请求数、N为含root的候选数、V为词表大小、Q为提案概率行数。`candidates/retrive_index`为int64 `[B,N]`，`target_probs`为FP32 `[B,N,V]`，`draft_probs`为FP32 `[B,Q,V]`且`Q>=max(N-1,1)`；它是真实提案分布输入，不被清零或改写。`uniform_samples`为FP32 `[B,N]`，最终抽样uniform为FP32 `[B]`。

`predicts`是一维int32调用方输出池；`accept_index`必须int32 `[B,N]`，强制topk1线性链；`accept_token_num`为int32 `[B]`。所有实际消费Tensor须与target_probs同设备且连续。检查比较device相等，没有额外验证`device.type==npu`；实际launch仍需要可用NPU Triton环境。N=0在非空batch下报错；B=0在仅检查candidates/target rank后早返，后续shape/dtype/device检查与写出均不执行。

`retrive_next_token/retrive_next_sibling`直接被丢弃，三个控制参数`threshold_single/threshold_acc/deterministic`也被丢弃。传非默认值不改变算法，不能据签名宣称树遍历、阈值加速接受或确定性执行模式。设备、具体产品矩阵与CANN版本没有被本入口固定，保持平台未定位草稿；本卡是源码接口蒸馏，不发布缺少平台/版本证据的完整Operator卡。

## 严格接受与输出槽位

每请求从`cur_prob_row=0`、root的flat `retrive_index[b,0]`开始，将root写入`accept_index[b,0]`。对`step=1..N-1`，只在尚未拒绝时读取candidate token，使用上一已接受节点对应的target/draft行及`uniform_samples[b,step-1]`，按严格条件`coin*draft_prob < target_prob`接受。这里没有显式计算比值；p=q=0时条件为假，不能替换成包含等号的规则。

接受时先将candidate写到前一个已接受节点的predicts槽，再把当前`retrive_index[b,step]`加入accept_index；计数加1，概率行切到step。首个拒绝终止后续接受判断。`accept_token_num=a`不含root；有效accept_index为前`a+1`项，其余调用方原值不被清理。最后bonus写在`accept_index[b,a]`对应的predicts槽，不能固定取最后一个draft槽。uniform最后一列不参与接受判断。

caller须保证token在`[0,V)`、retrive_index可作为predicts有效flat下标、输出没有跨请求写冲突。shape检查不验证这些设备值、概率非负/归一化/有限性或uniform值域；int64槽号最终写入int32 accept_index还需要可表示。传入树指针不会修复候选排列或输出跨度错误。

## 三阶段残差与CDF

Host固定分配int64 `metadata[B,3]`与FP32 `block_sums[B,ceil(V/2048)]`。有效载荷分别为`24*B`和`4*B*ceil(V/2048)`字节，不等于物理分配器占用。依次launch接受、分块求和、最终抽样三个本仓Triton节点；metadata保存`[最终target行, 最终输出槽, 是否全接受]`，后两阶段只读该状态。

全接受时最终分布为最后target行；发生拒绝时为`max(target-draft,0)`。分块节点按2048词元tile求和，program数限制为`min(B*ceil(V/2048), num_vectorcore)`，grid stride覆盖全部请求/块，尾块masked load明确补0。最终节点每请求读取补齐至2次幂的块和，计算块CDF及total，以`final_uniform*total`选择块，再重读所选块的target/draft重建残差、做局部CDF。无需物化整个`[B,V]`残差，但并未消除target/draft全词表输入。

两层逆CDF都通过计数`cdf<=target`跳过已经到达的累计质量，块号限制到最后块。若局部计数落到有效词元域外，回退到所选块最后一个正残差词元；该块无正质量时回退词表最后token。全零残差因此落到`V-1`，并非抛出错误或重抽样。调用方应提供合法uniform及正质量分布；代码未检查`[0,1)`，不能把uniform=1或负数的实现终点当正常采样承诺。分层FP32 reduction/CDF与一次整行串行CDF的舍入次序不同，靠近CDF边界时不能无条件要求相同token。

V没有显式正值校验；V=0会进入零块launch/索引域，不能因其他shape通过就视为支持。临时metadata/block_sums由Host Tensor持有至launch提交；它们的异步回收与stream可见性依赖匹配Triton/Torch运行时，本文件没有额外event或跨stream同步。输入/output池须由caller保活并避免错误别名。`get_device_properties()`无参数cache只保留首次current_device核数，切换设备后不自动重查。

## 验证定义与集成

固定测试提供CPU经典拒绝参考，覆盖B2/N4/V11的接受与首拒、以及V151552的多词表块循环，比较predicts、accept_index与计数；测试名称中的GPU算法只表示参考来源，代码实际调用NPU入口。本次未执行测试或分布统计，没有产品矩阵、图捕获或性能验收结论。

接入应核对真实proposal分布、target过滤温度、uniform行宽、root与bonus、有效输出前缀及下一轮状态提交；不能用target-only的清零scratch替代draft输入。SGLang上层cutoff及输出解释见[DSpark链采样接入](../../guides/integration/sglang_ascend/sglang_ascend_spec_dspark_chain_sampling.md)，树语义另见[target-only树接口](sgl_tree_target_only_sampling.md)。两个固定上游快照不自动构成发布wheel兼容证明。
