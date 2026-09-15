// Design system colors from "AI Student Finance Assistant" Stitch project
// Theme: Dark Modern Fintech Minimalist

export const Colors = {
  // Background & Core Surfaces
  background: '#0A0F1D',
  surface: '#0E1321',
  surfaceContainerLowest: '#090E1C',
  surfaceContainerLow: '#161B2A',
  surfaceContainer: '#0F172A',
  surfaceContainerHigh: '#161F36',
  surfaceContainerHighest: '#1E293B',
  surfaceDim: '#0E1321',
  surfaceBright: '#343948',
  surfaceVariant: '#161F36',

  // Primary - Vivid Mint & Emerald
  primary: '#4EDEA3',
  onPrimary: '#003824',
  primaryContainer: '#10B981',
  onPrimaryContainer: '#00422B',
  primaryFixed: '#6FFBBE',
  primaryFixedDim: '#4EDEA3',
  onPrimaryFixed: '#002113',
  onPrimaryFixedVariant: '#005236',
  inversePrimary: '#006C49',

  // Secondary - Electric Cyan & Slate
  secondary: '#7BD0FF',
  onSecondary: '#00354A',
  secondaryContainer: '#00A6E0',
  onSecondaryContainer: '#00374D',
  secondaryFixed: '#C4E7FF',
  secondaryFixedDim: '#7BD0FF',
  onSecondaryFixed: '#001E2C',
  onSecondaryFixedVariant: '#004C69',

  // Tertiary / Accent - Warm Amber & Coral
  tertiary: '#FFB2B7',
  onTertiary: '#67001B',
  tertiaryContainer: '#F59E0B',
  onTertiaryContainer: '#523200',
  tertiaryFixed: '#FFDADB',
  tertiaryFixedDim: '#FFB2B7',
  onTertiaryFixed: '#40000D',
  onTertiaryFixedVariant: '#92002A',

  // Error & Expense
  error: '#F87171',
  onError: '#690005',
  errorContainer: '#93000A',
  onErrorContainer: '#FFDAD6',

  // Typography & On-Colors
  onSurface: '#F8FAFC',
  onSurfaceVariant: '#94A3B8',
  onBackground: '#DEE2F6',
  inverseSurface: '#DEE2F6',
  inverseOnSurface: '#2B303F',

  // Borders & Outlines
  outline: '#86948A',
  outlineVariant: '#1E293B',
  border: '#1E293B',
  borderLight: '#334155',

  // Tint
  surfaceTint: '#4EDEA3',
};

export type ColorKey = keyof typeof Colors;
