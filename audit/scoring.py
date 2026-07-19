import yaml

def load_scoring_policy():
    with open("audit/config/scoring_policy.yaml", "r") as f:
        return yaml.safe_load(f)

class ScoringEngine:
    def __init__(self, policy: dict):
        self.policy = policy
        self.categories = policy.get("categories", {})
        self.gates = policy.get("release_gates", {})

    def score_findings(self, findings: list) -> dict:
        scores = {}
        total_weight = sum(cat.get("weight", 0) for cat in self.categories.values())
        earned_points = 0
        
        for name, cat in self.categories.items():
            cat_findings = [f for f in findings if f.get("category") == name]
            
            # Simple heuristic: lose points for HIGH/CRITICAL severities
            deductions = 0
            has_critical = False
            for f in cat_findings:
                if f.get("severity") == "CRITICAL":
                    deductions += 5
                    has_critical = True
                elif f.get("severity") == "HIGH":
                    deductions += 2
            
            max_points = cat.get("weight", 0)
            awarded = max(0, max_points - deductions)
            earned_points += awarded
            
            scores[name] = {
                "earned": awarded,
                "max": max_points,
                "has_critical": has_critical,
                "confidence": 1.0 if not any(f.get("status") == "BLOCKED" for f in cat_findings) else 0.5
            }
            
        overall = (earned_points / total_weight * 100) if total_weight > 0 else 0
        
        return {
            "categories": scores,
            "overall_score": overall
        }

    def evaluate_gates(self, scores: dict, command_results: dict) -> str:
        overall = scores.get("overall_score", 0)
        has_critical = any(cat.get("has_critical", False) for cat in scores.get("categories", {}).values())
        
        # Check READY gate
        ready_reqs = self.gates.get("READY", {})
        if overall >= ready_reqs.get("min_overall_score", 90) and not has_critical:
            return "READY"
            
        # Check CONDITIONALLY_READY
        cond_reqs = self.gates.get("CONDITIONALLY_READY", {})
        if overall >= cond_reqs.get("min_overall_score", 75) and not has_critical:
            return "CONDITIONALLY_READY"
            
        return "NOT_READY"
