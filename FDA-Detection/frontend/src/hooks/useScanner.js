import { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../utils/constants';

export const useScanner = () => {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [history, setHistory] = useState([]);
    const [error, setError] = useState('');
    const [scanMessage, setScanMessage] = useState('');
    const [loadingDetail, setLoadingDetail] = useState(false);
    const [detailData, setDetailData] = useState(null);

    const fetchHistory = async () => {
        try {
            const res = await axios.get(`${API_URL}/history`);
            setHistory(res.data);
        } catch (err) {
            console.error("Failed to fetch history", err);
        }
    };

    const handleScan = async (targetUrl, isAutoMode = false) => {
        setLoading(true);
        if (!isAutoMode) {
            setError('');
            setResult(null);
            setScanMessage('กำลังเชื่อมต่อ...');
        }

        try {
            const response = await fetch(`${API_URL}/scan`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: targetUrl, force: !isAutoMode })
            });

            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || 'Network response was not ok');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (let line of lines) {
                    const trimmedLine = line.trim();
                    if (!trimmedLine || !trimmedLine.startsWith('data: ')) continue;
                    
                    try {
                        const data = JSON.parse(trimmedLine.substring(6));
                        if (data.status === 'progress') {
                            setScanMessage(data.message);
                        } else if (data.status === 'complete') {
                            setResult(data.result);
                            fetchHistory();
                        } else if (data.status === 'error') {
                            if (!isAutoMode) setError(data.message || 'Scan failed.');
                        }
                    } catch (err) {
                        console.error('Error parsing SSE json line:', trimmedLine, err);
                    }
                }
            }
            return true;
        } catch (err) {
            if (!isAutoMode) setError(err.message || 'Scan failed. Please check the URL and try again.');
            return false;
        } finally {
            if (!isAutoMode) {
                setLoading(false);
                setScanMessage('');
            }
        }
    };

    const fetchDetail = async (id) => {
        setLoadingDetail(true);
        try {
            const res = await axios.get(`${API_URL}/scan/${id}`);
            setDetailData(res.data);
        } catch (err) {
            console.error("Failed to fetch scan detail", err);
        } finally {
            setLoadingDetail(false);
        }
    };

    const clearHistory = async () => {
        if (!window.confirm("Are you sure you want to clear all scan history?")) return;
        try {
            await axios.delete(`${API_URL}/history/clear`);
            setHistory([]);
        } catch (err) {
            console.error("Failed to clear history", err);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, []);

    return {
        loading,
        result,
        history,
        error,
        setError,
        scanMessage,
        handleScan,
        clearHistory,
        fetchHistory,
        fetchDetail,
        setResult,
        loadingDetail,
        detailData
    };
};
