/**
 * Window — Frameless transparent BrowserWindow for the floating orb.
 */

import { BrowserWindow, screen } from 'electron'
import { join } from 'path'

const PORT = 8420
let mainWindow: BrowserWindow | null = null

export function createWindow(): BrowserWindow {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize

  mainWindow = new BrowserWindow({
    width: 600,
    height: 600,
    x: Math.round(width / 2 - 300),
    y: Math.round(height / 2 - 300),
    frame: false,
    transparent: true,
    resizable: true,
    alwaysOnTop: false,
    hasShadow: false,
    skipTaskbar: false,
    backgroundColor: '#00000000',
    webPreferences: {
      preload: join(__dirname, '..', 'preload', 'index.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  // Load the orb UI from the Python server
  mainWindow.loadURL(`http://localhost:${PORT}/ui`)

  // Allow dragging from anywhere in the window
  mainWindow.setMovable(true)

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  return mainWindow
}

export function getWindow(): BrowserWindow | null {
  return mainWindow
}

export function toggleWindow(): void {
  if (!mainWindow) {
    createWindow()
    return
  }

  if (mainWindow.isVisible()) {
    mainWindow.hide()
  } else {
    mainWindow.show()
    mainWindow.focus()
  }
}
