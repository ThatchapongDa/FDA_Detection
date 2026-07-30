import React from 'react';
import ImageWithBoxes from './ImageWithBoxes';
import { getStatusConfig } from '../utils/helpers';

const DeepDiveModal = ({ isOpen, onClose, detailId, detailData, loading }) => {
    if (!isOpen) return null;

    const result = detailData; // Alias for consistency with index.js naming

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/90 dark:bg-black/95 backdrop-blur-md p-4 md:p-8">
            <div className="bg-[#f8fafc] dark:bg-slate-950 rounded-[40px] shadow-[0_0_100px_rgba(0,0,0,0.5)] w-full max-w-6xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in duration-300 border border-white/20 dark:border-slate-800">

                {/* Header: Action Bar */}
                <div className="flex justify-between items-center px-8 py-5 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 shrink-0">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-200 dark:shadow-none">
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                            </svg>
                        </div>
                        <div>
                            <h2 className="text-xl font-black text-slate-800 dark:text-white tracking-tight">เจาะลึกข้อมูลหลักฐานจาก AI</h2>
                            <p className="text-[10px] text-slate-400 dark:text-slate-500 font-black uppercase tracking-[0.2em]">รหัสการตรวจสอบ: {detailId}</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="group p-3 bg-slate-100 dark:bg-slate-800 hover:bg-red-500 text-slate-400 dark:text-slate-500 hover:text-white rounded-2xl transition-all duration-300 border border-slate-200 dark:border-slate-700 hover:border-red-400 shadow-sm"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Main Scrollable Body */}
                <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center py-32 space-y-6">
                            <div className="relative">
                                <div className="w-20 h-20 border-4 border-slate-100 dark:border-slate-800 border-t-indigo-600 rounded-full animate-spin"></div>
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <div className="w-10 h-10 bg-indigo-100 dark:bg-indigo-900 rounded-full animate-pulse"></div>
                                </div>
                            </div>
                            <span className="text-xs font-black uppercase tracking-[0.3em] text-slate-400 dark:text-slate-600 animate-pulse">กำลังประมวลผลข้อมูลหลักฐาน...</span>
                        </div>
                    ) : result ? (
                        <div className="space-y-8">

                            {/* Top Tier: The Certification Header */}
                            <div className="bg-white dark:bg-slate-900 p-8 rounded-[32px] border border-slate-200 dark:border-slate-800 shadow-xl shadow-slate-200/50 dark:shadow-none relative overflow-hidden">
                                <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600"></div>

                                <div className="flex flex-col gap-6">
                                    <div className="flex flex-col lg:flex-row justify-between items-start gap-6">
                                        <div className="flex-1 min-w-0">
                                            <a
                                                href={result.product_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-2xl font-black text-slate-900 dark:text-white mb-3 block leading-tight hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
                                            >
                                                {result.product_name || 'Generic Product Data'}
                                            </a>
                                            <div className="flex flex-wrap gap-2">
                                                <span className="px-3 py-1 bg-indigo-600 text-white rounded-full text-[10px] font-black uppercase tracking-widest">{result.product_type}</span>
                                                <span className="px-3 py-1 bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 rounded-full text-[10px] font-bold uppercase tracking-widest border border-slate-200 dark:border-slate-700">{result.product_category}</span>
                                                <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border shadow-sm ${getStatusConfig(result.risk_level, result.status).colorClass}`}>
                                                    ผลสรุปเบื้องต้น: {getStatusConfig(result.risk_level, result.status).label}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Verification Pillars Grid */}
                                    <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
                                        {[
                                            { 
                                                id: 'fda_info', label: 'ข้อมูล อย. (FDA Info)', 
                                                found: result.verified_credentials?.fda_info?.found, 
                                                desc: result.verified_credentials?.fda_info?.text || 'ไม่พบเลขจดแจ้ง',
                                                missingMsg: 'ไม่พบเลขสารบบอาหาร / เลขทะเบียน อย. ทั้งบนภาพและในรายละเอียดสินค้า'
                                            },
                                            { 
                                                id: 'fda_label', label: 'ฉลาก อย. (FDA Label)', 
                                                found: result.verified_credentials?.fda_label?.found, 
                                                desc: result.verified_credentials?.fda_label?.found ? `พบสัญลักษณ์บนบรรจุภัณฑ์` : 'ไม่พบสัญลักษณ์ อย.',
                                                missingMsg: 'AI ไม่ตรวจพบกล่องหรือสัญลักษณ์ อย. บนบรรจุภัณฑ์จากการวิเคราะห์ภาพ'
                                            },
                                            { 
                                                id: 'thai_language', label: 'ภาษาไทย (Thai Label)', 
                                                found: result.verified_credentials?.thai_language?.found, 
                                                desc: result.verified_credentials?.thai_language?.found ? 'พบฉลากภาษาไทย' : 'ไม่พบภาษาไทย',
                                                missingMsg: 'ไม่พบข้อความภาษาไทยเพียงพอบนฉลาก อาจเป็นสินค้านำเข้าที่ไม่มีฉลากไทย'
                                            },
                                            { 
                                                id: 'drug_reg', label: 'ทะเบียนยา (Drug Reg)', 
                                                found: result.verified_credentials?.drug_reg?.found, 
                                                desc: result.verified_credentials?.drug_reg?.text || 'ไม่พบทะเบียนตำรับยา',
                                                missingMsg: 'ไม่พบเลขทะเบียนตำรับยา (รูปแบบ Reg.No.) บนภาพหรือรายละเอียดสินค้า'
                                            },
                                            { 
                                                id: 'ad_license', label: 'ใบอนุญาตโฆษณา (Ad Lic)', 
                                                found: result.verified_credentials?.ad_license_info?.found, 
                                                desc: result.verified_credentials?.ad_license_info?.text || 'ไม่พบการขอโฆษณา',
                                                missingMsg: 'ไม่พบเลขที่ใบอนุญาตโฆษณา (ฆพ.) ซึ่งจำเป็นสำหรับสินค้าที่มีการโฆษณาคุณสมบัติด้านสุขภาพ'
                                            }
                                        ].map((v) => (
                                            <div key={v.id} className={`p-4 rounded-2xl border-2 transition-all ${v.found ? 'bg-emerald-50/50 dark:bg-emerald-500/10 border-emerald-200 dark:border-emerald-500/30' : 'bg-red-50/50 dark:bg-red-500/5 border-red-100 dark:border-red-500/20'}`}>
                                                <div className="flex items-center gap-3 mb-2">
                                                    <div className={`p-2 rounded-xl ${v.found ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-200 dark:shadow-none' : 'bg-red-400 text-white shadow-sm shadow-red-200 dark:shadow-none'}`}>
                                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            {v.found ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" /> : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M6 18L18 6M6 6l12 12" />}
                                                        </svg>
                                                    </div>
                                                    <div className={`text-[10px] font-black uppercase tracking-wider ${v.found ? 'text-emerald-700 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
                                                        {v.found ? 'ตรวจพบหลักฐาน' : 'ไม่พบ'}
                                                    </div>
                                                </div>
                                                <div className="text-[11px] font-bold text-slate-800 dark:text-slate-200 leading-tight mb-1">{v.label}</div>
                                                {v.found 
                                                    ? <div className="text-[10px] text-slate-500 dark:text-slate-400 font-medium line-clamp-1">{v.desc}</div>
                                                    : <div className="text-[10px] text-red-600 dark:text-red-400 font-semibold leading-tight">{v.missingMsg}</div>
                                                }
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* [NEW] Legal Violation Alert — shown when a violation is detected */}
                            {result.legal_compliance && result.legal_compliance.length > 0 && (
                                <div className="bg-rose-50 dark:bg-rose-950/40 border-2 border-rose-200 dark:border-rose-500/30 rounded-[28px] p-6 flex items-start gap-5 shadow-sm shadow-rose-100 dark:shadow-none">
                                    <div className="p-3 bg-rose-600 text-white rounded-2xl shadow-lg shadow-rose-300 dark:shadow-rose-900/50 shrink-0">
                                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                        </svg>
                                    </div>
                                    <div className="flex-1">
                                        <div className="text-[10px] font-black text-rose-400 dark:text-rose-500 uppercase tracking-[0.25em] mb-3">ข้อกฎหมายที่เกี่ยวข้อง</div>
                                        <div className="space-y-3">
                                            {result.legal_compliance.map((v, idx) => (
                                                <div key={idx} className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 bg-white/60 dark:bg-rose-900/20 rounded-2xl px-4 py-3 border border-rose-100 dark:border-rose-500/20">
                                                    <div className="shrink-0">
                                                        <span className="text-[11px] font-black text-rose-600 dark:text-rose-400 bg-rose-100 dark:bg-rose-500/20 px-3 py-1 rounded-full border border-rose-200 dark:border-rose-500/30 whitespace-nowrap">
                                                            {v.law} {v.section}
                                                        </span>
                                                    </div>
                                                    <p className="text-sm font-bold text-rose-900 dark:text-rose-200 leading-tight">
                                                        {v.details}
                                                    </p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Middle Tier: Data Comparison */}
                            <div className="grid grid-cols-12 gap-8">
                                {/* Left Side: Shop Data Record */}
                                <div className="col-span-12 lg:col-span-4 space-y-4">
                                    <div className="flex items-center gap-2 px-2">
                                        <div className="w-1.5 h-4 bg-amber-400 rounded-full"></div>
                                        <h4 className="text-[11px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em]">ข้อมูลที่ร้านค้าระบุ</h4>
                                    </div>
                                    <div className="space-y-4">
                                        <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden">
                                            <div className="text-[10px] font-black text-slate-300 dark:text-slate-600 uppercase mb-4 tracking-widest">พยานหลักฐานจากหน้าร้านค้า</div>
                                            <div className="space-y-4">
                                                <div>
                                                    <div className="text-[9px] font-bold text-slate-400 dark:text-slate-500 uppercase mb-1.5 flex items-center gap-2">
                                                        <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full"></span>
                                                        หมายเลข อย. / ทะเบียนยา
                                                    </div>
                                                    <div className="text-lg font-mono font-black text-slate-800 dark:text-slate-200 bg-slate-50 dark:bg-slate-950 p-3 rounded-xl border border-slate-100 dark:border-slate-800 shadow-inner break-words">
                                                        {result.scraped_fda_number || 'ไม่พบการระบุ'}
                                                    </div>
                                                </div>
                                                
                                                {result.scraped_ad_license && (
                                                    <div>
                                                        <div className="text-[9px] font-bold text-slate-400 dark:text-slate-500 uppercase mb-1.5 flex items-center gap-2">
                                                            <span className="w-1.5 h-1.5 bg-amber-400 rounded-full"></span>
                                                            หมายเลข ฆพ. (ใบอนุญาตโฆษณา)
                                                        </div>
                                                        <div className="text-lg font-mono font-black text-slate-800 dark:text-slate-200 bg-amber-50/30 dark:bg-amber-500/5 p-3 rounded-xl border border-amber-100 dark:border-amber-500/20 shadow-inner break-words">
                                                            {result.scraped_ad_license}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                        <div className="bg-white/50 dark:bg-slate-900/30 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-500 leading-relaxed italic">
                                            "หมายเหตุ: หมายเลขทะเบียนด้านบนถูกดึงมาจากข้อความรายละเอียดสินค้าที่ผู้ขายระบุไว้ในร้านค้าโดยตรง"
                                        </div>
                                    </div>
                                </div>

                                {/* Right Side: Visual Evidence & Raw Stream */}
                                <div className="col-span-12 lg:col-span-8 space-y-6">
                                    <div className="flex items-center justify-between px-2">
                                        <div className="flex items-center gap-2">
                                            <div className="w-1.5 h-4 bg-indigo-500 rounded-full"></div>
                                            <h4 className="text-[11px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em]">ข้อมูลหลักฐานจากภาพสินค้า</h4>
                                        </div>
                                        <span className="text-[10px] font-black text-indigo-500 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-500/10 px-3 py-1 rounded-full border border-indigo-100 dark:border-indigo-500/20 shadow-sm">
                                            วิเคราะห์แล้ว {result.results?.length || 0} รูปภาพ
                                        </span>
                                    </div>

                                    {/* Evidence Gallery */}
                                    <div className="grid grid-cols-2 gap-4">
                                        {result.results?.map((res, i) => (
                                            <div key={i} className="group bg-white dark:bg-slate-900 p-3 rounded-[32px] border border-slate-200 dark:border-slate-800 shadow-sm transition-all duration-300 hover:shadow-xl hover:scale-[1.02]">
                                                <div className="aspect-video relative rounded-2xl overflow-hidden bg-slate-900 border border-slate-100 dark:border-slate-700">
                                                    <ImageWithBoxes url={res.url} detections={res.detections || []} />
                                                    <div className="absolute top-3 left-3 px-2 py-1 bg-black/40 backdrop-blur-md rounded-full text-[8px] font-black text-white uppercase tracking-widest border border-white/10">รูปที่ {i + 1}</div>
                                                </div>
                                                {res.crops_b64?.length > 0 && (
                                                    <div className="mt-3 flex flex-wrap gap-2">
                                                        {res.crops_b64.map((b64, ci) => (
                                                            <img key={ci} src={`data:image/jpeg;base64,${b64}`} className="h-12 w-auto rounded-lg border border-slate-100 dark:border-slate-700 shadow-sm hover:scale-125 transition-transform" alt="AI Crop" />
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>

                                    {/* OCR Stream */}
                                    <div className="bg-slate-900 dark:bg-black/50 rounded-[32px] p-8 shadow-2xl relative overflow-hidden group border border-slate-800">
                                        <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 blur-[60px] rounded-full group-hover:bg-indigo-500/20 transition-all duration-500"></div>
                                        <div className="text-[10px] font-black text-slate-500 dark:text-slate-600 uppercase mb-4 tracking-[0.3em] flex items-center gap-2">
                                            <svg className="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                            ข้อมูลดิบที่อ่านได้จากภาพ (OCR Stream)
                                        </div>
                                        <div className="max-h-[300px] overflow-y-auto pr-4 scrollbar-thin scrollbar-thumb-white/10">
                                            <p className="text-emerald-400 dark:text-emerald-500 font-mono text-[11px] leading-relaxed whitespace-pre-wrap selection:bg-emerald-500/20">
                                                {result.extracted_text || '// ไม่พบข้อมูลตัวอักษรที่อ่านได้'}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center py-24 text-red-500 space-y-4">
                            <svg className="w-16 h-16 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                            <span className="text-sm font-black uppercase tracking-widest">Internal Engine Conflict - Metadata Unresolved</span>
                        </div>
                    )}
                </div>

                {/* Footer: Status Summary */}
                <div className="px-8 py-5 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 shrink-0 flex justify-between items-center">
                    <div className="flex items-center gap-6">
                        <div className="flex flex-col">
                            <span className="text-[9px] font-black text-slate-400 dark:text-slate-600 uppercase tracking-widest">วันเวลาที่วิเคราะห์</span>
                            <span className="text-xs font-bold text-slate-600 dark:text-slate-400">{result?.created_at ? new Date(result.created_at).toLocaleString('th-TH') : '—'}</span>
                        </div>
                        <div className="w-px h-8 bg-slate-100 dark:bg-slate-800"></div>
                        <div className="flex flex-col">
                            <span className="text-[9px] font-black text-slate-400 dark:text-slate-600 uppercase tracking-widest">ระดับความสมบูรณ์ของข้อมูล</span>
                            <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 tracking-tight flex items-center gap-1.5">
                                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span>
                                วิเคราะห์ด้วยความละเอียดสูง (High Fidelity)
                            </span>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="px-6 py-2 bg-slate-900 dark:bg-slate-700 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-slate-800 dark:hover:bg-slate-600 transition-all shadow-xl shadow-slate-200 dark:shadow-none active:scale-95"
                    >
                        ปิดหน้าต่างข้อมูลเชิงลึก
                    </button>
                </div>
            </div>

            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 6px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: #e2e8f0;
                    border-radius: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: #cbd5e1;
                }
            `}</style>
        </div>
    );
};

export default DeepDiveModal;
