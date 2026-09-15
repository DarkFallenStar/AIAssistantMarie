import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { BorderRadius, Shadow } from '../theme/spacing';

export type TabName = 'dashboard' | 'chat' | 'voice' | 'goals';

interface BottomNavProps {
  activeTab: TabName;
  onTabPress: (tab: TabName) => void;
}

interface TabItem {
  key: TabName;
  label: string;
  icon: string;
  isCentral?: boolean;
}

const TABS: TabItem[] = [
  { key: 'dashboard', label: 'Inicio', icon: '⊞' },
  { key: 'chat', label: 'Copiloto', icon: '💬' },
  { key: 'voice', label: 'Voz IA', icon: '🎙️', isCentral: true },
  { key: 'goals', label: 'Metas', icon: '🎯' },
];

export function BottomNav({ activeTab, onTabPress }: BottomNavProps) {
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.wrapper, { paddingBottom: insets.bottom + 8 }]}>
      <View style={styles.pill}>
        {TABS.map((tab) => {
          const isActive = activeTab === tab.key;

          if (tab.isCentral) {
            return (
              <TouchableOpacity
                key={tab.key}
                onPress={() => onTabPress(tab.key)}
                style={styles.centralWrapper}
                activeOpacity={0.85}
              >
                <View style={styles.centralButton}>
                  <Text style={styles.centralIcon}>{tab.icon}</Text>
                </View>
                <Text style={[styles.label, styles.centralLabel]}>{tab.label}</Text>
              </TouchableOpacity>
            );
          }

          return (
            <TouchableOpacity
              key={tab.key}
              onPress={() => onTabPress(tab.key)}
              style={styles.tab}
              activeOpacity={0.7}
            >
              <Text style={[styles.icon, isActive && styles.iconActive]}>{tab.icon}</Text>
              <Text style={[styles.label, isActive && styles.labelActive]}>{tab.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingHorizontal: 16,
    zIndex: 100,
  },
  pill: {
    height: 64,
    backgroundColor: Colors.surfaceContainer,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    borderColor: Colors.border,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    paddingHorizontal: 8,
    ...Shadow.lg,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    height: 48,
  },
  icon: {
    fontSize: 20,
    color: Colors.onSurfaceVariant,
    opacity: 0.6,
  },
  iconActive: {
    color: Colors.primary,
    opacity: 1,
  },
  label: {
    ...Typography.labelSm,
    color: Colors.onSurfaceVariant,
    marginTop: 2,
    fontSize: 11,
  },
  labelActive: {
    color: Colors.primary,
    fontFamily: 'PlusJakartaSans_700Bold',
  },
  centralWrapper: {
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: -20,
  },
  centralButton: {
    width: 52,
    height: 52,
    borderRadius: BorderRadius.full,
    backgroundColor: Colors.primaryContainer,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: Colors.background,
    shadowColor: Colors.primaryContainer,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.5,
    shadowRadius: 12,
    elevation: 8,
  },
  centralIcon: {
    fontSize: 22,
  },
  centralLabel: {
    marginTop: 4,
    color: Colors.primary,
    fontFamily: 'PlusJakartaSans_700Bold',
  },
});
