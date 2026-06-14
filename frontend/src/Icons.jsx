/* Storefront — shared icons (Lucide-style outline) */

export const StoreIcon = ({ name, size = 22, stroke = 1.7 }) => {
  const props = { width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: stroke, strokeLinecap: "round", strokeLinejoin: "round" };
  switch (name) {
    case 'truck':
      return (<svg {...props}><path d="M3 7h11v9H3z"/><path d="M14 10h4l3 3v3h-7"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/></svg>);
    case 'shield-check':
      return (<svg {...props}><path d="M12 3l7 3v6c0 4-3 7-7 8-4-1-7-4-7-8V6l7-3z"/><path d="M9 12l2 2 4-4"/></svg>);
    case 'plant':
      return (<svg {...props}><path d="M12 21c0-5-3-8-8-8 0 5 3 8 8 8z"/><path d="M12 21c0-5 3-8 8-8 0 5-3 8-8 8z"/><path d="M12 21V9"/></svg>);
    case 'calendar':
      return (<svg {...props}><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 9h18M8 3v4M16 3v4"/></svg>);
    case 'box':
      return (<svg {...props}><path d="M21 8l-9-5-9 5 9 5 9-5z"/><path d="M3 8v8l9 5 9-5V8"/></svg>);
    case 'file-check':
      return (<svg {...props}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><polyline points="9 15 11 17 15 13"/></svg>);
    case 'pin':
      return (<svg {...props}><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 1 1 16 0z"/><circle cx="12" cy="10" r="3"/></svg>);
    case 'phone':
      return (<svg {...props}><path d="M22 16.92V20a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.79 19.79 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3.08a2 2 0 0 1 2 1.72c.13.96.37 1.9.72 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.35 1.85.59 2.81.72A2 2 0 0 1 22 16.92z"/></svg>);
    case 'clock':
      return (<svg {...props}><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>);
    case 'cart':
      return (<svg {...props}><circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M3 4h2l2.7 12.4a2 2 0 0 0 2 1.6h7.5a2 2 0 0 0 2-1.5L21 8H6"/></svg>);
    case 'line':
      return (<svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-label="LINE"><path d="M12 2C6.5 2 2 5.66 2 10.16c0 4.03 3.55 7.41 8.35 8.05.32.07.77.21.88.49.1.25.07.65.03.9l-.14.85c-.04.25-.2.99.86.54 1.06-.45 5.74-3.39 7.83-5.79C21.27 13.59 22 11.97 22 10.16 22 5.66 17.5 2 12 2zm-3.97 10.66H6.04c-.21 0-.39-.17-.39-.39V8.36c0-.21.17-.39.39-.39.21 0 .39.17.39.39v3.52h1.6c.21 0 .39.17.39.39 0 .21-.18.39-.39.39zm1.51-.39c0 .21-.17.39-.39.39-.21 0-.39-.17-.39-.39V8.36c0-.21.17-.39.39-.39.21 0 .39.17.39.39v3.91zm4.69 0c0 .17-.11.31-.27.36-.04.01-.08.02-.12.02-.12 0-.24-.05-.31-.16l-2.02-2.74v2.52c0 .21-.17.39-.39.39s-.39-.17-.39-.39V8.36c0-.17.11-.31.27-.36.04-.01.08-.02.12-.02.12 0 .23.07.31.16l2.03 2.75V8.36c0-.21.17-.39.39-.39s.39.17.39.39v3.91zm3.15-2.34c.21 0 .39.17.39.39 0 .21-.17.39-.39.39h-1.6v1.18h1.6c.21 0 .39.17.39.39 0 .21-.17.39-.39.39h-1.99c-.21 0-.39-.17-.39-.39V8.36c0-.21.17-.39.39-.39h1.99c.21 0 .39.17.39.39 0 .21-.17.39-.39.39h-1.6v1.18h1.6z"/></svg>);
    case 'facebook':
      return (<svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor"><path d="M22 12c0-5.5-4.5-10-10-10S2 6.5 2 12c0 5 3.7 9.1 8.4 9.9V15h-2.5v-3h2.5v-2c0-2.5 1.5-3.9 3.8-3.9 1.1 0 2.2.2 2.2.2V9h-1.2c-1.2 0-1.6.8-1.6 1.6V12h2.7l-.4 3h-2.3v7c4.7-.8 8.4-4.9 8.4-9.9z"/></svg>);
    case 'instagram':
      return (<svg {...props}><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor"/></svg>);
    default: return null;
  }
};

window.StoreIcon = StoreIcon;
