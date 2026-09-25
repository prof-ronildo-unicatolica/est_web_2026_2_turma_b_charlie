import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import HotelSkeleton from '../components/HotelSkeleton'
import { buscaService, cidadeService } from '../services/catalogo'

export default function BuscaHoteisPage() {
  const [cidades, setCidades] = useState([])
  const [hoteis, setHoteis] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState('')

  const [filtros, setFiltros] = useState({
    cidade: '',
    estrelas: '',
    adultos: 2,
    criancas: 0,
    preco_max: '',
  })

  useEffect(() => {
    const carregarInicial = async () => {
      try {
        setCarregando(true)
        const [cidadesData, buscaData] = await Promise.all([
          cidadeService.listar(),
          buscaService.buscarHoteis(),
        ])
        setCidades(cidadesData)
        setHoteis(buscaData.hoteis || [])
      } catch {
        setErro('Erro ao conectar ao catálogo MongoDB.')
      } finally {
        setCarregando(false)
      }
    }
    carregarInicial()
  }, [])

  const handleChange = (e) => {
    setFiltros({ ...filtros, [e.target.name]: e.target.value })
  }

  const handleBuscar = async (e) => {
    if (e) e.preventDefault()
    setCarregando(true)
    setErro('')
    try {
      const data = await buscaService.buscarHoteis(filtros)
      setHoteis(data.hoteis || [])
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao realizar busca no MongoDB.')
    } finally {
      setCarregando(false)
    }
  }

  const handleLimparFiltros = async () => {
    const limpos = { cidade: '', estrelas: '', adultos: 2, criancas: 0, preco_max: '' }
    setFiltros(limpos)
    setCarregando(true)
    try {
      const data = await buscaService.buscarHoteis(limpos)
      setHoteis(data.hoteis || [])
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao buscar hotéis.')
    } finally {
      setCarregando(false)
    }
  }

  return (
    <div>
      <section className="bg-primary text-white py-5 mb-5 shadow-sm">
        <div className="container">
          <div className="row align-items-center mb-4">
            <div className="col-lg-8">
              <h1 className="display-5 fw-bold mb-2">Encontre sua Próxima Estadia</h1>
              <p className="lead opacity-75 mb-0">
                Hotéis de 1 a 5 estrelas com disponibilidade e busca ultrarrápida via MongoDB.
              </p>
            </div>
          </div>

          <div className="card shadow border-0 p-3 text-dark">
            <form onSubmit={handleBuscar}>
              <div className="row g-2 align-items-end">
                <div className="col-md-3">
                  <label className="form-label small fw-bold text-muted">Destino / Cidade</label>
                  <select
                    className="form-select"
                    name="cidade"
                    value={filtros.cidade}
                    onChange={handleChange}
                  >
                    <option value="">Todas as cidades</option>
                    {cidades.map(c => (
                      <option key={c.id} value={c.nome}>{c.nome}</option>
                    ))}
                  </select>
                </div>

                <div className="col-md-2 col-6">
                  <label className="form-label small fw-bold text-muted">Adultos</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    className="form-control"
                    name="adultos"
                    value={filtros.adultos}
                    onChange={handleChange}
                  />
                </div>

                <div className="col-md-2 col-6">
                  <label className="form-label small fw-bold text-muted">Crianças</label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    className="form-control"
                    name="criancas"
                    value={filtros.criancas}
                    onChange={handleChange}
                  />
                </div>

                <div className="col-md-2">
                  <label className="form-label small fw-bold text-muted">Estrelas Mínimas</label>
                  <select
                    className="form-select"
                    name="estrelas"
                    value={filtros.estrelas}
                    onChange={handleChange}
                  >
                    <option value="">Todas</option>
                    {[1, 2, 3, 4, 5].map(n => (
                      <option key={n} value={n}>{n} ★ ou mais</option>
                    ))}
                  </select>
                </div>

                <div className="col-md-3 d-flex gap-2">
                  <button type="submit" className="btn btn-primary flex-fill fw-bold py-2">
                    🔍 Buscar
                  </button>
                  <button
                    type="button"
                    className="btn btn-outline-secondary"
                    onClick={handleLimparFiltros}
                    title="Limpar Filtros"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      </section>

      <div className="container pb-5">
        <div className="d-flex justify-content-between align-items-center mb-4">
          <div>
            <h3 className="fw-bold mb-0">Hotéis Disponíveis</h3>
            <small className="text-muted">
              {hoteis.length} {hoteis.length === 1 ? 'hotel encontrado' : 'hotéis encontrados'} no catálogo
            </small>
          </div>
        </div>

        {erro && <div className="alert alert-danger">{erro}</div>}

        {carregando && <HotelSkeleton count={6} />}

        {!carregando && hoteis.length === 0 && (
          <div className="card p-5 text-center border-0 shadow-sm">
            <h4 className="text-secondary">Nenhum hotel atende aos filtros selecionados.</h4>
            <p className="text-muted">Experimente ajustar o destino ou reduzir os requisitos de hóspedes.</p>
            <div>
              <button className="btn btn-primary btn-sm" onClick={handleLimparFiltros}>
                Ver Todos os Hotéis
              </button>
            </div>
          </div>
        )}

        {!carregando && hoteis.length > 0 && (
          <div className="row g-4">
            {hoteis.map(hotel => (
              <div key={hotel.hotel_id} className="col-md-6 col-lg-4">
                <div className="card h-100 shadow-sm border-0 overflow-hidden d-flex flex-column hover-shadow transition">
                  <img
                    src="https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=600&q=80"
                    alt={hotel.nome}
                    className="card-img-top"
                    style={{ height: '200px', objectFit: 'cover' }}
                  />

                  <div className="card-body d-flex flex-column">
                    <div className="d-flex justify-content-between align-items-start mb-1">
                      <span className="badge bg-light text-dark border">
                        📍 {hotel.cidade_nome}
                      </span>
                      {hotel.categoria_estrelas && (
                        <span className="text-warning small">
                          {'★'.repeat(hotel.categoria_estrelas)}
                        </span>
                      )}
                    </div>

                    <h5 className="card-title fw-bold text-dark mt-2 mb-2">{hotel.nome}</h5>

                    <div className="d-flex flex-wrap gap-1 mb-3">
                      {hotel.comodidades && hotel.comodidades.length > 0 ? (
                        hotel.comodidades.slice(0, 3).map((c, i) => (
                          <span key={i} className="badge bg-info-subtle text-info-emphasis small">
                            {c}
                          </span>
                        ))
                      ) : (
                        <span className="text-muted small">Sem comodidades</span>
                      )}
                      {hotel.comodidades?.length > 3 && (
                        <span className="badge bg-light text-muted small">
                          +{hotel.comodidades.length - 3}
                        </span>
                      )}
                    </div>

                    <div className="mt-auto pt-3 border-top d-flex justify-content-between align-items-center">
                      <div>
                        <span className="text-muted small d-block">A partir de</span>
                        <strong className="fs-5 text-primary">
                          {hotel.preco_minimo > 0
                            ? `R$ ${hotel.preco_minimo.toFixed(2)}`
                            : 'Consulte'}
                        </strong>
                        <span className="text-muted small"> / diária</span>
                      </div>

                      <Link
                        to={`/hoteis/${hotel.hotel_id}`}
                        className="btn btn-outline-primary btn-sm px-3 fw-semibold"
                      >
                        Ver Quartos →
                      </Link>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
