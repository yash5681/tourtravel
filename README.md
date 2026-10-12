# Delux Tour & Travel - Full Stack (Python Django + MySQL WAMP)

Aa project ne complete **.NET (C#) mathi Python Django 5.x** ma successfully replace karyu che.
Tamari original design, layout, color theme ane badhu working same che. Sathe **next-level attractive features** pan add karya che!

---

## 🌟 New & Next-Level Features

1. **Python Django Full-Stack Architecture**:
   - .NET / C# Web API ni jagyae high-performance Django 5.x ORM, Views ane APIs.
   - WAMP Server MySQL (`deluxtourtraveldb` on `localhost:3306`) sathe 100% compatible.
2. **Interactive Live Search & Filter** (`packages.html`):
   - Customer destination (Bali, Paris, Dubai, Kashmir etc.), budget filter (Under 40k, 40k-80k, Above 80k) ane sorting thi live filter kari shake che.
3. **Day-Wise Itinerary & Inclusions Modal**:
   - Koi pan tour package par "Details ℹ" click karta popup ma day-wise travel plan ane included items (hotel, meals, transfer) instantly joi shake che.
4. **Admin Panel Package Management (CRUD)**:
   - Admin dashboard mathi new tour packages add ane old packages delete kari shake che.
5. **Customer "My Bookings" Portal**:
   - Login customer navbar ma potana name par click kari badha previous bookings ane status (Pending / Confirmed / Cancelled) joi shake che.
6. **Export Bookings to Excel / CSV**:
   - Admin dashboard mathi 1 click ma badha bookings Excel/CSV file ma download kari shake che.
7. **Dual Admin System**:
   - Dedicated custom admin portal: `/admin-login.html` -> `/admin.html`
   - Official Django superadmin portal: `/django-admin/`
9. **Online Razorpay Payment Gateway Integration**:
   - Official Razorpay SDK integration for booking packages (`create-order`, `verify-payment`, HMAC-SHA256 signature verification).
   - Dynamic price calculation based on traveler count (`₹package_price × travelers`).
   - Digital tax invoice & booking receipt generation with Razorpay Payment ID, print/download receipt button.
   - Database schema records `payment_status`, `razorpay_order_id`, `razorpay_payment_id`, `razorpay_signature`, and `amount_paid`.
   - Admin panel and customer profile display verified payment badge and transaction ID.
10. **Brand Logo Suite & Universal Integration**:
   - High-resolution SVG luxury gold star & compass crest with orbit arc (`logo.svg`, `logo-light.svg`, `logo-icon.svg`, `favicon.svg`).
   - Deployed across all 12 templates: navbar header, footer, auth screens, admin console, email vouchers, and WhatsApp concierge avatar.
11. **Contact Page Laptop & Desktop Responsive Redesign**:
   - Fixed unconstrained desktop margins and alignment issues on laptops (1366px - 1440px).
   - Designed 1200px balanced 2-column grid layout with direct clickable cards (phone, email, address, and interactive Google Map) + balanced contact form card.
12. **Automated Gmail SMTP Notifications**:
   - Contact form ke booking submit thata j admin email (`yashprajapati5681@gmail.com`) par automatic email notification with payment confirmation.

---

## 🗂 Project Structure

```
DeluxTourTravel_FullStack/
├── manage.py                       # Django management utility
├── run.bat                         # One-click Windows starter (http://localhost:5000)
├── requirements.txt                # Python dependencies (Django, PyMySQL, etc.)
├── delux_travel/                   # Django settings, URLs, MySQL patches
│   ├── settings.py                 # WAMP MySQL, SMTP, Session config
│   ├── urls.py                     # Root routing + static fallback
│   └── __init__.py                 # WAMP MySQL compatibility layer
├── tours/                          # Application logic
│   ├── models.py                   # Package, Booking, TripPlan, ContactMessage, CustomerUser
│   ├── api_views.py                # Full REST API endpoints
│   ├── views.py                    # HTML templates renderers
│   ├── emails.py                   # Gmail SMTP notification engine
│   ├── security.py                 # PBKDF2 password hasher
│   ├── admin.py                    # Django Admin models configuration
│   └── management/commands/seed_data.py # Initial database seeder
├── static/                         # Frontend CSS, JS, scripts
│   ├── style.css                   # Premium luxury styling + modals + toasts
│   ├── app.js                      # Frontend interactivity & APIs
│   ├── admin.js                    # Admin dashboard interactivity
│   └── script.js
├── templates/                      # Original HTML pages
│   ├── index.html, about.html, packages.html, book.html, plan.html
│   ├── gallery.html, contact.html, login.html, register.html
│   ├── admin-login.html, admin.html
└── _legacy_dotnet_backup/          # Pela ni .NET files no secure backup
```   

---

## ▶️ Server Kevi Rite Start Karvo

### Method 1: `run.bat` par double-click karo (Easy!)
`DeluxTourTravel_FullStack` folder ma ni `run.bat` file par double-click karo.
Aa automatically Python server start kari dese.

### Method 2: Terminal / Command Prompt thi
```powershell
cd "d:\Tours and Travels\DeluxTourTravel_FullStack django\DeluxTourTravel_FullStack"
python manage.py runserver 0.0.0.0:5000
```

Browser ma open karo:
👉 **http://localhost:5000**

---

## 🔐 Login Details

### 1. Admin Dashboard (Admin Dashboard & Django Admin)
- **URL**: `http://localhost:5000/admin-login.html` athva `http://localhost:5000/django-admin/`
- **Email / Username**: `admin@deluxtour.com` (athva `admin`)
- **Password**: `Admin@123`

### 2. Customer Login
- **URL**: `http://localhost:5000/login.html`
- **Email**: `pyash7571@gmail.com`
- **Password**: `yash@2007`
*(athva Register page par thi new account pan banavi shako cho.)*

---

## 💾 WAMP MySQL Database Details
- **Host**: `127.0.0.1` / `localhost`
- **Port**: `3306`
- **Database Name**: `deluxtourtraveldb`
- **User**: `root`
- **Password**: ` ` (blank)
- WAMP Server 2.1 (MySQL 5.5.8) mate special compatibility layer lagadyo che, etle badhu smoothly chale che.



========================================================================
                     ✦ ALL PROJECT URLS / બધી જ લિંક ✦
========================================================================

 [ CUSTOMER WEBSITE PAGES / મુલાકાતીઓ માટે પેજીસ ]
   - Home Page:           http://localhost:5000/
   - Tour Packages:       http://localhost:5000/packages.html  (or /packages)
   - Book a Package:      http://localhost:5000/book.html      (or /book)
   - Plan Custom Trip:    http://localhost:5000/plan.html      (or /plan)
   - Photo Gallery:       http://localhost:5000/gallery.html   (or /gallery)
   - About Us:            http://localhost:5000/about.html     (or /about)
   - Contact Us:          http://localhost:5000/contact.html   (or /contact)

 [ CUSTOMER ACCOUNT & PROFILE / કસ્ટમર એકાઉન્ટ ]
   - Customer Login:      http://localhost:5000/login.html     (or /login)
   - Customer Register:   http://localhost:5000/register.html  (or /register)
   - Instagram Profile:   http://localhost:5000/profile.html   (or /profile)

 [ ADMIN PORTALS / એડમિન પોર્ટલ ]
   - Custom Admin Login:  http://localhost:5000/admin-login.html (or /admin-login)
   - Custom Admin Panel:  http://localhost:5000/admin.html       (or /admin)
   - Django SuperAdmin:   http://localhost:5000/django-admin/

 [ ADMIN CREDENTIALS / એડમિન લૉગિન વિગત ]
   - Admin Email:         admin@deluxtour.com
   - Django Username:     admin
   - Password:            Admin@123

 [ DATA & EXPORT APIS ]
   - Packages API:        http://localhost:5000/api/packages
   - Export Bookings CSV: http://localhost:5000/api/admin/export/bookings
========================================================================