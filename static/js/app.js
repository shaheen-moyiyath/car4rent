// Car4Rent: Main Application State & API Controller

let currentUser = {
    user_id: 4,
    role: 'Client',
    name: 'John Doe',
    email: 'john.doe@gmail.com'
};

window.currentUser = currentUser;

let allCategories = [];
let activeTab = 'catalog';

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    setupRoleMenu();
    await loadCategories();
    await loadVehicles();
    updateUserBadge();

    // Price slider listener
    const priceSlider = document.getElementById('filter-price');
    if (priceSlider) {
        priceSlider.addEventListener('input', (e) => {
            document.getElementById('price-slider-val').innerText = `$${e.target.value}/day`;
        });
    }

    // Set default checkout dates
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 3);

    const startInput = document.getElementById('checkout-start-date');
    const endInput = document.getElementById('checkout-end-date');
    if (startInput && endInput) {
        startInput.value = today.toISOString().split('T')[0];
        endInput.value = tomorrow.toISOString().split('T')[0];
    }
}

// --- Persona Switching & Authentication ---
function setupRoleMenu() {
    const btn = document.getElementById('role-badge-btn');
    const menu = document.getElementById('role-menu');
    if (btn && menu) {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            menu.classList.toggle('hidden');
        });
        document.addEventListener('click', () => menu.classList.add('hidden'));
    }
}

function demoLogin(userId, role, name) {
    currentUser = {
        user_id: userId,
        role: role,
        name: name,
        email: role === 'Admin' ? 'admin@car4rent.com' : role === 'Owner' ? 'alex.fleet@car4rent.com' : 'john.doe@gmail.com'
    };
    window.currentUser = currentUser;
    updateUserBadge();

    // Switch tab according to role
    if (role === 'Owner') switchTab('owner');
    else if (role === 'Admin') switchTab('admin');
    else switchTab('catalog');
}

function updateUserBadge() {
    const roleSpan = document.getElementById('current-user-role');
    const nameSpan = document.getElementById('current-user-name');
    if (roleSpan && nameSpan) {
        roleSpan.innerText = currentUser.role;
        nameSpan.innerText = currentUser.name;

        if (currentUser.role === 'Admin') {
            roleSpan.className = 'font-semibold text-purple-400';
        } else if (currentUser.role === 'Owner') {
            roleSpan.className = 'font-semibold text-emerald-400';
        } else {
            roleSpan.className = 'font-semibold text-blue-400';
        }
    }
    const ownerNameDisplay = document.getElementById('owner-name-display');
    if (ownerNameDisplay) ownerNameDisplay.innerText = currentUser.name;
}

// --- Tab Switching ---
function switchTab(tabId) {
    activeTab = tabId;
    ['catalog', 'ai', 'my-bookings', 'owner', 'admin'].forEach(t => {
        const sec = document.getElementById(`tab-${t}`);
        const nav = document.getElementById(`nav-${t}`);
        if (sec) sec.classList.toggle('hidden', t !== tabId);
        if (nav) nav.classList.toggle('active', t !== tabId);
    });

    if (tabId === 'catalog') loadVehicles();
    else if (tabId === 'ai') loadAIRecommendations();
    else if (tabId === 'my-bookings') loadClientBookings();
    else if (tabId === 'owner') loadOwnerPortal();
    else if (tabId === 'admin') loadAdminPortal();
}

// --- Categories ---
async function loadCategories() {
    try {
        const res = await fetch('/api/vehicles/categories');
        const data = await res.json();
        if (data.success) {
            allCategories = data.categories;
            const select = document.getElementById('filter-category');
            const addVehSelect = document.getElementById('add-veh-category');
            
            if (select) {
                select.innerHTML = '<option value="">All Categories</option>';
                data.categories.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c.category_id;
                    opt.textContent = c.category_name;
                    select.appendChild(opt);
                });
            }
            if (addVehSelect) {
                addVehSelect.innerHTML = '';
                data.categories.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c.category_id;
                    opt.textContent = c.category_name;
                    addVehSelect.appendChild(opt);
                });
            }
        }
    } catch (err) {
        console.error("Failed to load categories:", err);
    }
}

