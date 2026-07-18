# Deep checkpointing

NeuralForecast saves the trained model and dataset into an application-owned checkpoint directory. CausalCast records a SHA-256 checksum, size, framework version, model-run owner, and global step. APIs expose checksums and state, never server paths.

Resume requests accept a model-run UUID and application-owned checkpoint type. Absolute paths and traversal are rejected. A resumed attempt receives a new model-run UUID and keeps `resumed_from` lineage; the source remains immutable.

Checkpoint recovery requires compatible PyTorch, PyTorch Lightning, and NeuralForecast versions. User-supplied checkpoints are never loaded.
