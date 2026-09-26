"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  FaBars,
  FaHome,
  FaPills,
  FaHistory,
  FaBook,
  FaInfoCircle,
  FaCog,
  FaUser,
  FaSignOutAlt,
} from "react-icons/fa";

interface SidebarProps {
  isOpen: boolean;
  setIsOpenAction: (value: boolean) => void;
}

const mainMenu = [
  {
    label: "Dashboard",
    href: "/beranda",
    icon: FaHome,
  },
  {
    label: "DDI Checker",
    href: "/ddi",
    icon: FaPills,
  },
  {
    label: "History",
    href: "/history",
    icon: FaHistory,
  },
];

const knowledgeMenu = [
  {
    label: "Evidence Sources",
    href: "/evidence",
    icon: FaBook,
  },
];

const systemMenu = [
  {
    label: "About",
    href: "/about",
    icon: FaInfoCircle,
  },
  {
    label: "Settings",
    href: "/settings",
    icon: FaCog,
  },
];

export function Sidebar({
  isOpen,
  setIsOpenAction,
}: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {/* SIDEBAR */}
      <aside
        className={`
          fixed
          left-0
          top-0
          z-50
          flex
          h-screen
          flex-col
          border-r
          border-slate-200
          bg-white
          shadow-lg
          transition-all
          duration-300
          ease-in-out
          ${isOpen ? "w-64" : "w-20"}
        `}
      >
        {/* =========================
            LOGO / BRAND
        ========================== */}
        <div
          className={`
            flex
            h-20
            shrink-0
            items-center
            border-b
            border-slate-200
            ${isOpen ? "justify-between px-4" : "justify-center px-2"}
          `}
        >
          {/* BRAND */}
          <div className="flex items-center gap-3">
            <div
              className="
                flex
                h-11
                w-11
                shrink-0
                items-center
                justify-center
                overflow-hidden
                rounded-xl
                border
                border-blue-100
                bg-blue-50
              "
            >
              <Image
                src="/icuq.png"
                alt="RSA DDI Assistant"
                width={34}
                height={34}
                className="h-8 w-8 object-contain"
                priority
              />
            </div>

            {isOpen && (
              <div className="min-w-0">
                <h1 className="whitespace-nowrap text-sm font-bold text-slate-800">
                  RSA DDI Assistant
                </h1>

                <p className="mt-0.5 text-xs text-blue-600">
                  RSA UGM
                </p>
              </div>
            )}
          </div>

          {/* COLLAPSE BUTTON */}
          <button
            type="button"
            onClick={() => setIsOpenAction(!isOpen)}
            className="
              flex
              h-9
              w-9
              items-center
              justify-center
              rounded-lg
              text-slate-500
              transition
              duration-200
              hover:bg-blue-50
              hover:text-blue-600
            "
            title={isOpen ? "Collapse sidebar" : "Expand sidebar"}
            aria-label={
              isOpen ? "Collapse sidebar" : "Expand sidebar"
            }
          >
            <FaBars size={16} />
          </button>
        </div>

        {/* =========================
            NAVIGATION
        ========================== */}
        <nav className="flex-1 overflow-y-auto px-3 py-6">
          {/* MAIN */}
          <SidebarSection
            title="MAIN"
            items={mainMenu}
            pathname={pathname}
            isOpen={isOpen}
          />

          {/* KNOWLEDGE */}
          <SidebarSection
            title="KNOWLEDGE"
            items={knowledgeMenu}
            pathname={pathname}
            isOpen={isOpen}
          />

          {/* SYSTEM */}
          <SidebarSection
            title="SYSTEM"
            items={systemMenu}
            pathname={pathname}
            isOpen={isOpen}
          />
        </nav>

        {/* =========================
            USER PROFILE
        ========================== */}
        <div className="shrink-0 border-t border-slate-200 bg-white p-3">
          {isOpen ? (
            <div className="flex items-center gap-3 rounded-xl px-2 py-2">
              {/* USER ICON */}
              <div
                className="
                  flex
                  h-10
                  w-10
                  shrink-0
                  items-center
                  justify-center
                  rounded-full
                  bg-blue-50
                  text-blue-600
                "
              >
                <FaUser size={15} />
              </div>

              {/* USER INFO */}
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-slate-700">
                  Pharmacist
                </p>

                <p className="truncate text-xs text-slate-400">
                  RSA UGM
                </p>
              </div>

              {/* LOGOUT */}
              <button
                type="button"
                className="
                  flex
                  h-9
                  w-9
                  shrink-0
                  items-center
                  justify-center
                  rounded-lg
                  text-slate-400
                  transition
                  duration-200
                  hover:bg-blue-50
                  hover:text-blue-600
                "
                title="Logout"
                aria-label="Logout"
              >
                <FaSignOutAlt size={14} />
              </button>
            </div>
          ) : (
            <button
              type="button"
              className="
                flex
                h-10
                w-full
                items-center
                justify-center
                rounded-xl
                text-slate-400
                transition
                duration-200
                hover:bg-blue-50
                hover:text-blue-600
              "
              title="Logout"
              aria-label="Logout"
            >
              <FaSignOutAlt size={15} />
            </button>
          )}

          {/* VERSION */}
          {isOpen && (
            <p className="mt-2 px-2 text-[10px] text-slate-400">
              RSA DDI Assistant v1.0
            </p>
          )}
        </div>
      </aside>

      {/* =========================
          MOBILE OVERLAY
      ========================== */}
      {isOpen && (
        <div
          className="
            fixed
            inset-0
            z-40
            bg-slate-900/20
            backdrop-blur-[1px]
            md:hidden
          "
          onClick={() => setIsOpenAction(false)}
        />
      )}
    </>
  );
}