// --- Vehicles Catalog ---
async function loadVehicles(query = '') {
    const grid = document.getElementById('vehicle-grid');
    if (!grid) return;
    grid.innerHTML = '<div class="col-span-3 text-center py-12 text-slate-400"><i class="fa-solid fa-spinner fa-spin text-2xl mb-2"></i><p>Loading premium vehicles...</p></div>';

    try {
        const res = await fetch(`/api/vehicles${query}`);
        const data = await res.json();
        if (data.success && data.vehicles.length > 0) {
            grid.innerHTML = '';
            data.vehicles.forEach(v => {
                const isAvailable = v.availability === 'Available';
                
                // Parse 3D color
                let colorHex = '#c51111';
                try {
                    const viewObj = typeof v.vehicle_3d_view === 'string' ? JSON.parse(v.vehicle_3d_view) : v.vehicle_3d_view;
                    if (viewObj && viewObj.color) colorHex = viewObj.color;
                } catch(e){}

                const card = document.createElement('div');
                card.className = "bg-slate-800/80 border border-slate-700/60 rounded-2xl overflow-hidden shadow-xl hover:border-slate-600 transition flex flex-col group";
                card.innerHTML = `
                    <div class="relative h-48 overflow-hidden bg-slate-900">
                        <img src="${v.image_url}" alt="${v.vehicle_name}" class="w-full h-full object-cover group-hover:scale-105 transition duration-500">
                        <div class="absolute top-3 left-3 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-900/80 backdrop-blur border border-slate-700 text-indigo-300">
                            ${v.category_name}
                        </div>
                        <div class="absolute top-3 right-3 px-2.5 py-1 rounded-full text-[11px] font-semibold ${isAvailable ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'}">
                            ${v.availability}
                        </div>
                    </div>
                    <div class="p-5 flex-1 flex flex-col justify-between space-y-4">
                        <div class="space-y-2">
                            <div class="flex justify-between items-start">
                                <h3 class="font-bold text-white text-base group-hover:text-indigo-400 transition">${v.vehicle_name}</h3>
                                <div class="text-right">
                                    <span class="text-lg font-extrabold text-emerald-400">$${v.price_per_day}</span>
                                    <span class="text-[11px] text-slate-400">/day</span>
                                </div>
                            </div>
                            <div class="flex items-center space-x-3 text-xs text-slate-400">
                                <span><i class="fa-solid fa-location-dot text-indigo-400 mr-1"></i>${v.location}</span>
                                <span><i class="fa-solid fa-gauge-high text-indigo-400 mr-1"></i>${v.mileage.toLocaleString()} km</span>
                            </div>
                            <div class="flex items-center space-x-2 text-xs">
                                <div class="flex text-amber-400">
                                    ${getStarRatingHtml(v.avg_rating)}
                                </div>
                                <span class="font-bold text-slate-300">${v.avg_rating}</span>
                                <span class="text-slate-500">(${v.review_count} reviews)</span>
                            </div>
                        </div>

                        <div class="pt-2 border-t border-slate-700/60 flex items-center space-x-2">
                            <button onclick="open3DPreview('${v.vehicle_name.replace(/'/g, "\\'")}', '${colorHex}')" class="flex-1 bg-slate-700/80 hover:bg-slate-700 text-slate-200 text-xs font-semibold py-2 px-3 rounded-lg border border-slate-600 transition flex items-center justify-center space-x-1.5">
                                <i class="fa-solid fa-cube text-indigo-400"></i>
                                <span>3D View</span>
                            </button>
                            <button onclick="openCheckoutModal(${v.vehicle_id}, '${v.vehicle_name.replace(/'/g, "\\'")}', ${v.price_per_day}, '${v.image_url}')" 
                                    ${!isAvailable ? 'disabled' : ''}
                                    class="flex-1 ${isAvailable ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/30' : 'bg-slate-700 text-slate-500 cursor-not-allowed'} text-xs font-semibold py-2 px-3 rounded-lg transition flex items-center justify-center space-x-1.5">
                                <i class="fa-solid fa-key"></i>
                                <span>${isAvailable ? 'Book Now' : 'Reserved'}</span>
                            </button>
                        </div>
                    </div>
                `;
                grid.appendChild(card);
            });
        } else {
            grid.innerHTML = '<div class="col-span-3 text-center py-12 text-slate-400">No vehicles match your search criteria.</div>';
        }
    } catch (err) {
        console.error("Failed to load vehicles:", err);
    }
}

function getStarRatingHtml(rating) {
    let stars = '';
    for (let i = 1; i <= 5; i++) {
        if (rating >= i) stars += '<i class="fa-solid fa-star"></i>';
        else if (rating >= i - 0.5) stars += '<i class="fa-solid fa-star-half-stroke"></i>';
        else stars += '<i class="fa-regular fa-star text-slate-600"></i>';
    }
    return stars;
}

function applyFilters() {
    const search = document.getElementById('filter-search').value.trim();
    const cat = document.getElementById('filter-category').value;
    const maxPrice = document.getElementById('filter-price').value;

    let params = new URLSearchParams();
    if (search) params.append('search', search);
    if (cat) params.append('category_id', cat);
    if (maxPrice) params.append('price_max', maxPrice);

    loadVehicles(`?${params.toString()}`);
}

function resetFilters() {
    document.getElementById('filter-search').value = '';
    document.getElementById('filter-category').value = '';
    document.getElementById('filter-price').value = 300;
    document.getElementById('price-slider-val').innerText = '$300/day';
    loadVehicles();
}

