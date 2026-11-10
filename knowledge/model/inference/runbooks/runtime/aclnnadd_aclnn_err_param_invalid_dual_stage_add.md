---
{
  "type": "Runbook",
  "title": "aclnnAdd 拒绝整型张量返回 161002（ACLNN_ERR_PARAM_INVALID）：dual-stage Add 的 alpha 硬编码 ACL_FLOAT，dtype 转 int32 无效，整型/bool add 需降级 torch fallback",
  "description": "fx_converter dual-stage Add 的 prepare 阶段对整型张量稳定返回 aclnnAddGetWorkspaceSize 161002（ACLNN_ERR_PARAM_INVALID）。给失败路径加输入 desc dump 可观测形状广播合法、dtype=int64；把索引算术转 int32 后仍被拒，可判别根因是 BuildAddAclArgs 将 alpha 硬编码为 ACL_FLOAT（整型张量 + float alpha 即参数非法，对任何整型 dtype 成立），而非单纯的 int64 不支持。处置：索引算术转 int32 + add_ops_hook 把整型/bool add 降级 torch fallback（Op.custom_call），修复后 161002 类错误消失。",
  "tags": [
    "task.debugging",
    "topic.graph_execution"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-03T12:00:00Z",
  "updated_at": "2026-11-03T12:00:00Z",
  "platforms": [
    "910"
  ]
}
---

# aclnnAdd 拒绝整型张量返回 161002（ACLNN_ERR_PARAM_INVALID）：dual-stage Add 的 alpha 硬编码 ACL_FLOAT，dtype 转 int32 无效，整型/bool add 需降级 torch fallback

## 适用场景

- 框架/栈：fx_converter dual-stage Add（`fxrt/fx_converter/src/opp/add_dual_stage_impl.cc`，FxAddPrepare 在 OpExecutePrepareContext 的 prepare 阶段调 aclnnAddGetWorkspaceSize）；CANN 9.2.0（aclnn 头文件位于 `${CANN_INCLUDE_DIR}`）。
- 平台：Atlas 910B3（rt2 模式，ModelV2Runner）。
- 触发面：任何被 fx_converter 图重写生成的整型 add（典型是 flat-index 算术 `i0*D1 + i1`，由 `_rewrite_index_tensor_two` 生成，dtype int64）以及 bool add。
- 缺失信息：未在其它 CANN 版本上验证 161002 的 dtype 约束矩阵；未逐一测试 int8/int16。

路径补充：。按本地环境设置变量，保留文中的相对路径关系。

路径补充：`${CANN_INCLUDE_DIR}` 为当前 CANN 安装中的 aclnn 头文件目录，按本地安装设置。

## 触发与观测

- 触发（事件 2041，FXRT ERROR 日志原文）：`FxAddPrepare: aclnnAddGetWorkspaceSize failed, status=161002`，位置 `fxrt/fx_converter/src/opp/add_dual_stage_impl.cc:90 RunAddGetWorkspace`。该失败发生在**执行前的 prepare 阶段**（所有 dual-stage op 的 prepare 先于任何 kernel 执行），导致 `ModelV2Executor::Execute failed` → `RuntimeError: ModelV2Runner::Execute failed`。
- 错误码定义（事件 2054，`op_errno.h` 原文）：`16:#define ACLNN_ERR_PARAM_INVALID 161002` —— 参数校验失败，输入确实非法。

## 探针与操作

探针 1（事件 2067 编辑 + 事件 2097 gdb 重跑）：给 `AddPrepare` 的 `RunAddGetWorkspace` 失败路径加输入 desc dump（shape/dtype/addr）。观测（事件 2098/2101，原文）：

```
FxAddPrepare input dump: x1 shape=[8,1,1,1] dtype=9 addr=0x12c068ffd000 | x2 shape=[1,1,1,11] dtype=9 addr=0x12c068ffca00 | y shape=[8,1,1,11] dtype=9 addr=0x12ccbf610000
```

形状广播完全合法；dtype=9（int64）是唯一异常项（事件 2103 判读）。

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

- 结论：dual-stage Add 的 prepare 阶段 aclnnAddGetWorkspaceSize 对整型张量稳定返回 161002（ACLNN_ERR_PARAM_INVALID），失败路径加输入 desc dump 可观测到形状广播完全合法、dtype=int64（GE dtype 9）；该失败发生在任何 kernel 执行之前（所有 dual-stage op 的 prepare 先于执行）。
- 判别链：int64 → 161002；仅转 int32 → 仍 161002（事件 2108）。两条观测合起来排除"int64 这一 dtype 单独不被支持"的解释，锁定 alpha 类型约束：BuildAddAclArgs 把 alpha 硬编码为 ACL_FLOAT，整型张量 + float alpha 即参数校验失败，对任何整型 dtype（含 bool）均成立。
- 结论：把索引算术从 int64 转 int32（dtype 9→3）后仍返回 161002，可判别根因并非『int64 不支持』单因素，而是 BuildAddAclArgs 中 alpha 硬编码 ACL_FLOAT：整型张量 + float alpha 即参数校验失败，对任何整型 dtype 均成立。
- 结论：处置为索引算术转 int32 并把整型/bool add 降级 torch fallback（add_ops_hook 返回 Op.custom_call 并注册到 Op.add），修复后 161002 类错误在本轨迹内消失，后续失败转为设备侧 MTE（另一独立缺陷）。
- 未验证推断：161002 具体由 aclnnAdd 的哪一层校验抛出（acl 层 desc 校验还是算子 tiling）未深挖；"aclCreateScalar 按 ACL_FLOAT 传 1.0f 对整型张量必然非法"是从两次 dtype 观测 + 源码硬编码推断的结论。

## 验证信号

- 事件 2120（修复后 gdb 运行）：grep `FxAddPrepare input dump|aclnnAddGetWorkspaceSize failed` 在 gdb.log 中无 161002 命中（错误类消失）。
- 事件 2123（同一运行）：失败变为 `RuntimeError: npuSynchronizeDevice:...SUSPECT REMOTE ERROR, error code is 507057`（设备侧 MTE，属另一缺陷链），日志中不再出现 RunAddGetWorkspace 失败行。
- 证据等级：910B3 + CANN 9.2.0 + 私有 fxrt 构建，gdb 批处理运行（单次）；判别链（int64 拒 → int32 仍拒 → alpha 硬编码）在同会话内两次独立运行中复现。

## 适用与失效边界

- 适用：fx_converter dual-stage Add（或任何以 aclCreateScalar(..., ACL_FLOAT) 构造 alpha 的 aclnn 调用方）接收整型/bool 张量的场景；症状是 prepare 期 161002。
- 失效边界/注意：int32 转换不是修复（单独无效），仅当配合 fallback 降级才闭合；int32 flat-index 的值域上限约 2^31，超大张量 numel 需评估（轨迹内注释称"int32 range covers any realistic flat index"）；float 张量的 add 不受影响，仍走 catalog 路径。
- 若上游修复 alpha 按张量 dtype 构造（如整型用 ACL_INT32/匹配 dtype 的 scalar），则 add_ops_hook 降级可回退。
