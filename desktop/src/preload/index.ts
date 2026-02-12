/**
 * Preload — Exposes safe IPC methods to the renderer.
 */

import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('nex', {
  platform: process.platform,
  send: (channel: string, data: unknown) => {
    const validChannels = ['command', 'toggle-always-on-top']
    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, data)
    }
  },
  on: (channel: string, callback: (...args: unknown[]) => void) => {
    const validChannels = ['status-update', 'event']
    if (validChannels.includes(channel)) {
      ipcRenderer.on(channel, (_event, ...args) => callback(...args))
    }
  },
})
