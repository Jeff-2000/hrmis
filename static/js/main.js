document.addEventListener('DOMContentLoaded', () => {
    // Mobile menu toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('sidebar');
    const sidebarBackdrop = document.getElementById('sidebarBackdrop');

    mobileMenuBtn.addEventListener('click', () => {
        sidebar.classList.toggle('active');
        sidebarBackdrop.classList.toggle('hidden');
    });

    sidebarBackdrop.addEventListener('click', () => {
        sidebar.classList.remove('active');
        sidebarBackdrop.classList.add('hidden');
    });

    // User dropdown toggle
    const userBtn = document.getElementById('userBtn');
    const dropdownMenu = document.getElementById('dropdownMenu');

    userBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdownMenu.classList.toggle('active');
        dropdownMenu.classList.toggle('opacity-0');
        dropdownMenu.classList.toggle('invisible');
        dropdownMenu.classList.toggle('-translate-y-2');
        userBtn.setAttribute('aria-expanded', dropdownMenu.classList.contains('active'));
    });

    document.addEventListener('click', () => {
        dropdownMenu.classList.remove('active');
        dropdownMenu.classList.add('opacity-0', 'invisible', '-translate-y-2');
        userBtn.setAttribute('aria-expanded', 'false');
    });

    dropdownMenu.addEventListener('click', (e) => {
        e.stopPropagation();
    });

    // Submenu toggle with event delegation
    sidebar.addEventListener('click', (e) => {
        const submenuToggle = e.target.closest('.has-submenu > a');
        if (submenuToggle) {
            e.preventDefault();
            const parent = submenuToggle.parentElement;
            const isExpanded = parent.classList.contains('expanded');
            document.querySelectorAll('.has-submenu.expanded').forEach(item => {
                if (item !== parent) {
                    item.classList.remove('expanded');
                    item.querySelector('.submenu').classList.add('hidden');
                }
            });
            parent.classList.toggle('expanded');
            parent.querySelector('.submenu').classList.toggle('hidden', isExpanded);
        }
    });

    // Responsive adjustments
    window.addEventListener('resize', () => {
        if (window.innerWidth > 1024) {
            sidebar.classList.remove('active');
            sidebarBackdrop.classList.add('hidden');
        }
    });
});