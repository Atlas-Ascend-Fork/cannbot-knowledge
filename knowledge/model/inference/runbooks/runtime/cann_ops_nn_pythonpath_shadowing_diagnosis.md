---
{
  "type": "Runbook",
  "title": "cann_ops_nn 参数数目不匹配：检查 set_env.sh 改写的导入优先级",
  "description": "自定义 vendors 包可能被 CANN set_env.sh 前置的包路径遮蔽；先核对实际解释器、包路径和 schema，再选择受启动链支持的环境包装。",
  "tags": [
    "task.debugging",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": []
}
---
# cann_ops_nn 参数数目不匹配：检查 set_env.sh 改写的导入优先级

## 适用场景

同一环境并存 CANN 自带与自定义 cann_ops_nn；不同训练/推理启动脚本表现不同。

## 触发与观测

入口报 expected at most 5 argument(s) but received 8，而另一入口正常；报错声明缺少新接口的 weight/group_index。

## 探针与操作

在最终启动环境打印 cann_ops_nn.__file__ 和目标 _schema。逐次 source 后检查 PYTHONPATH，排除 vendors 路径已失效的情况。包装示例中的目录必须由调用者提供。

整理后的启动包装示例：只做静态语法检查：

```bash
#!/usr/bin/env bash
set -euo pipefail
: "${VENDORS:?set the absolute custom Python package directory}"
: "${CUSTOM_OPP:?set the matching custom OPP directory}"
CANN_SET_ENV="${CANN_SET_ENV:-/usr/local/Ascend/cann/set_env.sh}"
[[ -d "$VENDORS" && -d "$CUSTOM_OPP" && -f "$CANN_SET_ENV" ]]
(( $# > 0 )) || { echo 'usage: wrapper.sh TRAIN_COMMAND [ARGS...]' >&2; exit 2; }
WRAP="$(mktemp "${TMPDIR:-/tmp}/set_env_vendors.XXXXXX.sh")"
trap 'rm -f -- "$WRAP"' EXIT
{
    printf 'source %q\n' "$CANN_SET_ENV"
    printf 'export PYTHONPATH=%q:"${PYTHONPATH:-}"\n' "$VENDORS"
} > "$WRAP"
export ASCEND_SET_ENV_PATH="$WRAP"
source "$WRAP"
export ASCEND_CUSTOM_OPP_PATH="$CUSTOM_OPP"
export LD_LIBRARY_PATH="$CUSTOM_OPP/op_api/lib:${LD_LIBRARY_PATH:-}"
"$@"
```

## 机制与判别

所读启动链会在已有 vendors 设置之后 source CANN set_env.sh，后者前置 site-packages，因此实际导入可能重新命中旧包。先 source 工具包再前置有效 vendors，可作为该启动链支持 ASCEND_SET_ENV_PATH 时的候选规避。

## 验证信号

记录有默认与显式 vendors 置顶后的 schema 对照，以及 set_env.sh 的路径设置。没有该训练入口修正后的原始设备终验；包装脚本目前仅作静态检查。

## 适用与失效边界

ASCEND_SET_ENV_PATH 只有在启动链真正消费该变量时有效。动态库与 OPP 环境需匹配 Python 包；不得以导入路径正确代替设备功能和完整训练验收。
