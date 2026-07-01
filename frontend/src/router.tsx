import type { AnchorHTMLAttributes, ReactNode } from "react";

export function Link({ href, children, ...props }: AnchorHTMLAttributes<HTMLAnchorElement> & { children: ReactNode }) {
  return (
    <a
      href={href}
      onClick={(event) => {
        if (!href || href.startsWith("http") || event.metaKey || event.ctrlKey) return;
        event.preventDefault();
        window.history.pushState({}, "", href);
        window.dispatchEvent(new PopStateEvent("popstate"));
      }}
      {...props}
    >
      {children}
    </a>
  );
}
