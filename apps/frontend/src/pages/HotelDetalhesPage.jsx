import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { avaliacaoService, hotelService } from '../services/catalogo'

export default function HotelDetalhesPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [hotel, setHotel] = useState(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState('')
  const [avaliacoes, setAvaliacoes] = useState([])
  const [resumoAvaliacoes, setResumoAvaliacoes] = useState({ media: 0.0, total_avaliacoes: 0 })

  useEffect(() => {
    const carregar = async () => {
      try {
        setCarregando(true)
        const [hotelData, avalsData, resumoData] = await Promise.all([
          hotelService.obterPorId(id),
          avaliacaoService.listarPorHotel(id).catch(() => []),
          avaliacaoService.obterResumoHotel(id).catch(() => ({ media: 0.0, total_avaliacoes: 0 })),
        ])
        setHotel(hotelData)
        setAvaliacoes(avalsData)
        setResumoAvaliacoes(resumoData)
      } catch (err) {
        setErro(err.response?.data?.detail || 'Erro ao carregar detalhes do hotel.')
      } finally {
        setCarregando(false)
      }
    }
    carregar()
  }, [id])

  if (carregando) {
    return (
      <div className="container py-5 text-center">
        <div className="spinner-border text-primary" role="status"></div>
        <p className="mt-2 text-muted">Carregando acomodações do hotel...</p>
      </div>
    )
  }

  if (erro || !hotel) {
    return (
      <div className="container py-5">
        <div className="alert alert-danger">{erro || 'Hotel não encontrado.'}</div>
        <Link to="/" className="btn btn-outline-primary">← Voltar para a busca</Link>
      </div>
    )
  }

  const quartosAtivos = hotel.quartos?.filter(q => q.ativo) || []

  return (
    <div className="container py-4">
      <Link to="/" className="btn btn-link text-decoration-none px-0 mb-3">
        ← Voltar para busca de hotéis
      </Link>

      <div className="card shadow-sm border-0 mb-4 overflow-hidden">
        <div className="row g-0">
          <div className="col-md-5">
            <img
              src="https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80"
              alt={hotel.nome}
              className="img-fluid h-100 w-100"
              style={{ objectFit: 'cover', minHeight: '260px' }}
            />
          </div>
          <div className="col-md-7 d-flex flex-column justify-content-center p-4">
            <div className="d-flex align-items-center gap-2 mb-2">
              <span className="badge bg-primary fs-6">{hotel.cidade?.nome}</span>
              {hotel.categoria_estrelas && (
                <span className="text-warning fs-5">
                  {'★'.repeat(hotel.categoria_estrelas)}
                </span>
              )}
              {resumoAvaliacoes.total_avaliacoes > 0 ? (
                <span className="badge bg-warning text-dark fs-6 d-inline-flex align-items-center gap-1">
                  ⭐ {resumoAvaliacoes.media.toFixed(1)} / 5.0 ({resumoAvaliacoes.total_avaliacoes} avaliações)
                </span>
              ) : (
                <span className="badge bg-light text-muted border small">Sem avaliações ainda</span>
              )}
            </div>

            <h1 className="fw-bold display-6 mb-2">{hotel.nome}</h1>
            <p className="text-muted mb-3">
              📍 Localização privilegiada em {hotel.cidade?.nome}. Conforto, segurança e atendimento exclusivo.
            </p>

            <div className="mb-2">
              <strong className="d-block mb-1 text-secondary small text-uppercase fw-semibold">
                Comodidades do Hotel:
              </strong>
              {hotel.comodidades && hotel.comodidades.length > 0 ? (
                <div className="d-flex flex-wrap gap-1">
                  {hotel.comodidades.map(c => (
                    <span key={c.id} className="badge bg-info text-dark">
                      ✓ {c.nome}
                    </span>
                  ))}
                </div>
              ) : (
                <span className="text-muted small">Nenhuma comodidade cadastrada.</span>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="mb-4">
        <h3 className="fw-bold mb-1">Acomodações Disponíveis</h3>
        <p className="text-muted">Selecione o quarto ideal para sua viagem</p>
      </div>

      {quartosAtivos.length === 0 ? (
        <div className="alert alert-warning shadow-sm">
          Este hotel ainda não possui quartos ativos disponíveis para reserva.
        </div>
      ) : (
        <div className="row g-4">
          {quartosAtivos.map(quarto => (
            <div key={quarto.id} className="col-md-6 col-lg-4">
              <div className="card h-100 shadow-sm border-0 d-flex flex-column">
                <div className="card-header bg-white border-0 pt-3 pb-0 d-flex justify-content-between align-items-center">
                  <span className="badge bg-secondary">Quarto #{quarto.numero}</span>
                  <span className="badge bg-success-subtle text-success border border-success-subtle">
                    Disponível
                  </span>
                </div>
                <div className="card-body flex-grow-1">
                  <h4 className="card-title fw-bold text-primary mb-2">{quarto.tipo}</h4>
                  <p className="text-muted small mb-3">
                    {quarto.descricao || 'Quarto aconchegante com mobília moderna, ar-condicionado e banheiro privativo.'}
                  </p>

                  <div className="p-3 bg-light rounded mb-3">
                    <div className="d-flex justify-content-between small text-secondary mb-1">
                      <span>👥 Adultos:</span>
                      <strong>Até {quarto.max_adultos} pessoa(s)</strong>
                    </div>
                    <div className="d-flex justify-content-between small text-secondary">
                      <span>🧒 Crianças:</span>
                      <strong>Até {quarto.max_criancas} criança(s)</strong>
                    </div>
                  </div>
                </div>

                <div className="card-footer bg-white border-top p-3 d-flex justify-content-between align-items-center">
                  <div>
                    <span className="text-muted small d-block">Diária a partir de</span>
                    <strong className="fs-5 text-dark">
                      R$ {quarto.preco_diaria.toFixed(2)}
                    </strong>
                  </div>
                  <button
                    type="button"
                    className="btn btn-primary px-3"
                    onClick={() => navigate(`/checkout?hotel_id=${hotel.id}&quarto_id=${quarto.id}`)}
                  >
                    Reservar
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-5 pt-4 border-top">
        <div className="d-flex justify-content-between align-items-center mb-4">
          <div>
            <h3 className="fw-bold mb-1">Avaliações e Opiniões de Hóspedes</h3>
            <p className="text-muted mb-0">Comentários verificados de clientes que se hospedaram neste hotel</p>
          </div>
          {resumoAvaliacoes.total_avaliacoes > 0 && (
            <div className="text-end">
              <div className="fs-3 fw-bold text-dark">⭐ {resumoAvaliacoes.media.toFixed(1)}</div>
              <small className="text-muted">{resumoAvaliacoes.total_avaliacoes} hóspedes avaliaram</small>
            </div>
          )}
        </div>

        {avaliacoes.length === 0 ? (
          <div className="alert alert-light border text-muted py-4 text-center">
            Este hotel ainda não recebeu avaliações. Seja o primeiro a se hospedar e deixar sua opinião!
          </div>
        ) : (
          <div className="row g-3">
            {avaliacoes.map((av) => (
              <div className="col-md-6" key={av.id}>
                <div className="card h-100 border-0 shadow-sm bg-white p-3">
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <span className="fw-bold text-dark">{av.autor?.nome || 'Hóspede Anônimo'}</span>
                    <span className="text-warning fw-bold">
                      {'★'.repeat(av.nota)}{'☆'.repeat(5 - av.nota)}
                    </span>
                  </div>
                  <p className="text-muted small mb-2">
                    {av.comentario || 'Estadia excelente sem comentários adicionais.'}
                  </p>
                  <span className="text-muted" style={{ fontSize: '0.75rem' }}>
                    Avaliado em {new Date(av.criado_em).toLocaleDateString('pt-BR')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  )
}