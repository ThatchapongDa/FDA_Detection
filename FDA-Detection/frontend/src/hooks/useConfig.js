import { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../utils/constants';

export const useConfig = () => {
    const [settings, setSettings] = useState({
        crawler_delay: 30,
        cache_expiry_hours: 24,
        enable_medicine_filter: true,
        max_scan_limit: 10
    });
    const [isSavingConfig, setIsSavingConfig] = useState(false);

    const fetchConfig = async () => {
        try {
            const resS = await axios.get(`${API_URL}/config/settings`);
            setSettings(resS.data);
        } catch (err) {
            console.error("Failed to fetch settings", err);
        }
    };

    const saveSettings = async (newSettings) => {
        setIsSavingConfig(true);
        try {
            await axios.post(`${API_URL}/config/settings`, newSettings);
            setSettings(newSettings);
        } catch (err) {
            alert("Failed to save settings");
        } finally {
            setIsSavingConfig(false);
        }
    };

    useEffect(() => {
        fetchConfig();
    }, []);

    return {
        settings,
        isSavingConfig,
        saveSettings
    };
};
