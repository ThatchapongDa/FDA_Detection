import React, { useState } from 'react';

const SettingsModal = ({ isOpen, onClose, settings, onSaveSettings, isSaving }) => {
    const [localSettings, setLocalSettings] = useState({
        ...settings,
        crawler_keywords: settings?.crawler_keywords || []
    });
    const [newKeyword, setNewKeyword] = useState('');

    if (!isOpen) return null;

    const handleSave = () => {
        onSaveSettings(localSettings);
        onClose();
    };

    const addKeyword = () => {
        if (newKeyword && !localSettings.crawler_keywords.includes(newKeyword)) {
            setLocalSettings({
                ...localSettings,
                crawler_keywords: [...localSettings.crawler_keywords, newKeyword]
            });
            setNewKeyword('');
        }
    };

    const removeKeyword = (kw) => {
        setLocalSettings({
            ...localSettings,
            crawler_keywords: localSettings.crawler_keywords.filter(k => k !== kw)
        });
    };

    return (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-slate-900/90 dark:bg-black/90 backdrop-blur-md p-4">
            <div className="bg-white dark:bg-slate-950 rounded-3xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden animate-in zoom-in duration-200 border border-slate-200 dark:border-slate-800">
                <div className="flex justify-between items-center p-6 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-100 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 rounded-xl">
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                        </div>
                        <h2 className="text-xl font-black text-slate-800 dark:text-white">ตั้งค่าระบบ (Configuration)</h2>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-full transition-colors">
                        <svg className="w-6 h-6 text-slate-400 dark:text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div className="p-8 overflow-y-auto space-y-8 custom-scrollbar">
                    {/* Crawler Settings */}
                    <section className="space-y-4">
                        <h3 className="text-xs font-black text-slate-400 dark:text-slate-600 uppercase tracking-widest flex items-center gap-2">
                            <span className="w-1.5 h-1.5 bg-blue-500 rounded-full"></span>
                            พฤติกรรมการทำงาน (Crawler Behavior)
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">ระยะเวลาหน่วงเพื่อป้องกันการบล็อก (วินาที)</label>
                                <input
                                    type="number"
                                    className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                    value={localSettings.crawler_delay}
                                    onChange={(e) => setLocalSettings({ ...localSettings, crawler_delay: parseInt(e.target.value) })}
                                />
                                <p className="text-[10px] text-slate-400 dark:text-slate-600">ระยะเวลาพักระบบระหว่างสแกนแต่ละชิ้น</p>
                            </div>
                            <div className="space-y-2">
                                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">จำกัดการสแกน (ต่อหนึ่งคีย์เวิร์ด)</label>
                                <input
                                    type="number"
                                    className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                    value={localSettings.max_scan_limit}
                                    onChange={(e) => setLocalSettings({ ...localSettings, max_scan_limit: parseInt(e.target.value) })}
                                />
                                <p className="text-[10px] text-slate-400 dark:text-slate-600">จำนวนสินค้าสูงสุดที่จะสแกนต่อหนึ่งคีย์เวิร์ด</p>
                            </div>
                        </div>
                    </section>

                    {/* Filter Settings */}
                    <section className="space-y-4">
                        <h3 className="text-xs font-black text-slate-400 dark:text-slate-600 uppercase tracking-widest flex items-center gap-2">
                            <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
                            การกรองสินค้า (Product Filtering)
                        </h3>
                        <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800">
                            <div>
                                <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">ระบบกรองสินค้าอัจฉริยะ (Smart Filter)</h4>
                                <p className="text-xs text-slate-500 dark:text-slate-500">ข้ามการสแกนหากไม่ใช่สินค้าที่อยู่ในกลุ่มเป้าหมาย (ยา/อาหารเสริม)</p>
                            </div>
                            <button
                                onClick={() => setLocalSettings({ ...localSettings, enable_medicine_filter: !localSettings.enable_medicine_filter })}
                                className={`w-12 h-6 rounded-full transition-colors relative ${localSettings.enable_medicine_filter ? 'bg-blue-600' : 'bg-slate-300 dark:bg-slate-700'}`}
                            >
                                <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${localSettings.enable_medicine_filter ? 'left-7' : 'left-1'}`}></div>
                            </button>
                        </div>
                    </section>

                    {/* Keywords Settings */}
                    <section className="space-y-4">
                        <h3 className="text-xs font-black text-slate-400 dark:text-slate-600 uppercase tracking-widest flex items-center gap-2">
                            <span className="w-1.5 h-1.5 bg-purple-500 rounded-full"></span>
                            คีย์เวิร์ดเป้าหมาย (Target Keywords)
                        </h3>
                        <div className="space-y-3">
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    placeholder="เพิ่มคีย์เวิร์ดใหม่..."
                                    className="flex-1 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-2 text-sm text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500 placeholder:text-slate-400 dark:placeholder:text-slate-600"
                                    value={newKeyword}
                                    onChange={(e) => setNewKeyword(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && addKeyword()}
                                />
                                <button
                                    onClick={addKeyword}
                                    className="px-4 py-2 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-500 transition-all text-sm"
                                >
                                    เพิ่ม
                                </button>
                            </div>
                            <div className="flex flex-wrap gap-2 p-4 bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800 min-h-[100px]">
                                {localSettings.crawler_keywords.map((kw, i) => (
                                    <span key={i} className="px-3 py-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 rounded-lg text-xs font-bold flex items-center gap-2 shadow-sm animate-fade-in hover:border-red-200 dark:hover:border-red-900/50 hover:text-red-500 transition-all group">
                                        {kw}
                                        <button onClick={() => removeKeyword(kw)} className="text-slate-300 dark:text-slate-600 group-hover:text-red-500 transition-colors">
                                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                                            </svg>
                                        </button>
                                    </span>
                                ))}
                                {localSettings.crawler_keywords.length === 0 && (
                                    <div className="w-full flex items-center justify-center text-slate-400 dark:text-slate-600 italic text-xs">ไม่มีคีย์เวิร์ดในรายการ</div>
                                )}
                            </div>
                        </div>
                    </section>
                </div>

                <div className="p-6 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-6 py-2.5 text-sm font-bold text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-xl transition-all"
                    >
                        ยกเลิก
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={isSaving}
                        className={`px-8 py-2.5 text-sm font-bold bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition-all shadow-lg shadow-blue-500/20 dark:shadow-none ${isSaving ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105 active:scale-95'}`}
                    >
                        {isSaving ? 'กำลังบันทึก...' : 'บันทึกการตั้งค่า'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SettingsModal;
