import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import PaginationControls from '../components/PaginationControls'
import { reservaService } from '../services/catalogo'

const PAGE_SIZE = 20

export default function MinhasReservasPage() {
  const navigate = useNavigate()
  const [reservas, setReservas] = useState([])
  const [offset, setOffset] = useState(0)
  const [total, setTotal] = useState(0)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState('')
  const [sucessoMsg, setSucessoMsg] = useState('')
  const [filtroStatus, setFiltroStatus] = useState('TODAS')
  const [reservaSelecionada, setReservaSelecionada] = useState(null)
  const [detalheCarregando, setDetalheCarregando] = useState(false)
  const [reservaParaCancelar, setReservaParaCancelar] = useState(null)
  const [previewCancelamento, setPreviewCancelamento] = useState(null)
  const [motivoCancelamento, setMotivoCancelamento] = useState('')
  const [cancelando, setCancelando] = useState(false)
  const [carregandoPreview, setCarregandoPreview] = useState(false)

  const token = localStorage.getItem('access_token')

  const carregarReservas = useCallback(async (mostrarLoading = true) => {
    if (!token) {
      navigate('/login')
      return
    }
    if (mostrarLoading) setCarregando(true)
    try {
      const status = filtroStatus === 'TODAS'
        ? undefined
        : {
            CONFIRMADA: 'Confirmada',
            PENDENTE: 'Pendente',
            CANCELADA: 'Cancelada',
          }[filtroStatus]
      const data = await reservaService.listarMinhasReservas({
        limit: PAGE_SIZE,
        offset,
        status,
      })
      setReservas(data.items)
      setTotal(data.total)
      setErro('')
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao carregar o painel de reservas.')
    } finally {
      if (mostrarLoading) setCarregando(false)
    }
  }, [filtroStatus, navigate, offset, token])

  useEffect(() => {
    carregarReservas(true)
  }, [carregarReservas])

  useEffect(() => {
    const temPendente = reservas.some((r) => r.status === 'Pendente')
    if (!temPendente) return

    const intervalo = setInterval(() => {
      carregarReservas(false)
    }, 3500)

    return () => clearInterval(intervalo)
  }, [carregarReservas, reservas])

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

  const iniciarCancelamento = async (reserva) => {
    setReservaParaCancelar(reserva)
    setMotivoCancelamento('')
    setCarregandoPreview(true)
    try {
      const preview = await reservaService.obterPreviewCancelamento(reserva.id)
      setPreviewCancelamento(preview)
    } catch (err) {
      alert(err.response?.data?.detail || 'Não foi possível simular a política de cancelamento.')
      setReservaParaCancelar(null)
    } finally {
      setCarregandoPreview(false)
    }
  }

  const confirmarCancelamento = async () => {
    if (!reservaParaCancelar) return
    setCancelando(true)
    try {
      const resp = await reservaService.cancelar(reservaParaCancelar.id, {
        motivo: motivoCancelamento || 'Solicitado pelo hóspede via painel',
      })
      setSucessoMsg(
        `Reserva cancelada com sucesso! Multa aplicada: R$ ${resp.valor_multa.toFixed(
          2
        )} | Reembolso: R$ ${resp.valor_reembolso.toFixed(2)}.`
      )
      setReservaParaCancelar(null)
      setPreviewCancelamento(null)
      carregarReservas(false)
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao cancelar a reserva.')
    } finally {
      setCancelando(false)
    }
  }

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
          <p className="text-muted mb-0">
            Acompanhe suas viagens, vouchers e gerencie solicitações de cancelamento com política transparente.
          </p>
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
      {sucessoMsg && (
        <div className="alert alert-success alert-dismissible fade show shadow-sm p-3 mb-4">
          <h5 className="alert-heading fw-bold mb-1">🎉 Sucesso!</h5>
          <p className="mb-0">{sucessoMsg}</p>
          <button
            type="button"
            className="btn-close"
            onClick={() => setSucessoMsg('')}
          />
        </div>
      )}

      {erro && (
        <div className="alert alert-danger shadow-sm d-flex justify-content-between align-items-center mb-4">
          <div><strong>Atenção:</strong> {erro}</div>
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
            onClick={() => {
              setFiltroStatus(f.value)
              setOffset(0)
            }}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* skeleton */}
      {carregando && (
        <div className="text-center py-5">
          <div className="spinner-border text-primary mb-3" role="status" />
          <p className="text-muted">Carregando histórico de reservas...</p>
        </div>
      )}

      {/* empty state */}
      {!carregando && reservas.length === 0 && (
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
      {!carregando && reservas.length > 0 && (
        <div className="row g-4">
          {reservas.map((r) => {
            const ehReembolsavel = r.tipo_tarifa === 'reembolsavel'
            const dataLimiteFormatada = r.data_limite_cancelamento
              ? new Date(r.data_limite_cancelamento).toLocaleString('pt-BR', {
                  day: '2-digit',
                  month: '2-digit',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })
              : ''

            return (
              <div className="col-lg-6" key={r.id}>
                <div className="card h-100 border-0 shadow-sm bg-white overflow-hidden">
                  <div className="card-header bg-white border-bottom pt-3 pb-2 d-flex justify-content-between align-items-center">
                    <div>
                      <span className="badge bg-secondary-subtle text-secondary me-2">
                        {ehReembolsavel ? '🛡️ Reembolsável' : '🔒 Não Reembolsável'}
                      </span>
                      <span className="text-muted small">
                        {new Date(r.criado_em).toLocaleDateString('pt-BR')}
                      </span>
                    </div>
                    <div>{getStatusBadge(r.status)}</div>
                  </div>

                  <div className="card-body p-4">
                    <h4 className="fw-bold text-dark mb-1">{r.hotel_nome}</h4>
                    <p className="text-muted small mb-3">📍 {r.cidade_nome}</p>

                    <div className="p-3 bg-light rounded-3 mb-3">
                      <div className="row g-2 small">
                        <div className="col-6">
                          <span className="text-muted d-block">Quarto</span>
                          <strong className="text-dark">Nº {r.quarto_numero} ({r.quarto_tipo})</strong>
                        </div>
                        <div className="col-6">
                          <span className="text-muted d-block">Hóspedes</span>
                          <strong className="text-dark">
                            {r.adultos} adulto(s){r.criancas > 0 ? `, ${r.criancas} criança(s)` : ''}
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

                    {/* aviso da política de cancelamento */}
                    {r.status === 'Confirmada' && (
                      <div
                        className={`alert ${
                          ehReembolsavel ? 'alert-info' : 'alert-secondary'
                        } py-2 px-3 small mb-3`}
                      >
                        {ehReembolsavel ? (
                          <>
                            <strong>🕒 Prazo de Cancelamento sem Multa:</strong> até{' '}
                            <span className="text-primary fw-bold">{dataLimiteFormatada}</span> (48h antes do check-in).
                          </>
                        ) : (
                          <>
                            <strong>⚠️ Política Restritiva:</strong> Tarifa Não Reembolsável contratada. O cancelamento acarreta retenção de 100% do valor.
                          </>
                        )}
                      </div>
                    )}

                    {/* exibição dos valores retidos se cancelada */}
                    {r.status === 'Cancelada' && (
                      <div className="alert alert-danger py-2 px-3 small mb-3">
                        <div className="d-flex justify-content-between">
                          <span>Multa Aplicada:</span>
                          <strong>R$ {Number(r.valor_multa || 0).toFixed(2)}</strong>
                        </div>
                        <div className="d-flex justify-content-between">
                          <span>Reembolso Efetuado:</span>
                          <strong>R$ {Number(r.valor_reembolso || 0).toFixed(2)}</strong>
                        </div>
                      </div>
                    )}

                    <div className="d-flex justify-content-between align-items-center mt-3 pt-2 border-top">
                      <div>
                        <span className="text-muted small d-block">Valor Total</span>
                        <span className="fs-4 fw-bold text-primary">
                          R$ {Number(r.valor_total).toFixed(2)}
                        </span>
                      </div>

                      <div className="d-flex gap-2">
                        {r.pode_cancelar && (
                          <button
                            className="btn btn-outline-danger btn-sm px-3 fw-semibold"
                            onClick={() => iniciarCancelamento(r)}
                          >
                            🚫 Cancelar Reserva
                          </button>
                        )}
                        <button
                          className="btn btn-outline-primary btn-sm px-3 fw-semibold"
                          onClick={() => abrirVoucher(r.id)}
                          disabled={detalheCarregando}
                        >
                          📄 Voucher
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
      {!carregando && total > 0 && (
        <PaginationControls
          offset={offset}
          limit={PAGE_SIZE}
          total={total}
          onPageChange={setOffset}
        />
      )}

      {/* modal de confirmação de cancelamento com aviso de multa */}
      {reservaParaCancelar && (
        <div
          className="modal fade show d-block"
          style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
          tabIndex="-1"
        >
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content border-0 shadow">
              <div className="modal-header bg-danger text-white">
                <h5 className="modal-title fw-bold">🚫 Confirmar Cancelamento da Reserva</h5>
                <button
                  type="button"
                  className="btn-close btn-close-white"
                  onClick={() => setReservaParaCancelar(null)}
                  disabled={cancelando}
                />
              </div>

              <div className="modal-body p-4">
                {carregandoPreview ? (
                  <div className="text-center py-4">
                    <div className="spinner-border text-danger mb-2" role="status" />
                    <p className="text-muted small">Simulando regras e calculando multas aplicáveis...</p>
                  </div>
                ) : (
                  <>
                    <h5 className="fw-bold mb-1">{reservaParaCancelar.hotel_nome}</h5>
                    <p className="text-muted small mb-3">
                      Quarto #{reservaParaCancelar.quarto_numero} • Check-in:{' '}
                      {new Date(reservaParaCancelar.checkin + 'T00:00:00').toLocaleDateString('pt-BR')}
                    </p>

                    {previewCancelamento && (
                      <div className="border rounded p-3 mb-3 bg-light">
                        <h6 className="fw-bold text-dark mb-2">Simulação da Política de Cancelamento (RFO10):</h6>
                        <div
                          className={`alert ${
                            previewCancelamento.dentro_do_prazo &&
                            previewCancelamento.tipo_tarifa === 'reembolsavel'
                              ? 'alert-success'
                              : 'alert-warning'
                          } py-2 px-3 small mb-3`}
                        >
                          {previewCancelamento.mensagem_politica}
                        </div>

                        <div className="d-flex justify-content-between small mb-1">
                          <span>Valor Total Pago:</span>
                          <strong>R$ {previewCancelamento.valor_total.toFixed(2)}</strong>
                        </div>
                        <div className="d-flex justify-content-between small text-danger mb-1">
                          <span>Multa de Cancelamento:</span>
                          <strong>- R$ {previewCancelamento.valor_multa.toFixed(2)}</strong>
                        </div>
                        <hr className="my-2" />
                        <div className="d-flex justify-content-between fs-5 fw-bold text-success">
                          <span>Reembolso Líquido:</span>
                          <span>R$ {previewCancelamento.valor_reembolso.toFixed(2)}</span>
                        </div>
                      </div>
                    )}

                    <div className="mb-3">
                      <label className="form-label small fw-semibold text-muted">
                        Motivo do cancelamento (opcional):
                      </label>
                      <input
                        type="text"
                        className="form-control form-control-sm"
                        placeholder="Ex: Mudança de planos pessoais..."
                        value={motivoCancelamento}
                        onChange={(e) => setMotivoCancelamento(e.target.value)}
                        disabled={cancelando}
                      />
                    </div>

                    <p className="text-muted small mb-0">
                      ⚠️ Esta ação é definitiva e liberará a acomodação imediatamente no sistema.
                    </p>
                  </>
                )}
              </div>

              <div className="modal-footer bg-light">
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => setReservaParaCancelar(null)}
                  disabled={cancelando}
                >
                  Manter Reserva
                </button>
                <button
                  type="button"
                  className="btn btn-danger btn-sm px-3 fw-semibold"
                  onClick={confirmarCancelamento}
                  disabled={cancelando || carregandoPreview}
                >
                  {cancelando ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" />
                      Cancelando...
                    </>
                  ) : (
                    'Confirmar Cancelamento'
                  )}
                </button>
              </div>
            </div>
          </div>
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
                  <p className="text-muted small">ID: <code>{reservaSelecionada.id}</code></p>
                </div>

                <div className="row g-3 mb-3 small">
                  <div className="col-sm-4">
                    <div className="p-3 bg-light rounded">
                      <span className="text-muted d-block">Tipo de Tarifa</span>
                      <strong className="text-dark">
                        {reservaSelecionada.tipo_tarifa === 'reembolsavel' ? '🛡️ Reembolsável' : '🔒 Não Reembolsável'}
                      </strong>
                    </div>
                  </div>
                  <div className="col-sm-4">
                    <div className="p-3 bg-light rounded">
                      <span className="text-muted d-block">Check-in</span>
                      <strong className="text-dark">
                        {new Date(reservaSelecionada.checkin + 'T00:00:00').toLocaleDateString('pt-BR')}
                      </strong>
                    </div>
                  </div>
                  <div className="col-sm-4">
                    <div className="p-3 bg-light rounded">
                      <span className="text-muted d-block">Check-out</span>
                      <strong className="text-dark">
                        {new Date(reservaSelecionada.checkout + 'T00:00:00').toLocaleDateString('pt-BR')}
                      </strong>
                    </div>
                  </div>
                </div>

                {reservaSelecionada.status === 'Cancelada' && (
                  <div className="alert alert-danger p-3 mb-3">
                    <h6 className="fw-bold mb-1">Informações de Cancelamento (RFO10):</h6>
                    <div className="d-flex justify-content-between small">
                      <span>Multa Cobrada:</span>
                      <strong>R$ {Number(reservaSelecionada.valor_multa || 0).toFixed(2)}</strong>
                    </div>
                    <div className="d-flex justify-content-between small">
                      <span>Reembolso Concedido:</span>
                      <strong>R$ {Number(reservaSelecionada.valor_reembolso || 0).toFixed(2)}</strong>
                    </div>
                    {reservaSelecionada.motivo_cancelamento && (
                      <div className="mt-2 pt-2 border-top small text-muted">
                        <strong>Motivo:</strong> {reservaSelecionada.motivo_cancelamento}
                      </div>
                    )}
                  </div>
                )}

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
                  🖨️ Imprimir
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}