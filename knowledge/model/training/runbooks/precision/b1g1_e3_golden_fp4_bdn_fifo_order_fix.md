---
{
  "type": "Runbook",
  "title": "GMM1 行分块改造的 FIFO 风险：权重链不能随消费者循环重复",
  "description": "fp4 权重预取链按 kb/half/nsub 顺序消费；把它放进额外行分块循环后需重审事务次数。记录的修正只闭合静态与编译检查，设备重跑未收口。",
  "tags": [
    "task.debugging",
    "topic.precision"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# GMM1 行分块改造的 FIFO 风险：权重链不能随消费者循环重复

## 适用场景

CannBot-DSL GMM1 的 fp4_bdn 预取链与 16 行 A 消费路径改造。

## 触发与观测

新增 producer 形态后，设备 golden 在多 rank 报大幅数值失败。没有匹配的基线通过原始结果，不组成完整数值 A/B。

## 探针与操作

分别列出每个 job 的 prime、commit、wait 次数，以及行分块是否重复推进同一条权重 FIFO；再比较 consumer 切片和编译回归。

事务计数审查要点；设备修复尚未闭环：

```text
prime: once per job
consume order: (kb, half, nsub)
additional A-row loop: must not advance the same weight FIFO again
status: static/compiler checks only; device golden result unavailable
```

## 机制与判别

该静态分析发现，按 flat 序号消费的权重链不能仅因 A 侧增加 t8 循环就重复推进。修正方向是把权重链保留在原消费层，让多个 A 行分块读取已就绪的权重；这仍需匹配真实 FIFO 规则验证。

## 验证信号

记录有修改后的 L0 157 passed、L1 6/6 编译通过和 consumer 切片比较。设备 golden 重跑只记录提交，没有最终结果；不写成数值问题已经修复。

## 适用与失效边界

本记录覆盖 fp4_bdn 的静态/编译检查。其他权重布局与设备多波情况不能外推；必须取得修改版本的设备输出后再形成修复闭环。
