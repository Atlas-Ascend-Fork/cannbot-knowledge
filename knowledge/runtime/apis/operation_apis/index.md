# Runtime Operation API

CANN Runtime Operation 数据对象与配套接口：aclDataBuffer 内存描述、Profiling 配置对象（aclprof*）、自定义 Allocator（aclrtAllocator*）、Stream 配置对象（aclrtStreamConfigHandle）以及 TDT 数据对象（acltdt*DataItem/Dataset/QueueAttr/QueueRoute 等）。该类接口多为 Create/Set/Get/Destroy 配对的资源管理接口。

## 数据内存描述（aclDataBuffer）

- [aclCreateDataBuffer](acl_create_data_buffer.md)：将已有内存地址和大小封装为 aclDataBuffer 描述对象，底层 Host/Device 内存由用户自行申请、释放；空描述要求 data=NULL 且 size=0。
- [aclDestroyDataBuffer](acl_destroy_data_buffer.md)：销毁 aclDataBuffer 描述对象，不释放创建时传入的 data 内存，底层内存须由用户单独释放。
- [aclGetDataBufferAddr](acl_get_data_buffer_addr.md)：获取 aclDataBuffer 中数据的内存地址。
- [aclGetDataBufferSize](acl_get_data_buffer_size.md)：以 uint32 返回 DataBuffer 记录的字节数；后续版本将废弃，推荐使用返回 size_t 的 aclGetDataBufferSizeV2。
- [aclGetDataBufferSizeV2](acl_get_data_buffer_size_v2.md)：以 size_t 返回 DataBuffer 记录的内存字节数，替代旧版返回 uint32 的 aclGetDataBufferSize。
- [aclUpdateDataBuffer](acl_update_data_buffer.md)：更新 DataBuffer 描述的地址和大小；旧数据内存仍由用户管理，不再使用时须自行释放。

## Profiling 配置对象（aclprofConfig / aclprofStepInfo / aclprofSubscribeConfig）

- [aclprofCreateConfig](aclprof_create_config.md)：按 Device 列表、AI Core 指标及采集开关创建 Profiling 配置，可复用；使用后须 DestroyConfig 释放。
- [aclprofDestroyConfig](aclprof_destroy_config.md)：释放 CreateConfig 创建的 Profiling 采集配置；同一配置指针不能重复销毁。
- [aclprofCreateStepInfo](aclprof_create_step_info.md)：创建 Profiling 迭代信息对象，与 DestroyStepInfo 配对；同一对象的同一 tag 只能设置一次。
- [aclprofDestroyStepInfo](aclprof_destroy_step_info.md)：释放 CreateStepInfo 创建的 Profiling 迭代信息对象；同一对象不能重复销毁。
- [aclprofCreateSubscribeConfig](aclprof_create_subscribe_config.md)：创建算子性能订阅配置，指定采集开关和管道写指针；当前仅支持耗时统计，不支持 AicoreMetrics 采集。
- [aclprofDestroySubscribeConfig](aclprof_destroy_subscribe_config.md)：释放 CreateSubscribeConfig 创建的算子性能订阅配置；同一配置指针不能重复销毁。

## 自定义 Allocator（aclrtAllocatorDesc）

- [aclrtAllocatorCreateDesc](aclrt_allocator_create_desc.md)：创建 Allocator 描述信息。
- [aclrtAllocatorDestroyDesc](aclrt_allocator_destroy_desc.md)：销毁 Allocator 描述信息。
- [aclrtAllocatorSetObjToDesc](aclrt_allocator_set_obj_to_desc.md)：设置 Allocator 对象。
- [aclrtAllocatorSetAllocFuncToDesc](aclrt_allocator_set_alloc_func_to_desc.md)：设置申请内存 block 的回调函数。
- [aclrtAllocatorSetAllocAdviseFuncToDesc](aclrt_allocator_set_alloc_advise_func_to_desc.md)：设置按建议地址申请内存 block 的回调函数。
- [aclrtAllocatorSetFreeFuncToDesc](aclrt_allocator_set_free_func_to_desc.md)：设置释放内存 block 的回调函数。
- [aclrtAllocatorSetGetAddrFromBlockFuncToDesc](aclrt_allocator_set_get_addr_from_block_func_to_desc.md)：设置根据 block 获取 Device 内存地址的回调函数。

## Stream 配置对象（aclrtStreamConfigHandle）

- [aclrtCreateStreamConfigHandle](aclrt_create_stream_config_handle.md)：创建供 CreateStreamV2 使用的 Stream 配置对象，可通过 SetStreamConfigOpt 填写属性，使用后销毁配置句柄。
- [aclrtDestroyStreamConfigHandle](aclrt_destroy_stream_config_handle.md)：释放 CreateStreamConfigHandle 创建的 Stream 配置对象；操作对象是创建流所用的配置句柄。

