## 2026-01-20 - ONNX Threading for Sequential Models
**Learning:** Setting `inter_op_num_threads` equal to `intra_op_num_threads` degrades performance for sequential models like Parakeet (batch size 1). It creates unnecessary thread pool overhead.
**Action:** Always force `inter_op_num_threads=1` for local sequential inference unless profiling proves otherwise.
