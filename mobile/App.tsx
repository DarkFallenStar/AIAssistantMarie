import React, { useState } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import AssistantScreen from './src/screens/AssistantScreen';
import ConnectionDiagnosticScreen from './src/screens/ConnectionDiagnosticScreen';
import NotificationAutomationScreen from './src/screens/NotificationAutomationScreen';
import DatabaseManagerScreen from './src/screens/DatabaseManagerScreen';
import { DEFAULT_BACKEND_URL } from './src/config';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<'assistant' | 'database_manager' | 'diagnostics' | 'automation'>('assistant');
  const [backendUrl, setBackendUrl] = useState<string>(DEFAULT_BACKEND_URL);

  return (
    <SafeAreaProvider>
      {currentScreen === 'diagnostics' && (
        <ConnectionDiagnosticScreen
          initialUrl={backendUrl}
          onUrlChange={setBackendUrl}
          onBackToAssistant={() => setCurrentScreen('assistant')}
        />
      )}
      {currentScreen === 'automation' && (
        <NotificationAutomationScreen
          backendUrl={backendUrl}
          onBackToAssistant={() => setCurrentScreen('assistant')}
          onOpenDiagnostics={() => setCurrentScreen('diagnostics')}
        />
      )}
      {currentScreen === 'database_manager' && (
        <DatabaseManagerScreen
          backendUrl={backendUrl}
          onBackToAssistant={() => setCurrentScreen('assistant')}
          onOpenDiagnostics={() => setCurrentScreen('diagnostics')}
        />
      )}
      {currentScreen === 'assistant' && (
        <AssistantScreen
          backendUrl={backendUrl}
          onOpenDiagnostics={() => setCurrentScreen('diagnostics')}
          onOpenAutomation={() => setCurrentScreen('automation')}
          onOpenDatabase={() => setCurrentScreen('database_manager')}
        />
      )}
    </SafeAreaProvider>
  );
}
