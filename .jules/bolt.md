## 2024-05-23 - [ONNX Runtime Threading Optimization]
**Learning:** For sequential workloads like STT (processing one stream), setting `inter_op_num_threads` > 1 adds overhead without benefit. It should be pinned to 1 while `intra_op_num_threads` can scale with CPU cores.
**Action:** When configuring ONNX Runtime `SessionOptions`, ensure `inter_op_num_threads` is explicitly set to 1 if the model graph doesn't support parallel execution of operators.
