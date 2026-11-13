---
{
  "type": "Runbook",
  "title": "模型推理流水线 gmm.sh 的 CANN 版本耦合：固定源码分支与跨版本构建缓存",
  "description": "模型推理流水线的 grouped_matmul 安装钩子固定使用9.1.0源码分支，而流水线CANN默认配置已为9.2.0；run包存在时跳过重编，随后安装至当前CANN。通过核对配置、缓存与实际加载包定界版本耦合，静态结构不能单独证明兼容或模型间隔离。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T12:13:52Z",
  "platforms": [
    "a3"
  ]
}
---
# 模型推理流水线 gmm.sh 的 CANN 版本耦合：固定源码分支与跨版本构建缓存

## 适用场景

模型推理流水线通过 `inference/hooks/${MODEL_NAME}/gmm.sh` 安装 GroupedBatchedGemm/MoE 所需的 `grouped_matmul`。切换 CANN 版本时，需要核对钩子选用的源码分支、构建环境、缓存包和当前运行时是否一致。本例源码构建参数为 `--soc=ascend910_93`。

`${MODEL_NAME}` 表示使用该钩子的模型配置名；`${WORK_DIR}` 表示钩子的源码及构建缓存目录，来源使用仓库相对路径 `inference/workdir/gmm`。按自己的流水线设置，不依赖原模型标识或个人 fork。

## 触发与观测

- 配置检查显示 `config.sh` 默认 `CANN_VERSION=9.2.0`，`CANN_HOME` 默认指向 `/usr/local/Ascend/cann-${CANN_VERSION}`。
- `gmm.sh` 则固定 `git_branch="9.1.0"`，源码目录有效时复用已有 checkout；不能仅根据当前 CANN 环境推断源码版本。
- `build_out/cann-ops-transformer-custom_linux-aarch64.run` 存在且未指定 `--force` 时跳过重编；切换运行时版本不会自动失效此缓存。
- 安装前清除 `ASCEND_CUSTOM_OPP_PATH` 后执行 run 包。因此“当前 CANN 已切换”与“算子已按当前版本重编”是两个不同观测。

## 探针与操作

1. 在来源工程内只读检查 `config.sh`、`scripts/pipeline_runner.py` 及目标模型的 `gmm.sh`，核对实际传入的 CANN 环境和钩子调用路径。
2. 分别记录已有 checkout 的分支及提交、run 包的构建环境与哈希、安装目标和实际加载的算子路径；缓存目录存在不能替代这些检查。
3. 核对版本切换时是否沿用同一构建包，并检查 `--force` 分支。重编或更换包属于后续受控实验，应重新验证模型精度和性能。
4. 若需判断其他模型是否受影响，还须检查完整的 vendor 清理、装载、失败退出与钩子调用链；仅凭目录盘点或脚本注释不能证明运行时隔离。

## 机制与判别

以下为来源脚本的控制流节选，省略环境准备、源码获取、参数解析与 `cd`；不是可直接执行的独立脚本。`force` 来自脚本的 `--force` 参数，默认0。

```bash
git_branch="9.1.0"
install_file="build_out/cann-ops-transformer-custom_linux-aarch64.run"
if [ "${force}" -eq 1 ] || [ ! -f "${install_file}" ]; then
    bash build.sh --pkg --soc=ascend910_93 --ops=grouped_matmul -j16
fi
[ -f "${install_file}" ] || { echo "未找到 run 包: ${install_file}" >&2; exit 1; }
unset ASCEND_CUSTOM_OPP_PATH
bash "${install_file}"
```

判别重点是缓存键中没有 CANN 版本，且重编条件仅检查 `force` 与文件存在性。这能说明跨版本复用的结构性风险；不能据此断言旧包一定不兼容，也不能证明当前加载的就是该缓存包。源码分支参数只在实际取码路径上生效，已有 checkout 的真实提交仍须单独核对。

## 验证信号

来源工具输出支持两项静态观测：配置默认版本为9.2.0；钩子源码分支为9.1.0且已有run包会绕过构建。来源中的既往运行通过摘要未与实际加载包、构建环境及提交完整绑定，本卡不据此声称跨版本ABI兼容、输出逐位一致或升级后仍可工作。

## 适用与失效边界

适用于模型流水线自定义算子安装钩子的版本与缓存排查。改变分支映射、缓存布局或安装逻辑后须重新核对。本卡仅完成静态配置与控制流分析，没有修复后的构建、设备或端到端验证，也未证明模型间完全隔离。
