# 资源管理

- [自定义TBufPool](custom_t_buf_pool/index.md)：自定义TBufPool接口索引页，汇总EXTERN_IMPL_BUFPOOL宏、Reset、Init、GetBufHandle及地址与大小管理方法。
- [GetTPipePtr](get_t_pipe_ptr.md)：获取创建TPipe对象时设置的全局唯一TPipe指针，获取后可进行TPipe相关的操作如InitBuffer。
- [LocalMemAllocator](local_mem_allocator/index.md)：根据用户指定的逻辑位置、数据类型、数据长度返回对应的LocalTensor对象。
- [PopStackBuffer](pop_stack_buffer.md)：在指定position（逻辑位置）申请临时空间，空间大小为指定position的全部剩余空间。
- [资源管理](resource_management.md)：资源管理API总览，涵盖TPipe、TBuf、TBufPool、TQue、TQueBind、TSCM、LocalMemAllocator及workspace等。
- [TBuf](t_buf/index.md)：从TBuf上获取指定长度的Tensor，或者获取全部长度的Tensor。
- [TBufPool](t_buf_pool/index.md)：从Tpipe或TBufPool划分资源池，支持非共享模式和共享模式（复用已有资源池地址）。
- [TPipe](t_pipe/index.md)：用于申请HardEvent（硬件类型同步事件）的TEventID，必须与ReleaseEventID搭配使用，调用后占用TEventID直至释放。
- [TQue](t_que/index.md)：从Que中分配Tensor，Tensor大小为InitBuffer时设置的每块内存长度，支持non-inplace和inplace两种接口。
- [TQueBind](t_que_bind/index.md)：从Que中分配Tensor，Tensor所占大小为InitBuffer时设置的每块内存长度。
- [TSCM](tscm/index.md)：从TSCM中分配tensor，大小为InitBuffer时设置的每块内存长度，分配内容可能为随机值。
- [Workspace](workspace/index.md)：获取系统workspace指针。部分高阶API如Matmul需要使用系统workspace，相关接口需要传入系统workspace指针，此时可以通过该接口获取。使用系统workspace时，host侧开发者需要自行申请系统worksp...
