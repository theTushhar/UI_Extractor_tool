import React, { useState, useRef, useEffect } from 'react';
import type { ExtractedElement } from '../../types';
import { Target, MousePointer2 } from 'lucide-react';

interface InteractiveScreenshotProps {
  screenshot: string;
  elements: ExtractedElement[];
  onSelectElement: (el: ExtractedElement) => void;
  selectedXpath?: string;
}

export const InteractiveScreenshot: React.FC<InteractiveScreenshotProps> = ({ 
  screenshot, 
  elements, 
  onSelectElement,
  selectedXpath 
}) => {
  const [hoveredEl, setHoveredEl] = useState<ExtractedElement | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const [scale, setScale] = useState({ x: 1, y: 1 });

  // Update scale when image loads or resizes
  const updateScale = () => {
    if (imgRef.current) {
      const { width, height, naturalWidth, naturalHeight } = imgRef.current;
      setScale({
        x: width / naturalWidth,
        y: height / naturalHeight
      });
    }
  };

  useEffect(() => {
    window.addEventListener('resize', updateScale);
    return () => window.removeEventListener('resize', updateScale);
  }, []);

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!imgRef.current) return;
    
    const rect = imgRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / scale.x;
    const y = (e.clientY - rect.top) / scale.y;

    // Find the smallest element that contains the mouse
    const matches = elements
      .filter(el => el.rect && 
        x >= el.rect.x && x <= el.rect.x + el.rect.width &&
        y >= el.rect.y && y <= el.rect.y + el.rect.height)
      .sort((a, b) => (a.rect!.width * a.rect!.height) - (b.rect!.width * b.rect!.height));

    setHoveredEl(matches[0] || null);
  };

  const handleClick = () => {
    if (hoveredEl) {
      onSelectElement(hoveredEl);
    }
  };

  const selectedEl = elements.find(el => el.absolute_xpath === selectedXpath);

  return (
    <div className="relative flex flex-col h-full bg-black rounded-xl overflow-hidden border border-bg-border shadow-2xl">
      <div className="flex items-center justify-between px-3 py-2 bg-bg-elevated/80 border-b border-bg-border z-10">
        <div className="flex items-center gap-2">
           <Target size={12} className="text-accent animate-pulse" />
           <span className="text-[10px] font-bold text-slate-200 uppercase tracking-widest">Inspect Mode Active</span>
        </div>
        <div className="text-[9px] text-slate-500 font-medium">CLICK ELEMENT TO SELECT</div>
      </div>

      <div 
        ref={containerRef}
        className="relative flex-1 overflow-auto cursor-crosshair group"
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHoveredEl(null)}
        onClick={handleClick}
      >
        <img 
          ref={imgRef}
          src={`data:image/png;base64,${screenshot}`} 
          alt="Live Site Preview" 
          onLoad={updateScale}
          className="w-full h-auto block select-none pointer-events-none"
        />

        {/* Hover Highlight */}
        {hoveredEl?.rect && (
          <div 
            className="absolute pointer-events-none border-2 border-accent bg-accent/10 shadow-[0_0_15px_rgba(168,85,247,0.4)] z-20 transition-all duration-75"
            style={{
              left: hoveredEl.rect.x * scale.x,
              top: hoveredEl.rect.y * scale.y,
              width: hoveredEl.rect.width * scale.x,
              height: hoveredEl.rect.height * scale.y
            }}
          >
            <div className="absolute -top-6 left-0 bg-accent text-white px-1.5 py-0.5 rounded text-[10px] font-bold whitespace-nowrap shadow-lg">
              {hoveredEl.element_name}
            </div>
          </div>
        )}

        {/* Selection Highlight */}
        {selectedEl?.rect && (
          <div 
            className="absolute pointer-events-none border-2 border-emerald-500 bg-emerald-500/5 shadow-[0_0_15px_rgba(16,185,129,0.3)] z-10"
            style={{
              left: selectedEl.rect.x * scale.x,
              top: selectedEl.rect.y * scale.y,
              width: selectedEl.rect.width * scale.x,
              height: selectedEl.rect.height * scale.y
            }}
          />
        )}
      </div>

      {hoveredEl && (
        <div className="absolute bottom-4 left-4 right-4 p-2 glass rounded-lg border border-white/10 shadow-2xl animate-in fade-in slide-in-from-bottom-2 z-30 pointer-events-none">
           <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-bg-elevated flex items-center justify-center">
                 <MousePointer2 size={12} className="text-accent" />
              </div>
              <div>
                 <p className="text-[10px] font-bold text-slate-200 leading-none">{hoveredEl.element_name}</p>
                 <p className="text-[9px] text-slate-500 mt-1 font-mono truncate">{hoveredEl.recommended_locator.value}</p>
              </div>
           </div>
        </div>
      )}
    </div>
  );
};
