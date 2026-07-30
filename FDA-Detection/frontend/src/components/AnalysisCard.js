import React from 'react';
import { getStatusConfig, formatTime, normalizeFda } from '../utils/helpers';

const AnalysisCard = ({ rec, onOpenDetail }) => {
    const config = getStatusConfig(rec.risk_level, rec.status);
    const hasFdaตรวจจับed = rec.fda_numbers && rec.fda_numbers.length > 0;
    const reportedFda = rec.scraped_fda_number ? normalizeFda(rec.scraped_fda_number) : null;
    const score = rec.score !== undefined ? Math.round(rec.score * 100) : null;

    // Count how many credentials were found
    const vc = rec.verified_credentials || {};
    const foundCount = [vc.fda_info?.found, vc.fda_label?.found, vc.thai_language?.found, vc.drug_reg?.found].filter(Boolean).length;

    // Neutral compliance status (NOT risk/safety judgment)
    const complianceConfig = {
        4: { label: 'พบข้อมูลครบถ้วน', icon: '●', accent: 'text-blue-400 bg-blue-500/10 border-blue-500/25' },
        3: { label: 'พบข้อมูลครบถ้วน', icon: '●', accent: 'text-blue-400 bg-blue-500/10 border-blue-500/25' },
        2: { label: 'พบข้อมูลบางส่วน', icon: '◐', accent: 'text-slate-400 bg-slate-500/10 border-slate-500/25' },
        1: { label: 'พบข้อมูลบางส่วน', icon: '◐', accent: 'text-slate-400 bg-slate-500/10 border-slate-500/25' },
        0: { label: 'ตรวจสอบเพิ่มเติม', icon: '○', accent: 'text-orange-400 bg-orange-500/10 border-orange-500/25' },
    }[foundCount] || { label: 'รอผลตรวจ', icon: '…', accent: 'text-slate-500 bg-slate-800 border-slate-700' };

    return (
        <div className="bg-white rounded-[32px] border border-slate-200 transition-all duration-500 hover:shadow-2xl hover:shadow-indigo-100 hover:scale-[1.01] overflow-hidden group/card shadow-sm">
            <div className="flex flex-col lg:flex-row min-h-[240px]">
                {/* LEFT: Product Image & Type */}
                <div className="w-full lg:w-[240px] shrink-0 relative overflow-hidden bg-slate-50 border-r border-slate-100">
                    {rec.product_image ? (
                        <div className="relative h-56 lg:h-full">
                            <img 
                                src={rec.product_image} 
                                alt={rec.product_name || 'Product'} 
                                className="w-full h-full object-cover transition-transform duration-700 group-hover/card:scale-110"
                                onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-slate-900/60 via-transparent to-transparent"></div>
                        </div>
                    ) : (
                        <div className="w-full h-56 lg:h-full bg-slate-100 flex items-center justify-center">
                            <svg className="w-16 h-16 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                        </div>
                    )}
                    
                    {/* Floating Badges on Image */}
                    <div className="absolute top-4 left-4 flex flex-col gap-2">
                        {rec.product_type && rec.product_type !== 'UNKNOWN' && (
                            <span className="px-4 py-1.5 bg-indigo-600 text-white text-[11px] font-black rounded-full shadow-lg border border-indigo-500 uppercase tracking-widest">
                                {rec.product_type}
                            </span>
                        )}
                        <span className={`px-4 py-1.5 rounded-full text-[11px] font-black shadow-lg border backdrop-blur-md bg-white/90 ${getStatusConfig(rec.risk_level, rec.status).colorClass.replace('bg-', 'text-').replace('text-', 'text-')}`}>
                            {getStatusConfig(rec.risk_level, rec.status).label}
                        </span>
                    </div>
                </div>

                {/* CENTER: Main Info & Summary */}
                <div className="flex-1 p-8 flex flex-col justify-between gap-6">
                    <div>
                        <div className="flex justify-between items-start mb-4">
                            <div className="flex items-center gap-3">
                                <div className={`w-3 h-3 rounded-full ${foundCount >= 3 ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.6)]' : 'bg-amber-500 animate-pulse'}`}></div>
                                <span className="text-xs font-black text-slate-500 uppercase tracking-[0.15em]">{complianceConfig.label} ({foundCount}/4)</span>
                            </div>
                            <span className="text-xs font-mono text-slate-400 font-black bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-200 shadow-sm">
                                {formatTime(rec.created_at)}
                            </span>
                        </div>

                        <a href={rec.product_url} target="_blank" rel="noopener noreferrer" 
                           className="text-xl font-black text-slate-900 hover:text-indigo-600 transition-all line-clamp-2 leading-tight mb-6 group/title" 
                           title={rec.product_name}>
                            <span className="bg-left-bottom bg-gradient-to-r from-indigo-600 to-indigo-600 bg-[length:0%_2px] bg-no-repeat group-hover/title:bg-[length:100%_2px] transition-all duration-500">
                                {rec.product_name || rec.product_url}
                            </span>
                        </a>

                        {/* Evidence Pills */}
                        <div className="flex flex-wrap gap-3 mb-4">
                            {[
                                { label: 'เลข อย.', found: vc.fda_info?.found },
                                { label: 'ฉลาก อย.', found: vc.fda_label?.found },
                                { label: 'ภาษาไทย', found: vc.thai_language?.found },
                                { label: 'ทะเบียนยา', found: vc.drug_reg?.found }
                            ].map((v, i) => (
                                <div key={i} className={`flex items-center gap-2 px-4 py-2 rounded-2xl border transition-all shadow-sm ${
                                    v.found 
                                    ? 'bg-emerald-50 text-emerald-800 border-emerald-200' 
                                    : 'bg-slate-50 text-slate-400 border-slate-200'
                                }`}>
                                    <div className={`w-5 h-5 rounded-full flex items-center justify-center ${v.found ? 'bg-emerald-500 text-white shadow-sm' : 'bg-slate-200 text-slate-400'}`}>
                                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="4" d={v.found ? "M5 13l4 4L19 7" : "M6 18L18 6M6 6l12 12"} />
                                        </svg>
                                    </div>
                                    <span className="text-xs font-black tracking-tight">{v.label}</span>
                                </div>
                            ))}
                        </div>

                        {/* [NEW] Missing Information Summary — shows exactly what's absent */}
                        {(() => {
                            const missingItems = [
                                !vc.fda_info?.found && { key: 'fda', label: 'ไม่พบเลขจดแจ้ง อย. / เลขสารบบอาหาร', desc: 'ไม่พบเลขทะเบียนทั้งบนสินค้าและในข้อมูลร้านค้า' },
                                !vc.fda_label?.found && { key: 'label', label: 'ไม่พบฉลากหรือสัญลักษณ์ อย.', desc: 'AI ไม่ตรวจพบกล่องหรือสัญลักษณ์ อย. บนบรรจุภัณฑ์' },
                                !vc.thai_language?.found && { key: 'thai', label: 'ไม่พบฉลากภาษาไทย', desc: 'ไม่พบข้อความภาษาไทยเพียงพอบนสินค้า (อาจเป็นสินค้านอก)' },
                                !vc.drug_reg?.found && rec.product_type === 'DRUG' && { key: 'drug', label: 'ไม่พบเลขทะเบียนตำรับยา', desc: 'สินค้าจัดอยู่ในหมวดยา แต่ไม่พบเลขทะเบียนตำรับยา' },
                            ].filter(Boolean);

                            if (missingItems.length === 0 || ['MATCH', 'SKIPPED', 'PRODUCT_ONLY'].includes(rec.risk_level)) return null;

                            return (
                                <div className="mb-4 bg-amber-50 border border-amber-200 rounded-2xl px-4 py-3">
                                    <div className="text-[10px] font-black text-amber-500 uppercase tracking-[0.2em] mb-2 flex items-center gap-1.5">
                                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>
                                        ข้อมูลที่ไม่พบ ({missingItems.length} รายการ)
                                    </div>
                                    <ul className="space-y-1">
                                        {missingItems.map(item => (
                                            <li key={item.key} className="flex items-start gap-2 text-xs text-amber-800">
                                                <span className="text-amber-400 font-black mt-0.5 shrink-0">—</span>
                                                <span><span className="font-black">{item.label}</span><span className="text-amber-600 font-medium"> · {item.desc}</span></span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            );
                        })()}
                    </div>

                    {/* AI Reasoning Box - High Visibility */}
                    <div className="bg-indigo-50 p-5 rounded-3xl border-2 border-indigo-100 flex items-start gap-4 shadow-sm shadow-indigo-100/50">
                        <div className="p-2 bg-indigo-600 text-white rounded-2xl shadow-lg shadow-indigo-200 shrink-0">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        </div>
                        <div>
                            <div className="text-[10px] font-black text-indigo-400 uppercase tracking-[0.2em] mb-1">AI Analytical Insight</div>
                            <p className="text-sm text-indigo-900 font-bold leading-relaxed line-clamp-3">
                                {rec.risk_reason || config.fact}
                            </p>
                        </div>
                    </div>

                    {/* [NEW] Legal Violation Box - High Alert Visibility */}
                    {rec.legal_compliance && rec.legal_compliance.length > 0 && (
                        <div className="bg-rose-50 p-5 rounded-3xl border-2 border-rose-200 flex items-start gap-4 shadow-sm shadow-rose-100/50 mt-0 animate-pulse-slow">
                            <div className="p-2 bg-rose-600 text-white rounded-2xl shadow-lg shadow-rose-200 shrink-0">
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                            </div>
                            <div>
                                <div className="text-[10px] font-black text-rose-400 uppercase tracking-[0.2em] mb-1">Legal Violation Detected</div>
                                {rec.legal_compliance.map((v, idx) => (
                                    <div key={idx} className="mb-2 last:mb-0">
                                        <p className="text-[11px] font-black text-rose-500 uppercase tracking-wider mb-0.5">
                                            {v.law} {v.section}
                                        </p>
                                        <p className="text-sm text-rose-900 font-bold leading-tight">
                                            {v.details}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* RIGHT: Credentials Data & Details CTA */}
                <div className="w-full lg:w-[320px] shrink-0 bg-slate-50 p-8 border-t lg:border-t-0 lg:border-l border-slate-200 flex flex-col gap-8 justify-center">
                    <div className="space-y-5">
                        <div className="group/item">
                            <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">ข้อมูลที่ร้านระบุ</div>
                            <div className="font-mono font-black text-slate-900 text-sm bg-white p-3 rounded-2xl border border-slate-200 shadow-inner truncate">
                                {rec.scraped_fda_number || rec.scraped_drug_number || '— ไม่ระบุข้อมูล —'}
                            </div>
                        </div>
                        <div>
                            <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 flex items-center justify-between">
                                <span>AI ตรวจพบจากภาพ</span>
                                {hasFdaตรวจจับed && <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>}
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {hasFdaตรวจจับed ? (
                                    <div className="w-full font-mono text-sm font-black text-indigo-700 bg-indigo-100/50 p-3 rounded-2xl border-2 border-indigo-200 text-center shadow-sm">
                                        {rec.fda_numbers[0]}
                                    </div>
                                ) : (
                                    <div className="w-full text-slate-400 italic text-xs p-3 bg-slate-100 rounded-2xl border border-slate-200 text-center">
                                        ไม่พบพยานหลักฐานตัวเลข
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="space-y-4 pt-6 border-t border-slate-200">
                        <div className="flex items-center justify-between px-1">
                            <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Compliance Rate</span>
                            <span className="text-xs font-black text-indigo-600">{(foundCount/4)*100}%</span>
                        </div>
                        <div className="flex gap-1 h-2 w-full bg-slate-200 rounded-full overflow-hidden p-0.5">
                            {[vc.fda_info?.found, vc.fda_label?.found, vc.thai_language?.found, vc.drug_reg?.found].map((f, i) => (
                                <div key={i} className={`flex-1 rounded-full transition-all duration-1000 ${f ? 'bg-indigo-600 shadow-[0_0_8px_rgba(79,70,229,0.4)]' : 'bg-transparent'}`}></div>
                            ))}
                        </div>
                        <button 
                            onClick={() => onOpenDetail(rec.id)} 
                            className="w-full py-4 bg-slate-900 hover:bg-indigo-600 text-white rounded-[20px] text-xs font-black uppercase tracking-[0.2em] transition-all shadow-xl shadow-slate-200 hover:scale-[1.03] active:scale-95 flex items-center justify-center gap-3 mt-4"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                            Audit Evidence
                        </button>
                    </div>
                </div>
            </div>

            {/* Disclaimer Footer */}
            <div className="px-8 py-2.5 bg-slate-50 dark:bg-slate-900/40 border-t border-slate-100 dark:border-slate-800 flex items-center gap-2">
                <svg className="w-3.5 h-3.5 text-slate-300 dark:text-slate-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                <p className="text-[10px] text-slate-400 dark:text-slate-600 leading-none">
                    ผลลัพธ์นี้วิเคราะห์โดย AI · ไม่ใช่หลักฐานทางกฎหมาย · ควรตรวจสอบซ้ำกับฐานข้อมูลทางการของ อย.
                </p>
            </div>
        </div>
    );
};

export default AnalysisCard;
