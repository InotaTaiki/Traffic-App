import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, radius, type } from '../theme';
import { Incident } from '../types';

export function IncidentChip({ incident }: { incident: Incident }) {
  return (
    <View style={styles.chip}>
      <View style={styles.dot} />
      <Text style={styles.text} numberOfLines={1}>
        {incident.label} (+{incident.delayMinutes} min)
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  chip: {
    flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-start',
    backgroundColor: '#FBE4DF', borderRadius: radius.sm,
    paddingHorizontal: 10, paddingVertical: 5, marginTop: 6,
  },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.orange, marginRight: 8 },
  text: { ...type.caption, color: colors.ink, flexShrink: 1 },
});