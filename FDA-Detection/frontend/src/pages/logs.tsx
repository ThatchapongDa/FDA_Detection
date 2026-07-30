import React, { useState, useEffect, useRef } from 'react';
import Head from 'next/head';

const LogsPage = () => {
    const [logs, setLogs] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [autoRefresh, setAutoRefresh] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const logsEndRef = useRef<HTMLDivElement>(null);

    const fetchLogs = async () => {
        try {
            setLoading(true);
            setError(null);
            const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
            const res = await fetch(`${apiBase}/logs?limit=500`);
            if (res.ok) {
                const data = await res.json();
                setLogs(data.logs || []);
            } else {
                const text = await res.text();
                setError(`Failed to fetch logs: ${res.status} ${text}`);
            }
        } catch (err: any) {
            setError(`Network error: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    // Initial fetch + Auto-refresh
    useEffect(() => {
        fetchLogs();
        const interval = setInterval(() => {
            if (autoRefresh) fetchLogs();
        }, 5000); // Refresh every 5 seonds

        return () => clearInterval(interval);
    }, [autoRefresh]);

    // Auto-scroll to bottom only if user was already at bottom or on first load
    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [logs]);

    return (
        <div className="min-h-screen bg-gray-900 text-gray-100 p-6 font-mono">
            <Head>
                <title>System Logs | FDA Detection</title>
            </Head>

            <header className="flex justify-between items-center mb-6 border-b border-gray-700 pb-4">
                <h1 className="text-2xl font-bold text-green-400">System Logs</h1>
                <div className="flex gap-4 items-center">
                    <label className="flex items-center gap-2 cursor-pointer select-none">
                        <input
                            type="checkbox"
                            checked={autoRefresh}
                            onChange={(e) => setAutoRefresh(e.target.checked)}
                            className="w-4 h-4 accent-green-500"
                        />
                        <span className="text-sm text-gray-400">Auto-refresh (5s)</span>
                    </label>
                    <button
                        onClick={() => fetchLogs()}
                        disabled={loading}
                        className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm transition-colors disabled:opacity-50"
                    >
                        {loading ? 'Refreshing...' : 'Refresh Now'}
                    </button>
                    <a href="/" className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded text-sm text-white no-underline">
                        Back to Dashboard
                    </a>
                </div>
            </header>

            <main className="bg-black rounded-lg border border-gray-800 shadow-2xl overflow-hidden h-[80vh] flex flex-col">
                <div className="flex-1 overflow-y-auto p-4 space-y-1 custom-scrollbar">
                    {error && (
                        <div className="bg-red-900/30 border border-red-500/50 p-4 rounded-lg mb-4 text-red-200 text-sm">
                            <strong>Error:</strong> {error}
                        </div>
                    )}
                    {logs.length === 0 ? (
                        <div className="text-gray-500 italic text-center mt-10">
                            {loading ? 'Fetching logs...' : 'No logs available.'}
                        </div>
                    ) : (
                        logs.map((line, index) => {
                            // Simple coloring based on log level
                            let colorClass = "text-gray-300";
                            if (line.includes("ERROR")) colorClass = "text-red-500 font-bold";
                            else if (line.includes("WARNING")) colorClass = "text-yellow-400";
                            else if (line.includes("INFO")) colorClass = "text-blue-300";
                            else if (line.includes("DEBUG")) colorClass = "text-gray-500";

                            return (
                                <div key={index} className={`whitespace-pre-wrap ${colorClass} text-sm hover:bg-gray-900 px-1 rounded`}>
                                    <span className="select-none text-gray-600 mr-2 text-xs opacity-50">{index + 1}</span>
                                    {line}
                                </div>
                            );
                        })
                    )}
                    <div ref={logsEndRef} />
                </div>
            </main>

            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 10px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: #1a1a1a;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: #4a5568;
                    border-radius: 5px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: #718096;
                }
            `}</style>
        </div>
    );
};

export default LogsPage;
