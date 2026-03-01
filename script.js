// ==========================================
// BoneScan AI — Enhanced Script
// ==========================================

const fileInput = document.getElementById('file-input');
const dropZone = document.getElementById('drop-zone');
const fileName = document.getElementById('file-name');
const uploadSection = document.getElementById('upload-section');
const loadingOverlay = document.getElementById('loading-overlay');
const resultsSection = document.getElementById('results-section');
const imagePreview = document.getElementById('image-preview');
const detectionBox = document.getElementById('detection-box');
const annotationTag = document.getElementById('annotation-tag');
const gaugeFill = document.getElementById('gauge-fill');
const gaugeNumber = document.getElementById('gauge-number');
const severityFill = document.getElementById('severity-fill');
const severityMarker = document.getElementById('severity-marker');

// --- Inject SVG gradient for gauge ---
function injectGaugeGradient() {
    const svg = document.querySelector('.gauge-svg');
    if (!svg) return;
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
    gradient.setAttribute('id', 'gaugeGradient');
    gradient.setAttribute('x1', '0');
    gradient.setAttribute('y1', '0');
    gradient.setAttribute('x2', '1');
    gradient.setAttribute('y2', '1');

    const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    stop1.setAttribute('offset', '0%');
    stop1.setAttribute('stop-color', '#ff4d6a');

    const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    stop2.setAttribute('offset', '100%');
    stop2.setAttribute('stop-color', '#f59e0b');

    gradient.appendChild(stop1);
    gradient.appendChild(stop2);
    defs.appendChild(gradient);
    svg.insertBefore(defs, svg.firstChild);
}

// --- Drag & Drop ---
dropZone.addEventListener('click', (e) => {
    if (e.target !== fileInput) {
        fileInput.click();
    }
});

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        handleFile(file);
    }
});

// --- File Input ---
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleFile(file);
});

// --- Handle File ---
function handleFile(file) {
    fileName.textContent = file.name;

    const reader = new FileReader();
    reader.onload = (event) => {
        imagePreview.src = event.target.result;

        // Show loading, hide upload & results
        uploadSection.style.display = 'none';
        loadingOverlay.classList.remove('hidden');
        resultsSection.classList.add('hidden');

        // Simulate AI processing
        setTimeout(() => {
            loadingOverlay.classList.add('hidden');
            resultsSection.classList.remove('hidden');
            animateResults();
        }, 2200);
    };
    reader.readAsDataURL(file);
}

// --- Animate Results ---
function animateResults() {
    injectGaugeGradient();

    // Animate confidence gauge
    const targetConfidence = 92;
    const circumference = 2 * Math.PI * 52; // radius = 52
    const targetOffset = circumference - (circumference * targetConfidence / 100);

    // Trigger animation after a tiny delay for CSS transition to kick in
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            gaugeFill.style.strokeDashoffset = targetOffset;
        });
    });

    // Animate number count
    animateCounter(gaugeNumber, 0, targetConfidence, 1500);

    // Show detection box & annotation
    setTimeout(() => {
        detectionBox.classList.remove('hidden');
    }, 600);

    setTimeout(() => {
        annotationTag.classList.remove('hidden');
    }, 900);

    // Animate severity bar (65% = moderate-to-severe)
    setTimeout(() => {
        severityFill.style.width = '65%';
        severityMarker.style.left = '65%';
    }, 400);

    // Increment scan counter
    const statScans = document.getElementById('stat-scans');
    const currentScans = parseInt(statScans.textContent);
    statScans.textContent = currentScans + 1;
}

// --- Counter Animation ---
function animateCounter(element, start, end, duration) {
    const startTime = performance.now();
    const easeOut = (t) => 1 - Math.pow(1 - t, 3);

    function step(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easedProgress = easeOut(progress);
        const current = Math.round(start + (end - start) * easedProgress);
        element.textContent = current;

        if (progress < 1) {
            requestAnimationFrame(step);
        }
    }

    requestAnimationFrame(step);
}

// --- Nav scroll effect ---
let lastScroll = 0;
window.addEventListener('scroll', () => {
    const navbar = document.getElementById('navbar');
    const scrollY = window.scrollY;

    if (scrollY > 10) {
        navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.3)';
    } else {
        navbar.style.boxShadow = 'none';
    }
    lastScroll = scrollY;
});