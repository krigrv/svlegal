document.addEventListener('DOMContentLoaded', () => {

    // ── 1. Header shrink on scroll ──────────────────────────────────────────
    const header = document.querySelector('.site-header');
    if (header) {
        window.addEventListener('scroll', () => {
            header.classList.toggle('is-scrolled', window.scrollY > 60);
        }, { passive: true });
    }

    // ── 1b. Mobile nav toggle ────────────────────────────────────────────────
    const navToggle = document.querySelector('[data-nav-toggle]');
    const siteNav = document.querySelector('[data-nav]');
    if (navToggle && siteNav) {
        navToggle.addEventListener('click', () => {
            const isOpen = document.body.classList.toggle('nav-open');
            navToggle.setAttribute('aria-expanded', isOpen);
            // Position nav right below the header
            if (isOpen && header) {
                siteNav.style.top = header.offsetHeight + 'px';
            }
        });

        // Close nav when a link is clicked
        siteNav.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                document.body.classList.remove('nav-open');
                navToggle.setAttribute('aria-expanded', 'false');
            });
        });
    }

    // ── 2. Floating WhatsApp button ─────────────────────────────────────────
    const wa = document.createElement('a');
    wa.href = 'https://wa.me/919611344455';
    wa.target = '_blank';
    wa.rel = 'noopener noreferrer';
    wa.className = 'whatsapp-float';
    wa.setAttribute('aria-label', 'Chat on WhatsApp');
    wa.title = 'Chat on WhatsApp';
    wa.innerHTML = '<i class="fa fa-whatsapp"></i>';
    document.body.appendChild(wa);

    // ── 3. Back-to-top button ───────────────────────────────────────────────
    const btt = document.createElement('button');
    btt.className = 'back-to-top';
    btt.setAttribute('aria-label', 'Back to top');
    btt.innerHTML = '<i class="fa fa-chevron-up"></i>';
    document.body.appendChild(btt);

    window.addEventListener('scroll', () => {
        btt.classList.toggle('is-visible', window.scrollY > 300);
    }, { passive: true });

    btt.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

    // ── 4. Smooth page transition (fade-in on load, fade-out on nav) ────────
    const overlay = document.createElement('div');
    overlay.className = 'page-transition-overlay';
    document.body.appendChild(overlay);

    // Fade page in on load
    overlay.style.opacity = '1';
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            overlay.style.transition = 'opacity 0.4s ease';
            overlay.style.opacity = '0';
        });
    });

    // Fade page out on internal link click
    document.querySelectorAll('a[href]').forEach(link => {
        const href = link.getAttribute('href');
        if (!href || href.startsWith('#') || href.startsWith('mailto:') ||
            href.startsWith('tel:') || href.startsWith('http') ||
            link.target === '_blank') return;
        link.addEventListener('click', e => {
            e.preventDefault();
            overlay.style.opacity = '1';
            setTimeout(() => { window.location.href = href; }, 350);
        });
    });

    // ── 5. Animated counter numbers ─────────────────────────────────────────
    const counters = document.querySelectorAll('.stat-num');
    if (counters.length > 0) {
        const countObserver = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (!entry.isIntersecting) return;
                const el = entry.target;
                if (!el.dataset.target) {
                    countObserver.unobserve(el);
                    return;
                }
                const target = parseInt(el.dataset.target, 10);
                const suffix = el.dataset.suffix || '';
                let current = 0;
                const step = Math.max(1, Math.ceil(target / 60));
                const interval = setInterval(() => {
                    current = Math.min(current + step, target);
                    el.textContent = current + suffix;
                    if (current >= target) clearInterval(interval);
                }, 25);
                countObserver.unobserve(el);
            });
        }, { threshold: 0.5 });
        counters.forEach(c => countObserver.observe(c));
    }

});
