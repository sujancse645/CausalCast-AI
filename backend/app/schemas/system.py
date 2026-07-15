from typing import Literal

from pydantic import BaseModel

ModuleStatus = Literal["planned", "ingestion_ready"]


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
    data_intelligence: ModuleStatus = "ingestion_ready"
    forecasting: ModuleStatus = "planned"
    causal_intelligence: ModuleStatus = "planned"
    simulation: ModuleStatus = "planned"
    optimization: ModuleStatus = "planned"
    rag_copilot: ModuleStatus = "planned"


class SystemInfoResponse(BaseModel):
    application: ApplicationInfo
    backend: BackendInfo
    database: DatabaseInfo
    modules: ModulesInfo
