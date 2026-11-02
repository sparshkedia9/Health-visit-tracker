// Small helpers shared by every page. No frameworks needed.

// 1. Turn <i data-lucide="icon-name"> tags into SVG icons (Lucide is loaded in base.html).
if (window.lucide) {
  lucide.createIcons();
}

// 2. Collapse / expand the sidebar.
//    We add or remove the "sidebar-collapsed" class on the <html> tag; style.css does the rest.
//    The choice is saved so the sidebar stays the same when you open another page.
var sidebarToggle = document.getElementById("sidebar-toggle");
if (sidebarToggle) {
  sidebarToggle.addEventListener("click", function () {
    var isCollapsed = document.documentElement.classList.toggle("sidebar-collapsed");
    try {
      localStorage.setItem("sidebarCollapsed", isCollapsed ? "yes" : "no");
    } catch (error) {}
  });
}

// 3. Dashboard greeting: "Good Morning / Afternoon / Evening" based on the user's clock.
var greeting = document.getElementById("greeting");
if (greeting) {
  var hour = new Date().getHours();
  var partOfDay = hour < 12 ? "Morning" : hour < 17 ? "Afternoon" : "Evening";
  greeting.textContent = "Good " + partOfDay;
}

// 4. Today's date under the dashboard heading, e.g. "Tuesday, 3 November 2026".
var todayLabel = document.getElementById("today-label");
if (todayLabel) {
  todayLabel.textContent = new Date().toLocaleDateString(undefined, {
    weekday: "long", day: "numeric", month: "long", year: "numeric"
  });
}
