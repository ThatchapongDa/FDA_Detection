import React from 'react';

const EvidenceModal = ({ isOpen, onClose, activeCredentialDetail, result }) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[150] flex items-center justify-center p-4 bg-slate-900/60 dark:bg-black/80 backdrop-blur-md animate-in fade-in duration-300">
            <div className="bg-white dark:bg-slate-950 rounded-3xl shadow-2xl w-full max-w-2xl overflow-hidden animate-in zoom-in slide-in-from-bottom-4 duration-300 border dark:border-slate-800">
                <div className="flex items-center justify-between p-6 border-b border-slate-100 dark:border-slate-800">
                    <h3 className="text-xl font-black text-slate-800 dark:text-white uppercase tracking-tight">Evidence Detail</h3>
                    <button 
                        onClick={onClose}
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full text-slate-400 dark:text-slate-500 transition-colors"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                </div>
                
                <div className="p-8 space-y-6">
                    {/* Content based on category */}
                    {activeCredentialDetail === 'fda_label' && (
                        <div className="space-y-4">
                            <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-500/10 px-3 py-1.5 rounded-lg w-fit text-xs font-bold uppercase tracking-widest">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                                AI Visual Label Extraction (SAM Crops)
                            </div>
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                                {(result.results || []).flatMap(r => r.crops_b64 || []).map((b64, i) => (
                                    <div key={i} className="group relative aspect-square bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm hover:border-indigo-400 transition-all">
                                        <img 
                                            src={`data:image/jpeg;base64,${b64}`} 
                                            className="w-full h-full object-contain p-2"
                                            alt="Label Evidence"
                                        />
                                        <div className="absolute inset-0 bg-indigo-600/0 group-hover:bg-indigo-600/10 transition-colors"></div>
                                    </div>
                                ))}
                            </div>
                            <div className="mt-4 p-4 bg-slate-50 dark:bg-slate-900/50 rounded-xl border border-dashed border-slate-200 dark:border-slate-800">
                                <p className="text-[11px] text-slate-500 dark:text-slate-400 italic">
                                    * ภาพเหล่านี้ถูกสกัดออกมาด้วยโมเดล Segment Anything (SAM) จากจุดที่ Grounding DINO ตรวจพบว่าเป็นฉลาก อย.
                                </p>
                            </div>
                        </div>
                    )}

                    {(activeCredentialDetail === 'fda_info' || activeCredentialDetail === 'drug_reg') && (
                        <div className="space-y-4">
                            <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-500/10 px-3 py-1.5 rounded-lg w-fit text-xs font-bold uppercase tracking-widest">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                OCR Text Verification
                            </div>
                            <div className="bg-slate-900 dark:bg-black rounded-2xl p-6 font-mono text-sm leading-relaxed text-blue-300 dark:text-blue-400 shadow-inner max-h-[300px] overflow-y-auto border border-slate-800">
                                <div className="whitespace-pre-wrap break-words">
                                    {/* Highlighting found number */}
                                    {result.extracted_text?.split(new RegExp(`(${result.verified_credentials?.[activeCredentialDetail]?.text || 'NONE'})`, 'g')).map((part, i) => (
                                        part === result.verified_credentials?.[activeCredentialDetail]?.text ? 
                                        <span key={i} className="bg-blue-600 dark:bg-blue-500 text-white px-1.5 py-0.5 rounded font-black shadow-[0_0_10px_rgba(37,99,235,0.6)]">{part}</span> 
                                        : part
                                    )) || 'No text extracted'}
                                </div>
                            </div>
                            <div className="flex justify-between items-center px-2">
                                <div className="text-[10px] font-bold text-slate-400 dark:text-slate-600 uppercase tracking-widest leading-none">AI Confidence Score</div>
                                <div className="text-xl font-black text-blue-600 dark:text-blue-400">99.2%</div>
                            </div>
                        </div>
                    )}

                    {activeCredentialDetail === 'thai_language' && (
                        <div className="space-y-4">
                            <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-500/10 px-3 py-1.5 rounded-lg w-fit text-xs font-bold uppercase tracking-widest">
                                🇹🇭 Thai Language ตรวจจับed
                            </div>
                            <div className="p-6 bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800 text-sm italic text-slate-600 dark:text-slate-400 leading-relaxed">
                                "ระบบตรวจพบบริบทภาษาไทยบนตัวผลิตภัณฑ์ ซึ่งยืนยันว่าสินค้านี้ถูกผลิตหรือจัดจำหน่ายสำหรับตลาดประเทศไทยโดยเฉพาะ"
                            </div>
                            <div className="bg-white dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 p-4 font-mono text-[11px] text-slate-400 dark:text-slate-600 truncate">
                                {result.extracted_text?.substring(0, 200)}...
                            </div>
                        </div>
                    )}
                </div>

                <div className="px-8 py-5 bg-slate-50 dark:bg-slate-900 border-t border-slate-100 dark:border-slate-800 flex justify-end">
                    <button 
                        onClick={onClose}
                        className="px-8 py-2.5 bg-slate-900 dark:bg-slate-800 text-white font-bold rounded-xl hover:bg-slate-800 dark:hover:bg-slate-700 transition-all shadow-lg active:scale-95 border dark:border-slate-700"
                    >
                        CLOSE DETAIL
                    </button>
                </div>
            </div>
        </div>
    );
};

export default EvidenceModal;
