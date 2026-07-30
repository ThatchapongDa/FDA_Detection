import React from 'react';
import { getStatusConfig } from '../utils/helpers';

const StatusBadge = ({ riskLevel, status, className = "" }) => {
    const config = getStatusConfig(riskLevel, status);

    return (
        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase ${config.colorClass} ${className}`}>
            {config.label}
        </span>
    );
};

export default StatusBadge;
