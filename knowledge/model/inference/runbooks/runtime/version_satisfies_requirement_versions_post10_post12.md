---
{
  "type": "Runbook",
  "title": "torch_npu 官方版本号与 pip 包名映射：v7.3.0 对应 torch-npu==2.7.1.post2",
  "description": "按 README/官方文档「Ascend Extension for PyTorch vX.Y.Z」口径（如 wan2.2-i2v 要求 A2/A3：torch_npu v7.3.0 + PyTorch 2.7.1，配套 CANN 8.5.0）在 pip 环境安装 torch_npu。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-24T01:53:53Z",
  "platforms": [
    "a3"
  ]
}
---

# torch_npu 官方版本号与 pip 包名映射：v7.3.0 对应 torch-npu==2.7.1.post2

## 适用场景

- 平台范围依据：source 0 seq 1的实际环境/设备记录确认本次为Atlas A3；这里不扩展未记录的产品或版本。

- 按 README/官方文档「Ascend Extension for PyTorch vX.Y.Z」口径（如 wan2.2-i2v 要求 A2/A3：torch_npu v7.3.0 + PyTorch 2.7.1，配套 CANN 8.5.0）在 pip 环境安装 torch_npu。

## 触发与观测

- 触发（source 0 seq 74，tool_observed，逐字）：

```text
ERROR: Could not find a version that satisfies the requirement torch-npu==7.3.0 (from versions: 2.1.0.post8, ... 2.7.1, 2.7.1.post2, 2.7.1.post4, ... 2.9.0.post2, ...)
```

- PyPI 上 torch-npu 只有 `{PyTorch 版本}.postN` 命名；官方文档页（hiascend）为 JS 渲染无法抓取配套表。

## 探针与操作

- 探针（source 0 seq 98/109-110，tool_observed）：查询 `https://pypi.org/pypi/torch-npu/{ver}/json` 的 description——postX 系列 wheel 的 PyPI 描述内嵌配套表，逐字：

```text
| CANN 8.5.0            | 2.9.0                     | 2.9.0                       | v2.9.0-7.3.0      |
|                       | 2.7.1                     | 2.7.1.post2                 | v2.7.1-7.3.0      |
```

- 结论：官方 v7.3.0（CANN 8.5.0 配套、PyTorch 2.7.1）→ pip 包 `torch-npu==2.7.1.post2`（GitHub 分支 v2.7.1-7.3.0）。命名约定为 `{PyTorch version}-{Ascend version}`。

## 机制与判别

- 机制：torch_npu 官方发布用 v7.x.y（Ascend 侧版本），pip 包版本跟随 PyTorch 版本号 + postN 后缀；两端映射只记录在 wheel 的 PyPI description 配套表里，文档页抓不到时以 PyPI JSON description 为准。
- 判别：安装成功 + 后续在 CANN 9.2.0 环境完整跑通 14B 推理（40 步视频生成），证明映射选择正确且 2.7.1.post2 与更高版本 CANN（9.2.0）兼容可用。

## 验证信号

- 安装逐字（source 0 seq 116，tool_observed）：`Successfully installed ... torch-2.7.1 torch-npu-2.7.1.post2 torchvision-0.22.1 ...`。
- 端到端（source 0 seq 189，tool_observed）：CANN 9.2.0 上 40 步去噪 300.04s 出片成功（README 配套为 CANN 8.5.0，实际 9.2.0 可运行）。

## 适用与失效边界

- 适用：torch_npu v7.x 官方版本号 → pip 包名的通用解析路径（PyPI JSON description 配套表）。
- 失效/停止：postN 与 v7.x 的具体对应随版本演进需每次查表，不可凭记忆推断；CANN 高于配套版本（8.5.0→9.2.0）在本例可用但不构成兼容承诺，遇到算子异常应先回配套版本排查。

## 附：断言存档

- torch_npu 官方版本号 v7.3.0（CANN 8.5.0 配套、PyTorch 2.7.1）对应 pip 包 torch-npu==2.7.1.post2：PyPI 无 7.x 版本号，映射记录在 wheel 的 PyPI description 配套表（分支命名 {PyTorch版本}-{Ascend版本}）

```text
ERROR: Could not find a version that satisfies the requirement torch-npu==7.3.0 (from versions: 2.1.0.post8, 2.1.0.post10, 2.1.0.post12, 2.1.0.post13, 2.1.0.post17, 2.3.1.post2, 2.3.1.post4, 2.3.1.post6, 2.4.0, 2.4.0.post2, 2.4.0.post4, 2.5.1rc1, 2.5.1, 2.5.1.post1, 2.6.0rc1, 2.6.0, 2.6.0.post3, 2.6.0.post5, 2.7.1rc1, 2.7.1, 2.7.1.post2, 2.7.1.post4, 2.7.1.post6, 2.7.1.post8, 2.7.1.post10, 2.7.1.post11, 2.8.0rc1, 2.8.0, 2.8.0.post2, 2.8.0.post4, 2.8.0.post5, 2.9.0rc1, 2.9.0, 2.9.0.post2, 2.9.0.p
```