// --- AI Recommendations ---
async function loadAIRecommendations() {
    const grid = document.getElementById('ai-recommendation-grid');
    if (!grid) return;
    grid.innerHTML = '<div class="col-span-3 text-center py-12 text-slate-400"><i class="fa-solid fa-brain fa-spin text-2xl text-violet-400 mb-2"></i><p>Computing personalized AI suggestions...</p></div>';

    try {
        const res = await fetch(`/api/ai/recommendations/${currentUser.user_id}?top_n=6`);
        const data = await res.json();
        if (data.success && data.recommendations.length > 0) {
            grid.innerHTML = '';
            data.recommendations.forEach(rec => {
                let colorHex = '#c51111';
                try {
                    const viewObj = typeof rec.vehicle_3d_view === 'string' ? JSON.parse(rec.vehicle_3d_view) : rec.vehicle_3d_view;
                    if (viewObj && viewObj.color) colorHex = viewObj.color;
                } catch(e){}

                const card = document.createElement('div');
                card.className = "bg-slate-800/80 border border-violet-500/30 hover:border-violet-500/70 rounded-2xl overflow-hidden shadow-xl transition flex flex-col relative";
                card.innerHTML = `
                    <div class="absolute top-3 left-3 z-10 px-3 py-1 rounded-full text-xs font-extrabold bg-violet-600 text-white shadow-lg shadow-violet-600/40 flex items-center space-x-1.5">
                        <i class="fa-solid fa-wand-magic-sparkles"></i>
                        <span>${rec.recommendation_score}% Match</span>
                    </div>

                    <div class="relative h-48 overflow-hidden bg-slate-900">
                        <img src="${rec.image_url}" alt="${rec.vehicle_name}" class="w-full h-full object-cover">
                    </div>

                    <div class="p-5 flex-1 flex flex-col justify-between space-y-4">
                        <div class="space-y-2">
                            <div class="flex justify-between items-start">
                                <div>
                                    <h3 class="font-bold text-white text-base">${rec.vehicle_name}</h3>
                                    <span class="text-xs text-indigo-400">${rec.category_name}</span>
                                </div>
                                <div class="text-right">
                                    <span class="text-lg font-extrabold text-emerald-400">$${rec.price_per_day}</span>
                                    <span class="text-[11px] text-slate-400">/day</span>
                                </div>
                            </div>

                            <!-- AI Reasoning Callout -->
                            <div class="bg-violet-950/40 border border-violet-800/50 p-2.5 rounded-xl text-xs text-violet-200 space-y-1">
                                <div class="font-semibold text-[10px] uppercase tracking-wider text-violet-400 flex items-center space-x-1">
                                    <i class="fa-solid fa-microchip"></i>
                                    <span>AI Match Rationale</span>
                                </div>
                                <p class="text-[11px] leading-snug">${rec.recommendation_reason}</p>
                            </div>
                        </div>

                        <div class="pt-2 border-t border-slate-700/60 flex items-center space-x-2">
                            <button onclick="open3DPreview('${rec.vehicle_name.replace(/'/g, "\\'")}', '${colorHex}')" class="flex-1 bg-slate-700/80 hover:bg-slate-700 text-slate-200 text-xs font-semibold py-2 px-3 rounded-lg border border-slate-600 transition flex items-center justify-center space-x-1">
                                <i class="fa-solid fa-cube text-indigo-400"></i>
                                <span>3D View</span>
                            </button>
                            <button onclick="openCheckoutModal(${rec.vehicle_id}, '${rec.vehicle_name.replace(/'/g, "\\'")}', ${rec.price_per_day}, '${rec.image_url}')" class="flex-1 bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold py-2 px-3 rounded-lg transition shadow-md shadow-violet-600/30 flex items-center justify-center space-x-1">
                                <i class="fa-solid fa-key"></i>
                                <span>Book Pick</span>
                            </button>
                        </div>
                    </div>
                `;
                grid.appendChild(card);
            });
        }
    } catch (err) {
        console.error("Failed to load AI picks:", err);
    }
}

// --- Client Bookings ---
async function loadClientBookings() {
    const list = document.getElementById('client-bookings-list');
    if (!list) return;
    list.innerHTML = '<div class="text-center py-12 text-slate-400"><i class="fa-solid fa-spinner fa-spin text-2xl mb-2"></i><p>Fetching your rental bookings...</p></div>';

    try {
        const res = await fetch(`/api/bookings?client_id=${currentUser.user_id}`);
        const data = await res.json();
        if (data.success && data.bookings.length > 0) {
            list.innerHTML = '';
            data.bookings.forEach(b => {
                const isActive = b.status === 'Active';
                const isCompleted = b.status === 'Completed';
                
                const card = document.createElement('div');
                card.className = "bg-slate-800/80 border border-slate-700/60 rounded-xl p-5 shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4";
                card.innerHTML = `
                    <div class="flex items-center space-x-4">
                        <img src="${b.image_url}" alt="${b.vehicle_name}" class="w-20 h-16 rounded-xl object-cover">
                        <div class="space-y-1">
                            <div class="flex items-center space-x-2">
                                <span class="font-bold text-white text-base">${b.vehicle_name}</span>
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                    isActive ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                                    isCompleted ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                                    'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                                }">${b.status}</span>
                            </div>
                            <div class="text-xs text-slate-400">
                                <span><i class="fa-regular fa-calendar mr-1"></i>${b.start_date} to ${b.end_date}</span>
                                <span class="ml-3"><i class="fa-solid fa-location-dot mr-1 text-indigo-400"></i>${b.location}</span>
                            </div>
                            <div class="text-xs text-slate-300">
                                Owner: <span class="text-slate-200 font-medium">${b.owner_name}</span> (${b.owner_phone})
                            </div>
                        </div>
                    </div>

                    <div class="flex flex-col sm:flex-row sm:items-center gap-3 border-t md:border-t-0 pt-3 md:pt-0 border-slate-700">
                        <div class="text-right">
                            <div class="text-base font-extrabold text-white">$${b.total_amount.toFixed(2)}</div>
                            <div class="text-[11px] text-slate-400">${b.payment_status ? 'Paid via ' + b.payment_method : 'Payment Pending'}</div>
                        </div>

                        <div class="flex items-center space-x-2">
                            ${isActive ? `
                                <button onclick="triggerReturnVehicle(${b.booking_id})" class="bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-md transition flex items-center space-x-1">
                                    <i class="fa-solid fa-arrow-right-arrow-left"></i>
                                    <span>Return Vehicle</span>
                                </button>
                            ` : ''}
                            ${isCompleted ? `
                                <button onclick="openReviewModal(${b.booking_id}, ${b.vehicle_id})" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-md transition flex items-center space-x-1">
                                    <i class="fa-regular fa-star"></i>
                                    <span>Leave Review</span>
                                </button>
                            ` : ''}
                        </div>
                    </div>
                `;
                list.appendChild(card);
            });
        } else {
            list.innerHTML = '<div class="text-center py-12 text-slate-400">You currently have no active or previous bookings.</div>';
        }
    } catch (err) {
        console.error("Failed to load client bookings:", err);
    }
}

