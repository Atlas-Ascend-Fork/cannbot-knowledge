---
{
  "type": "Runbook",
  "title": "fx_converter dual-stage Add 的 int64/int32 prepare 返回 161002：alpha 类型候选原因与 fallback 规避",
  "description": "该 fx_converter/CANN 9.2.0 快照中，int64 索引 add 在 aclnnAddGetWorkspaceSize 返回161002，转int32后仍失败。源码将 alpha 硬编码为 ACL_FLOAT，构成待隔离验证的候选原因；没有证明所有整数或 bool 都被 API 拒绝。轨迹采用整型/bool add 的 torch fallback 后不再出现该错误，但同次运行仍以设备错误507057结束。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": [
    "910"
  ]
}
---
# fx_converter dual-stage Add 的 int64/int32 prepare 返回 161002：alpha 类型候选原因与 fallback 规避

## 适用场景

- 框架/栈：fx_converter dual-stage Add（`fxrt/fx_converter/src/opp/add_dual_stage_impl.cc`，FxAddPrepare 在 OpExecutePrepareContext 的 prepare 阶段调 aclnnAddGetWorkspaceSize）；CANN 9.2.0（aclnn 头文件位于 `${CANN_INCLUDE_DIR}`）。
- 平台：Atlas 910B3（rt2 模式，ModelV2Runner）。
- 已观测触发：图重写生成的 int64 flat-index add（`i0*D1 + i1`）及其 int32 改写。bool/int8/int16 被纳入规避 hook，但没有独立失败探针。
- 缺失信息：未在其它 CANN 版本上验证 161002 的 dtype 约束矩阵；未逐一测试 int8/int16。

路径补充：`${CANN_INCLUDE_DIR}` 为当前 CANN 安装中的 aclnn 头文件目录，按本地安装设置。

## 触发与观测

- 触发（事件 2041，FXRT ERROR 日志原文）：`FxAddPrepare: aclnnAddGetWorkspaceSize failed, status=161002`，位置 `fxrt/fx_converter/src/opp/add_dual_stage_impl.cc:90 RunAddGetWorkspace`。该失败发生在**执行前的 prepare 阶段**（所有 dual-stage op 的 prepare 先于任何 kernel 执行），导致 `ModelV2Executor::Execute failed` → `RuntimeError: ModelV2Runner::Execute failed`。
- 错误码定义（事件 2054，`op_errno.h` 原文）：`16:#define ACLNN_ERR_PARAM_INVALID 161002` —— 参数校验失败，输入确实非法。

## 探针与操作

探针 1（事件 2067 编辑 + 事件 2097 gdb 重跑）：给 `AddPrepare` 的 `RunAddGetWorkspace` 失败路径加输入 desc dump（shape/dtype/addr）。观测（事件 2098/2101，原文）：

```
FxAddPrepare input dump: x1 shape=[8,1,1,1] dtype=9 addr=0x12c068ffd000 | x2 shape=[1,1,1,11] dtype=9 addr=0x12c068ffca00 | y shape=[8,1,1,11] dtype=9 addr=0x12ccbf610000
```

这些形状符合通常的广播关系；dtype=9（int64）。仅凭 desc dump 不能排除 alpha、布局或其他参数约束，不能认定 dtype 是唯一异常项。

第一次修复尝试（事件 2104）：`_rewrite_index_tensor_two` 把 flat-index 算术转为 int32（`convert_element_type(i0/i1, torch.int32)`）。重跑后（事件 2108）dump 显示 dtype 已变 3（int32）但**仍返回 161002** —— dtype 转换单独无效。

探针 2（事件 2111/2112）：查 dual-stage Add 源码，`add_dual_stage_impl.cc` 中（事件 2044 读取的函数原文）：

```
bool BuildAddAclArgs(const gert::Tensor *x1, const gert::Tensor *x2, const gert::Tensor *y, AddAclArgs *args) {
  args->x1 = ToAclTensor(x1);
  args->x2 = ToAclTensor(x2);
  args->y = ToAclTensor(y);
  args->alpha = aclCreateScalar(&args->alpha_storage, ACL_FLOAT);
```

