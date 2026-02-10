// Cookie Consent Management (KVKK/GDPR)
(function() {
    const COOKIE_NAME = 'ocrchestra_cookie_consent';
    const COOKIE_EXPIRY_DAYS = 365;

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    function setCookie(name, value, days) {
        const d = new Date();
        d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
        const expires = `expires=${d.toUTCString()}`;
        document.cookie = `${name}=${value};${expires};path=/;samesite=lax`;
    }

    function getConsent() {
        const consentCookie = getCookie(COOKIE_NAME);
        if (!consentCookie) return null;
        try {
            return JSON.parse(decodeURIComponent(consentCookie));
        } catch (e) {
            return null;
        }
    }

    function saveConsent(preferences) {
        const consentData = {
            necessary: true,
            preferences: preferences.preferences || false,
            analytics: preferences.analytics || false,
            marketing: preferences.marketing || false,
            timestamp: new Date().toISOString()
        };
        setCookie(COOKIE_NAME, encodeURIComponent(JSON.stringify(consentData)), COOKIE_EXPIRY_DAYS);
        applyConsent(consentData);
        hideBanner();
    }

    function applyConsent(consent) {
        // Apply actual cookie policies based on consent
        if (consent.analytics) {
            console.log('Analytics cookies enabled');
            // TODO: Enable Google Analytics or other analytics
        } else {
            console.log('Analytics cookies disabled');
        }

        if (consent.marketing) {
            console.log('Marketing cookies enabled');
        } else {
            console.log('Marketing cookies disabled');
        }

        // Store preference for server-side consent tracking
        if (window.csrfToken) {
            fetch('/corpus/gdpr/consent/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': window.csrfToken
                },
                body: new URLSearchParams({
                    'analytics': consent.analytics ? 'true' : 'false',
                    'marketing': consent.marketing ? 'true' : 'false'
                })
            }).catch(err => console.error('Failed to save consents:', err));
        }
    }

    function showBanner() {
        document.getElementById('cookieConsent').style.display = 'block';
    }

    function hideBanner() {
        document.getElementById('cookieConsent').style.display = 'none';
    }

    function showModal() {
        document.getElementById('cookieModal').style.display = 'flex';
        const consent = getConsent();
        if (consent) {
            document.getElementById('cookiePreferences').checked = consent.preferences;
            document.getElementById('cookieAnalytics').checked = consent.analytics;
            document.getElementById('cookieMarketing').checked = consent.marketing;
        }
    }

    function hideModal() {
        document.getElementById('cookieModal').style.display = 'none';
    }

    // Initialize event listeners
    function init() {
        const acceptAllBtn = document.getElementById('cookieAcceptAll');
        const rejectAllBtn = document.getElementById('cookieRejectAll');
        const customizeBtn = document.getElementById('cookieCustomize');
        const modalClose = document.getElementById('cookieModalClose');
        const modalCancel = document.getElementById('cookieModalCancel');
        const modalOverlay = document.getElementById('cookieModalOverlay');
        const savePrefsBtn = document.getElementById('cookieSavePreferences');

        if (acceptAllBtn) {
            acceptAllBtn.addEventListener('click', function() {
                saveConsent({ preferences: true, analytics: true, marketing: true });
            });
        }

        if (rejectAllBtn) {
            rejectAllBtn.addEventListener('click', function() {
                saveConsent({ preferences: false, analytics: false, marketing: false });
            });
        }

        if (customizeBtn) customizeBtn.addEventListener('click', showModal);
        if (modalClose) modalClose.addEventListener('click', hideModal);
        if (modalCancel) modalCancel.addEventListener('click', hideModal);
        if (modalOverlay) modalOverlay.addEventListener('click', hideModal);

        if (savePrefsBtn) {
            savePrefsBtn.addEventListener('click', function() {
                saveConsent({
                    preferences: document.getElementById('cookiePreferences').checked,
                    analytics: document.getElementById('cookieAnalytics').checked,
                    marketing: document.getElementById('cookieMarketing').checked
                });
                hideModal();
            });
        }

        // Check consent on page load
        const consent = getConsent();
        if (!consent) {
            showBanner();
        } else {
            applyConsent(consent);
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose function for preference page
    window.showCookiePreferences = showModal;
})();
