import React from 'react';
import { StyleSheet, View } from 'react-native';
import { colors } from '../theme';

// Stand-in for the real map. When you wire things up, replace the body with
// <MapView> from react-native-maps (or @rnmapbox/maps) and keep the same props.
export function MapPlaceholder({ selectedIndex }: { selectedIndex: number }) {
  const streets = [12, 28, 44, 60, 76];
  return (
    <View style={styles.map}>
      {streets.map((p) => (
        <React.Fragment key={p}>
          <View style={[styles.h, { top: `${p}%` }]} />
          <View style={[styles.v, { left: `${p}%` }]} />
        </React.Fragment>
      ))}
      {/* Alternatives (blue) and the selected route (orange) */}
      <View style={[styles.route, { backgroundColor: colors.bay, top: '28%', left: '18%', width: '58%', opacity: selectedIndex === 1 ? 0.9 : 0.4 }]} />
      <View style={[styles.route, { backgroundColor: colors.bay, top: '60%', left: '18%', width: '58%', opacity: selectedIndex === 2 ? 0.9 : 0.4 }]} />
      <View style={[styles.route, styles.selected, { top: '44%', left: '18%', width: '62%' }]} />
      {/* Incident marker */}
      <View style={[styles.incident, { top: '60%', left: '52%' }]} />
      {/* Origin and destination */}
      <View style={[styles.origin, { top: '44%', left: '16%' }]} />
      <View style={[styles.dest, { top: '44%', left: '78%' }]} />
    </View>
  );
}

const styles = StyleSheet.create({
  map: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: colors.fog },
  h: { position: 'absolute', left: 0, right: 0, height: 10, backgroundColor: '#F6F8F9' },
  v: { position: 'absolute', top: 0, bottom: 0, width: 10, backgroundColor: '#F6F8F9' },
  route: { position: 'absolute', height: 6, borderRadius: 3 },
  selected: { backgroundColor: colors.orange, height: 8 },
  incident: { position: 'absolute', width: 18, height: 18, borderRadius: 9, backgroundColor: colors.heavy, borderWidth: 3, borderColor: '#fff' },
  origin: { position: 'absolute', width: 18, height: 18, borderRadius: 9, backgroundColor: '#fff', borderWidth: 4, borderColor: colors.bay },
  dest: { position: 'absolute', width: 18, height: 18, borderRadius: 3, backgroundColor: colors.orange, borderWidth: 3, borderColor: '#fff' },
});