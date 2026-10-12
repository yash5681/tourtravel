// ============================================================
// Delux Tour & Travel — Admin Dashboard Engine (Django API)
// Handles admin auth, summary stats, live booking updates,
// package CRUD, and views for plans, contacts, and users.
// ============================================================

const ADMIN_API = {
  login: '/api/admin/login',
  logout: '/api/admin/logout',
  me: '/api/admin/me',
  summary: '/api/admin/summary',
  bookings: '/api/admin/bookings',
  plans: '/api/admin/plans',
  contacts: '/api/admin/contacts',
  users: '/api/admin/users',
  packages: '/api/packages',
  adminPackages: '/api/admin/packages'
};

let allAdminBookings = [];

async function postJson(url, data, method = 'POST') {
  const res = await fetch(url, {
    method: method,
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify(data)
  });
  let body = {};
  try { body = await res.json(); } catch { /* no body */ }
  return { ok: res.ok, status: res.status, body };
}

async function getJson(url) {
  const res = await fetch(url, { credentials: 'same-origin' });
  if (res.status === 401 || res.status === 403) {
    location.href = 'admin-login.html';
    return null;
  }
  return res.json();
}

function esc(v) {
  return (v ?? '').toString()
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function fmtDate(d) {
  if (!d) return '—';
  const dt = new Date(d);
  return isNaN(dt) ? '—' : dt.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

document.addEventListener('DOMContentLoaded', () => {

  // ---------- admin-login.html ----------
  const adminLoginForm = document.getElementById('adminLoginForm');
  if (adminLoginForm) {
    adminLoginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const status = document.getElementById('adminLoginStatus');
      status.textContent = 'Signing you in...';
      status.style.color = '#b48738';

      const { ok, body } = await postJson(ADMIN_API.login, {
        email: adminLoginForm.querySelector('[name="email"]').value,
        password: adminLoginForm.querySelector('[name="password"]').value
      });

      if (ok) {
        status.textContent = 'Welcome! Redirecting to dashboard...';
        status.style.color = '#27ae60';
        setTimeout(() => (location.href = 'admin.html'), 400);
      } else {
        status.textContent = body.message || 'Invalid admin email or password.';
        status.style.color = '#c0392b';
      }
    });
  }

  // ---------- admin.html ----------
  const summaryCards = document.getElementById('summaryCards');
  if (summaryCards) {
    initAdminDashboard();
  }
});

async function initAdminDashboard() {
  const me = await getJson(ADMIN_API.me);
  if (!me) return;
  if (!me.authenticated) {
    location.href = 'admin-login.html';
    return;
  }
  document.getElementById('adminEmailTag').textContent = me.email || 'admin@deluxtour.com';

  document.getElementById('adminLogoutBtn').addEventListener('click', async () => {
    await fetch(ADMIN_API.logout, { method: 'POST', credentials: 'same-origin' });
    location.href = 'admin-login.html';
  });

  // Tab switching
  const buttons = document.querySelectorAll('.admin-nav-btn');
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('.admin-tab').forEach(t => t.style.display = 'none');
      const target = document.getElementById(`tab-${btn.dataset.tab}`);
      if (target) target.style.display = 'block';
      document.getElementById('adminSectionTitle').textContent = btn.textContent;
    });
  });

  // Add Package Form submit listener
  const addPkgForm = document.getElementById('addPackageForm');
  if (addPkgForm) {
    addPkgForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fd = new FormData(addPkgForm);
      const pkgId = fd.get('id');
      const pkgData = {
        title: fd.get('title'),
        duration: fd.get('duration'),
        location: fd.get('location'),
        price: Number(fd.get('price')),
        imageUrl: fd.get('imageUrl') || 'https://placehold.co/900x600/17201d/ffffff?text=Delux+Tour',
        description: fd.get('description') || '',
        itinerary: fd.get('itinerary') || '',
        inclusions: fd.get('inclusions') || ''
      };
      if (pkgId) pkgData.id = Number(pkgId);

      const { ok, body } = await postJson(ADMIN_API.adminPackages, pkgData);
      if (ok) {
        alert(pkgId ? 'Tour package updated successfully!' : 'Tour package created successfully!');
        closeAddPackageModal();
        loadAdminPackages();
        loadSummary();
      } else {
        alert(body.message || 'Failed to save package.');
      }
    });
  }

  // Booking search and status filter listeners
  const searchInput = document.getElementById('adminBookingSearch');
  const statusFilter = document.getElementById('adminBookingStatusFilter');
  if (searchInput) searchInput.addEventListener('input', filterAdminBookings);
  if (statusFilter) statusFilter.addEventListener('change', filterAdminBookings);

  await Promise.all([
    loadSummary(),
    loadBookings(),
    loadAdminPackages(),
    loadPlans(),
    loadContacts(),
    loadUsers()
  ]);
}

