import { Navigate } from 'react-router-dom'

export default function AdminRoute({ children }) {
  const user = JSON.parse(localStorage.getItem('user_profile') || 'null')

  if (!user || !user.is_admin) {
    return <Navigate to="/" replace />
  }

  return children
}