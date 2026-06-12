"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { logout } from "@/components/actions/logout-action";

const NAV_LINKS = [
  { href: "/dashboard/simulation", label: "입지분석" },
  { href: "/dashboard/board", label: "게시판" },
];

export default function NavBar() {
  const pathname = usePathname();

  return (
    <nav aria-label="주 메뉴" className="fixed top-0 left-0 right-0 h-14 flex items-center justify-between px-6 bg-white border-b border-dalock-border z-50">
      <span className="text-dalock-primary font-semibold text-xl">다락</span>
      <div className="flex items-center gap-1">
        {NAV_LINKS.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={
              pathname === link.href || pathname.startsWith(link.href + "/")
                ? "bg-dalock-primary text-white rounded-md px-3 py-1.5 text-sm font-medium"
                : "text-dalock-text2 hover:text-dalock-text1 rounded-md px-3 py-1.5 text-sm"
            }
          >
            {link.label}
          </Link>
        ))}
        <form action={logout} className="ml-4">
          <button
            type="submit"
            className="text-sm text-dalock-text2 hover:text-dalock-text1 border border-dalock-border rounded-md px-3 py-1.5"
          >
            로그아웃
          </button>
        </form>
      </div>
    </nav>
  );
}
