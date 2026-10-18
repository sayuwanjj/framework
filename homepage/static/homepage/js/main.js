// Текущий год в подвале страницы.
const yearElement = document.getElementById("current-year");

if (yearElement) {
    yearElement.textContent = new Date().getFullYear();
}

// Подсветка пункта меню, соответствующего открытому разделу.
const currentPath = window.location.pathname;

document.querySelectorAll(".site-nav .nav-link").forEach((link) => {
    const linkPath = link.getAttribute("href");
    const isHome = linkPath === "/";
    if (isHome ? currentPath === "/" : currentPath.startsWith(linkPath)) {
        link.classList.add("active");
    }
});
