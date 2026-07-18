import os
from fastapi import FastAPI
from prometheus_client import make_asgi_app
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def setup_observability(app: FastAPI, app_name: str, app_env: str) -> None:
    # 1. Prometheus Metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    # 2. OpenTelemetry setup
    otel_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otel_endpoint:
        resource = Resource.create({
            "service.name": app_name,
            "deployment.environment": app_env
        })
        
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=otel_endpoint, insecure=True)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        
        FastAPIInstrumentor.instrument_app(app)
