const menuToggle = document.querySelector('.mobile-menu-toggle');
const menuBackdrop = document.querySelector('.mobile-nav-backdrop');

if (menuToggle && menuBackdrop) {
  const sidebar = document.getElementById(menuToggle.getAttribute('aria-controls'));
  const mobileQuery = window.matchMedia('(max-width: 900px)');

  function setMenuOpen(isOpen) {
    document.body.classList.toggle('mobile-nav-open', isOpen && mobileQuery.matches);
    menuToggle.setAttribute('aria-expanded', String(isOpen && mobileQuery.matches));
  }

  menuToggle.addEventListener('click', () => {
    setMenuOpen(menuToggle.getAttribute('aria-expanded') !== 'true');
    if (menuToggle.getAttribute('aria-expanded') === 'true') sidebar.focus();
  });
  menuBackdrop.addEventListener('click', () => setMenuOpen(false));
  sidebar.addEventListener('click', event => {
    if (event.target.closest('a')) setMenuOpen(false);
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && document.body.classList.contains('mobile-nav-open')) {
      setMenuOpen(false);
      menuToggle.focus();
    }
  });
  window.addEventListener('resize', () => {
    if (!mobileQuery.matches) setMenuOpen(false);
  });
}