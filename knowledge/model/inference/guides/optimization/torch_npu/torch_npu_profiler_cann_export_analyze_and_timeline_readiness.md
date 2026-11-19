---
type: Guide
title: TorchNPU Profiler的CANN导出、分析、能力判定与产物等待
description: 固定双版本CANN导出、分析返回码、环境检查、时间线轮询，以及msprof能力探测缓存与Feature字符串版本比较的实际边界。
tags:
- task.debugging
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/cann_parse/_cann_export.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/cann_parse/_cann_analyze.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_base_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_file_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_path_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/cann_parse/_cann_export.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/cann_parse/_cann_analyze.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_base_parser.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_file_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_path_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_cann_package_manager.py
  role: primary
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_cann_package_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_feature_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_feature_manager.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_singleton.py
  role: implementation
- resource: https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_singleton.py
  role: implementation
created_at: '2026-11-11T06:49:34Z'
updated_at: "2026-11-14T08:44:18Z"
platforms: []
---

# TorchNPU Profiler的CANN导出、分析、能力判定与产物等待

## 固定版本与输入

依据PyTorch主线`ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf`和发布快照`f3ecfe4a7ef7395754da7ca2e35661a7132b519b`。本文完整核对CANNExportParser、CANNAnalyzeParser、CANNTimelineParser、BaseParser，以及CannPackageManager、FeatureManager的本地定义，只静态读取源码，没有运行msprof、子进程、采集或设备实验。CANN外部工具、完整任务调度器和ProfilerConfig的配置归一化各自另计。

BaseParser保存param_dict中的profiler_path/output_path，按get_cann_path的结果选COMMON_CONFIG或ONLY_FWK_CONFIG，从对应name取deps和mode；无配置时默认空依赖、SUB_PROCESS。export_type取param_dict，缺省[]。这些是本地入口规则，不能单凭实例化推断任务已执行、依赖已完成或外部工具能力已检测。

## Db与Text是两次有顺序的命令

导出与分析run都会先初始化日志并load_info，再检查CANN路径是否目录；没有目录直接返回SUCCESS、None。这个状态可以表示跳过，不证明产生了任何文件。msprof由构造时shutil.which取得，不是在每条命令前重新搜索PATH。

| 路径 | Db命令 | Text命令 | 非零退出码 |
|---|---|---|---|
| CANNExportParser | msprof --export=on --type=db --output=目录 | msprof --export=on --output=目录 | 抛RuntimeError，由run捕获后返回FAIL |
| CANNAnalyzeParser | msprof --analyze=on --type=db --output=目录 | msprof --analyze=on --output=目录 | 仅打印警告；没有随后异常时最终仍SUCCESS |

两种模式都请求时先Db再Text。导出Db失败即退出，不会接着跑Text；分析Db的非零退出码不阻止Text，但subprocess.run本身抛异常会进入FAIL分支。调用均capture_output=True、shell=False，没有本地timeout，也不解析stdout/stderr证明产物完整。Text刻意不传--type，以容纳旧工具；不等于所有CANN版本都会额外生成DB。空export_type下导出仍做环境和大小检查，分析仍做路径/msprof检查，但两者都可能不派发任何命令就SUCCESS。

导出run捕获的是try内部Exception，日志初始化在try前；分析相同。没有在此证明所有日志、调用者异常都转换成FAIL。导出耗时使用带时区datetime差，表示解析墙钟耗时，不是算子、通信或设备执行时间。类上的error_msg说明常量两版提示set_env.sh/set-env.sh不同，两版run实现均未读取该常量，实际命令来自上述列表。

## 环境检查的版本差异

导出先检查CANN子目录，再检查msprof及其脚本。get_all_subdir默认max_depth=4，收集每层目录后递归，cur_depth>max_depth才停；它不是对任意深度、所有文件和CANN根本身的完整权限审计。文件归属helper接受root或当前有效UID；另一个check_path_permission名称虽含permission，实际只stat并比较root/当前实际UID，不检查执行位、可读性或全部路径祖先。

