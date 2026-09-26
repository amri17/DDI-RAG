"use client";

import { usePathname } from "next/navigation";
import { useState } from "react";

import Navbar from "@/app/navbar";
import { Sidebar } from "@/app/sidebar";

export default function AppShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(true);
  const pathname = usePathname();

  const isAuthPage =
    pathname === "/login" ||
    pathname === "/register";

  return (
    <>
      {isAuthPage ? (
        <>{children}</>
      ) : (
        <>
          <div
            className={`fixed top-0 right-0 z-40 transition-all duration-300 ${
              isOpen ? "left-64" : "left-20"
            }`}
          >
            <Navbar />
          </div>

          <Sidebar
            isOpen={isOpen}
            setIsOpenAction={setIsOpen}
          />

          <main
            className={`min-h-screen pt-20 transition-all duration-300 ${
              isOpen ? "ml-64" : "ml-20"
            }`}
          >
            {children}
          </main>
        </>
      )}
    </>
  );
}
