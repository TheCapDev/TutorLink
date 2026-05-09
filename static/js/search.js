/* ============================================================
   TutorLink — Search & Filter JS
   ============================================================ */

(function () {
    'use strict';

    const form = document.querySelector('#search-filters');
    if (!form) return;

    // Auto-submit on filter change for instant feedback (optional)
    form.querySelectorAll('input[type="checkbox"], select').forEach(el => {
        el.addEventListener('change', () => {
            // Could auto-submit here. For now, leave manual to keep server load reasonable.
        });
    });

    // Reset all filters
    const resetBtn = form.querySelector('[data-reset]');
    if (resetBtn) {
        resetBtn.addEventListener('click', (e) => {
            e.preventDefault();
            form.querySelectorAll('input[type="text"], input[type="number"]').forEach(i => i.value = '');
            form.querySelectorAll('input[type="checkbox"]').forEach(i => i.checked = false);
            form.querySelectorAll('select').forEach(s => { s.selectedIndex = 0; });
            form.submit();
        });
    }

})();
