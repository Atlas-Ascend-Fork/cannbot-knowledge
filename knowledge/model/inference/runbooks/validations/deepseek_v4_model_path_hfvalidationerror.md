---
{
  "type": "Runbook",
  "title": "deepseek_v4 model_path 指向不存在路径时报误导性 HFValidationError",
  "description": "cann-recipes-infer 统一推理入口在 YAML model_path 指向不存在的本地路径时，报 huggingface_hub 的 HFValidationError（Repo id must be in the form ...），把本地路径当非法 HF repo id 处理，提示 Use repo_type 与根因（路径不存在）脱节。两条独立轨迹用同一路径 ${LOCAL_PATH_2} 复现，报错逐字一致；合法本地路径正常加载可证明报错由存在性而非路径形式触发。",
  "tags": [
    "task.debugging",
    "task.testing",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-06T09:40:40Z",
  "platforms": [
    "a3"
  ]
}
---

# deepseek_v4 统一推理入口 model_path 指向不存在路径时报误导性 HFValidationError

## 适用场景

- 模型/框架：cann-recipes-infer 仓库 `models/deepseek_v4`（DeepSeek-V4 Flash，285B MoE），统一推理入口 `executor/scripts/infer.sh`（内部经 `executor/offline/infer.py` 加载模型与 tokenizer）。
- 平台/版本：Atlas A3（Ascend 910_9362 ×16，单 die 64GB HBM），CANN 9.2.0，Docker 容器 `cann_recipes_infer`（镜像 `cann9.2.0.pt2.9.0_dsv4_aarch_a3_image_custom_20260827`），transformers 5.0.0（镜像预装）、Python 3.11.12（来源记录）；另一轨迹为容器 `cann_recipes_infer_dsv4_bak_1014`（同镜像，torch_npu 2.9.0.post7）（来源记录）。
- 工作负载：离线推理前的 YAML 配置校验场景（model_path 配置错误时的报错质量评估）。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_3}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${RECIPES_ROOT}` 为cann-recipes-infer 源码根。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

触发：YAML 中 `model_path` 被改成不存在的本地路径（基于 `ci_a3/deepseek_v4_flash_rank_16_16ep_w8a8_platform.yaml` 副本，将 `model_path: "${LOCAL_PATH_1}"` 改为 `"${LOCAL_PATH_2}"`）。

两条独立轨迹中的逐字客观输出（ct7 / ct5 负向用例）：

```
[rank0]:     raise HFValidationError(
[rank0]: huggingface_hub.errors.HFValidationError: Repo id must be in the form 'repo_name' or 'namespace/repo_name': '${LOCAL_PATH_2}'. Use `repo_type` argument if needed.
[rank0]:     raise OSError(f"{e}") from e
[rank0]: OSError: Repo id must be in the form 'repo_name' or 'namespace/repo_name': '${LOCAL_PATH_2}'. Use `repo_type` argument if needed.
```

（来源：来源记录 T 284、来源记录 T 179；后者随后还打印 `[ERROR] 2026-10-15-00:56:49 (PID:61481, Device:0, RankID:-1) ERR99999 UNKNOWN applicaiton exception`。）

## 探针与操作

探针命令（来源记录 C 178，退出码经 docker exec 逐层透传，可同时观测报错与外层退出码）：

```
docker exec cann_recipes_infer_dsv4_bak_1014 bash -l -c "cd ${RECIPES_ROOT} && bash executor/scripts/infer.sh --model deepseek_v4 --yaml ct5_bad_model_path.yaml" > ${LOCAL_PATH_3} 2>&1; echo "EXIT_CODE=$?"; grep -E "OSError|HFValidationError|Error" ${LOCAL_PATH_3} | head -4; echo "---duration---"; grep -m1 "get env LOCAL_RANK" ${LOCAL_PATH_3}; tail -1 ${RECIPES_ROOT}/models/deepseek_v4/res/20261015/deepseek_v4_ct5_bad_model_path/log_0.log 2>/dev/null | head -c 200
```

另一轨迹（来源记录 C 283）用等价探针运行 `ci_a3/ct7_bad_model_path.yaml` 并 grep rank0 日志。两条轨迹使用完全相同的非法路径 `${LOCAL_PATH_2}`，结果逐字一致。

## 机制与判别

- 结论 1：model_path 指向不存在的本地路径时，deepseek_v4 统一推理入口报出 huggingface_hub 的 HFValidationError（"Repo id must be in the form 'repo_name' or 'namespace/repo_name'"），把本地路径当作格式非法的 HF repo id 处理，报错提示 `Use repo_type argument if needed` 与实际根因（本地路径不存在）脱节。
  - 证据：来源记录 T 284、来源记录 T 179（报错原文逐字一致，仅外层 OSError 包装相同）。
- 结论 2：该报错由"路径不存在"触发而非"路径形式"触发——同一 YAML 框架下合法本地路径 `${LOCAL_PATH_1}`（275GB、46 个 safetensors）正常完成加载与推理（来源记录 T 148 主样例 EXIT_CODE=0 且 16 rank 零错误），可区分两个解释分支：
  - 分支 A（成立）：transformers/huggingface_hub 在本地目录不存在时回退到 HF repo id 解析分支，于是把 `/` 开头的路径当 repo id 校验并报格式错误；
  - 分支 B（排除）：若报错源于"路径形式本身非法"，则合法存在的本地路径也应报同样错误，与观测矛盾。
- 未验证推断（轨迹内未实施修复）：在加载前增加 `os.path.exists(model_path)` 前置检查、本地场景直接报"路径不存在"，可消除误导；此为两条轨迹报告中的建议，未在本组来源观测轨迹内验证。

## 验证信号

- 来源记录 T 284：ct7_bad_model_path 运行后 rank0 日志逐字包含 HFValidationError 与 OSError 双层报错（平台：Atlas A3 容器；证据等级：工具结果原文）。
- 来源记录 T 179：ct5_bad_model_path 运行后同一报错原文 + `EXIT_CODE=0`（外层退出码）+ `[ERROR] ... ERR99999 UNKNOWN applicaiton exception`（00:56:49，rank 启动 00:56:44 后约 5 秒，属配置/tokenizer 加载早期快速失败，未进入权重加载）。
- 单次观测说明：每条轨迹对该场景各观测 1 次，两条轨迹共 2 次、结果一致；未测试"存在但缺 config.json 的目录"等其他非法形态。

## 适用与失效边界

- 适用：cann-recipes-infer 统一入口（transformers 加载链路）+ 本地绝对路径 model_path 不存在的场景；两条独立轨迹（2026-10-14/15）在相同路径字面量上复现。
- 失效边界/未知：
  - 未测试 `model_path` 指向存在但内容不完整（缺 safetensors/config.json）的目录，报错形态可能不同；
  - 未测试 HF repo id 形式的 model_path（本环境 HF 不可达）；
  - 修复建议（加载前本地路径存在性检查）未在轨迹内实施与验证；
  - 报错时机本身较早（未浪费权重加载时间），问题仅在于报错文案的语义误导。