// --- Checkout Modal & Flow ---
function openCheckoutModal(vehicleId, vehicleName, pricePerDay, imgUrl) {
    document.getElementById('checkout-vehicle-id').value = vehicleId;
    document.getElementById('checkout-price-per-day').value = pricePerDay;
    document.getElementById('checkout-car-name').innerText = vehicleName;
    document.getElementById('checkout-car-rate').innerText = `$${pricePerDay.toFixed(2)} / day`;
    document.getElementById('checkout-car-img').src = imgUrl;

    calculateCheckoutTotal();
    document.getElementById('modal-checkout').classList.remove('hidden');
}

function closeCheckoutModal() {
    document.getElementById('modal-checkout').classList.add('hidden');
}

function calculateCheckoutTotal() {
    const startStr = document.getElementById('checkout-start-date').value;
    const endStr = document.getElementById('checkout-end-date').value;
    const pricePerDay = parseFloat(document.getElementById('checkout-price-per-day').value || 0);

    if (!startStr || !endStr) return;

    const s = new Date(startStr);
    const e = new Date(endStr);
    let diffDays = Math.ceil((e - s) / (1000 * 60 * 60 * 24));
    if (diffDays <= 0) diffDays = 1;

    const total = diffDays * pricePerDay;
    document.getElementById('summary-days').innerText = `${diffDays} day(s)`;
    document.getElementById('summary-daily-rate').innerText = `$${pricePerDay.toFixed(2)}`;
    document.getElementById('summary-total').innerText = `$${total.toFixed(2)}`;
}

