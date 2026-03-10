import { cookies } from "next/headers";
import { fetchAdminUsers } from "./actions";
import { AdminLoginForm } from "./admin-login-form";
import { AdminPanel } from "./admin-panel";

export const dynamic = "force-dynamic";

export default async function AdminPage() {
  const cookieStore = await cookies();
  const adminKey = cookieStore.get("xmrcheckout_admin_key")?.value;

  if (!adminKey) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="w-full max-w-md">
          <h1 className="text-2xl font-bold mb-6 text-center">Admin</h1>
          <AdminLoginForm />
        </div>
      </div>
    );
  }

  const users = await fetchAdminUsers();

  if (users === null) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="w-full max-w-md">
          <h1 className="text-2xl font-bold mb-6 text-center">Admin</h1>
          <p className="text-center text-red-500 mb-4">Invalid or expired admin key.</p>
          <AdminLoginForm />
        </div>
      </div>
    );
  }

  return <AdminPanel users={users} />;
}
