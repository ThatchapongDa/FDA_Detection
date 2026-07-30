import { useState, useEffect } from 'react';
import axios from 'axios';
import Head from 'next/head';

// Utilities
import { API_URL } from '../utils/constants';
import { getStatusConfig, highlightFda } from '../utils/helpers';

// Components
import ImageWithBoxes from '../components/ImageWithBoxes';
import CredentialBox from '../components/CredentialBox';
import StatusBadge from '../components/StatusBadge';
import AnalysisCard from '../components/AnalysisCard';
import SettingsModal from '../components/SettingsModal';
import DeepDiveModal from '../components/DeepDiveModal';
import EvidenceModal from '../components/EvidenceModal';

// Hooks
import { useConfig } from '../hooks/useConfig';
import { useScanner } from '../hooks/useScanner';
import { useCrawler } from '../hooks/useCrawler';

export default function Home() {
    const [activeTab, setActiveTab] = useState('analysis');
    const [darkMode, setDarkMode] = useState(false);
    const [mounted, setMounted] = useState(false);

    // Handle Hydration & Persistence
    useEffect(() => {
        setMounted(true);
        const savedTheme = localStorage.getItem('darkMode');
        if (savedTheme === 'true') {
            setDarkMode(true);
        } else if (savedTheme === null && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            setDarkMode(true);
        }
    }, []);

    useEffect(() => {
        if (!mounted) return;

        if (darkMode) {
            document.documentElement.classList.add('dark');
            localStorage.setItem('darkMode', 'true');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('darkMode', 'false');
        }
    }, [darkMode, mounted]);

    const toggleDarkMode = () => {
        setDarkMode(prev => !prev);
    };

    const [url, setUrl] = useState('');
    const [keyword, setKeyword] = useState('');
    const [showDebug, setShowDebug] = useState(false);
    const [selectedDetailId, setSelectedDetailId] = useState(null);
    const [activeCredentialDetail, setActiveCredentialDetail] = useState(null);

    const {
        settings,
        loading: loadingConfig,
        isSaving: isSavingConfig,
        saveSettings
    } = useConfig();

    const {
        loading,
        error,
        result,
        history,
        scanMessage,
        setResult,
        handleScan,
        clearHistory,
        loadingDetail,
        detailData,
        fetchHistory,
        fetchDetail
    } = useScanner();

    const {
        crawlerStatus,
        crawlerHistory,
        startCrawler,
        stopCrawler,
        error: crawlerError,
        setError: setCrawlerError
    } = useCrawler(activeTab);

    const [isSettingsOpen, setIsSettingsOpen] = useState(false);

    // Initial data fetch
    useEffect(() => {
        // You might want to fetch initial history here if useScanner doesn't
    }, []);

    const onSingleScan = (e) => {
        e.preventDefault();
        handleScan(url);
    };

    const onStartCrawler = (e) => {
        e.preventDefault();
        startCrawler(keyword, settings.max_scan_limit);
    };

    const handleOpenDetail = (id) => {
        setSelectedDetailId(id);
        fetchDetail(id);
    };

    return (
        <div className="min-h-screen bg-[#f8fafc] dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans selection:bg-blue-100 selection:text-blue-900 transition-colors duration-300">
            <Head>
                <title>FDA Intelligence System | Thai Consumer Protection</title>
                <meta name="description" content="AI-powered FDA verification system for e-commerce safety monitoring" />
            </Head>

            {/* Premium Navigation Header */}
            <header className="sticky top-0 z-40 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border-b border-slate-200/60 dark:border-slate-800 shadow-sm">
                <div className="max-w-[1440px] mx-auto px-6 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-200 dark:shadow-none">
                            <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                            </svg>
                        </div>
                        <div className="hidden sm:block">
                            <h1 className="text-xl font-black text-slate-900 dark:text-white tracking-tighter leading-none">FDA DETECTION</h1>
                            <p className="text-[9px] font-bold text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-2 tracking-wide">
                                <span className="bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-1.5 py-0.5 rounded text-[7px] font-black border border-blue-100 dark:border-blue-800 uppercase">AI-Powered</span>
                                <span className="w-1 h-1 bg-slate-300 dark:bg-slate-700 rounded-full"></span>
                                <span>ระบบวิเคราะห์ฉลากผลิตภัณฑ์สุขภาพอัตโนมัติ</span>
                            </p>
                        </div>
                    </div>

                    <nav className="flex bg-slate-100/80 dark:bg-slate-800/80 p-1.5 rounded-2xl border border-slate-200 dark:border-slate-700">
                        <button
                            onClick={() => setActiveTab('analysis')}
                            className={`px-6 py-2 rounded-xl text-sm font-bold transition-all flex items-center gap-2 ${activeTab === 'analysis'
                                ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-md ring-1 ring-slate-200 dark:ring-slate-600'
                                : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white hover:bg-slate-200/50 dark:hover:bg-slate-700/50'
                                }`}
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                            ตรวจสอบรายชิ้น
                        </button>
                        <button
                            onClick={() => setActiveTab('crawler')}
                            className={`px-6 py-2 rounded-xl text-sm font-bold transition-all flex items-center gap-2 ${activeTab === 'crawler'
                                ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-md ring-1 ring-slate-200 dark:ring-slate-600'
                                : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white hover:bg-slate-200/50 dark:hover:bg-slate-700/50'
                                }`}
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                            ระบบเฝ้าสังเกตการณ์
                        </button>
                        <button
                            onClick={() => setActiveTab('dashboard')}
                            className={`px-6 py-2 rounded-xl text-sm font-bold transition-all flex items-center gap-2 ${activeTab === 'dashboard'
                                ? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-md ring-1 ring-slate-200 dark:ring-slate-600'
                                : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white hover:bg-slate-200/50 dark:hover:bg-slate-700/50'
                                }`}
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
                            สรุปภาพรวม
                        </button>
                    </nav>

                    <div className="flex items-center gap-4">
                        <button
                            onClick={toggleDarkMode}
                            className="p-3 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded-2xl border border-slate-200 dark:border-slate-700 hover:bg-white dark:hover:bg-slate-700 transition-all shadow-sm"
                        >
                            {darkMode ? (
                                <svg className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" /></svg>
                            ) : (
                                <svg className="w-5 h-5 text-slate-500" fill="currentColor" viewBox="0 0 20 20"><path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" /></svg>
                            )}
                        </button>
                        <button onClick={() => setIsSettingsOpen(true)} className="flex items-center gap-2 px-5 py-2.5 bg-slate-900 dark:bg-blue-600 text-white rounded-2xl font-bold text-xs uppercase tracking-widest hover:bg-slate-800 dark:hover:bg-blue-500 transition-all shadow-lg">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924-1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                            ตั้งค่า
                        </button>
                    </div>
                </div>
            </header>

            <main className="max-w-[1440px] mx-auto px-6 py-10">
                {activeTab === 'analysis' ? (
                    /* ANALYSIS MODE: MAIN CONTENT */
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                        <div className="lg:col-span-8 space-y-8">
                        {/* Disclaimer Banner */}
                            <div className="flex items-start gap-3 px-5 py-4 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-2xl">
                                <svg className="w-5 h-5 text-slate-400 dark:text-slate-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                                    <span className="font-black text-slate-700 dark:text-slate-300">ข้อจำกัดความรับผิดชอบ · </span>
                                    ระบบนี้ใช้ AI วิเคราะห์ข้อมูลและภาพถ่ายสินค้าโดยอัตโนมัติ <span className="font-bold text-slate-600 dark:text-slate-300">ผลลัพธ์อาจไม่ถูกต้องครบถ้วน</span> และไม่ถือเป็นหลักฐานทางกฎหมาย
                                    ควรตรวจสอบซ้ำกับเจ้าหน้าที่หรือฐานข้อมูลทางการก่อนดำเนินการใดๆ
                                </p>
                            </div>

                            {/* Input Area */}
                            <div className="bg-white/60 dark:bg-slate-900/60 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 backdrop-blur-md shadow-sm">
                                <form onSubmit={onSingleScan} className="flex flex-col md:flex-row gap-4">
                                    <input
                                        type="url"
                                        required
                                        disabled={loading}
                                        placeholder="วางลิงก์สินค้า Shopee เพื่อเริ่มวิเคราะห์..."
                                        className="flex-1 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none placeholder:text-slate-400 dark:placeholder:text-slate-600 disabled:opacity-50"
                                        value={url}
                                        onChange={(e) => setUrl(e.target.value)}
                                    />
                                    <button
                                        type="submit"
                                        disabled={loading}
                                        className={`px-8 py-3 rounded-xl font-bold transition-all shadow-lg whitespace-nowrap ${loading
                                            ? 'bg-slate-200 dark:bg-slate-800 text-slate-400 dark:text-slate-600 cursor-not-allowed'
                                            : 'bg-blue-600 hover:bg-blue-500 text-white hover:scale-105 shadow-blue-200 dark:shadow-none'
                                            }`}
                                    >
                                        {loading ? 'กำลังวิเคราะห์...' : 'เริ่มวิเคราะห์สินค้า'}
                                    </button>
                                </form>

                                {/* Loading / Progress State */}
                                {loading && (
                                    <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/30 border border-blue-100 dark:border-blue-800 rounded-xl shadow-sm">
                                        <div className="text-blue-700 dark:text-blue-400 text-sm font-medium animate-pulse flex items-center gap-3">
                                            <svg className="animate-spin h-5 w-5 text-blue-600 dark:text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                            {scanMessage}
                                        </div>
                                    </div>
                                )}
                                {error && <p className="mt-4 text-red-500 dark:text-red-400 text-sm font-medium bg-red-50 dark:bg-red-900/20 p-3 rounded-lg border border-red-100 dark:border-red-900/30">{error}</p>}
                            </div>

                            {/* RESULTS AREA */}
                            {result && (
                                <div className="space-y-6 animate-fade-in">
                                    {/* Header: Product Title & Certification */}
                                    <div className="bg-white dark:bg-slate-900 p-8 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl dark:shadow-none relative overflow-hidden">
                                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500"></div>

                                        <div className="flex flex-col gap-6">
                                            {/* Warning: Category Mismatch */}
                                            {result.product_info?.category === 'GENERAL' && (
                                                <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border-l-4 border-amber-400 text-amber-800 dark:text-amber-400 rounded-r-lg flex items-start gap-4">
                                                    <svg className="w-6 h-6 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                                                    <div>
                                                        <h4 className="font-black text-sm uppercase tracking-tight">Regulated Product Logic Caution</h4>
                                                        <p className="text-xs mt-1 leading-relaxed">This item was detected as a <strong>General Product</strong> (non-food/drug). However, the system is performing a deep-scan to ensure no hidden medical claims are present.</p>
                                                    </div>
                                                </div>
                                            )}

                                            {/* SCRAPE_FAILED Informer */}
                                            {result.status === 'scrape_failed' && (
                                                <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-900/30 rounded-2xl flex items-start gap-4 ring-2 ring-red-100 dark:ring-red-900/20">
                                                    <div className="p-2 bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400 rounded-xl">
                                                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                                                    </div>
                                                    <div>
                                                        <h3 className="font-black text-red-900 dark:text-red-400 uppercase text-xs">พบระบบป้องกัน (Bot Shield)</h3>
                                                        <p className="text-xs text-red-700 dark:text-red-500 mt-1 leading-relaxed">แพลตฟอร์มต้นทางจำกัดการเข้าถึงข้อมูลบางส่วน ระบบพยายามวิเคราะห์ข้อมูลเท่าที่ตรวจพบได้</p>
                                                    </div>
                                                </div>
                                            )}

                                            {/* 1. ชื่อเรื่องและข้อมูลอภิมาน (Meta) */}
                                            <div className="flex flex-col md:flex-row justify-between items-start gap-4">
                                                <div className="flex-1 min-w-0">
                                                    <h2 className="text-3xl font-black text-slate-900 dark:text-white mb-3 leading-tight tracking-tight">
                                                        {result.product_info?.title}
                                                    </h2>
                                                    <div className="flex flex-wrap gap-2">
                                                        <span className="px-3 py-1 bg-indigo-600 text-white rounded-full text-[10px] font-black uppercase tracking-widest shadow-md shadow-indigo-200 dark:shadow-none">
                                                            {result.product_type}
                                                        </span>
                                                        <span className="px-3 py-1 bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 rounded-full text-[10px] font-bold uppercase tracking-widest border border-slate-200 dark:border-slate-700">
                                                            {result.product_info?.category}
                                                        </span>
                                                        {result.product_info?.location && (
                                                            <span className="px-3 py-1 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 rounded-full text-[10px] font-bold flex items-center gap-1 border border-emerald-100 dark:border-emerald-900/30">
                                                                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" /></svg>
                                                                {result.product_info.location}
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>

                                                <div className="shrink-0 pt-1">
                                                    <div className="text-[10px] font-black text-slate-300 uppercase tracking-[0.2em] mb-1 text-right">Verification ID</div>
                                                    <div className="text-xs font-mono font-bold text-slate-400 bg-slate-50 px-3 py-1 rounded-lg border border-slate-100">
                                                        #{result.id || 'TEMP'}
                                                    </div>
                                                </div>
                                            </div>

                                            {/* 2. Certification Summary Block (The 4 Pillars) */}
                                            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                                                {[
                                                    { id: 'fda_info', label: 'ข้อมูล อย. (FDA Info)', found: result.verified_credentials?.fda_info?.found, desc: result.verified_credentials?.fda_info?.text || 'ไม่พบเลขจดแจ้ง' },
                                                    { id: 'fda_label', label: 'ฉลาก อย. (FDA Label)', found: result.verified_credentials?.fda_label?.found, desc: result.verified_credentials?.fda_label?.found ? `พบสัญลักษณ์บนบรรจุภัณฑ์` : 'ไม่พบสัญลักษณ์ อย.' },
                                                    { id: 'thai_language', label: 'ภาษาไทย (Thai Label)', found: result.verified_credentials?.thai_language?.found, desc: result.verified_credentials?.thai_language?.found ? 'พบฉลากภาษาไทย' : 'ไม่พบภาษาไทย' },
                                                    { id: 'drug_reg', label: 'ทะเบียนยา (Drug Reg)', found: result.verified_credentials?.drug_reg?.found, desc: result.verified_credentials?.drug_reg?.text || 'ไม่พบทะเบียนตำรับยา' }
                                                ].map((v) => (
                                                    <div
                                                        key={v.id}
                                                        className={`p-4 rounded-2xl border-2 transition-all ${v.found
                                                            ? 'bg-green-50/50 border-green-200 shadow-sm'
                                                            : 'bg-slate-50 border-slate-100 opacity-60 grayscale-[0.5]'
                                                            }`}
                                                    >
                                                        <div className="flex items-center gap-3 mb-2">
                                                            <div className={`p-2 rounded-xl ${v.found ? 'bg-green-500 text-white shadow-lg shadow-green-200' : 'bg-slate-200 text-slate-400'}`}>
                                                                {v.id === 'fda_info' && <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>}
                                                                {v.id === 'fda_label' && <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>}
                                                                {v.id === 'thai_language' && <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" /></svg>}
                                                                {v.id === 'drug_reg' && <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.183.244l-.28.14a2 2 0 01-2.983-1.832V12a9 9 0 0118 0v1.762a2 2 0 01-2.131 1.996l-.228-.03z" /></svg>}
                                                            </div>
                                                            <div className={`text-[10px] font-black uppercase tracking-wider ${v.found ? 'text-green-700' : 'text-slate-400'}`}>
                                                                {v.found ? 'FOUND' : 'NOT DETECTED'}
                                                            </div>
                                                        </div>
                                                        <div className="text-[11px] font-bold text-slate-800 leading-tight mb-1">{v.label}</div>
                                                        <div className="text-[10px] text-slate-500 font-medium line-clamp-1">{v.desc}</div>
                                                    </div>
                                                ))}
                                            </div>

                                            <hr className="border-slate-100" />

                                            {/* [NEW] Legal Violation Box — แสดงเมื่อพบความผิดทางกฎหมาย */}
                                            {result.legal_compliance && result.legal_compliance.length > 0 && (
                                                <div className="bg-rose-50 p-5 rounded-3xl border-2 border-rose-200 flex items-start gap-4 shadow-sm shadow-rose-100/50">
                                                    <div className="p-2.5 bg-rose-600 text-white rounded-2xl shadow-lg shadow-rose-200 shrink-0">
                                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                                        </svg>
                                                    </div>
                                                    <div className="flex-1">
                                                        <div className="text-[10px] font-black text-rose-400 uppercase tracking-[0.2em] mb-3 flex items-center gap-2">
                                                            <span className="w-1.5 h-1.5 bg-rose-400 rounded-full animate-pulse"></span>
                                                            ข้อกฎหมายที่เกี่ยวข้อง — Legal Violation Detected
                                                        </div>
                                                        <div className="space-y-2">
                                                            {result.legal_compliance.map((v, idx) => (
                                                                <div key={idx} className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 bg-white/70 rounded-2xl px-4 py-3 border border-rose-100">
                                                                    <span className="text-[11px] font-black text-rose-600 bg-rose-100 px-3 py-1 rounded-full border border-rose-200 whitespace-nowrap shrink-0">
                                                                        {v.law} {v.section}
                                                                    </span>
                                                                    <p className="text-sm font-bold text-rose-900 leading-tight">
                                                                        {v.details}
                                                                    </p>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </div>
                                            )}

                                            {/* 3. ส่วนของการตรวจสอบเชิงลึก */}
                                            <div className="grid grid-cols-12 gap-8">
                                                {/* LEFT: Shop Claims */}
                                                <div className="col-span-12 lg:col-span-4 space-y-4">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <div className="w-1.5 h-4 bg-amber-400 rounded-full"></div>
                                                        <h4 className="text-[11px] font-black text-slate-400 uppercase tracking-[0.2em]">ข้อมูลที่ผู้ขายระบุ</h4>
                                                    </div>
                                                    <div className="space-y-3">
                                                        {/* Enforce 2-column Metadata UI */}
                                                        <div className="bg-slate-50 rounded-2xl border border-slate-100 p-5 shadow-inner">
                                                            <div className="text-[10px] font-bold text-slate-400 uppercase mb-3 flex items-center gap-1.5">
                                                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
                                                                เลข อย. (อาหาร/เสริม)
                                                            </div>
                                                            <div className="text-xl font-mono font-black text-slate-800 mb-1 line-clamp-1">{result.verified_credentials?.fda_info?.claimed_fda || result.product_info?.scraped_fda || 'ไม่ระบุ'}</div>
                                                            <div className="text-[10px] text-slate-500 font-medium italic">Scraped FDA Number</div>
                                                        </div>

                                                        <div className="bg-slate-50 rounded-2xl border border-slate-100 p-5 shadow-inner">
                                                            <div className="text-[10px] font-bold text-slate-400 uppercase mb-3 flex items-center gap-1.5">
                                                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.183.244l-.28.14a2 2 0 01-2.983-1.832V12a9 9 0 0118 0v1.762a2 2 0 01-2.131 1.996l-.228-.03z" /></svg>
                                                                เลขทะเบียนตำรับยา
                                                            </div>
                                                            <div className="text-xl font-mono font-black text-slate-800 mb-1 line-clamp-1">{result.verified_credentials?.fda_info?.claimed_drug || result.product_info?.scraped_drug || 'ไม่ระบุ'}</div>
                                                            <div className="text-[10px] text-slate-500 font-medium italic">Scraped Drug Registration</div>
                                                        </div>

                                                        <div className="bg-slate-50 rounded-2xl border border-slate-100 p-5 shadow-inner">
                                                            <div className="text-[10px] font-bold text-slate-400 uppercase mb-3 flex items-center gap-1.5">
                                                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>
                                                                หมวดหมู่สินค้า
                                                            </div>
                                                            <div className="text-lg font-bold text-slate-800 mb-1 truncate">{result.product_info?.category || 'N/A'}</div>
                                                            <div className="text-[10px] text-slate-500 font-medium">หมวดหมู่ที่ผู้ขายระบุใน Shopee</div>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* RIGHT: AI Evidence Grid */}
                                                <div className="col-span-12 lg:col-span-8 space-y-4">
                                                    <div className="flex items-center justify-between mb-2">
                                                        <div className="flex items-center gap-2">
                                                            <div className="w-1.5 h-4 bg-indigo-500 rounded-full"></div>
                                                            <h4 className="text-[11px] font-black text-slate-400 uppercase tracking-[0.2em]">ผลการวิเคราะห์จาก AI</h4>
                                                        </div>
                                                        <div className="text-[10px] font-bold text-slate-400 whitespace-nowrap uppercase tracking-widest">สถานะ: {result.risk_level}</div>
                                                    </div>

                                                    <CredentialBox
                                                        result={result}
                                                        onShowDetail={(id) => setActiveCredentialDetail(id)}
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Visual Evidence Section */}
                                    <div className="pt-4">
                                        <div className="flex items-center justify-between mb-6">
                                            <h3 className="text-xl font-black text-slate-800 flex items-center gap-3">
                                                <span className="bg-blue-600 w-2 h-7 rounded-full shadow-[0_0_15px_rgba(37,99,235,0.4)]"></span>
                                                หลักฐานจากภาพถ่ายสินค้า
                                            </h3>
                                            <div className="px-4 py-1.5 bg-slate-100 rounded-full text-[10px] text-slate-500 font-bold border border-slate-200">
                                                วิเคราะห์แล้ว {result.results?.length} รูปภาพ
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                                            {[...(result.results || [])]
                                                .sort((a, b) => (b.detections?.length || 0) - (a.detections?.length || 0))
                                                .map((item, idx) => (
                                                    <div key={idx} className="group bg-white rounded-3xl border border-slate-200 shadow-sm hover:shadow-xl transition-all duration-300 flex flex-col h-full overflow-hidden">
                                                        <div className="relative aspect-video bg-slate-900 overflow-hidden">
                                                            <div className="absolute inset-0 flex items-center justify-center p-2 opacity-90 group-hover:opacity-100 transition-opacity">
                                                                <ImageWithBoxes url={item.url} detections={item.detections} />
                                                            </div>
                                                            <div className="absolute top-4 left-4 z-20">
                                                                <span className="px-3 py-1 bg-black/40 backdrop-blur-md border border-white/20 text-white text-[10px] font-black rounded-full shadow-lg">
                                                                    รูปภาพลำดับที่ #{idx + 1}
                                                                </span>
                                                            </div>
                                                            {item.detections?.length > 0 && (
                                                                <div className="absolute top-4 right-4 z-20">
                                                                    <span className="px-3 py-1 bg-emerald-500 text-white text-[10px] font-black rounded-full shadow-lg flex items-center gap-1.5">
                                                                        <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></span>
                                                                        พบข้อมูล
                                                                    </span>
                                                                </div>
                                                            )}
                                                        </div>

                                                        <div className="flex-1 p-6 flex flex-col bg-slate-50/50 space-y-5">
                                                            <div>
                                                                <div className="flex items-center justify-between mb-3">
                                                                    <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-2">
                                                                        ข้อมูลที่อ่านได้ (OCR)
                                                                    </h4>
                                                                    {item.text && (
                                                                        <button onClick={() => navigator.clipboard.writeText(item.text)} className="p-1.5 hover:bg-white hover:shadow-sm rounded-lg transition-all text-slate-400 hover:text-blue-500">
                                                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                                                                        </button>
                                                                    )}
                                                                </div>
                                                                <div className="bg-white rounded-2xl border border-slate-200 p-4 h-40 overflow-y-auto text-xs leading-relaxed text-slate-600 font-mono shadow-inner">
                                                                    {item.text ? (
                                                                        <div className="whitespace-pre-wrap break-words">
                                                                            {highlightFda(item.text).map((part, i) =>
                                                                                /(\d{2}-\d-\d{5}-\d-\d{4})/.test(part) ?
                                                                                    <span key={i} className="bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded border border-emerald-200 font-black shadow-sm">{part}</span>
                                                                                    : part
                                                                            )}
                                                                        </div>
                                                                    ) : (
                                                                        <div className="h-full flex flex-col items-center justify-center text-slate-300 italic gap-2">
                                                                            <svg className="w-8 h-8 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                                                                            <span>ไม่พบข้อมูลที่อ่านได้</span>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            </div>

                                                            {item.crops_b64?.length > 0 && (
                                                                <div className="space-y-3">
                                                                    <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.15em]">ภาพขยายเฉพาะจุด</h4>
                                                                    <div className="flex flex-wrap gap-2.5">
                                                                        {item.crops_b64.map((b64, ci) => (
                                                                            <img key={ci} src={`data:image/jpeg;base64,${b64}`} alt={`crop-${ci}`} className="h-20 w-auto rounded-xl border border-slate-200 shadow-sm object-contain bg-white hover:scale-110 transition-transform cursor-zoom-in" />
                                                                        ))}
                                                                    </div>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))}
                                        </div>
                                    </div>

                                    {/* Debug Panel Toggle */}
                                    <div className="pt-8 flex justify-center">
                                        <button onClick={() => setShowDebug(!showDebug)} className="px-6 py-2 bg-slate-100 text-slate-500 rounded-full text-[10px] font-black uppercase tracking-[0.2em] hover:bg-slate-200 transition-all border border-slate-200">
                                            {showDebug ? 'ซ่อนข้อมูลดิบ' : 'แสดงข้อมูลดิบ'}
                                        </button>
                                    </div>

                                    {showDebug && (
                                        <div className="mt-4 bg-slate-900 rounded-3xl p-6 overflow-x-auto shadow-2xl ring-1 ring-white/10">
                                            <div className="text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-4">Neural Engine JSON Dump</div>
                                            <pre className="text-emerald-400 font-mono text-[11px] leading-relaxed">
                                                {JSON.stringify(result, null, 2)}
                                            </pre>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* RIGHT PANEL: Analytics & Settings */}
                        <div className="lg:col-span-4 space-y-6">
                            {/* Analysis Statistics Card */}
                            <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
                                <h3 className="text-lg font-black text-slate-800 mb-4 tracking-tight">สถิติการใช้งาน</h3>
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between p-3 bg-slate-50 rounded-2xl border border-slate-100">
                                        <span className="text-xs font-bold text-slate-500">รายการที่วิเคราะห์แล้ว</span>
                                        <span className="text-sm font-black text-slate-900">{history.length}</span>
                                    </div>
                                    <button onClick={clearHistory} className="w-full py-3 bg-red-50 text-red-600 rounded-2xl text-xs font-black uppercase tracking-widest border border-red-100 hover:bg-red-100 transition-colors">
                                        ล้างประวัติการตรวจสอบ
                                    </button>
                                </div>
                            </div>

                            {/* Scrollable Mini-History Feed */}
                            <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm flex flex-col max-h-[400px]">
                                <h3 className="text-[11px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4">ประวัติล่าสุด</h3>
                                <div className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-thin">
                                    {history.length > 0 ? history.map((h) => (
                                        <div key={h.id} className="p-4 bg-slate-50 rounded-2xl border border-slate-100 hover:bg-indigo-50 transition cursor-pointer group">
                                            <div className="flex justify-between items-start mb-2">
                                                <StatusBadge riskLevel={h.risk_level} status={h.status} />
                                                <span className="text-[9px] font-black text-slate-300 font-mono">{new Date(h.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                            </div>
                                            <div className="text-xs font-bold text-slate-800 line-clamp-1 group-hover:text-indigo-600 transition-colors">{h.product_name || h.product_url}</div>
                                        </div>
                                    )) : (
                                        <div className="text-center py-10 text-slate-300 text-[10px] font-bold uppercase italic">ไม่มีประวัติการใช้งาน</div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                ) : activeTab === 'crawler' ? (
                    /* AUTO-SCAN CENTER LAYOUT */
                    <div className="space-y-10 animate-fade-in max-w-5xl mx-auto">
                        {/* ... existing crawler content ... */}
                        <div className="bg-white/70 p-8 rounded-[32px] border border-slate-200 backdrop-blur-xl shadow-xl">
                            <h2 className="text-2xl font-black text-slate-900 mb-6 tracking-tight flex items-center gap-3">
                                <span className="bg-indigo-600 w-3 h-8 rounded-full shadow-[0_0_15px_rgba(79,70,229,0.3)]"></span>
                                ระบบเฝ้าสังเกตการณ์สินค้าอัตโนมัติ
                            </h2>

                            <form onSubmit={crawlerStatus?.is_running ? (e) => { e.preventDefault(); stopCrawler(); } : onStartCrawler} className="flex flex-col md:flex-row gap-4 mb-8">
                                <input
                                    type="text"
                                    required={!crawlerStatus?.is_running}
                                    disabled={crawlerStatus?.is_running}
                                    placeholder="ระบุคำค้นหา (เช่น อาหารเสริมลดน้ำหนัก)..."
                                    className="flex-1 bg-white border border-slate-200 rounded-2xl px-5 py-4 text-slate-900 font-bold focus:ring-4 focus:ring-indigo-100 outline-none placeholder:text-slate-400 placeholder:font-medium disabled:opacity-50 disabled:bg-slate-50 shadow-inner"
                                    value={keyword}
                                    onChange={(e) => setKeyword(e.target.value)}
                                />
                                <div className="flex gap-2">
                                    {!crawlerStatus?.is_running ? (
                                        <button type="submit" disabled={loading} className={`flex-1 px-10 py-4 rounded-2xl font-black uppercase text-xs tracking-widest transition-all shadow-xl shadow-indigo-100 whitespace-nowrap ${loading ? 'bg-slate-400 text-white cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-500 text-white hover:scale-[1.03] active:scale-95'}`}>
                                            เริ่มการเฝ้าสังเกต
                                        </button>
                                    ) : (
                                        <button type="submit" className="flex-1 px-10 py-4 rounded-2xl font-black uppercase text-xs tracking-widest transition-all shadow-xl shadow-red-100 whitespace-nowrap bg-red-500 hover:bg-red-400 text-white hover:scale-[1.03] active:scale-95">
                                            ปิดระบบเฝ้าสังเกต
                                        </button>
                                    )}
                                </div>
                            </form>

                            {/* Intelligent Status Display */}
                            <div className={`rounded-[24px] border p-6 transition-all duration-500 ${crawlerStatus?.is_running ? 'bg-indigo-50/50 border-indigo-100 ring-2 ring-indigo-50' : 'bg-slate-50 border-slate-100 grayscale-[0.3]'}`}>
                                <div className="flex items-center justify-between mb-6">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-3 h-3 rounded-full ${crawlerStatus?.is_running ? 'bg-indigo-500 animate-ping' : 'bg-slate-300'}`}></div>
                                        <span className="text-[11px] font-black text-slate-500 uppercase tracking-[0.2em]">{crawlerStatus?.is_running ? 'กำลังทำงาน' : 'พร้อมใช้งาน'}</span>
                                    </div>
                                    <button onClick={() => setIsSettingsOpen(true)} className="flex items-center gap-2 px-4 py-2 bg-white rounded-xl border border-slate-200 text-[10px] font-black text-slate-500 uppercase tracking-widest hover:border-indigo-300 hover:text-indigo-600 transition-all shadow-sm">
                                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" /></svg>
                                        ตั้งค่าระบบ
                                    </button>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    <div className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm">
                                        <div className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">สถานะ</div>
                                        <div className="text-sm font-black text-slate-800">{crawlerStatus?.current_status || 'IDLE'}</div>
                                    </div>
                                    <div className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm">
                                        <div className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">เป้าหมาย</div>
                                        <div className="text-sm font-black text-indigo-700 truncate">{crawlerStatus?.current_keyword || 'ไม่มี'}</div>
                                    </div>
                                    <div className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-center">
                                        <div className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">ความคืบหน้า</div>
                                        <div className="flex items-center gap-2">
                                            <span className="text-sm font-black text-slate-800">{crawlerStatus?.progress?.current || 0} / {crawlerStatus?.progress?.total || 0}</span>
                                            <div className="h-1.5 flex-1 bg-slate-100 rounded-full overflow-hidden">
                                                <div className="h-full bg-indigo-500 rounded-full transition-all duration-1000" style={{ width: `${(crawlerStatus?.progress?.current / crawlerStatus?.progress?.total) * 100 || 0}%` }}></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Analysis Feed */}
                        <div className="space-y-6">
                            <div className="flex items-center gap-4">
                                <h3 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight shrink-0">ประวัติการเฝ้าสังเกตล่าสุด</h3>
                                <div className="h-px bg-slate-200 dark:bg-slate-800 flex-1"></div>
                            </div>

                            {crawlerHistory.length === 0 ? (
                                <div className="text-center py-20 bg-white dark:bg-slate-900 rounded-[32px] border-2 border-dashed border-slate-200 dark:border-slate-800 text-slate-400 dark:text-slate-600 flex flex-col items-center gap-4">
                                    <svg className="w-12 h-12 opacity-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h10a2 2 0 012 2v2M7 7h10" /></svg>
                                    <span className="font-bold text-sm tracking-widest uppercase opacity-50">Pulse Monitor Offline</span>
                                </div>
                            ) : (
                                <div className="space-y-12 pb-20">
                                    {crawlerHistory.map((block, i) => (
                                        <div key={i} className="relative pl-10 border-l-4 border-indigo-100 dark:border-indigo-900/50 py-2">
                                            <div className="absolute -left-3 top-2 w-5 h-5 rounded-full bg-white dark:bg-slate-950 border-4 border-indigo-500 shadow-md shadow-indigo-100 dark:shadow-none"></div>

                                            <div className="flex items-center gap-4 mb-6">
                                                <div className="bg-indigo-600 text-white px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest shadow-lg shadow-indigo-100 dark:shadow-none">
                                                    {new Date(block.hour).toLocaleString('th-TH', { dateStyle: 'medium', timeStyle: 'short' })}
                                                </div>
                                                <div className="text-xs font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">{block.records.length} Incidents</div>
                                            </div>

                                            <div className="grid grid-cols-1 gap-4">
                                                {block.records.map((rec) => (
                                                    <AnalysisCard key={rec.id} rec={rec} onOpenDetail={handleOpenDetail} />
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                    /* DASHBOARD VIEW */
                    <div className="space-y-10 animate-fade-in max-w-6xl mx-auto">
                        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                            <div>
                                <h2 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight flex items-center gap-3">
                                    <span className="bg-blue-600 w-3 h-10 rounded-full shadow-lg shadow-blue-200 dark:shadow-none"></span>
                                    สรุปภาพรวมการตรวจสอบ
                                </h2>
                                <p className="text-slate-500 dark:text-slate-400 font-medium mt-2">สถิติการตรวจสอบข้อมูลผลิตภัณฑ์สุขภาพบนแพลตฟอร์มออนไลน์</p>
                            </div>
                            <div className="px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest shadow-sm">
                                อัปเดตล่าสุด: {new Date().toLocaleTimeString()}
                            </div>
                        </div>

                        {/* Top Stats Cards — Neutral */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                            {[
                                { label: 'ตรวจสอบทั้งหมด', value: history.length, icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2', color: 'slate' },
                                { label: 'พบเลขทะเบียน', value: history.filter(h => h.verified_credentials?.fda_info?.found || h.verified_credentials?.drug_reg?.found).length, icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z', color: 'emerald' },
                                { label: 'พบกรอบ/ฉลาก อย.', value: history.filter(h => h.verified_credentials?.fda_label?.found).length, icon: 'M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z', color: 'indigo' },
                                { label: 'พบข้อความภาษาไทย', value: history.filter(h => h.verified_credentials?.thai_language?.found).length, icon: 'M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129', color: 'blue' },
                            ].map((s, i) => (
                                <div key={i} className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-all">
                                    <div className={`w-12 h-12 rounded-2xl bg-${s.color}-50 dark:bg-${s.color}-500/10 text-${s.color}-600 dark:text-${s.color}-400 flex items-center justify-center mb-4`}>
                                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={s.icon} /></svg>
                                    </div>
                                    <div className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">{s.label}</div>
                                    <div className="text-3xl font-black text-slate-900 dark:text-white">{s.value}</div>
                                </div>
                            ))}
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                            {/* Data Completeness Chart */}
                            <div className="bg-white dark:bg-slate-900 p-8 rounded-[32px] border border-slate-200 dark:border-slate-800 shadow-sm">
                                <h3 className="text-lg font-black text-slate-800 dark:text-white mb-8 flex items-center gap-2">
                                    <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                    สถานะข้อมูลที่พบ
                                </h3>
                                <div className="space-y-6">
                                    {[
                                        { label: 'พบข้อมูลครบถ้วน', level: 'LOW', color: 'bg-blue-500' },
                                        { label: 'พบข้อมูลบางส่วน', level: 'MEDIUM', color: 'bg-slate-400' },
                                        { label: 'ต้องตรวจสอบเพิ่มเติม', level: 'HIGH', color: 'bg-orange-400' },
                                        { label: 'รอผลการตรวจ', level: 'UNKNOWN', color: 'bg-slate-300 dark:bg-slate-700' }
                                    ].map((r, i) => {
                                        const count = history.filter(h => h.risk_level === r.level || (r.level === 'UNKNOWN' && (h.risk_level === 'UNKNOWN' || h.risk_level === 'NEED_REVIEW'))).length;
                                        const percent = history.length > 0 ? (count / history.length) * 100 : 0;
                                        return (
                                            <div key={i}>
                                                <div className="flex justify-between items-end mb-2">
                                                    <span className="text-xs font-bold text-slate-600 dark:text-slate-400">{r.label}</span>
                                                    <span className="text-xs font-black text-slate-900 dark:text-white">{count} รายการ ({Math.round(percent)}%)</span>
                                                </div>
                                                <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                                    <div className={`h-full ${r.color} transition-all duration-1000`} style={{ width: `${percent}%` }}></div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* Category Distribution Chart */}
                            <div className="bg-white dark:bg-slate-900 p-8 rounded-[32px] border border-slate-200 dark:border-slate-800 shadow-sm">
                                <h3 className="text-lg font-black text-slate-800 dark:text-white mb-8 flex items-center gap-2">
                                    <svg className="w-5 h-5 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>
                                    หมวดหมู่ผลิตภัณฑ์
                                </h3>
                                <div className="space-y-6">
                                    {[
                                        { label: 'ผลิตภัณฑ์ยา (Drug)', cat: 'DRUG', color: 'bg-indigo-600' },
                                        { label: 'อาหาร / เสริมอาหาร (Food)', cat: 'FOOD', color: 'bg-blue-500' },
                                        { label: 'เครื่องสำอาง (Cosmetic)', cat: 'COSMETIC', color: 'bg-pink-500' },
                                        { label: 'ทั่วไป / อื่นๆ (General)', cat: 'GENERAL', color: 'bg-slate-400 dark:bg-slate-700' }
                                    ].map((c, i) => {
                                        const count = history.filter(h => h.product_type === c.cat).length;
                                        const percent = history.length > 0 ? (count / history.length) * 100 : 0;
                                        return (
                                            <div key={i}>
                                                <div className="flex justify-between items-end mb-2">
                                                    <span className="text-xs font-bold text-slate-600 dark:text-slate-400">{c.label}</span>
                                                    <span className="text-xs font-black text-slate-900 dark:text-white">{count} รายการ ({Math.round(percent)}%)</span>
                                                </div>
                                                <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                                    <div className={`h-full ${c.color} transition-all duration-1000`} style={{ width: `${percent}%` }}></div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>

                        {/* Items Needing Review — Neutral */}
                        <div className="bg-slate-900 dark:bg-black/40 p-8 rounded-[32px] shadow-2xl border border-white/10 dark:border-slate-800">
                            <div className="flex items-center justify-between mb-8">
                                <h3 className="text-xl font-black text-white flex items-center gap-3">
                                    <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                                    รายการที่ต้องตรวจสอบเพิ่มเติม
                                </h3>
                                <div className="text-[10px] font-black text-blue-400 uppercase tracking-widest border border-blue-500/30 px-3 py-1 rounded-full">
                                    {history.filter(h => h.risk_level === 'HIGH' || h.risk_level === 'UNKNOWN').length} รายการ
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {history.filter(h => h.risk_level === 'HIGH' || h.risk_level === 'UNKNOWN').slice(0, 4).map((h, i) => (
                                    <div key={i} className="bg-white/5 dark:bg-white/5 border border-white/10 dark:border-slate-800 p-5 rounded-2xl flex gap-4 hover:bg-white/10 dark:hover:bg-slate-800/60 transition-all cursor-pointer" onClick={() => handleOpenDetail(h.id)}>
                                        <div className="w-12 h-12 bg-blue-500/20 text-blue-400 rounded-xl flex items-center justify-center shrink-0">
                                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                        </div>
                                        <div className="min-w-0">
                                            <div className="text-sm font-bold text-white truncate mb-1">{h.product_name}</div>
                                            <div className="text-[10px] text-slate-400 font-medium line-clamp-1">{h.risk_reason}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </main>

            {/* Premium Modals */}
            <DeepDiveModal isOpen={!!selectedDetailId} onClose={() => setSelectedDetailId(null)} detailId={selectedDetailId} detailData={detailData} loading={loadingDetail} />
            <EvidenceModal isOpen={!!activeCredentialDetail} onClose={() => setActiveCredentialDetail(null)} activeCredentialDetail={activeCredentialDetail} result={result} />
            <SettingsModal
                isOpen={isSettingsOpen}
                onClose={() => setIsSettingsOpen(false)}
                settings={settings}
                onSaveSettings={saveSettings}
                isSaving={isSavingConfig}
            />
        </div>
    );
}