---
{
  "type": "Runbook",
  "title": "mega_moe combine 量化协议：ND tiling key 映射与单个双卡用例边界",
  "description": "记录 combineQuantMode 3/4 的映射与 ND 模板约束；区分 e5m2 二进制对拍、e4m3 精度测试和未完成的 e4m3 二进制对拍。",
  "tags": [
    "task.implementation",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": [
    "950"
  ]
}
---
# mega_moe combine 量化协议：ND tiling key 映射与单个双卡用例边界

## 适用场景

mega_moe A8W8 的 combine 输出量化迁移；启动前输出为 Ascend950PR，记录用例为 EP=2、moe=4、bs=128、h=2048、intermediate=512、topk=2。测试输入 x 为 BF16；--dtype=e4m3 控制权重量化类型和 dispatch_quant_out_dtype，combine 模式由独立选项指定。

## 触发与观测

需要核对 CLI 量化名称、协议值、tiling key 与实际实例化组合是否一致。

## 探针与操作

对照映射和 entry.cpp 的实例化范围，先拒绝未实例化组合，再按相同输入比对源算子、重实现及参考输出。下列片段属于测试入口配置。

从记录配置单元整理的 combine 映射；仅覆盖本卡采用的非零 combine/ND 范围：

```python
def configure_combine(a):
    a.combine_quant_mode = {'0': 0, 'e5m2': 3, 'e4m3': 4}[a.combine_quant]
    a.combine_quant_offset = {0: 0, 3: 16, 4: 20}[a.combine_quant_mode]
    if a.combine_quant_mode != 0:
        assert a.weight_format == 'nd'
        assert not a.topk_prefetch
    return a
```

## 机制与判别

该测试入口把 0/e5m2/e4m3 映射到协议值 0/3/4，combine_quant_offset 为 0/16/20。该版本 combine-quant 组合限定 ND，且不与 topk-prefetch 组合；这些是当前模板实例化范围，不能当作所有版本的协议保证。

## 验证信号

原始构建输出报告 Build OK。combine=e5m2 的双卡二进制对拍报告两 rank 的 y 字节一致、etn match=True、参考对比 PASS、Overall binary consistency: IDENTICAL 和 RC=0；另一次 combine=e4m3 的精度测试两 rank PASS、Overall PASS、RC=0。后续 e4m3 二进制对拍只有启动记录，不能沿用精度 PASS 作为其结果。

## 适用与失效边界

仅覆盖该版本模板与单个双卡配置，不包含性能收益、全部量化模式或更多并行规模。corr 显示值接近 1 不能替代实际逐字节比较；这里的一致性结论来自另行报告的字节比较。
