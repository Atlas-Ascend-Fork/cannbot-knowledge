---
{
  "type": "Runbook",
  "title": "DeepGEMM-Ascend test_mega_moe 多进程 spawn 报 ModuleNotFoundError deep_ep：baseline 对比依赖未安装",
  "description": "test_mega_moe.py 多进程 spawn 在子进程内报 ModuleNotFoundError: No module named 'deep_ep'，触发点是 MegaMoECase.__init__ 中 with_baseline 为真时的 import deep_ep（test_mega_moe.py:78）。当前 conda 环境未安装 deep_ep（pip 仅 tilelang 0.1.15）；deep_ep 是 DeepEP-Ascend 独立通信库。",
  "tags": [
    "task.debugging",
    "topic.mixture_of_experts"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# DeepGEMM-Ascend test_mega_moe 多进程 spawn 报 ModuleNotFoundError deep_ep：baseline 对比依赖未安装


## 适用场景

test_mega_moe.py 多进程 spawn 在子进程内报 ModuleNotFoundError: No module named 'deep_ep'，触发点是 MegaMoECase.__init__ 中 with_baseline 为真时的 import deep_ep（test_mega_moe.py:78）。当前 conda 环境未安装 deep_ep（pip 仅 tilelang 0.1.15）；deep_ep 是 DeepEP-Ascend 独立通信库。

## 触发与观测


来源在 Python 3.14 环境尝试加载 DeepGEMM MegaMoE 相关依赖，`import deep_ep` 直接报 `ModuleNotFoundError: No module named deep_ep`，已列出的 pip 包仅见 tilelang 0.1.15。存在源码目录不等于模块已经安装进当前解释器。

## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${PYTHON_ENV_NAME}`：来源实验使用的 Python 环境名称，其依赖仍需单独核对。
- `${SCRATCH_DIR}`：由复现者创建的本次实验临时目录。


机制片段：原文：

```
python -c "import deep_ep; print(deep_ep.__file__)" 2>&1 | tail -3; pip list 2>/dev/null | grep -i -E "deep|tilelang|ep"
```

## 机制与判别

来源结论：

当前 conda 环境（${PYTHON_ENV_NAME}，python 3.14）未安装 deep_ep：python -c "import deep_ep" 报 ModuleNotFoundError、pip list 仅 tilelang 0.1.15；deep_ep 是 DeepEP-Ascend 独立通信库（提供 EPBuffer EP all-toall、FP8 dispatch 等），本机 ${SCRATCH_DIR}/deepep_ascend 有其源码快照（README+include 头文件）但未安装进环境。


## 验证信号

本卡验证信号并入『机制与判别』节：来源结论：的 import/pip 探针观测（客观观测）。

## 适用与失效边界

适用：DeepGEMM-Ascend test_mega_moe 多进程 baseline 对比运行前的依赖自检。失效边界：仅确认当前环境 deep_ep 缺失；安装 DeepEP-Ascend 后测试能否通过未验证；会话无最终结论文本。validation_scope: source_read。