async function loadSummary() {
  const data = await getJson(ADMIN_API.summary);
  if (!data) return;
  const cards = [
    ['Total Bookings', data.totalBookings],
    ['Awaiting UPI Verify', `<span style="color:#d97706;font-weight:800;">${data.pendingVerifications || 0}</span>`],
    ['Pending Bookings', data.pendingBookings],
    ['Tour Packages', data.totalPackages],
    ['Train Bookings', data.trainBookings],
    ['Flight Bookings', data.flightBookings],
    ['Trip Plan Requests', data.totalTripPlans],
    ['Registered Users', data.totalUsers]
  ];
  document.getElementById('summaryCards').innerHTML = cards.map(([label, value]) => `
    <div class="admin-card"><strong>${value}</strong><span>${label}</span></div>
  `).join('');
}

async function loadBookings() {
  const data = await getJson(ADMIN_API.bookings);
  if (!data) return;
  allAdminBookings = data;
  filterAdminBookings();
}

window.adminApproveUpi = async function(bookingId) {
  if (!confirm(`Are you sure you want to APPROVE payment for booking #${bookingId}?\nThis will mark the booking CONFIRMED and dispatch the official GST Tax Invoice email to the customer.`)) {
    return;
  }
  const { ok, body } = await postJson(`/api/admin/bookings/${bookingId}/approve-upi`, {});
  if (ok) {
    alert(body.message || 'Payment verified and booking confirmed!');
    await loadSummary();
    await loadBookings();
  } else {
    alert(body.message || 'Failed to approve booking.');
  }
};

window.adminRejectUpi = async function(bookingId) {
  const reason = prompt(`Enter rejection reason for booking #${bookingId}:`, 'The submitted UPI Reference / UTR number could not be matched with bank records.');
  if (reason === null) return;
  const { ok, body } = await postJson(`/api/admin/bookings/${bookingId}/reject-upi`, { reason });
  if (ok) {
    alert(body.message || 'Payment marked as rejected.');
    await loadSummary();
    await loadBookings();
  } else {
    alert(body.message || 'Failed to reject booking.');
  }
};

