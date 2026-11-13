---
{
  "type": "Runbook",
  "title": "外部 AI 的 FIA 精度修复 patch（tiling cap + 均分 + PipeBarrier）在已测 kv=512/1000/1024/1293 失败",
  "description": "评估外部 AI/其他助手针对 FIA（fused_infer_attention_score）精度问题给出的 patch 方案时的可信度判别。 场景：ascend910_93、ops-transformer 仓的 FIA 算子（D=1024 MLA、BAND sparse_mode=4），已有两套\"tiling 层调整 + PipeBarrier\"思路的修改，需要判断它们是否真正解决精度问题。 知识形态：negative_result（attempt / failure / boundary，不伪称成功）。",
  "tags": [
    "task.debugging",
    "topic.attention"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "a3"
  ]
}
---
# 外部 AI 的 FIA 精度修复 patch（tiling cap + 均分 + PipeBarrier）在已测 kv=512/1000/1024/1293 失败

## 适用场景

- 评估外部 AI/其他助手针对 FIA（fused_infer_attention_score）精度问题给出的 patch 方案时的可信度判别。
- 场景：ascend910_93、ops-transformer 仓的 FIA 算子（D=1024 MLA、BAND sparse_mode=4），已有两套"tiling 层调整 + PipeBarrier"思路的修改，需要判断它们是否真正解决精度问题。

## 触发与观测

- 尝试对象：外部 AI 助手基于干净 master 分支的 patch，核心内容为 tiling cap=1024 + tail≤576 均分 + PipeBarrier<PIPE_FIX> + CalcMaxWorkspaceSize s2BaseSize 修复 + vec 层 headDim 变量化。
- 客观失败数据（单 batch、逐 kv 长度扫描，tool_result）——来源结论：外部 patch 应用到干净仓库并直装内核后，单 batch 精度实测 kv=400 与 500 通过（out_diff=0.0039、lse_diff≈1e-6），kv=512、1000、1024、1293 全部失败（out_diff 分别为 0.733、1.306、1.330、0.792，lse_diff 均约 1e12），在已测点中，512 是最小失败长度；500 与 512 之间以及其他未测长度的边界未知。

## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${CONTAINER_NAME}`：复现环境的容器名称或 ID。
- `${CONTAINER_WORKDIR}`：复现容器中的工程工作根目录。
- `${SCRATCH_DIR}`：由复现者创建的本次实验临时目录。


- 操作流程（完整复现路径）：
  1. 分析 patch 的 tiling 层与 kernel 层修改点（cap=1024 + tail≤576 均分；PipeBarrier + vec 层 headDim 变量化）。
  2. 将 patch 应用到干净的 ops-transformer master 分支，`bash build.sh --pkg --ops=fused_infer_attention_score --soc=ascend910_93 -j64` 编译。
  3. 把内核二进制与配置直装 CANN vendor 目录（kernel bin、binary_info_config.json、ops-info、libcust_opmaster_rt2.0.so、libcust_opapi.so）。
  4. 逐 kv 长度跑精度对比（golden 为非融合 float32 实现）。测试命令：

```text
docker cp ${SCRATCH_DIR}/opencode/fia_varlen_test.py ${CONTAINER_NAME}:${CONTAINER_WORKDIR}/fia_varlen_test.py 2>/dev/null; docker exec ${CONTAINER_NAME} bash -c "cd ${CONTAINER_WORKDIR} && timeout 30 python3 -c \"
import torch, torch_npu
from fia_varlen_test import make_test_data, compute_golden_unfused, call_fia

for kv in [400, 500, 512, 1000, 1024, 1293]:
    data = make_test_data([kv], [1], D=1024, P=64, N=4, block_size=128, scale=0.0625, device='cpu', seed=42)
    golden = compute_golden_unfused(data)
    out, lse = call_fia(data, 'npu:0')
    out_d = (golden['output'].float() - out.float()).abs().max().item()
    lse_d = (golden['lse'].float() - lse.float()).abs().max().item()
    status = 'OK' if out_d < 0.01 else 'ERR'
    print(f'kv={kv:4d}: out_diff={out_d:.8f} lse_diff={lse_d:.8f} [{status}]')
\" 2>&1; echo EXIT=\$?"
```

## 机制与判别

- 判别逻辑：
  1. 外部 patch 的"tail≤576 均分"只是把"小 tail"换成"均分两块"，未能解决精度问题。
  2. vec 层 headDim 变量化在 HEAD 代码已包含，与本问题无差异。

## 验证信号

  - kv=400/500 OK（0.0039 / 1e-6）；kv=512/1000/1024/1293 ERR（0.733/1.306/1.330/0.792，lse≈1e12）。
  - 多 batch 的独立失败矩阵见 [FIA 多 batch 精度诊断](fia_multibatch_precision_fixs2basesize.md)。
- 安装有效性信号：直装后 vendor 目录 kernel 文件数（52）、libcust_opmaster.so md5 更新记录，排除"没装上"的干扰假设。

## 适用与失效边界

- 结论边界：本负结果只覆盖来源安装的这份具体 patch 及已测点（D=1024 MLA、BAND、ascend910_93）；它不能证明 FIA 精度问题不可修，也不能证明同类思路的其他实现均不可行。
- 评估外部 patch 的通用教训：patch 声称的修复效果必须在本环境以多 batch 变长 + 多 kv 长度矩阵复测；golden 验证只做单 batch 固定 kv_len 会漏掉整类问题。
