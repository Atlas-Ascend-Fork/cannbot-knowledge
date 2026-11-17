---
{
  "type": "Runbook",
  "title": "集成测试的验收边界：harness 检查退出码不等于独立数值对比",
  "description": "所示 run_tests.py 失败分支检查子进程 returncode；局部源码和测试入口通过不足以确认是否有独立数值验收，需继续检查完整入口与子程序。",
  "tags": [
    "task.debugging",
    "topic.precision"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-14T18:00:00Z",
  "updated_at": "2026-11-16T05:50:55Z",
  "platforms": [
    "agnostic"
  ]
}
---
# 集成测试的验收边界：harness 检查退出码不等于独立数值对比

## 适用场景

所读版本的 torchtitan integration test harness 局部源码与验证设计。退出码判据本身与硬件无关。

## 触发与观测

希望从集成测试通过推导 loss/metric 已被独立比较，但所示失败分支只有退出码判据。

## 探针与操作

读完整 run_tests 失败处理，再沿实际子程序检查其断言、阈值和参考输入。不能以 harness 没解析 loss 就断言所有子程序也没有数值检查。

本次整理的完整 AST 定位函数；只能定位判据，不能据此证明全程序不存在数值检查：

```python
def find_exit_code_checks(source_path):
    import ast
    from pathlib import Path
    source = Path(source_path).read_text(encoding='utf-8')
    tree = ast.parse(source)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            names = {n.id for n in ast.walk(node.test) if isinstance(n, ast.Name)}
            if 'returncode' in names:
                found.append({'line': node.lineno, 'condition': ast.unparse(node.test)})
    return found
```

原始 grep 显示的判据；仅局部源码，非完整函数：

```text
returncode = result.returncode
if returncode != 0:
```

## 机制与判别

所示 returncode != 0 分支只能证明这一失败判据。仅凭该局部源码，不能判断完整 harness 或子程序是否提供独立数值 oracle；精度保障需要指明真实断言与参考，不能仅列“integration tests passed”。

## 验证信号

原始源码输出包含 returncode 的失败判定。本卡不将其他确定性单测或 PR 自述当作该入口已完成的数值验证。

## 适用与失效边界

结论绑定所读入口版本。新增子程序断言或 harness 数值检查后应重审；测试名称、退出码与设备型号均不能代替数值对拍依据。
