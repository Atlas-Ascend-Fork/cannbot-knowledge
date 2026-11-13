---
{
  "type": "Runbook",
  "title": "tyro 1.0.15 bool 否置语法判别与关闭 SwapOptimizer 的合法 CLI 写法",
  "description": "torchtitan-npu 训练关闭 SwapOptimizer 的调优动作中的 tyro CLI 否置语法判别：tyro 1.0.15 下 --optimizer.swap-optimizer=true/=false、--optimizer.swap-optimizer false、--no-optimizer.swap-optimizer 均被拒，唯一合法写法是 --optimizer.no-swap-optimizer。",
  "tags": [
    "task.implementation",
    "topic.optimizer"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T12:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# tyro 1.0.15 bool 否置语法判别与关闭 SwapOptimizer 的合法 CLI 写法

torchtitan-npu 训练关闭 SwapOptimizer 的调优动作中，本卡记录 tyro 1.0.15 bool 否置语法判别与正确的关闭写法。

## 适用场景

torchtitan-npu 训练调优中需要通过 CLI 关闭 SwapOptimizer（虚拟/换出优化器）的场景；同时是 tyro CLI bool 参数否置语法的操作手册。route=training，area=performance。

## 触发与观测

触发：调优动作 AO-1 授权命令为 `--optimizer.swap-optimizer false`，实际训练启动直接失败（tyro 1.0.15 报 Unrecognized options，exit code 2）。

## 探针与操作

### 复现路径约定

以下路径已脱敏。历史命令中的变量占位符需由复现者按实际环境替换；Python/JSON 字符串内的占位符不会自动展开。

- `${TRAINING_REPO_ROOT}`：该版本训练框架的检出根目录。


语法判别（容器内 tyro 实测矩阵）：--optimizer.swap-optimizer=True/=true/=false、--no-optimizer.swap-optimizer 均 exit code 2；--optimizer.no-swap-optimizer OK swap= False。落地修改：

```bash
python3 - <<'EOF'
path = '${TRAINING_REPO_ROOT}/run_trainv4_2die.sh'
with open(path) as f:
    txt = f.read()
old = '    --optimizer.swap-optimizer false\n'
new = '    --optimizer.no-swap-optimizer\n'
assert old in txt, 'old line not found'
txt = txt.replace(old, new)
with open(path, 'w') as f:
    f.write(txt)
print('replaced with --optimizer.no-swap-optimizer')
EOF
bash -n ${TRAINING_REPO_ROOT}/run_trainv4_2die.sh && echo "SYNTAX OK"
```

## 机制与判别

tyro 1.0.15 的 bool 否置语法实测：--optimizer.swap-optimizer=true/=false、--optimizer.swap-optimizer false、--no-optimizer.swap-optimizer 均以 exit code 2 被拒，唯一合法写法是 --optimizer.no-swap-optimizer（容器内实测 OK swap= False）。

## 验证信号

验证信号：tyro 1.0.15 否置语法矩阵实测（三种错误写法均 exit code 2，--optimizer.no-swap-optimizer OK swap= False，容器内实测）。

## 适用与失效边界

边界：tyro 否置语法结论绑定 tyro 1.0.15；关闭 SwapOptimizer 的适用性需按显存余量另行评估。
