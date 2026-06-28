"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { get, post, patch, del } from "@/lib/api";
import { useSubscription, useCreditBalance, useCreditTransactions, useChangePlan, useBillingPortal } from "@/hooks/useBilling";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";

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

  if (isLoading) {
    return (
      <div className="max-w-lg space-y-6">
        <Skeleton className="h-48 rounded-xl" />
        <Skeleton className="h-56 rounded-xl" />
      </div>
    );
  }

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
    <div className="max-w-lg space-y-6">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Personal Information</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleProfileSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-foreground">First Name</label>
                <input className="input-base w-full" value={form.first_name} onChange={e => setForm(f => ({ ...f, first_name: e.target.value }))} />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-foreground">Last Name</label>
                <input className="input-base w-full" value={form.last_name} onChange={e => setForm(f => ({ ...f, last_name: e.target.value }))} />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-foreground">Email</label>
              <input className="input-base w-full bg-muted text-muted-foreground" value={user?.email ?? ""} disabled />
            </div>
            {profileMsg && <p className={`text-sm ${profileMsg.includes("Failed") ? "text-destructive" : "text-success"}`}>{profileMsg}</p>}
            <Button type="submit" loading={updateProfile.isPending}>
              {updateProfile.isPending ? "Saving..." : "Save Changes"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Change Password</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePwSubmit} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-foreground">Current Password</label>
              <input type="password" className="input-base w-full" value={pwForm.current_password} onChange={e => setPwForm(f => ({ ...f, current_password: e.target.value }))} />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-foreground">New Password</label>
              <input type="password" className="input-base w-full" value={pwForm.new_password} onChange={e => setPwForm(f => ({ ...f, new_password: e.target.value }))} />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-foreground">Confirm New Password</label>
              <input type="password" className="input-base w-full" value={pwForm.confirm_password} onChange={e => setPwForm(f => ({ ...f, confirm_password: e.target.value }))} />
            </div>
            {pwMsg && <p className={`text-sm ${pwMsg.includes("Failed") || pwMsg.includes("don't") ? "text-destructive" : "text-success"}`}>{pwMsg}</p>}
            <Button type="submit" variant="secondary" loading={changePassword.isPending}>
              {changePassword.isPending ? "Changing..." : "Change Password"}
            </Button>
          </form>
        </CardContent>
      </Card>
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

  if (loadingSub) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-40 rounded-xl" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-48 rounded-xl" />)}
        </div>
      </div>
    );
  }

  const currentPlan = subscription?.plan ?? "FREE";
  const creditsRemaining = credits?.credits_remaining ?? subscription?.credits_remaining ?? 0;
  const creditsMonthly = credits?.credits_monthly ?? subscription?.credits_monthly ?? 100;
  const pct = creditsMonthly > 0 ? Math.min(100, (creditsRemaining / creditsMonthly) * 100) : 0;

  const PLAN_ORDER = ["FREE", "STARTER", "PRO", "ENTERPRISE"];
  const currentIdx = PLAN_ORDER.indexOf(currentPlan);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">Current Plan</CardTitle>
              <p className="mt-1 text-2xl font-bold text-primary">{currentPlan}</p>
            </div>
            <Badge variant={subscription?.status === "active" ? "success" : "warning"}>
              {subscription?.status ?? "unknown"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="mb-2 flex justify-between text-sm text-muted-foreground">
            <span>Credits remaining</span>
            <span>{creditsRemaining.toLocaleString()} / {creditsMonthly.toLocaleString()}</span>
          </div>
          <div className="h-2 w-full rounded-full bg-muted">
            <div className="h-2 rounded-full bg-primary transition-all" style={{ width: `${pct}%` }} />
          </div>
          <Button
            variant="secondary"
            className="mt-4"
            onClick={() => billingPortal.mutate(window.location.href)}
            loading={billingPortal.isPending}
          >
            {billingPortal.isPending ? "Opening..." : "Manage Billing"}
          </Button>
        </CardContent>
      </Card>

      <div>
        <h2 className="mb-4 text-base font-semibold text-foreground">Plans</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {PLANS.map((plan, idx) => {
            const isCurrent = plan.id === currentPlan;
            const isUpgrade = idx > currentIdx;
            return (
              <Card key={plan.id} className={isCurrent ? "border-primary bg-primary/5" : ""}>
                <CardContent className="p-5">
                  <div className="font-semibold text-foreground">{plan.label}</div>
                  <div className="mb-3 mt-1 text-xl font-bold text-primary">{plan.price}</div>
                  <ul className="mb-4 space-y-1">
                    {plan.features.map(f => (
                      <li key={f} className="flex items-start gap-1 text-xs text-muted-foreground">
                        <span className="mt-0.5 text-success">✓</span> {f}
                      </li>
                    ))}
                  </ul>
                  {isCurrent ? (
                    <Badge className="w-full justify-center py-1.5" variant="primary">Current Plan</Badge>
                  ) : (
                    <Button
                      size="sm"
                      variant={isUpgrade ? "primary" : "secondary"}
                      className="w-full"
                      onClick={() => changePlan.mutate(plan.id)}
                      loading={changePlan.isPending}
                    >
                      {isUpgrade ? "Upgrade" : "Downgrade"}
                    </Button>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Recent Transactions</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {!transactions?.items?.length ? (
            <p className="px-6 py-8 text-sm text-muted-foreground">No transactions yet.</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="border-b border-border bg-muted/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Amount</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Balance</th>
                </tr>
              </thead>
              <tbody>
                {transactions.items.map(tx => (
                  <tr key={tx.id} className="border-t border-border hover:bg-muted/30">
                    <td className="px-4 py-3 text-muted-foreground">{new Date(tx.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3 text-foreground">{tx.transaction_type}</td>
                    <td className={`px-4 py-3 font-medium ${tx.amount >= 0 ? "text-success" : "text-destructive"}`}>
                      {tx.amount >= 0 ? "+" : ""}{tx.amount}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{tx.balance_after}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
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
    <div className="space-y-6">
      <Card className="border-warning/30 bg-warning/5">
        <CardContent className="flex items-start gap-3 p-4">
          <span className="text-lg text-warning">⚠</span>
          <p className="text-sm text-foreground">API keys grant full access to your organization. Keep them secure and never share them publicly.</p>
        </CardContent>
      </Card>

      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-foreground">API Keys</h2>
        <Button onClick={() => setShowModal(true)}>+ Create API Key</Button>
      </div>

      {isLoading ? (
        <Skeleton className="h-48 rounded-xl" />
      ) : !apiKeys?.length ? (
        <p className="text-sm text-muted-foreground">No API keys yet.</p>
      ) : (
        <Card className="overflow-hidden">
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead className="border-b border-border bg-muted/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Key Prefix</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Created</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Last Used</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {apiKeys.map(key => (
                  <tr key={key.id} className="border-t border-border hover:bg-muted/30">
                    <td className="px-4 py-3 font-medium text-foreground">{key.name}</td>
                    <td className="px-4 py-3 font-mono text-muted-foreground">{key.key_prefix.slice(0, 8)}...</td>
                    <td className="px-4 py-3 text-muted-foreground">{new Date(key.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3 text-muted-foreground">{key.last_used_at ? new Date(key.last_used_at).toLocaleDateString() : "Never"}</td>
                    <td className="px-4 py-3">
                      <Badge variant={key.is_active ? "success" : "gray"}>{key.is_active ? "Active" : "Inactive"}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => revokeKey.mutate(key.id)}
                        disabled={revokeKey.isPending}
                        className="text-xs font-medium text-destructive hover:underline disabled:opacity-50"
                      >
                        Revoke
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
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
    <div className="space-y-6">
      <h2 className="text-base font-semibold text-foreground">Integrations</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {INTEGRATIONS.map(integration => (
          <Card key={integration.id}>
            <CardContent className="p-5">
              <div className="mb-3 flex items-center gap-3">
                <div className={`flex h-10 w-10 items-center justify-center rounded-lg text-sm font-bold text-white ${integration.color}`}>
                  {integration.initials}
                </div>
                <div>
                  <div className="text-sm font-medium text-foreground">{integration.name}</div>
                  <Badge variant={connected[integration.id] ? "success" : "gray"}>
                    {connected[integration.id] ? "Connected" : "Disconnected"}
                  </Badge>
                </div>
              </div>
              <p className="mb-4 text-xs text-muted-foreground">{integration.description}</p>
              <Button variant="secondary" size="sm" className="w-full" onClick={() => { setConfiguring(integration); setApiKey(""); setMsg(""); }}>
                Configure
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <Modal
        open={configuring !== null}
        onClose={() => setConfiguring(null)}
        title={configuring ? `Configure ${configuring.name}` : "Configure"}
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setConfiguring(null)}>Cancel</Button>
            <Button type="submit" form="integration-form" loading={saving}>Save</Button>
          </div>
        }
      >
        <form id="integration-form" onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-foreground">API Key</label>
            <input type="password" className="input-base w-full" value={apiKey} onChange={e => setApiKey(e.target.value)} placeholder="Enter your API key" />
          </div>
          {msg && <p className={`text-sm ${msg.includes("Failed") ? "text-destructive" : "text-success"}`}>{msg}</p>}
        </form>
      </Modal>
    </div>
  );
}

// ---- Main Settings Page ----
export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<Tab>("Profile");

  return (
    <div className="page-container space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground md:text-3xl">Settings</h1>
        <p className="text-sm text-muted-foreground">Manage your profile, billing, API keys, and integrations.</p>
      </div>

      <div className="flex gap-1 overflow-x-auto border-b border-border">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`shrink-0 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === tab
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === "Profile" && <ProfileTab />}
      {activeTab === "Billing" && <BillingTab />}
      {activeTab === "API Keys" && <ApiKeysTab />}
      {activeTab === "Integrations" && <IntegrationsTab />}
    </div>
  );
}
