/**
 * KaiOrb — WebView wrapper that renders the Kai orb UI from the server.
 */

import React from 'react'
import { StyleSheet, View, ActivityIndicator, Text } from 'react-native'
import { WebView } from 'react-native-webview'

interface KaiOrbProps {
  serverUrl: string
  onError?: (error: string) => void
}

interface KaiOrbState {
  loading: boolean
  error: boolean
}

export class KaiOrb extends React.Component<KaiOrbProps, KaiOrbState> {
  state: KaiOrbState = { loading: true, error: false }

  render() {
    const { serverUrl } = this.props
    const { loading, error } = this.state
    const orbUrl = `${serverUrl}/ui`

    return (
      <View style={styles.container}>
        {error ? (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>Cannot connect to Kai</Text>
            <Text style={styles.errorSub}>{orbUrl}</Text>
          </View>
        ) : (
          <WebView
            source={{ uri: orbUrl }}
            style={styles.webview}
            backgroundColor="transparent"
            scrollEnabled={false}
            bounces={false}
            onLoadStart={() => this.setState({ loading: true })}
            onLoadEnd={() => this.setState({ loading: false })}
            onError={() => {
              this.setState({ error: true, loading: false })
              this.props.onError?.('Failed to load orb UI')
            }}
          />
        )}
        {loading && (
          <View style={styles.loadingOverlay}>
            <ActivityIndicator size="large" color="#78b4e6" />
          </View>
        )}
      </View>
    )
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0e1a',
  },
  webview: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0a0e1a',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    color: '#e06060',
    fontSize: 18,
    fontWeight: '500',
  },
  errorSub: {
    color: '#666',
    fontSize: 14,
    marginTop: 8,
  },
})
