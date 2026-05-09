/* ============================================================
   TutorLink — Main JS
   Lightweight interactions, no framework
   ============================================================ */

(function () {
    'use strict';

    // -------- Mobile nav toggle --------
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', () => {
            navLinks.classList.toggle('open');
            const expanded = navLinks.classList.contains('open');
            navToggle.setAttribute('aria-expanded', String(expanded));
        });
    }

    // -------- Auto-dismiss alerts --------
    document.querySelectorAll('.alert[data-dismiss]').forEach(el => {
        const delay = parseInt(el.dataset.dismiss, 10) || 5000;
        setTimeout(() => {
            el.style.transition = 'opacity 0.3s ease';
            el.style.opacity = '0';
            setTimeout(() => el.remove(), 300);
        }, delay);
    });

    // -------- Confirm dialogs on dangerous actions --------
    document.querySelectorAll('[data-confirm]').forEach(el => {
        el.addEventListener('click', (e) => {
            const msg = el.dataset.confirm;
            if (!window.confirm(msg)) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    });

    // -------- Password feedback (strength + match + short-hint) --------
    const passwordInput = document.querySelector('#password');

    function classifyPwd(pwd) {
        if (!pwd) return { level: 0, label: '', tip: '' };
        if (pwd.length < 8) {
            return { level: 1, label: 'Too short', tip: 'Use at least 8 characters' };
        }
        let classes = 0;
        if (/[a-z]/.test(pwd)) classes++;
        if (/[A-Z]/.test(pwd)) classes++;
        if (/[0-9]/.test(pwd)) classes++;
        if (/[^A-Za-z0-9]/.test(pwd)) classes++;
        if (pwd.length >= 12 && classes >= 3) {
            return { level: 4, label: 'Strong', tip: '' };
        }
        if (pwd.length >= 10 && classes >= 2) {
            return { level: 3, label: 'Good', tip: 'Add a symbol or extra length for "Strong"' };
        }
        if (classes >= 2) {
            return { level: 2, label: 'Fair', tip: 'Try a longer password or add symbols' };
        }
        return { level: 2, label: 'Weak', tip: 'Mix in numbers, symbols, or uppercase' };
    }

    const strengthEl = document.querySelector('[data-pwd-strength]');
    if (strengthEl && passwordInput) {
        const labelEl = strengthEl.querySelector('[data-pwd-strength-text]');
        const tipEl = strengthEl.querySelector('[data-pwd-strength-tip]');
        const defaultTip = (tipEl && tipEl.dataset.default) || '';
        const updateStrength = () => {
            const result = classifyPwd(passwordInput.value);
            strengthEl.dataset.level = String(result.level);
            if (labelEl) labelEl.textContent = result.label;
            if (tipEl) tipEl.textContent = result.level === 0 ? defaultTip : result.tip;
            passwordInput.classList.toggle('is-invalid', result.level === 1);
            passwordInput.classList.toggle('is-valid', result.level === 4);
        };
        passwordInput.addEventListener('input', updateStrength);
        updateStrength();
    }

    const matchEl = document.querySelector('[data-pwd-match]');
    const confirmPwdInput = document.querySelector('#password_confirm');
    if (matchEl && passwordInput && confirmPwdInput) {
        const matchText = matchEl.querySelector('[data-pwd-match-text]');
        const matchIcon = matchEl.querySelector('[data-pwd-match-icon]');
        const updateMatch = () => {
            if (!confirmPwdInput.value) {
                matchEl.classList.remove('show', 'is-ok', 'is-bad');
                confirmPwdInput.setCustomValidity('');
                confirmPwdInput.classList.remove('is-invalid', 'is-valid');
                return;
            }
            const ok = confirmPwdInput.value === passwordInput.value;
            matchEl.classList.add('show');
            matchEl.classList.toggle('is-ok', ok);
            matchEl.classList.toggle('is-bad', !ok);
            if (matchText) matchText.textContent = ok ? 'Passwords match' : "Passwords don't match";
            if (matchIcon) matchIcon.textContent = ok ? 'OK' : '!';
            confirmPwdInput.setCustomValidity(ok ? '' : 'Passwords do not match');
            confirmPwdInput.classList.toggle('is-invalid', !ok);
            confirmPwdInput.classList.toggle('is-valid', ok);
        };
        passwordInput.addEventListener('input', updateMatch);
        confirmPwdInput.addEventListener('input', updateMatch);
    }

    const shortHintEl = document.querySelector('[data-pwd-short-hint]');
    if (shortHintEl && passwordInput) {
        const updateShort = () => {
            const v = passwordInput.value;
            const isShort = v.length > 0 && v.length < 8;
            shortHintEl.classList.toggle('show', isShort);
            passwordInput.classList.toggle('is-invalid', isShort);
        };
        passwordInput.addEventListener('input', updateShort);
        updateShort();
    }

    // -------- Phone feedback --------
    function normalizePhone(raw) {
        let digits = raw.replace(/\D/g, '');
        if (digits.length === 11 && digits.startsWith('1')) {
            digits = digits.slice(1);
        }
        if (digits.length !== 10) return null;
        return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
    }

    document.querySelectorAll('[data-phone-input]').forEach(input => {
        const hint = input.closest('.field')?.querySelector('[data-phone-hint]');
        const hadServerError = input.classList.contains('is-invalid');
        const updatePhone = () => {
            const raw = input.value.trim();
            const formatted = normalizePhone(raw);
            const isInvalid = (raw.length > 0 && !formatted) || (hadServerError && raw.length === 0);
            if (hint) hint.classList.toggle('show', isInvalid);
            input.classList.toggle('is-invalid', isInvalid);
            input.classList.toggle('is-valid', raw.length > 0 && !!formatted);
        };
        input.addEventListener('input', updatePhone);
        input.addEventListener('blur', () => {
            const formatted = normalizePhone(input.value.trim());
            if (formatted) input.value = formatted;
            updatePhone();
        });
        updatePhone();
    });

    // -------- Tabs --------
    document.querySelectorAll('[data-tabs]').forEach(group => {
        const tabs = group.querySelectorAll('.tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                const target = tab.dataset.target;
                if (target) {
                    document.querySelectorAll(`[data-tab-content]`).forEach(p => {
                        p.style.display = p.dataset.tabContent === target ? '' : 'none';
                    });
                }
            });
        });
    });

    // -------- Booking duration → price preview --------
    const durationInput = document.querySelector('[data-rate-input]');
    const ratePerHour = parseFloat(document.querySelector('[data-rate]')?.dataset.rate || '0');
    const totalEl = document.querySelector('[data-total]');
    if (durationInput && totalEl && ratePerHour) {
        const update = () => {
            const minutes = parseInt(durationInput.value, 10) || 0;
            const total = (ratePerHour * minutes) / 60;
            totalEl.textContent = '$' + total.toFixed(2);
        };
        durationInput.addEventListener('input', update);
        update();
    }

    // -------- Character counter for textareas --------
    document.querySelectorAll('textarea[maxlength]').forEach(ta => {
        const max = parseInt(ta.getAttribute('maxlength'), 10);
        const counter = document.createElement('div');
        counter.className = 'help text-right';
        counter.style.marginTop = '4px';
        ta.parentNode.insertBefore(counter, ta.nextSibling);
        const update = () => {
            counter.textContent = `${ta.value.length} / ${max}`;
        };
        ta.addEventListener('input', update);
        update();
    });

    // -------- Auto-scroll thread to latest message --------
    const thread = document.querySelector('.thread');
    if (thread) thread.scrollTop = thread.scrollHeight;

})();
