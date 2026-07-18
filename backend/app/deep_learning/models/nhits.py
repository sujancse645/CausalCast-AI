from typing import Any

from app.deep_learning.config.nhits import NHiTSConfig


class NHiTSForecastModel:
    """Lazy NeuralForecast N-HiTS model factory."""

    def build(
        self,
        config: NHiTSConfig,
        historical: list[str],
        future: list[str],
        static: list[str],
        accelerator: str,
        framework_root: str,
    ) -> Any:
        import torch
        from neuralforecast.losses.pytorch import MAE
        from neuralforecast.models import NHITS

        optimizers = {"adam": torch.optim.Adam, "adamw": torch.optim.AdamW, "sgd": torch.optim.SGD}
        schedulers = {
            "step": torch.optim.lr_scheduler.StepLR,
            "cosine": torch.optim.lr_scheduler.CosineAnnealingLR,
        }
        scheduler = schedulers.get(config.scheduler)
        scheduler_kwargs: dict[str, object] | None = None
        if config.scheduler == "step":
            scheduler_kwargs = {"step_size": max(1, config.validation_check_steps), "gamma": 0.5}
        elif config.scheduler == "cosine":
            scheduler_kwargs = {"T_max": max(1, config.max_steps)}
        stacks = config.stack_count
        return NHITS(
            h=config.forecast_horizon,
            input_size=config.input_size,
            hist_exog_list=historical or None,
            futr_exog_list=future or None,
            stat_exog_list=static or None,
            stack_types=["identity"] * stacks,
            n_blocks=[config.blocks_per_stack] * stacks,
            mlp_units=[[config.hidden_size, config.hidden_size]] * config.hidden_layers,
            n_pool_kernel_size=[max(1, 2 ** (stacks - index - 1)) for index in range(stacks)],
            n_freq_downsample=[max(1, 2 ** (stacks - index - 1)) for index in range(stacks)],
            dropout_prob_theta=config.dropout,
            activation=config.activation,
            loss=MAE(),
            valid_loss=MAE(),
            max_steps=config.max_steps,
            learning_rate=config.learning_rate,
            early_stop_patience_steps=config.early_stopping_patience_steps,
            val_check_steps=config.validation_check_steps,
            batch_size=config.batch_size,
            windows_batch_size=config.windows_batch_size,
            scaler_type=config.scaler_type,
            random_seed=config.random_seed,
            optimizer=optimizers[config.optimizer],
            optimizer_kwargs={"weight_decay": config.weight_decay},
            lr_scheduler=scheduler,
            lr_scheduler_kwargs=scheduler_kwargs,
            accelerator=accelerator,
            devices=config.devices if accelerator != "cpu" else 1,
            precision="16-mixed" if accelerator == "cuda" else "32-true",
            deterministic=config.deterministic,
            enable_checkpointing=True,
            logger=False,
            enable_progress_bar=False,
            default_root_dir=framework_root,
        )
