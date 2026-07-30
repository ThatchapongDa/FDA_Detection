import { STATUS_CONFIG } from './constants';

export const getStatusConfig = (code, dbStatus = null) => {
    if (dbStatus === 'processing' || dbStatus === 'pending') return STATUS_CONFIG.SCANNING;
    if (dbStatus === 'cancelled' || dbStatus === 'error' || dbStatus === 'failed') return STATUS_CONFIG.CANCELLED;
    return STATUS_CONFIG[code] || STATUS_CONFIG.NEED_REVIEW;
};

export const normalizeFda = (s) => (s ? s.replace(/[-\s\.\:\/]/g, '').toUpperCase() : '');

export const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('th-TH', { 
        dateStyle: 'medium', 
        timeStyle: 'short' 
    });
};

export const formatTime = (dateStr) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit' 
    });
};

export const highlightFda = (text) => {
    if (!text) return text;
    // Regex matches common Thai FDA number patterns
    const fdaRegex = /(\d{2}-\d-\d{5}-\d-\d{4})/g;
    return text.split(fdaRegex);
};
