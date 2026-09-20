import { Navigate } from 'react-router-dom'

export function ProtectedRoute({ children }) {
  const token = localStorage.getItem('access_token')
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return children
}

export function AdminRoute({ children }) {
  const token = localStorage.getItem('access_token')
  const user = JSON.parse(localStorage.getItem('user_profile') || '{}')

  if (!token) return <Navigate to="/login" replace />
  if (!user.is_admin) return <Navigate to="/" replace />

  return children
}