async function processBookingCheckout(event) {
    event.preventDefault();
    const btn = document.getElementById('btn-pay-confirm');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i> Authorizing Transaction...';

    const vehicleId = document.getElementById('checkout-vehicle-id').value;
    const startDate = document.getElementById('checkout-start-date').value;
    const endDate = document.getElementById('checkout-end-date').value;
    const payMethod = document.querySelector('input[name="pay-method"]:checked').value;

    try {
        // 1. Create Booking
        const bookRes = await fetch('/api/bookings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                client_id: currentUser.user_id,
                vehicle_id: parseInt(vehicleId),
                start_date: startDate,
                end_date: endDate
            })
        });
        const bookData = await bookRes.json();
        if (!bookData.success) throw new Error(bookData.error || "Booking failed");

        // 2. Process Digital Payment
        const payRes = await fetch('/api/payments/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                booking_id: bookData.booking_id,
                amount: bookData.total_amount,
                payment_method: payMethod
            })
        });
        const payData = await payRes.json();
        if (!payData.success) throw new Error(payData.error || "Payment failed");

        alert(`🎉 Booking Confirmed!\nTransaction ID: ${payData.transaction_id}\nYour vehicle is reserved.`);
        closeCheckoutModal();
        switchTab('my-bookings');
    } catch (err) {
        alert(`Error: ${err.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-lock mr-2"></i> Pay & Authorize Booking';
    }
}

// --- Return Vehicle & Fine Calculation ---
async function triggerReturnVehicle(bookingId) {
    if (!confirm("Confirm vehicle drop-off and return? This will calculate any overdue fine if past return date.")) return;

    try {
        const res = await fetch(`/api/bookings/${bookingId}/return`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        const data = await res.json();
        if (data.success) {
            let msg = "Vehicle returned successfully!";
            if (data.fine_details && data.fine_details.is_overdue) {
                msg += `\n⚠️ Overdue Fine Assessed: $${data.fine_details.fine_amount}\nReason: ${data.fine_details.reason}`;
            }
            alert(msg);
            loadClientBookings();
            loadVehicles();
        }
    } catch (err) {
        alert("Failed to return vehicle: " + err);
    }
}

// --- Review Modal ---
function openReviewModal(bookingId, vehicleId) {
    document.getElementById('review-booking-id').value = bookingId;
    document.getElementById('review-vehicle-id').value = vehicleId;
    setRating(5);
    document.getElementById('modal-review').classList.remove('hidden');
}

function closeReviewModal() {
    document.getElementById('modal-review').classList.add('hidden');
}

function setRating(val) {
    document.getElementById('review-rating-val').value = val;
    const stars = document.querySelectorAll('#star-picker i');
    stars.forEach(s => {
        const v = parseInt(s.getAttribute('data-val'));
        s.className = v <= val ? 'fa-solid fa-star' : 'fa-regular fa-star text-slate-600';
    });
}

async function handleReviewSubmit(e) {
    e.preventDefault();
    const bookingId = document.getElementById('review-booking-id').value;
    const vehicleId = document.getElementById('review-vehicle-id').value;
    const rating = document.getElementById('review-rating-val').value;
    const reviewText = document.getElementById('review-text').value.trim();

    try {
        const res = await fetch('/api/reviews', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                client_id: currentUser.user_id,
                vehicle_id: parseInt(vehicleId),
                booking_id: parseInt(bookingId),
                rating: parseInt(rating),
                review_text: reviewText
            })
        });
        const data = await res.json();
        if (data.success) {
            alert("🌟 Review submitted! Thank you.");
            closeReviewModal();
            loadClientBookings();
        } else {
            alert(data.error || "Review submission failed");
        }
    } catch (err) {
        alert("Error: " + err);
    }
}

// --- Owner Portal Controller ---
async function loadOwnerPortal() {
    const ownerId = currentUser.user_id;

    // 1. Fetch Fleet
    const res = await fetch(`/api/vehicles?owner_id=${ownerId}`);
    const data = await res.json();
    const fleet = data.vehicles || [];

    // 2. Fetch Bookings for Revenue & Active counts
    const bRes = await fetch(`/api/bookings?owner_id=${ownerId}`);
    const bData = await bRes.json();
    const bookings = bData.bookings || [];

    // 3. Fetch Maintenance Alerts
    const mRes = await fetch(`/api/maintenance/owner/${ownerId}/alerts`);
    const mData = await mRes.json();
    const alerts = mData.alerts || [];

    // 4. Update KPI stats
    document.getElementById('owner-stat-fleet').innerText = fleet.length;
    const activeCount = bookings.filter(b => b.status === 'Active').length;
    document.getElementById('owner-stat-active').innerText = activeCount;
    
    const overdueAlerts = alerts.filter(a => a.is_alert_triggered).length;
    document.getElementById('owner-stat-maintenance').innerText = overdueAlerts;

    const totalRev = bookings
        .filter(b => b.payment_status === 'Completed')
        .reduce((sum, b) => sum + b.total_amount, 0);
    document.getElementById('owner-stat-revenue').innerText = `$${totalRev.toFixed(2)}`;

    // Render Fleet Table
    renderOwnerFleetTable(fleet);
    renderOwnerMaintenance(alerts);
    renderOwnerFines(ownerId);

    // Initialize/Update GPS Map
    const gpsRes = await fetch(`/api/gps/owner/${ownerId}/fleet`);
    const gpsData = await gpsRes.json();
    if (gpsData.success) {
        updateFleetMap(gpsData.fleet);
    }
}

function renderOwnerFleetTable(fleet) {
    const container = document.getElementById('owner-vehicle-table');
    if (!container) return;

    if (fleet.length === 0) {
        container.innerHTML = '<div class="text-center py-6 text-slate-400">No vehicles registered yet. Click "Add New Vehicle" to publish your first car.</div>';
        return;
    }

    let html = `
        <table class="w-full text-left text-xs text-slate-300">
            <thead class="text-[11px] text-slate-400 uppercase bg-slate-900/60 border-b border-slate-700">
                <tr>
                    <th class="py-3 px-4">Vehicle</th>
                    <th class="py-3 px-4">Category</th>
                    <th class="py-3 px-4">Rate / Day</th>
                    <th class="py-3 px-4">Odometer</th>
                    <th class="py-3 px-4">GPS Device</th>
                    <th class="py-3 px-4">Status</th>
                    <th class="py-3 px-4 text-right">Actions</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
    `;

    fleet.forEach(v => {
        html += `
            <tr class="hover:bg-slate-800/40 transition">
                <td class="py-3 px-4 font-bold text-white flex items-center space-x-2">
                    <img src="${v.image_url}" class="w-8 h-8 rounded object-cover">
                    <span>${v.vehicle_name}</span>
                </td>
                <td class="py-3 px-4">${v.category_name}</td>
                <td class="py-3 px-4 text-emerald-400 font-bold">$${v.price_per_day.toFixed(2)}</td>
                <td class="py-3 px-4">${v.mileage.toLocaleString()} km</td>
                <td class="py-3 px-4 text-indigo-400 font-mono text-[11px]">${v.gps_device_id || 'N/A'}</td>
                <td class="py-3 px-4">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold ${v.availability === 'Available' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}">${v.availability}</span>
                </td>
                <td class="py-3 px-4 text-right space-x-2">
                    <button onclick="simulateOdometerDrive(${v.vehicle_id}, ${v.mileage})" class="text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 px-2 py-1 rounded" title="Simulate +500km Drive">
                        <i class="fa-solid fa-road"></i> +500km
                    </button>
                    <button onclick="deleteVehicle(${v.vehicle_id})" class="text-xs text-rose-400 hover:text-rose-300 px-2 py-1 rounded">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });

    html += `</tbody></table>`;
    container.innerHTML = html;
}

