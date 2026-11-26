export default function PaginationControls({
  offset,
  limit,
  total,
  onPageChange,
  disabled = false,
}) {
  const firstItem = total === 0 ? 0 : offset + 1
  const lastItem = Math.min(offset + limit, total)

  return (
    <nav
      className="d-flex flex-wrap justify-content-end align-items-center gap-2 my-3"
      aria-label="Navegação da paginação"
    >
      <span className="small text-muted me-2">
        Exibindo {firstItem}-{lastItem} de {total}
      </span>
      <button
        type="button"
        className="btn btn-outline-primary btn-sm"
        onClick={() => onPageChange(Math.max(0, offset - limit))}
        disabled={disabled || offset === 0}
      >
        Anterior
      </button>
      <button
        type="button"
        className="btn btn-outline-primary btn-sm"
        onClick={() => onPageChange(offset + limit)}
        disabled={disabled || offset + limit >= total}
      >
        Próxima
      </button>
    </nav>
  )
}
