---
{
  "type": "Runbook",
  "title": "ops-transformer EngramFetchTrain 训练态 SF 分发缺陷：sfTableAddr 未使用致 fetched_sf 全零（!12399@91207eff7）",
  "description": "框架/模型链路：torchtitan-npu DeepSeek-V4.1 Engram MXFP8 训练，经 ElasticBuffer 注册 Host pinned CPU 的 E4M3 表与 E8M0 SF 表，`engram_fetch(with_grad=True)` 跨卡取行。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:05Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "950"
  ]
}
---

# ops-transformer EngramFetchTrain 训练态 SF 分发缺陷：sfTableAddr 未使用致 fetched_sf 全零（!12399@91207eff7）

## 适用场景

- 平台范围依据：source 0 seq 1996的实际环境/设备记录确认本次为Ascend 950；这里不扩展未记录的产品或版本。

- 框架/模型链路：torchtitan-npu DeepSeek-V4.1 Engram MXFP8 训练，经 ElasticBuffer 注册 Host pinned CPU 的 E4M3 表与 E8M0 SF 表，`engram_fetch(with_grad=True)` 跨卡取行。
- 平台/版本：Ascend 950DT 单机四卡；ops-transformer MR `!12399`，缺陷 head `91207eff7ab025f64ec5248012008cf40ad391de`，修复 head `64e68094286c5d571c236a9390f72925bff6226e`；issue `cann/ops-transformer#5518`。
- 目标：判断"FP8 数据 Fetch 正确但 SF 全错"时是自有接入代码问题还是算子问题。

## 触发与观测

- 触发：四卡 MXFP8 探针（run.sh mxfp8）中 E4M3 数据四个 rank 逐元素一致、`max_abs_error=0`，而 E8M0 `fetched_sf` 四个 rank 均 512/512 元素不匹配，最大误差恰为 `1/256`（期望 scale 全为 1/256、实际疑似全零）；后续 `ERR99999`/SIGTERM 为断言失败连带退出（source 0 seq 1424，tool_observed）。

## 探针与操作

- 判别探针：对 `!12399` 做 `git diff f5e957d86..91207eff7` 与 `git show 91207eff7:...elastic_buffer.cpp` 追 SF 注册与调用链（source 0 seq 1425、seq 1430，source_read）。
- 版本探针：训练态接口自检 `training_sf_api`（`engram_fetch(with_grad=True)` 是否具备 `_local_sf_table_addr`）可在测试启动前拦截旧 wheel（source 0 seq 1214，tool_observed）。

## 机制与判别

- 根因链（source 0 seq 1514，source_read + 工具日志交叉）：Python 层把 `_local_sf_table_addr` 传给 `engram_fetch_train`；C++ `ElasticBuffer::EngramFetchTrain` 也接收 `sfTableAddr`；但调用 `aclnnEngramFetch` 时 `sf_table` 位置仍传 `nullTensor`，`sfTableAddr` 完全未使用；tiling 仅当 `sf_table` 输入非空才选 `HasSf=true`，于是执行了无 SF 训练 kernel，`fetched_sf` 未写入，而 FP8 数据本体仍正确返回。自 `d39238d7a` 引入 SF 模板分发逻辑起存在。
- 判别要点：SF 全量不匹配且最大差恰等于参考 scale 值（1/256）⇒ SF 通路整体未写，而非量化误差；数据通路零误差 ⇒ 通信域注册与 Fetch 主体正常。
- 修复（上游 `64e680942`，user_reported + 源码摘要 source 0 seq 1726/1762）：取消依赖 `sf_table` input 的 `HasSf` tiling key，kernel 依据已注册 SF 地址和输出 shape 运行时选择 SF 路径；每行 4 字节的 E8M0 SF 在 UB 中按 32 字节对齐；Torch extension 无变化，只需重编 `.run`。

## 验证信号

- 修复前观测：四卡 SF 512/512 不匹配、max diff 1/256、数据 max_abs_error=0（source 0 seq 1424，tool_observed）。
- 修复后独立复测（本方四卡，重编安装 `!12399@64e680942`）：MXFP8 连续两步 Fetch 数据/SF、FetchGrad、两次 SparseAdam 后触达行重量化全部四卡 `max_abs_error=0`，`rc=0`；无 SF 的 FP32 回归路径同样两步零误差（source 0 seq 1786、seq 1980，device_functional）。issue #5518 已附复测并关闭（source 0 seq 1624）。

## 适用与失效边界

- 适用：使用 `!12399`（91207eff7 及之前含 `d39238d7a` 的 head）构建的 Engram 训练态 SF 路径；症状为数据正确、SF 全零。
- 部署侧同类陷阱：构建产物 `.run`/wheel 生成后未安装时，venv 中旧 wheel 仍被加载，`training_sf_api: False` 是有效判别探针（source 0 seq 1214、seq 1400/1405）；替换 wheel 后需清理旧 JIT 缓存（source 0 seq 1686，agent 叙述+操作记录）。
- `.run` 与 wheel 必须来自同一提交，否则接口面可能不一致（source 0 seq 1686，agent 叙述）。

## 附：断言存档

- ops-transformer !12399@91207eff7 训练态 EngramFetch 中 sfTableAddr 未使用、aclnnEngramFetch 的 sf_table 位置传 nullTensor，tiling 因此选择 HasSf=false，fetched_sf 不写入；症状为四卡 E4M3 数据 max_abs_error=0 而 SF 512/512 不匹配、最大差恰为期望 scale 1/256

```text
1. Python 层把 `_local_sf_table_addr` 传给 `engram_fetch_train`。
2. C++ 的 `EngramFetchTrain` 也接收 `sfTableAddr` 参数。
3. 但它实际调用 `aclnnEngramFetch` 时，`sf_table` 位置传入了 `nullTensor`，`sfTableAddr` 完全没有使用。
4. 最新 tiling 只有在 `sf_table` 输入非空时才选择 `HasSf=true`。
5. 因此实际执行了无 SF 的训练 kernel，`fetched_sf` 没有被写入，而 FP8 数据本体仍能正确返回。
```