function renderOwnerMaintenance(alerts) {
    const container = document.getElementById('maintenance-alert-list');
    if (!container) return;

    container.innerHTML = '';
    alerts.forEach(a => {
        const isOverdue = a.alert_status === 'OVERDUE';
        const isWarning = a.alert_status === 'WARNING';

        const card = document.createElement('div');
        card.className = `p-4 rounded-xl border ${
            isOverdue ? 'bg-rose-950/30 border-rose-600/50' :
            isWarning ? 'bg-amber-950/30 border-amber-600/50' :
            'bg-slate-800/60 border-slate-700/50'
        } space-y-3`;

        const progressPct = Math.min(100, Math.round((a.current_km / a.next_service_km) * 100));

        card.innerHTML = `
            <div class="flex justify-between items-start">
                <div>
                    <h4 class="font-bold text-white text-sm">${a.vehicle_name}</h4>
                    <span class="text-xs text-slate-400">Vehicle ID: #${a.vehicle_id}</span>
                </div>
                <span class="px-2.5 py-1 rounded-full text-[10px] font-bold ${
                    isOverdue ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' :
                    isWarning ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' :
                    'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                }">${a.alert_status}</span>
            </div>

            <div class="space-y-1">
                <div class="flex justify-between text-xs text-slate-300">
                    <span>Odometer: <strong class="text-white">${a.current_km.toLocaleString()} km</strong></span>
                    <span>Service Limit: <strong>${a.next_service_km.toLocaleString()} km</strong></span>
                </div>
                <div class="w-full bg-slate-900 rounded-full h-2 overflow-hidden">
                    <div class="${isOverdue ? 'bg-rose-500' : isWarning ? 'bg-amber-500' : 'bg-emerald-500'} h-2 rounded-full" style="width: ${progressPct}%"></div>
                </div>
                <div class="text-[11px] text-slate-400 flex justify-between">
                    <span>${a.remaining_km > 0 ? `${a.remaining_km.toLocaleString()} km until service` : `Overdue by ${Math.abs(a.remaining_km).toLocaleString()} km`}</span>
                    <span>${progressPct}% usage</span>
                </div>
            </div>

            <div class="pt-2 border-t border-slate-700/60 flex justify-end">
                <button onclick="logServiceComplete(${a.vehicle_id}, ${a.current_km})" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-3 py-1.5 rounded-lg flex items-center space-x-1.5 transition">
                    <i class="fa-solid fa-check"></i>
                    <span>Log Service Completed</span>
                </button>
            </div>
        `;
        container.appendChild(card);
    });
}

async function renderOwnerFines(ownerId) {
    const container = document.getElementById('owner-fines-table');
    if (!container) return;

    const res = await fetch(`/api/fines?owner_id=${ownerId}`);
    const data = await res.json();
    const fines = data.fines || [];

    if (fines.length === 0) {
        container.innerHTML = '<div class="text-center py-6 text-slate-400">No overdue penalties or fines recorded.</div>';
        return;
    }

    let html = `
        <table class="w-full text-left text-xs text-slate-300">
            <thead class="text-[11px] text-slate-400 uppercase bg-slate-900/60 border-b border-slate-700">
                <tr>
                    <th class="py-3 px-4">Booking #</th>
                    <th class="py-3 px-4">Client</th>
                    <th class="py-3 px-4">Vehicle</th>
                    <th class="py-3 px-4">Fine Amount</th>
                    <th class="py-3 px-4">Reason</th>
                    <th class="py-3 px-4">Status</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
    `;
    fines.forEach(f => {
        html += `
            <tr class="hover:bg-slate-800/40">
                <td class="py-3 px-4 font-mono text-indigo-400">#${f.booking_id}</td>
                <td class="py-3 px-4 font-medium text-white">${f.client_name}</td>
                <td class="py-3 px-4">${f.vehicle_name}</td>
                <td class="py-3 px-4 text-rose-400 font-bold">$${f.fine_amount.toFixed(2)}</td>
                <td class="py-3 px-4 text-slate-400">${f.reason}</td>
                <td class="py-3 px-4">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold ${f.payment_status === 'Paid' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}">${f.payment_status}</span>
                </td>
            </tr>
        `;
    });
    html += `</tbody></table>`;
    container.innerHTML = html;
}

