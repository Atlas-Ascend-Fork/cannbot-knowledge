---
type: Optimization
title: 极值索引单趟融合与选中位置单点失效
description: 把极值、位置查找和删除的多趟扫描融合为单趟值索引更新，再用单点Scatter失效选中项。
tags:
- task.optimization
- topic.programming_model.execution_unit.vector
- topic.implementation.synchronization
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cannbot-skills/blob/caff8714bf2ad1daef619df998a08e17eb3e9bf9/ops/ascendc-performance-strategy-engine/strategy/vec-A5/single-pass-extremum-index-point-invalidation.md
  role: primary
created_at: '2026-11-13T07:22:04Z'
updated_at: '2026-11-13T07:22:04Z'
platforms:
- '950'
---

<!-- strategy-metadata
{
  "id": "single-pass-extremum-index-point-invalidation",
  "name": "极值索引单趟融合与选中位置单点失效",
  "classification": "validated_strategy",
  "slug": "single-pass-extremum-index-point-invalidation",
  "generality": "dataflow_pattern",
  "feature_signature": {
    "pattern": "single-pass-extremum-index-point-invalidation"
  },
  "verification": {
    "status": "validated_with_preconditions",
    "attribution": "在固定布局下验证扫描合并机制；不同数值域和失效编码须重新验证。",
    "migration_required": true
  }
}
-->

# 性能优化策略：极值索引单趟融合与选中位置单点失效

> 单一优化点：把取极值、寻找位置和删除选中项的多趟扫描，改为单趟同步维护值与索引，再以单点Scatter使选中位置失效。

## 1. 原理

按位置顺序扫描，每次比较候选值与运行极值，同时更新位置编码。严格比较可保留首个等值位置；采用非严格比较则会改变并列选择规则，必须由契约决定。

一轮选择结束后，按选中位置直接写入失效标记，替代遍历全部候选寻找并删除命中项。后续读取前闭合片上store到load依赖；若最后一轮没有任何后继消费者，可以删除不再被读取的失效写入。

失效标记与最小有效值不能混同。若全数值域内不存在严格更差的哨兵，应同时维护有效性信息，并把有效性纳入比较。

## 2. 性能问题模式

- 每轮分别扫描极值、匹配位置和删除选中项。
- 索引维护占用额外读回和比较，而最大值状态已在向量中。
- 每次只删除少量位置，却反复重写整个工作缓冲。

## 3. 正确性红线

- 定义并列优先位置、NaN、正负零和极值的处理；不能默认严格GT适合所有契约。
- 只修改私有工作缓冲，原输入和其他消费者可见的数据不得被失效操作破坏。
- 验证选中位置范围、地址乘加宽度与输出位置唯一性；单点Scatter不能越界或跨行。
- 失效标记须严格劣于所有合法候选，或使用独立有效位解决哨兵与真实最值碰撞。
- 下一轮读取前建立RAW屏障；只有证明不存在后继读取时才省略末轮失效。

## 4. 泛化条件

适用：需要重复返回极值及位置；工作集可以片上驻留，选中位置可直接寻址且每轮失效项少。

不适用或需回退：输入不可复制也不可修改、失效会影响其他消费者、有效性无法无歧义表达，或单点随机写及同步成本更高。

## 5. 实施步骤

1. 冻结原比较、并列和有效性契约，确认三类扫描及工作缓冲所有权。
2. 单趟更新值和索引状态；明确首轮初始化与无有效候选的退出。
3. 以选中位置执行单点失效，并建立下一轮的store到load可见性。
4. 覆盖重复极值、全等、最值、尾部及全部失效边界。
5. 在布局和其他算法固定时独立测量，检查扫描减少是否转化为总耗时收益。

## 6. LLM 前置问题

- 等值时保留首位置还是末位置？
- 哨兵会不会与真实候选碰撞？
- 删除写入有哪个后继消费者，屏障何时必须保留？
- 工作缓冲是否为当前任务独占？

## 7. 验收标准

正确性：保持原接口、精度阈值和输出布局，覆盖空域、尾部、容量边界、重复值和所有受影响分支。先验证语义与合法访问，再判断收益；不放宽阈值以迁就新路径。

性能：冻结前后源码和二进制，同设备、同输入、同工具链，依照配对测量协议比较设备Task Duration；每个输入域先取均值，再按约定跨域聚合，保留域内回归和剔除补测记录。迁移到新的资源、布局或数值域必须重新验证。

决策：资源、越界、同步或精度检查失败时修复或回退；没有可信收益时保留原路径。组合验证不能推出任何子动作独立有效。

## 8. 与相邻策略的边界

与[per-lane-running-argmax-scan](per_lane_running_argmax_scan.md)的延后跨lane合并不同，本策略处理重复选择中的位置查找和失效扫描；与[vectorized-arg-index-reduce](vectorized_arg_index_reduce.md)不同，不依赖先求极值再做独立EQ回溯。

## 检索卡（短卡）

动作：把极值、位置查找和删除的多趟扫描融合为单趟值索引更新，再用单点Scatter失效选中项。
适用：重复极值选择需返回位置，工作缓冲可驻片上且选中位置可直接寻址。
限制：保留并列与特殊值语义；哨兵须严格劣于真值或另设有效位；失效后建立RAW屏障。
范围：重复选择、带索引极值与候选淘汰。
检索词：Compare、Max、Select、Scatter、LocalMemBar、有效位
机会：每轮多次扫描相同候选，仅删除少量位置却重写整片缓冲。
代价：比较依赖链、随机写和同步可能抵消扫描节省。
