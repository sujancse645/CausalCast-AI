import type { ReactNode } from "react";
import { Header } from "./header";
import { Sidebar } from "./sidebar";
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <>
      <Sidebar />
      <div className="main-shell min-h-screen md:ml-64">
        <Header />
        <main className="p-5 md:p-8">{children}</main>
      </div>
    </>
  );
}
