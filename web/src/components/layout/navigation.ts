import type { LucideIcon } from 'lucide-react';
import {
  Bell,
  CalendarClock,
  CheckSquare,
  FileBarChart2,
  FilePlus2,
  HandCoins,
  Home,
  LayoutDashboard,
  ReceiptText,
  UserMinus,
  Users,
  Wallet,
} from 'lucide-react';
import type { Peran } from '@/app/authContext';

export interface NavigationItem {
  id: string;
  label: string;
  to: string;
  icon: LucideIcon;
  allowedRoles: readonly Peran[];
}

const MENU_BENDAHARA: readonly NavigationItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    to: '/dashboard',
    icon: LayoutDashboard,
    allowedRoles: ['BENDAHARA', 'KETUA'],
  },
  {
    id: 'data-anggota',
    label: 'Data Anggota',
    to: '/anggota',
    icon: Users,
    allowedRoles: ['BENDAHARA', 'KETUA'],
  },
  {
    id: 'simpanan',
    label: 'Simpanan',
    to: '/simpanan',
    icon: Wallet,
    allowedRoles: ['BENDAHARA', 'KETUA'],
  },
  {
    id: 'pembiayaan',
    label: 'Pembiayaan',
    to: '/pembiayaan',
    icon: HandCoins,
    allowedRoles: ['BENDAHARA', 'KETUA'],
  },
  {
    id: 'angsuran',
    label: 'Angsuran',
    to: '/angsuran',
    icon: ReceiptText,
    allowedRoles: ['BENDAHARA'],
  },
  {
    id: 'rekap-gaji',
    label: 'Rekap Potong Gaji',
    to: '/rekap-gaji',
    icon: CalendarClock,
    allowedRoles: ['BENDAHARA', 'KETUA'],
  },
  {
    id: 'notifikasi',
    label: 'Notifikasi Tagihan',
    to: '/notifikasi',
    icon: Bell,
    allowedRoles: ['BENDAHARA'],
  },
  {
    id: 'laporan',
    label: 'Laporan Keuangan',
    to: '/laporan',
    icon: FileBarChart2,
    allowedRoles: ['BENDAHARA', 'KETUA'],
  },
];

const MENU_KETUA: readonly NavigationItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    to: '/dashboard',
    icon: LayoutDashboard,
    allowedRoles: ['BENDAHARA', 'KETUA'],
  },
  {
    id: 'persetujuan-kas',
    label: 'Persetujuan Kas',
    to: '/persetujuan-kas',
    icon: CheckSquare,
    allowedRoles: ['KETUA'],
  },
  {
    id: 'data-anggota',
    label: 'Data Anggota',
    to: '/anggota',
    icon: Users,
    allowedRoles: ['BENDAHARA', 'KETUA'],
  },
  {
    id: 'simpanan',
    label: 'Simpanan',
    to: '/simpanan',
    icon: Wallet,
    allowedRoles: ['BENDAHARA', 'KETUA'],
  },
  {
    id: 'pembiayaan',
    label: 'Pembiayaan',
    to: '/pembiayaan',
    icon: HandCoins,
    allowedRoles: ['BENDAHARA', 'KETUA'],
  },
  {
    id: 'rekap-gaji',
    label: 'Rekap Potong Gaji',
    to: '/rekap-gaji',
    icon: CalendarClock,
    allowedRoles: ['BENDAHARA', 'KETUA'],
  },
  {
    id: 'laporan',
    label: 'Laporan Keuangan',
    to: '/laporan',
    icon: FileBarChart2,
    allowedRoles: ['BENDAHARA', 'KETUA'],
  },
];

const MENU_ANGGOTA: readonly NavigationItem[] = [
  {
    id: 'beranda',
    label: 'Beranda',
    to: '/beranda',
    icon: Home,
    allowedRoles: ['ANGGOTA'],
  },
  {
    id: 'simpanan-saya',
    label: 'Simpanan Saya',
    to: '/simpanan-saya',
    icon: Wallet,
    allowedRoles: ['ANGGOTA'],
  },
  {
    id: 'pembiayaan-saya',
    label: 'Pembiayaan Saya',
    to: '/pembiayaan-saya',
    icon: HandCoins,
    allowedRoles: ['ANGGOTA'],
  },
  {
    id: 'ajukan-pembiayaan',
    label: 'Ajukan Pembiayaan',
    to: '/pembiayaan/ajukan',
    icon: FilePlus2,
    allowedRoles: ['ANGGOTA'],
  },
  {
    id: 'pengunduran-diri',
    label: 'Ajukan Pengunduran Diri',
    to: '/pengunduran-diri',
    icon: UserMinus,
    allowedRoles: ['ANGGOTA'],
  },
];

export function getNavigationByRole(peran: Peran): readonly NavigationItem[] {
  switch (peran) {
    case 'BENDAHARA':
      return MENU_BENDAHARA;
    case 'KETUA':
      return MENU_KETUA;
    case 'ANGGOTA':
      return MENU_ANGGOTA;
  }
}

export function getHomePathByRole(peran: Peran): string {
  return peran === 'ANGGOTA' ? '/beranda' : '/dashboard';
}
