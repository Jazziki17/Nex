/**
 * SettingsScreen — Server IP config and connection management.
 */

import React, { useState, useEffect } from 'react'
import {
  StyleSheet,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Alert,
  ScrollView,
} from 'react-native'
import { KaiClient } from '../services/KaiClient'
import { Discovery, DiscoveredServer } from '../services/Discovery'

interface SettingsScreenProps {
  client: KaiClient
  discovery: Discovery
  onConnect: (host: string, port: number) => void
}

export function SettingsScreen({ client, discovery, onConnect }: SettingsScreenProps) {
  const [host, setHost] = useState('192.168.1.')
  const [port, setPort] = useState('8420')
  const [testing, setTesting] = useState(false)
  const [servers, setServers] = useState<DiscoveredServer[]>([])

  useEffect(() => {
    const unsubscribe = discovery.onChange(setServers)
    discovery.startScan()
    return () => {
      unsubscribe()
    }
  }, [discovery])

  const testConnection = async () => {
    setTesting(true)
    try {
      const found = await discovery.probeHost(host, parseInt(port, 10))
      if (found) {
        Alert.alert('Connected', `Kai server found at ${host}:${port}`)
        onConnect(host, parseInt(port, 10))
      } else {
        Alert.alert('Not Found', `No Kai server at ${host}:${port}`)
      }
    } catch {
      Alert.alert('Error', 'Could not reach server')
    } finally {
      setTesting(false)
    }
  }

  const connectToServer = (server: DiscoveredServer) => {
    setHost(server.host)
    setPort(String(server.port))
    onConnect(server.host, server.port)
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Server Connection</Text>

      {/* Manual IP entry */}
      <View style={styles.section}>
        <Text style={styles.label}>Server IP</Text>
        <TextInput
          style={styles.input}
          value={host}
          onChangeText={setHost}
          placeholder="192.168.1.100"
          placeholderTextColor="#556"
          keyboardType="numbers-and-punctuation"
          autoCorrect={false}
        />

        <Text style={styles.label}>Port</Text>
        <TextInput
          style={styles.input}
          value={port}
          onChangeText={setPort}
          placeholder="8420"
          placeholderTextColor="#556"
          keyboardType="number-pad"
        />

        <TouchableOpacity
          style={[styles.button, testing && styles.buttonDisabled]}
          onPress={testConnection}
          disabled={testing}
        >
          <Text style={styles.buttonText}>
            {testing ? 'Testing...' : 'Test Connection'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Discovered servers */}
      {servers.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Discovered Servers</Text>
          {servers.map((server) => (
            <TouchableOpacity
              key={server.host}
              style={styles.serverItem}
              onPress={() => connectToServer(server)}
            >
              <Text style={styles.serverName}>{server.name}</Text>
              <Text style={styles.serverAddress}>
                {server.host}:{server.port}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0e1a',
  },
  content: {
    padding: 24,
    paddingTop: 72,
  },
  title: {
    color: '#d0e0f0',
    fontSize: 24,
    fontWeight: '600',
    marginBottom: 32,
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    color: '#8899aa',
    fontSize: 14,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 16,
  },
  label: {
    color: '#8899aa',
    fontSize: 14,
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#141822',
    color: '#d0e0f0',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    marginBottom: 16,
  },
  button: {
    backgroundColor: '#2a4060',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  buttonText: {
    color: '#78b4e6',
    fontSize: 16,
    fontWeight: '600',
  },
  serverItem: {
    backgroundColor: '#141822',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
  },
  serverName: {
    color: '#d0e0f0',
    fontSize: 16,
    fontWeight: '500',
  },
  serverAddress: {
    color: '#556677',
    fontSize: 14,
    marginTop: 4,
  },
})
