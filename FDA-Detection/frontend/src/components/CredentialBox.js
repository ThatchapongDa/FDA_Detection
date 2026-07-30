import React from 'react';
import { getStatusConfig } from '../utils/helpers';
import CredentialCard from './CredentialCard';

const CredentialBox = ({ result, onShowDetail }) => {
    if (!result) return null;

    const creds = result.verified_credentials || {
        fda_info: { found: false },
        fda_label: { found: false },
        thai_language: { found: false },
        drug_reg: { found: false }
    };
    
    const config = getStatusConfig(result.risk_level, result.status);

    const cards = [
        { 
            id: 'fda_info', 
            label: 'ข้อมูล อย. (FDA Info)', 
            icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>,
            found: creds.fda_info.found,
            value: creds.fda_info.text
        },
        { 
            id: 'fda_label', 
            label: 'ฉลาก อย. (FDA Label)', 
            icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" /></svg>,
            found: creds.fda_label.found,
            detailCount: creds.fda_label.count
        },
        { 
            id: 'thai_language', 
            label: 'ฉลากภาษาไทย (Thai)', 
            icon: <div className="font-bold text-sm">กข</div>,
            found: creds.thai_language.found,
            value: creds.thai_language.found ? 'พบข้อมูลสินค้าไทย' : null
        },
        { 
            id: 'drug_reg', 
            label: 'ทะเบียนยา (Drug Reg)', 
            icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a2 2 0 00-1.96 1.414l-.727 2.903a2 2 0 01-1.652 1.414l-2.387.477a2 2 0 01-1.96-1.414l-.727-2.903a2 2 0 00-1.652-1.414l-2.387-.477a2 2 0 00-1.96 1.414l-.727 2.903a2 2 0 01-1.652 1.414l-2.387.477a2 2 0 01-1.96-1.414l-.727-2.903a2 2 0 00-1.652-1.414l-2.387-.477z" /></svg>,
            found: creds.drug_reg.found,
            value: creds.drug_reg.text
        }
    ];

    return (
        <div className="w-full bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl dark:shadow-none overflow-hidden animate-fade-up">
            {/* Header: Simplified Summary */}
            <div className={`px-6 py-4 border-b dark:border-slate-800 flex items-center justify-between ${config.mainBg}`}>
                <div className="flex items-center gap-3">
                    <div className={`w-3.5 h-3.5 rounded-full ${creds.fda_info.found || creds.drug_reg.found ? 'bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.4)]' : 'bg-red-500'}`}></div>
                    <div>
                        <h3 className="text-sm font-black tracking-tight uppercase">ผลการตรวจสอบบนภาพผลิตภัณฑ์</h3>
                        <p className="text-[10px] font-bold opacity-70 tracking-widest uppercase">ระดับความสอดคล้อง: {config.label}</p>
                    </div>
                </div>
                <div className="px-3 py-1 bg-black/5 dark:bg-white/5 rounded-full text-[10px] font-bold text-slate-500 dark:text-slate-400 border border-black/5 dark:border-white/5 uppercase tracking-widest">
                    REF ID: {result.id}
                </div>
            </div>

            <div className="p-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {cards.map((card) => (
                        <CredentialCard 
                            key={card.id}
                            {...card}
                            shopValue={result.product_info?.scraped_fda}
                            onClick={() => onShowDetail(card.id)}
                        />
                    ))}
                </div>

                {/* Simplified Reasoning Section */}
                <div className="mt-6 p-4 bg-slate-50 dark:bg-slate-950/50 rounded-2xl border border-slate-100 dark:border-slate-800 flex gap-4 items-start">
                    <div className="p-2 bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 rounded-xl">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    </div>
                    <div>
                        <h5 className="text-xs font-bold text-slate-800 dark:text-white mb-0.5">สรุปการวิเคราะห์เชิงลึกจากระบบ AI</h5>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed font-medium">
                            {result.risk_summary || result.risk_reason || "กระบวนการตรวจสอบเสร็จสมบูรณ์ ข้อมูลทั้งหมดถูกดึงออกมาเพื่อเปรียบเทียบเรียบร้อยแล้ว"}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CredentialBox;
