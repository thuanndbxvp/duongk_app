import {
  IconDashboard,
  IconChannels,
  IconPlus,
  IconMic,
  IconBilling,
  IconUser,
  IconChart,
  IconCode,
  IconScript,
  IconPalette,
  IconLayers,
  IconPlug,
  IconSettings,
} from '@/components/icons';
import type { ComponentType, SVGProps } from 'react';

type IconCmp = ComponentType<SVGProps<SVGSVGElement> & { size?: number }>;

export interface NavItem {
  href: string;
  label: string;
  icon: IconCmp;
  group?: 'main' | 'account' | 'admin';
}

export const NAV_ITEMS: NavItem[] = [
  // Main navigation
  { href: '/dashboard', label: 'Dashboard', icon: IconDashboard, group: 'main' },
  { href: '/projects', label: 'Projects', icon: IconCode, group: 'main' },
  { href: '/assistants', label: 'Channels', icon: IconChannels, group: 'main' },
  { href: '/projects/new', label: 'New Project', icon: IconPlus, group: 'main' },
  
  // Tools section
  { href: '/channel-collector', label: 'Collector', icon: IconPlug, group: 'main' },
  { href: '/batch-planner', label: 'Batch Planner', icon: IconLayers, group: 'main' },
  { href: '/style-bibles', label: 'Style Bibles', icon: IconPalette, group: 'main' },
  { href: '/scripts', label: 'Scripts', icon: IconScript, group: 'main' },
  
  // External
  { href: 'https://voice.ai86.click', label: 'Voice Cloning', icon: IconMic, group: 'main' },
  
  // Account
  { href: '/billing', label: 'Billing', icon: IconBilling, group: 'account' },
  { href: '/account/settings', label: 'Settings', icon: IconSettings, group: 'account' },
  { href: '/account', label: 'Account', icon: IconUser, group: 'account' },
  { href: '/pricing', label: 'Pricing', icon: IconChart, group: 'account' },
];

export function isActiveRoute(pathname: string, href: string): boolean {
  if (href === '/dashboard' && pathname === '/dashboard') return true;
  if (href === '/dashboard') return false;
  return pathname === href || pathname.startsWith(href + '/');
}
