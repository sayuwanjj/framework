// Текущий год в подвале страницы.
const yearElement = document.getElementById("current-year");

if (yearElement) {
    yearElement.textContent = new Date().getFullYear();
}

// Подсветка пункта меню, соответствующего открытому разделу.
// Выбирается ссылка с самым длинным совпадающим адресом, чтобы
// на странице /layouts/statistics/ подсвечивалась «Статистика»,
// а не «Макеты».
const currentPath = window.location.pathname;
let activeLink = null;

document.querySelectorAll(".site-nav .nav-link").forEach((link) => {
    const linkPath = link.getAttribute("href");
    const isHome = linkPath === "/";
    const matches = isHome
        ? currentPath === "/"
        : currentPath.startsWith(linkPath);
    if (matches && (!activeLink || linkPath.length > activeLink.getAttribute("href").length)) {
        activeLink = link;
    }
});

if (activeLink) {
    activeLink.classList.add("active");
}
