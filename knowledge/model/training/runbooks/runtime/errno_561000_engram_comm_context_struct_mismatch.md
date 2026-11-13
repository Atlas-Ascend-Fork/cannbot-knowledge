---
{
  "type": "Runbook",
  "title": "EngramFetch errno 561000 时核对 commAlg 与 context 协议版本",
  "description": "来源在 GetWorkspaceSize 阶段报 IsValidEngramCommAlg(commAlg) failed，写入侧源码的 context 仅五字段且无 commAlg。尚未绑定运行产物读侧布局和值，因此结构体错配是待验证方向，不能认定 padding 已被读作非法 commAlg。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T18:00:00Z",
  "updated_at": "2026-11-13T02:13:38Z",
  "platforms": []
}
---
# EngramFetch errno 561000 时核对 commAlg 与 context 协议版本


## 摘要

Engram训练在GetWorkspaceSize阶段报告IsValidEngramCommAlg(commAlg)校验失败，Python detail为空。来源读到写入侧context只有五字段、没有commAlg；尚未绑定运行动态库的读侧布局、字段偏移或实际commAlg值。协议/构建配套是排查方向，不能认定旧padding已被当作commAlg读取；初始化、实际读侧构建和生命周期等原因仍需核对。此问题应与kernel执行期WaitAllStatusFlags超时分开。

## 适用场景

mc2/engram 类自定义算子在训练脚本（torch.compile / npugraph_ex 图模式）中调用报 Mc2Aclnn context 层校验错误，且 Python 侧错误详情为空的情形；以及任何『host 侧 GetWorkspaceSize 阶段失败、错误只进 plog 不进 aclGetRecentErrMsg』的 aclnn 算子问题排查。

## 触发与观测

触发：engram 训练脚本首次 warmup 调用触发 ACLGraph 捕获，捕获期执行 engram_fetch_train 时 aclnnEngramFetch host 侧直接返回失败；日志形态为 RuntimeError 'call aclnnEngramFetch failed, detail:'（detail 为空，重复伴随 NPUGraph capture failed）。随后（重跑或换机器）可见 errno[561000] Check Mc2Aclnn::IsValidEngramCommAlg(commAlg) failed（aclnn_engram_fetch.cpp:57，aclnnEngramFetchGetWorkspaceSize 内）。

## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${PLOG_DIR}`：故障运行对应的 plog 日志目录。


1) 先查 plog（${PLOG_DIR}/）grep 算子名 + ERROR，分辨 tiling 校验失败与 runtime 捕获拒绝；2) 在仓库内 grep -rn "struct EngramCommContext" 定义处，核对外写字段集合；3) 在机器 CANN include 目录 grep IsValidEngramCommAlg/EngramCommContext 看新版结构与合法 commAlg 取值；4) 核对 libcust_opapi.so（OPP 侧）与 pip 包（extension 侧）的构建时间/来源是否配套。

## 机制与判别


首先区分 GetWorkspaceSize 的 host 校验失败与 kernel launch 之后的 WaitAllStatusFlags 超时。来源只读到了写入侧五字段定义，不足以确定运行产物读侧的字段偏移、ABI 与 commAlg 实际值。下一步应同时核对 extension、OPP 动态库与头文件的构建身份，必要时打印传入结构体及校验值。不能从 Python detail 为空推导日志通道是唯一原因。

## 验证信号


已观察到 host 校验错误日志，并读到 rankId/rankSize/virtualAddrList/hcommHandle/channelsPerRank 五字段定义。rebase 后重建未完成，engram 未复跑；尚无两侧 ABI 一致性或修复成功证据。

## 适用与失效边界


这是协议/构建配套的排查方向。若两侧 ABI 一致，仍需检查 commAlg 取值、初始化与内存生命周期等其他原因。不能把所有 561000 都归因于结构体错配。
