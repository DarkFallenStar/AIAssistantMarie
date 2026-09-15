// Typography tokens from "AI Student Finance Assistant" Stitch project
// Font family: Plus Jakarta Sans

import { TextStyle } from 'react-native';

export const FontFamily = {
  regular: 'PlusJakartaSans_400Regular',
  semiBold: 'PlusJakartaSans_600SemiBold',
  bold: 'PlusJakartaSans_700Bold',
  extraBold: 'PlusJakartaSans_800ExtraBold',
};

export const Typography: Record<string, TextStyle> = {
  display: {
    fontFamily: FontFamily.extraBold,
    fontSize: 40,
    lineHeight: 48,
    letterSpacing: -0.03 * 40,
  },
  displayMobile: {
    fontFamily: FontFamily.extraBold,
    fontSize: 32,
    lineHeight: 38,
    letterSpacing: -0.02 * 32,
  },
  headlineLg: {
    fontFamily: FontFamily.bold,
    fontSize: 28,
    lineHeight: 36,
    letterSpacing: -0.02 * 28,
  },
  headlineMd: {
    fontFamily: FontFamily.bold,
    fontSize: 22,
    lineHeight: 28,
    letterSpacing: -0.01 * 22,
  },
  headlineSm: {
    fontFamily: FontFamily.semiBold,
    fontSize: 18,
    lineHeight: 24,
  },
  bodyLg: {
    fontFamily: FontFamily.regular,
    fontSize: 16,
    lineHeight: 24,
  },
  bodyMd: {
    fontFamily: FontFamily.regular,
    fontSize: 14,
    lineHeight: 20,
  },
  bodySm: {
    fontFamily: FontFamily.regular,
    fontSize: 12,
    lineHeight: 16,
  },
  labelLg: {
    fontFamily: FontFamily.semiBold,
    fontSize: 14,
    lineHeight: 20,
    letterSpacing: 0.01 * 14,
  },
  labelMd: {
    fontFamily: FontFamily.semiBold,
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 0.02 * 12,
  },
  labelSm: {
    fontFamily: FontFamily.bold,
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: 0.04 * 11,
  },
};
