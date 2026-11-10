---
{
  "type": "Runbook",
  "title": "cann-recipes-infer LongBench 加载失败：datasets 4.8.5 降级 3.6.0 修复「Dataset scripts are no longer supported」",
  "description": "cann-recipes-infer 的 load_longbench_dataset 对本地 dataset/LongBench 目录（含 LongBench.py 数据集脚本）调用 load_dataset(trust_remote_code=True)，环境预装的 datasets 4.8.5 已移除数据集脚本支持，导致 ge_graph 样例 16 rank 全部在数据集加载阶段以 RuntimeError: Dataset scripts are no longer supported, but found LongBench.py（ERR99999）失败。按 models/qwen3_moe/requirements.txt 声明降级 pip3 install datasets==3.6.0 后，narrativeqa 加载成功（200 条），同环境 LongBench 样例（eager）完整跑通且输出通顺。",
  "tags": [
    "task.debugging",
    "topic.graph_execution",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-03T12:00:00Z",
  "platforms": [
    "a3"
  ]
}
---

# cann-recipes-infer LongBench 加载失败：datasets 4.8.5 降级 3.6.0 修复「Dataset scripts are no longer supported」

## 适用场景

- 框架/仓库：cann-recipes-infer，使用本地 LongBench 数据集（`dataset/LongBench/` 目录含 `LongBench.py` 数据集脚本与 `data/*.jsonl`）的样例（YAML `dataset: "LongBench"`）。
- 环境（来源轨迹 来源记录，2026-10-14）：Atlas A3（Ascend 910_9362 ×16）、CANN 9.2.0、Python 3.11.15（conda `recipes_infer_py311`）、torch 2.10.0+cpu、torch_npu 2.10.0.post7.dev20260924、transformers 5.0.0；环境预装 datasets 4.8.5，而 `models/qwen3_moe/requirements.txt` 声明 `datasets==3.6.0`。
- 目标：让 `load_longbench_dataset` 能加载本地 LongBench（`load_dataset('dataset/LongBench', <task>, split='test', trust_remote_code=True)`），不改动仓库代码。

## 触发与观测

触发条件：环境 datasets ≥ 4.x（本例 4.8.5）且数据集以脚本目录形式提供。现象：样例启动后 16 rank 全部在数据集加载阶段失败（ERR99999），推理未开始。

c1：cann-recipes-infer 的 load_longbench_dataset（executor/utils/data_utils.py:175）对本地 dataset/LongBench 目录（含 LongBench.py 数据集脚本）调用 load_dataset(trust_remote_code=True)，datasets 4.8.5 已移除数据集脚本支持，16 rank 全部报「RuntimeError: Dataset scripts are no longer supported, but found LongBench.py」（ERR99999）

逐字报错（`models/qwen3_moe/res/20261014/qwen3_moe_qwen3_235b_16tp/log_0.log`）：

```
12:[ERROR][2026-10-14 22:59:31.142][load.py:1663] `trust_remote_code` is not supported anymore.
15:Traceback (most recent call last):
34:    raise RuntimeError(f"Dataset scripts are no longer supported, but found {filename}")
35:RuntimeError: Dataset scripts are no longer supported, but found LongBench.py
36:[ERROR] 2026-10-14-22:59:31 (PID:3134811, Device:-1, RankID:-1) ERR99999 UNKNOWN applicaiton exception
```

失败前置事实：`python3 -c "import datasets; print(datasets.__version__)"` 输出 `4.8.5`（before，来源记录 seq 107）；`models/qwen3_moe/requirements.txt` 明确 `datasets==3.6.0`（seq 49）。加载逻辑本身（`data_utils.py` 中 `load_longbench_dataset` 对每个任务调用 `load_dataset(data_path, dataset, split='test', trust_remote_code=True)`）经代码阅读确认。

## 探针与操作

修复操作（单变量：仅降级 datasets，不动其他包与仓库代码）：

```
pip3 install datasets==3.6.0 2>&1 | tail -2; python3 -c "
from datasets import load_dataset
d = load_dataset('dataset/LongBench', 'narrativeqa', split='test', trust_remote_code=True)
print('OK', len(d))
" 2>&1 | tail -5
```

执行结果（after）：`Successfully installed datasets-3.6.0` 且加载验证输出 `OK 200`（narrativeqa 200 条）。

c2：按 models/qwen3_moe/requirements.txt 声明将 datasets 从 4.8.5 降级到 3.6.0 后，同一 load_dataset 调用加载 narrativeqa 成功（OK 200 条），此后 LongBench 样例（eager）完整跑通：decode 平均 299.88 ms/token、16 rank 输出通顺（单次观测）

## 机制与判别

- 机制：datasets 3.x→4.x 移除了对「数据集脚本（LongBench.py 这类 trust_remote_code 脚本）」的支持；cann-recipes-infer 的本地 LongBench 数据集正是以脚本目录形式分发（README 要求在 LongBench.py 中改本地 data 路径），因此 requirements 锁定 `datasets==3.6.0`。环境预装 4.8.5 与 requirements 不符即触发。
- 可区分分支：报错发生在数据集加载阶段（`[load.py:1663]`，权重尚未加载），与 ge_graph 图编译失败（发生在权重加载后的编译阶段）时间线与报错形态完全不同；本轨迹中两问题先后出现（先 datasets 失败，降级后重跑才暴露 ge_graph 失败），修复 datasets 不影响后者。
- 混杂变量声明：本修复只改了 datasets 版本一个变量；同会话先前还执行过 transformers 4.46.3→5.0.0 升级（按 requirements 过滤 torch 系包后安装），但该变更发生在首跑失败之前，与数据集修复无交互。

## 验证信号

（均在来源轨迹 来源记录 内，平台 Atlas A3 / CANN 9.2.0）

1. failure：seq 103——16 rank `RuntimeError: Dataset scripts are no longer supported, but found LongBench.py`（ERR99999）。
2. before：seq 107——datasets 4.8.5；seq 49——requirements 声明 datasets==3.6.0。
3. after：seq 117——`Successfully installed datasets-3.6.0` + narrativeqa 加载 `OK 200`。
4. 端到端验证：seq 139/158——降级后 ge_graph 样例重跑越过数据集加载进入图编译（后续失败与本修复无关），eager 样例（qwen3_235b_1tp_16ep）完整跑通：LongBench narrativeqa 摘要输出通顺（`<think>` 开头、内容与输入对应、256 token 处按配置截断），decode 平均 299.88 ms/token（batch 16，单次观测）。
5. 旁证：同机另一会话（来源记录，datasets 已是 3.6.0）中相同 LongBench 预检直接通过（`LongBench load OK, examples: 200`），未再出现该报错。

## 适用与失效边界

- 适用：cann-recipes-infer 本地 LongBench（脚本目录形式）+ datasets ≥ 4.x 环境报「Dataset scripts are no longer supported, but found LongBench.py」时，按对应模型 requirements.txt 降级 datasets 到 3.6.0。
- 失效/边界：
  - 降级 datasets 可能与其他依赖该库的模型/工具冲突（本环境 pip 输出中未出现 datasets 相关冲突，但多模型共享环境需自查）；根因侧的长期修复是把 LongBench 改为脚本无关的加载方式（仓库侧改进，本轨迹未实施）。
  - 该修复不解决 ge_graph 图编译失败（E90003/ERR03005），两者是独立问题。
  - `infer.sh` 失败时退出码仍为 0（本轨迹 seq 91/121/147 多次观测），验证数据集修复必须看日志中的加载与输出内容，不能只看退出码。
  - 200 条/299.88 ms 等数值为单次观测，仅作修复生效证据，不作性能基线。
