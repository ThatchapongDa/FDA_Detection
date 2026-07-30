import React from 'react';

const CredentialCard = ({ id, label, icon, found, value, detailCount, shopValue, onClick }) => {
    return (
        <div
            onClick={found ? onClick : null}
            className={`relative group flex flex-col p-4 rounded-2xl border transition-all duration-300 ${found
                    ? 'bg-white dark:bg-slate-900 border-green-200 dark:border-green-500/30 shadow-sm hover:shadow-md hover:scale-[1.02] cursor-pointer'
                    : 'bg-slate-50 dark:bg-slate-950/50 border-slate-100 dark:border-slate-800 opacity-70'
                }`}
        >
            {/* Header Section */}
            <div className="flex items-center justify-between mb-3">
                <div className={`p-2 rounded-xl border ${found
                        ? 'bg-green-50 dark:bg-green-500/10 border-green-100 dark:border-green-500/20 text-green-600 dark:text-green-400'
                        : 'bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-400 dark:text-slate-500'
                    }`}>
                    {React.isValidElement(icon) ? React.cloneElement(icon, { className: 'w-5 h-5' }) : icon}
                </div>
                {found ? (
                    <div className="flex items-center gap-1.5 text-[9px] font-bold text-green-600 dark:text-green-400 uppercase tracking-wide bg-green-50 dark:bg-green-500/10 px-2.5 py-1 rounded-lg border border-green-100 dark:border-green-500/20">
                        <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                        Verified
                    </div>
                ) : (
                    <div className="text-[9px] font-semibold text-slate-400 dark:text-slate-600 uppercase tracking-wide bg-slate-100 dark:bg-slate-900 px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-800">
                        Missing
                    </div>
                )}
            </div>

            {/* Content Section */}
            <div className="flex-1 flex flex-col min-h-[100px]">
                {/* Label Row */}
                <div className="flex items-center justify-between gap-2 mb-2">
                    <h4 className="text-[11px] font-bold text-slate-500 dark:text-slate-500 uppercase tracking-tight truncate">
                        {label}
                    </h4>
                    {found && (
                        <span className="text-[8px] font-bold text-indigo-600 dark:text-indigo-400 uppercase bg-indigo-50 dark:bg-indigo-500/10 px-1.5 py-0.5 rounded border border-indigo-100 dark:border-indigo-500/20 whitespace-nowrap flex-shrink-0">
                            Scan Found
                        </span>
                    )}
                </div>

                {found ? (
                    <div className="flex-1 flex flex-col justify-between">
                        {/* Value Display */}
                        <div className="mb-2">
                            <div className="text-sm font-mono font-bold text-slate-800 dark:text-white break-words line-clamp-2 group-hover:text-blue-700 dark:group-hover:text-blue-400 transition-colors">
                                {value || (detailCount ? `${detailCount} Markers` : 'ตรวจจับed')}
                            </div>
                        </div>

                        {/* Alert Section */}
                        <div className="space-y-2">
                            {shopValue && value && shopValue.toString().replace(/[-\s]/g, '') !== value.toString().replace(/[-\s]/g, '') && (
                                <div className="flex items-center gap-1.5 text-[8px] font-bold text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-500/10 px-2 py-1 rounded border border-red-200 dark:border-red-500/30">
                                    <svg className="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                    </svg>
                                    <span className="uppercase tracking-wide">Mismatch</span>
                                </div>
                            )}

                            {/* View Evidence Button */}
                            <div className="flex items-center gap-1.5 text-[10px] text-blue-600 dark:text-blue-400 font-bold group-hover:translate-x-0.5 transition-transform uppercase tracking-wide">
                                <span>View Evidence</span>
                                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                                </svg>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="flex-1 flex items-center">
                        <div className="text-[11px] text-slate-400 dark:text-slate-600 font-medium leading-relaxed">
                            No markers found. Try another angle?
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default CredentialCard;