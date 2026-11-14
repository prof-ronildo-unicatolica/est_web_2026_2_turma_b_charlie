import { useEffect, useState, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { reservaService } from '../services/catalogo'

export default function MinhasReservasPage() {
  const navigate = useNavigate()
  const [reservas, setReservas] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState('')
  const [filtroStatus, setFiltroStatus] = useState('TODAS')
  const [reservaSelecionada, setReservaSelecionada] = useState(null)
  const [detalheCarregando, setDetalheCarregando] = useState(false)

  const token = localStorage.getItem('access_token')

  const carregarReservas = async (mostrarLoading = true) => {
    if (!token) {
      navigate('/login')
      return
    }
    if (mostrarLoading) setCarregando(true)
    try {
      const data = await reservaService.listarMinhasReservas()
      setReservas(data)
      setErro('')
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao carregar o painel de reservas.')
    } finally {
      if (mostrarLoading) setCarregando(false)
    }
  }

  useEffect(() => {
    carregarReservas(true)
  }, [])

  useEffect(() => {
    const temPendente = reservas.some((r) => r.status === 'Pendente')
    if (!temPendente) return

    const intervalo = setInterval(() => {
      carregarReservas(false)
    }, 3500)

    return () => clearInterval(intervalo)
  }, [reservas])

  const abrirVoucher = async (reservaId) => {
    try {
      setDetalheCarregando(true)
      const detalhe = await reservaService.obterPorId(reservaId)
      setReservaSelecionada(detalhe)
    } catch (err) {
      alert('Não foi possível carregar os detalhes do voucher.')
    } finally {
      setDetalheCarregando(false)
    }
  }

  const reservasFiltradas = reservas.filter((r) => {
    if (filtroStatus === 'TODAS') return true
    return r.status.toUpperCase() === filtroStatus
  })

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Confirmada':
        return (
          <span className="badge bg-success-subtle text-success border border-success-subtle px-3 py-2 fs-6 rounded-pill d-inline-flex align-items-center gap-1">
            <span>✅</span> Confirmada
          </span>
        )
      case 'Pendente':
        return (
          <span className="badge bg-warning-subtle text-dark border border-warning-subtle px-3 py-2 fs-6 rounded-pill d-inline-flex align-items-center gap-1">
            <span className="spinner-grow spinner-grow-sm text-warning" role="status" />
            Processando Pagamento...
          </span>
        )
      case 'Cancelada':
        return (
          <span className="badge bg-danger-subtle text-danger border border-danger-subtle px-3 py-2 fs-6 rounded-pill d-inline-flex align-items-center gap-1">
            <span>❌</span> Cancelada
          </span>
        )
      default:
        return <span className="badge bg-secondary px-3 py-2 rounded-pill">{status}</span>
    }
  }

  return (
    <div className="container py-4">
      {/* cabeçalho */}
      <div className="d-flex flex-wrap justify-content-between align-items-center mb-4 pb-3 border-bottom gap-3">
        <div>
          <h2 className="fw-bold text-dark mb-1">🛎️ Minhas Reservas</h2>
          <p className="text-muted mb-0">Acompanhe em tempo real suas estadias, vouchers e status de confirmação.</p>
        </div>
        <div className="d-flex gap-2">
          <button
            className="btn btn-outline-primary btn-sm px-3 d-flex align-items-center gap-1"
            onClick={() => carregarReservas(true)}
            disabled={carregando}
          >
            <span>🔄</span> Atualizar Lista
          </button>
          <Link to="/" className="btn btn-primary btn-sm px-3">
            + Nova Reserva
          </Link>
        </div>
      </div>

      {/* alertas */}
      {erro && (
        <div className="alert alert-danger shadow-sm d-flex justify-content-between align-items-center">
          <div>
            <strong>Atenção:</strong> {erro}
          </div>
          <button className="btn btn-sm btn-outline-danger" onClick={() => carregarReservas(true)}>
            Tentar Novamente
          </button>
        </div>
      )}

      {/* filtros status */}
      <div className="d-flex flex-wrap gap-2 mb-4">
        {[
          { label: 'Todas', value: 'TODAS' },
          { label: 'Confirmadas', value: 'CONFIRMADA' },
          { label: 'Em Processamento', value: 'PENDENTE' },
          { label: 'Canceladas', value: 'CANCELADA' },
        ].map((f) => (
          <button
            key={f.value}
            className={`btn btn-sm rounded-pill px-3 fw-semibold ${
              filtroStatus === f.value ? 'btn-primary shadow-sm' : 'btn-light border'
            }`}
            onClick={() => setFiltroStatus(f.value)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* skeleton */}
      {carregando && (
        <div className="text-center py-5">
          <div className="spinner-border text-primary mb-3" role="status" />
          <p className="text-muted">Carregando suas reservas...</p>
        </div>
      )}

      {/* empty state */}
      {!carregando && reservasFiltradas.length === 0 && (
        <div className="card border-0 shadow-sm text-center py-5 my-3 bg-white">
          <div className="card-body">
            <span style={{ fontSize: '3.5rem' }}>🧳</span>
            <h4 className="fw-bold mt-3 mb-2">Nenhuma reserva encontrada</h4>
            <p className="text-muted mb-4">
              {filtroStatus === 'TODAS'
                ? 'Você ainda não possui viagens ou reservas cadastradas.'
                : `Não existem reservas com o status "${filtroStatus}".`}
            </p>
            <Link to="/" className="btn btn-primary px-4 py-2 fw-semibold">
              Explorar Hotéis & Fazer Reserva
            </Link>
          </div>
        </div>
      )}

      {/* grid de cards de Reserva */}
      {!carregando && reservasFiltradas.length > 0 && (
        <div className="row g-4">
          {reservasFiltradas.map((r) => (
            <div className="col-lg-6" key={r.id}>
              <div className="card h-100 border-0 shadow-sm bg-white overflow-hidden transition-all">
                <div className="card-header bg-white border-bottom pt-3 pb-2 d-flex justify-content-between align-items-center">
                  <span className="text-muted small">
                    Solicitada em: {new Date(r.criado_em).toLocaleDateString('pt-BR')}
                  </span>
                  <div>{getStatusBadge(r.status)}</div>
                </div>

                <div className="card-body p-4">
                  <h4 className="fw-bold text-dark mb-1">{r.hotel_nome}</h4>
                  <p className="text-muted small mb-3">📍 {r.cidade_nome}</p>

                  <div className="p-3 bg-light rounded-3 mb-3">
                    <div className="row g-2 small">
                      <div className="col-6">
                        <span className="text-muted d-block">Quarto</span>
                        <strong className="text-dark">
                          Nº {r.quarto_numero} ({r.quarto_tipo})
                        </strong>
                      </div>
                      <div className="col-6">
                        <span className="text-muted d-block">Hóspedes</span>
                        <strong className="text-dark">
                          {r.adultos} adulto(s)
                          {r.criancas > 0 ? `, ${r.criancas} criança(s)` : ''}
                        </strong>
                      </div>
                      <div className="col-6 mt-2">
                        <span className="text-muted d-block">Check-in</span>
                        <strong className="text-dark">
                          {new Date(r.checkin + 'T00:00:00').toLocaleDateString('pt-BR')}
                        </strong>
                      </div>
                      <div className="col-6 mt-2">
                        <span className="text-muted d-block">Check-out</span>
                        <strong className="text-dark">
                          {new Date(r.checkout + 'T00:00:00').toLocaleDateString('pt-BR')}
                        </strong>
                      </div>
                    </div>
                  </div>

                  <div className="d-flex justify-content-between align-items-center mt-2">
                    <div>
                      <span className="text-muted small d-block">Valor Total</span>
                      <span className="fs-4 fw-bold text-primary">
                        R$ {Number(r.valor_total).toFixed(2)}
                      </span>
                    </div>

                    <button
                      className="btn btn-outline-primary btn-sm px-3 fw-semibold"
                      onClick={() => abrirVoucher(r.id)}
                      disabled={detalheCarregando}
                    >
                      📄 Ver Voucher
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* modal de voucher */}
      {reservaSelecionada && (
        <div
          className="modal fade show d-block"
          style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
          tabIndex="-1"
        >
          <div className="modal-dialog modal-dialog-centered modal-lg">
            <div className="modal-content border-0 shadow">
              <div className="modal-header bg-primary text-white">
                <h5 className="modal-title fw-bold">🎫 Comprovante de Reserva & Voucher</h5>
                <button
                  type="button"
                  className="btn-close btn-close-white"
                  onClick={() => setReservaSelecionada(null)}
                />
              </div>

              <div className="modal-body p-4">
                <div className="text-center pb-3 border-bottom mb-3">
                  <div className="mb-2">{getStatusBadge(reservaSelecionada.status)}</div>
                  <h3 className="fw-bold text-dark mb-0">
                    {reservaSelecionada.quarto?.hotel?.nome || 'Hotel Selecionado'}
                  </h3>
                  <p className="text-muted small">
                    Identificador da Reserva: <code>{reservaSelecionada.id}</code>
                  </p>
                </div>

                <div className="row g-3 mb-4">
                  <div className="col-sm-6">
                    <div className="p-3 bg-light rounded">
                      <span className="text-muted small d-block">Check-in</span>
                      <strong className="fs-6">
                        {new Date(reservaSelecionada.checkin + 'T00:00:00').toLocaleDateString('pt-BR')}
                      </strong>
                    </div>
                  </div>
                  <div className="col-sm-6">
                    <div className="p-3 bg-light rounded">
                      <span className="text-muted small d-block">Check-out</span>
                      <strong className="fs-6">
                        {new Date(reservaSelecionada.checkout + 'T00:00:00').toLocaleDateString('pt-BR')}
                      </strong>
                    </div>
                  </div>
                </div>

                {/* breakdown de servicos e valores */}
                {reservaSelecionada.cotacao_snapshot && (
                  <div className="border rounded p-3 mb-3 bg-light-subtle">
                    <h6 className="fw-bold mb-2">Resumo Financeiro da Cotação</h6>
                    <div className="d-flex justify-content-between small mb-1">
                      <span>Total Diárias Base:</span>
                      <strong>
                        R$ {reservaSelecionada.cotacao_snapshot.total_diarias?.toFixed(2) || '0.00'}
                      </strong>
                    </div>
                    {reservaSelecionada.cotacao_snapshot.total_servicos > 0 && (
                      <div className="d-flex justify-content-between small mb-1">
                        <span>Serviços Adicionais:</span>
                        <strong>
                          R$ {reservaSelecionada.cotacao_snapshot.total_servicos?.toFixed(2)}
                        </strong>
                      </div>
                    )}
                    <hr className="my-2" />
                    <div className="d-flex justify-content-between fs-5 fw-bold text-primary">
                      <span>Valor Total da Estadia:</span>
                      <span>R$ {Number(reservaSelecionada.valor_total).toFixed(2)}</span>
                    </div>
                  </div>
                )}
              </div>

              <div className="modal-footer bg-light">
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => setReservaSelecionada(null)}
                >
                  Fechar
                </button>
                <button
                  type="button"
                  className="btn btn-primary btn-sm px-3"
                  onClick={() => window.print()}
                >
                  🖨️ Imprimir Voucher
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}