import { useEffect, useState } from 'react'
import { cidadeService } from '../../services/catalogo'

export default function AdminCidadesPage() {
  const [cidades, setCidades] = useState([])
  const [nome, setNome] = useState('')
  const [editando, setEditando] = useState(null)
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(false)

  const carregar = async () => {
    try {
      setCidades(await cidadeService.listar())
    } catch {
      setErro('Erro ao carregar cidades.')
    }
  }

  useEffect(() => { carregar() }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErro('')
    setCarregando(true)
    try {
      if (editando) {
        await cidadeService.atualizar(editando.id, { nome })
        setEditando(null)
      } else {
        await cidadeService.criar({ nome })
      }
      setNome('')
      await carregar()
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao salvar cidade.')
    } finally {
      setCarregando(false)
    }
  }

  const handleEditar = (cidade) => {
    setEditando(cidade)
    setNome(cidade.nome)
    setErro('')
  }

  const handleRemover = async (id) => {
    if (!window.confirm('Remover esta cidade? Os hotéis vinculados também serão removidos.')) return
    try {
      await cidadeService.remover(id)
      await carregar()
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao remover cidade.')
    }
  }

  return (
    <div className="container mt-4">
      <h2>Gerenciar Cidades</h2>
      {erro && <div className="alert alert-danger">{erro}</div>}
      <div className="card mb-4 p-3">
        <h5>{editando ? 'Editar Cidade' : 'Nova Cidade'}</h5>
        <form onSubmit={handleSubmit} className="d-flex gap-2">
          <input
            className="form-control"
            placeholder="Nome da cidade"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            required
            minLength={1}
            maxLength={100}
          />
          <button className="btn btn-primary" type="submit" disabled={carregando}>
            {editando ? 'Salvar' : 'Criar'}
          </button>
          {editando && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => { setEditando(null); setNome('') }}
            >
              Cancelar
            </button>
          )}
        </form>
      </div>
      <table className="table table-striped table-hover">
        <thead className="table-dark">
          <tr>
            <th>Nome</th>
            <th>Limite Territorial</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {cidades.length === 0 && (
            <tr>
              <td colSpan={3} className="text-center text-muted">Nenhuma cidade cadastrada.</td>
            </tr>
          )}
          {cidades.map((cidade) => (
            <tr key={cidade.id}>
              <td>{cidade.nome}</td>
              <td>
                {cidade.limite_territorial
                  ? <span className="badge bg-success">GeoJSON definido</span>
                  : <span className="badge bg-secondary">Não definido</span>}
              </td>
              <td>
                <button className="btn btn-sm btn-warning me-2" onClick={() => handleEditar(cidade)}>
                  Editar
                </button>
                <button className="btn btn-sm btn-danger" onClick={() => handleRemover(cidade.id)}>
                  Remover
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
