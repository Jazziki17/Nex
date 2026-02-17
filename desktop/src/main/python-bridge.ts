/**
 * Python Bridge — Spawns and monitors the Nex API server.
 * Handles health checks, auto-restart, and graceful shutdown.
 * Works in both dev mode (npm run dev) and packaged mode (.app).
 */

import { ChildProcess, spawn, execSync } from 'child_process'
import { join } from 'path'
import { existsSync } from 'fs'
import { app } from 'electron'
import http from 'http'

const PORT = 8420
const HEALTH_URL = `http://localhost:${PORT}/api/status`
const HEALTH_INTERVAL = 5000
const MAX_RESTARTS = 5
const STARTUP_TIMEOUT = 30000

export class PythonBridge {
  private process: ChildProcess | null = null
  private healthTimer: NodeJS.Timeout | null = null
  private restartCount = 0
  private stopping = false
  private externalServer = false
  private _serverReachable = false

  async start(): Promise<void> {
    this.stopping = false

    // Check if server is already running (started externally)
    const alreadyUp = await this.healthCheck()
    if (alreadyUp) {
      console.log('[PythonBridge] Server already running — attaching to existing instance')
      this.externalServer = true
      this._serverReachable = true
      this.startHealthCheck()
      return
    }

    this.spawn()
    await this.waitForReady()
    this._serverReachable = true
    this.startHealthCheck()
  }

  async stop(): Promise<void> {
    this.stopping = true
    this._serverReachable = false
    this.stopHealthCheck()

    if (this.externalServer) {
      this.externalServer = false
      return
    }

    if (this.process) {
      this.process.kill('SIGTERM')

      await new Promise<void>((resolve) => {
        const timeout = setTimeout(() => {
          if (this.process) {
            this.process.kill('SIGKILL')
          }
          resolve()
        }, 5000)

        if (this.process) {
          this.process.on('exit', () => {
            clearTimeout(timeout)
            resolve()
          })
        } else {
          clearTimeout(timeout)
          resolve()
        }
      })

      this.process = null
    }
  }

  async restart(): Promise<void> {
    await this.stop()
    this.stopping = false
    this.restartCount = 0
    await this.start()
  }

  get isRunning(): boolean {
    return this._serverReachable
  }

  private getProjectRoot(): string {
    if (app.isPackaged) {
      // Packaged .app — project lives at ~/Nex
      const homeProject = join(process.env.HOME || '/Users/jazz', 'Nex')
      if (existsSync(join(homeProject, 'nex', '__init__.py'))) {
        return homeProject
      }
      // Fallback: check if .app is still inside the project tree
      const fromExe = join(app.getPath('exe'), '..', '..', '..', '..', '..', '..')
      if (existsSync(join(fromExe, 'nex', '__init__.py'))) {
        return fromExe
      }
      return homeProject
    }

    // Dev mode — desktop/ is inside the project
    return join(__dirname, '..', '..', '..')
  }

  private findPython(): string {
    // Try common locations for python3 with our deps
    const candidates = [
      join(process.env.HOME || '', 'anaconda3', 'bin', 'python3'),
      '/usr/local/bin/python3',
      '/opt/homebrew/bin/python3',
      'python3',
    ]

    for (const p of candidates) {
      try {
        execSync(`${p} -c "import fastapi"`, { stdio: 'pipe' })
        return p
      } catch {
        continue
      }
    }

    return 'python3'
  }

  private spawn(): void {
    const projectRoot = this.getProjectRoot()
    const python = this.findPython()

    console.log(`[PythonBridge] Starting ${python} -m nex.api in ${projectRoot}`)

    this.process = spawn(python, ['-m', 'nex.api'], {
      cwd: projectRoot,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: {
        ...process.env,
        PYTHONPATH: projectRoot,
        PYTHONUNBUFFERED: '1',
      },
    })

    this.process.stdout?.on('data', (data: Buffer) => {
      console.log(`[Nex] ${data.toString().trim()}`)
    })

    this.process.stderr?.on('data', (data: Buffer) => {
      console.error(`[Nex:err] ${data.toString().trim()}`)
    })

    this.process.on('exit', (code) => {
      console.log(`[PythonBridge] Process exited with code ${code}`)
      this.process = null
      this._serverReachable = false

      if (!this.stopping && this.restartCount < MAX_RESTARTS) {
        this.restartCount++
        console.log(`[PythonBridge] Auto-restarting (${this.restartCount}/${MAX_RESTARTS})...`)
        setTimeout(() => this.spawn(), 2000)
      }
    })
  }

  private waitForReady(): Promise<void> {
    return new Promise((resolve, reject) => {
      const startTime = Date.now()

      const check = () => {
        if (Date.now() - startTime > STARTUP_TIMEOUT) {
          reject(new Error('Python server failed to start within timeout'))
          return
        }

        this.healthCheck()
          .then((ok) => {
            if (ok) {
              console.log('[PythonBridge] Server is ready')
              resolve()
            } else {
              setTimeout(check, 500)
            }
          })
          .catch(() => setTimeout(check, 500))
      }

      setTimeout(check, 1000)
    })
  }

  private healthCheck(): Promise<boolean> {
    return new Promise((resolve) => {
      http
        .get(HEALTH_URL, (res) => {
          resolve(res.statusCode === 200)
        })
        .on('error', () => {
          resolve(false)
        })
    })
  }

  private startHealthCheck(): void {
    this.healthTimer = setInterval(async () => {
      const ok = await this.healthCheck()
      this._serverReachable = ok
      if (!ok && !this.stopping) {
        console.warn('[PythonBridge] Health check failed, server may be down')
      }
    }, HEALTH_INTERVAL)
  }

  private stopHealthCheck(): void {
    if (this.healthTimer) {
      clearInterval(this.healthTimer)
      this.healthTimer = null
    }
  }
}