| 检查 | 主线 | 发布快照 |
|---|---|---|
| CANN所列子目录owner不匹配 | logger.warning，继续 | RuntimeError |
| CANN所列子目录组/其他可写 | 该方法没有对应拒绝分支 | path_is_other_writable按st_mode & 0o022拒绝，包含组写 |
| msprof不存在 | 立即RuntimeError，提示重新source | 先积累错误字符串，随后继续调用权限helper；可能先由os.stat(None)等路径抛异常 |
| msprof或脚本owner不匹配 | 积累信息后warning；脚本缺失仍立即抛错 | 积累信息，最终RuntimeError；中间helper也可先抛 |
| 脚本组/其他可写 | 没有该本地分支 | 0o022检查并加入失败信息 |

_get_msprof_script_path把realpath(msprof.strip())按第一次出现的字符串tools截断，再拼tools/profiler/profiler_tool/analysis/msprof/msprof.py，存在则返回，否则空串；没有证明这是按路径组件识别Toolkit根。代码只打印权限修复建议，不执行chown/chmod。分析parser只检查msprof是否找到，没有调用导出的整套环境检查。这里的差异限所列固定函数，不推导整个软件栈的安全策略。

## 数据量警告不是耗时预测或大小上限

_check_prof_data_size累计host/data和各device/data的文件字节数，walk_with_depth默认只走10层。阈值PROF_WARN_SIZE为1024³字节；达到后打印“可能超过30分钟”的警告，不中断导出、不自动改离线，也不是实际测得的30分钟。

警告判断在device路径循环内部。只有host且其大小已超阈值时，空device循环仍不会打印该条警告；不能笼统写成总量大于1GiB必警告。stat/getsize等异常可让导出run返回FAIL；没有在这里保证同时变化的目录可一致读取，也不宣称遍历计数覆盖所有采集数据。

## 时间线等待只识别名称，不验完整性

CANNTimelineParser无CANN目录也返回SUCCESS。存在时load_info；export_type含Text优先走mindstudio_profiler_output轮询，只要listdir中某个名字以.csv结束便SUCCESS，没有isfile、内容、时间戳或模式检查，旧文件甚至同名目录都可能满足。否则走DB轮询，要求CANN目录下匹配^msprof_\d+\.db$且isfile的条目；不检查数据库可读性、schema、关闭状态或本轮创建时间。Text与Db同时请求也只等Text；空export_type走DB分支。

两条循环每次sleep 0.1秒，没有本地重试次数、超时或导出子进程退出联动。只有sleep抛InterruptedError明确返回FAIL；listdir/load_info等异常不在该try里，本地不会统一转换。外层调度是否终止另看调用者。因此“导出任务SUCCESS”“命令退出0”“时间线就绪SUCCESS”“后续文件/表可解析”应分别记录；任一状态都不能替代算子、通信和内存指标真实存在的核验。

指标配置与op_attr/Level产品声明见[指标选择](torch_npu_profiler_metrics_selection.md)，本卡不改写该stable卡的产品声明。

## 能力探测缓存与Feature字符串版本比较

CannPackageManager按msprof帮助文本探测导出能力，FeatureManager比较调用者提供的feature字典；两者不是同一份CANN版本兼容矩阵。check_msprof_help_output先用shutil.which找msprof，没找到返回False；找到后以[msprof_path, --help]执行，capture_output=True、shell=False、text=True，退出码必须0且stdout包含目标子串才True，stderr不参与匹配。try内任何Exception都变False，未设置本地timeout；False不能区分未安装、调用失败、帮助文本变化或真的不支持。发布版还先调用ProfilerPathManager.check_path_permission，不通过即False；主线没有这一局部检查。该helper实际检查stat owner是否root或当前实际UID，没有验证执行位或所有祖先；helper抛异常也由探测函数转False，不能把这个差异推成主线工具一定能运行或发布探测具备完整权限证明。

