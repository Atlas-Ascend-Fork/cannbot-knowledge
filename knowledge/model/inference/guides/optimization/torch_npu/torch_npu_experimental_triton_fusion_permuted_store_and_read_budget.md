---
type: Guide
title: 实验 Triton 融合限制：置换写出与读 buffer 数
description: 区分父类和template优先序、归约加置换写出检测、unique buffer名称读数阈值与真实load/布局/资源边界。
tags:
- task.optimization
- topic.compilation
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py
  role: implementation
created_at: '2026-11-11T09:24:06Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# 实验 Triton 融合限制：置换写出与读 buffer 数

## 固定规则与顺序

针对 TorchNPU 主线 `ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf` 的实验 NPUTritonScheduling 两个完整局部方法、vertical/horizontal 别名和两项配置声明。发布固定快照在本轮两个精确实验路径缺失，只说明来源关系。未导入、调用 hint/调度/WhyNoFuse、生成代码或运行模型；注释中的编译耗时、8 倍收益和“绝不影响正确性”不是本次实验结论，产品范围未知。

can_fuse 的顺序是：先调用父类 can_fuse，拒绝就返回 False；任一侧包含 template 子节点则直接 True；然后是 reduction+置换写出限制；最后才是读 buffer 数上限。True 只表示这套局部检查没有拒绝，不能作为整个图已经融合或执行正确的证明。

## template 提前豁免

只要 node1/node2 任一 get_nodes() 中有 is_template()，且父类检查已通过，就跳过后面**两项**本地限制；不是跳过所有上游条件，也不是只给同构 MM 两侧一个豁免。模板自己的外部 epilogue、布局、资源和数值合同未在本卡展开。

## 置换写出的实际检测

默认 no_fuse_permuted_store=True。两侧任一子节点是 reduction，同时任一侧被 `_npu_writes_permuted_output` 检出时，记录 WhyNoFuse 并返回 False。实际条件没有要求“第一侧一定是 reduction producer、第二侧一定是其直接 consumer”，不能只照注释把它限缩成一种有向图模式。

helper 遍历各子节点的 read_writes.writes，经 scheduler.name_to_buf 取 IR node。没有 read_writes、找不到 buffer/node，或读取 layout/stride/size 发生 Exception 时，跳过该项。原 stride 数少于 2 也跳过。

随后把 stride、size 用 optimization_hint 转 int，按 zip 配对，剔除 size hint 等于 1 的维；剩不到两维不检测。其余仅判断：

```text
最后一个有效 stride != 1
或者任意相邻有效 stride 满足 前者 < 后者
```

命中任一条件就 True。它没有逐轴核验 `stride[i] == size[i+1]*stride[i+1]` 的 dense chain，也没有把相等的相邻 stride 一律拒绝；所以 False 不是通用连续性、无重叠或没有置换的证明。stride/size 长度不一致时 zip 只配到较短一边，未知/跳过项也不会在这里强制拒绝融合。

hint 转换在前述读取 layout 的 try 外，未统一吞掉异常。该检测依赖当前提示值，不是在本地为完整动态尺寸范围新建布局证明；源码的“strictly descending”文字也不能替代实际用 `<` 的谓词。

## 读数上限统计的是名称集合

默认 max_fused_reads=24。若它<=0，读数检查直接 True；但前面的 reduction+置换写出限制已经执行，设置 0 并不会同时关闭那条规则。

正上限时，遍历两侧各子节点的 read_writes.reads，将 dep.name 加入 set；缺 read_writes 的子节点跳过。只有**不同名称数量严格大于**上限才 WhyNoFuse 并 False，等于上限仍可通过。相同名重复依赖只算一次，write 不加入这份 set。

因此它不是最终 kernel 的 tl.load 指令数、读 dep 总条目数、指针 ABI 参数数或字节流量的精确上限；同一 buffer 可产生多次加载，不同名字也未在这里按底层 storage 别名合并。不能由“24 名称以内”推导真实中间值/UB、编译时间或整个 kernel 规模已经有同等数值的严格界限。

## 两个调度入口都显式绑定

类体将 can_fuse_vertical 和 can_fuse_horizontal 都指向本类 can_fuse。因此本地两个名字实际使用同一套顺序，而不只留下一个父类函数对象的别名。这里的显式父调用仍是 `super().can_fuse`；未展开上游调度器、其他过滤和最终融合采用流程，不把一个 override 等同于完整 compiler 规则已审阅。

整体也没有总 except：布局读取的局部跳过、部分缺失 metadata 的忽略和阈值关闭，不是任意 hint、配置类型、依赖/日志/父类异常都会变成安全拒绝或继续融合的协议。

排查融合数量、编译耗时或置换写出性能时，保留父类结果、template 分支、两侧 reduction/write 信息、hint 后的 size/stride、实际 unique read_names、两项有效配置和最终生成图，再验证数值和性能。本卡只解释局部拒绝理由，不新增设备支持或 verified。

## Evidence

- [固定源码 1](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/codegen/triton.py)（primary）：5931–6065；仅所列完整局部方法/别名/声明，上游调度与实际设备结果另计。
- [固定源码 2](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/_inductor/triton_experimental/config.py)（implementation）：56–56、364–364；仅所列完整局部方法/别名/声明，上游调度与实际设备结果另计。
