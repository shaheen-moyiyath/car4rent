// Three.js Interactive 3D Vehicle Inspector Module

let scene, camera, renderer, controls, carGroup, bodyMaterial;
let isWireframe = false;

function init3DViewer() {
    const canvas = document.getElementById('threejs-canvas');
    if (!canvas) return;

    const width = canvas.parentElement.clientWidth || 800;
    const height = canvas.parentElement.clientHeight || 450;

    // 1. Scene setup
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0f1d);

    // 2. Camera setup
    camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(5, 3, 5);

    // 3. Renderer setup
    renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;

    // 4. Orbit Controls
    if (window.THREE.OrbitControls) {
        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.maxPolarAngle = Math.PI / 2 - 0.02; // Prevent going below floor
        controls.minDistance = 3;
        controls.maxDistance = 15;
    }

    // 5. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight1.position.set(6, 10, 6);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x6366f1, 0.6);
    dirLight2.position.set(-6, 5, -6);
    scene.add(dirLight2);

    // 6. Ground Grid & Shadow Plane
    const grid = new THREE.GridHelper(20, 20, 0x4f46e5, 0x1e293b);
    grid.position.y = -0.01;
    scene.add(grid);

    // 7. Car Geometry Builder
    buildProceduralCar('#c51111');

    // 8. Event Listeners
    const colorPicker = document.getElementById('car-color-picker');
    if (colorPicker) {
        colorPicker.addEventListener('input', (e) => {
            if (bodyMaterial) {
                bodyMaterial.color.set(e.target.value);
            }
        });
    }

    window.addEventListener('resize', onWindowResize);

    // 9. Animation loop
    animate();
}

function buildProceduralCar(initialColor) {
    if (carGroup) scene.remove(carGroup);
    carGroup = new THREE.Group();

    // Body Material
    bodyMaterial = new THREE.MeshStandardMaterial({
        color: initialColor,
        metalness: 0.85,
        roughness: 0.2,
        wireframe: isWireframe
    });

    // Glass Material
    const glassMaterial = new THREE.MeshStandardMaterial({
        color: 0x111827,
        metalness: 0.9,
        roughness: 0.1,
        transparent: true,
        opacity: 0.85
    });

    // Wheel Material
    const wheelMaterial = new THREE.MeshStandardMaterial({
        color: 0x1f2937,
        roughness: 0.8
    });
    const rimMaterial = new THREE.MeshStandardMaterial({
        color: 0xe2e8f0,
        metalness: 0.9,
        roughness: 0.1
    });

    // --- 1. Lower Chassis / Base ---
    const baseGeo = new THREE.BoxGeometry(3.6, 0.55, 1.7);
    const baseMesh = new THREE.Mesh(baseGeo, bodyMaterial);
    baseMesh.position.y = 0.55;
    carGroup.add(baseMesh);

    // --- 2. Cabin / Roof ---
    const cabinGeo = new THREE.BoxGeometry(2.0, 0.55, 1.4);
    const cabinMesh = new THREE.Mesh(cabinGeo, glassMaterial);
    cabinMesh.position.set(-0.2, 1.05, 0);
    carGroup.add(cabinMesh);

    // Roof Top
    const roofGeo = new THREE.BoxGeometry(1.9, 0.08, 1.38);
    const roofMesh = new THREE.Mesh(roofGeo, bodyMaterial);
    roofMesh.position.set(-0.2, 1.34, 0);
    carGroup.add(roofMesh);

    // --- 3. Headlights & Taillights ---
    const lightGeo = new THREE.BoxGeometry(0.1, 0.15, 0.35);
    const headLightMat = new THREE.MeshBasicMaterial({ color: 0x60a5fa });
    const tailLightMat = new THREE.MeshBasicMaterial({ color: 0xef4444 });

    const flLight = new THREE.Mesh(lightGeo, headLightMat);
    flLight.position.set(1.8, 0.65, 0.55);
    const frLight = new THREE.Mesh(lightGeo, headLightMat);
    frLight.position.set(1.8, 0.65, -0.55);
    carGroup.add(flLight, frLight);

    const rlLight = new THREE.Mesh(lightGeo, tailLightMat);
    rlLight.position.set(-1.8, 0.65, 0.55);
    const rrLight = new THREE.Mesh(lightGeo, tailLightMat);
    rrLight.position.set(-1.8, 0.65, -0.55);
    carGroup.add(rlLight, rrLight);

    // --- 4. Wheels ---
    const wheelGeo = new THREE.CylinderGeometry(0.38, 0.38, 0.28, 24);
    wheelGeo.rotateX(Math.PI / 2);
    const rimGeo = new THREE.CylinderGeometry(0.24, 0.24, 0.29, 12);
    rimGeo.rotateX(Math.PI / 2);

    const wheelPositions = [
        [1.15, 0.38, 0.85],
        [1.15, 0.38, -0.85],
        [-1.15, 0.38, 0.85],
        [-1.15, 0.38, -0.85]
    ];

    wheelPositions.forEach(pos => {
        const tire = new THREE.Mesh(wheelGeo, wheelMaterial);
        tire.position.set(...pos);
        const rim = new THREE.Mesh(rimGeo, rimMaterial);
        rim.position.set(...pos);
        carGroup.add(tire, rim);
    });

    scene.add(carGroup);
}

function toggle3DWireframe() {
    isWireframe = !isWireframe;
    if (bodyMaterial) {
        bodyMaterial.wireframe = isWireframe;
    }
    const btn = document.getElementById('btn-wireframe');
    if (btn) {
        btn.classList.toggle('text-indigo-400', isWireframe);
    }
}

function reset3DCamera() {
    if (camera && controls) {
        camera.position.set(5, 3, 5);
        controls.target.set(0, 0.6, 0);
        controls.update();
    }
}

function open3DPreview(vehicleName, colorHex) {
    const modal = document.getElementById('modal-3d');
    const title = document.getElementById('modal-3d-title');
    const picker = document.getElementById('car-color-picker');

    if (modal) modal.classList.remove('hidden');
    if (title) title.innerText = `3D Inspection: ${vehicleName}`;
    if (picker) picker.value = colorHex || '#c51111';

    if (!scene) {
        setTimeout(init3DViewer, 100);
    } else {
        if (bodyMaterial) {
            bodyMaterial.color.set(colorHex || '#c51111');
        }
        reset3DCamera();
    }
}

function close3DModal() {
    const modal = document.getElementById('modal-3d');
    if (modal) modal.classList.add('hidden');
}

function onWindowResize() {
    const canvas = document.getElementById('threejs-canvas');
    if (!canvas || !camera || !renderer) return;
    const width = canvas.parentElement.clientWidth || 800;
    const height = canvas.parentElement.clientHeight || 450;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
}

function animate() {
    requestAnimationFrame(animate);
    if (controls) controls.update();
    if (renderer && scene && camera) {
        renderer.render(scene, camera);
    }
}
