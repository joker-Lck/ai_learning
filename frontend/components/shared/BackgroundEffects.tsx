/**
 * 大胆的抽象线条背景 — 粗细混合 + 大幅动画 + 多样化形状
 * 优化：使用CSS contain减少重绘，React.memo减少重渲染
 */
'use client';

import { memo } from 'react';

export const FullBackground = memo(function FullBackground() {
  return (
    <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden" style={{ contain: 'strict' }}>

      {/* === 超大型粗线有机形 === */}
      <svg className="absolute -top-24 -right-16 w-[1300px] h-[750px] opacity-[0.30] svg-float-1" viewBox="0 0 911 470" fill="none" aria-hidden="true">
        <path d="M469.603 10.5C599.535 10.5 707.991 38.1049 783.484 82.7314C858.976 127.357 901.447 188.958 899.615 256.975C896.793 316.013 852.818 366.397 777.705 402.045C702.603 437.687 596.472 458.54 469.603 458.54C342.748 458.54 228.593 432.89 145.837 392.034C63.0538 351.166 11.8357 295.165 10.5 234.522C11.7343 193.799 24.049 159.46 46.0537 130.848C68.0649 102.227 99.7919 79.3108 139.884 61.4766C220.079 25.803 333.66 10.5 469.603 10.5Z" stroke="#6643FF" strokeWidth="4" />
      </svg>

      <svg className="absolute -bottom-20 -left-12 w-[1200px] h-[650px] opacity-[0.25] svg-float-2" viewBox="0 0 1205 377" fill="none" aria-hidden="true">
        <path d="M621.726 0.5C797.541 0.500031 944.318 23.6729 1046.5 61.1445C1097.59 79.8809 1137.5 102.182 1164.33 126.924C1191.14 151.658 1204.83 178.797 1203.6 207.242C1201.7 231.923 1185.93 254.845 1157.86 275.36C1129.79 295.874 1089.49 313.938 1038.66 328.902C937.007 358.83 793.383 376.333 621.726 376.333C450.077 376.333 295.6 354.802 183.6 320.5C127.597 303.348 82.2406 283.012 50.6709 260.597C19.0929 238.176 1.39991 213.743 0.5 188.411C2.1707 154.332 18.7836 125.559 48.5488 101.549C78.3354 77.5212 121.283 58.2745 175.558 43.2969C284.106 13.3421 437.812 0.49998 621.726 0.5Z" stroke="#6643FF" strokeWidth="4" />
      </svg>

      {/* === 同心圆 — 粗线 + 虚线 === */}
      <svg className="absolute top-[10%] right-[3%] w-[650px] h-[650px] opacity-[0.22] svg-float-3" viewBox="0 0 600 600" fill="none" aria-hidden="true">
        <circle cx="300" cy="300" r="280" stroke="#6643FF" strokeWidth="3" />
        <circle cx="300" cy="300" r="230" stroke="#6643FF" strokeWidth="2" className="svg-dash" />
        <circle cx="300" cy="300" r="180" stroke="#6643FF" strokeWidth="1.5" />
        <circle cx="300" cy="300" r="130" stroke="#6643FF" strokeWidth="1.2" className="svg-dash" />
        <circle cx="300" cy="300" r="80" stroke="#6643FF" strokeWidth="1" />
      </svg>

      {/* === 菱形 — 粗线 === */}
      <svg className="absolute top-[5%] left-[8%] w-[450px] h-[450px] opacity-[0.28] svg-float-2" viewBox="0 0 300 300" fill="none" aria-hidden="true">
        <path d="M150 10L290 150L150 290L10 150Z" stroke="#6643FF" strokeWidth="3.5" />
      </svg>

      <svg className="absolute bottom-[10%] right-[12%] w-[300px] h-[300px] opacity-[0.20] svg-float-1" viewBox="0 0 300 300" fill="none" aria-hidden="true">
        <path d="M150 10L290 150L150 290L10 150Z" stroke="#6643FF" strokeWidth="2.5" className="svg-dash" />
      </svg>

      {/* === 中型有机形 === */}
      <svg className="absolute top-[40%] left-[2%] w-[550px] h-[380px] opacity-[0.20] svg-float-2" viewBox="0 0 500 350" fill="none" aria-hidden="true">
        <path d="M250 20C350 20 450 60 470 130C490 200 430 260 350 290C270 320 170 320 100 280C30 240 10 180 40 120C70 60 150 20 250 20Z" stroke="#6643FF" strokeWidth="3" />
      </svg>

      <svg className="absolute top-[65%] right-[5%] w-[400px] h-[280px] opacity-[0.16] svg-float-1" viewBox="0 0 400 280" fill="none" aria-hidden="true">
        <path d="M200 15C300 15 370 50 380 110C390 170 340 220 260 250C180 280 90 270 40 230C-10 190 0 130 40 80C80 30 130 15 200 15Z" stroke="#6643FF" strokeWidth="2.5" />
      </svg>

      {/* === 三角形 === */}
      <svg className="absolute top-[25%] left-[35%] w-[200px] h-[200px] opacity-[0.15] svg-float-1" viewBox="0 0 200 200" fill="none" aria-hidden="true">
        <path d="M100 15L185 175L15 175Z" stroke="#6643FF" strokeWidth="2" />
      </svg>

      <svg className="absolute top-[70%] left-[15%] w-[150px] h-[150px] opacity-[0.12] svg-float-2" viewBox="0 0 200 200" fill="none" aria-hidden="true">
        <path d="M100 15L185 175L15 175Z" stroke="#6643FF" strokeWidth="1.5" className="svg-dash" />
      </svg>

      {/* === 六边形 === */}
      <svg className="absolute top-[55%] right-[25%] w-[180px] h-[180px] opacity-[0.14] svg-float-1" viewBox="0 0 200 200" fill="none" aria-hidden="true">
        <path d="M100 10L180 55L180 145L100 190L20 145L20 55Z" stroke="#6643FF" strokeWidth="2" />
      </svg>

      {/* === 波浪线 — 底部 === */}
      <svg className="absolute bottom-0 left-0 w-full h-[300px] opacity-[0.18]" viewBox="0 0 1440 300" fill="none" preserveAspectRatio="none" aria-hidden="true">
        <path d="M0 150C240 60 480 240 720 150C960 60 1200 240 1440 150" stroke="#6643FF" strokeWidth="3.5" />
        <path d="M0 200C240 110 480 290 720 200C960 110 1200 290 1440 200" stroke="#6643FF" strokeWidth="2.5" className="svg-dash" />
        <path d="M0 250C240 160 480 340 720 250C960 160 1200 340 1440 250" stroke="#6643FF" strokeWidth="1.5" />
      </svg>

      {/* === 波浪线 — 顶部 === */}
      <svg className="absolute top-0 left-0 w-full h-[200px] opacity-[0.14]" viewBox="0 0 1440 200" fill="none" preserveAspectRatio="none" aria-hidden="true">
        <path d="M0 80C360 180 720 -20 1080 80C1260 130 1380 50 1440 80" stroke="#6643FF" strokeWidth="3" />
        <path d="M0 40C360 140 720 -60 1080 40C1260 90 1380 10 1440 40" stroke="#6643FF" strokeWidth="1.5" className="svg-dash" />
      </svg>

      {/* === 十字准线 — 大 === */}
      <svg className="absolute top-[50%] left-[5%] w-24 h-24 opacity-[0.35]" viewBox="0 0 40 40" fill="none" aria-hidden="true">
        <line x1="20" y1="0" x2="20" y2="40" stroke="#6643FF" strokeWidth="1.5" />
        <line x1="0" y1="20" x2="40" y2="20" stroke="#6643FF" strokeWidth="1.5" />
        <circle cx="20" cy="20" r="10" stroke="#6643FF" strokeWidth="1.2" />
        <circle cx="20" cy="20" r="5" stroke="#6643FF" strokeWidth="0.8" />
      </svg>

      <svg className="absolute top-[20%] right-[8%] w-16 h-16 opacity-[0.28]" viewBox="0 0 40 40" fill="none" aria-hidden="true">
        <line x1="20" y1="0" x2="20" y2="40" stroke="#6643FF" strokeWidth="1.2" />
        <line x1="0" y1="20" x2="40" y2="20" stroke="#6643FF" strokeWidth="1.2" />
        <circle cx="20" cy="20" r="8" stroke="#6643FF" strokeWidth="1" />
      </svg>

      <svg className="absolute top-[80%] right-[35%] w-12 h-12 opacity-[0.22]" viewBox="0 0 40 40" fill="none" aria-hidden="true">
        <line x1="20" y1="5" x2="20" y2="35" stroke="#6643FF" strokeWidth="1" />
        <line x1="5" y1="20" x2="35" y2="20" stroke="#6643FF" strokeWidth="1" />
      </svg>

      {/* === 散点 — 大小混合 === */}
      <svg className="absolute top-[15%] left-[50%] w-5 h-5 opacity-[0.5]" viewBox="0 0 10 10" fill="none" aria-hidden="true">
        <circle cx="5" cy="5" r="4" fill="#6643FF" />
      </svg>
      <svg className="absolute top-[60%] left-[22%] w-4 h-4 opacity-[0.4]" viewBox="0 0 10 10" fill="none" aria-hidden="true">
        <circle cx="5" cy="5" r="4" fill="#6643FF" />
      </svg>
      <svg className="absolute top-[35%] right-[18%] w-3.5 h-3.5 opacity-[0.35]" viewBox="0 0 10 10" fill="none" aria-hidden="true">
        <circle cx="5" cy="5" r="4" fill="#6643FF" />
      </svg>
      <svg className="absolute top-[85%] left-[60%] w-3 h-3 opacity-[0.3]" viewBox="0 0 10 10" fill="none" aria-hidden="true">
        <circle cx="5" cy="5" r="4" fill="#6643FF" />
      </svg>
      <svg className="absolute top-[8%] left-[65%] w-3 h-3 opacity-[0.28]" viewBox="0 0 10 10" fill="none" aria-hidden="true">
        <circle cx="5" cy="5" r="4" fill="#6643FF" />
      </svg>
      <svg className="absolute top-[45%] left-[75%] w-2 h-2 opacity-[0.25]" viewBox="0 0 10 10" fill="none" aria-hidden="true">
        <circle cx="5" cy="5" r="4" fill="#6643FF" />
      </svg>

      {/* === 光晕 === */}
      <div className="absolute -top-40 -right-40 w-[800px] h-[800px] rounded-full opacity-[0.12] will-change-transform"
        style={{ background: 'radial-gradient(circle, #6643FF, transparent 50%)', filter: 'blur(120px)' }} />
      <div className="absolute -bottom-40 -left-40 w-[700px] h-[700px] rounded-full opacity-[0.08] will-change-transform"
        style={{ background: 'radial-gradient(circle, #6643FF, transparent 50%)', filter: 'blur(120px)' }} />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] rounded-full opacity-[0.04] will-change-transform"
        style={{ background: 'radial-gradient(circle, #6643FF, transparent 45%)', filter: 'blur(150px)' }} />
    </div>
  );
});