function switchOwnerSubtab(sub) {
    ['fleet', 'gps', 'maintenance', 'fines'].forEach(s => {
        const view = document.getElementById(`owner-view-${s}`);
        const btn = document.getElementById(`owner-subtab-${s}`);
        if (view) view.classList.toggle('hidden', s !== sub);
        if (btn) btn.classList.toggle('active', s === sub);
    });

    if (sub === 'gps') {
        setTimeout(() => {
            initGPSMap();
            if (map) map.invalidateSize();
        }, 150);
    }
}

async function simulateOdometerDrive(vehicleId, currentKm) {
    const newKm = currentKm + 500;
    try {
        const res = await fetch('/api/maintenance/odometer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vehicle_id: vehicleId, mileage: newKm })
        });
        const data = await res.json();
        if (data.success) {
            loadOwnerPortal();
        }
    } catch (err) {
        console.error("Failed to update odometer:", err);
    }
}

async function logServiceComplete(vehicleId, currentKm) {
    try {
        const res = await fetch('/api/maintenance/service', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                vehicle_id: vehicleId,
                service_type: 'Full Maintenance & Oil Service',
                current_km: currentKm,
                next_service_interval_km: 10000
            })
        });
        const data = await res.json();
        if (data.success) {
            alert("✅ Maintenance logged! Next service milestone established.");
            loadOwnerPortal();
        }
    } catch (err) {
        alert("Error: " + err);
    }
}

function openAddVehicleModal() {
    document.getElementById('modal-vehicle').classList.remove('hidden');
}

function closeAddVehicleModal() {
    document.getElementById('modal-vehicle').classList.add('hidden');
}

async function handleAddVehicleSubmit(e) {
    e.preventDefault();
    const name = document.getElementById('add-veh-name').value.trim();
    const categoryId = document.getElementById('add-veh-category').value;
    const price = document.getElementById('add-veh-price').value;
    const mileage = document.getElementById('add-veh-mileage').value;
    const gpsId = document.getElementById('add-veh-gps').value.trim();
    const location = document.getElementById('add-veh-location').value.trim();
    const imgUrl = document.getElementById('add-veh-image').value.trim();

    try {
        const res = await fetch('/api/vehicles', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                owner_id: currentUser.user_id,
                category_id: parseInt(categoryId),
                vehicle_name: name,
                price_per_day: parseFloat(price),
                mileage: parseInt(mileage),
                gps_device_id: gpsId || `GPS-${name.slice(0, 3).toUpperCase()}-101`,
                location: location,
                image_url: imgUrl || 'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=800&q=80'
            })
        });
        const data = await res.json();
        if (data.success) {
            alert("🚗 Vehicle published to fleet!");
            closeAddVehicleModal();
            loadOwnerPortal();
            loadVehicles();
        }
    } catch (err) {
        alert("Error: " + err);
    }
}

