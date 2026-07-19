"use client";

import { useState } from "react";
import { ShieldCheck, FileText, Lock, Eye, AlertTriangle } from "lucide-react";

export function ComplianceDashboard() {
  const [activeTab, setActiveTab] = useState("audit");

  return (
    <div className="space-y-6">
      <div className="flex gap-4 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("audit")}
          className={`flex items-center gap-2 px-3 py-2 text-sm ${activeTab === "audit" ? "border-b-2 border-emerald-400 text-emerald-400" : "text-slate-400 hover:text-slate-200"}`}
        >
          <FileText size={16} /> Audit Logs
        </button>
        <button
          onClick={() => setActiveTab("rbac")}
          className={`flex items-center gap-2 px-3 py-2 text-sm ${activeTab === "rbac" ? "border-b-2 border-emerald-400 text-emerald-400" : "text-slate-400 hover:text-slate-200"}`}
        >
          <Lock size={16} /> Access Control (RBAC)
        </button>
        <button
          onClick={() => setActiveTab("governance")}
          className={`flex items-center gap-2 px-3 py-2 text-sm ${activeTab === "governance" ? "border-b-2 border-emerald-400 text-emerald-400" : "text-slate-400 hover:text-slate-200"}`}
        >
          <Eye size={16} /> Data Lineage & Governance
        </button>
      </div>

      {activeTab === "audit" && (
        <div className="panel p-5">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-semibold text-slate-200">
              Recent Audit Events
            </h3>
          </div>
          <div className="space-y-4">
            {[
              {
                action: "DATASET_UPLOAD",
                user: "admin",
                resource: "dataset-123",
                time: "2 mins ago",
              },
              {
                action: "ROLE_UPDATED",
                user: "admin",
                resource: "user-456",
                time: "1 hour ago",
              },
              {
                action: "MODEL_TRAINED",
                user: "data_scientist_1",
                resource: "model-789",
                time: "3 hours ago",
              },
            ].map((log, i) => (
              <div
                key={i}
                className="flex items-center justify-between border-b border-slate-800 pb-3"
              >
                <div>
                  <div className="text-sm font-medium text-slate-200">
                    {log.action}
                  </div>
                  <div className="text-xs text-slate-500">
                    By {log.user} on {log.resource}
                  </div>
                </div>
                <div className="text-xs text-slate-400">{log.time}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "rbac" && (
        <div className="panel p-5">
          <h3 className="mb-4 font-semibold text-slate-200">
            Role-Based Access Policies
          </h3>
          <p className="mb-4 text-sm text-slate-400">
            Manage roles and permissions for users and service accounts.
          </p>
          <div className="rounded-md border border-dashed border-slate-700 p-8 text-center">
            <ShieldCheck className="mx-auto mb-2 text-emerald-400" size={32} />
            <p className="text-sm text-slate-300">RBAC Enforcement Active</p>
          </div>
        </div>
      )}

      {activeTab === "governance" && (
        <div className="panel border-l-2 border-l-amber-500 p-5">
          <div className="mb-4 flex items-center gap-2">
            <AlertTriangle className="text-amber-500" size={20} />
            <h3 className="font-semibold text-slate-200">
              Compliance Warnings
            </h3>
          </div>
          <p className="text-sm text-slate-400">
            1 dataset is missing PII classification.
          </p>
        </div>
      )}
    </div>
  );
}
