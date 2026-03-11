"use client"

type Props = {
  size?: number
  animateOnHover?: boolean
  highlightOnHover?: boolean
}

export default function DCBLogo({
  size = 75,
  animateOnHover = true,
  highlightOnHover = true
}: Props) {

  const classes = [
    "logo",
    animateOnHover ? "logo-animate" : "",
    highlightOnHover ? "logo-highlight" : ""
  ].join(" ")

  return (
    <>
      <style jsx>{`
        .logo {
          color: var(--accent);
          display: inline-block;
          fontFamily: "'Fraunces', serif";
        }

        /* highlight toggle */
        .logo-highlight {
          transition: color .2s ease;
        }

        .logo-highlight:hover {
          color: var(--accent-hover);
        }

        /* swing pivot points */
        .spoon { transform-origin: 7px 16px; }
        .whisk { transform-origin: 11.5px 16px; }
        .spatula { transform-origin: 16px 16px; }

        /* animation toggle */
        .logo-animate:hover .utensil {
          animation: swing 900ms ease-out;
        }

        .logo-animate:hover .spoon { animation-delay: 0ms; }
        .logo-animate:hover .whisk { animation-delay: 45ms; }
        .logo-animate:hover .spatula { animation-delay: 90ms; }

        @keyframes swing {
          0%   { transform: rotate(0deg); }
          20%  { transform: rotate(18deg); }
          40%  { transform: rotate(-10deg); }
          55%  { transform: rotate(6deg); }
          70%  { transform: rotate(-3deg); }
          85%  { transform: rotate(1.5deg); }
          100% { transform: rotate(0deg); }
        }
      `}</style>

      <svg className={classes} viewBox="0 0 28 42" width={(size*2)/3} height={size}>
        {/* monitor */}
        <path d="M13 12 Q14 12 14.9 12.5 L21.1 16.15 Q22 16.75 22 17.67 L22 24 Q22 25 21 25 L2 25 Q1 25 1 24 L1 13 Q1 12 2 12 Z"
          fill="none" stroke="currentColor" strokeWidth="0.8"/>

        <path d="M13 25 L13 27 15 27 Q16 27 16 28 16 29 15 29 L8 29 Q7 29 7 28 7 27 8 27 L10 27 10 25 Z"
          fill="currentColor"/>

        {/* hat */}
        <path d="M15.4 11.62 Q14.6 11.12 15.17 10.2 L16.6 7.62 Q17.1 6.72 18 7.2 L24 10.75 Q25 11.33 24.5 12.27 L22.85 14.9 Q22.4 15.77 21.5 15.2 Z"
          fill="none" stroke="currentColor" strokeWidth="0.8"/>

        <path d="M18.5 6.33 Q17.67 5.9 17.67 4.93 L17.67 4.48 Q17.67 2.93 19.17 2.93 20.67 2.93 20.67 4.48 22 2.06 24.33 3.48 26.67 4.83 25.25 7.23 26.5 6.48 27.25 7.83 28 8.98 26.75 9.83 L26.33 10.06 Q25.5 10.48 24.75 10 Z"
          fill="none" stroke="currentColor" strokeWidth="0.8" strokeLinejoin="round"/>

        {/* rail */}
        <path d="M5 16 L18 16"
          fill="none" stroke="currentColor" strokeWidth="0.6" strokeLinecap="round"/>

        {/* spoon */}
        <g className="utensil spoon">
          <path d="M7 16.25 L7 21"
            fill="none" stroke="currentColor" strokeWidth="0.6"/>
          <path d="M7 20.5 Q8 21 8 22.5 8 24 7 24 6 24 6 22.5 6 21 7 20.5"
            fill="currentColor"/>
        </g>

        {/* whisk */}
        <g className="utensil whisk">
          <path d="M11.5 16.25 L11.5 19.5"
            fill="none" stroke="currentColor" strokeWidth="0.8"/>
          <path d="M11.5 19 L12.5 22 Q13.17 24 11.5 24 9.83 24 10.5 22 Z"
            fill="none" stroke="currentColor" strokeWidth="0.5"/>
          <path d="M11.5 19 L12 22 Q12.1 23.75 11.5 23.75 10.9 23.75 11 22 Z"
            fill="none" stroke="currentColor" strokeWidth="0.4"/>
        </g>

        {/* spatula */}
        <g className="utensil spatula">

        {/* mask definition */}
        <defs>
            <mask id="spatulaSlots">
            {/* visible area */}
            <rect x="0" y="0" width="28" height="30" fill="white"/>

            {/* slot cutouts */}
            <line x1="15.25" y1="21.5" x2="15.25" y2="23" stroke="black" strokeWidth="0.45" strokeLinecap="round"/>
            <line x1="16"   y1="21.5" x2="16"   y2="23" stroke="black" strokeWidth="0.45" strokeLinecap="round"/>
            <line x1="16.75" y1="21.5" x2="16.75" y2="23" stroke="black" strokeWidth="0.45" strokeLinecap="round"/>
            </mask>
        </defs>

        {/* handle */}
        <path
            d="M16 16.25 L16 21"
            fill="none"
            stroke="currentColor"
            strokeWidth="0.6"
        />

        {/* spatula head */}
        <path
            d="M16 21 L17.25 21 17.25 23.5 14.75 23.5 14.75 21 Z"
            fill="currentColor"
            stroke="currentColor"
            strokeWidth="0.4"
            strokeLinejoin="round"
            mask="url(#spatulaSlots)"
        />

        </g>

        <text x="2" y="34" stroke="none" fill="currentColor" fontSize={6} fontFamily="Fraunces">Dr. Dan's</text>
        <text x="1" y="40" stroke="none" fill="currentColor" fontSize={6} fontFamily="Fraunces">Cookbook</text>

      </svg>
    </>
  )
}
