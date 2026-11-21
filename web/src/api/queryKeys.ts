export const queryKeys = {
  auth: {
    all: ['auth'] as const,
    me: () => ['auth', 'me'] as const,
  },
  dashboard: {
    all: ['dashboard'] as const,
    ringkasan: () => ['dashboard', 'ringkasan'] as const,
    berandaAnggota: () => ['dashboard', 'beranda-anggota'] as const,
  },
} as const;
