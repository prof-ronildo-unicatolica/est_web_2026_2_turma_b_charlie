import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { hotelService } from '../services/catalogo'

export default function HotelDetalhesPage() {
  const { id } = useParams()
  const [hotel, setHotel] = useState(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState('')

  useEffect(() => {
    const carregar = async () => {
      try {
        setCarregando(true)
        const data = await hotelService.obterPorId(id)
        setHotel(data)
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
                    className="btn btn-primary px-3"
                    onClick={() => alert(`Quarto ${quarto.tipo} (#${quarto.numero}) selecionado! O fluxo de reserva assíncrona será conectado nas próximas Sprints.`)}
                  >
                    Selecionar
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
