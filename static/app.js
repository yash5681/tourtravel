// ============================================================
// Delux Tour & Travel — Full Stack Frontend Engine (Django API)
// Handles: Customer Auth, Contact, Plan-a-Trip, Dynamic Packages,
// Package Itinerary Modal, Live Search, My-Bookings & Support.
// ============================================================

const API = {
  register: '/api/auth/register',
  login: '/api/auth/login',
  logout: '/api/auth/logout',
  me: '/api/auth/me',
  contact: '/api/contact',
  plan: '/api/plan',
  packages: '/api/packages',
  bookings: '/api/bookings',
  upiCreateBooking: '/api/upi/create-booking',
  upiSubmitUtr: '/api/upi/submit-utr',
  myBookings: '/api/my-bookings'
};

let allLoadedPackages = [];

// ---------- Toast Notification System ----------
function showToast(message, type = 'info') {
  let container = document.getElementById('deluxToastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'deluxToastContainer';
    container.className = 'delux-toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `delux-toast ${type}`;
  toast.innerHTML = `<span>${message}</span><span style="cursor:pointer;opacity:.6">&times;</span>`;

  toast.querySelector('span:last-child').onclick = () => toast.remove();
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity .3s, transform .3s';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(40px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ---------- API Helpers ----------
async function postJson(url, data) {
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify(data)
    });
    let body = {};
    try { body = await res.json(); } catch { /* no body */ }
    return { ok: res.ok, status: res.status, body };
  } catch (err) {
    return { ok: false, status: 0, body: { message: 'Network error. Please try again.' } };
  }
}

// ---------- Global image fallback ----------
function attachImageFallback() {
  document.querySelectorAll('img').forEach(img => {
    if (img.dataset.fallbackAttached) return;
    img.dataset.fallbackAttached = '1';
    img.loading = img.loading || 'lazy';
    const placeholder = 'https://placehold.co/900x600/17201d/ffffff?text=Delux+Tour+%26+Travel';
    img.addEventListener('error', function onErr() {
      this.removeEventListener('error', onErr);
      this.src = placeholder;
    });
    if (img.complete && img.naturalWidth === 0 && img.src) {
      img.src = placeholder;
    }
  });
}

// ---------- Interactive Quick WhatsApp Concierge Widget ----------
const WA_PHONE = '919023433407';

window.toggleDeluxWhatsApp = function() {
  const chatBox = document.getElementById('waChatBox');
  if (chatBox) {
    chatBox.classList.toggle('open');
    if (chatBox.classList.contains('open')) {
      const inputField = document.getElementById('waCustomInput');
      if (inputField) inputField.focus();
    }
  }
};

window.closeDeluxWhatsApp = function() {
  const chatBox = document.getElementById('waChatBox');
  if (chatBox) chatBox.classList.remove('open');
};

window.startWhatsApp = function(message) {
  const text = encodeURIComponent(message || 'Hello Delux Tour & Travel! I would like to inquire about your holiday packages.');
  const whatsappUrl = `https://wa.me/${WA_PHONE}?text=${text}`;
  window.open(whatsappUrl, '_blank');
};

window.sendWhatsAppCustom = function() {
  const inputField = document.getElementById('waCustomInput');
  const msg = inputField ? inputField.value.trim() : '';
  if (msg) {
    window.startWhatsApp(msg);
    inputField.value = '';
    window.closeDeluxWhatsApp();
  }
};

