/*  ──────────────────────────────────────────────────────────────
    NextGen AutoCare — Global Theme Toggle
    - Applies saved theme on EVERY page (no button shown)
    - The toggle button lives ONLY in index.html navbar
    ────────────────────────────────────────────────────────────── */

(function () {
    'use strict';

    /* ── Apply saved theme immediately BEFORE first paint (no flash) ── */
    const saved = localStorage.getItem('ng-theme') || 'dark';
    applyTheme(saved);

    /* ── Wait for DOM to wire up the navbar button (index.html only) ── */
    document.addEventListener('DOMContentLoaded', function () {
        updateNavBtn();
        initScrollAnimations();
    });

    /* ── Scroll Reveal System ── */
    function initScrollAnimations() {
        const observerOptions = {
            threshold: 0.15,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                }
            });
        }, observerOptions);

        // Targets: any element with .reveal or .stagger class
        document.querySelectorAll('.reveal, .stagger').forEach(el => observer.observe(el));
    }

    /* ── Core: set data-theme on <html> ── */
    function applyTheme(theme) {
        if (theme === 'light') {
            document.documentElement.setAttribute('data-theme', 'light');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
        updateNavBtn();
    }

    /* ── Update the navbar toggle button icon (index.html only) ── */
    function updateNavBtn() {
        const icon = document.getElementById('theme-icon');
        if (!icon) return; // not on index.html — skip silently

        const current = localStorage.getItem('ng-theme') || 'dark';
        if (current === 'light') {
            // Switch icon to sun
            icon.setAttribute('data-lucide', 'sun');
        } else {
            // Switch icon to moon
            icon.setAttribute('data-lucide', 'moon');
        }
        // Re-render lucide icon if library is loaded
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    /* ── Toggle handler — called by the button in index.html ── */
    window.toggleTheme = function () {
        const current = localStorage.getItem('ng-theme') || 'dark';
        const next = current === 'dark' ? 'light' : 'dark';
        localStorage.setItem('ng-theme', next);
        applyTheme(next);

        // Spin the button for feedback
        const btn = document.getElementById('theme-toggle');
        if (btn) {
            btn.style.transform = 'rotate(360deg) scale(1.2)';
            btn.style.transition = 'transform 0.4s cubic-bezier(0.175,0.885,0.32,1.275)';
            setTimeout(function () {
                btn.style.transform = '';
                btn.style.transition = '';
            }, 420);
        }
    };

})();
