/**
 * FilesScreen — Remote file browser connected to Nex server.
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  StyleSheet,
  View,
  Text,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native'
import { NexClient, FileEntry } from '../services/NexClient'

interface FilesScreenProps {
  client: NexClient
}

export function FilesScreen({ client }: FilesScreenProps) {
  const [currentPath, setCurrentPath] = useState('~')
  const [entries, setEntries] = useState<FileEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadDirectory = useCallback(async (path: string) => {
    setLoading(true)
    setError(null)
    try {
      const files = await client.listFiles(path)
      setEntries(files)
      setCurrentPath(path)
    } catch (e) {
      setError('Failed to load directory')
    } finally {
      setLoading(false)
    }
  }, [client])

  useEffect(() => {
    loadDirectory(currentPath)
  }, [])

  const navigateUp = () => {
    const parent = currentPath.replace(/\/[^/]+$/, '') || '/'
    loadDirectory(parent)
  }

  const onEntryPress = (entry: FileEntry) => {
    if (entry.is_dir) {
      loadDirectory(entry.path)
    } else {
      // Show file content
      client.readFile(entry.path).then((content) => {
        Alert.alert(entry.name, content.substring(0, 500))
      }).catch(() => {
        Alert.alert('Error', 'Cannot read this file')
      })
    }
  }

  const formatSize = (size: number | null) => {
    if (size === null) return ''
    if (size < 1024) return `${size} B`
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
    return `${(size / (1024 * 1024)).toFixed(1)} MB`
  }

  const renderEntry = ({ item }: { item: FileEntry }) => (
    <TouchableOpacity style={styles.entry} onPress={() => onEntryPress(item)}>
      <Text style={styles.icon}>{item.is_dir ? '📁' : '📄'}</Text>
      <View style={styles.entryInfo}>
        <Text style={styles.entryName} numberOfLines={1}>{item.name}</Text>
        <Text style={styles.entryMeta}>{formatSize(item.size)}</Text>
      </View>
    </TouchableOpacity>
  )

  return (
    <View style={styles.container}>
      {/* Path bar */}
      <View style={styles.pathBar}>
        <TouchableOpacity onPress={navigateUp} style={styles.upButton}>
          <Text style={styles.upText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.pathText} numberOfLines={1}>{currentPath}</Text>
      </View>

      {/* File list */}
      {loading ? (
        <ActivityIndicator size="large" color="#78b4e6" style={styles.loader} />
      ) : error ? (
        <Text style={styles.error}>{error}</Text>
      ) : (
        <FlatList
          data={entries}
          renderItem={renderEntry}
          keyExtractor={(item) => item.path}
          contentContainerStyle={styles.list}
        />
      )}
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0e1a',
  },
  pathBar: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    paddingTop: 60,
    borderBottomWidth: 1,
    borderBottomColor: '#1a1e2a',
  },
  upButton: {
    padding: 8,
    marginRight: 12,
  },
  upText: {
    color: '#78b4e6',
    fontSize: 20,
  },
  pathText: {
    color: '#8899aa',
    fontSize: 14,
    flex: 1,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  list: {
    padding: 8,
  },
  entry: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#141822',
  },
  icon: {
    fontSize: 20,
    marginRight: 14,
  },
  entryInfo: {
    flex: 1,
  },
  entryName: {
    color: '#d0e0f0',
    fontSize: 16,
  },
  entryMeta: {
    color: '#556677',
    fontSize: 12,
    marginTop: 2,
  },
  loader: {
    marginTop: 40,
  },
  error: {
    color: '#e06060',
    textAlign: 'center',
    marginTop: 40,
    fontSize: 16,
  },
})
