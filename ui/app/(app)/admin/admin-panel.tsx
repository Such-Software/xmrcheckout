"use client";

import { useActionState, useState } from "react";
import {
  adminCreateUserAction,
  adminDeleteUserAction,
  adminLogoutAction,
  type AdminCreateUserState,
  type AdminDeleteUserState,
  type AdminUser,
} from "./actions";

const createInitial: AdminCreateUserState = {
  error: null,
  success: null,
  apiKey: null,
  webhookSecret: null,
  storeId: null,
};

const deleteInitial: AdminDeleteUserState = {
  error: null,
  success: null,
  deletedId: null,
};

export function AdminPanel({ users }: { users: AdminUser[] }) {
  const [createState, createAction, createPending] = useActionState(
    adminCreateUserAction,
    createInitial
  );
  const [deleteState, deleteAction, deletePending] = useActionState(
    adminDeleteUserAction,
    deleteInitial
  );
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  const visibleUsers = users.filter(
    (u) => u.id !== deleteState.deletedId
  );

  return (
    <div className="min-h-screen px-4 py-12 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold">Admin — Merchants</h1>
        <form action={adminLogoutAction}>
          <button
            type="submit"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Log out
          </button>
        </form>
      </div>

      {/* Add merchant form */}
      <div className="mb-10 p-6 rounded-lg border border-border bg-card">
        <h2 className="text-lg font-semibold mb-4">Add Merchant</h2>
        <form action={createAction} className="space-y-3">
          <div>
            <label htmlFor="payment_address" className="block text-sm font-medium mb-1">
              Primary Address
            </label>
            <textarea
              id="payment_address"
              name="payment_address"
              rows={2}
              className="w-full rounded border border-border bg-background px-3 py-2 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-primary"
              required
            />
          </div>
          <div>
            <label htmlFor="view_key" className="block text-sm font-medium mb-1">
              Secret View Key
            </label>
            <input
              type="text"
              id="view_key"
              name="view_key"
              className="w-full rounded border border-border bg-background px-3 py-2 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-primary"
              required
            />
          </div>
          <button
            type="submit"
            disabled={createPending}
            className="rounded bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            {createPending ? "Creating…" : "Create Merchant"}
          </button>
        </form>

        {createState.error && (
          <p className="mt-3 text-sm text-red-500">{createState.error}</p>
        )}
        {createState.success && (
          <div className="mt-3 p-4 rounded border border-green-500/30 bg-green-500/10 text-sm space-y-2">
            <p className="font-medium text-green-600">{createState.success}</p>
            <div className="space-y-1 font-mono text-xs">
              <p><span className="font-semibold">Store ID:</span> {createState.storeId}</p>
              <p><span className="font-semibold">API Key:</span> {createState.apiKey}</p>
              <p><span className="font-semibold">Webhook Secret:</span> {createState.webhookSecret}</p>
            </div>
            <p className="text-xs text-muted-foreground">Save these credentials — the API key is shown only once.</p>
          </div>
        )}
      </div>

      {/* Merchant list */}
      <div>
        <h2 className="text-lg font-semibold mb-4">
          Registered Merchants ({visibleUsers.length})
        </h2>
        {visibleUsers.length === 0 ? (
          <p className="text-muted-foreground text-sm">No merchants registered yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left">
                  <th className="py-2 pr-4 font-medium">Address</th>
                  <th className="py-2 pr-4 font-medium">Invoices</th>
                  <th className="py-2 pr-4 font-medium">Created</th>
                  <th className="py-2 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {visibleUsers.map((user) => (
                  <tr key={user.id} className="border-b border-border/50">
                    <td className="py-3 pr-4">
                      <span className="font-mono text-xs break-all">
                        {user.payment_address.slice(0, 8)}…{user.payment_address.slice(-8)}
                      </span>
                    </td>
                    <td className="py-3 pr-4">{user.invoice_count}</td>
                    <td className="py-3 pr-4 text-muted-foreground">
                      {user.created_at
                        ? new Date(user.created_at).toLocaleDateString()
                        : "—"}
                    </td>
                    <td className="py-3">
                      {confirmDelete === user.id ? (
                        <span className="flex items-center gap-2">
                          <form action={deleteAction}>
                            <input type="hidden" name="user_id" value={user.id} />
                            <button
                              type="submit"
                              disabled={deletePending}
                              className="text-xs text-red-500 hover:text-red-700 font-medium disabled:opacity-50"
                            >
                              Confirm
                            </button>
                          </form>
                          <button
                            type="button"
                            onClick={() => setConfirmDelete(null)}
                            className="text-xs text-muted-foreground hover:text-foreground"
                          >
                            Cancel
                          </button>
                        </span>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setConfirmDelete(user.id)}
                          className="text-xs text-red-500 hover:text-red-700"
                        >
                          Delete
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {deleteState.error && (
          <p className="mt-3 text-sm text-red-500">{deleteState.error}</p>
        )}
        {deleteState.success && (
          <p className="mt-3 text-sm text-green-600">{deleteState.success}</p>
        )}
      </div>
    </div>
  );
}
