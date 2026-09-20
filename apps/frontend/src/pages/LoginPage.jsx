import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../services/api'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErro('')
    try {
      const resp = await api.post('/auth/login', { email, senha })
      localStorage.setItem('access_token', resp.data.access_token)

      // Busca dados do perfil logado
      const meResp = await api.get('/auth/me')
      localStorage.setItem('user_profile', JSON.stringify(meResp.data))

      navigate('/')
    } catch (err) {
      setErro(err.response?.data?.detail || 'Erro ao realizar login')
    }
  }

  return (
    <div className="container mt-5" style={{ maxWidth: '400px' }}>
      <div className="card shadow-sm p-4">
        <h3 className="mb-3 text-center">Entrar</h3>
        {erro && <div className="alert alert-danger">{erro}</div>}
        <form onSubmit={handleSubmit}>
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
            />
          </div>
          <button type="submit" className="btn btn-primary w-100">Acessar</button>
        </form>
        <p className="mt-3 text-center small">
          Não tem conta? <Link to="/register">Cadastre-se aqui</Link>
        </p>
      </div>
    </div>
  )
}