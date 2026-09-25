import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'

import AdminRoute from './components/AdminRoute'
import HoteisRaw from './components/HoteisRaw'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import AdminCidadesPage     from './pages/admin/AdminCidadesPage'
import AdminHoteisPage      from './pages/admin/AdminHoteisPage'
import AdminComodidadesPage from './pages/admin/AdminComodidadesPage'
import AdminQuartosPage     from './pages/admin/AdminQuartosPage' 
import BuscaHoteisPage  from './pages/BuscaHoteisPage'  
import HotelDetalhesPage from './pages/HotelDetalhesPage' 


function Navbar() {
  const user = JSON.parse(localStorage.getItem('user_profile') || 'null')

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_profile')
    window.location.href = '/login'
  }

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark shadow-sm sticky-top">
      <div className="container">
        <Link className="navbar-brand d-flex align-items-center" to="/">
          <span className="fs-4 fw-bold text-primary">🏨 Rede Hoteleira</span>
          <span className="ms-2 badge bg-secondary small">Estágio II</span>
        </Link>
        <button
          className="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarNav"
          aria-controls="navbarNav"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav me-auto">
            <li className="nav-item">
              <Link className="nav-link" to="/">Buscar Hotéis</Link>
            </li>
          </ul>
          <div className="d-flex align-items-center gap-2">
            {/* dropdown admin */}
            {user?.is_admin && (
              <div className="dropdown me-2">
                <button
                  className="btn btn-outline-light btn-sm dropdown-toggle"
                  data-bs-toggle="dropdown"
                >
                  ⚙️ Painel Admin
                </button>
                <ul className="dropdown-menu dropdown-menu-end shadow">
                  <li><Link className="dropdown-item" to="/admin/cidades">Cidades</Link></li>
                  <li><Link className="dropdown-item" to="/admin/hoteis">Hotéis</Link></li>
                  <li><Link className="dropdown-item" to="/admin/comodidades">Comodidades</Link></li>
                  <li><hr className="dropdown-divider" /></li>
                  <li><Link className="dropdown-item fw-bold text-primary" to="/admin/quartos">Quartos & Catálogo</Link></li>
                </ul>
              </div>
            )}
            {user ? (
              <>
                <span className="text-light small me-2">{user.nome || user.email}</span>
                <button
                  className="btn btn-outline-danger btn-sm px-3"
                  type="button"
                  onClick={handleLogout}
                >
                  Sair
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn btn-outline-primary btn-sm px-3">
                  Login
                </Link>
                <Link to="/register" className="btn btn-primary btn-sm px-3">
                  Cadastrar
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}


export default function App() {
  return (
    <BrowserRouter>
      <div className="bg-light min-vh-100 d-flex flex-column justify-content-between">
        <Navbar />

        <main className="flex-grow-1">
          <Routes>
            {/* rotas publicas */}
            <Route path="/" element={<BuscaHoteisPage />} />
            <Route path="/hoteis/:id" element={<HotelDetalhesPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* rotas admin */}
            <Route
              path="/admin/cidades"
              element={<AdminRoute><AdminCidadesPage /></AdminRoute>}
            />
            <Route
              path="/admin/hoteis"
              element={<AdminRoute><AdminHoteisPage /></AdminRoute>}
            />
            <Route
              path="/admin/comodidades"
              element={<AdminRoute><AdminComodidadesPage /></AdminRoute>}
            />
            <Route
              path="/admin/quartos"
              element={<AdminRoute><AdminQuartosPage /></AdminRoute>}
            />
          </Routes>
        </main>

        <footer className="mt-5 py-4 bg-white border-top text-center text-muted small">
          <div className="container">
            <p className="mb-0">
              &copy; {new Date().getFullYear()} Rede Hoteleira — Estágio II (Turma B · Charlie). Todos os direitos reservados.
            </p>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  )
}