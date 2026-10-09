import { useEffect, useState } from 'react'
import { cidadeService, hotelService } from '../../services/catalogo'

export default function AdminHoteisPage() {
  const [hoteis, setHoteis] = useState([])
  const [cidades, setCidades] = useState([])
  const [editando, setEditando] = useState(null)
  const [form, setForm] = useState({ nome: '', cidade_id: '', categoria_estrelas: '' })
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(false)

  const carregar = async () => {
    try {
      const [h, c] = await Promise.all([hotelService.listar(), cidadeService.listar()])
      setHoteis(h)
      setCidades(c)
    } catch {
      setErro('Erro ao carregar hotéis e cidades.')
    }
  }

  useEffect(() => { carregar() }, [])

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErro('')
    setCarregando(true)
    const payload = {
      nome: form.nome,
      cidade_id: form.cidade_id,
      categoria_estrelas: form.categoria_estrelas ? parseInt(form.categoria_estrelas) : null,
    }
    try {
      if (editando) {
        await hotelService.atualizar(editando.id, payload)
        setEditando(null)
      } else {
        await hotelService.criar(payload)
      }
      setForm({ nome: '', cidade_id: '', categoria_estrelas: '' })
      await carregar()
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao salvar hotel.')
    } finally {
      setCarregando(false)
    }
  }

  const handleEditar = (hotel) => {
    setEditando(hotel)
    setForm({ nome: hotel.nome, cidade_id: hotel.cidade.id, categoria_estrelas: hotel.categoria_estrelas ?? '' })
    setErro('')
  }

  const handleRemover = async (id) => {
    if (!window.confirm('Remover este hotel?')) return
    try {
      await hotelService.remover(id)
      await carregar()
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao remover hotel.')
    }
  }

  const renderEstrelas = (qtd) =>
    qtd ? String.fromCodePoint(0x2B50).repeat(qtd) : <span className="text-muted">—</span>

  return (
    <div className="container mt-4">
      <h2>Gerenciar Hotéis</h2>
      {erro && <div className="alert alert-danger">{erro}</div>}
      <div className="card mb-4 p-3">
        <h5>{editando ? 'Editar Hotel' : 'Novo Hotel'}</h5>
        <form onSubmit={handleSubmit}>
          <div className="row g-2">
            <div className="col-md-4">
              <input
                className="form-control"
                placeholder="Nome do hotel"
                name="nome"
                value={form.nome}
                onChange={handleChange}
                required
                maxLength={100}
              />
            </div>
            <div className="col-md-4">
              <select className="form-select" name="cidade_id" value={form.cidade_id} onChange={handleChange} required>
                <option value="">Selecione a cidade...</option>
                {cidades.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
              </select>
            </div>
            <div className="col-md-2">
              <select className="form-select" name="categoria_estrelas" value={form.categoria_estrelas} onChange={handleChange}>
                <option value="">Estrelas (opcional)</option>
                {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n} estrela(s)</option>)}
              </select>
            </div>
            <div className="col-md-2 d-flex gap-1">
              <button className="btn btn-primary flex-fill" type="submit" disabled={carregando}>
                {editando ? 'Salvar' : 'Criar'}
              </button>
              {editando && (
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => { setEditando(null); setForm({ nome: '', cidade_id: '', categoria_estrelas: '' }) }}
                >
                  X
                </button>
              )}
            </div>
          </div>
        </form>
      </div>
      <table className="table table-striped table-hover">
        <thead className="table-dark">
          <tr>
            <th>Nome</th>
            <th>Cidade</th>
            <th>Categoria</th>
            <th>Comodidades</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {hoteis.length === 0 && (
            <tr>
              <td colSpan={5} className="text-center text-muted">Nenhum hotel cadastrado.</td>
            </tr>
          )}
          {hoteis.map((hotel) => (
            <tr key={hotel.id}>
              <td>{hotel.nome}</td>
              <td>{hotel.cidade.nome}</td>
              <td>{renderEstrelas(hotel.categoria_estrelas)}</td>
              <td>
                {hotel.comodidades.length === 0
                  ? <span className="text-muted">—</span>
                  : hotel.comodidades.map((c) => (
                    <span key={c.id} className="badge bg-info me-1">{c.nome}</span>
                  ))}
              </td>
              <td>
                <button className="btn btn-sm btn-warning me-2" onClick={() => handleEditar(hotel)}>Editar</button>
                <button className="btn btn-sm btn-danger" onClick={() => handleRemover(hotel.id)}>Remover</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
