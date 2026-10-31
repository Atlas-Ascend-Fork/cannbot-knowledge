# Profiling 数据采集

性能数据采集、msproftx 扩展标记、算子信息订阅及 PyTorch 迭代时间标记接口。

- [aclprof_init.md](aclprof_init.md)：在 aclInit 之后初始化 Profiling 并设置数据保存路径，须与 Finalize 配对；不能与算子订阅流程交叉调用。
- [aclprof_set_config.md](aclprof_set_config.md)：在 Profiling Start 前配置额外采集参数，扩展 CreateConfig 的配置项；支持多次调用，配置字符串最长 256 字节。
- [aclprof_start.md](aclprof_start.md)：按配置使能 Profiling，采集调用之后的数据，须在模型执行前调用；连续 Start 指定重复 Device 会报错。
- [aclprof_stop.md](aclprof_stop.md)：按与 Start 一致的配置停止本次 Profiling 采集，与 Start 配对；初始化生命周期结束另用 Finalize。
- [aclprof_finalize.md](aclprof_finalize.md)：结束 Profiling 初始化生命周期，与 aclprofInit 配对，建议只调用一次；与单次采集的 Stop 区分。
- [aclprof_create_stamp.md](aclprof_create_stamp.md)：在 Profiling Start 之后创建 msproftx Stamp，供瞬时标记或时间区间打点使用，须与 DestroyStamp 配对。
- [aclprof_set_stamp_trace_message.md](aclprof_set_stamp_trace_message.md)：为 Stamp 携带字符串描述
- [aclprof_mark.md](aclprof_mark.md)：标记瞬时事件
- [aclprof_mark_ex.md](aclprof_mark_ex.md)：向指定 Stream 下发带字符串的打点任务，关联 Host 与 Device 打点；消息最长 127 字符。
- [aclprof_push.md](aclprof_push.md)：以 Stamp 开始 msproftx 时间区间，须在同一线程用 Pop 结束；跨线程区间应使用 RangeStart/RangeStop。
- [aclprof_pop.md](aclprof_pop.md)：在与 Push 相同的线程结束 msproftx 时间区间并记录结束时间戳；跨线程区间应使用 RangeStart/RangeStop。
- [aclprof_range_start.md](aclprof_range_start.md)：开始可跨线程结束的 msproftx 时间区间，返回唯一 rangeId，交给 RangeStop 标识并结束该区间。
- [aclprof_range_stop.md](aclprof_range_stop.md)：按 RangeStart 返回的 rangeId 结束 msproftx 时间区间，支持在另一线程完成结束记录。
- [aclprof_range_push_ex.md](aclprof_range_push_ex.md)：在 Torch 算子加载前缓存待上报的 Tensor 信息，之后由 RangePop 上报；与 msproftx 时间区间标记区分。
- [aclprof_range_pop.md](aclprof_range_pop.md)：上报 RangePushEx 缓存的 Torch Tensor 信息，配对完成该次 Profiling 数据上报。
- [aclprof_destroy_stamp.md](aclprof_destroy_stamp.md)：释放 msproftx Stamp，与 CreateStamp 配对；须在 aclprofStop 停止采集前调用。
- [aclprof_str2id.md](aclprof_str2id.md)：字符串转哈希 ID
- [aclprof_model_subscribe.md](aclprof_model_subscribe.md)：按模型 ID 和订阅配置采集算子名称、类型、耗时；须与 UnSubscribe 配对，不能与 Init/Start/Stop/Finalize 采集流程混用。
- [aclprof_model_unsubscribe.md](aclprof_model_unsubscribe.md)：取消订阅算子信息
- [aclprof_get_op_desc_size.md](aclprof_get_op_desc_size.md)：获取算子数据结构大小
- [aclprof_get_op_num.md](aclprof_get_op_num.md)：获取算子数量
- [aclprof_get_op_type_len.md](aclprof_get_op_type_len.md)：获取算子类型名称长度
- [aclprof_get_op_type.md](aclprof_get_op_type.md)：获取算子类型名称
- [aclprof_get_op_name_len.md](aclprof_get_op_name_len.md)：获取算子名称长度
- [aclprof_get_op_name.md](aclprof_get_op_name.md)：获取算子名称
- [aclprof_get_op_start.md](aclprof_get_op_start.md)：获取算子开始时间
- [aclprof_get_op_end.md](aclprof_get_op_end.md)：获取算子结束时间
- [aclprof_get_op_duration.md](aclprof_get_op_duration.md)：获取算子耗时
- [aclprof_get_model_id.md](aclprof_get_model_id.md)：获取算子所在模型 ID
- [aclprof_get_op_flag.md](aclprof_get_op_flag.md)：从 opInfo 中识别指定节点属于算子、子图还是算子线程，返回订阅类型标记，失败返回 NONE。
- [aclprof_get_op_attri_value.md](aclprof_get_op_attri_value.md)：从 opInfo 中按算子索引读取订阅属性，当前支持线程 ID；返回属性字符串，失败返回 NULL。
- [aclprof_get_step_timestamp.md](aclprof_get_step_timestamp.md)：在单算子模型训练中标记迭代开始或结束，将 StepInfo、START/END 标记与 Stream 关联，供 Profiling 解析迭代。
- [aclrtProfTrace](aclrt_prof_trace.md)：在网络指定位置下发自定义 Profiling 打点（异步）。
