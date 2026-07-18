from typing import Literal

from pydantic import BaseModel

ModuleStatus = Literal["planned", "next", "preparation_ready", "baseline_forecasting_ready", "gradient_boosting_ready"]


class ApplicationInfo(BaseModel):
    name: str
    version: str
    environment: str


class BackendInfo(BaseModel):
    framework: Literal["FastAPI"] = "FastAPI"
    status: Literal["operational"] = "operational"


class DatabaseInfo(BaseModel):
    type: str
    status: Literal["connected", "unavailable"]


class ModulesInfo(BaseModel):
    data_intelligence: ModuleStatus = "preparation_ready"
    forecasting: ModuleStatus = "gradient_boosting_ready"
    deep_forecasting_infrastructure: Literal["ready"] = "ready"
    deep_forecasting_training: Literal["nhits_ready"] = "nhits_ready"
    probabilistic_forecasting: Literal["planned"] = "planned"
    causal_intelligence: ModuleStatus = "planned"
    simulation: ModuleStatus = "planned"
    optimization: ModuleStatus = "planned"
    rag_copilot: ModuleStatus = "planned"


class SystemInfoResponse(BaseModel):
    application: ApplicationInfo
    backend: BackendInfo
    database: DatabaseInfo
    modules: ModulesInfo
