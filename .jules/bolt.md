# Bolt's Journal

## 2025-02-27 - Force inter-op threads to 1 for Parakeet
**Learning:** For sequential STT models like Parakeet (RNN/Transformer based), forcing `inter_op_num_threads` to 1 in ONNX Runtime significantly reduces threading overhead and context switching, compared to letting it default to the number of physical cores or matching `intra_op_num_threads`.
**Action:** Always enforce `inter_op_num_threads=1` when creating ONNX sessions for sequential models, regardless of the `intra_op_num_threads` setting.