## TDT 数据对象（acltdtDataItem / acltdtDataset）

- [acltdtCreateDataItem](acltdt_create_data_item.md)：创建单个 Tensor 数据项，记录数据或结束标志、Shape、元素类型、数据地址和长度，供加入 Dataset 传输。
- [acltdtDestroyDataItem](acltdt_destroy_data_item.md)：销毁 acltdtDataItem。
- [acltdtGetTensorTypeFromItem](acltdt_get_tensor_type_from_item.md)：判断收到的 DataItem 是正常数据、结束标记还是异常数据，返回 acltdtTensorType，供决定后续处理方式。
- [acltdtGetDataTypeFromItem](acltdt_get_data_type_from_item.md)：读取 DataItem 中正常 Tensor 的元素数据类型，返回 aclDataType；与区分正常、结束、异常数据的 TensorType 查询不同。
- [acltdtGetDataAddrFromItem](acltdt_get_data_addr_from_item.md)：从单个 DataItem 读取正常 Tensor 数据的地址，操作对象为数据项而非 Dataset 容器或共享 Buffer。
- [acltdtGetDataSizeFromItem](acltdt_get_data_size_from_item.md)：从单个 DataItem 读取正常 Tensor 数据的长度，与 GetDatasetSize 返回的数据项数量区分。
- [acltdtGetDimNumFromItem](acltdt_get_dim_num_from_item.md)：获取数据 Shape 的维度个数。
- [acltdtGetDimsFromItem](acltdt_get_dims_from_item.md)：获取数据 Shape。
- [acltdtCreateDataset](acltdt_create_dataset.md)：创建容纳多个 Tensor DataItem 的 Dataset，配合 AddDataItem 组装通道传输数据，使用后 DestroyDataset。
- [acltdtDestroyDataset](acltdt_destroy_dataset.md)：销毁 acltdtDataset。
- [acltdtGetDataItem](acltdt_get_data_item.md)：获取 Dataset 中指定位置的 DataItem。
- [acltdtAddDataItem](acltdt_add_data_item.md)：把已创建的单个 Tensor 数据项加入 Dataset 容器，Dataset 和 DataItem 均须先分别创建。
- [acltdtGetDatasetSize](acltdt_get_dataset_size.md)：获取 Dataset 中 DataItem 个数。
- [acltdtGetDatasetName](acltdt_get_dataset_name.md)：获取 Dataset 的描述符。

## TDT 队列属性与路由（acltdtQueueAttr / acltdtQueueRoute）

- [acltdtCreateQueueAttr](acltdt_create_queue_attr.md)：创建队列属性配置对象，供 SetQueueAttr 填写属性并交给 CreateQueue 使用。
- [acltdtDestroyQueueAttr](acltdt_destroy_queue_attr.md)：销毁队列属性配置信息。
- [acltdtSetQueueAttr](acltdt_set_queue_attr.md)：向队列属性配置对象写入指定类型的属性值，供创建队列使用；len 须匹配整数或指针类型大小。
- [acltdtGetQueueAttr](acltdt_get_queue_attr.md)：从已创建的队列属性配置对象读取指定属性及实际返回长度；len 须匹配属性的整数或指针类型大小。
- [acltdtCreateQueueRoute](acltdt_create_queue_route.md)：按源、目的队列 ID 创建一条路由配置对象，供加入 QueueRouteList 后绑定队列关系。
- [acltdtDestroyQueueRoute](acltdt_destroy_queue_route.md)：销毁队列路由配置。
- [acltdtGetQueueRouteParam](acltdt_get_queue_route_param.md)：获取队列路由配置参数。
- [acltdtCreateQueueRouteList](acltdt_create_queue_route_list.md)：创建容纳多条队列路由的配置列表，供 AddQueueRoute 组装以及批量绑定、查询或解绑使用。
- [acltdtDestroyQueueRouteList](acltdt_destroy_queue_route_list.md)：销毁队列路由配置数组。
- [acltdtAddQueueRoute](acltdt_add_queue_route.md)：向路由数组添加路由配置。
- [acltdtGetQueueRoute](acltdt_get_queue_route.md)：从路由数组获取指定路由配置。
- [acltdtGetQueueRouteNum](acltdt_get_queue_route_num.md)：获取路由数组中的路由数量。
- [acltdtCreateQueueRouteQueryInfo](acltdt_create_queue_route_query_info.md)：创建队列路由的查询条件对象，配合 SetQueueRouteQueryInfo 设置条件后交给 QueryQueueRoutes 查询。
- [acltdtDestroyQueueRouteQueryInfo](acltdt_destroy_queue_route_query_info.md)：销毁队列路由关系查询条件。
- [acltdtSetQueueRouteQueryInfo](acltdt_set_queue_route_query_info.md)：向已创建的路由查询条件对象写入指定参数，供 QueryQueueRoutes 使用；参数长度须匹配类型。
