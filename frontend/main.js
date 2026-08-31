// Mobile Menu Toggle
const burger = document.getElementById('burger');
const overlay = document.getElementById('overlay');
const mobileMenu = document.getElementById('mobileMenu');
const mobileLinks = document.querySelectorAll('.mobile-link');

function toggleMenu() {
    const isOpen = burger.getAttribute('aria-expanded') === 'true';
    burger.setAttribute('aria-expanded', !isOpen);
    overlay.classList.toggle('active', !isOpen);
    mobileMenu.classList.toggle('active', !isOpen);
    document.body.classList.toggle('menu-open', !isOpen);
}

burger.addEventListener('click', toggleMenu);
overlay.addEventListener('click', toggleMenu);

// Close menu on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && burger.getAttribute('aria-expanded') === 'true') {
        toggleMenu();
    }
});

// Close menu on link click
mobileLinks.forEach(link => {
    link.addEventListener('click', () => {
        if (burger.getAttribute('aria-expanded') === 'true') {
            toggleMenu();
        }
    });
});

// Close menu on resize > 720px
window.addEventListener('resize', () => {
    if (window.innerWidth > 720 && burger.getAttribute('aria-expanded') === 'true') {
        toggleMenu();
    }
});

// Stats Count-up Animation
const statValues = document.querySelectorAll('.stat-value');

function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
}

function animateValue(element, start, end, duration, decimals, suffix) {
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easedProgress = easeOutCubic(progress);
        
        const current = start + (end - start) * easedProgress;
        element.textContent = current.toFixed(decimals) + suffix;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// Intersection Observer for stats
const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
            const element = entry.target;
            const target = parseFloat(element.dataset.target);
            const suffix = element.dataset.suffix;
            const decimals = parseInt(element.dataset.decimals);
            
            const startOffset = 480 + index * 90;
            const duration = 1500 + index * 80;
            
            setTimeout(() => {
                animateValue(element, 0, target, duration, decimals, suffix);
            }, startOffset);
            
            statsObserver.unobserve(element);
        }
    });
}, { threshold: 0.25 });

statValues.forEach(stat => statsObserver.observe(stat));

// Ensure video plays on load
const video = document.querySelector('.bg-video');
if (video) {
    video.play().catch(err => {
        console.log('Video autoplay failed:', err);
    });
}

// Backend Integration
const API_BASE = 'http://localhost:8000';
const getStartedBtn = document.getElementById('getStartedBtn');
const investigationSection = document.getElementById('investigationSection');
const clusterSelect = document.getElementById('clusterSelect');
const investigateBtn = document.getElementById('investigateBtn');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultsContainer = document.getElementById('resultsContainer');
const rootCauseText = document.getElementById('rootCauseText');
const suggestedFixText = document.getElementById('suggestedFixText');
const confidenceFill = document.getElementById('confidenceFill');
const confidenceText = document.getElementById('confidenceText');
const historyContainer = document.getElementById('historyContainer');
const historyList = document.getElementById('historyList');

// Show investigation section when clicking Get Started
getStartedBtn.addEventListener('click', () => {
    investigationSection.style.display = 'block';
    investigationSection.scrollIntoView({ behavior: 'smooth' });
    loadClusters();
});

// Load clusters from backend
async function loadClusters() {
    try {
        const response = await fetch(`${API_BASE}/clusters`);
        const data = await response.json();
        
        clusterSelect.innerHTML = '<option value="">Select a cluster...</option>';
        data.clusters.forEach(cluster => {
            const option = document.createElement('option');
            option.value = cluster.name;
            option.textContent = cluster.name;
            clusterSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load clusters:', error);
        clusterSelect.innerHTML = '<option value="">Failed to load clusters</option>';
    }
}

// Start investigation
investigateBtn.addEventListener('click', async () => {
    const cluster = clusterSelect.value;
    if (!cluster) {
        alert('Please select a cluster first');
        return;
    }
    
    investigateBtn.disabled = true;
    progressContainer.style.display = 'block';
    resultsContainer.style.display = 'none';
    progressFill.style.width = '0%';
    progressText.textContent = 'Initializing investigation...';
    
    try {
        const response = await fetch(`${API_BASE}/investigate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                namespace: 'default',
                collect_logs: true,
                enable_ai: true
            })
        });
        
        const data = await response.json();
        
        // Update progress
        progressFill.style.width = '100%';
        progressText.textContent = 'Investigation complete!';
        
        // Show results
        setTimeout(() => {
            progressContainer.style.display = 'none';
            resultsContainer.style.display = 'flex';
            
            rootCauseText.textContent = data.analysis?.root_cause || 'No issues detected';
            suggestedFixText.textContent = data.analysis?.suggested_fix || 'No action required';
            
            const confidence = data.analysis?.confidence || 0;
            confidenceFill.style.width = `${confidence}%`;
            confidenceText.textContent = `${confidence}% confidence`;
        }, 500);
        
    } catch (error) {
        console.error('Investigation failed:', error);
        progressText.textContent = 'Investigation failed. Please try again.';
    } finally {
        investigateBtn.disabled = false;
    }
});

// Load investigation history
async function loadHistory() {
    // History feature disabled for now - would need InsForge integration
    historyContainer.style.display = 'none';
}