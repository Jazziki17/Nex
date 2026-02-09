/**
 * Kai Desktop — Electron Main Process
 * =====================================
 * Orchestrates Python server, native window, and tray icon.
 */

import { app } from 'electron'
import { createWindow, getWindow } from './window'
import { createTray } from './tray'
import { PythonBridge } from './python-bridge'

let pythonBridge: PythonBridge | null = null

app.whenReady().then(async () => {
  // Start the Python API server
  pythonBridge = new PythonBridge()
  await pythonBridge.start()

  // Create the floating orb window
  createWindow()

  // Create the tray icon
  createTray(pythonBridge)
})

app.on('window-all-closed', () => {
  // On macOS, keep running in tray
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  // Re-show window when dock icon clicked (macOS)
  const win = getWindow()
  if (win) {
    win.show()
  } else {
    createWindow()
  }
})

app.on('before-quit', async () => {
  if (pythonBridge) {
    await pythonBridge.stop()
  }
})
