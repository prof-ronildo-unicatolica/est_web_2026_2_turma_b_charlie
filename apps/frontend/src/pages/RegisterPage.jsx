import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../services/api'

export default function RegisterPage() {
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [sucesso, setSucesso] = useState('')
  const [carregando, setCarregando] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErro('')
    setSucesso('')
    setCarregando(true)

    try {
      await api.post('/auth/register', { nome, email, senha })
      setSucesso('Cadastro realizado com sucesso! Redirecionando para login...')
      setTimeout(() => {
        navigate('/login')
      }, 1500)
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao realizar cadastro.')
    } finally {
      setCarregando(false)
    }
  }

  return (
    <div className="container mt-5" style={{ maxWidth: '450px' }}>
      <div className="card shadow-sm p-4">
        <h3 className="mb-3 text-center">Criar Conta</h3>
        {erro && <div className="alert alert-danger">{erro}</div>}
        {sucesso && <div className="alert alert-success">{sucesso}</div>}
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label">Nome Completo</label>
            <input
              type="text"
              className="form-control"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              required
              minLength={2}
              maxLength={120}
            />
          </div>
          <div className="mb-3">
            <label className="form-label">E-mail</label>
            <input
              type="email"
              className="form-control"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="mb-3">
            <label className="form-label">Senha</label>
            <input
              type="password"
              className="form-control"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              required
              minLength={6}
              maxLength={100}
            />
            <div className="form-text">Mínimo de 6 caracteres.</div>
          </div>
          <button type="submit" className="btn btn-primary w-100" disabled={carregando}>
            {carregando ? 'Cadastrando...' : 'Cadastrar'}
          </button>
        </form>
        <p className="mt-3 text-center small">
          Já tem conta? <Link to="/login">Entre aqui</Link>
        </p>
      </div>
    </div>
  )
}