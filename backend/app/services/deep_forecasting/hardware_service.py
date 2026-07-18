import os
import platform
from functools import lru_cache
from importlib import util
from typing import Any

from app.core.config import Settings
from app.schemas.deep_forecasting import DeepForecastHardwareResponse
from app.services.deep_forecasting.errors import DeepHardwareConfigurationError


@lru_cache(maxsize=8)
def _detect(accelerator: str, devices: int, cpu_fallback: bool, threads: int, deterministic: bool) -> tuple[Any, ...]:
    torch_available = util.find_spec("torch") is not None
    cuda_available = False
    cuda_count = 0
    cuda_names: list[str] = []
    cuda_version: str | None = None
    mps_available = False
    if torch_available:
        try:
            import torch

            cuda_available = bool(torch.cuda.is_available())
            cuda_count = int(torch.cuda.device_count()) if cuda_available else 0
            cuda_names = [str(torch.cuda.get_device_name(index)) for index in range(cuda_count)]
            cuda_version = str(torch.version.cuda) if torch.version.cuda else None
            mps_backend = getattr(torch.backends, "mps", None)
            mps_available = bool(mps_backend and mps_backend.is_available())
        except (ImportError, RuntimeError, OSError):
            torch_available = False
    available = {"cpu": True, "cuda": cuda_available, "mps": mps_available}
    if accelerator == "auto":
        selected = "cuda" if cuda_available else "mps" if mps_available else "cpu"
    elif available.get(accelerator, False):
        selected = accelerator
    elif cpu_fallback:
        selected = "cpu"
    else:
        raise DeepHardwareConfigurationError(f"Requested accelerator '{accelerator}' is unavailable")
    selected_devices = min(devices, cuda_count) if selected == "cuda" else 1
    return (
        platform.system(),
        platform.architecture()[0],
        os.cpu_count() or 1,
        threads,
        None,
        torch_available,
        cuda_available,
        cuda_count,
        tuple(cuda_names),
        cuda_version,
        mps_available,
        selected,
        selected_devices,
        cpu_fallback,
        deterministic,
    )


def hardware_report(settings: Settings, requested_accelerator: str | None = None) -> DeepForecastHardwareResponse:
    values = _detect(
        requested_accelerator or settings.deep_forecasting_accelerator,
        settings.deep_forecasting_devices,
        settings.deep_forecasting_cpu_fallback,
        settings.deep_forecasting_torch_num_threads,
        settings.deep_forecasting_deterministic,
    )
    return DeepForecastHardwareResponse(
        operating_system=values[0],
        python_architecture=values[1],
        cpu_logical_count=values[2],
        configured_training_threads=values[3],
        available_memory_bytes=values[4],
        pytorch_available=values[5],
        cuda_available=values[6],
        cuda_device_count=values[7],
        cuda_device_names=list(values[8]),
        cuda_version=values[9],
        mps_available=values[10],
        selected_accelerator=values[11],
        selected_device_count=values[12],
        cpu_fallback_enabled=values[13],
        deterministic_mode_configured=values[14],
    )
