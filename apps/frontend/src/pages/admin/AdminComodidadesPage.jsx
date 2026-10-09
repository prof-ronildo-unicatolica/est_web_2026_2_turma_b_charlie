import { useEffect, useState } from 'react'
import { comodidadeService } from '../../services/catalogo'

export default function AdminComodidadesPage() {
  const [comodidades, setComodidades] = useState([])
  const [nome, setNome] = useState('')
  const [editando, setEditando] = useState(null)
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(false)

  const carregar = async () => {
    try { setComodidades(await comodidadeService.listar()) }
    catch { setErro('Erro ao carregar comodidades.') }
  }

  useEffect(() => { carregar() }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErro('')
    setCarregando(true)
    try {
      if (editando) {
        await comodidadeService.atualizar(editando.id, { nome }); setEditando(null)
      } else {
        await comodidadeService.criar({ nome })
      }
      setNome('')
      await carregar()
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao salvar comodidade.')
    } finally { setCarregando(false) }
  }

  const handleEditar = (com) => { setEditando(com); setNome(com.nome); setErro('') }

  const handleRemover = async (id) => {
    if (!window.confirm('Remover esta comodidade?')) return
    try { await comodidadeService.remover(id); await carregar() }
    catch (err) { setErro(err.response?.data?.detail || 'Erro ao remover comodidade.') }
  }

  return (
    <div className="container mt-4">
      <h2>Gerenciar Comodidades</h2>
      {erro && <div className="alert alert-danger">{erro}</div>}
      <div className="card mb-4 p-3">
        <h5>{editando ? 'Editar Comodidade' : 'Nova Comodidade'}</h5>
        <form onSubmit={handleSubmit} className="d-flex gap-2">
          <input
            className="form-control"
            placeholder="Ex: Piscina, Wi-Fi, Estacionamento..."
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            required
          />
          <button className="btn btn-primary" type="submit" disabled={carregando}>
            {editando ? 'Salvar' : 'Criar'}
          </button>
          {editando && (
            <button type="button" className="btn btn-secondary"
              onClick={() => { setEditando(null); setNome('') }}>
              Cancelar
            </button>
          )}
        </form>
      </div>
      <table className="table table-striped table-hover">
        <thead className="table-dark">
          <tr><th>Nome</th><th>Acoes</th></tr>
        </thead>
        <tbody>
          {comodidades.length === 0 && (
            <tr><td colSpan={2} className="text-center text-muted">Nenhuma comodidade cadastrada.</td></tr>
          )}
          {comodidades.map((com) => (
            <tr key={com.id}>
              <td>{com.nome}</td>
              <td>
                <button className="btn btn-sm btn-warning me-2" onClick={() => handleEditar(com)}>Editar</button>
                <button className="btn btn-sm btn-danger" onClick={() => handleRemover(com.id)}>Remover</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}