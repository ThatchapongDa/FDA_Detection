import { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../utils/constants';

export const useCrawler = (scanMode) => {
    const [crawlerStatus, setCrawlerStatus] = useState(null);
    const [crawlerHistory, setCrawlerHistory] = useState([]);
    const [error, setError] = useState('');

    const fetchCrawlerData = async () => {
        try {
            const [statusRes, histRes] = await Promise.all([
                axios.get(`${API_URL}/crawler/status`),
                axios.get(`${API_URL}/crawler/history`)
            ]);
            setCrawlerStatus(statusRes.data);
            setCrawlerHistory(histRes.data);
        } catch (err) {
            console.error("Failed to fetch crawler data", err);
        }
    };

    const startCrawler = async (keyword, limit) => {
        setError('');
        try {
            await axios.post(`${API_URL}/crawler/start`, {
                keyword: keyword.trim(),
                limit: limit || 10
            });
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Failed to start crawler.');
        }
    };

    const stopCrawler = async () => {
        try {
            await axios.post(`${API_URL}/crawler/stop`);
        } catch (err) {
            console.error("Failed to stop crawler", err);
        }
    };

    useEffect(() => {
        let interval;
        if (scanMode === 'crawler' || scanMode === 'auto') {
            fetchCrawlerData();
            interval = setInterval(fetchCrawlerData, 5000);
        }
        return () => clearInterval(interval);
    }, [scanMode]);

    return {
        crawlerStatus,
        crawlerHistory,
        error,
        setError,
        startCrawler,
        stopCrawler
    };
};
