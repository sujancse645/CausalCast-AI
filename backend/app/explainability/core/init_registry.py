from app.explainability.core.registry import ExplanationMethodRegistry

ExplanationMethodRegistry.register(
    method_name="native_importance",
    description="Native feature importance derived directly from the model (e.g. split/gain for trees, weights for linear models).",
    requires_background_data=False,
    is_global=True,
    is_local=False
)(lambda *args, **kwargs: None)

ExplanationMethodRegistry.register(
    method_name="tree_shap_global",
    description="SHAP summary across all features using TreeExplainer.",
    requires_background_data=True,
    is_global=True,
    is_local=False
)(lambda *args, **kwargs: None)

ExplanationMethodRegistry.register(
    method_name="tree_shap_local",
    description="SHAP feature attribution for a single prediction using TreeExplainer.",
    requires_background_data=True,
    is_global=False,
    is_local=True
)(lambda *args, **kwargs: None)

ExplanationMethodRegistry.register(
    method_name="permutation_importance",
    description="Permutation feature importance calculated on a validation set.",
    requires_background_data=True,
    is_global=True,
    is_local=False
)(lambda *args, **kwargs: None)

ExplanationMethodRegistry.register(
    method_name="linear_coefficients",
    description="Standardized coefficients of a linear model.",
    requires_background_data=False,
    is_global=True,
    is_local=False
)(lambda *args, **kwargs: None)

ExplanationMethodRegistry.register(
    method_name="pdp",
    description="Partial Dependence Plot.",
    requires_background_data=True,
    is_global=True,
    is_local=False
)(lambda *args, **kwargs: None)

ExplanationMethodRegistry.register(
    method_name="ale",
    description="Accumulated Local Effects.",
    requires_background_data=True,
    is_global=True,
    is_local=False
)(lambda *args, **kwargs: None)

ExplanationMethodRegistry.register(
    method_name="lag_occlusion_importance",
    description="Importance of lag variables estimated via occlusion/perturbation.",
    requires_background_data=True,
    is_global=True,
    is_local=False
)(lambda *args, **kwargs: None)

ExplanationMethodRegistry.register(
    method_name="tft_variable_selection",
    description="TFT native variable selection weights.",
    requires_background_data=False,
    is_global=True,
    is_local=False
)(lambda *args, **kwargs: None)

ExplanationMethodRegistry.register(
    method_name="tft_attention",
    description="TFT native temporal attention weights.",
    requires_background_data=False,
    is_global=False,
    is_local=True
)(lambda *args, **kwargs: None)
