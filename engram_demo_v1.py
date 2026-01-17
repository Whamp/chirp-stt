import torch
import torch.nn as nn
import numpy as np

class HashMapping:
    def __init__(self, num_layers=32):
        self.num_layers = num_layers

    def hash(self, input_ids):
        """
        Computes hashes for all layers.
        input_ids: torch.Tensor [B, L]
        Returns: numpy array of shape [num_layers, B, L]
        """
        if isinstance(input_ids, torch.Tensor):
            input_np = input_ids.cpu().numpy()
        else:
            input_np = input_ids

        hashes = []
        for i in range(self.num_layers):
            hashes.append(self._get_ngram_hashes(input_np, i))

        return np.array(hashes)

    def _get_ngram_hashes(self, input_ids_np, layer_id):
        """
        Computes hash for a single layer.
        """
        # N-gram hashing logic simulation
        result = (input_ids_np * (layer_id + 17)) ^ 0xDEADBEEF
        result = (result * 31) % 50000
        return result.astype(np.int64)

class EnGramLayer(nn.Module):
    def __init__(self, layer_id, hash_mapping):
        super().__init__()
        self.layer_id = layer_id
        self.hash_mapping = hash_mapping
        self.multi_head_embedding = nn.Embedding(50000, 64)

    def forward(self, hidden_states, input_ids):
        """
        hidden_states: [B, L, HC_MULT, D]
        input_ids: [B, L]
        """
        # Optimized: Call internal _get_ngram_hashes directly for the specific layer
        # instead of computing hashes for all layers.
        input_np = input_ids.cpu().numpy() if isinstance(input_ids, torch.Tensor) else input_ids
        hash_input_ids = torch.from_numpy(self.hash_mapping._get_ngram_hashes(input_np, self.layer_id))

        embeddings = self.multi_head_embedding(hash_input_ids).flatten(start_dim=-2)
        gates = []
        return embeddings
