/**
 * NexClient — HTTP + WebSocket client for communicating with the Nex server.
 */

export interface NexStatus {
  status: string
  modules: Record<string, { status: string }>
  uptime: number
  event_history_count: number
}

export interface FileEntry {
  name: string
  path: string
  is_dir: boolean
  size: number | null
  modified: number
}

export interface NexEvent {
  type: string
  data: Record<string, unknown>
}

type EventCallback = (event: NexEvent) => void

export class NexClient {
  private baseUrl: string
  private wsUrl: string
  private ws: WebSocket | null = null
  private listeners: EventCallback[] = []
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null

  constructor(host: string = 'localhost', port: number = 8420) {
    this.baseUrl = `http://${host}:${port}`
    this.wsUrl = `ws://${host}:${port}/ws`
  }

  updateHost(host: string, port: number = 8420): void {
    this.baseUrl = `http://${host}:${port}`
    this.wsUrl = `ws://${host}:${port}/ws`
    this.disconnectWs()
    this.connectWs()
  }

  // ─── REST API ─────────────────────────────────────

  async getStatus(): Promise<NexStatus> {
    const res = await fetch(`${this.baseUrl}/api/status`)
    return res.json()
  }

  async listFiles(path: string = '~', pattern: string = '*'): Promise<FileEntry[]> {
    const res = await fetch(`${this.baseUrl}/api/files/list`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, pattern }),
    })
    const data = await res.json()
    return data.entries
  }

  async readFile(path: string): Promise<string> {
    const res = await fetch(`${this.baseUrl}/api/files/read`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path }),
    })
    const data = await res.json()
    return data.content
  }

  async writeFile(path: string, content: string): Promise<void> {
    await fetch(`${this.baseUrl}/api/files/write`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, content }),
    })
  }

  async runCommand(command: string): Promise<{ stdout: string; stderr: string; exit_code: number }> {
    const res = await fetch(`${this.baseUrl}/api/commands/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command }),
    })
    return res.json()
  }

  // ─── WebSocket ────────────────────────────────────

  connectWs(): void {
    if (this.ws) return

    this.ws = new WebSocket(this.wsUrl)

    this.ws.onopen = () => {
      console.log('[NexClient] WebSocket connected')
    }

    this.ws.onmessage = (event) => {
      try {
        const parsed: NexEvent = JSON.parse(event.data)
        this.listeners.forEach((cb) => cb(parsed))
      } catch {
        // ignore parse errors
      }
    }

    this.ws.onclose = () => {
      console.log('[NexClient] WebSocket disconnected')
      this.ws = null
      // Auto-reconnect after 3 seconds
      this.reconnectTimer = setTimeout(() => this.connectWs(), 3000)
    }

    this.ws.onerror = () => {
      this.ws?.close()
    }
  }

  disconnectWs(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  onEvent(callback: EventCallback): () => void {
    this.listeners.push(callback)
    return () => {
      this.listeners = this.listeners.filter((cb) => cb !== callback)
    }
  }

  sendCommand(command: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'command', command }))
    }
  }
}
