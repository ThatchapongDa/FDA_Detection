import React, { useState, useEffect, useRef } from 'react';

const ImageWithBoxes = ({ url, detections }) => {
    const imgRef = useRef(null);
    const [dims, setDims] = useState({ w: 1, h: 1, scaleX: 1, scaleY: 1 });
    const [loaded, setLoaded] = useState(false);
    const [hasError, setHasError] = useState(false);

    const handleImageLoad = (e) => {
        const img = e.target;
        const naturalW = img.naturalWidth;
        const naturalH = img.naturalHeight;
        const displayW = img.clientWidth;
        const displayH = img.clientHeight;

        setDims({
            w: naturalW,
            h: naturalH,
            scaleX: displayW / naturalW,
            scaleY: displayH / naturalH
        });
        setLoaded(true);
    };

    useEffect(() => {
        const handleResize = () => {
            if (imgRef.current) {
                const img = imgRef.current;
                if (img.naturalWidth) {
                    setDims(prev => ({
                        ...prev,
                        scaleX: img.clientWidth / img.naturalWidth,
                        scaleY: img.clientHeight / img.naturalHeight
                    }));
                }
            }
        };
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return (
        <div className="relative flex items-center justify-center w-full h-full overflow-hidden rounded-lg">
            {!hasError ? (
                <>
                    <img
                        ref={imgRef}
                        src={url}
                        alt="Scanned"
                        referrerPolicy="no-referrer"
                        onLoad={handleImageLoad}
                        onError={() => setHasError(true)}
                        className={`max-h-[600px] max-w-full h-auto object-contain block mx-auto shadow-sm transition-opacity duration-300 ${loaded ? 'opacity-100' : 'opacity-0'}`}
                    />

                    {loaded && detections.map((d, i) => {
                        const w = d.width * dims.scaleX;
                        const h = d.height * dims.scaleY;
                        const xc = d.x * dims.scaleX;
                        const yc = d.y * dims.scaleY;

                        const left = xc - (w / 2);
                        const top = yc - (h / 2);

                        const isPackage = d.class === 'Package' || (d.class && d.class.toLowerCase().includes('package') && !d.class.includes('FDA'));
                        const isFDABox = d.class === 'FDA Box' || d.class === 'FDA / Registration Label';
                        
                        const boxColor = isPackage ? '#a855f7' : (isFDABox ? '#ef4444' : '#3b82f6');
                        const bgColor = isPackage ? 'rgba(168, 85, 247, 0.1)' : (isFDABox ? 'rgba(239, 68, 68, 0.1)' : 'rgba(59, 130, 246, 0.1)');
                        const labelBg = isPackage ? 'bg-purple-600' : (isFDABox ? 'bg-red-600' : 'bg-blue-600');

                        return (
                            <div
                                key={i}
                                style={{
                                    position: 'absolute',
                                    left: `${left}px`,
                                    top: `${top}px`,
                                    width: `${w}px`,
                                    height: `${h}px`,
                                    border: `2px solid ${boxColor}`,
                                    backgroundColor: bgColor,
                                    pointerEvents: 'none',
                                    zIndex: 10
                                }}
                            >
                                <div className={`absolute -top-6 left-0 ${labelBg} text-white text-[10px] px-1 rounded shadow whitespace-nowrap font-bold`}>
                                    {d.class} {(d.confidence).toFixed(0)}%
                                </div>
                            </div>
                        );
                    })}
                    {!hasError && (
                        <div className="absolute top-2 left-2 bg-black/70 backdrop-blur text-white text-xs px-2 py-1 rounded z-20">
                            {detections.length} ตรวจจับions
                        </div>
                    )}
                </>
            ) : (
                <div className="flex flex-col items-center justify-center text-red-400 gap-2 p-4 text-center w-full h-full bg-slate-800/50 rounded-lg">
                    <svg className="w-10 h-10 opacity-80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div className="text-xs font-bold tracking-wider">IMAGE LOAD BLOCKED</div>
                    <div className="text-[10px] text-slate-400 max-w-[150px]">(AdBlocker or Format Error)</div>
                </div>
            )}
        </div>
    );
};

export default ImageWithBoxes;
