---
{
  "type": "Runbook",
  "title": "torchtitan-npu quant_meta.json 写入 checkpoint 目录干扰初始权重加载（移至 dump_folder 修复）",
  "description": "框架：torchtitan-npu QAT 训练（DSV4 mini1b yelp SFT QAT 场景，torchtitan checkpoint DCP 保存）。；任务：fake-quant MXFP8 converter 的 `quant_meta.json`（供离线导出/评测校验折叠配置，`--fake-quant auto` 依赖）落盘位置修复。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:03Z",
  "updated_at": "2026-11-20T14:17:03Z",
  "platforms": []
}
---

# torchtitan-npu quant_meta.json 写入 checkpoint 目录干扰初始权重加载（移至 dump_folder 修复）

## 适用场景

- 框架：torchtitan-npu QAT 训练（DSV4 mini1b yelp SFT QAT 场景，torchtitan checkpoint DCP 保存）。
- 任务：fake-quant MXFP8 converter 的 `quant_meta.json`（供离线导出/评测校验折叠配置，`--fake-quant auto` 依赖）落盘位置修复。

## 触发与观测

- 用户报告（user_reported，source 0 seq 4）："前边修复quant_meta 的存放问题, 但是其实还是有一些问题……我希望 quant_meta 应该和 tp / checkpoint 同级存放, 存放到 checkpoint 中会影响到初始权重的加载."
- 根因（source_observed，source 0 seq 104）："`write_quant_meta_for_trainer`（`quant_converter.py:166`）目前把 `quant_meta.json` 写到 `checkpointer.folder`，也就是 `<dump_folder>/checkpoint/`，和 DCP 的 `step-N` 分片放在同一个目录里。这会在 checkpoint 目录里留下一个非 DCP 的杂散文件，干扰初始权重加载。而读取侧 `find_quant_meta`（`quant_meta.py:100-111`）的 docstring 自己就写明:meta 应该位于 `<dump>`,checkpoint 在 `<dump>/checkpoint/step-N`——它会从 checkpoint 路径向上回溯最多 5 层来找。**也就是说写入侧和读取侧的约定本来就不一致,读取侧早已支持 `<dump>` 根目录。**"

## 探针与操作

- 探查：git show 439f112（前次 fix）、grep quant_meta 引用、核验 `dump_folder` 为 `Trainer.Config` 顶层字段且 `checkpointer.folder = os.path.join(dump_folder, checkpoint.folder)`、读 `find_quant_meta` 回溯逻辑。
- 修复（before/after，source 0 seq 155）：
  - before：写入 `checkpointer.folder`（`<dump>/checkpoint`），且受 `checkpointer.enable` 门控。
  - after："写入目标:`checkpointer.folder`(`<dump>/checkpoint`)→ `trainer.config.dump_folder`(`<dump>`,与 `checkpoint/`、`tp/`、`tb/` 同级)。去掉 `checkpointer.enable` 门控,不依赖 checkpointer——只要配了 fake-quant converter 就写,checkpoint 关闭也写。"
  - 读取侧不改："读取侧 `find_quant_meta` 本来就从 ckpt 路径向上回溯命中 `<dump>`,无需改动,离线 convert/eval 的 `--fake-quant auto` 照常工作。"
  - 配套注释同步四处（quant_converter build()、train.py docstring、config_registry.py、run_yelp_sft_qat_mini1b.sh）。

## 机制与判别

- 根因：写入侧与读取侧目录约定不一致；checkpoint 目录内非 DCP 杂散文件干扰初始权重加载（后者为用户报告的故障表现，本 trace 未单独复现）。
- 判别：读取侧 docstring/回溯逻辑早已支持 `<dump>` 根目录——移位后读取无需改动即为可区分证据。
- 已知残留：不删除旧 run 中已落错的 `<dump>/checkpoint/quant_meta.json`（新 run 不受影响）。

## 验证信号

- tool_observed（静态）：`python -m py_compile`（3 文件）+ `bash -n` 脚本均通过（source 0 seq 153/154）。
- 未做：训练重跑验证权重加载恢复——"干扰初始权重加载"的消除仅由根因分析支撑，无运行级复核（单次修复单次静态验证）。

## 适用与失效边界

- 适用于：torchtitan-npu QAT 训练的 quant_meta 落盘与离线 `--fake-quant auto` 定位。
- 失效边界：权重加载受扰的具体报错形态未记录；若读取侧回溯逻辑或目录约定再变更需重核。
- 停止条件：新 run 的 quant_meta 应位于 `<dump>/quant_meta.json`；旧 run 手动清理旧位置文件。

## 附：断言存档

- quant_meta.json 写入 checkpointer.folder（<dump>/checkpoint）在 checkpoint 目录留下非 DCP 杂散文件、干扰初始权重加载；读取侧 find_quant_meta 的 docstring 与 ≤5 层回溯逻辑早已约定 meta 位于 <dump> 根目录——写入/读取约定不一致为根因。
