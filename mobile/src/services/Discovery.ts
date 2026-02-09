/**
 * Discovery — Find Kai servers on the local network via mDNS/Bonjour.
 */

// Note: requires react-native-zeroconf to be installed and linked
// import Zeroconf from 'react-native-zeroconf'

export interface DiscoveredServer {
  name: string
  host: string
  port: number
  addresses: string[]
}

type DiscoveryCallback = (servers: DiscoveredServer[]) => void

export class Discovery {
  private servers: Map<string, DiscoveredServer> = new Map()
  private listeners: DiscoveryCallback[] = []
  private scanning = false

  /**
   * Start scanning for Kai servers on the local network.
   * Uses mDNS to discover services advertised as "_kai._tcp."
   *
   * Falls back to manual IP entry if zeroconf is not available.
   */
  async startScan(): Promise<void> {
    if (this.scanning) return
    this.scanning = true

    try {
      const Zeroconf = require('react-native-zeroconf').default
      const zeroconf = new Zeroconf()

      zeroconf.on('resolved', (service: any) => {
        const server: DiscoveredServer = {
          name: service.name || 'Kai Server',
          host: service.host,
          port: service.port || 8420,
          addresses: service.addresses || [],
        }
        this.servers.set(server.host, server)
        this.notify()
      })

      zeroconf.on('remove', (name: string) => {
        for (const [host, server] of this.servers) {
          if (server.name === name) {
            this.servers.delete(host)
            this.notify()
            break
          }
        }
      })

      zeroconf.scan('kai', 'tcp', 'local.')
    } catch {
      console.log('[Discovery] Zeroconf not available, use manual IP entry')
    }
  }

  stopScan(): void {
    this.scanning = false
    // Zeroconf stop would go here
  }

  /**
   * Manually probe an IP:port to check if a Kai server is running.
   */
  async probeHost(host: string, port: number = 8420): Promise<boolean> {
    try {
      const res = await fetch(`http://${host}:${port}/api/status`, {
        signal: AbortSignal.timeout(3000),
      })
      if (res.ok) {
        const data = await res.json()
        if (data.status) {
          this.servers.set(host, {
            name: 'Kai Server',
            host,
            port,
            addresses: [host],
          })
          this.notify()
          return true
        }
      }
    } catch {
      // Not reachable
    }
    return false
  }

  getServers(): DiscoveredServer[] {
    return Array.from(this.servers.values())
  }

  onChange(callback: DiscoveryCallback): () => void {
    this.listeners.push(callback)
    return () => {
      this.listeners = this.listeners.filter((cb) => cb !== callback)
    }
  }

  private notify(): void {
    const servers = this.getServers()
    this.listeners.forEach((cb) => cb(servers))
  }
}
