import { useState } from 'react';
import './index.css';

interface Camera {
  id: string;
  ip: string;
  name: string;
  status: 'online' | 'offline' | 'auth_required';
  rtspUrl?: string;
}

function App() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);
  const [authForm, setAuthForm] = useState({ user: 'admin', pass: '' });
  const [isAuthenticating, setIsAuthenticating] = useState(false);

  const handleScan = async () => {
    setIsScanning(true);
    try {
      // Em produção, isso deveria ser o IP da máquina, não localhost, para funcionar no celular
      const response = await fetch('http://localhost:3001/api/scan');
      const data = await response.json();

      if (data.success) {
        setCameras(data.cameras.map((cam: any) => ({
          id: cam.id,
          ip: cam.ip, // Geralmente vem uma URL completa, precisaríamos limpar
          name: cam.name,
          status: 'online' // Se o scan achou, está online
        })));
      }
    } catch (error) {
      console.error("Erro ao conectar com servidor:", error);
      alert("Erro ao conectar ao servidor local (Backend offline?)");
    } finally {
      setIsScanning(false);
    }
  };

  const handleCameraClick = (cam: Camera) => {
    // Abre sempre para permitir reautenticação ou correção de senha
    setSelectedCamera(cam);
    setAuthForm({ user: 'admin', pass: '' });
    setShowAuthModal(true);
  };

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCamera) return;

    setIsAuthenticating(true);
    try {
      const response = await fetch('http://localhost:3001/api/camera/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ip: selectedCamera.ip,
          user: authForm.user,
          pass: authForm.pass
        })
      });
      const data = await response.json();

      if (data.success) {
        // Atualiza a câmera para online e salva o streamUrl (na memória por enquanto)
        setCameras(prev => prev.map(c =>
          c.id === selectedCamera.id ? { ...c, status: 'online', name: `${c.name} (Autenticada)` } : c
        ));
        setShowAuthModal(false);
        alert(`Sucesso! Câmera ${selectedCamera.ip} conectada.`);
      } else {
        alert("Falha na autenticação: " + data.message);
      }
    } catch (error) {
      console.error(error);
      alert("Erro ao comunicar com servidor.");
    } finally {
      setIsAuthenticating(false);
    }
  };

  const [showManualModal, setShowManualModal] = useState(false);
  const [manualForm, setManualForm] = useState({ ip: '', user: 'admin', pass: '', mode: 'simple', customUrl: '' });

  // === ARP SCAN LOGIC ===
  const [showArpModal, setShowArpModal] = useState(false);
  const [arpDevices, setArpDevices] = useState<any[]>([]);

  const handleArpScan = async () => {
    setShowArpModal(true);
    try {
      const res = await fetch('http://localhost:3001/api/network/devices');
      const data = await res.json();
      if (data.success) {
        setArpDevices(data.devices);
      }
    } catch (e) {
      alert("Erro ao listar rede. Backend offline?");
    }
  };

  const selectArpDevice = (ip: string) => {
    setManualForm(prev => ({ ...prev, ip }));
    setShowArpModal(false);
    setShowManualModal(true);
  };
  // ======================

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsAuthenticating(true);

    // Tenta validar direto
    try {
      const payload = manualForm.mode === 'simple'
        ? { ip: manualForm.ip, user: manualForm.user, pass: manualForm.pass }
        : { ip: 'custom', user: 'admin', pass: '', rtspUrl: manualForm.customUrl }; // Envia URL direta

      const response = await fetch('http://localhost:3001/api/camera/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();

      if (data.success) {
        const newCam: Camera = {
          id: `manual-${Date.now()}`,
          ip: manualForm.mode === 'simple' ? manualForm.ip : 'Custom URL',
          name: manualForm.mode === 'simple' ? `Câmera Manual (${manualForm.ip})` : 'Câmera Customizada',
          status: 'online',
          rtspUrl: data.streamUrl // Salva a URL retornada pelo backend
        };
        setCameras(prev => [...prev, newCam]);
        setShowManualModal(false);
        setManualForm({ ip: '', user: 'admin', pass: '', mode: 'simple', customUrl: '' }); // Reset
        alert("Câmera adicionada com sucesso!");
      } else {
        alert("Não foi possível conectar: " + data.message);
      }
    } catch (err) {
      alert("Erro ao contatar servidor.");
    } finally {
      setIsAuthenticating(false);
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', position: 'relative' }}>

      {/* ARP List Modal */}
      {showArpModal && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 110,
          background: 'rgba(0,0,0,0.9)', backdropFilter: 'blur(5px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <div className="glass-panel" style={{ padding: '2rem', width: '500px', borderRadius: '12px', maxHeight: '80vh', display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ marginBottom: '1rem' }}>Dispositivos na Rede (ARP)</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
              Selecione um IP abaixo para tentar adicionar como câmera.
            </p>

            <div style={{ flex: 1, overflowY: 'auto', marginBottom: '1rem' }}>
              {arpDevices.length === 0 ? <p style={{ textAlign: 'center', padding: '2rem' }}>Carregando...</p> : (
                <ul style={{ listStyle: 'none' }}>
                  {arpDevices.map((dev, i) => (
                    <li key={i} onClick={() => selectArpDevice(dev.ip)} style={{
                      padding: '0.8rem',
                      borderBottom: '1px solid var(--border-color)',
                      cursor: 'pointer',
                      display: 'flex', justifyContent: 'space-between'
                    }}
                      onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    >
                      <span style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>{dev.ip}</span>
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{dev.type} [{dev.mac}]</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <button onClick={() => setShowArpModal(false)} style={{ padding: '1rem', background: 'transparent', border: '1px solid var(--border-color)', color: 'white', borderRadius: '8px', cursor: 'pointer' }}>
              Fechar
            </button>
          </div>
        </div>
      )}

      {/* Manual Add Modal */}
      {showManualModal && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 100,
          background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(5px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <div className="glass-panel" style={{ padding: '2rem', width: '400px', borderRadius: '12px' }}>
            <h3 style={{ marginBottom: '1rem' }}>Adicionar Câmera</h3>

            <div style={{ display: 'flex', gap: '10px', marginBottom: '1.5rem' }}>
              <button
                onClick={() => setManualForm(f => ({ ...f, mode: 'simple' }))}
                style={{ flex: 1, padding: '5px', background: manualForm.mode === 'simple' ? 'var(--accent-primary)' : 'transparent', border: '1px solid var(--border-color)', color: 'white', fontSize: '0.8rem', borderRadius: '4px' }}
              >
                Padrão (IP)
              </button>
              <button
                onClick={() => setManualForm(f => ({ ...f, mode: 'advanced' }))}
                style={{ flex: 1, padding: '5px', background: manualForm.mode === 'advanced' ? 'var(--accent-primary)' : 'transparent', border: '1px solid var(--border-color)', color: 'white', fontSize: '0.8rem', borderRadius: '4px' }}
              >
                Avançado (URL)
              </button>
            </div>

            <form onSubmit={handleManualSubmit}>
              {manualForm.mode === 'simple' ? (
                <>
                  <div style={{ marginBottom: '1rem' }}>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.8rem' }}>IP da Câmera</label>
                    <input
                      className="input-field"
                      value={manualForm.ip}
                      onChange={e => setManualForm({ ...manualForm, ip: e.target.value })}
                      required={manualForm.mode === 'simple'}
                      placeholder="192.168.3.14"
                    />
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                    <div>
                      <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.8rem' }}>Usuário</label>
                      <input className="input-field" value={manualForm.user} onChange={e => setManualForm({ ...manualForm, user: e.target.value })} />
                    </div>
                    <div>
                      <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.8rem' }}>Senha</label>
                      <input type="password" className="input-field" value={manualForm.pass} onChange={e => setManualForm({ ...manualForm, pass: e.target.value })} />
                    </div>
                  </div>
                </>
              ) : (
                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.8rem' }}>URL RTSP Completa</label>
                  <textarea
                    className="input-field"
                    style={{ minHeight: '80px', fontFamily: 'monospace', fontSize: '0.75rem' }}
                    value={manualForm.customUrl}
                    onChange={e => setManualForm({ ...manualForm, customUrl: e.target.value })}
                    required={manualForm.mode === 'advanced'}
                    placeholder="rtsp://admin:123456@192.168.1.10:554/stream1"
                  />
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '5px' }}>
                    Use para câmeras com tokens especiais ou portas não-padrão.
                  </p>
                </div>
              )}

              <div style={{ display: 'flex', gap: '1rem' }}>
                <button type="button" onClick={() => setShowManualModal(false)} style={{ flex: 1, padding: '0.75rem', background: 'transparent', border: '1px solid var(--border-color)', color: 'var(--text-secondary)', borderRadius: '8px', cursor: 'pointer' }}>Cancelar</button>
                <button type="submit" disabled={isAuthenticating} className="btn-primary" style={{ flex: 1 }}>
                  {isAuthenticating ? 'Testando...' : 'Adicionar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Auth Modal */}
      {showAuthModal && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 100,
          background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(5px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <div className="glass-panel" style={{ padding: '2rem', width: '400px', borderRadius: '12px' }}>
            <h3 style={{ marginBottom: '1.5rem' }}>Autenticação da Câmera</h3>
            <p style={{ marginBottom: '1rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
              Para acessar {selectedCamera?.ip}, insira as credenciais RTSP.
            </p>
            <form onSubmit={handleAuthSubmit}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.8rem' }}>Usuário</label>
                <input
                  className="input-field"
                  value={authForm.user}
                  onChange={e => setAuthForm({ ...authForm, user: e.target.value })}
                  required
                />
              </div>
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.8rem' }}>Senha</label>
                <input
                  type="password"
                  className="input-field"
                  value={authForm.pass}
                  onChange={e => setAuthForm({ ...authForm, pass: e.target.value })}
                  required
                />
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button type="button" onClick={() => setShowAuthModal(false)} style={{ flex: 1, padding: '0.75rem', background: 'transparent', border: '1px solid var(--border-color)', color: 'var(--text-secondary)', borderRadius: '8px', cursor: 'pointer' }}>Cancelar</button>
                <button type="submit" disabled={isAuthenticating} className="btn-primary" style={{ flex: 1 }}>
                  {isAuthenticating ? 'Testando...' : 'Conectar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Sidebar */}
      <aside className="glass-panel" style={{ width: '300px', display: 'flex', flexDirection: 'column', zIndex: 10 }}>
        <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)' }}>
          <h1 style={{ fontSize: '1.2rem', fontWeight: 700, letterSpacing: '1px' }}>
            OMNI<span style={{ color: 'var(--accent-primary)' }}>VIEW</span>
          </h1>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Monitoramento Residencial
          </p>
        </div>

        <div style={{ padding: '1.5rem', flex: 1 }}>
          <h2 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '1rem', letterSpacing: '0.05em' }}>
            Dispositivos
          </h2>

          {/* Botões de Ação */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1.5rem' }}>
            <button
              className="btn-primary"
              onClick={() => setShowManualModal(true)}
              style={{ fontSize: '0.8rem', background: 'var(--bg-surface)', border: '1px solid var(--accent-primary)' }}
            >
              + Adicionar Manualmente
            </button>

            <button
              onClick={handleArpScan}
              style={{ padding: '0.5rem', background: 'transparent', border: '1px dashed var(--text-muted)', color: 'var(--text-secondary)', fontSize: '0.75rem', cursor: 'pointer', borderRadius: '4px' }}
            >
              📋 Listar Todos (ARP)
            </button>

            <button
              onClick={handleScan}
              disabled={isScanning}
              style={{ padding: '0.5rem', background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '0.75rem', cursor: 'pointer', textDecoration: 'underline' }}
            >
              {isScanning ? 'Procurando...' : 'Tentar Scan Automático'}
            </button>
          </div>

          <ul style={{ listStyle: 'none' }}>
            {cameras.length === 0 && !isScanning && (
              <li style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '2rem' }}>
                Nenhuma câmera detectada.<br />Clique em escanear.
              </li>
            )}

            {cameras.map((cam, idx) => (
              <li key={idx}
                onClick={() => handleCameraClick(cam)}
                style={{
                  padding: '0.8rem',
                  background: 'rgba(255,255,255,0.03)',
                  marginBottom: '0.5rem',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  borderLeft: `3px solid ${cam.status === 'online' ? 'var(--accent-success)' : 'var(--accent-danger)'}`,
                  transition: 'background 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.08)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '140px' }}>{cam.name}</span>
                  {cam.status === 'online' && <span className="status-live"></span>}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {cam.ip} • {cam.status === 'auth_required' ? '🔑 Configurar' : 'Online'}
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div style={{ padding: '1rem', borderTop: '1px solid var(--border-color)', fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center' }}>
          Servidor: <span style={{ color: 'var(--accent-success)' }}>Online (Porta 3001)</span>
        </div>
      </aside>

      {/* Main Grid */}
      <main style={{ flex: 1, padding: '2rem', overflowY: 'auto' }}>
        <h2 style={{ marginBottom: '1.5rem', fontSize: '1.5rem', fontWeight: 300 }}>
          Visualização em <b style={{ fontWeight: 700 }}>Tempo Real</b>
        </h2>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
          gap: '1.5rem'
        }}>
          {cameras.map(cam => (
            <div
              key={cam.id}
              onClick={() => handleCameraClick(cam)}
              className="glass-panel"
              style={{
                aspectRatio: '16/9',
                borderRadius: '12px',
                overflow: 'hidden',
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: '#000',
                cursor: 'pointer',
                transition: 'transform 0.2s, border-color 0.2s',
                border: cam.status === 'online' ? '1px solid var(--accent-success)' : '1px solid var(--border-color)'
              }}
              onMouseEnter={e => {
                e.currentTarget.style.transform = 'scale(1.02)';
                e.currentTarget.style.borderColor = 'var(--accent-primary)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.transform = 'scale(1)';
                e.currentTarget.style.borderColor = cam.status === 'online' ? 'var(--accent-success)' : 'var(--border-color)';
              }}
            >
              {cam.status === 'online' ? (
                <>
                  <img
                    src={`http://localhost:3001/api/stream/live?url=${encodeURIComponent(cam.rtspUrl || '')}`}
                    alt={cam.name}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'fill',
                      display: 'block'
                    }}
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                      e.currentTarget.parentElement!.style.background = '#220000';
                    }}
                  />
                  <button
                    style={{ position: 'absolute', bottom: 10, right: 10, zIndex: 100, padding: '5px 10px', cursor: 'pointer' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      window.open(`http://localhost:3001/api/stream/snapshot?url=${encodeURIComponent(cam.rtspUrl || '')}`, '_blank');
                    }}
                  >
                    📸 Snapshot
                  </button>
                </>
              ) : (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                  <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>
                    {cam.status === 'auth_required' ? '🔒' : '📡'}
                  </div>
                  {cam.status === 'auth_required' ? 'Autenticação Necessária' : 'Sinal Perdido'}
                </div>
              )}

              {/* Overlay Info */}
              <div style={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                padding: '1rem',
                background: 'linear-gradient(to top, rgba(0,0,0,0.8), transparent)',
                display: 'flex',
                justifyContent: 'space-between'
              }}>
                <span style={{ fontWeight: 600 }}>{cam.name}</span>
                <span style={{ fontFamily: 'monospace', opacity: 0.7 }}>{new Date().toLocaleTimeString()}</span>
              </div>
            </div>
          ))}
        </div>
      </main >
    </div >
  )
}

export default App
