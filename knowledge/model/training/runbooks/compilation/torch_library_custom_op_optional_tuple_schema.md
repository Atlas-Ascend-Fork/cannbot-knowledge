---
{
  "type": "Runbook",
  "title": "custom_op 返回含 Optional 的 tuple：核对显式 schema 与底层注册",
  "description": "记录中自定义算子的 tuple Optional 注解推断失败；显式 schema 绕开该处推断，并需逐参数核对底层算子和注册器版本。",
  "tags": [
    "task.debugging",
    "topic.compilation"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-17T01:57:52Z",
  "platforms": [
    "agnostic"
  ]
}
---
# custom_op 返回含 Optional 的 tuple：核对显式 schema 与底层注册

## 适用场景

torchtitan-npu 的 Kimi 训练入口在注册 CANN 自定义算子时失败；该问题位于 Python/schema 注册层。

## 触发与观测

返回 tuple[Tensor, Tensor | None] 的包装在 import 阶段触发 infer_schema 错误。底层打印的 schema 能表达 (Tensor, Tensor?)。

## 探针与操作

打印底层 overload 的 _schema，再检查当前 custom_op 如何拼接名称和 schema。下面的参数段属于该算子的注册配置，必须与完整底层签名配套。

原始源码差分或测试输出（用于核对）：

```text
    schema=(
        "(Tensor grad_y, Tensor x, Tensor? weight=None, "
        "Tensor? group_index=None, int dim=-1, float beta=1., "
        "float linear_beta=0., bool activate_left=True) -> (Tensor, Tensor?)"
    ),
```

## 机制与判别

该版本的注解推断没有处理本例 tuple 内 Optional，而显式 schema 能表达返回类型。记录还遇到重复填写算子名前缀和 Tensor kwarg-only 的注册错误；这些约束应限定于所用注册接口与版本，不扩展成所有 PyTorch schema 的规则。

## 验证信号

修正后 import 和两个 schema 打印通过，训练入口越过注册阶段；随后初始化超时，不能因此宣称端到端训练已通过。

## 适用与失效边界

需要逐参数核对 high_precision 等可选参数属于 forward 还是 grad 算子。PyTorch 升级可能改变推断能力；不要把本例写成所有 torch 2.x 的限制。
