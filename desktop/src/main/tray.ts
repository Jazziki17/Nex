/**
 * Tray — macOS menu bar icon with show/hide, status, restart, launch at login, quit.
 */

import { Tray, Menu, app, nativeImage } from 'electron'
import { toggleWindow } from './window'
import { PythonBridge } from './python-bridge'

let tray: Tray | null = null

export function createTray(pythonBridge: PythonBridge): void {
  // Create a simple tray icon (small circle)
  const icon = nativeImage.createFromDataURL(
    'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAACXBIWXMAAAsTAAALEwEAmpwYAAABHUlEQVQ4y62TvUoDQRSFv5lNNouFYGEhWNj4AG7hA/gA2lj5AG5hZWHhA2hjYWFhYWFhIYKFhYVgIcQf4u5mZ+baJCuyuwnBAxeGO3PO3Lkz8M9SVEV7qmt7qrOqHxp4p/pT9UP1QnVTdTUkbKreJsnW49t76rcJX6ke6YhZDL4n+FRnU8GBVHBf1aN0RVkhSJeBCq4kUoE1xwvHs3I6GyVYc5R9T3AzEawCG44n1rKE1cAFICpBJCpOAD2AlSI44WiPdxbYd7yA5cAz4KFE+Iw5XpXTYSJojnLGEVwrJoJ+Br43BU+Ad8CeI/gdBT/QOU08F51PUkcjoIPVQ/TjLSqb/p8BU8Cv6vuqh6ntgepV0ny67+FX+xfeKI5WL4/AAAAABJRU5ErkJggg=='
  )

  // Make it template for macOS dark/light mode
  icon.setTemplateImage(true)
  tray = new Tray(icon)
  tray.setToolTip('Kai AI Assistant')

  const isLoginItem = app.getLoginItemSettings().openAtLogin

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show/Hide Kai',
      click: () => toggleWindow(),
    },
    {
      type: 'separator',
    },
    {
      label: 'Status',
      sublabel: pythonBridge.isRunning ? 'Running' : 'Stopped',
      enabled: false,
    },
    {
      type: 'separator',
    },
    {
      label: 'Launch at Login',
      type: 'checkbox',
      checked: isLoginItem,
      click: (menuItem) => {
        app.setLoginItemSettings({
          openAtLogin: menuItem.checked,
          openAsHidden: true,
        })
      },
    },
    {
      type: 'separator',
    },
    {
      label: 'Restart Server',
      click: async () => {
        await pythonBridge.restart()
      },
    },
    {
      type: 'separator',
    },
    {
      label: 'Quit',
      click: () => {
        app.quit()
      },
    },
  ])

  tray.setContextMenu(contextMenu)

  // Click tray icon to toggle window
  tray.on('click', () => {
    toggleWindow()
  })
}
