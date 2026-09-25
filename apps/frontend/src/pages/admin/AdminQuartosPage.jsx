import { useEffect, useState } from 'react'
import { hotelService, quartoService, buscaService } from '../../services/catalogo'

export default function AdminQuartosPage() {
  const [hoteis, setHoteis] = useState([])
  const [quartos, setQuartos] = useState([])
  const [hotelSelecionado, setHotelSelecionado] = useState('')
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState('')
  const [sucesso, setSucesso] = useState('')
  const [editando, setEditando] = useState(null)

  const [form, setForm] = useState({
    hotel_id: '',
    numero: '',
    tipo: 'Standard',
    preco_diaria: '',
    max_adultos: 2,
    max_criancas: 0,
    descricao: '',
    ativo: true,
  })

  const carregarHoteis = async () => {
    try {
      const lista = await hotelService.listar()
      setHoteis(lista)
      if (lista.length > 0) {
        setHotelSelecionado((atual) => atual || lista[0].id)
      }
    } catch {
      setErro('Erro ao carregar lista de hotéis.')
    }
  }

  const carregarQuartos = async (hid) => {
    try {
      setCarregando(true)
      const data = await quartoService.listar(hid || null)
      setQuartos(data)
    } catch {
      setErro('Erro ao carregar quartos.')
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => {
    carregarHoteis()
  }, [])

  useEffect(() => {
    if (hotelSelecionado) {
      carregarQuartos(hotelSelecionado)
    }
  }, [hotelSelecionado])

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setForm({
      ...form,
      [name]: type === 'checkbox' ? checked : value,
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErro('')
    setSucesso('')
    setCarregando(true)

    const payload = {
      hotel_id: form.hotel_id || hotelSelecionado,
      numero: form.numero.trim(),
      tipo: form.tipo.trim(),
      preco_diaria: parseFloat(form.preco_diaria),
      max_adultos: parseInt(form.max_adultos),
      max_criancas: parseInt(form.max_criancas),
      descricao: form.descricao.trim() || null,
      ativo: form.ativo,
    }

    try {
      if (editando) {
        await quartoService.atualizar(editando.id, payload)
        setSucesso('Quarto atualizado e MongoDB sincronizado!')
        setEditando(null)
      } else {
        await quartoService.criar(payload)
        setSucesso('Quarto cadastrado e MongoDB sincronizado!')
      }
      setForm({
        hotel_id: hotelSelecionado,
        numero: '',
        tipo: 'Standard',
        preco_diaria: '',
        max_adultos: 2,
        max_criancas: 0,
        descricao: '',
        ativo: true,
      })
      await carregarQuartos(hotelSelecionado)
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao salvar quarto.')
    } finally {
      setCarregando(false)
    }
  }

  const handleEditar = (quarto) => {
    setEditando(quarto)
    setForm({
      hotel_id: quarto.hotel_id,
      numero: quarto.numero,
      tipo: quarto.tipo,
      preco_diaria: quarto.preco_diaria,
      max_adultos: quarto.max_adultos,
      max_criancas: quarto.max_criancas,
      descricao: quarto.descricao || '',
      ativo: quarto.ativo,
    })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleRemover = async (id) => {
    if (!window.confirm('Deseja realmente remover este quarto?')) return
    try {
      await quartoService.remover(id)
      setSucesso('Quarto removido com sucesso!')
      await carregarQuartos(hotelSelecionado)
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao remover quarto.')
    }
  }

  const handleRebuildMongo = async () => {
    try {
      setCarregando(true)
      const res = await buscaService.reconstruirCatalogoMongo()
      setSucesso(`Catálogo MongoDB reconstruído! ${res.total_hoteis_sincronizados} hotéis sincronizados.`)
    } catch {
      setErro('Erro ao reconstruir catálogo no MongoDB.')
    } finally {
      setCarregando(false)
    }
  }

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Gerenciamento de Quartos (CQRS)</h2>
        <button className="btn btn-outline-secondary btn-sm" onClick={handleRebuildMongo} disabled={carregando}>
          🔄 Sincronizar Tudo com MongoDB
        </button>
      </div>

      {erro && <div className="alert alert-danger">{erro}</div>}
      {sucesso && <div className="alert alert-success">{sucesso}</div>}

      <div className="card shadow-sm p-4 mb-4">
        <h5 className="card-title mb-3 text-primary">
          {editando ? `Editar Quarto #${editando.numero}` : 'Cadastrar Novo Quarto'}
        </h5>
        <form onSubmit={handleSubmit}>
          <div className="row g-3">
            <div className="col-md-4">
              <label className="form-label small fw-bold">Hotel</label>
              <select
                className="form-select"
                name="hotel_id"
                value={form.hotel_id || hotelSelecionado}
                onChange={(e) => {
                  handleChange(e)
                  setHotelSelecionado(e.target.value)
                }}
                required
              >
                {hoteis.map(h => (
                  <option key={h.id} value={h.id}>{h.nome} ({h.cidade?.nome})</option>
                ))}
              </select>
            </div>

            <div className="col-md-2">
              <label className="form-label small fw-bold">Número</label>
              <input
                className="form-control"
                placeholder="Ex: 101"
                name="numero"
                value={form.numero}
                onChange={handleChange}
                required
                maxLength={20}
              />
            </div>

            <div className="col-md-3">
              <label className="form-label small fw-bold">Tipo de Quarto</label>
              <input
                className="form-control"
                placeholder="Ex: Casal Luxo, Família..."
                name="tipo"
                value={form.tipo}
                onChange={handleChange}
                required
                minLength={2}
                maxLength={50}
              />
            </div>

            <div className="col-md-3">
              <label className="form-label small fw-bold">Preço Diária (R$)</label>
              <input
                type="number"
                step="0.01"
                min="1"
                className="form-control"
                placeholder="Ex: 250.00"
                name="preco_diaria"
                value={form.preco_diaria}
                onChange={handleChange}
                required
              />
            </div>

            <div className="col-md-3">
              <label className="form-label small fw-bold">Máx. Adultos</label>
              <input
                type="number"
                min="1"
                max="10"
                className="form-control"
                name="max_adultos"
                value={form.max_adultos}
                onChange={handleChange}
                required
              />
            </div>

            <div className="col-md-3">
              <label className="form-label small fw-bold">Máx. Crianças</label>
              <input
                type="number"
                min="0"
                max="10"
                className="form-control"
                name="max_criancas"
                value={form.max_criancas}
                onChange={handleChange}
                required
              />
            </div>

            <div className="col-md-4">
              <label className="form-label small fw-bold">Descrição</label>
              <input
                className="form-control"
                placeholder="Detalhes opcionais..."
                name="descricao"
                value={form.descricao}
                onChange={handleChange}
                maxLength={500}
              />
            </div>

            <div className="col-md-2 d-flex align-items-center mt-4">
              <div className="form-check">
                <input
                  type="checkbox"
                  className="form-check-input"
                  id="ativoCheck"
                  name="ativo"
                  checked={form.ativo}
                  onChange={handleChange}
                />
                <label className="form-check-label" htmlFor="ativoCheck">Ativo</label>
              </div>
            </div>

            <div className="col-12 d-flex gap-2">
              <button className="btn btn-primary" type="submit" disabled={carregando}>
                {editando ? 'Salvar Alterações' : 'Criar Quarto'}
              </button>
              {editando && (
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    setEditando(null)
                    setForm({
                      hotel_id: hotelSelecionado,
                      numero: '',
                      tipo: 'Standard',
                      preco_diaria: '',
                      max_adultos: 2,
                      max_criancas: 0,
                      descricao: '',
                      ativo: true,
                    })
                  }}
                >
                  Cancelar
                </button>
              )}
            </div>
          </div>
        </form>
      </div>

      <div className="card shadow-sm p-3">
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h5 className="mb-0">Quartos Cadastrados</h5>
          <div className="d-flex align-items-center gap-2">
            <span className="small text-muted">Filtrar por Hotel:</span>
            <select
              className="form-select form-select-sm"
              value={hotelSelecionado}
              onChange={(e) => setHotelSelecionado(e.target.value)}
              style={{ width: '220px' }}
            >
              {hoteis.map(h => (
                <option key={h.id} value={h.id}>{h.nome}</option>
              ))}
            </select>
          </div>
        </div>

        <table className="table table-striped table-hover align-middle">
          <thead className="table-dark">
            <tr>
              <th>Número</th>
              <th>Tipo</th>
              <th>Diária</th>
              <th>Capacidades</th>
              <th>Status</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            {quartos.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-4 text-muted">
                  Nenhum quarto cadastrado para o hotel selecionado.
                </td>
              </tr>
            ) : (
              quartos.map(q => (
                <tr key={q.id}>
                  <td className="fw-bold">#{q.numero}</td>
                  <td>{q.tipo}</td>
                  <td>R$ {q.preco_diaria.toFixed(2)}</td>
                  <td>👥 {q.max_adultos} | 🧒 {q.max_criancas}</td>
                  <td>
                    {q.ativo ? (
                      <span className="badge bg-success">Ativo</span>
                    ) : (
                      <span className="badge bg-secondary">Inativo</span>
                    )}
                  </td>
                  <td>
                    <button className="btn btn-sm btn-warning me-2" onClick={() => handleEditar(q)}>
                      Editar
                    </button>
                    <button className="btn btn-sm btn-danger" onClick={() => handleRemover(q.id)}>
                      Remover
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