/* =====================================================
   SIDEBAR SECTION
===================================================== */

interface SidebarSectionProps {
  title: string;

  items: {
    label: string;
    href: string;
    icon: React.ComponentType<{ size?: number }>;
  }[];

  pathname: string;
  isOpen: boolean;
}

function SidebarSection({
  title,
  items,
  pathname,
  isOpen,
}: SidebarSectionProps) {
  return (
    <div className="mb-7">
      {/* SECTION TITLE */}
      {isOpen && (
        <p
          className="
            mb-3
            px-3
            text-[10px]
            font-bold
            uppercase
            tracking-[0.15em]
            text-slate-400
          "
        >
          {title}
        </p>
      )}

      {/* MENU ITEMS */}
      <div className="space-y-1">
        {items.map((item) => {
          const Icon = item.icon;

          const isActive =
            pathname === item.href ||
            pathname.startsWith(`${item.href}/`);

          return (
            <Link
              key={item.href}
              href={item.href}
              title={!isOpen ? item.label : undefined}
              className={`
                group
                relative
                flex
                items-center
                rounded-xl
                transition-all
                duration-200
                ${
                  isOpen
                    ? "gap-3 px-3 py-3"
                    : "justify-center px-2 py-3"
                }
                ${
                  isActive
                    ? `
                      border-r-4
                      border-blue-600
                      bg-blue-50
                      text-blue-700
                      shadow-sm
                    `
                    : `
                      text-slate-600
                      hover:bg-blue-50
                      hover:text-blue-600
                    `
                }
              `}
            >
              {/* ICON */}
              <span
                className={`
                  flex
                  shrink-0
                  items-center
                  justify-center
                  transition-colors
                  duration-200
                  ${
                    isActive
                      ? "text-blue-600"
                      : "text-slate-400 group-hover:text-blue-600"
                  }
                `}
              >
                <Icon size={18} />
              </span>

              {/* LABEL */}
              {isOpen && (
                <span
                  className={`
                    whitespace-nowrap
                    text-sm
                    ${
                      isActive
                        ? "font-semibold"
                        : "font-medium"
                    }
                  `}
                >
                  {item.label}
                </span>
              )}

              {/* ACTIVE INDICATOR */}
              {isOpen && isActive && (
                <span
                  className="
                    ml-auto
                    h-2
                    w-2
                    rounded-full
                    bg-blue-600
                  "
                />
              )}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
