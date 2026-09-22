import api from './api'


export const cidadeService = {
  listar:    ()            => api.get('/cidades').then(r => r.data),
  criar:     (payload)     => api.post('/admin/cidades', payload).then(r => r.data),
  atualizar: (id, payload) => api.put(`/admin/cidades/${id}`, payload).then(r => r.data),
  remover:   (id)          => api.delete(`/admin/cidades/${id}`),
}


export const hotelService = {
  listar: (cidadeId = null) => {
    const params = cidadeId ? { cidade_id: cidadeId } : {}
    return api.get('/hoteis', { params }).then(r => r.data)
  },
  criar:     (payload)     => api.post('/admin/hoteis', payload).then(r => r.data),
  atualizar: (id, payload) => api.put(`/admin/hoteis/${id}`, payload).then(r => r.data),
  remover:   (id)          => api.delete(`/admin/hoteis/${id}`),
  adicionarComodidade: (hotelId, comodidadeId) =>
    api.post(`/admin/hoteis/${hotelId}/comodidades/${comodidadeId}`).then(r => r.data),
  removerComodidade: (hotelId, comodidadeId) =>
    api.delete(`/admin/hoteis/${hotelId}/comodidades/${comodidadeId}`),
}


export const comodidadeService = {
  listar:    ()            => api.get('/admin/comodidades').then(r => r.data),
  criar:     (payload)     => api.post('/admin/comodidades', payload).then(r => r.data),
  atualizar: (id, payload) => api.put(`/admin/comodidades/${id}`, payload).then(r => r.data),
  remover:   (id)          => api.delete(`/admin/comodidades/${id}`),
}