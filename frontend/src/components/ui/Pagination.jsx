export default function Pagination({ page, totalPages, onChange }) {
  if (totalPages <= 1) return null

  // Build page window: always show first, last, current ±2
  const pages = []
  for (let i = 1; i <= totalPages; i++) {
    if (
      i === 1 ||
      i === totalPages ||
      (i >= page - 2 && i <= page + 2)
    ) {
      pages.push(i)
    }
  }

  // Insert ellipsis markers
  const withEllipsis = []
  for (let i = 0; i < pages.length; i++) {
    if (i > 0 && pages[i] - pages[i - 1] > 1) withEllipsis.push('…')
    withEllipsis.push(pages[i])
  }

  const btn = 'min-w-[36px] h-9 px-2 flex items-center justify-center rounded-lg text-sm transition-colors'

  return (
    <nav className="flex items-center justify-center gap-1 py-6" aria-label="Pagination">
      {/* Prev */}
      <button
        onClick={() => onChange(page - 1)}
        disabled={page === 1}
        className={`${btn} ${page === 1
          ? 'text-[#55556a] cursor-not-allowed'
          : 'text-[#9999aa] hover:bg-[#1a1a24] hover:text-white'}`}
        aria-label="Previous page"
      >
        <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
          <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1
            1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
      </button>

      {/* Page numbers */}
      {withEllipsis.map((p, i) =>
        p === '…' ? (
          <span key={`ellipsis-${i}`} className="min-w-[36px] h-9 flex items-center justify-center text-[#55556a] text-sm">
            …
          </span>
        ) : (
          <button
            key={p}
            onClick={() => onChange(p)}
            className={`${btn} font-medium ${p === page
              ? 'bg-red-600 text-white'
              : 'text-[#9999aa] hover:bg-[#1a1a24] hover:text-white'}`}
            aria-current={p === page ? 'page' : undefined}
          >
            {p}
          </button>
        )
      )}

      {/* Next */}
      <button
        onClick={() => onChange(page + 1)}
        disabled={page === totalPages}
        className={`${btn} ${page === totalPages
          ? 'text-[#55556a] cursor-not-allowed'
          : 'text-[#9999aa] hover:bg-[#1a1a24] hover:text-white'}`}
        aria-label="Next page"
      >
        <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
          <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1
            1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
        </svg>
      </button>
    </nav>
  )
}
