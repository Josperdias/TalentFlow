const PATHS = {
  home: 'M3 11l9-7 9 7M5 10v10h14V10', jobs: 'M4 7h16v12H4zM9 7V4h6v3', people: 'M16 11a4 4 0 10-8 0 4 4 0 008 0zM4 21c0-4 4-6 8-6s8 2 8 6',
  team: 'M9 11a3 3 0 100-6 3 3 0 000 6zM3 20c0-3 3-5 6-5s6 2 6 5M17 11a3 3 0 100-6M21 20c0-2-1.5-3.6-4-4.3',
  plan: 'M4 19V5M4 19h16M8 15l4-5 3 3 5-6', leave: 'M5 5h14v15H5zM5 10h14M9 3v4M15 3v4', account: 'M12 12a4 4 0 100-8 4 4 0 000 8zM5 21a7 7 0 0114 0',
  clock: 'M12 7v5l3 2M21 12a9 9 0 11-18 0 9 9 0 0118 0z', check: 'M5 12.5l4.5 4.5L19 7.5', trend: 'M3 17l6-6 4 4 8-8M15 7h6v6',
  alert: 'M12 8v5M12 17h.01M10.3 3.9L2.5 17.5A2 2 0 004.2 20.5h15.6a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z',
  sun: 'M12 3v2M12 19v2M5.6 5.6L7 7M17 17l1.4 1.4M3 12h2M19 12h2M5.6 18.4L7 17M17 7l1.4-1.4M12 8a4 4 0 100 8 4 4 0 000-8z', moon: 'M20 14.5A8 8 0 019.5 4a8 8 0 1010.5 10.5z', auto: 'M12 3a9 9 0 100 18V3z',
  arrow: 'M5 12h14M13 6l6 6-6 6', shield: 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z', sync: 'M20 11a8 8 0 00-14-4M4 4v4h4M4 13a8 8 0 0014 4M20 20v-4h-4'
} as const;
export type IconName = keyof typeof PATHS;

export function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={PATHS[name]} /></svg>;
}
