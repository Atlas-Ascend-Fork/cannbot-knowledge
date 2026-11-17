---
{
  "type": "Runbook",
  "title": "mega_moe 内核打点：按角色、marker 和 worker 写入设备计数器",
  "description": "记录 get_system_cycle 与 scalar.store_bypass 的设备侧打点布局；时钟频率、扰动和跨 rank 对齐须单独核定。",
  "tags": [
    "task.implementation",
    "topic.performance.analysis"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# mega_moe 内核打点：按角色、marker 和 worker 写入设备计数器

## 适用场景

CannBot-DSL mega_moe 的 AIC/AIV 多角色流水分析。需使用实际平台的计数器频率和对应 host 解析器。

## 触发与观测

外部算子总耗时无法直接定位内核内部阶段，源码提供 enable_stage_timing 控制的 marker 写入入口。

## 探针与操作

确认开关、role 常量与缓冲区 shape 后插入打点。按真实 marker 表配对阶段，保留 rank、worker 身份和原始计数值。

源码函数单元（依赖所属模块上下文）：

```python
def _stage_timestamp(
    self, stage_timing_gm: Tensor, marker, role, core
):
    if self.enable_stage_timing:
        worker = get_block_idx()
        scalar.store_bypass(
            stage_timing_gm.ptr((role, marker, worker, 0)),
            get_system_cycle(),
            core=core,
        )

@jit
def _stage_timestamp_aic(self, stage_timing_gm: Tensor, marker):
    self._stage_timestamp(
        stage_timing_gm, marker, STAGE_TIMING_ROLE_AIC, "aic"
    )
```

## 机制与判别

该实现用 get_block_idx() 定位 worker，并将 get_system_cycle() 写到 stage_timing_gm 的 (role, marker, worker, 0) 位置。三个角色需分别解释；store_bypass 的使用本身不证明测量无扰动或写入已全局可见。

## 验证信号

原始源码读取给出打点函数和 AIC 包装入口。已有设备分段记录可用于说明设施被使用，但本卡不据此验证计数器单位、绝对阶段时长或零开销。

## 适用与失效边界

不要直接把 cycles/1000 当成通用微秒换算；先核定设备频率。各 rank 独立归零不构成跨 rank 时钟同步。开关关闭后的开销与测量扰动需要独立对照。