function injectWhatsAppWidget() {
  if (document.getElementById('waWidgetContainer')) return;

  const container = document.createElement('div');
  container.id = 'waWidgetContainer';
  container.innerHTML = `
    <!-- Floating Bubble -->
    <a class="wa-widget-bubble" id="waToggleBtn" title="Chat with Delux Travel Concierge on WhatsApp" href="https://wa.me/${WA_PHONE}?text=Hello%20Delux%20Tour%20%26%20Travel!%20I%20would%20like%20to%20inquire%20about%20your%20holiday%20packages." target="_blank" onclick="event.preventDefault(); window.toggleDeluxWhatsApp();">
      <span class="wa-pulse-dot"></span>
      <svg viewBox="0 0 24 24"><path d="M12.04 2c-5.46 0-9.91 4.45-9.91 9.91 0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21 5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.816 9.816 0 0 0 12.04 2m.01 1.67c2.2 0 4.26.86 5.82 2.42a8.225 8.225 0 0 1 2.41 5.83c0 4.54-3.7 8.24-8.24 8.24-1.48 0-2.93-.4-4.2-1.15l-.3-.18-3.12.82.83-3.04-.2-.31a8.196 8.196 0 0 1-1.26-4.38c0-4.54 3.7-8.24 8.24-8.24m4.52 11.66c-.25-.13-1.47-.72-1.7-.81-.23-.08-.39-.13-.56.13-.17.25-.64.81-.79.97-.14.17-.29.19-.54.06-.25-.13-1.06-.39-2.02-1.25-.75-.67-1.26-1.5-1.4-1.75-.15-.25-.02-.39.11-.51.11-.11.25-.29.38-.44.13-.14.17-.25.25-.42.08-.17.04-.31-.02-.44-.06-.13-.56-1.35-.77-1.85-.2-.49-.41-.42-.56-.43h-.48c-.17 0-.44.06-.67.31-.23.25-.88.86-.88 2.1 0 1.24.9 2.44 1.03 2.61.13.17 1.77 2.7 4.29 3.79.6.26 1.07.41 1.43.53.6.19 1.15.16 1.58.1.48-.07 1.47-.6 1.68-1.18.21-.58.21-1.07.15-1.18-.07-.1-.23-.17-.48-.29z"/></svg>
      <span>WhatsApp Chat</span>
    </a>

    <!-- WhatsApp Chat Dialog Box -->
    <div class="wa-chat-box" id="waChatBox">
      <div class="wa-chat-header">
        <div class="wa-chat-header-info">
          <img src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=150&q=80" alt="Concierge" class="wa-avatar">
          <div>
            <h4>Delux Travel Concierge</h4>
            <span><span style="display:inline-block;width:7px;height:7px;background:#25d366;border-radius:50%"></span> Online · Quick Replies</span>
          </div>
        </div>
        <button class="wa-chat-close" id="waCloseBtn" onclick="window.closeDeluxWhatsApp()">&times;</button>
      </div>
      <div class="wa-chat-body">
        <div class="wa-bubble">
          Hello! 👋 Welcome to <strong>Delux Tour & Travel</strong>. Looking for an unforgettable holiday or custom itinerary? How can we help you today?
        </div>
        <div class="wa-chips">
          <button class="wa-chip" data-msg="Hi! I want details & pricing for the Bali Island Escape package.">🌴 Bali Island Package quote</button>
          <button class="wa-chip" data-msg="Hello! Can you help me plan a custom Switzerland & Europe trip?">🗺️ Custom European Trip Plan</button>
          <button class="wa-chip" data-msg="Hi! I would like to know about Train vs Flight travel options for packages.">🚆 Train vs Flight booking options</button>
          <button class="wa-chip" data-msg="Hello! What are your best upcoming seasonal offers and discounts?">🏷️ Today's Best Tour Deals</button>
        </div>
      </div>
      <div class="wa-chat-footer">
        <input type="text" id="waCustomInput" placeholder="Type your travel inquiry..." />
        <button class="wa-chat-send" id="waSendBtn" title="Send to WhatsApp" onclick="window.sendWhatsAppCustom()">
          <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(container);

  const inputField = document.getElementById('waCustomInput');
  if (inputField) {
    inputField.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        window.sendWhatsAppCustom();
      }
    });
  }

  container.querySelectorAll('.wa-chip').forEach(chip => {
    chip.onclick = () => {
      window.startWhatsApp(chip.dataset.msg);
      window.closeDeluxWhatsApp();
    };
  });
}

// Immediate injection attempt in case script is deferred or body ready
if (document.body) {
  injectWhatsAppWidget();
}


// ---------- DOM Ready ----------
document.addEventListener('DOMContentLoaded', () => {

  attachImageFallback();
  injectWhatsAppWidget();
  updateNavAuthState();

  // ---------- Register Form ----------
  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const status = document.getElementById('registerStatus');
      const f = registerForm;
      const password = f.querySelector('[name="password"]').value;
      const confirm = f.querySelector('[name="confirm"]').value;

      if (password !== confirm) {
        status.textContent = 'Passwords do not match.';
        status.style.color = '#c0392b';
        showToast('Passwords do not match.', 'error');
        return;
      }

      status.textContent = 'Creating your account...';
      status.style.color = '';

      const { ok, body } = await postJson(API.register, {
        fullName: f.querySelector('[name="name"]').value,
        email: f.querySelector('[name="email"]').value,
        password,
        confirm
      });

      if (ok) {
        status.textContent = 'Account created successfully! Redirecting...';
        status.style.color = '#27ae60';
        showToast('Account created successfully!', 'success');
        const nextParam = new URLSearchParams(location.search).get('next');
        const redirectUrl = nextParam ? `login.html?next=${encodeURIComponent(nextParam)}` : 'login.html';
        setTimeout(() => (location.href = redirectUrl), 800);
      } else {
        status.textContent = body.message || 'Registration failed. Please try again.';
        status.style.color = '#c0392b';
        showToast(body.message || 'Registration failed.', 'error');
      }
    });
  }

  // Preserve 'next' parameter across login and register page switch links
  const urlNextParam = new URLSearchParams(location.search).get('next');
  if (urlNextParam) {
    document.querySelectorAll('a[href="login.html"]').forEach(a => {
      a.href = `login.html?next=${encodeURIComponent(urlNextParam)}`;
    });
    document.querySelectorAll('a[href="register.html"]').forEach(a => {
      a.href = `register.html?next=${encodeURIComponent(urlNextParam)}`;
    });
  }

  // ---------- Login Form ----------
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const status = document.getElementById('loginStatus');
      const f = loginForm;

      status.textContent = 'Signing you in...';
      status.style.color = '';

      const { ok, body } = await postJson(API.login, {
        email: f.querySelector('[name="email"]').value,
        password: f.querySelector('[name="password"]').value
      });

      if (ok) {
        status.textContent = 'Login successful! Welcome back.';
        status.style.color = '#27ae60';
        showToast('Login successful! Welcome back.', 'success');
        const nextParam = new URLSearchParams(location.search).get('next');
        const redirectUrl = nextParam ? decodeURIComponent(nextParam) : 'index.html';
        setTimeout(() => (location.href = redirectUrl), 600);
      } else {
        status.textContent = body.message || 'Invalid email or password.';
        status.style.color = '#c0392b';
        showToast(body.message || 'Invalid email or password.', 'error');
      }
    });
  }

  // ---------- Contact Form ----------
  const contactForm = document.getElementById('contactForm');
  if (contactForm) {
    contactForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const status = document.getElementById('contactStatus');
      const f = contactForm;

      status.textContent = 'Sending your message...';
      status.style.color = '';

      const { ok, body } = await postJson(API.contact, {
        name: f.querySelector('[name="name"]').value,
        email: f.querySelector('[name="email"]').value,
        subject: f.querySelector('[name="subject"]').value,
        message: f.querySelector('[name="message"]').value
      });

      if (ok) {
        status.textContent = body.message || 'Thanks! Your message has been sent.';
        status.style.color = '#27ae60';
        showToast('Message sent! Our team will contact you soon.', 'success');
        f.reset();
      } else {
        status.textContent = body.message || 'Something went wrong. Please try again.';
        status.style.color = '#c0392b';
        showToast('Could not send message. Please try again.', 'error');
      }
    });
  }

  // ---------- Plan Trip Form ----------
  const planForm = document.getElementById('planForm');
  if (planForm) {
    planForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const status = document.getElementById('planStatus');
      const f = planForm;

      status.textContent = 'Submitting your custom trip request...';
      status.style.color = '';

      const travelModeInput = f.querySelector('[name="travelMode"]:checked');

      const { ok, body } = await postJson(API.plan, {
        name: f.querySelector('[name="name"]').value,
        email: f.querySelector('[name="email"]').value,
        destination: f.querySelector('[name="destination"]').value,
        date: f.querySelector('[name="date"]').value,
        travelers: f.querySelector('[name="travelers"]').value,
        budget: f.querySelector('[name="budget"]').value,
        travelMode: travelModeInput ? travelModeInput.value : 'Flight',
        message: f.querySelector('[name="message"]').value
      });

      if (ok) {
        const custEmail = f.querySelector('[name="email"]').value;
        status.innerHTML = `<strong>🎉 Trip Request Received!</strong> Confirmation details have been emailed to <u>${custEmail}</u>. Our travel team will contact you soon!`;
        status.style.color = '#27ae60';
        showToast(`🎉 Request received! Details emailed to ${custEmail}`, 'success');
        f.reset();
      } else {
        status.textContent = body.message || 'Something went wrong. Please try again.';
        status.style.color = '#c0392b';
        showToast('Failed to submit trip plan.', 'error');
      }
    });
  }

  // ---------- Packages Page (Search + Load) ----------
  const packageGrid = document.getElementById('packageGrid');
  if (packageGrid) {
    setupPackagesPage(packageGrid);
  }

  // ---------- Booking Page (book.html) ----------
  const bookingPackageCard = document.getElementById('bookingPackageCard');
  if (bookingPackageCard) {
    loadBookingPackage(bookingPackageCard);
  }

  const bookingForm = document.getElementById('bookingForm');
  if (bookingForm) {
    const travelersSelect = document.getElementById('bookingTravelersSelect');
    if (travelersSelect) {
      travelersSelect.addEventListener('change', updateLivePriceSummary);
    }

    // Verify User Authentication Before Allowing Booking
    (async function checkBookingAuth() {
      try {
        const res = await fetch(API.me, { credentials: 'same-origin' });
        const me = await res.json();
        const gate = document.getElementById('bookingLoginGate');
        const badge = document.getElementById('bookingAuthBadge');
        const params = new URLSearchParams(location.search);
        const packageId = params.get('packageId');
        const nextUrl = packageId ? `book.html?packageId=${packageId}` : 'book.html';

        if (!me.authenticated) {
          if (gate) {
            gate.style.display = 'block';
            const gateLoginBtn = document.getElementById('gateLoginBtn');
            const gateRegisterBtn = document.getElementById('gateRegisterBtn');
            if (gateLoginBtn) gateLoginBtn.href = `login.html?next=${encodeURIComponent(nextUrl)}`;
            if (gateRegisterBtn) gateRegisterBtn.href = `register.html?next=${encodeURIComponent(nextUrl)}`;
          }
          bookingForm.style.display = 'none';
        } else {
          if (gate) gate.style.display = 'none';
          bookingForm.style.display = 'block';
          if (badge) {
            badge.style.display = 'flex';
            const nameSpan = document.getElementById('authUserName');
            const emailSpan = document.getElementById('authUserEmail');
            if (nameSpan) nameSpan.textContent = me.name || 'Traveler';
            if (emailSpan) emailSpan.textContent = me.email || '';
          }
          // Auto pre-fill traveler information from logged-in account
          const nameInput = bookingForm.querySelector('[name="fullName"]');
          const emailInput = bookingForm.querySelector('[name="email"]');
          const phoneInput = bookingForm.querySelector('[name="phone"]');
          if (nameInput && !nameInput.value && me.name) nameInput.value = me.name;
          if (emailInput && !emailInput.value && me.email) emailInput.value = me.email;
          if (phoneInput && !phoneInput.value && me.phone) phoneInput.value = me.phone;
        }
      } catch (err) {
        // network issue fallback
      }
    })();

    bookingForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const status = document.getElementById('bookingStatus');
      const submitBtn = document.getElementById('payRazorpaySubmitBtn') || bookingForm.querySelector('button[type="submit"]');
      const f = bookingForm;
      const packageId = Number(document.getElementById('packageIdField').value);

      if (!packageId) {
        status.textContent = 'Please choose a package from the Packages page first.';
        status.style.color = '#c0392b';
        showToast('Please select a tour package first.', 'error');
        return;
      }

      const fullName = f.querySelector('[name="fullName"]').value.trim();
      const email = f.querySelector('[name="email"]').value.trim();
      const phone = f.querySelector('[name="phone"]').value.trim();
      const travelDate = f.querySelector('[name="travelDate"]').value;
      const travelers = f.querySelector('[name="travelers"]').value;
      const travelModeInput = f.querySelector('[name="travelMode"]:checked');
      const travelMode = travelModeInput ? travelModeInput.value : 'Flight';
      const notes = f.querySelector('[name="notes"]').value.trim();

      if (!fullName || !email || !phone || !travelDate) {
        status.textContent = 'Please fill all required traveler fields.';
        status.style.color = '#c0392b';
        showToast('Please fill all required traveler details.', 'error');
        return;
      }

      const originalBtnHtml = submitBtn.innerHTML;
      status.textContent = '🔒 Initializing secure UPI payment session...';
      status.style.color = '#b48738';
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="rzp-btn-spinner"></span> Generating UPI Payment Link & QR...';

      // 1. Create UPI Booking on server (server calculates exact Decimal fare)
      const { ok, body } = await postJson(API.upiCreateBooking, {
        packageId,
        fullName,
        email,
        phone,
        travelDate,
        travelers,
        travelMode,
        notes
      });

      if (!ok) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnHtml;
        if (body && body.requireLogin) {
          status.textContent = 'Please login to your account to book a tour package.';
          status.style.color = '#c0392b';
          showToast('Please login to continue booking.', 'error');
          const pkgId = document.getElementById('packageIdField').value;
          const nextUrl = pkgId ? `book.html?packageId=${pkgId}` : 'book.html';
          setTimeout(() => {
            location.href = `login.html?next=${encodeURIComponent(nextUrl)}`;
          }, 1000);
          return;
        }
        status.textContent = body.message || 'Could not initiate booking. Please try again.';
        status.style.color = '#c0392b';
        showToast(body.message || 'Could not initiate payment.', 'error');
        return;
      }

      showToast('Booking initiated! Redirecting to UPI payment page...', 'success');
      status.textContent = '✓ Booking created! Opening UPI payment gateway...';
      status.style.color = '#27ae60';

      const redirectUrl = body.redirectUrl || `/payment/upi/${body.bookingId}/`;
      setTimeout(() => {
        location.href = redirectUrl;
      }, 350);
    });
  }
});

// ---------- Live Fare & Price Summary Calculation ----------
function updateLivePriceSummary() {
  if (!window.currentBookingPackage) return;
  const travelersSelect = document.getElementById('bookingTravelersSelect');
  const count = travelersSelect ? Number(travelersSelect.value) || 1 : 1;
  const unitPrice = Number(window.currentBookingPackage.price) || 0;
  const total = unitPrice * count;

  const pkgTitleSpan = document.getElementById('summaryPkgTitle');
  const basePriceSpan = document.getElementById('summaryBasePrice');
  const travelersSpan = document.getElementById('summaryTravelersCount');
  const totalPayableSpan = document.getElementById('summaryTotalPayable');
  const btnPayAmount = document.getElementById('btnPayAmount');

  if (pkgTitleSpan) pkgTitleSpan.textContent = window.currentBookingPackage.title;
  if (basePriceSpan) basePriceSpan.textContent = `₹${unitPrice.toLocaleString('en-IN')} / person`;
  if (travelersSpan) travelersSpan.textContent = `${count} traveler${count > 1 ? 's' : ''}`;
  if (totalPayableSpan) totalPayableSpan.textContent = total.toLocaleString('en-IN');
  if (btnPayAmount) btnPayAmount.textContent = total.toLocaleString('en-IN');
}

// ---------- Render Verified UPI Booking Success Receipt ----------
function renderBookingSuccessReceipt(data, formElement) {
  if (formElement) formElement.style.display = 'none';
  const pkgCard = document.getElementById('bookingPackageCard');
  if (pkgCard) pkgCard.style.display = 'none';

  const container = document.getElementById('bookingReceiptContainer');
  if (!container) return;

  container.style.display = 'block';
  container.innerHTML = `
    <div class="booking-receipt-card">
      <div class="receipt-success-icon">✓</div>
      <span class="receipt-badge">VERIFIED DIRECT UPI PAYMENT</span>
      <h2 style="margin-top:12px;font-size:26px;">Booking &amp; Payment Confirmed!</h2>
      
      <!-- Official Tax Invoice Notice Banner -->
      <div style="margin:18px 0;padding:14px 18px;background:#e8f8f0;border:1.5px solid #27ae60;border-radius:10px;text-align:left;display:flex;align-items:center;gap:14px;">
        <span style="font-size:30px;line-height:1;">📧</span>
        <div>
          <strong style="color:#1e7e34;font-size:15px;display:block;margin-bottom:2px;">Official Tax Invoice Dispatched to Your Mail!</strong>
          <span style="color:#2d572c;font-size:13.5px;line-height:1.4;display:block;">
            Your formal GST Tax Invoice <strong>#INV-2026-DELUX-00${data.bookingId}</strong> and official booking itinerary have been sent directly to <strong>${esc(data.customerEmail)}</strong>.
          </span>
        </div>
      </div>

      <p style="color:#555;font-size:14px;margin-top:6px;">
        Thank you, <strong>${esc(data.customerName)}</strong>. Your payment was securely verified via Direct UPI.
      </p>

      <table class="receipt-table" style="margin-top:18px;">
        <tr>
          <td>Tax Invoice No:</td>
          <td><strong style="color:#1e7e34;font-family:monospace;letter-spacing:0.5px;">INV-2026-DELUX-00${data.bookingId}</strong></td>
        </tr>
        <tr>
          <td>Booking Reference:</td>
          <td>#DELUX-BK-${data.bookingId}</td>
        </tr>
        <tr>
          <td>UPI Reference / UTR:</td>
          <td><code style="background:#f4f0e6;padding:3px 8px;border-radius:4px;color:#17201d;font-family:monospace;font-weight:700;">${esc(data.utrNumber || data.paymentId || 'Verified UPI')}</code></td>
        </tr>
        <tr>
          <td>Tour Package:</td>
          <td><strong>${esc(data.packageTitle)}</strong></td>
        </tr>
        <tr>
          <td>Number of Travelers:</td>
          <td>${esc(data.travelers)} Traveler(s)</td>
        </tr>
        <tr>
          <td>Total Paid (INR):</td>
          <td><strong style="color:#b48738;font-size:18px;">₹${Number(data.amountPaid).toLocaleString('en-IN')}</strong></td>
        </tr>
        <tr>
          <td>Payment Mode:</td>
          <td><span style="color:#27ae60;font-weight:700;">✓ Verified Direct UPI (Zero-Fee Bank Transfer)</span></td>
        </tr>
      </table>

      <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-top:24px;">
        <a href="profile.html" class="btn primary">View in My Profile →</a>
        <button class="btn outline" onclick="window.print()">Print Receipt 🖨</button>
        <a href="packages.html" class="btn outline">Explore Other Tours</a>
      </div>
    </div>
  `;
}

// ---------- Load Package on Book.html ----------
async function loadBookingPackage(container) {
  const params = new URLSearchParams(location.search);
  const packageId = Number(params.get('packageId'));
  const packageIdField = document.getElementById('packageIdField');

  if (!packageId) {
    container.innerHTML = '<p style="padding:20px;">No package selected. <a href="packages.html" style="color:#b48738;font-weight:700">Browse packages</a> and click "Book Now".</p>';
    return;
  }

  try {
    const res = await fetch(API.packages);
    const packages = await res.json();
    const pkg = packages.find(p => p.id === packageId);

    if (!pkg) {
      container.innerHTML = '<p style="padding:20px;">That package could not be found. <a href="packages.html" style="color:#b48738;font-weight:700">Browse packages</a> instead.</p>';
      return;
    }

    window.currentBookingPackage = pkg;
    if (packageIdField) packageIdField.value = pkg.id;

    container.innerHTML = `
      <img src="${pkg.imageUrl}" alt="${pkg.title}">
      <div>
        <span>${pkg.duration}</span>
        <h3>${pkg.title}</h3>
        <p>${pkg.description}</p>
        <strong>₹${Number(pkg.price).toLocaleString('en-IN')} <small>/ person</small></strong>
      </div>`;

    updateLivePriceSummary();
    attachImageFallback();
  } catch {
    container.innerHTML = '<p style="padding:20px;">Could not load package details. Please try again from the Packages page.</p>';
  }
}

// ---------- Nav Auth State & "My Bookings" modal ----------
async function updateNavAuthState() {
  const loginLink = document.querySelector('.nav-login');
  const registerLink = document.querySelector('.nav-register');
  if (!loginLink || !registerLink) return;

  try {
    const res = await fetch('/api/auth/me', { credentials: 'same-origin' });
    const data = await res.json();

    if (data.authenticated) {
      loginLink.textContent = `✦ ${data.name.split(' ')[0]}`;
      loginLink.href = 'profile.html';
      loginLink.title = 'View Instagram-Style Travel Profile';
      loginLink.onclick = null;

      registerLink.textContent = 'Logout';

      registerLink.href = '#';
      registerLink.addEventListener('click', async (e) => {
        e.preventDefault();
        await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
        showToast('Logged out successfully.', 'info');
        setTimeout(() => (location.href = 'index.html'), 500);
      });
    }
  } catch {
    // static preview fallback
  }
}

// ---------- Packages Page with Live Search & Filter ----------
async function setupPackagesPage(container) {
  // Inject Search & Filter Bar before grid if not already present
  if (!document.getElementById('packageFilterBar')) {
    const filterHtml = `
      <div class="filter-bar" id="packageFilterBar">
        <div class="filter-group">
          <input type="text" id="packageSearchInput" placeholder="🔍 Search destination (Bali, Paris, Kashmir...)" />
        </div>
        <div class="filter-group" style="max-width:220px">
          <select id="budgetFilter">
            <option value="all">All Budgets</option>
            <option value="under40k">Under ₹40,000</option>
            <option value="40k-80k">₹40,000 - ₹80,000</option>
            <option value="above80k">Above ₹80,000</option>
          </select>
        </div>
        <div class="filter-group" style="max-width:200px">
          <select id="sortFilter">
            <option value="featured">Featured First</option>
            <option value="low-high">Price: Low to High</option>
            <option value="high-low">Price: High to Low</option>
          </select>
        </div>
      </div>
    `;
    container.insertAdjacentHTML('beforebegin', filterHtml);

    document.getElementById('packageSearchInput').addEventListener('input', applyPackageFilters);
    document.getElementById('budgetFilter').addEventListener('change', applyPackageFilters);
    document.getElementById('sortFilter').addEventListener('change', applyPackageFilters);
  }

  try {
    const res = await fetch(API.packages);
    allLoadedPackages = await res.json();
    renderPackageCards(allLoadedPackages, container);
  } catch {
    // Keep fallback cards if fetch fails
  }
}

function applyPackageFilters() {
  const query = (document.getElementById('packageSearchInput').value || '').toLowerCase().trim();
  const budget = document.getElementById('budgetFilter').value;
  const sort = document.getElementById('sortFilter').value;
  const container = document.getElementById('packageGrid');

  let filtered = allLoadedPackages.filter(p => {
    const matchesQuery = !query || p.title.toLowerCase().includes(query) || p.location.toLowerCase().includes(query) || p.duration.toLowerCase().includes(query);
    let matchesBudget = true;
    const price = Number(p.price);
    if (budget === 'under40k') matchesBudget = price < 40000;
    else if (budget === '40k-80k') matchesBudget = price >= 40000 && price <= 80000;
    else if (budget === 'above80k') matchesBudget = price > 80000;
    return matchesQuery && matchesBudget;
  });

  if (sort === 'low-high') {
    filtered.sort((a, b) => Number(a.price) - Number(b.price));
  } else if (sort === 'high-low') {
    filtered.sort((a, b) => Number(b.price) - Number(a.price));
  }

  renderPackageCards(filtered, container);
}

function renderPackageCards(packages, container) {
  if (!packages.length) {
    container.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:50px 20px;"><p style="font-size:18px;color:#707872;">No packages found matching your criteria.</p></div>';
    return;
  }

  container.innerHTML = packages.map(p => `
    <article class="package">
      <img loading="lazy" src="${p.imageUrl}" alt="${p.title}">
      <div class="package-body">
        <span>${p.duration}</span>
        <h3>${p.title}</h3>
        <p>${p.description}</p>
        <div class="package-footer">
          <strong>₹${Number(p.price).toLocaleString('en-IN')} <small>/ person</small></strong>
          <div class="package-actions">
            <button class="btn small outline" onclick="openPackageModal(${p.id})">Details ℹ</button>
            <a class="btn small primary" href="book.html?packageId=${p.id}">Book Now →</a>
          </div>
        </div>
      </div>
    </article>
  `).join('');
  attachImageFallback();
}

// ---------- Detailed Package Modal (Itinerary & Inclusions) ----------
window.openPackageModal = function(packageId) {
  const pkg = allLoadedPackages.find(p => p.id === packageId);
  if (!pkg) return;

  let modal = document.getElementById('deluxPackageModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'deluxPackageModal';
    modal.className = 'delux-modal';
    document.body.appendChild(modal);
  }

  const itineraryLines = (pkg.itinerary || '').split('\n').filter(Boolean);
  const inclusionLines = (pkg.inclusions || '').split('\n').filter(Boolean);

  modal.innerHTML = `
    <div class="delux-modal-box">
      <button class="delux-modal-close" onclick="this.closest('.delux-modal').classList.remove('open')">&times;</button>
      <span style="font-size:11px;font-weight:800;color:#b48738;letter-spacing:2px;text-transform:uppercase">${pkg.duration}</span>
      <h2 class="delux-modal-title">${pkg.title}</h2>
      <p style="color:#6c736e;font-size:14px;margin-bottom:20px">${pkg.description}</p>
      
      <div style="margin-bottom:20px">
        <h4 style="font-size:15px;margin-bottom:8px;color:#17201d">📍 Location & Pricing:</h4>
        <p style="font-size:13px;color:#444"><strong>Destination:</strong> ${pkg.location}</p>
        <p style="font-size:18px;color:#b48738;font-weight:700;margin-top:4px">₹${Number(pkg.price).toLocaleString('en-IN')} <small style="color:#777;font-size:11px">/ person (All taxes incl.)</small></p>
      </div>

      ${itineraryLines.length ? `
        <div style="margin-bottom:20px">
          <h4 style="font-size:15px;margin-bottom:10px;color:#17201d">🗺 Day-Wise Itinerary:</h4>
          <ul style="padding-left:20px;font-size:13px;color:#555;line-height:1.7">
            ${itineraryLines.map(line => `<li>${line}</li>`).join('')}
          </ul>
        </div>
      ` : ''}

      ${inclusionLines.length ? `
        <div style="margin-bottom:24px">
          <h4 style="font-size:15px;margin-bottom:10px;color:#17201d">✨ Package Inclusions:</h4>
          <div style="display:flex;flex-wrap:wrap;gap:8px">
            ${inclusionLines.map(inc => `<span style="background:#f1eee7;padding:6px 12px;border-radius:20px;font-size:12px;font-weight:600">✓ ${inc}</span>`).join('')}
          </div>
        </div>
      ` : ''}

      <div style="display:flex;justify-content:flex-end;gap:12px;margin-top:20px;border-top:1px solid #eee;padding-top:16px">
        <button class="btn outline" onclick="document.getElementById('deluxPackageModal').classList.remove('open')">Close</button>
        <a class="btn primary" href="book.html?packageId=${pkg.id}">Book This Package →</a>
      </div>
    </div>
  `;

  modal.classList.add('open');
  modal.onclick = (e) => {
    if (e.target === modal) modal.classList.remove('open');
  };
};

// ---------- Customer "My Bookings" Modal ----------
async function openMyBookingsModal(userName) {
  let modal = document.getElementById('deluxMyBookingsModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'deluxMyBookingsModal';
    modal.className = 'delux-modal';
    document.body.appendChild(modal);
  }

  modal.innerHTML = `
    <div class="delux-modal-box" style="max-width:750px">
      <button class="delux-modal-close" onclick="this.closest('.delux-modal').classList.remove('open')">&times;</button>
      <h2 class="delux-modal-title">My Travel Dashboard</h2>
      <p style="color:#707872;font-size:13px;margin-bottom:20px">Welcome back, <strong>${userName}</strong>! Here is the status of your booked tours and trip inquiries.</p>
      <div id="myBookingsContent" style="min-height:120px;display:flex;align-items:center;justify-content:center">
        <span>Loading your bookings...</span>
      </div>
    </div>
  `;

  modal.classList.add('open');
  modal.onclick = (e) => { if (e.target === modal) modal.classList.remove('open'); };

  try {
    const res = await fetch(API.myBookings);
    const data = await res.json();
    const content = document.getElementById('myBookingsContent');

    if (!data.bookings?.length && !data.plans?.length) {
      content.innerHTML = '<p style="padding:20px;text-align:center;color:#777">You have not made any bookings yet. <a href="packages.html" style="color:#b48738;font-weight:700">Browse packages</a> to plan your journey!</p>';
      return;
    }

    let html = '';
    if (data.bookings?.length) {
      html += '<h4 style="margin:15px 0 10px;font-size:14px;color:#17201d">📦 Tour Package Bookings</h4>';
      html += '<div style="overflow-x:auto"><table class="admin-table"><thead><tr><th>Package</th><th>Travel Mode</th><th>Travelers</th><th>Status</th></tr></thead><tbody>';
      data.bookings.forEach(b => {
        const badgeClass = b.status === 'Confirmed' ? 'status-confirmed' : (b.status === 'Cancelled' ? 'status-cancelled' : 'status-pending');
        html += `
          <tr>
            <td><strong>${b.packageTitle}</strong><br><small>₹${Number(b.packagePrice).toLocaleString('en-IN')}</small></td>
            <td><span class="mode-pill mode-${b.travelMode.toLowerCase()}">${b.travelMode}</span></td>
            <td>${b.travelers}</td>
            <td><span class="status-badge ${badgeClass}">${b.status}</span></td>
          </tr>
        `;
      });
      html += '</tbody></table></div>';
    }

    if (data.plans?.length) {
      html += '<h4 style="margin:25px 0 10px;font-size:14px;color:#17201d">🗺 Custom Trip Inquiries</h4>';
      html += '<div style="overflow-x:auto"><table class="admin-table"><thead><tr><th>Destination</th><th>Mode</th><th>Budget</th><th>Date</th></tr></thead><tbody>';
      data.plans.forEach(p => {
        html += `
          <tr>
            <td><strong>${p.destination}</strong></td>
            <td><span class="mode-pill mode-${p.travelMode.toLowerCase()}">${p.travelMode}</span></td>
            <td>${p.budget || 'Flexible'}</td>
            <td>${p.travelDate || 'Flexible'}</td>
          </tr>
        `;
      });
      html += '</tbody></table></div>';
    }

    content.innerHTML = html;
  } catch {
    document.getElementById('myBookingsContent').innerHTML = '<p style="color:#c0392b">Unable to load bookings at this moment.</p>';
  }
}
