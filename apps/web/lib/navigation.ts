import {
  IconDashboard,
  IconChannels,
  IconPlus,
  IconMic,
  IconBilling,
  IconUser,
  IconChart,
} from '@/components/icons';
import type { ComponentType, SVGProps } from 'react';

type IconCmp = ComponentType<SVGProps<SVGSVGElement> & { size?: number }>;

export interface NavItem {
  href: string;
  label: string;
  icon: IconCmp;
  group?: 'main' | 'account';
}

export const NAV_ITEMS: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: IconDashboard, group: 'main' },
  { href: '/assistants', label: 'Channels', icon: IconChannels, group: 'main' },
  { href: '/projects/new', label: 'New Project', icon: IconPlus, group: 'main' },
  { href: 'https://voice.ai86.click', label: 'Voice Cloning', icon: IconMic, group: 'main' },
  { href: '/billing', label: 'Billing', icon: IconBilling, group: 'main' },
  { href: '/account/settings', label: 'Account', icon: IconUser, group: 'account' },
  { href: '/pricing', label: 'Pricing', icon: IconChart, group: 'account' },
];

export function isActiveRoute(pathname: string, href: string): boolean {
  if (href === '/dashboard' && pathname === '/dashboard') return true;
  if (href === '/dashboard') return false;
  return pathname === href || pathname.startsWith(href + '/');
}