export const DashboardBackground = memo(function DashboardBackground() {
  return (
    <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden" style={{ contain: 'strict' }}>

      {/* === 超大型粗线有机形 === */}
      <svg className="absolute -top-24 -right-16 w-[1100px] h-[650px] opacity-[0.25] svg-float-1" viewBox="0 0 911 470" fill="none" aria-hidden="true">
        <path d="M469.603 10.5C599.535 10.5 707.991 38.1049 783.484 82.7314C858.976 127.357 901.447 188.958 899.615 256.975C896.793 316.013 852.818 366.397 777.705 402.045C702.603 437.687 596.472 458.54 469.603 458.54C342.748 458.54 228.593 432.89 145.837 392.034C63.0538 351.166 11.8357 295.165 10.5 234.522C11.7343 193.799 24.049 159.46 46.0537 130.848C68.0649 102.227 99.7919 79.3108 139.884 61.4766C220.079 25.803 333.66 10.5 469.603 10.5Z" stroke="#6643FF" strokeWidth="3.5" />
      </svg>

      <svg className="absolute -bottom-20 -left-12 w-[1000px] h-[550px] opacity-[0.20] svg-float-2" viewBox="0 0 1205 377" fill="none" aria-hidden="true">
        <path d="M621.726 0.5C797.541 0.500031 944.318 23.6729 1046.5 61.1445C1097.59 79.8809 1137.5 102.182 1164.33 126.924C1191.14 151.658 1204.83 178.797 1203.6 207.242C1201.7 231.923 1185.93 254.845 1157.86 275.36C1129.79 295.874 1089.49 313.938 1038.66 328.902C937.007 358.83 793.383 376.333 621.726 376.333C450.077 376.333 295.6 354.802 183.6 320.5C127.597 303.348 82.2406 283.012 50.6709 260.597C19.0929 238.176 1.39991 213.743 0.5 188.411C2.1707 154.332 18.7836 125.559 48.5488 101.549C78.3354 77.5212 121.283 58.2745 175.558 43.2969C284.106 13.3421 437.812 0.49998 621.726 0.5Z" stroke="#6643FF" strokeWidth="3.5" />
      </svg>

      {/* === 同心圆 === */}
      <svg className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[750px] h-[750px] opacity-[0.14] svg-float-3" viewBox="0 0 600 600" fill="none" aria-hidden="true">
        <circle cx="300" cy="300" r="280" stroke="#6643FF" strokeWidth="2.5" />
        <circle cx="300" cy="300" r="230" stroke="#6643FF" strokeWidth="1.8" className="svg-dash" />
        <circle cx="300" cy="300" r="180" stroke="#6643FF" strokeWidth="1.2" />
        <circle cx="300" cy="300" r="130" stroke="#6643FF" strokeWidth="1" className="svg-dash" />
      </svg>

      {/* === 菱形 === */}
      <svg className="absolute top-[12%] right-[6%] w-[350px] h-[350px] opacity-[0.18] svg-float-1" viewBox="0 0 300 300" fill="none" aria-hidden="true">
        <path d="M150 10L290 150L150 290L10 150Z" stroke="#6643FF" strokeWidth="2.5" />
      </svg>

      {/* === 中型有机形 === */}
      <svg className="absolute top-[45%] left-[3%] w-[450px] h-[320px] opacity-[0.16] svg-float-2" viewBox="0 0 500 350" fill="none" aria-hidden="true">
        <path d="M250 20C350 20 450 60 470 130C490 200 430 260 350 290C270 320 170 320 100 280C30 240 10 180 40 120C70 60 150 20 250 20Z" stroke="#6643FF" strokeWidth="2.5" />
      </svg>

      {/* === 三角形 === */}
      <svg className="absolute top-[30%] left-[40%] w-[160px] h-[160px] opacity-[0.12] svg-float-1" viewBox="0 0 200 200" fill="none" aria-hidden="true">
        <path d="M100 15L185 175L15 175Z" stroke="#6643FF" strokeWidth="1.5" />
      </svg>

      {/* === 六边形 === */}
      <svg className="absolute top-[65%] right-[20%] w-[150px] h-[150px] opacity-[0.10] svg-float-2" viewBox="0 0 200 200" fill="none" aria-hidden="true">
        <path d="M100 10L180 55L180 145L100 190L20 145L20 55Z" stroke="#6643FF" strokeWidth="1.5" className="svg-dash" />
      </svg>

      {/* === 波浪线 — 底部 === */}
      <svg className="absolute bottom-0 left-0 w-full h-[250px] opacity-[0.14]" viewBox="0 0 1440 250" fill="none" preserveAspectRatio="none" aria-hidden="true">
        <path d="M0 120C240 40 480 200 720 120C960 40 1200 200 1440 120" stroke="#6643FF" strokeWidth="3" />
        <path d="M0 170C240 90 480 250 720 170C960 90 1200 250 1440 170" stroke="#6643FF" strokeWidth="2" className="svg-dash" />
      </svg>

      {/* === 十字准线 === */}
      <svg className="absolute top-[55%] left-[6%] w-20 h-20 opacity-[0.30]" viewBox="0 0 40 40" fill="none" aria-hidden="true">
        <line x1="20" y1="0" x2="20" y2="40" stroke="#6643FF" strokeWidth="1.2" />
        <line x1="0" y1="20" x2="40" y2="20" stroke="#6643FF" strokeWidth="1.2" />
        <circle cx="20" cy="20" r="8" stroke="#6643FF" strokeWidth="1" />
      </svg>

      <svg className="absolute top-[22%] right-[10%] w-14 h-14 opacity-[0.22]" viewBox="0 0 40 40" fill="none" aria-hidden="true">
        <line x1="20" y1="5" x2="20" y2="35" stroke="#6643FF" strokeWidth="1" />
        <line x1="5" y1="20" x2="35" y2="20" stroke="#6643FF" strokeWidth="1" />
      </svg>

      {/* === 散点 === */}
      <svg className="absolute top-[30%] left-[55%] w-4 h-4 opacity-[0.4]" viewBox="0 0 10 10" fill="none" aria-hidden="true">
        <circle cx="5" cy="5" r="4" fill="#6643FF" />
      </svg>
      <svg className="absolute top-[70%] left-[28%] w-3 h-3 opacity-[0.3]" viewBox="0 0 10 10" fill="none" aria-hidden="true">
        <circle cx="5" cy="5" r="4" fill="#6643FF" />
      </svg>
      <svg className="absolute top-[40%] right-[15%] w-2.5 h-2.5 opacity-[0.25]" viewBox="0 0 10 10" fill="none" aria-hidden="true">
        <circle cx="5" cy="5" r="4" fill="#6643FF" />
      </svg>

      {/* === 光晕 === */}
      <div className="absolute -top-24 -right-24 w-[650px] h-[650px] rounded-full opacity-[0.10] will-change-transform"
        style={{ background: 'radial-gradient(circle, #6643FF, transparent 50%)', filter: 'blur(120px)' }} />
      <div className="absolute -bottom-24 -left-24 w-[550px] h-[550px] rounded-full opacity-[0.07] will-change-transform"
        style={{ background: 'radial-gradient(circle, #6643FF, transparent 50%)', filter: 'blur(120px)' }} />
    </div>
  );
});
