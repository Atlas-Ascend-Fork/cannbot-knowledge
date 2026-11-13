---
{
  "type": "Runbook",
  "title": "PyPTO 精度定位：kernel 内检查点全对而 matmul 读数错时，dump 图 opmagic 追踪定位 Pass_25_ReplaceTensor 改 nope COPY_IN dst offset",
  "description": "deepseekv32_mla_indexer_prolog_quant 用例 k_int8 失败（max diff=127、1008 个误差点、atol=1 不允许误差），而 pass_verify_save 的 7 个 kernel 内检查点全与 golden 一致——数据在 UB 正确、vector 路径（assemble）读取正确、cube 路径（matmul）读取错误。[:] = 与 .move() 写回 A/B 均以相同 max diff 失败、hadamard 权重全 0 输入时用例通过，排除写回方式与 k 路径计算。",
  "tags": [
    "task.debugging",
    "topic.precision"
  ],
  "status": "draft",
  "sources": [],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-12T11:53:46Z",
  "platforms": []
}
---
# PyPTO 精度定位：kernel 内检查点全对而 matmul 读数错时，dump 图 opmagic 追踪定位 Pass_25_ReplaceTensor 改 nope COPY_IN dst offset

## 适用场景

deepseekv32_mla_indexer_prolog_quant 用例 k_int8 失败（max diff=127、1008 个误差点、atol=1 不允许误差），而 pass_verify_save 的 7 个 kernel 内检查点全与 golden 一致——数据在 UB 正确、vector 路径（assemble）读取正确、cube 路径（matmul）读取错误。[:] = 与 .move() 写回 A/B 均以相同 max diff 失败、hadamard 权重全 0 输入时用例通过，排除写回方式与 k 路径计算。dump 图（compile_debug_mode:1）按 opmagic=25461 追踪 Key-Hadamard matmul 输入链：前端 concat 被拆为两个跨子图 ASSEMBLE，Pass_09 把 UB 拆到 GM，Pass_20 将 SLICE 改为 COPY_IN，Pass_25_ReplaceTensor 把 nope 的 COPY_IN dst offset 从 [0,0] 改为 [0,64]。


## 触发与观测


前端检查点看似正确、后续 matmul 读数异常时，来源按 opmagic 追踪同一 tensor 的 move/offset 演变，避免仅凭最终 kernel 归因。

## 探针与操作

- dump 图 opmagic 追踪（Key-Hadamard A_MUL_B opmagic=25461，SLICE→L1_TO_L0A opmagic=25458）显示演变链：Pass_00-04 前端 concat 被转为两个 ASSEMBLE 写同一 UB tensor；Pass_09_SplitLargeFanoutTensor 将 UB 拆到 GM 形成 GM→L1 COPY_IN 路径；Pass_20_GenerateMoveOp 将 SLICE 改为 COPY_IN（offset 仍 [0,0]）；Pass_25_ReplaceTensor 将 nope 的 COPY_IN dst offset 改为 [0,64]（对应 L1 buffer 的 [64:128]）。

## 机制与判别

机制片段：

```
BASE="output/output_20260811_110342_745944_1613838_0d28cba96a8240de92af714226b9e047/computation_graph/Strategy_00_PVC2_OOO"
python3 -c "
import json, os, glob

target_opmagic = 25461

for pass_dir in sorted(glob.glob('$BASE/Pass_*'), key=lambda x: int(os.path.basename(x).split('_')[1])):
    pass_name = os.path.basename(pass_dir)
    f = glob.glob(f'{pass_dir}/After_*Unroll8*hiddenfunc_7.json')
    if not f: continue
    f = f[0]
    d = json.load(open(f))
    func = d['functions'][0]
    ops = func['operations']
    tensors = func.get('tensors', [])
    tensor_map = {t['magic']: t for t in tensors}

    for i, op in enumerate(ops):
        if op.get('opmagic') == target_opmagic:
            opcode = op.get('opcode','')
            iop = op.get('ioperands',[])
            oop = op.get('ooperands',[])
            # 打印输入 tensor 信息
            in_info = []
            for tid in iop:
                t = tensor_map.get(tid, {})
                shape = t.get('shape','?')
                mt = t.get('mem_type',{})
                offset = t.get('offset','?')
                rt = t.get('rawtensor','?')
                in_info.append(f'{tid}(shape={shape},mem={mt.get(\"tobe\",\"?\")},offset={offset},rt={rt})')
            out_info = []
            for tid in oop:
                t = tensor_map.get(tid, {})
                out_info.append(f'{tid}(shape={t.get(\"shape\",\"?\")},mem={t.get(\"mem_type\",{}).get(\"tobe\",\"?\")})')
            print(f'{pass_name}: [{i}] {opcode} opmagic={target_opmagic}')
            print(f'  in: {in_info}')
            print(f'  out: {out_info}')
            break
" 2>&1
```

## 验证信号


dump 输出保留了 A_MUL_B 的 opmagic=25461 与相邻 SLICE/L1_TO_L0A 的 opmagic=25458：Pass_20 阶段 COPY_IN dst offset 为 [0,0]，Pass_25 阶段变成 [0,64]。这是 pass 间变化定位；是否应改变该 offset 及完整修复效果仍需结合 buffer 几何与数值回归。

## 适用与失效边界

适用：PyPTO 融合算子"kernel 内检查点全对、最终输出错"的精度问题定位，尤其 vector 读数正确而 cube（matmul）读数错误的形态。失效边界：定位依赖 compile_debug_mode:1 的 dump 图与 opmagic 追踪（opmagic 跨 Pass 不变）；本轨迹按要求只定位不修改；结论基于单次 loop（t=8=tile_bs）场景，推广到多迭代循环需再验证。
