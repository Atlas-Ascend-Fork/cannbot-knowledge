---
{
  "type": "Runbook",
  "title": "torchtitan rank 启动崩溃：ds41.indexer_prologue_qw 重复注册报错的环境定位（base 位于 CANN 构建目录、exp 位于系统 site-packages、本机探针为空）",
  "description": "torchtitan 真机训练 rank5 启动即崩溃，报 Tried to register an operator (cann_ops_transformer::ds41.indexer_prologue_qw...) with the same name and overload name multiple times。报错路径显示 base 包位于 CANN 9.3.0 构建目录、exp 包位于系统 Python site-packages；本地探针确认真机环境不在本机，需在真机做最小 import 复现与版本配套排查（同文件双注册判别与加载链路分析未被账本采纳）。",
  "tags": [
    "task.debugging",
    "topic.model_serving"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# torchtitan rank 启动崩溃：ds41.indexer_prologue_qw 重复注册报错的环境定位（base 位于 CANN 构建目录、exp 位于系统 site-packages、本机探针为空）


## 适用场景

torchtitan 真机训练 rank5 启动即崩溃，报 Tried to register an operator (cann_ops_transformer::ds41.indexer_prologue_qw...) with the same name and overload name multiple times。报错路径显示 base 来自 CANN 9.3.0 构建目录而 exp 装在系统 Python site-packages；本地探针确认真机环境不在本机，需在真机做最小 import 复现与版本配套排查（同文件双注册判别与加载链路分析未被账本采纳）。

适用：torchtitan/torch_npu 启动期报 torch.Library 重复注册且 base/exp 包分处 CANN 目录与系统 site-packages 的场景。失效/边界：故障环境在真机、本机探针为空；版本错配结论在轨迹内只有路径层面证据，exp 1.0.0 与 CANN 9.3.0 构建不配套的确认依赖真机 pip show/dist-info 核对（未回传）；最小复现命令与 define() 追踪脚本的执行结果不在轨迹内。

## 触发与观测

触发：torchtitan 真机训练 rank5 启动即崩溃，报 torch.Library 重复注册错误。

## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${CANN_ROOT}`：该次实验实际使用的 CANN 安装根目录；版本以本卡适用条件为准。


### 事实 c3

环境定位证据：报错栈路径显示 base 包位于 CANN 9.3.0 构建目录（${CANN_ROOT}/python/site-packages/cann_ops_transformer），而 exp 包位于系统 Python site-packages（/usr/local/python3.12.14/lib/python3.12/site-packages/cann_ops_transformer_exp）；本地探针（ls ${PRIVATE_PATH_1}、ls 系统 site-packages | grep -i cann、ls ${PRIVATE_PATH_2}; ls /home/; ls /usr/local/python3.12.14）在本机返回空且 exit=2，确认故障环境在真机、本机不可复现。


## 机制与判别

以下为轨迹事件原文中的完整机制单元：

### 补充机制片段

```bash
ls ${CANN_ROOT}/python/site-packages/ 2>/dev/null; echo "---"; ls /usr/local/python3.12.14/lib/python3.12/site-packages/ 2>/dev/null | grep -i cann
```

### 补充机制片段

```bash
ls /usr/local/python3.12.14/lib/python3.12/site-packages/cann_ops_transformer_exp/ops/attention/ 2>/dev/null; echo "---"; ls ${CANN_ROOT}/python/site-packages/cann_ops_transformer/ops/ 2>/dev/null
```

## 验证信号

本轨迹内验证层级：source_read（对报错栈与路径的静态分析 + 本机探针确认环境不在本机）。真机上的最小 import 复现与版本核对由用户在真机执行，结果未回传本轨迹。


## 适用与失效边界

适用：torchtitan/torch_npu 启动期报 torch.Library 重复注册且 base/exp 包分处 CANN 目录与系统 site-packages 的场景。失效/边界：故障环境在真机、本机探针为空；版本错配结论在轨迹内只有路径层面证据，exp 1.0.0 与 CANN 9.3.0 构建不配套的确认依赖真机 pip show/dist-info 核对（未回传）；最小复现命令与 define() 追踪脚本的执行结果不在轨迹内。
