"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { get, post, patch, del } from "@/lib/api";
import { useSubscription, useCreditBalance, useCreditTransactions, useChangePlan, useBillingPortal } from "@/hooks/useBilling";

// ---- Types ----
interface UserProfile {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
}

interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at?: string;
  is_active: boolean;
}

// ---- Hooks ----
function useCurrentUser() {
  return useQuery({
    queryKey: ["user", "me"],
    queryFn: () => get<{ data: UserProfile }>("/users/me").then(r => r.data),
  });
}

function useApiKeys() {
  return useQuery({
    queryKey: ["user", "api-keys"],
    queryFn: () => get<{ data: ApiKey[]; items?: ApiKey[] }>("/users/api-keys").then(r => r.data ?? []),
  });
}

// ---- Tab definitions ----
const TABS = ["Profile", "Billing", "API Keys", "Integrations"] as const;
type Tab = typeof TABS[number];

// ---- Profile Tab ----
function ProfileTab() {
  const { data: user, isLoading } = useCurrentUser();
  const qc = useQueryClient();
  const [form, setForm] = useState({ first_name: "", last_name: "" });
  const [pwForm, setPwForm] = useState({ current_password: "", new_password: "", confirm_password: "" });
  const [profileMsg, setProfileMsg] = useState("");
  const [pwMsg, setPwMsg] = useState("");

  useEffect(() => {
    if (user) setForm({ first_name: user.first_name, last_name: user.last_name });
  }, [user]);

  const updateProfile = useMutation({
    mutationFn: (data: { first_name: string; last_name: string }) => patch("/users/me", data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["user", "me"] }); setProfileMsg("Profile updated."); setTimeout(() => setProfileMsg(""), 3000); },
    onError: () => setProfileMsg("Failed to update profile."),
  });

  const changePassword = useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) => post("/users/me/password", data),
    onSuccess: () => { setPwMsg("Password changed."); setPwForm({ current_password: "", new_password: "", confirm_password: "" }); setTimeout(() => setPwMsg(""), 3000); },
    onError: () => setPwMsg("Failed to change password."),
  });

  if (isLoading) return <div className="py-12 flex justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" /></div>;

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfile.mutate(form);
  };

  const handlePwSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (pwForm.new_password !== pwForm.confirm_password) { setPwMsg("Passwords don't match."); return; }
    changePassword.mutate({ current_password: pwForm.current_password, new_password: pwForm.new_password });
  };

  return (
    <div className="space-y-8 max-w-lg">
      <div>
        <h2 className="text-base font-semibold text-gray-900 mb-4">Personal Information</h2>
        <form onSubmit={handleProfileSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={form.first_name}
                onChange={e => setForm(f => ({ ...f, first_name: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={form.last_name}
                onChange={e => setForm(f => ({ ...f, last_name: e.target.value }))}
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-gray-50 text-gray-500"
              value={user?.email ?? ""}
              disabled
            />
          </div>
          {profileMsg && <p className={`text-sm ${profileMsg.includes("Failed") ? "text-red-600" : "text-green-600"}`}>{profileMsg}</p>}
          <button type="submit" disabled={updateProfile.isPending} className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50">
            {updateProfile.isPending ? "Saving..." : "Save Changes"}
          </button>
        </form>
      </div>

      <div className="border-t border-gray-200 pt-8">
        <h2 className="text-base font-semibold text-gray-900 mb-4">Change Password</h2>
        <form onSubmit={handlePwSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Current Password</label>
            <input
              type="password"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={pwForm.current_password}
              onChange={e => setPwForm(f => ({ ...f, current_password: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
            <input
              type="password"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={pwForm.new_password}
              onChange={e => setPwForm(f => ({ ...f, new_password: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
            <input
              type="password"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={pwForm.confirm_password}
              onChange={e => setPwForm(f => ({ ...f, confirm_password: e.target.value }))}
            />
          </div>
          {pwMsg && <p className={`text-sm ${pwMsg.includes("Failed") || pwMsg.includes("don't") ? "text-red-600" : "text-green-600"}`}>{pwMsg}</p>}
          <button type="submit" disabled={changePassword.isPending} className="px-4 py-2 bg-gray-800 text-white text-sm font-medium rounded-lg hover:bg-gray-900 disabled:opacity-50">
            {changePassword.isPending ? "Changing..." : "Change Password"}
          </button>
        </form>
      </div>
    </div>
  );
}

// ---- Billing Tab ----
const PLANS = [
  { id: "FREE", label: "Free", price: "$0/mo", features: ["100 credits/mo", "Basic search", "Email support"] },
  { id: "STARTER", label: "Starter", price: "$49/mo", features: ["2,000 credits/mo", "Advanced search", "CRM access", "Priority support"] },
  { id: "PRO", label: "Pro", price: "$149/mo", features: ["10,000 credits/mo", "All integrations", "API access", "Dedicated support"] },
  { id: "ENTERPRISE", label: "Enterprise", price: "$499/mo", features: ["Unlimited credits", "Custom integrations", "SLA guarantee", "Account manager"] },
];

function BillingTab() {
  const { data: subscription, isLoading: loadingSub } = useSubscription();
  const { data: credits } = useCreditBalance();
  const { data: transactions } = useCreditTransactions();
  const changePlan = useChangePlan();
  const billingPortal = useBillingPortal();

  if (loadingSub) return <div className="py-12 flex justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" /></div>;

  const currentPlan = subscription?.plan ?? "FREE";
  const creditsRemaining = credits?.credits_remaining ?? subscription?.credits_remaining ?? 0;
  const creditsMonthly = credits?.credits_monthly ?? subscription?.credits_monthly ?? 100;
  const pct = creditsMonthly > 0 ? Math.min(100, (creditsRemaining / creditsMonthly) * 100) : 0;

  const PLAN_ORDER = ["FREE", "STARTER", "PRO", "ENTERPRISE"];
  const currentIdx = PLAN_ORDER.indexOf(currentPlan);

  return (
    <div className="space-y-8">
      {/* Current plan card */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-gray-900">Current Plan</h2>
            <p className="text-2xl font-bold text-indigo-600 mt-1">{currentPlan}</p>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${subscription?.status === "active" ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"}`}>
            {subscription?.status ?? "unknown"}
          </span>
        </div>
        <div className="mb-2 flex justify-between text-sm text-gray-600">
          <span>Credits remaining</span>
          <span>{creditsRemaining.toLocaleString()} / {creditsMonthly.toLocaleString()}</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2">
          <div className="bg-indigo-500 h-2 rounded-full transition-all" style={{ width: `${pct}%` }} />
        </div>
        <button
          onClick={() => billingPortal.mutate(window.location.href)}
          disabled={billingPortal.isPending}
          className="mt-4 px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          {billingPortal.isPending ? "Opening..." : "Manage Billing"}
        </button>
      </div>

      {/* Plan cards */}
      <div>
        <h2 className="text-base font-semibold text-gray-900 mb-4">Plans</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {PLANS.map((plan, idx) => {
            const isCurrent = plan.id === currentPlan;
            const isUpgrade = idx > currentIdx;
            return (
              <div key={plan.id} className={`border rounded-xl p-5 ${isCurrent ? "border-indigo-400 bg-indigo-50" : "border-gray-200 bg-white"}`}>
                <div className="font-semibold text-gray-900">{plan.label}</div>
                <div className="text-xl font-bold text-indigo-600 mt-1 mb-3">{plan.price}</div>
                <ul className="space-y-1 mb-4">
                  {plan.features.map(f => (
                    <li key={f} className="text-xs text-gray-600 flex items-start gap-1">
                      <span className="text-green-500 mt-0.5">✓</span> {f}
                    </li>
                  ))}
                </ul>
                {isCurrent ? (
                  <div className="text-center text-xs font-medium text-indigo-600 bg-indigo-100 rounded-lg py-1.5">Current Plan</div>
                ) : (
                  <button
                    onClick={() => changePlan.mutate(plan.id)}
                    disabled={changePlan.isPending}
                    className={`w-full text-xs font-medium rounded-lg py-1.5 ${isUpgrade ? "bg-indigo-600 text-white hover:bg-indigo-700" : "border border-gray-300 text-gray-700 hover:bg-gray-50"} disabled:opacity-50`}
                  >
                    {changePlan.isPending ? "..." : isUpgrade ? "Upgrade" : "Downgrade"}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Transactions */}
      <div>
        <h2 className="text-base font-semibold text-gray-900 mb-4">Recent Transactions</h2>
        {!transactions?.items?.length ? (
          <p className="text-gray-400 text-sm">No transactions yet.</p>
        ) : (
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Date</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Type</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Amount</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Balance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {transactions.items.map(tx => (
                  <tr key={tx.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-600">{new Date(tx.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3 text-gray-800">{tx.transaction_type}</td>
                    <td className={`px-4 py-3 font-medium ${tx.amount >= 0 ? "text-green-600" : "text-red-600"}`}>
                      {tx.amount >= 0 ? "+" : ""}{tx.amount}
                    </td>
                    <td className="px-4 py-3 text-gray-600">{tx.balance_after}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ---- API Keys Tab ----
function ApiKeysTab() {
  const { data: apiKeys, isLoading } = useApiKeys();
  const qc = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  const createKey = useMutation({
    mutationFn: (name: string) => post<{ data: { key: string } }>("/users/api-keys", { name }),
    onSuccess: (res: { data: { key: string } }) => {
      qc.invalidateQueries({ queryKey: ["user", "api-keys"] });
      setCreatedKey(res.data.key);
    },
    onError: () => setError("Failed to create API key."),
  });

  const revokeKey = useMutation({
    mutationFn: (id: string) => del(`/users/api-keys/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["user", "api-keys"] }),
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) { setError("Name is required."); return; }
    setError("");
    createKey.mutate(newKeyName.trim());
  };

  const handleCopy = () => {
    if (createdKey) { navigator.clipboard.writeText(createdKey); setCopied(true); setTimeout(() => setCopied(false), 2000); }
  };

  const closeModal = () => {
    setShowModal(false);
    setNewKeyName("");
    setCreatedKey(null);
    setError("");
    setCopied(false);
  };

  return (
    <div>
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6 flex items-start gap-3">
        <span className="text-amber-500 text-lg">⚠</span>
        <p className="text-sm text-amber-800">API keys grant full access to your organization. Keep them secure and never share them publicly.</p>
      </div>

      <div className="flex justify-between items-center mb-4">
        <h2 className="text-base font-semibold text-gray-900">API Keys</h2>
        <button onClick={() => setShowModal(true)} className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700">
          + Create API Key
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" /></div>
      ) : !apiKeys?.length ? (
        <p className="text-gray-400 text-sm">No API keys yet.</p>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Name</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Key Prefix</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Created</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Last Used</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Status</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {apiKeys.map(key => (
                <tr key={key.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{key.name}</td>
                  <td className="px-4 py-3 font-mono text-gray-600">{key.key_prefix.slice(0, 8)}...</td>
                  <td className="px-4 py-3 text-gray-600">{new Date(key.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3 text-gray-600">{key.last_used_at ? new Date(key.last_used_at).toLocaleDateString() : "Never"}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${key.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}`}>
                      {key.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => revokeKey.mutate(key.id)}
                      disabled={revokeKey.isPending}
                      className="text-xs text-red-600 hover:text-red-800 font-medium disabled:opacity-50"
                    >
                      Revoke
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create API Key Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Create API Key</h2>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
            </div>
            {createdKey ? (
              <div>
                <p className="text-sm text-gray-700 mb-3">Your API key has been created. Copy it now — you won't be able to see it again.</p>
                <div className="flex gap-2 mb-4">
                  <code className="flex-1 bg-gray-100 px-3 py-2 rounded-lg text-xs font-mono break-all">{createdKey}</code>
                  <button onClick={handleCopy} className="px-3 py-2 bg-indigo-600 text-white text-xs rounded-lg hover:bg-indigo-700 shrink-0">
                    {copied ? "Copied!" : "Copy"}
                  </button>
                </div>
                <button onClick={closeModal} className="w-full px-4 py-2 text-sm bg-gray-800 text-white rounded-lg hover:bg-gray-900">
                  Done
                </button>
              </div>
            ) : (
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Key Name</label>
                  <input
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    value={newKeyName}
                    onChange={e => setNewKeyName(e.target.value)}
                    placeholder="e.g. Production App"
                  />
                </div>
                {error && <p className="text-red-600 text-sm">{error}</p>}
                <div className="flex gap-3">
                  <button type="button" onClick={closeModal} className="flex-1 px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">Cancel</button>
                  <button type="submit" disabled={createKey.isPending} className="flex-1 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50">
                    {createKey.isPending ? "Creating..." : "Create"}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ---- Integrations Tab ----
const INTEGRATIONS = [
  { id: "apollo", name: "Apollo.io", initials: "AP", color: "bg-blue-500", description: "B2B data and lead enrichment platform." },
  { id: "hunter", name: "Hunter.io", initials: "HU", color: "bg-orange-500", description: "Find and verify professional email addresses." },
  { id: "clearbit", name: "Clearbit", initials: "CB", color: "bg-teal-500", description: "Real-time data enrichment for companies and contacts." },
  { id: "slack", name: "Slack", initials: "SL", color: "bg-purple-500", description: "Send notifications and alerts to Slack channels." },
  { id: "hubspot", name: "HubSpot", initials: "HS", color: "bg-red-500", description: "Sync deals and contacts with HubSpot CRM." },
  { id: "salesforce", name: "Salesforce", initials: "SF", color: "bg-sky-500", description: "Sync your pipeline with Salesforce." },
];

function IntegrationsTab() {
  const [configuring, setConfiguring] = useState<typeof INTEGRATIONS[0] | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [connected, setConnected] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!configuring) return;
    setSaving(true);
    try {
      await patch(`/integrations/${configuring.id}`, { api_key: apiKey });
      setConnected(c => ({ ...c, [configuring.id]: true }));
      setMsg("Integration configured successfully.");
      setTimeout(() => { setMsg(""); setConfiguring(null); setApiKey(""); }, 1500);
    } catch {
      setMsg("Failed to save integration.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <h2 className="text-base font-semibold text-gray-900 mb-4">Integrations</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {INTEGRATIONS.map(integration => (
          <div key={integration.id} className="bg-white border border-gray-200 rounded-xl p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className={`w-10 h-10 rounded-lg ${integration.color} flex items-center justify-center text-white text-sm font-bold`}>
                {integration.initials}
              </div>
              <div>
                <div className="font-medium text-gray-900 text-sm">{integration.name}</div>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${connected[integration.id] ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                  {connected[integration.id] ? "Connected" : "Disconnected"}
                </span>
              </div>
            </div>
            <p className="text-xs text-gray-500 mb-4">{integration.description}</p>
            <button
              onClick={() => { setConfiguring(integration); setApiKey(""); setMsg(""); }}
              className="w-full px-3 py-1.5 text-xs font-medium border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Configure
            </button>
          </div>
        ))}
      </div>

      {/* Configure Modal */}
      {configuring && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-lg ${configuring.color} flex items-center justify-center text-white text-xs font-bold`}>
                  {configuring.initials}
                </div>
                <h2 className="text-lg font-semibold text-gray-900">{configuring.name}</h2>
              </div>
              <button onClick={() => setConfiguring(null)} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
            </div>
            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
                <input
                  type="password"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={apiKey}
                  onChange={e => setApiKey(e.target.value)}
                  placeholder="Enter your API key"
                />
              </div>
              {msg && <p className={`text-sm ${msg.includes("Failed") ? "text-red-600" : "text-green-600"}`}>{msg}</p>}
              <div className="flex gap-3">
                <button type="button" onClick={() => setConfiguring(null)} className="flex-1 px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">Cancel</button>
                <button type="submit" disabled={saving} className="flex-1 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50">
                  {saving ? "Saving..." : "Save"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// ---- Main Settings Page ----
export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<Tab>("Profile");

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-8">
        <nav className="flex gap-1">
          {TABS.map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab
                  ? "border-indigo-600 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      {activeTab === "Profile" && <ProfileTab />}
      {activeTab === "Billing" && <BillingTab />}
      {activeTab === "API Keys" && <ApiKeysTab />}
      {activeTab === "Integrations" && <IntegrationsTab />}
    </div>
  );
}
