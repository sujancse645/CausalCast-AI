"use client";

import { Activity, AlertTriangle, Search, CheckCircle2, GitBranch, Lightbulb } from "lucide-react";
import React from "react";

export function ExplainabilityDashboard() {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
      
      {/* Top Stats */}
      <div className="grid gap-6 md:grid-cols-4">
        {[
          { label: "Global Explanations", value: "24", icon: <Activity size={20} className="text-blue-400" /> },
          { label: "Local SHAP Run", value: "142", icon: <Search size={20} className="text-emerald-400" /> },
          { label: "Detected Anomalies", value: "3", icon: <AlertTriangle size={20} className="text-amber-400" /> },
          { label: "Active Scenarios", value: "12", icon: <GitBranch size={20} className="text-violet-400" /> },
        ].map((stat, i) => (
          <div key={i} className="panel p-6 flex flex-col relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="flex justify-between items-start mb-4 relative z-10">
              <span className="text-slate-400 font-medium">{stat.label}</span>
              {stat.icon}
            </div>
            <span className="text-4xl font-bold text-white relative z-10">{stat.value}</span>
          </div>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-[2fr_1fr]">
        {/* Main Content Area */}
        <div className="panel p-6 min-h-[400px]">
          <div className="flex items-center gap-3 mb-6">
            <Lightbulb className="text-amber-400" size={24} />
            <h2 className="text-xl font-semibold">Prediction Explainer</h2>
          </div>
          
          <div className="h-64 border border-slate-700/50 rounded-xl bg-slate-800/50 flex flex-col items-center justify-center text-center p-6">
             <Search className="text-slate-500 mb-4" size={48} />
             <p className="text-slate-300 font-medium mb-2">Select a Prediction</p>
             <p className="text-slate-500 text-sm max-w-sm">
                Choose a specific forecast point to visualize SHAP values, temporal attention, and counterfactuals.
             </p>
          </div>
        </div>

        {/* Diagnostics Panel */}
        <div className="space-y-6">
          <div className="panel p-6">
            <h3 className="font-semibold text-lg mb-4">Diagnostics Health</h3>
            <div className="space-y-4">
              {[
                { label: "Residual Bias", status: "Healthy", color: "text-emerald-400" },
                { label: "Feature Drift", status: "Warning: 'price'", color: "text-amber-400" },
                { label: "Model Disagreement", status: "Low", color: "text-emerald-400" },
              ].map((item, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
                  <span className="text-slate-300 text-sm">{item.label}</span>
                  <span className={`text-sm font-medium ${item.color}`}>{item.status}</span>
                </div>
              ))}
            </div>
          </div>
          
          <div className="panel p-6 bg-gradient-to-br from-indigo-900/20 to-purple-900/20 border-indigo-500/20">
            <h3 className="font-semibold text-lg mb-4 text-indigo-300">Scenario Studio</h3>
            <p className="text-sm text-slate-400 mb-4">
              Simulate business interventions and compare forecast outcomes.
            </p>
            <button className="w-full py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg font-medium transition-colors text-sm">
              Create Scenario
            </button>
          </div>
        </div>
      </div>
      
    </div>
  );
}
