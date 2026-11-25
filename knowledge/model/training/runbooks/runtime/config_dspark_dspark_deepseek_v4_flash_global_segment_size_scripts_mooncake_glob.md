---
{
  "type": "Runbook",
  "title": "Mooncake 共享存储段互相影响：DeepSpec 训练端默认 global_segment_size 4GiB→0 避免训练退出移除共享段",
  "description": "DeepSpec 在线训练仓（deepspec/online，DeepSeek-V4 flash recipe，NPU），推理端 vLLM 通过 DeepSpecMooncakeConnector（kv_producer）向 Mooncake 共享存储写 KV，训练端作为 consumer 从同一 Mooncake master（P2PHANDSHAKE）读取。",
  "tags": [
    "task.debugging",
    "topic.implementation.debugging"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-20T14:17:06Z",
  "updated_at": "2026-11-20T14:17:06Z",
  "platforms": []
}
---

# Mooncake 共享存储段互相影响：DeepSpec 训练端默认 global_segment_size 4GiB→0 避免训练退出移除共享段

## 适用场景

DeepSpec 在线训练仓（deepspec/online，DeepSeek-V4 flash recipe，NPU），推理端 vLLM 通过 DeepSpecMooncakeConnector（kv_producer）向 Mooncake 共享存储写 KV，训练端作为 consumer 从同一 Mooncake master（P2PHANDSHAKE）读取。多训练/推理共享同一 Mooncake 存储集群的部署。

## 触发与观测

- 失败现象（source 0 seq 11，user_reported）："拉起两个训练，停掉其中一个影响了另外一个"。
- 修改前默认值扫描（source 0 seq 18，rg 输出逐字）：
  - `./config/dspark/dspark_deepseek_v4_flash.py:128:        global_segment_size=4 * 1024**3,`
  - `./scripts/train/train.sh:79:mooncake_global_segment_size=${mooncake_global_segment_size:-}`
  - `./deepspec/data/online_feature_dataset.py:156:            int(self.config.get("global_segment_size", 4 * 1024**3)),`
  - 推理端 launch_vllm_dsv4_deepspec.sh 的 kv_connector_extra_config 中 `global_segment_size:4294967296`。

## 探针与操作

修复（commit `c5fd89d`，source 0 seq 34/39，fileChange 逐字 diff；以下 `\n` 为证据原文中的字面转义序列）：

- 训练默认配置（seq 34）：`-        global_segment_size=4 * 1024**3,\n+        # Training consumers do not contribute storage to the shared store.\n+        global_segment_size=0,`
- 读取端兜底（seq 34）：`-            int(self.config.get(\"global_segment_size\", 4 * 1024**3)),\n+            int(self.config.get(\"global_segment_size\", 0)),`
- 启动脚本（seq 34）：`-mooncake_global_segment_size=${mooncake_global_segment_size:-}\n+mooncake_global_segment_size=${mooncake_global_segment_size:-0}`
- 文档（seq 39）：`+| `mooncake_global_segment_size` | `0` | `data.mooncake.global_segment_size`；训练端默认不提供全局存储段，避免退出时移除其他训练可能使用的存储段。可显式覆盖。 |`

## 机制与判别

- 机制：Mooncake TransferEngine 的 global segment 是向共享存储贡献容量的注册段；训练 consumer 默认贡献 4GiB，进程退出时该段被移除，共享存储容量骤减/段失效，波及共用同一 master 的其他训练。训练端只需要读，不需要贡献存储，故默认置 0（`0` 表示不注册全局段，仍保留 local_buffer 与显式覆盖能力）。
- 判别：修复把三处默认（config/脚本/读取端兜底）全部收敛为 0，消除"训练退出→共享段被移除"路径；与失败现象一一对应（因果由配置-退出行为推出，双训练场景未实际复演）。
- 边界（agent_narrative，source 0 seq 55）：推理端未改（仍 4GiB），训练端不再贡献容量后共享存储总容量下降；若推理端贡献容量不足，可能写入失败，需增大推理端 global_segment_size 或加独立存储节点。

## 验证信号

- bash -n（train.sh/train_online_8card_tcp.sh）与 git diff --check 通过（source 0 seq 42）。
- AST+Mock 行为级检查（source 0 seq 41，逐字）：`PASS: consumer setup defaults to 0 and preserves explicit overrides; Python syntax valid`——提取 MooncakeTransfer 类、Mock mooncake.store，断言默认 setup 收到 0、显式传 4096 时收到 4096。
- 提交（source 0 seq 78）：`[online_train c5fd89d] fix: default training Mooncake global segment size to zero`。
- 验证缺口（Agent 明确声明，source 0 seq 44）："未实际运行双训练停止场景"；已有进程需重启才生效。验证层次为 static_check + cpu_reference(mock)，非端到端。

## 适用与失效边界

- 适用于 DeepSpec/Mooncake KV 传输架构中"consumer 不应贡献共享存储"的部署原则：任何会退出/重启的训练或临时消费进程，默认 global_segment_size 应为 0。
- 不适用于需要训练端贡献容量的小集群（无独立存储节点且推理端容量不足时，置 0 会带来写入失败风险——未验证的 agent 推断）。
- 端到端双训练停止场景未复演，采纳前建议补运行验证；Mooncake 版本未记录。

## 附：断言存档

- DeepSpec 在线训练仓（deepspec/online，DeepSeek-V4 flash，Mooncake KV 传输）训练端默认向 Mooncake 共享存储注册 4GiB 全局存储段（config global_segment_size=4*1024**3、train.sh 变量默认空、读取端兜底 4*1024**3）。两个训练共享同一 Mooncake master 时，停掉其中一个训练会把它贡献的存储段从共享存储移除，从而影响另一个训练（失败现象 user_reported：'拉起两个训练，停掉其中一个影响了另外一个'；默认值 rg 结果 tool_observed）。
- 修复（commit c5fd89d "fix: default training Mooncake global segment size to zero"，4 files changed）：训练端三处默认统一改为 0 且保留显式覆盖——config/dspark/dspark_deepseek_v4_flash.py global_segment_size=4*1024**3→0（附注释 Training consumers do not contribute storage to the shared store）；scripts/train/train.sh mooncake_global_segment_size 默认 空→0；deepspec/data/online_feature_dataset.py 读取端兜底 4*1024**3→0；docs/configuration.md 增补变量说明（训练端默认不提供全局存储段，避免退出时移除其他训练可能使用的存储段）（fileChange diff 全部 tool_observed）。
- 验证层次为静态+mock 级：bash -n 语法检查、git diff --check 通过；AST 提取 MooncakeTransfer 类并以 Mock mooncake.store 断言默认 setup 收到 global_segment_size=0、显式传入 4096 时收到 4096（PASS: consumer setup defaults to 0 and preserves explicit overrides）。Agent 明确声明'未实际运行双训练停止场景'；已有进程需重启才生效。推理端（launch_vllm DeepSpecMooncakeConnector kv_producer）配置未改仍为 4GiB，训练端退出不再移除共享段，但共享存储总容量下降，推理端容量不足时可能写入失败（agent_narrative，未验证）。

```text
./deepspec/data/online_feature_dataset.py:156:            int(self.config.get(\"global_segment_size\", 4 * 1024**3)),
```
