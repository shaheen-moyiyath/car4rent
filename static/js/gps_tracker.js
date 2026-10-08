// Leaflet.js Open-Source GPS Fleet Tracking Module

let map, markersGroup, polylineTrail;
let currentFleetData = [];
let trackedVehicleId = null;

function initGPSMap() {
    const mapContainer = document.getElementById('gps-map');
    if (!mapContainer || map) return;

    // Default center (San Francisco coordinate grid)
    map = L.map('gps-map', {
        zoomControl: true,
        attributionControl: false
    }).setView([37.7749, -122.4194], 13);

    // Open-source CartoDB Dark Matter tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        subdomains: 'abcd'
    }).addTo(map);

    markersGroup = L.layerGroup().addTo(map);
    polylineTrail = L.polyline([], { color: '#6366f1', weight: 4, opacity: 0.8, dashArray: '5, 10' }).addTo(map);
}

function updateFleetMap(fleetList) {
    if (!map) initGPSMap();
    if (!map) return;

    currentFleetData = fleetList;
    markersGroup.clearLayers();

    // Populate dropdown
    const select = document.getElementById('gps-vehicle-select');
    if (select && select.children.length <= 1) {
        select.innerHTML = '<option value="">Track Whole Fleet</option>';
        fleetList.forEach(v => {
            const opt = document.createElement('option');
            opt.value = v.vehicle_id;
            opt.textContent = `${v.vehicle_name} (${v.gps_device_id})`;
            select.appendChild(opt);
        });
    }

    const latLngs = [];

    fleetList.forEach(v => {
        const lat = v.latitude;
        const lng = v.longitude;
        latLngs.push([lat, lng]);

        // Create Custom HTML Marker with Pulse Effect
        const isMoving = v.speed > 5;
        const markerHtml = `
            <div class="relative flex items-center justify-center">
                <div class="w-8 h-8 rounded-full ${isMoving ? 'bg-emerald-500' : 'bg-indigo-600'} text-white flex items-center justify-center text-xs shadow-lg border-2 border-slate-900">
                    <i class="fa-solid fa-car"></i>
                </div>
                ${isMoving ? '<span class="absolute -inset-1 rounded-full bg-emerald-400 opacity-75 animate-ping"></span>' : ''}
            </div>
        `;

        const customIcon = L.divIcon({
            html: markerHtml,
            className: 'custom-car-marker',
            iconSize: [32, 32],
            iconAnchor: [16, 16]
        });

        const marker = L.marker([lat, lng], { icon: customIcon });
        
        const popupContent = `
            <div class="p-2 space-y-1 text-xs">
                <div class="font-bold text-white">${v.vehicle_name}</div>
                <div class="text-slate-300">GPS ID: <span class="text-indigo-400">${v.gps_device_id}</span></div>
                <div class="text-slate-300">Speed: <span class="font-semibold text-emerald-400">${v.speed} km/h</span></div>
                <div class="text-slate-400 text-[10px]">Status: ${v.availability}</div>
            </div>
        `;
        marker.bindPopup(popupContent);
        markersGroup.addLayer(marker);
    });

    if (latLngs.length > 0 && !trackedVehicleId) {
        map.fitBounds(latLngs, { padding: [50, 50], maxZoom: 14 });
    }
}

function focusVehicleOnMap() {
    const select = document.getElementById('gps-vehicle-select');
    const vehId = select.value ? parseInt(select.value) : null;
    trackedVehicleId = vehId;

    if (!vehId) {
        // Reset to all fleet
        const latLngs = currentFleetData.map(v => [v.latitude, v.longitude]);
        if (latLngs.length > 0) map.fitBounds(latLngs, { padding: [50, 50] });
        document.getElementById('live-speed-display').innerHTML = `0.0 <span class="text-xs font-normal text-slate-400">km/h</span>`;
        document.getElementById('live-device-display').innerText = 'Device: Whole Fleet';
        polylineTrail.setLatLngs([]);
        return;
    }

    const veh = currentFleetData.find(v => v.vehicle_id === vehId);
    if (veh) {
        map.flyTo([veh.latitude, veh.longitude], 16, { duration: 1.2 });
        document.getElementById('live-speed-display').innerHTML = `${veh.speed} <span class="text-xs font-normal text-slate-400">km/h</span>`;
        document.getElementById('live-device-display').innerText = `Device: ${veh.gps_device_id}`;
        
        // Fetch route history
        fetch(`/api/gps/vehicle/${vehId}/history`)
            .then(res => res.json())
            .then(data => {
                if (data.success && data.history) {
                    const trail = data.history.map(h => [h.latitude, h.longitude]);
                    polylineTrail.setLatLngs(trail);
                }
            });
    }
}

async function simulateVehicleMovement() {
    const select = document.getElementById('gps-vehicle-select');
    const vehId = select && select.value ? select.value : (currentFleetData[0] ? currentFleetData[0].vehicle_id : 1);

    try {
        const res = await fetch(`/api/gps/vehicle/${vehId}/simulate-step`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            // Update owner fleet
            const ownerId = window.currentUser ? window.currentUser.user_id : 2;
            const fleetRes = await fetch(`/api/gps/owner/${ownerId}/fleet`);
            const fleetJson = await fleetRes.json();
            if (fleetJson.success) {
                updateFleetMap(fleetJson.fleet);
                if (trackedVehicleId) {
                    focusVehicleOnMap();
                }
            }
        }
    } catch (err) {
        console.error("Simulation error:", err);
    }
}
