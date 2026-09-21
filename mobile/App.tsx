import React, { useState } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import AssistantScreen from './src/screens/AssistantScreen';
import ConnectionDiagnosticScreen from './src/screens/ConnectionDiagnosticScreen';
import { DEFAULT_BACKEND_URL } from './src/config';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<'assistant' | 'diagnostics'>('assistant');
  const [backendUrl, setBackendUrl] = useState<string>(DEFAULT_BACKEND_URL);

  return (
    <SafeAreaProvider>
      {currentScreen === 'diagnostics' ? (
        <ConnectionDiagnosticScreen
          initialUrl={backendUrl}
          onUrlChange={setBackendUrl}
          onBackToAssistant={() => setCurrentScreen('assistant')}
        />
      ) : (
        <AssistantScreen
          backendUrl={backendUrl}
          onOpenDiagnostics={() => setCurrentScreen('diagnostics')}
        />
      )}
    </SafeAreaProvider>
  );
}
