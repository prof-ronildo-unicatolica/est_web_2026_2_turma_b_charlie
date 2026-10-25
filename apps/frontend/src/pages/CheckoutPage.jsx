import { useEffect, useState } from 'react'
import { useSearchParams, Link, useNavigate } from 'react-router-dom'
import { cotacaoService, hotelService, quartoService, reservaService, servicoAdicionalService } from '../services/catalogo'

export default function CheckoutPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const quartoIdParam = searchParams.get('quarto_id')
  const hotelIdParam = searchParams.get('hotel_id')

  const hoje = new Date().toISOString().split('T')[0]
  const amanha = new Date(Date.now() + 86400000).toISOString().split('T')[0]

  const [quarto, setQuarto] = useState(null)
  const [hotel, setHotel] = useState(null)
  const [servicosDisponiveis, setServicosDisponiveis] = useState([])

  const [checkin, setCheckin] = useState(searchParams.get('checkin') || hoje)
  const [checkout, setCheckout] = useState(searchParams.get('checkout') || amanha)
  const [adultos, setAdultos] = useState(Number(searchParams.get('adultos')) || 2)
  const [criancas, setCriancas] = useState(Number(searchParams.get('criancas')) || 0)
  const [bebes, setBebes] = useState(Number(searchParams.get('bebes')) || 0)
  const [earlyCheckin, setEarlyCheckin] = useState(false)
  const [lateCheckout, setLateCheckout] = useState(false)
  const [tipoTarifa, setTipoTarifa] = useState('reembolsavel')
  const [servicosSelecionados, setServicosSelecionados] = useState([])

  const [cotacao, setCotacao] = useState(null)
  const [calculando, setCalculando] = useState(false)
  const [erroCotacao, setErroCotacao] = useState('')
  const [sucessoMsg, setSucessoMsg] = useState('')
  const [reservaId, setReservaId] = useState(null)
  const [reservaStatus, setReservaStatus] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const [erroReserva, setErroReserva] = useState('')

  useEffect(() => {
    if (!reservaId || reservaStatus !== 'Pendente') return

    const intervalo = setInterval(async () => {
      try {
        const data = await reservaService.consultarStatus(reservaId)
        setReservaStatus(data.status)
        if (data.status !== 'Pendente') clearInterval(intervalo)
      } catch (err) {
        console.error('[Polling] Erro:', err)
      }
    }, 3000)

    return () => clearInterval(intervalo)
  }, [reservaId, reservaStatus])

  useEffect(() => {
    const carregarDadosIniciais = async () => {
      try {
        if (quartoIdParam) {
          const q = await quartoService.obterPorId(quartoIdParam)
          setQuarto(q)
          const hId = hotelIdParam || q.hotel_id
          if (hId) {
            const [h, servicos] = await Promise.all([
              hotelService.obterPorId(hId),
              servicoAdicionalService.listarPorHotel(hId).catch(() => []),
            ])
            setHotel(h)
            setServicosDisponiveis(servicos)
          }
        }
      } catch (err) {
        setErroCotacao('Não foi possível carregar os detalhes da acomodação.')
      }
    }
    carregarDadosIniciais()
  }, [quartoIdParam, hotelIdParam])

  useEffect(() => {
    if (!quartoIdParam || !checkin || !checkout) return

    const timer = setTimeout(async () => {
      try {
        setCalculando(true)
        setErroCotacao('')
        const payload = {
          quarto_id: quartoIdParam,
          checkin,
          checkout,
          adultos: Number(adultos),
          criancas: Number(criancas),
          bebes: Number(bebes),
          early_checkin: earlyCheckin,
          late_checkout: lateCheckout,
          tipo_tarifa: tipoTarifa,
          servicos_adicionais_ids: servicosSelecionados,
        }
        const data = await cotacaoService.calcular(payload)
        setCotacao(data)
      } catch (err) {
        setErroCotacao(err.response?.data?.detail || 'Erro ao calcular cotação.')
        setCotacao(null)
      } finally {
        setCalculando(false)
      }
    }, 250)

    return () => clearTimeout(timer)
  }, [
    quartoIdParam,
    checkin,
    checkout,
    adultos,
    criancas,
    bebes,
    earlyCheckin,
    lateCheckout,
    tipoTarifa,
    servicosSelecionados,
  ])

  const toggleServico = (id) => {
    setServicosSelecionados((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    )
  }

  const handleFinalizar = async (e) => {
    e.preventDefault()
    if (!cotacao) return
    try {
      setEnviando(true)
      setErroReserva('')
      const payload = {
        quarto_id: quartoIdParam,
        checkin,
        checkout,
        adultos: Number(adultos),
        criancas: Number(criancas),
        bebes: Number(bebes),
        valor_total: cotacao.valor_total,
        cotacao_snapshot: cotacao,
      }
      const resposta = await reservaService.criar(payload)
      setReservaId(resposta.id)
      setReservaStatus('Pendente')
    } catch (err) {
      setErroReserva(err.response?.data?.detail || 'Erro ao criar reserva. Tente novamente.')
    } finally {
      setEnviando(false)
    }
  }

  if (!quartoIdParam) {
    return (
      <div className="container py-5 text-center">
        <div className="alert alert-warning">
          Nenhum quarto selecionado para checkout.
        </div>
        <Link to="/" className="btn btn-primary">Voltar para a Busca</Link>
      </div>
    )
  }
  if (reservaStatus === 'Pendente') {
    return (
      <div className="container py-5 text-center">
        <div className="card shadow-sm border-0 p-5 mx-auto" style={{ maxWidth: '520px' }}>
          <div className="spinner-border text-primary mb-4" style={{ width: '3rem', height: '3rem' }} role="status" />
          <h3 className="fw-bold mb-2">A processar a sua Reserva...</h3>
          <p className="text-muted">A validar disponibilidade e a processar o pagamento.</p>
          <div className="mt-3 badge bg-secondary p-2">
            ID: <code className="text-white">{reservaId}</code>
          </div>
          <p className="text-muted small mt-3">🔄 A verificar a cada 3 segundos...</p>
        </div>
      </div>
    )
  }

  if (reservaStatus === 'Confirmada') {
    return (
      <div className="container py-5">
        <div className="card border-success shadow p-5 mx-auto" style={{ maxWidth: '600px' }}>
          <div className="text-center mb-4">
            <span style={{ fontSize: '4rem' }}>🎉</span>
            <h2 className="fw-bold text-success mt-2">Reserva Confirmada!</h2>
            <p className="text-muted">Pagamento processado com sucesso.</p>
          </div>
          <div className="border rounded p-4 bg-light mb-4">
            <h5 className="fw-bold mb-3 text-primary">🏨 Voucher da Reserva</h5>
            <div className="row g-2 small">
              <div className="col-6"><strong>ID:</strong><div className="text-muted font-monospace">{reservaId}</div></div>
              <div className="col-6"><strong>Status:</strong><div><span className="badge bg-success">✅ Confirmada</span></div></div>
              <div className="col-6"><strong>Hotel:</strong><div className="text-muted">{hotel?.nome}</div></div>
              <div className="col-6"><strong>Quarto:</strong><div className="text-muted">#{quarto?.numero} — {quarto?.tipo}</div></div>
              <div className="col-6"><strong>Check-in:</strong><div className="text-muted">{checkin}</div></div>
              <div className="col-6"><strong>Check-out:</strong><div className="text-muted">{checkout}</div></div>
              <div className="col-6"><strong>Hóspedes:</strong>
                <div className="text-muted">{adultos} adulto(s){criancas > 0 ? `, ${criancas} criança(s)` : ''}{bebes > 0 ? `, ${bebes} bebê(s)` : ''}</div>
              </div>
              <div className="col-6"><strong>Total:</strong><div className="text-success fw-bold fs-5">R$ {cotacao?.valor_total?.toFixed(2)}</div></div>
            </div>
          </div>
          <div className="d-flex gap-3 justify-content-center">
            <button className="btn btn-outline-secondary" onClick={() => window.print()}>🖨️ Imprimir</button>
            <Link to="/" className="btn btn-primary px-4">🏠 Voltar à Busca</Link>
          </div>
        </div>
      </div>
    )
  }

  if (reservaStatus === 'Cancelada' || erroReserva) {
    return (
      <div className="container py-5">
        <div className="card border-danger shadow p-5 mx-auto text-center" style={{ maxWidth: '520px' }}>
          <span style={{ fontSize: '4rem' }}>❌</span>
          <h2 className="fw-bold text-danger mt-2">Reserva Cancelada</h2>
          <p className="text-muted mt-2">
            {erroReserva || 'O quarto já não está disponível para este período (overbooking).'}
          </p>
          {reservaId && <p className="small text-muted">ID: <code>{reservaId}</code></p>}
          <div className="d-flex gap-3 justify-content-center mt-4">
            <button className="btn btn-outline-secondary"
              onClick={() => { setReservaId(null); setReservaStatus(null); setErroReserva('') }}>
              ← Tentar Novamente
            </button>
            <Link to="/" className="btn btn-primary px-4">Pesquisar Outros Quartos</Link>
          </div>
        </div>
      </div>
    )
  }
  return (
    <div className="container py-4">
      {/* header */}
      <div className="d-flex justify-content-between align-items-center mb-4 pb-2 border-bottom">
        <div>
          <h2 className="fw-bold mb-1">Finalização & Checkout</h2>
          <p className="text-muted mb-0">Confira as opções da sua estadia e visualize o valor total em tempo real.</p>
        </div>
        <Link to="/" className="btn btn-outline-secondary btn-sm">← Cancelar e Voltar</Link>
      </div>

      {sucessoMsg && (
        <div className="alert alert-success alert-dismissible fade show p-3 shadow-sm mb-4">
          <h5 className="alert-heading fw-bold mb-1">🎉 Sucesso na Cotação!</h5>
          <p className="mb-0">{sucessoMsg}</p>
        </div>
      )}

      {erroCotacao && (
        <div className="alert alert-danger shadow-sm mb-4">
          <strong>Atenção:</strong> {erroCotacao}
        </div>
      )}

      <div className="row g-4">
        {/* form principal */}
        <div className="col-lg-7">
          {/* card de quarto e hotel */}
          <div className="card shadow-sm border-0 mb-4">
            <div className="card-body p-4">
              <h5 className="fw-bold text-primary mb-2">Acomodação Selecionada</h5>
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h4 className="fw-bold mb-1">{hotel?.nome || 'Carregando hotel...'}</h4>
                  <span className="badge bg-secondary me-2">Quarto #{quarto?.numero}</span>
                  <span className="text-muted">{quarto?.tipo}</span>
                </div>
                <div className="text-end">
                  <span className="text-muted small d-block">Diária Base</span>
                  <strong className="fs-5 text-dark">R$ {quarto?.preco_diaria?.toFixed(2)}</strong>
                </div>
              </div>
            </div>
          </div>

          {/* card de datas e hospedes */}
          <div className="card shadow-sm border-0 mb-4">
            <div className="card-body p-4">
              <h5 className="fw-bold mb-3">1. Datas e Hóspedes</h5>
              <div className="row g-3">
                <div className="col-sm-6">
                  <label className="form-label small fw-semibold">Data de Check-in</label>
                  <input
                    type="date"
                    className="form-control"
                    value={checkin}
                    onChange={(e) => setCheckin(e.target.value)}
                  />
                </div>
                <div className="col-sm-6">
                  <label className="form-label small fw-semibold">Data de Check-out</label>
                  <input
                    type="date"
                    className="form-control"
                    value={checkout}
                    onChange={(e) => setCheckout(e.target.value)}
                  />
                </div>

                <div className="col-sm-4">
                  <label className="form-label small fw-semibold">Adultos</label>
                  <input
                    type="number"
                    min="1"
                    max={quarto?.max_adultos || 4}
                    className="form-control"
                    value={adultos}
                    onChange={(e) => setAdultos(e.target.value)}
                  />
                  <small className="text-muted">Máx: {quarto?.max_adultos || 2}</small>
                </div>

                <div className="col-sm-4">
                  <label className="form-label small fw-semibold">Crianças (6 a 12 anos)</label>
                  <input
                    type="number"
                    min="0"
                    max={quarto?.max_criancas || 2}
                    className="form-control"
                    value={criancas}
                    onChange={(e) => setCriancas(e.target.value)}
                  />
                  <small className="text-primary fw-semibold">+50% diária base</small>
                </div>

                <div className="col-sm-4">
                  <label className="form-label small fw-semibold">Bebês (0 a 5 anos)</label>
                  <input
                    type="number"
                    min="0"
                    max="3"
                    className="form-control"
                    value={bebes}
                    onChange={(e) => setBebes(e.target.value)}
                  />
                  <small className="text-success fw-bold">Grátis</small>
                </div>
              </div>
            </div>
          </div>

          {/* card tipo de tarefa */}
          <div className="card shadow-sm border-0 mb-4">
            <div className="card-body p-4">
              <h5 className="fw-bold mb-3">2. Modalidade de Tarifa</h5>
              <div className="d-flex flex-column gap-3">
                <label className={`card p-3 border cursor-pointer ${tipoTarifa === 'reembolsavel' ? 'border-primary bg-primary-subtle' : ''}`}>
                  <div className="d-flex align-items-center">
                    <input
                      type="radio"
                      name="tipoTarifa"
                      className="form-check-input me-3"
                      checked={tipoTarifa === 'reembolsavel'}
                      onChange={() => setTipoTarifa('reembolsavel')}
                    />
                    <div>
                      <strong className="d-block">Tarifa Flexível (Reembolsável)</strong>
                      <span className="small text-muted">Cancelamento sem custo até 48h antes da viagem. Preço regular.</span>
                    </div>
                  </div>
                </label>

                <label className={`card p-3 border cursor-pointer ${tipoTarifa === 'nao_reembolsavel' ? 'border-success bg-success-subtle' : ''}`}>
                  <div className="d-flex align-items-center">
                    <input
                      type="radio"
                      name="tipoTarifa"
                      className="form-check-input me-3"
                      checked={tipoTarifa === 'nao_reembolsavel'}
                      onChange={() => setTipoTarifa('nao_reembolsavel')}
                    />
                    <div>
                      <div className="d-flex align-items-center gap-2">
                        <strong className="d-block">Tarifa Promocional (Não Reembolsável)</strong>
                        <span className="badge bg-success">10% OFF</span>
                      </div>
                      <span className="small text-muted">Economize 10% no valor da estadia. Sem direito a reembolso em cancelamento.</span>
                    </div>
                  </div>
                </label>
              </div>
            </div>
          </div>

          {/* card horarios */}
          <div className="card shadow-sm border-0 mb-4">
            <div className="card-body p-4">
              <h5 className="fw-bold mb-3">3. Opcionais de Horário (RFO09)</h5>
              <div className="form-check form-switch mb-3">
                <input
                  className="form-check-input"
                  type="checkbox"
                  role="switch"
                  id="earlyCheckinSwitch"
                  checked={earlyCheckin}
                  onChange={(e) => setEarlyCheckin(e.target.checked)}
                />
                <label className="form-check-label ms-2" htmlFor="earlyCheckinSwitch">
                  <strong>Early Check-in (+30% de 1 diária base)</strong>
                  <span className="d-block small text-muted">Entrada antecipada a partir das 09:00h da manhã.</span>
                </label>
              </div>

              <div className="form-check form-switch">
                <input
                  className="form-check-input"
                  type="checkbox"
                  role="switch"
                  id="lateCheckoutSwitch"
                  checked={lateCheckout}
                  onChange={(e) => setLateCheckout(e.target.checked)}
                />
                <label className="form-check-label ms-2" htmlFor="lateCheckoutSwitch">
                  <strong>Late Check-out (+30% de 1 diária base)</strong>
                  <span className="d-block small text-muted">Saída estendida até as 18:00h da tarde.</span>
                </label>
              </div>
            </div>
          </div>

          {/* card servicos adicionais */}
          {servicosDisponiveis.length > 0 && (
            <div className="card shadow-sm border-0 mb-4">
              <div className="card-body p-4">
                <h5 className="fw-bold mb-3">4. Serviços Adicionais Disponíveis</h5>
                <div className="list-group">
                  {servicosDisponiveis.map((s) => (
                    <label key={s.id} className="list-group-item d-flex justify-content-between align-items-center">
                      <div className="d-flex align-items-center">
                        <input
                          type="checkbox"
                          className="form-check-input me-3"
                          checked={servicosSelecionados.includes(s.id)}
                          onChange={() => toggleServico(s.id)}
                        />
                        <div>
                          <strong>{s.nome}</strong>
                          {s.descricao && <span className="d-block small text-muted">{s.descricao}</span>}
                        </div>
                      </div>
                      <span className="badge bg-light text-dark fs-6 border">
                        R$ {s.preco.toFixed(2)} {s.por_diaria ? '/ diária' : '(taxa fixa)'}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* resumo lateral */}
        <div className="col-lg-5">
          <div className="card shadow-sm border-0 sticky-top" style={{ top: '90px' }}>
            <div className="card-header bg-primary text-white p-3">
              <h5 className="fw-bold mb-0">Resumo da Cotação</h5>
            </div>
            <div className="card-body p-4">
              {calculando ? (
                <div className="py-4 text-center">
                  <div className="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
                  <span className="text-muted">Calculando melhor tarifa...</span>
                </div>
              ) : cotacao ? (
                <div>
                  <div className="d-flex justify-content-between small text-muted mb-2">
                    <span>Período da viagem:</span>
                    <strong>{cotacao.num_diarias} noites</strong>
                  </div>

                  <hr className="my-2" />

                  {/* diarias individuais */}
                  <div className="mb-2">
                    <span className="small fw-bold text-secondary text-uppercase d-block mb-1">
                      Diárias por Data:
                    </span>
                    {cotacao.diarias.map((d, idx) => (
                      <div key={idx} className="d-flex justify-content-between small text-muted mb-1">
                        <span>
                          {d.data}{' '}
                          {d.tarifa_aplicada && (
                            <span className="badge bg-warning-subtle text-dark border">
                              {d.tarifa_aplicada} ({d.multiplicador_temporada}x)
                            </span>
                          )}
                        </span>
                        <span>R$ {d.valor_final.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>

                  <div className="d-flex justify-content-between small fw-semibold text-dark mb-2">
                    <span>Subtotal Diárias:</span>
                    <span>R$ {cotacao.subtotal_diarias.toFixed(2)}</span>
                  </div>

                  {/* adicionais de hospedes */}
                  {cotacao.criancas > 0 && (
                    <div className="d-flex justify-content-between small text-primary mb-1">
                      <span>Crianças extras ({cotacao.criancas}x a 50%):</span>
                      <span>+ R$ {cotacao.adicional_criancas.toFixed(2)}</span>
                    </div>
                  )}

                  {cotacao.bebes > 0 && (
                    <div className="d-flex justify-content-between small text-success mb-1">
                      <span>Bebês ({cotacao.bebes}x):</span>
                      <span>Grátis (R$ 0,00)</span>
                    </div>
                  )}

                  {/* antes e depois */}
                  {cotacao.taxa_early_checkin > 0 && (
                    <div className="d-flex justify-content-between small text-secondary mb-1">
                      <span>Early Check-in (+30%):</span>
                      <span>+ R$ {cotacao.taxa_early_checkin.toFixed(2)}</span>
                    </div>
                  )}

                  {cotacao.taxa_late_checkout > 0 && (
                    <div className="d-flex justify-content-between small text-secondary mb-1">
                      <span>Late Check-out (+30%):</span>
                      <span>+ R$ {cotacao.taxa_late_checkout.toFixed(2)}</span>
                    </div>
                  )}

                  {/* desconto nao reembolsavel */}
                  {cotacao.desconto_nao_reembolsavel > 0 && (
                    <div className="d-flex justify-content-between small text-success fw-bold mb-1">
                      <span>Desconto Não Reembolsável (-10%):</span>
                      <span>- R$ {cotacao.desconto_nao_reembolsavel.toFixed(2)}</span>
                    </div>
                  )}

                  {/* servicos adicionais */}
                  {cotacao.servicos_selecionados.length > 0 && (
                    <div className="mt-2 pt-2 border-top">
                      <span className="small fw-bold text-secondary text-uppercase d-block mb-1">
                        Serviços Adicionais:
                      </span>
                      {cotacao.servicos_selecionados.map((s) => (
                        <div key={s.id} className="d-flex justify-content-between small text-muted mb-1">
                          <span>{s.nome} ({s.quantidade_dias}x):</span>
                          <span>+ R$ {s.valor_total.toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  <hr className="my-3" />

                  {/* total final */}
                  <div className="d-flex justify-content-between align-items-center mb-3">
                    <span className="fs-5 fw-bold text-dark">Valor Total:</span>
                    <strong className="fs-3 text-success">
                      R$ {cotacao.valor_total.toFixed(2)}
                    </strong>
                  </div>

                  <button
                    className="btn btn-primary w-100 py-3 fw-bold fs-5 shadow-sm"
                    onClick={handleFinalizar}
                    disabled={enviando || !cotacao}
                  >
                    {enviando ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" role="status" />
                        A enviar Solicitação...
                      </>
                    ) : (
                      'Confirmar Solicitação de Reserva'
                    )}
                  </button>
                  <small className="text-muted text-center d-block mt-2">
                    🔒 Pagamento protegido e confirmação garantida.
                  </small>
                </div>
              ) : (
                <div className="text-muted text-center py-4">
                  Informe as datas e hóspedes para visualizar o cálculo.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}