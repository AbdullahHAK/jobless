// Shared by every page (no build step in this project, so this is a plain
// extra <script> tag rather than an import). Handles the collapsible left
// sidebar: collapsed by default on mobile (where it overlays content behind
// a backdrop), open by default on desktop, with the desktop preference
// remembered in localStorage.
const SIDEBAR_COLLAPSED_KEY = "jobless:sidebar-collapsed";

function initSidebar() {
  const toggle = document.getElementById("sidebar-toggle");
  const backdrop = document.getElementById("sidebar-backdrop");
  const isMobile = () => window.matchMedia("(max-width: 768px)").matches;

  let collapsed;
  try {
    collapsed = isMobile() ? true : localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "true";
  } catch {
    collapsed = isMobile();
  }
  document.body.classList.toggle("sidebar-collapsed", collapsed);

  function setCollapsed(value) {
    collapsed = value;
    document.body.classList.toggle("sidebar-collapsed", collapsed);
    if (isMobile()) return;
    try {
      localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(collapsed));
    } catch {
      // Couldn't persist (private mode, storage full, etc.) - the toggle
      // still works for this page view, it just won't survive a reload.
    }
  }

  toggle?.addEventListener("click", () => setCollapsed(!collapsed));
  backdrop?.addEventListener("click", () => setCollapsed(true));
}

initSidebar();