| 本地入口 | stdout目标子串 | 缓存 |
|---|---|---|
| check_cann_package_support_export_db / is_support_export_db | --type | SUPPORT_EXPORT_DB |
| check_cann_package_support_default_export_db / is_support_default_export_db | text(which will also export the database) | SUPPORT_DEFAULT_EXPORT_DB |

两个类属性各自起始None，只有None才探测，此后True和False都会复用，**失败结果同样被缓存**；可能分别启动两次--help。类内没有自动按PATH、Toolkit升级、语言或环境变化失效，也没有锁。直接check_*函数本身不使用类缓存；不要把“每次调用函数”与“每次classmethod查询”混为一谈。基于help的粗粒度命中只代表本地布尔结果，不证明真实导出能成功、全部DB表存在或产品适配通过。

FeatureManager初始化version='master'，fmkFeature仅默认登记ATTR，featureVersion='0'且compatibility='1'；YES为'1'，No为'0'。load_feature_info直接把传入字典引用赋给cannFeature，不复制或校验schema。is_supported_feature的实际顺序：

1. 从CANN条目取affectedComponent，只接受'all'或'PTA'；affectedComponentVersion只接受'all'或当前version。缺省空串会被拒绝。
2. 从框架与CANN条目取featureVersion，缺省均'0'，两者必须isdigit()，否则False。非字符串/错误条目类型可以先抛异常，本方法没有try转换。
3. **比较的是原字符串**，没有int转换。框架串大于CANN串时看框架compatibility，较小时看CANN compatibility，必须严格等于字符串'1'；相等直接True，不要求compatibility为'1'。

例如字符串'10'与'2'按字典序排序，不能按数值10、2解读分支；isdigit也不是固定整数版本协议验证。对框架未登记的feature仍取默认版本'0'，如果外部CANN条目满足component/version并同为'0'，也可能True；不能称为“所有未登记feature一律不支持”。version默认master只是本地字符串，既不自动读取真实包版本，也不代表和当前Toolkit配套。原docstring把版本关系写成大于/小于，不足以改变实际字符串运算；这里记录局部行为，不据它宣布兼容性缺陷已在真实模型中触发。完整CANN特性文件由谁装载、何时调用以及底层是否消费ATTR，不在本卡来源内。

FeatureManager.clear只调用cannFeature.clear，保留version和fmkFeature；由于load存原字典引用，也会清空调用者那份字典。它不清CannPackageManager的两个help缓存，二者不能混作同一个重置开关；通用Singleton装饰器的按类缓存实现见固定来源_singleton.py。排查“配置被关闭”时应分别记录最终export_type、help检测/缓存结果、实际传入feature字典与本地version，再核真实输出；不能由布尔检测替代真实产物或数值验收。

## Evidence

- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/cann_parse/_cann_export.py)（1–236行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/cann_parse/_cann_analyze.py)（1–68行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_view/_base_parser.py)（1–44行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_file_manager.py)（178–184行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_path_manager.py)（190–226行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py)（14–33行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/cann_parse/_cann_export.py)（1–188行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/cann_parse/_cann_analyze.py)（1–68行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_view/_base_parser.py)（1–44行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_file_manager.py)（190–196行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_path_manager.py)（169–208行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py)（14–34行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_cann_package_manager.py)（1–44行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_cann_package_manager.py)（1–48行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_feature_manager.py)（1–56行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_feature_manager.py)（1–56行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_singleton.py)（1–9行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_singleton.py)（1–10行；全文）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/ac0e1564ca6ffb00c1f4fb834fc4b41a601862bf/torch_npu/profiler/analysis/prof_common_func/_constant.py)（155–165行；有界辅助）
- [固定源码](https://gitcode.com/Ascend/pytorch/blob/f3ecfe4a7ef7395754da7ca2e35661a7132b519b/torch_npu/profiler/analysis/prof_common_func/_constant.py)（155–165行；有界辅助）