function filterAdminBookings() {
  const q = (document.getElementById('adminBookingSearch')?.value || '').toLowerCase().trim();
  const status = document.getElementById('adminBookingStatusFilter')?.value || 'all';
  const body = document.getElementById('bookingsBody');
  if (!body) return;

  const filtered = allAdminBookings.filter(b => {
    const matchesQ = !q ||
      b.fullName.toLowerCase().includes(q) ||
      b.email.toLowerCase().includes(q) ||
      b.phone.toLowerCase().includes(q) ||
      (b.utrNumber && b.utrNumber.toLowerCase().includes(q)) ||
      (b.bookingReference && b.bookingReference.toLowerCase().includes(q)) ||
      b.packageTitle.toLowerCase().includes(q);

    let matchesStatus = true;
    if (status !== 'all') {
      if (status === 'PENDING_VERIFICATION') {
        matchesStatus = (b.paymentStatus === 'PENDING_VERIFICATION');
      } else if (status === 'Pending') {
        matchesStatus = (b.status === 'Pending' || b.status === 'PENDING') && b.paymentStatus !== 'PENDING_VERIFICATION';
      } else if (status === 'Confirmed') {
        matchesStatus = (b.status === 'Confirmed' || b.status === 'CONFIRMED' || b.paymentStatus === 'PAID' || b.paymentStatus === 'Paid');
      } else if (status === 'REJECTED') {
        matchesStatus = (b.status === 'REJECTED' || b.paymentStatus === 'REJECTED');
      } else if (status === 'Cancelled') {
        matchesStatus = (b.status === 'Cancelled' || b.status === 'CANCELLED');
      }
    }

    return matchesQ && matchesStatus;
  });

  if (!filtered.length) {
    body.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:24px;color:#777">No bookings found matching your search.</td></tr>';
  } else {
    body.innerHTML = filtered.map(b => {
      let paymentBadge = '';
      if (b.paymentStatus === 'PENDING_VERIFICATION') {
        paymentBadge = `
          <span style="display:inline-block;padding:3px 8px;border-radius:10px;font-size:11px;font-weight:700;background:#fef3c7;color:#b45309">⏳ Awaiting Verification</span>
          ${b.utrNumber ? `<br><small style="font-weight:700;color:#0284c7;font-family:monospace;">UTR: ${esc(b.utrNumber)}</small>` : ''}
          <div style="margin-top:6px;display:flex;gap:4px;">
            <button type="button" class="btn small primary" onclick="adminApproveUpi(${b.id})" style="padding:3px 8px;font-size:11px;background:#16a34a;border:0;">✓ Approve</button>
            <button type="button" class="btn small danger" onclick="adminRejectUpi(${b.id})" style="padding:3px 8px;font-size:11px;background:#dc2626;border:0;">✕ Reject</button>
          </div>
        `;
      } else if (b.paymentStatus === 'PAID' || b.status === 'CONFIRMED') {
        paymentBadge = `
          <span style="display:inline-block;padding:3px 8px;border-radius:10px;font-size:11px;font-weight:700;background:#e8f8f0;color:#1e824c">✓ Verified &amp; Paid</span>
          ${b.utrNumber ? `<br><small style="color:#166534;font-family:monospace;">UTR: ${esc(b.utrNumber)}</small>` : ''}
          <br><small style="color:#64748b">Verified by: ${esc(b.verifiedBy || 'Admin')}</small>
        `;
      } else if (b.paymentStatus === 'REJECTED') {
        paymentBadge = `
          <span style="display:inline-block;padding:3px 8px;border-radius:10px;font-size:11px;font-weight:700;background:#fee2e2;color:#991b1b">✕ Payment Rejected</span>
          ${b.rejectionReason ? `<br><small style="color:#dc2626">${esc(b.rejectionReason)}</small>` : ''}
        `;
      } else {
        paymentBadge = `
          <span style="display:inline-block;padding:3px 8px;border-radius:10px;font-size:11px;font-weight:700;background:#f3f4f6;color:#4b5563">Pending Payment</span>
          <br><small style="color:#b48738;font-weight:700">₹${Number(b.totalAmount || b.packagePrice).toLocaleString('en-IN')}</small>
        `;
      }

      return `
        <tr>
          <td>${fmtDate(b.createdAt)}</td>
          <td><strong>${esc(b.packageTitle)}</strong><br><small>₹${Number(b.packagePrice).toLocaleString('en-IN')}</small></td>
          <td>${esc(b.fullName)}</td>
          <td>${esc(b.email)}<br><small>${esc(b.phone)}</small></td>
          <td><span class="mode-pill mode-${esc(b.travelMode).toLowerCase()}">${esc(b.travelMode)}</span></td>
          <td>${esc(b.travelers)}</td>
          <td>${fmtDate(b.travelDate)}</td>
          <td>${paymentBadge}</td>
          <td>
            <select class="status-select" data-id="${b.id}">
              <option value="Pending" ${b.status === 'Pending' || b.status === 'PENDING' ? 'selected' : ''}>Pending</option>
              <option value="Confirmed" ${b.status === 'Confirmed' || b.status === 'CONFIRMED' ? 'selected' : ''}>Confirmed</option>
              <option value="Cancelled" ${b.status === 'Cancelled' || b.status === 'CANCELLED' ? 'selected' : ''}>Cancelled</option>
              <option value="REJECTED" ${b.status === 'REJECTED' ? 'selected' : ''}>Rejected</option>
            </select>
          </td>
        </tr>
      `;
    }).join('');

    body.querySelectorAll('.status-select').forEach(sel => {
      sel.addEventListener('change', async () => {
        const newStatus = sel.value;
        await postJson(`/api/admin/bookings/${sel.dataset.id}/status`, { status: newStatus });
        const target = allAdminBookings.find(b => b.id === Number(sel.dataset.id));
        if (target) target.status = newStatus;
        loadSummary();
        filterAdminBookings();
      });
    });
  }

  // Populate Overview tab top 5 recent bookings
  const recentBody = document.getElementById('overviewRecentBookings');
  if (recentBody) {
    const top5 = allAdminBookings.slice(0, 5);
    if (!top5.length) {
      recentBody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:16px;color:#777">No bookings registered yet.</td></tr>';
    } else {
      recentBody.innerHTML = top5.map(b => `
        <tr>
          <td>${fmtDate(b.createdAt)}</td>
          <td><strong>${esc(b.packageTitle)}</strong></td>
          <td>${esc(b.fullName)}</td>
          <td><span class="mode-pill mode-${esc(b.travelMode).toLowerCase()}">${esc(b.travelMode)}</span></td>
          <td><span class="status-badge status-${(b.status || 'pending').toLowerCase()}">${esc(b.status)}</span></td>
        </tr>
      `).join('');
    }
  }
}

let loadedAdminPackages = [];

