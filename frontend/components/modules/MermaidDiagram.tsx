'use client';

import { useEffect, useRef, useState } from 'react';

interface MermaidDiagramProps {
  chart: string;
}

let mermaidInstance: any = null;
let mermaidId = 0;

async function getMermaid() {
  if (!mermaidInstance) {
    const mermaid = (await import('mermaid')).default;
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      themeVariables: {
        primaryColor: '#1e3a5f',
        primaryTextColor: '#e2e8f0',
        primaryBorderColor: '#64ffda',
        lineColor: '#64ffda',
        secondaryColor: '#0d1b2a',
        tertiaryColor: '#162033',
        fontFamily: 'system-ui, sans-serif',
      },
      flowchart: { curve: 'basis', padding: 15 },
    });
    mermaidInstance = mermaid;
  }
  return mermaidInstance;
}

export default function MermaidDiagram({ chart }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [svg, setSvg] = useState<string>('');

  useEffect(() => {
    if (!chart?.trim()) return;

    let cancelled = false;
    const renderChart = async () => {
      try {
        const mermaid = await getMermaid();
        const id = `mermaid-${++mermaidId}`;
        const { svg: renderedSvg } = await mermaid.render(id, chart);
        if (!cancelled) {
          setSvg(renderedSvg);
          setError(null);
        }
      } catch (e: any) {
        if (!cancelled) {
          setError(e?.message || '图表渲染失败');
          setSvg('');
        }
      }
    };

    renderChart();
    return () => { cancelled = true; };
  }, [chart]);

  if (error) {
    return (
      <div className="mt-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400">
        <div className="font-medium mb-1">⚠️ 图表渲染失败</div>
        <pre className="text-xs text-red-300/70 whitespace-pre-wrap">{chart}</pre>
      </div>
    );
  }

  if (!svg) {
    return (
      <div className="mt-2 p-3 text-white/40 text-sm">图表加载中...</div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="mt-2 p-3 bg-white/[0.03] rounded-lg border border-white/[0.06] overflow-x-auto
                 [&>svg]:max-w-full [&>svg]:h-auto"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
