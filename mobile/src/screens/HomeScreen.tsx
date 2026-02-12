/**
 * HomeScreen — Main screen with the Nex orb and command input.
 */

import React, { useState, useEffect, useRef } from 'react'
import {
  StyleSheet,
  View,
  TextInput,
  TouchableOpacity,
  Text,
  KeyboardAvoidingView,
  Platform,
} from 'react-native'
import { NexOrb } from '../components/NexOrb'
import { NexClient } from '../services/NexClient'

interface HomeScreenProps {
  client: NexClient
  serverUrl: string
}

export function HomeScreen({ client, serverUrl }: HomeScreenProps) {
  const [command, setCommand] = useState('')
  const [status, setStatus] = useState('Connecting...')
  const [response, setResponse] = useState('')
  const inputRef = useRef<TextInput>(null)

  useEffect(() => {
    client.connectWs()

    const unsubscribe = client.onEvent((event) => {
      if (event.type === 'connected') {
        setStatus('Connected')
      } else if (event.type === 'speech.respond') {
        setResponse(String(event.data.text || ''))
      }
    })

    // Initial status check
    client.getStatus().then((s) => {
      setStatus(s.status === 'online' ? 'Online' : s.status)
    }).catch(() => {
      setStatus('Offline')
    })

    return () => {
      unsubscribe()
      client.disconnectWs()
    }
  }, [client])

  const sendCommand = () => {
    if (!command.trim()) return
    client.sendCommand(command.trim())
    setResponse('')
    setCommand('')
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      {/* Status bar */}
      <View style={styles.statusBar}>
        <View style={[styles.dot, status === 'Online' && styles.dotOnline]} />
        <Text style={styles.statusText}>{status}</Text>
      </View>

      {/* Orb */}
      <View style={styles.orbContainer}>
        <NexOrb serverUrl={serverUrl} />
      </View>

      {/* Response text */}
      {response ? (
        <View style={styles.responseContainer}>
          <Text style={styles.responseText}>{response}</Text>
        </View>
      ) : null}

      {/* Command input */}
      <View style={styles.inputContainer}>
        <TextInput
          ref={inputRef}
          style={styles.input}
          value={command}
          onChangeText={setCommand}
          placeholder="Type a command..."
          placeholderTextColor="#556"
          returnKeyType="send"
          onSubmitEditing={sendCommand}
          autoCorrect={false}
          autoCapitalize="none"
        />
        <TouchableOpacity style={styles.sendButton} onPress={sendCommand}>
          <Text style={styles.sendText}>Send</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0e1a',
  },
  statusBar: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    paddingTop: 60,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#666',
    marginRight: 8,
  },
  dotOnline: {
    backgroundColor: '#4ae04a',
  },
  statusText: {
    color: '#8899aa',
    fontSize: 14,
  },
  orbContainer: {
    flex: 1,
  },
  responseContainer: {
    paddingHorizontal: 24,
    paddingBottom: 12,
  },
  responseText: {
    color: '#b0c8e0',
    fontSize: 16,
    textAlign: 'center',
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 16,
    paddingBottom: 36,
    borderTopWidth: 1,
    borderTopColor: '#1a1e2a',
  },
  input: {
    flex: 1,
    backgroundColor: '#141822',
    color: '#d0e0f0',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    marginRight: 12,
  },
  sendButton: {
    backgroundColor: '#2a4060',
    borderRadius: 12,
    paddingHorizontal: 20,
    justifyContent: 'center',
  },
  sendText: {
    color: '#78b4e6',
    fontSize: 16,
    fontWeight: '600',
  },
})
