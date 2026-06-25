let dailyMacros = JSON.parse(localStorage.getItem('dailyMacros')) || { cal: 0, pro: 0, carb: 0, fat: 0 };
let goals = JSON.parse(localStorage.getItem('goals')) || { cal: 2000, pro: 150, carb: 250, fat: 70 };


function updateDashboardDisplay() {
    
    const elements = {
        cal: document.getElementById('d-cal'),
        pro: document.getElementById('d-pro'),
        carb: document.getElementById('d-carb'),
        fat: document.getElementById('d-fat'),
        calGoal: document.getElementById('goal-cal-val'),
        proGoal: document.getElementById('goal-pro-val'),
        carbGoal: document.getElementById('goal-carb-val'),
        fatGoal: document.getElementById('goal-fat-val')
    };

    
    elements.cal.textContent = Math.round(dailyMacros.cal);
    elements.pro.textContent = Math.round(dailyMacros.pro);
    elements.carb.textContent = Math.round(dailyMacros.carb);
    elements.fat.textContent = Math.round(dailyMacros.fat);

    
    elements.calGoal.textContent = goals.cal;
    elements.proGoal.textContent = goals.pro;
    elements.carbGoal.textContent = goals.carb;
    elements.fatGoal.textContent = goals.fat;

    
    elements.cal.style.color = dailyMacros.cal > goals.cal ? '#ef4444' : 'white';
    elements.pro.style.color = dailyMacros.pro > goals.pro ? '#ef4444' : 'white';
    elements.carb.style.color = dailyMacros.carb > goals.carb ? '#ef4444' : 'white';
    elements.fat.style.color = dailyMacros.fat > goals.fat ? '#ef4444' : 'white';
}


function updateGoals() {
    const inputCal = document.getElementById('goal-cal');
    const inputPro = document.getElementById('goal-pro');
    const inputCarb = document.getElementById('goal-carb');
    const inputFat = document.getElementById('goal-fat');

    
    goals.cal = parseInt(inputCal.value) || goals.cal;
    goals.pro = parseInt(inputPro.value) || goals.pro;
    goals.carb = parseInt(inputCarb.value) || goals.carb;
    goals.fat = parseInt(inputFat.value) || goals.fat;
    
    
    localStorage.setItem('goals', JSON.stringify(goals));
    updateDashboardDisplay();

    inputCal.value = '';
    inputPro.value = '';
    inputCarb.value = '';
    inputFat.value = '';
}

function resetDaily() {
    dailyMacros = { cal: 0, pro: 0, carb: 0, fat: 0 };
    localStorage.setItem('dailyMacros', JSON.stringify(dailyMacros));
    updateDashboardDisplay();
}

const uploadArea = document.getElementById('uploadArea');
const imageInput = document.getElementById('imageInput');
const imagePreview = document.getElementById('imagePreview');
const uploadContent = document.querySelector('.upload-content');
const analyzeBtn = document.getElementById('analyzeBtn');
const btnText = document.querySelector('.btn-text');
const loader = document.querySelector('.loader');
const resultsPanel = document.getElementById('results');
const errorBox = document.getElementById('errorBox');
const errorMsg = document.getElementById('errorMsg');
const elFoodName = document.getElementById('foodName');
const elCal = document.getElementById('calValue');
const elPro = document.getElementById('proValue');
const elCarb = document.getElementById('carbValue');
const elFat = document.getElementById('fatValue');
const elMicro = document.getElementById('microValue');

let currentFile = null;
uploadArea.addEventListener('click', () => imageInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = 'var(--primary)';
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.style.borderColor = 'rgba(255, 255, 255, 0.2)';
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = 'rgba(255, 255, 255, 0.2)';
    if (e.dataTransfer.files.length) {
        handleFile(e.dataTransfer.files[0]);
    }
});

imageInput.addEventListener('change', function() {
    if (this.files.length) {
        handleFile(this.files[0]);
    }
});

function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        showError('Por favor selecciona un archivo de imagen válido.');
        return;
    }

    currentFile = file;
    hideError();
    resultsPanel.classList.add('hidden');
    analyzeBtn.disabled = false;

    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        imagePreview.classList.remove('hidden');
        uploadContent.classList.add('hidden');
    };
    reader.readAsDataURL(file);
}
analyzeBtn.addEventListener('click', async () => {
    if (!currentFile) return;
    analyzeBtn.disabled = true;
    btnText.classList.add('hidden');
    loader.classList.remove('hidden');
    resultsPanel.classList.add('hidden');
    hideError();

    const formData = new FormData();
    formData.append('image', currentFile);

    try {
        const response = await fetch('/analyze-food', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Error en el servidor');
        }

        const data = await response.json();
        renderResults(data);

    } catch (error) {
        showError(error.message);
    } finally {
        analyzeBtn.disabled = false;
        btnText.classList.remove('hidden');
        loader.classList.add('hidden');
    }
});

function renderResults(data) {
    
    elFoodName.textContent = data.food_identified || 'Plato Analizado';
    elMicro.textContent = data.micronutrients || 'Información de micronutrientes no disponible.';
    
    animateValue(elCal, 0, data.calories || 0, 1000);
    animateValue(elPro, 0, data.protein_g || 0, 1000);
    animateValue(elCarb, 0, data.carbs_g || 0, 1000);
    animateValue(elFat, 0, data.fats_g || 0, 1000);

    resultsPanel.classList.remove('hidden');


    dailyMacros.cal += data.calories || 0;
    dailyMacros.pro += data.protein_g || 0;
    dailyMacros.carb += data.carbs_g || 0;
    dailyMacros.fat += data.fats_g || 0;
    
    
    localStorage.setItem('dailyMacros', JSON.stringify(dailyMacros));
    updateDashboardDisplay();
}

function animateValue(obj, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const easeProgress = 1 - Math.pow(1 - progress, 4);
        obj.innerHTML = (progress === 1) ? end : Math.floor(easeProgress * (end - start) + start);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

function showError(msg) {
    errorMsg.textContent = msg;
    errorBox.classList.remove('hidden');
}

function hideError() {
    errorBox.classList.add('hidden');
}

document.getElementById('resetDaily').addEventListener('click', resetDaily);
updateDashboardDisplay();