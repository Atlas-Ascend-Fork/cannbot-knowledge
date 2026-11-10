---
{
  "type": "Runbook",
  "title": "infer.sh 推理失败时退出码恒为 0（function.sh tee 管道与 wait 不透传子进程退出码）",
  "description": "cann-recipes-infer 统一入口 function.sh 将各 rank 的 python 子进程放入后台（rank0 经 tee 管道、其余经重定向），循环后执行无参数 wait，子进程异常退出不影响脚本退出码。deepseek_v4 六个约束负向用例日志均含明确报错但外层 EXIT_CODE=0，与成功运行（同样 0）不可区分，CI 依赖 $? 判级会误判。",
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

# infer.sh 推理失败时退出码恒为 0（function.sh tee 管道与 wait 不透传子进程退出码）

## 适用场景

- 模型/框架：cann-recipes-infer 统一推理入口 `executor/scripts/infer.sh` → `executor/scripts/function.sh` 的 `launch_infer_task`（离线模式，多 rank `taskset` 启动 python 推理进程）。
- 平台/版本：Atlas A3（Ascend 910_9362 ×16），CANN 9.2.0；观测来自 deepseek_v4 模型（Docker 容器内执行，镜像 `cann9.2.0.pt2.9.0_dsv4_aarch_a3_image_custom_20260827`），transformers 5.0.0 / torch 2.9.0。
- 工作负载：CI/自动化流水线依赖 `infer.sh` 退出码判断推理成败的场景。

路径约定：`${LOCAL_PATH_1}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_2}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${LOCAL_PATH_3}` 为需按命令用途填写的本地文件或目录位置，原始绝对位置不公开；`${RECIPES_ROOT}` 为cann-recipes-infer 源码根。使用前在本地设置这些变量；不同编号不可假定为同一位置。代码中的变量样式字符串也须替换，不依赖 Python 自动展开。

## 触发与观测

触发：任意 rank 的 python 推理子进程异常退出（ValueError / Exception / HFValidationError 等约束负向用例，最终均以 `ERR99999 UNKNOWN applicaiton exception` 落日志）。

逐字客观输出（来源记录，2026-10-15，6 个负向用例全部呈现同一模式；此处以 ct4/ct5 为例）：

```
T 167 | EXIT_CODE=0
[rank0]: raise Exception(
（ct4_bad_dataset：Exception: your dataset NotExistBench is not supported, ...）

T 179 | EXIT_CODE=0
[rank0]:     raise HFValidationError(
[rank0]: huggingface_hub.errors.HFValidationError: Repo id must be in the form 'repo_name' or 'namespace/repo_name': '${LOCAL_PATH_1}'. Use `repo_type` argument if needed.
---duration---
[INFO][2026-10-15 00:56:44.394][patch_getenv.py:15] get env LOCAL_RANK = 0
[ERROR] 2026-10-15-00:56:49 (PID:61481, Device:0, RankID:-1) ERR99999 UNKNOWN applicaiton exception
```

其余同型信号：T 183（ct1 limit_core ValueError）、T 187（ct2 pypto 互斥 ValueError）、T 190（ct3 next_n=5 ValueError）、T 194（ct6 low_latency_tp ValueError）均为 `EXIT_CODE=0` + 日志含报错；来源记录 T 166（cv_v1 limit_core）、T 173（cv_v2 pypto）同样 `EXIT=0`。对照：主样例成功运行也是 `EXIT_CODE=0`（来源记录 T 148）——成功与失败在退出码上完全不可区分。

## 探针与操作

探针命令（退出码经 `docker exec` 逐层透传，`$?` 即 infer.sh 退出码；来源记录 C 166/C 178/C 182/C 186/C 189/C 193 同型）：

```
docker exec cann_recipes_infer_dsv4_bak_1014 bash -l -c "cd ${RECIPES_ROOT} && bash executor/scripts/infer.sh --model deepseek_v4 --yaml ct5_bad_model_path.yaml" > ${LOCAL_PATH_2} 2>&1; echo "EXIT_CODE=$?"; grep -E "OSError|HFValidationError|Error" ${LOCAL_PATH_2} | head -4
```

来源记录 的等价探针（C 165/C 172，`echo EXIT=\$?` 在容器内紧跟 infer.sh 之后）：`... timeout 720 bash executor/scripts/infer.sh --model deepseek_v4 --yaml ci_a3/cv_v1_limit_core_no_streams.yaml > ${LOCAL_PATH_3} 2>&1; echo EXIT=\$?; grep -E 'ValueError|Error|error' ${LOCAL_PATH_3} | grep -v '0 Error' | tail -5`。

注意：管道型写法（如 `infer.sh ... 2>&1 | grep ... | head -5; echo "EXIT=$?"`）中 `$?` 反映的是管道末端命令的退出码，不能作为 infer.sh 退出码证据；本卡只采用重定向型（`> log 2>&1; echo $?`）探针的观测。

## 机制与判别

机制（function.sh `launch_infer_task`，来源记录 T 112 读取原文，行 321-328）：

```
321:         cmd=(taskset -c "$cmdopt" python3 "${INFER_PATH}" --yaml_file_path="${YAML}" "${EXTRA_ARGS[@]}")
322:         if [ $i -eq 0 ] && [[ $LAUNCH_MODE -ne 1 ]];then
323:             "${cmd[@]}" 2>&1 | tee ${WORK_DIR}/${RES_PATH}/log_${LOCAL_RANK}.log &
324:         else
325:             "${cmd[@]}" &> ${WORK_DIR}/${RES_PATH}/log_${LOCAL_RANK}.log &
326:         fi
327:     done
328:     wait
```

- 结论 1：deepseek_v4 约束负向用例（ct1-ct6 共 6 例）推理日志均含明确报错，但 infer.sh 外层退出码全部为 0（`EXIT_CODE=0`）；同一镜像、同一入口下主样例成功运行同样返回 0，失败与成功在退出码维度不可区分。
  - 信号：来源记录 T 167/T 179/T 183/T 187/T 190/T 194（失败 6 例）、T 148（成功对照）；来源记录 T 166/T 173（失败 2 例）。
- 结论 2：机制为 function.sh 将每个 rank 的 python 子进程放入后台（rank0 经 `2>&1 | tee ... &` 管道、其余 rank 经 `&> ... &` 重定向），循环结束后执行无参数的 `wait`；无 pipefail 时 rank0 管道的退出码取 tee 的 0，无参数 `wait` 也不透传任何子进程退出码，因此脚本整体退出码与子进程成败解耦，恒为 0。
  - 机制锚点：来源记录 T 112（function.sh 行 321-328 原文）。
  - 判别：若仅有 rank0 的 tee 管道吞码，则 `LAUNCH_MODE` 分支下所有 rank 走 `&>` 重定向时应能透传失败；但实测重定向分支下同样 `EXIT_CODE=0`（6 例均覆盖多 rank 场景），支持"`wait`（无参数）+ 后台任务整体不透传"为统一根因，`tee` 吞码仅为 rank0 路径的叠加因素。此判别基于原文结构与退出码观测，未对 function.sh 做修改实验。
- 未验证推断（轨迹内未实施修复）：`set -o pipefail` + `wait $pid; exit $?` 显式透传可修复该问题；两条轨迹报告均如此建议，未验证。

## 验证信号

- 失败 8 例退出码 0：来源记录 T 167、T 179、T 183、T 187、T 190、T 194；来源记录 T 166、T 173（平台：Atlas A3 容器；证据等级：工具结果原文，均为重定向型探针）。
- 成功对照退出码 0：来源记录 T 148（主样例 16 rank 零错误 PASS）。
- 机制原文：来源记录 T 112（function.sh 321-328 行）。
- 单次说明：每条负向用例各观测 1 次；跨 2 条轨迹、2 个容器实例、6 类不同报错（数据集白名单/权重路径/limit_core/pypto/next_n/low_latency_tp）复现同一退出码模式。

## 适用与失效边界

- 适用：cann-recipes-infer 统一入口离线多 rank 启动路径（function.sh `launch_infer_task`）；CI 若以 `$?` 判级会把约束失败误判为成功。
- 失效边界/未知：
  - 在线（PD）模式走 `server_cmd` 后台重定向路径（T 112 行 299 `"${server_cmd[@]}" 2>&1 > "${WORK_DIR}/${RES_PATH}/log_server.log" &`），退出码行为未在轨迹内观测；
  - 修复方案（pipefail/显式透传）未在轨迹内实施与验证；
  - 管道型探针的 `EXIT=0`（如 来源记录 T 288、来源记录 T 235）不构成 infer.sh 退出码证据，已排除；
  - 观测均在 Docker 容器内经 `docker exec` 透传退出码；`docker exec` 自身会透传容器内命令退出码，该前提在本环境成立。
