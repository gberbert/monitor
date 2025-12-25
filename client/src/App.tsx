import { useState } from 'react';
import { appVersion } from './version';
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

  // Mobile menu state
  const [menuOpen, setMenuOpen] = useState(false);

  const handleScan = async () => {
    setIsScanning(true);
    try {
      const response = await fetch('http://localhost:3001/api/scan');
      const data = await response.json();

      if (data.success) {
        setCameras(data.cameras.map((cam: any) => ({
          id: cam.id,
          ip: cam.ip,
          name: cam.name,
          status: 'online'
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

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsAuthenticating(true);

    try {
      const payload = manualForm.mode === 'simple'
        ? { ip: manualForm.ip, user: manualForm.user, pass: manualForm.pass }
        : { ip: 'custom', user: 'admin', pass: '', rtspUrl: manualForm.customUrl };

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
          rtspUrl: data.streamUrl
        };
        setCameras(prev => [...prev, newCam]);
        setShowManualModal(false);
        setManualForm({ ip: '', user: 'admin', pass: '', mode: 'simple', customUrl: '' });
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

  // === USER MANAGEMENT LOGIC ===
  const [showUserModal, setShowUserModal] = useState(false);
  const [userList, setUserList] = useState<any[]>([]);

  const openUserManagement = async () => {
    setShowUserModal(true);
    try {
      const res = await fetch('http://localhost:3001/api/users/all');
      if (res.ok) {
        setUserList(await res.json());
      }
    } catch (e) {
      alert("Erro ao carregar usuários.");
    }
  };

  const toggleUserStatus = async (username: string, currentStatus: boolean) => {
    try {
      await fetch('http://localhost:3001/api/users/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, approved: !currentStatus })
      });
      setUserList(prev => prev.map(u =>
        u.username === username ? { ...u, approved: !currentStatus } : u
      ));
    } catch (e) {
      alert("Erro ao atualizar.");
    }
  };

  const deleteUser = async (username: string) => {
    if (!confirm(`Tem certeza que deseja remover ${username}?`)) return;
    try {
      await fetch('http://localhost:3001/api/users/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username })
      });
      setUserList(prev => prev.filter(u => u.username !== username));
    } catch (e) {
      alert("Erro ao deletar.");
    }
  };

  return (
    <div className="app-container">

      {/* Mobile Header */}
      <header className="mobile-header">
        <div style={{ fontSize: '1.2rem', fontWeight: 700, letterSpacing: '1px' }}>
          OMNI<span style={{ color: 'var(--accent-primary)' }}>VIEW</span>
        </div>
        <button
          onClick={() => setMenuOpen(true)}
          style={{ background: 'transparent', border: 'none', color: 'white', fontSize: '1.5rem', cursor: 'pointer' }}
        >
          ☰
        </button>
      </header>

      {/* Mobile Overlay */}
      {menuOpen && (
        <div
          onClick={() => setMenuOpen(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 15 }}
        />
      )}

      {/* ARP Modal */}
      {showArpModal && (
        <div className="modal-overlay">
          <div className="modal-panel">
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
        <div className="modal-overlay">
          <div className="modal-panel">
            <h3 style={{ marginBottom: '1rem' }}>Adicionar Câmera</h3>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '1.5rem' }}>
              <button
                onClick={() => setManualForm(f => ({ ...f, mode: 'simple' }))}
                style={{ flex: 1, padding: '8px', background: manualForm.mode === 'simple' ? 'var(--accent-primary)' : 'transparent', border: '1px solid var(--border-color)', color: 'white', fontSize: '0.8rem', borderRadius: '4px' }}
              >
                Padrão (IP)
              </button>
              <button
                onClick={() => setManualForm(f => ({ ...f, mode: 'advanced' }))}
                style={{ flex: 1, padding: '8px', background: manualForm.mode === 'advanced' ? 'var(--accent-primary)' : 'transparent', border: '1px solid var(--border-color)', color: 'white', fontSize: '0.8rem', borderRadius: '4px' }}
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
        <div className="modal-overlay">
          <div className="modal-panel">
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

      {/* User Management Modal */}
      {showUserModal && (
        <div className="modal-overlay">
          <div className="modal-panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h3 style={{ margin: 0 }}>Gestão de Usuários</h3>
              <button onClick={() => setShowUserModal(false)} style={{ background: 'transparent', border: 'none', color: 'white', fontSize: '1.2rem', cursor: 'pointer' }}>×</button>
            </div>
            <div style={{ flex: 1, overflowY: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                    <th style={{ textAlign: 'left', padding: '0.5rem' }}>Usuário</th>
                    <th style={{ textAlign: 'center', padding: '0.5rem' }}>Admin</th>
                    <th style={{ textAlign: 'center', padding: '0.5rem' }}>Acesso</th>
                    <th style={{ textAlign: 'right', padding: '0.5rem' }}>Ação</th>
                  </tr>
                </thead>
                <tbody>
                  {userList.map(u => (
                    <tr key={u.username} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <td style={{ padding: '0.8rem 0.5rem' }}>{u.username}</td>
                      <td style={{ textAlign: 'center' }}>{u.is_admin ? '👑' : ''}</td>
                      <td style={{ textAlign: 'center' }}>
                        {!u.is_admin && (
                          <button
                            onClick={() => toggleUserStatus(u.username, u.approved)}
                            style={{
                              padding: '4px 8px',
                              borderRadius: '4px',
                              border: 'none',
                              background: u.approved ? 'var(--accent-success)' : 'var(--text-muted)',
                              color: 'black',
                              fontWeight: 'bold',
                              cursor: 'pointer'
                            }}
                          >
                            {u.approved ? 'ON' : 'OFF'}
                          </button>
                        )}
                        {u.is_admin && <span style={{ color: 'var(--accent-success)', fontSize: '0.8rem' }}>SEMPRE ON</span>}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        {!u.is_admin && (
                          <button onClick={() => deleteUser(u.username)} style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}>🗑️</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {userList.length === 0 && <p style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '1rem' }}>Nenhum usuário encontrado.</p>}
            </div>
          </div>
        </div>
      )}

      {/* Sidebar */}
      <aside className={`sidebar ${menuOpen ? 'open' : ''}`}>
        {menuOpen && (
          <button
            onClick={() => setMenuOpen(false)}
            style={{ position: 'absolute', top: '10px', right: '10px', background: 'transparent', border: 'none', color: 'white', fontSize: '1.5rem', cursor: 'pointer', zIndex: 50 }}
          >
            ×
          </button>
        )}
        <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)' }}>
          <h1 style={{ fontSize: '1.2rem', fontWeight: 700, letterSpacing: '1px' }}>
            OMNI<span style={{ color: 'var(--accent-primary)' }}>VIEW</span>
          </h1>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Monitoramento Residencial
          </p>
        </div>

        <div style={{ padding: '1.5rem', flex: 1, overflowY: 'auto' }}>
          <h2 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '1rem', letterSpacing: '0.05em' }}>
            Dispositivos
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1.5rem' }}>
            <button
              className="btn-primary"
              onClick={() => { setShowManualModal(true); setMenuOpen(false); }}
              style={{ fontSize: '0.8rem', background: 'var(--bg-surface)', border: '1px solid var(--accent-primary)' }}
            >
              + Adicionar Manualmente
            </button>
            <button
              onClick={() => { openUserManagement(); setMenuOpen(false); }}
              style={{ padding: '0.8rem', background: 'transparent', border: '1px solid var(--border-color)', color: 'var(--text-secondary)', fontSize: '0.75rem', cursor: 'pointer', borderRadius: '4px', textAlign: 'center' }}
            >
              👥 Gestão de Usuários
            </button>
            <button
              onClick={() => { handleArpScan(); setMenuOpen(false); }}
              style={{ padding: '0.8rem', background: 'transparent', border: '1px dashed var(--text-muted)', color: 'var(--text-secondary)', fontSize: '0.75rem', cursor: 'pointer', borderRadius: '4px' }}
            >
              📋 Listar Todos (ARP)
            </button>
            <button
              onClick={handleScan}
              disabled={isScanning}
              style={{ padding: '0.8rem', background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '0.75rem', cursor: 'pointer', textDecoration: 'underline' }}
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
                onClick={() => { handleCameraClick(cam); setMenuOpen(false); }}
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
          <div>Servidor: <span style={{ color: 'var(--accent-success)' }}>Online (Porta 3001)</span></div>
          <div style={{ marginTop: '0.3rem', opacity: 0.6 }}>v{appVersion}</div>
        </div>
      </aside>

      {/* Main Grid */}
      <main className="main-content">
        <h2 style={{ marginBottom: '1.5rem', fontSize: '1.5rem', fontWeight: 300 }}>
          Visualização em <b style={{ fontWeight: 700 }}>Tempo Real</b>
        </h2>
        <div className="camera-grid">
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
              <div style={{
                position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, pointerEvents: 'none',
                background: 'linear-gradient(to top, rgba(0,0,0,0.8) 0%, transparent 20%)',
              }} />
              <div style={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                padding: '1rem',
                display: 'flex',
                justifyContent: 'space-between',
                pointerEvents: 'none'
              }}>
                <span style={{ fontWeight: 600 }}>{cam.name}</span>
                <span style={{ fontFamily: 'monospace', opacity: 0.7 }}>{new Date().toLocaleTimeString()}</span>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}

export default App
