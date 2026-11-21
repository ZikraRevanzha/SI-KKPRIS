import type { ReactNode } from 'react';
import { cn } from '@/lib/cn';

export interface TableColumn<T> {
  key: string;
  header: string;
  /** Rata kanan + tabular-nums untuk nominal Rupiah dan angka. */
  numeric?: boolean;
  className?: string;
  render: (row: T, index: number) => ReactNode;
}

export interface TableProps<T> {
  caption: string;
  columns: readonly TableColumn<T>[];
  rows: readonly T[];
  rowKey: (row: T, index: number) => string | number;
  /** Ubah tabel menjadi kartu bertumpuk saat kontainer < 40rem (default: true). */
  stackedOnMobile?: boolean;
  className?: string;
}

/**
 * Tabel data responsif semantik (AGENTS.md 7.F & modern-web-guidance/responsive-table).
 * Menggunakan container query untuk beralih ke kartu bertumpuk pada ruang sempit tanpa gulir halaman.
 */
export function Table<T>({
  caption,
  columns,
  rows,
  rowKey,
  stackedOnMobile = true,
  className,
}: TableProps<T>) {
  return (
    <div
      tabIndex={0}
      role="region"
      aria-label={caption}
      className={cn('kkpris-table-container', className)}
    >
      <table className={cn('kkpris-table', stackedOnMobile && 'kkpris-table-stacked')}>
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="bg-brand text-brand-ink">
            {columns.map((col, idx) => (
              <th
                key={col.key}
                scope="col"
                className={cn(
                  'px-4 py-3 text-xs font-semibold tracking-wide',
                  idx === 0 && 'rounded-tl-md',
                  idx === columns.length - 1 && 'rounded-tr-md',
                  col.numeric ? 'text-right' : 'text-left',
                  col.className,
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border bg-surface text-sm text-ink">
          {rows.map((row, rowIndex) => (
            <tr
              key={rowKey(row, rowIndex)}
              className="transition-colors duration-150 hover:bg-surface-subtle"
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  data-label={col.header}
                  className={cn(
                    'px-4 py-3 align-middle',
                    col.numeric && 'uang-tabular text-right font-medium',
                    col.className,
                  )}
                >
                  {col.render(row, rowIndex)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
