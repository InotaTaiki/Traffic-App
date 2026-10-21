import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { formatDuration } from '../format';
import { colors, radius, space, type } from '../theme';
import { Mode, RouteOption, TrafficLevel } from '../types';
import { IncidentChip } from './IncidentChip';

const trafficColor: Record<TrafficLevel, string> = {
  clear: colors.clear, slow: colors.slow, heavy: colors.heavy,
};
const trafficLabel: Record<TrafficLevel, string> = {
  clear: 'Light traffic', slow: 'Moderate traffic', heavy: 'Heavy traffic',
};
const modeLabel: Record<Mode, string> = { car: 'Driving', walk: 'Walking', bike: 'Cycling' };

interface Props {
  route: RouteOption;
  mode: Mode;
  selected: boolean;
  isBest: boolean;
  onPress: () => void;
}

export function RouteCard({ route, mode, selected, isBest, onPress }: Props) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityState={{ selected }}
      style={[styles.card, selected && styles.cardSelected]}
    >
      <View style={styles.row}>
        <View style={{ flex: 1 }}>
          <Text style={styles.name}>{route.name}</Text>
          <View style={styles.meta}>
            {mode === 'car' && (
              <View style={[styles.trafficBar, { backgroundColor: trafficColor[route.traffic] }]} />
            )}
            <Text style={styles.caption}>
              {mode === 'car'
                ? `${trafficLabel[route.traffic]} · ${route.distanceMiles} mi${route.reliability === 'variable' ? ' · Time may vary' : ''}`
                : `${modeLabel[mode]} · ${route.distanceMiles} mi`}
            </Text>
          </View>
        </View>
        <View style={styles.etaBlock}>
          <Text style={styles.eta}>{formatDuration(route.etaMinutes)}</Text>
          <Text style={styles.caption}>Arrive {route.arrivalTime}</Text>
        </View>
      </View>

      {isBest && (
        <Text style={styles.best}>
          Best route{route.minutesSaved ? `. Saves ${route.minutesSaved} min over the slowest.` : '.'}
        </Text>
      )}
      {route.incidents.map((i) => <IncidentChip key={i.id} incident={i} />)}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.paper, borderRadius: radius.md, padding: space.lg,
    borderWidth: 2, borderColor: 'transparent', marginBottom: space.md,
  },
  cardSelected: { borderColor: colors.orange },
  row: { flexDirection: 'row', alignItems: 'center' },
  name: { ...type.heading, color: colors.ink },
  meta: { flexDirection: 'row', alignItems: 'center', marginTop: 6 },
  trafficBar: { width: 22, height: 5, borderRadius: 3, marginRight: 8 },
  caption: { ...type.caption, color: colors.inkSoft },
  etaBlock: { alignItems: 'flex-end', marginLeft: space.md },
  eta: { ...type.eta, fontSize: 26, color: colors.ink },
  best: { ...type.caption, color: colors.clear, marginTop: 8, fontWeight: '700' },
});