（事件 2112 同时定位：`47:  float alpha_storage = 1.0f;` 与 `79:  args->alpha = aclCreateScalar(&args->alpha_storage, ACL_FLOAT);`。）

第二次（最终）修复（事件 2114，写入 `fx_converter/python/fx_converter/rewrites/ops.py` 的原文，已用 reader 复核）：

```
# pylint: disable=unused-argument
def add_ops_hook(op, node, flat_args, executor):
    """Integer add stays on torch fallback.

    The dual-stage Add prepare builds alpha as ACL_FLOAT; aclnnAdd rejects
    integer tensors with a float alpha (161002), so integer adds (typically
    flat-index arithmetic from rewrites) must not take the catalog path.
    """
    if any(dt == torch.bool for dt in _tensor_dtypes(node)):
        return Op.custom_call
    if _has_integer_tensor(node):
        return Op.custom_call
    return op
```

并注册（事件 2115）：`fxb.register_ops_mapping_hook(Op.add, add_ops_hook)`。

## 机制与判别

- 结论：dual-stage Add 的 prepare 阶段 aclnnAddGetWorkspaceSize 对本次 int64/int32 索引张量返回 161002（ACLNN_ERR_PARAM_INVALID），失败路径加输入 desc dump 可观测到形状广播完全合法、dtype=int64（GE dtype 9）；该失败发生在任何 kernel 执行之前（所有 dual-stage op 的 prepare 先于执行）。
- 判别链：int64 → 161002；仅转int32 → 仍161002（事件2108），说明改成int32不足以规避此失败。源码中 alpha 为 ACL_FLOAT，是值得单变量复核的候选原因；未完成仅修改 alpha 的对照，不能锁定因果。
- 结论范围：已有失败记录覆盖 int64/int32；bool/int8/int16 是否失败以及 aclnnAdd 的通用 dtype/alpha 契约没有在本轨迹中核实。
- 结论：处置为索引算术转 int32 并把整型/bool add 降级 torch fallback（add_ops_hook 返回 Op.custom_call 并注册到 Op.add），修复后 161002 类错误在本轨迹内消失，后续失败转为设备侧 MTE（另一独立缺陷）。
- 未验证推断：161002 的具体校验位置与 alpha 的独立作用未定位。上面原始 hook 的注释属于当时实现者的原因判断，不是所有整数/bool 均失败的验证结果。

## 验证信号

- 事件 2120（修复后 gdb 运行）：grep `FxAddPrepare input dump|aclnnAddGetWorkspaceSize failed` 在 gdb.log 中无 161002 命中（错误类消失）。
- 事件 2123（同一运行）：失败变为 `RuntimeError: npuSynchronizeDevice:...SUSPECT REMOTE ERROR, error code is 507057`（设备侧 MTE，属另一缺陷链），日志中不再出现 RunAddGetWorkspace 失败行。
- 证据等级：910B3 + CANN 9.2.0 + 私有 fxrt 构建，gdb 批处理运行（单次）；判别链（int64 拒 → int32 仍拒 → alpha 硬编码）在同会话内两次独立运行中复现。

## 适用与失效边界

- 适用：该快照的 fx_converter dual-stage Add 中的 int64/int32 索引算术失败场景；症状是 prepare 期 161002。
- 失效边界/注意：int32 转换不是修复（单独无效），仅当配合 fallback 降级才闭合；int32 flat-index 的值域上限约 2^31，超大张量 numel 需评估（轨迹内注释称"int32 range covers any realistic flat index"）；float 张量的 add 不受影响，仍走 catalog 路径。
- 若后续通过独立探针确认并修复参数约束，再对照精度、索引范围与 prepare/execute 成功情况决定是否撤销 hook；不能只凭 alpha 改动即视为恢复。