async function loadAdminPackages() {
  const body = document.getElementById('adminPackagesBody');
  if (!body) return;
  try {
    const data = await getJson(ADMIN_API.packages);
    loadedAdminPackages = data || [];
    if (!loadedAdminPackages.length) {
      body.innerHTML = '<tr><td colspan="7">No packages found.</td></tr>';
      return;
    }
    body.innerHTML = loadedAdminPackages.map(p => `
      <tr>
        <td>#${p.id}</td>
        <td><img src="${p.imageUrl}" style="width:60px;height:42px;border-radius:4px;object-fit:cover" /></td>
        <td><strong>${esc(p.title)}</strong></td>
        <td>${esc(p.location)}</td>
        <td>${esc(p.duration)}</td>
        <td>₹${Number(p.price).toLocaleString('en-IN')}</td>
        <td style="white-space:nowrap">
          <button class="btn small outline" onclick="editPackage(${p.id})" style="margin-right:6px">Edit</button>
          <button class="btn small danger" onclick="deletePackage(${p.id})">Delete</button>
        </td>
      </tr>
    `).join('');
  } catch {
    body.innerHTML = '<tr><td colspan="7">Error loading packages.</td></tr>';
  }
}

window.editPackage = function(pkgId) {
  const pkg = loadedAdminPackages.find(p => p.id === pkgId);
  if (!pkg) return;
  const form = document.getElementById('addPackageForm');
  if (!form) return;
  const title = document.getElementById('addPackageModalTitle');
  if (title) title.textContent = 'Edit Tour Package (#' + pkg.id + ')';
  const idField = document.getElementById('pkgIdField');
  if (idField) idField.value = pkg.id;
  form.querySelector('[name="title"]').value = pkg.title || '';
  form.querySelector('[name="duration"]').value = pkg.duration || '';
  form.querySelector('[name="location"]').value = pkg.location || '';
  form.querySelector('[name="price"]').value = pkg.price || 0;
  form.querySelector('[name="imageUrl"]').value = pkg.imageUrl || '';
  form.querySelector('[name="description"]').value = pkg.description || '';
  form.querySelector('[name="itinerary"]').value = pkg.itinerary || '';
  form.querySelector('[name="inclusions"]').value = pkg.inclusions || '';
  window.openAddPackageModal();
};

window.openAddPackageModal = function() {
  const modal = document.getElementById('addPackageModal');
  if (modal) {
    modal.style.setProperty('display', 'flex', 'important');
    modal.classList.add('open');
  }
};

window.closeAddPackageModal = function() {
  const modal = document.getElementById('addPackageModal');
  if (modal) {
    modal.style.setProperty('display', 'none', 'important');
    modal.classList.remove('open');
  }
  const form = document.getElementById('addPackageForm');
  if (form) form.reset();
  const idField = document.getElementById('pkgIdField');
  if (idField) idField.value = '';
  const title = document.getElementById('addPackageModalTitle');
  if (title) title.textContent = 'Add New Tour Package';
};

window.deletePackage = async function(pkgId) {
  if (!confirm('Are you sure you want to delete this tour package?')) return;
  const { ok, body } = await postJson(ADMIN_API.adminPackages, { id: pkgId }, 'DELETE');
  if (ok) {
    loadAdminPackages();
    loadSummary();
  } else {
    alert(body.message || 'Failed to delete package.');
  }
};

async function loadPlans() {
  const data = await getJson(ADMIN_API.plans);
  if (!data) return;
  const body = document.getElementById('plansBody');
  if (!data.length) { body.innerHTML = '<tr><td colspan="8">No trip plan requests yet.</td></tr>'; return; }

  body.innerHTML = data.map(p => `
    <tr>
      <td>${fmtDate(p.createdAt)}</td>
      <td>${esc(p.name)}</td>
      <td>${esc(p.email)}</td>
      <td>${esc(p.destination)}</td>
      <td><span class="mode-pill mode-${esc(p.travelMode).toLowerCase()}">${esc(p.travelMode)}</span></td>
      <td>${esc(p.travelers)}</td>
      <td>${esc(p.budget)}</td>
      <td>${esc(p.message)}</td>
    </tr>
  `).join('');
}

async function loadContacts() {
  const data = await getJson(ADMIN_API.contacts);
  if (!data) return;
  const body = document.getElementById('contactsBody');
  if (!data.length) { body.innerHTML = '<tr><td colspan="5">No messages yet.</td></tr>'; return; }

  body.innerHTML = data.map(c => `
    <tr>
      <td>${fmtDate(c.createdAt)}</td>
      <td>${esc(c.name)}</td>
      <td>${esc(c.email)}</td>
      <td>${esc(c.subject)}</td>
      <td>${esc(c.message)}</td>
    </tr>
  `).join('');
}

async function loadUsers() {
  const data = await getJson(ADMIN_API.users);
  if (!data) return;
  const body = document.getElementById('usersBody');
  if (!data.length) { body.innerHTML = '<tr><td colspan="3">No registered users yet.</td></tr>'; return; }

  body.innerHTML = data.map(u => `
    <tr>
      <td>${fmtDate(u.createdAt)}</td>
      <td>${esc(u.fullName)}</td>
      <td>${esc(u.email)}</td>
    </tr>
  `).join('');
}


