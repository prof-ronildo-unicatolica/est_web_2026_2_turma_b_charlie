
import { useEffect, useState } from 'react'

const API = 'http://localhost:8000/api/v1'

export default function HoteisRaw() {
  const [hoteis, setHoteis] = useState(null)
  const [cidades, setCidades] = useState(null)
  const [erro, setErro] = useState(null)
  const [carregando, setCarregando] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch(`${API}/cidades`),
      fetch(`${API}/hoteis`),
    ])
      .then(async ([resCidades, resHoteis]) => {
        if (!resCidades.ok) throw new Error(`GET /cidades devolveu ${resCidades.status}`)
        if (!resHoteis.ok) throw new Error(`GET /hoteis devolveu ${resHoteis.status}`)
        return [await resCidades.json(), await resHoteis.json()]
      })
      .then(([jsonCidades, jsonHoteis]) => {
        setCidades(jsonCidades)
        setHoteis(jsonHoteis)
      })
      .catch((e) => setErro(e.message))
      .finally(() => setCarregando(false))
  }, [])

  if (carregando) return <p>Carregando hotéis...</p>

  if (erro) {
    return (
      <div style={{ border: '1px solid red', padding: '1rem', margin: '1rem 0' }}>
        <strong>Erro ao conectar com a API:</strong> {erro}
        <br />
        Verifique se o backend está ativo em: <code>{API}/health</code>
      </div>
    )
  }

  return (
    <section style={{ marginTop: '2rem' }}>
      <h2>Hotéis e Cidades — JSON Bruto</h2>
      <p>
        Saída literal da API confirmando que o dado atravessou banco → repository →
        service → rota → rede → navegador.
      </p>

      <h3>GET {API}/cidades</h3>
      <pre style={{ background: '#f4f4f4', padding: '1rem', overflowX: 'auto', color: '#111' }}>
        {JSON.stringify(cidades, null, 2)}
      </pre>

      <h3>GET {API}/hoteis</h3>
      <pre style={{ background: '#f4f4f4', padding: '1rem', overflowX: 'auto', color: '#111' }}>
        {JSON.stringify(hoteis, null, 2)}
      </pre>
    </section>
  )
}


