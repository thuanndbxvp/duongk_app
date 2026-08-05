export interface NavItem {
  href: string;
  label: string;
  icon: string;
  group?: 'main' | 'account';
}

export const NAV_ITEMS: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: '📊', group: 'main' },
  { href: '/assistants', label: 'Channels', icon: '📺', group: 'main' },
  { href: '/projects/new', label: 'New Project', icon: '➕', group: 'main' },
  { href: '/voice-cloning', label: 'Voice Cloning', icon: '🎙️', group: 'main' },
  { href: '/billing', label: 'Billing', icon: '💰', group: 'main' },
  { href: '/account/settings', label: 'Account', icon: '👤', group: 'account' },
  { href: '/pricing', label: 'Pricing', icon: '📈', group: 'account' },
];

export function isActiveRoute(pathname: string, href: string): boolean {
  if (href === '/dashboard' && pathname === '/dashboard') return true;
  if (href === '/dashboard') return false; // Don't highlight on other routes
  return pathname === href || pathname.startsWith(href + '/');
}
