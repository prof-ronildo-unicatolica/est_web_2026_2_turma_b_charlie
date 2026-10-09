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
  obterPorId: (id)          => api.get(`/hoteis/${id}`).then(r => r.data),
  criar:      (payload)     => api.post('/admin/hoteis', payload).then(r => r.data),
  atualizar:  (id, payload) => api.put(`/admin/hoteis/${id}`, payload).then(r => r.data),
  remover:    (id)          => api.delete(`/admin/hoteis/${id}`),
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


export const quartoService = {
  listar: (hotelId = null) => {
    const params = hotelId ? { hotel_id: hotelId } : {}
    return api.get('/admin/quartos', { params }).then(r => r.data)
  },
  obterPorId: (id)          => api.get(`/admin/quartos/${id}`).then(r => r.data),
  criar:      (payload)     => api.post('/admin/quartos', payload).then(r => r.data),
  atualizar:  (id, payload) => api.put(`/admin/quartos/${id}`, payload).then(r => r.data),
  remover:    (id)          => api.delete(`/admin/quartos/${id}`),
}


export const buscaService = {
  buscarHoteis: (filtros = {}) => {
    const cleanParams = {}
    Object.keys(filtros).forEach((key) => {
      if (filtros[key] !== '' && filtros[key] !== null && filtros[key] !== undefined) {
        cleanParams[key] = filtros[key]
      }
    })
    return api.get('/busca', { params: cleanParams }).then(r => r.data)
  },
  reconstruirCatalogoMongo: () => api.post('/admin/catalogo/rebuild').then(r => r.data),
}
