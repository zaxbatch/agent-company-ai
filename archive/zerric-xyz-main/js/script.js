// =============================================================
// NAVIGATION
// =============================================================
document.getElementById('hamburger').addEventListener('click', function() {
    document.getElementById('navLinks').classList.toggle('open');
    document.getElementById('navAuth').classList.toggle('open');
    this.classList.toggle('active');
});

// Close mobile menu on link click
document.querySelectorAll('.nav-links a, .nav-auth a').forEach(link => {
    link.addEventListener('click', () => {
        document.getElementById('navLinks').classList.remove('open');
        document.getElementById('navAuth').classList.remove('open');
        document.getElementById('hamburger').classList.remove('active');
    });
});

// Navbar scroll effect
window.addEventListener('scroll', () => {
    const navbar = document.getElementById('navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// =============================================================
// TEASER FUNCTION (All buttons link here)
// =============================================================
function showTeaser(featureName) {
    alert(
        '🚀 Coming Soon!\n\n' +
        'The "' + featureName + '" feature is under active development.\n\n' +
        'We\'re building something amazing. Stay tuned!\n\n' +
        '— The ZDOT Team\n' +
        'zdotconnect@gmail.com'
    );
}

// =============================================================
// LEAD MAGNET – PDF Download + HubSpot capture (server-side via lead.php)
const leadForm = document.getElementById('leadMagnetForm');

if (leadForm) {
    leadForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const name = document.getElementById('leadName').value.trim();
        const email = document.getElementById('leadEmail').value.trim();

        if (!name || !email) {
            alert('Please fill in both fields.');
            return;
        }

        // 1) Send lead to HubSpot via server-side lead.php (token never exposed)
        fetch('lead.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, email: email, source: 'zdotllc-checklist' })
        }).catch(function() { /* offline fallback below */ });

        // 2) Local backup (works even if CRM call fails)
        try {
            const leads = JSON.parse(localStorage.getItem('zdot_leads') || '[]');
            leads.push({ name: name, email: email, date: new Date().toISOString(), source: 'checklist' });
            localStorage.setItem('zdot_leads', JSON.stringify(leads));
        } catch (err) {}

        // 3) Show success + trigger PDF download
        alert(
            '✅ Thanks ' + name + '!\n\n' +
            'Your "Zero-to-Launch Business Checklist" is downloading now.\n\n' +
            'Check your downloads folder for:\n' +
            'zero-to-launch-checklist.pdf\n\n' +
            'We\'ll also send a copy to:\n' +
            email + '\n\n' +
            '— The ZDOT Team\n' +
            'zdotconnect@gmail.com'
        );

        const link = document.createElement('a');
        link.href = 'resources/zero-to-launch-checklist.pdf';
        link.download = 'zero-to-launch-checklist.pdf';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        leadForm.reset();
    });
}

// COOKIE CONSENT
// =============================================================
const cookieConsent = document.getElementById('cookieConsent');

// Check if user already made a choice
if (!localStorage.getItem('swarm_cookie_consent')) {
    // Show banner after 1 second
    setTimeout(() => {
        cookieConsent.classList.add('visible');
    }, 1000);
}

const cookieAccept = document.getElementById('cookieAccept');
const cookieDecline = document.getElementById('cookieDecline');

if (cookieAccept) {
    cookieAccept.addEventListener('click', function() {
        localStorage.setItem('swarm_cookie_consent', 'accepted');
        cookieConsent.classList.remove('visible');
        console.log('🍪 Cookie consent accepted.');
    });
}

if (cookieDecline) {
    cookieDecline.addEventListener('click', function() {
        localStorage.setItem('swarm_cookie_consent', 'declined');
        cookieConsent.classList.remove('visible');
        console.log('🍪 Cookie consent declined.');
    });
}

// =============================================================
// CONSOLE LOG (Branding)
// =============================================================
console.log('%c🐝 ZDOT', 'font-size:24px;font-weight:bold;color:#1E1B4B;');
console.log('%cBusiness Solutions Company', 'font-size:14px;color:#0EA5E9;');
console.log('%c🚀 SWARM – The Business Ecosystem', 'font-size:14px;color:#8B5CF6;');
console.log('📦 Products: Bizzy Bee CRM (beta) | Social Butterfly (beta)');
console.log('📧 Contact: zdotconnect@gmail.com');
console.log('🔗 ' + window.location.href);