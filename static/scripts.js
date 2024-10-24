// static/js/scripts.js

// وظائف عامة للتطبيق
document.addEventListener('DOMContentLoaded', function() {
    // إعداد الإشعارات
    setupNotifications();
    
    // تفعيل tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // تحديث لحظي للتاريخ والوقت
    updateDateTime();
    setInterval(updateDateTime, 1000);
});

// تحديث التاريخ والوقت
function updateDateTime() {
    const now = new Date();
    const elements = document.querySelectorAll('.current-time');
    elements.forEach(element => {
        element.textContent = now.toLocaleTimeString('ar-SA');
    });
}

// إعداد الإشعارات
function setupNotifications() {
    if ("Notification" in window) {
        if (Notification.permission !== "granted" && Notification.permission !== "denied") {
            Notification.requestPermission();
        }
    }
}

// عرض التنبيهات
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.querySelector('.container-fluid').insertAdjacentElement('afterbegin', alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// تنسيق الأرقام
function formatNumber(number, decimals = 8) {
    return parseFloat(number).toFixed(decimals);
}

// تنسيق العملة
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('ar-SA', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

// تحميل البيانات
async function fetchData(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching data:', error);
        showAlert('حدث خطأ في جلب البيانات', 'danger');
        throw error;
    }
}

// إرسال البيانات
async function postData(url, data) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        return await response.json();
    } catch (error) {
        console.error('Error posting data:', error);
        showAlert('حدث خطأ في إرسال البيانات', 'danger');
        throw error;
    }
}

// التحقق من صحة النموذج
function validateForm(formElement) {
    const requiredFields = formElement.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            field.classList.add('is-invalid');
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// تحديث حالة التحميل
function toggleLoading(element, state) {
    if (state) {
        element.classList.add('loading');
        element.disabled = true;
    } else {
        element.classList.remove('loading');
        element.disabled = false;
    }
}

// تنسيق التاريخ
function formatDate(date, format = 'long') {
    const options = format === 'long' 
        ? { year: 'numeric', month: 'long', day: 'numeric', hour: 'numeric', minute: 'numeric' }
        : { year: 'numeric', month: 'numeric', day: 'numeric' };
        
    return new Date(date).toLocaleDateString('ar-SA', options);
}

// تحويل التوقيت
function convertTimezone(date, timezone = 'Asia/Riyadh') {
    return new Date(date).toLocaleString('ar-SA', { timeZone: timezone });
}

// حفظ في التخزين المحلي
function saveToStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
        console.error('Error saving to localStorage:', e);
    }
}

// جلب من التخزين المحلي
function getFromStorage(key) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : null;
    } catch (e) {
        console.error('Error reading from localStorage:', e);
        return null;
    }
}