async function deleteVehicle(vehId) {
    if (!confirm("Are you sure you want to remove this vehicle from your fleet?")) return;
    try {
        const res = await fetch(`/api/vehicles/${vehId}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            loadOwnerPortal();
            loadVehicles();
        }
    } catch (err) {
        alert("Error: " + err);
    }
}

// --- Administrator Portal ---
async function loadAdminPortal() {
    // 1. Stats
    const sRes = await fetch('/api/admin/stats');
    const sData = await sRes.json();
    if (sData.success) {
        const m = sData.metrics;
        document.getElementById('admin-stat-users').innerText = m.total_users;
        document.getElementById('admin-stat-vehicles').innerText = m.total_vehicles;
        document.getElementById('admin-stat-revenue').innerText = `$${m.total_revenue.toFixed(2)}`;
        document.getElementById('admin-stat-fines').innerText = `$${m.total_fines_collected.toFixed(2)}`;
    }

    // 2. Load Users Table
    const uRes = await fetch('/api/admin/users');
    const uData = await uRes.json();
    if (uData.success) {
        renderAdminUsers(uData.users);
    }

    // 3. Load Categories
    renderAdminCategories(allCategories);

    // 4. Load Logs
    const lRes = await fetch('/api/admin/logs');
    const lData = await lRes.json();
    if (lData.success) {
        renderAdminLogs(lData.recent_bookings, lData.recent_payments);
    }
}

function switchAdminSubtab(sub) {
    ['users', 'categories', 'logs'].forEach(s => {
        const view = document.getElementById(`admin-view-${s}`);
        const btn = document.getElementById(`admin-subtab-${s}`);
        if (view) view.classList.toggle('hidden', s !== sub);
        if (btn) btn.classList.toggle('active', s === sub);
    });
}

function renderAdminUsers(users) {
    const container = document.getElementById('admin-users-table');
    if (!container) return;

    let html = `
        <table class="w-full text-left text-xs text-slate-300">
            <thead class="text-[11px] text-slate-400 uppercase bg-slate-900/60 border-b border-slate-700">
                <tr>
                    <th class="py-3 px-4">User ID</th>
                    <th class="py-3 px-4">Name</th>
                    <th class="py-3 px-4">Email</th>
                    <th class="py-3 px-4">Phone</th>
                    <th class="py-3 px-4">Role</th>
                    <th class="py-3 px-4 text-right">Actions</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
    `;

    users.forEach(u => {
        html += `
            <tr class="hover:bg-slate-800/40">
                <td class="py-3 px-4 font-mono text-slate-400">#${u.user_id}</td>
                <td class="py-3 px-4 font-bold text-white">${u.name}</td>
                <td class="py-3 px-4">${u.email}</td>
                <td class="py-3 px-4 text-slate-400">${u.phone}</td>
                <td class="py-3 px-4">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold ${
                        u.role === 'Admin' ? 'bg-purple-500/20 text-purple-300' :
                        u.role === 'Owner' ? 'bg-emerald-500/20 text-emerald-300' :
                        'bg-blue-500/20 text-blue-300'
                    }">${u.role}</span>
                </td>
                <td class="py-3 px-4 text-right">
                    <button onclick="deleteUserAccount(${u.user_id})" class="text-rose-400 hover:text-rose-300 text-xs px-2 py-1">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    html += `</tbody></table>`;
    container.innerHTML = html;
}

function renderAdminCategories(categories) {
    const container = document.getElementById('admin-categories-table');
    if (!container) return;

    let html = `
        <table class="w-full text-left text-xs text-slate-300">
            <thead class="text-[11px] text-slate-400 uppercase bg-slate-900/60 border-b border-slate-700">
                <tr>
                    <th class="py-3 px-4">ID</th>
                    <th class="py-3 px-4">Category Name</th>
                    <th class="py-3 px-4">Description</th>
                    <th class="py-3 px-4 text-right">Action</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
    `;
    categories.forEach(c => {
        html += `
            <tr class="hover:bg-slate-800/40">
                <td class="py-3 px-4 font-mono text-slate-400">#${c.category_id}</td>
                <td class="py-3 px-4 font-bold text-white">${c.category_name}</td>
                <td class="py-3 px-4 text-slate-400">${c.description || 'N/A'}</td>
                <td class="py-3 px-4 text-right">
                    <button onclick="deleteCategory(${c.category_id})" class="text-rose-400 hover:text-rose-300 text-xs px-2 py-1">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    html += `</tbody></table>`;
    container.innerHTML = html;
}

function renderAdminLogs(bookings, payments) {
    const container = document.getElementById('admin-logs-table');
    if (!container) return;

    let html = `
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div class="bg-slate-900/80 p-4 rounded-xl border border-slate-800 space-y-2">
                <h4 class="font-bold text-white text-xs uppercase tracking-wider text-indigo-400">Recent Booking Logs</h4>
                <div class="divide-y divide-slate-800 text-xs">
                    ${bookings.map(b => `
                        <div class="py-2 flex justify-between items-center">
                            <div>
                                <span class="font-medium text-slate-200">${b.client_name}</span> rented <strong class="text-white">${b.vehicle_name}</strong>
                                <div class="text-[10px] text-slate-500">${b.booking_date}</div>
                            </div>
                            <span class="text-emerald-400 font-bold">$${b.total_amount.toFixed(2)}</span>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="bg-slate-900/80 p-4 rounded-xl border border-slate-800 space-y-2">
                <h4 class="font-bold text-white text-xs uppercase tracking-wider text-emerald-400">Payment Gateway Audit Log</h4>
                <div class="divide-y divide-slate-800 text-xs">
                    ${payments.map(p => `
                        <div class="py-2 flex justify-between items-center">
                            <div>
                                <div class="font-mono text-[11px] text-indigo-300">${p.transaction_id}</div>
                                <div class="text-[10px] text-slate-400">${p.payment_method} • ${p.payment_date}</div>
                            </div>
                            <span class="text-emerald-400 font-bold">+$${p.amount.toFixed(2)}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
    container.innerHTML = html;
}

async function deleteUserAccount(userId) {
    if (!confirm("Are you sure you want to remove this user?")) return;
    try {
        const res = await fetch(`/api/admin/users/${userId}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) loadAdminPortal();
    } catch (err) {
        alert("Error: " + err);
    }
}

async function deleteCategory(catId) {
    if (!confirm("Delete category? (Must not have existing vehicles assigned)")) return;
    try {
        const res = await fetch(`/api/admin/categories/${catId}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            await loadCategories();
            loadAdminPortal();
        } else {
            alert(data.error);
        }
    } catch (err) {
        alert("Error: " + err);
    }
}

function openAddCategoryModal() {
    const name = prompt("Enter new vehicle category name:");
    if (!name) return;
    const desc = prompt("Enter category description:");

    fetch('/api/admin/categories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category_name: name, description: desc })
    }).then(r => r.json()).then(async d => {
        if (d.success) {
            await loadCategories();
            loadAdminPortal();
        } else {
            alert(d.error);
        }
    });
}

function openAddUserModal() {
    const name = prompt("User full name:");
    if (!name) return;
    const email = prompt("User email address:");
    const phone = prompt("Phone number:");
    const role = prompt("Role (Admin, Owner, Client):", "Client");
    const password = prompt("Temporary password:", "user123");

    fetch('/api/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, phone, role, password })
    }).then(r => r.json()).then(d => {
        if (d.success) loadAdminPortal();
        else alert(d.error);
    });
}
