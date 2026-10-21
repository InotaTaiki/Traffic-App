import React, { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { fetchTrips } from '../api';
import { RouteCard } from '../components/RouteCard';
import { RouteMap } from '../components/RouteMap';
import { SearchCard } from '../components/SearchCard';
import { formatDuration } from '../format';
import { colors, radius, space, type } from '../theme';
import { Mode, RouteOption, TripsResponse } from '../types';

const MODES: { id: Mode; label: string }[] = [
  { id: 'car', label: '🚗 Car' },
  { id: 'walk', label: '🚶 Walk' },
  { id: 'bike', label: '🚲 Bike' },
];
const NO_ROUTES: RouteOption[] = [];

export default function HomeScreen() {
  const [from, setFrom] = useState('Mission Dolores Park, San Francisco');
  const [to, setTo] = useState('Ferry Building, San Francisco');
  const [trips, setTrips] = useState<TripsResponse | null>(null);
  const [mode, setMode] = useState<Mode>('car');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [locating, setLocating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [locationNotice, setLocationNotice] = useState<string | null>(null);
  const [fromCoordinates, setFromCoordinates] = useState<{ latitude: number; longitude: number } | null>(null);
  const [searchedFromLocation, setSearchedFromLocation] = useState(false);
  const startingPointRef = useRef<React.ElementRef<typeof TextInput>>(null);

  useEffect(() => {
    if (locationNotice) startingPointRef.current?.focus();
  }, [locationNotice]);

  function showMode(next: Mode, data: TripsResponse) {
    setMode(next);
    setSelectedId(data.modes[next]?.routes?.[0]?.id ?? null);
  }

  async function search() {
    if (loading) return;
    if ((!fromCoordinates && !from.trim()) || !to.trim()) {
      setError('Enter a starting address (or use your location) and a destination.');
      return;
    }
    const originQuery = fromCoordinates
      ? `${fromCoordinates.latitude.toFixed(5)},${fromCoordinates.longitude.toFixed(5)}`
      : from.trim();
    const usedLocation = Boolean(fromCoordinates);
    setLoading(true);
    setError(null);
    try {
      const res = await fetchTrips(originQuery, to.trim());
      setTrips(res);
      setSearchedFromLocation(usedLocation);
      // Keep the current mode if it has routes, otherwise use the first mode that does.
      const hasRoutes = (m: Mode) => Boolean(res.modes[m]?.ok && res.modes[m].routes?.length);
      const next = hasRoutes(mode) ? mode : MODES.find((m) => hasRoutes(m.id))?.id ?? mode;
      showMode(next, res);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  }

  // Browser only for now. On phones this would use expo-location.
  const canLocate = Platform.OS === 'web' && typeof navigator !== 'undefined' && !!navigator.geolocation;
  function fillMyLocation() {
    setLocating(true);
    setError(null);
    setLocationNotice(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setFrom('My location');
        setFromCoordinates({ latitude: pos.coords.latitude, longitude: pos.coords.longitude });
        setLocating(false);
      },
      (positionError) => {
        const notices: Record<number, string> = {
          1: 'Location access is blocked. Type your current address instead.',
          2: 'Your device could not find your location. Type your current address instead.',
          3: 'The location request timed out. Type your current address instead.',
        };
        setFrom('');
        setFromCoordinates(null);
        setLocationNotice(notices[positionError.code] ?? 'Location is unavailable. Type your current address instead.');
        setLocating(false);
      },
      { timeout: 10000 },
    );
  }

  const current = trips?.modes[mode];
  const routes = current?.ok ? current.routes ?? NO_ROUTES : NO_ROUTES;

  return (
    <View style={styles.root}>
      <RouteMap
        routes={routes}
        selectedId={selectedId}
        origin={trips?.origin}
        destination={trips?.destination}
        onSelect={setSelectedId}
      />

      <SafeAreaView edges={['top']} style={styles.top} pointerEvents="box-none">
        <SearchCard
          from={from} to={to}
          startingPointRef={startingPointRef}
          onChangeFrom={(value) => {
            setFrom(value);
            setFromCoordinates(null);
            setLocationNotice(null);
          }}
          onChangeTo={setTo}
          onSwap={() => {
            if (fromCoordinates) {
              setFrom(to);
              setTo(`${fromCoordinates.latitude.toFixed(5)},${fromCoordinates.longitude.toFixed(5)}`);
              setFromCoordinates(null);
            } else {
              setFrom(to);
              setTo(from);
            }
            setLocationNotice(null);
          }}
          onSubmit={search}
        />
        {canLocate && (
          <Pressable style={styles.locate} onPress={fillMyLocation} accessibilityRole="button">
            <Text style={styles.locateText}>{locating ? 'Finding you...' : '📍 Use my location as the start'}</Text>
          </Pressable>
        )}
        {locationNotice && <Text style={styles.locationNotice}>{locationNotice}</Text>}
      </SafeAreaView>

      <SafeAreaView edges={['bottom']} style={styles.sheet}>
        <View style={styles.grabber} />

        {trips ? (
          <>
            <Text style={styles.resolvedPlace} numberOfLines={1} ellipsizeMode="tail">
              From: {searchedFromLocation ? 'My location' : trips.origin.name}
            </Text>
            <Text style={styles.resolvedPlace} numberOfLines={1} ellipsizeMode="tail">
              To: {trips.destination.name}
            </Text>
            <Text style={styles.placeHint}>
              Wrong place? Add the city or ZIP code and search again.
            </Text>
            <View style={styles.tabs}>
              {MODES.map((m) => {
                const result = trips.modes[m.id];
                const best = result?.ok ? result.routes?.[0] : undefined;
                const active = m.id === mode;
                return (
                  <Pressable
                    key={m.id}
                    onPress={() => showMode(m.id, trips)}
                    accessibilityRole="button"
                    accessibilityState={{ selected: active }}
                    style={[styles.tab, active && styles.tabActive]}
                  >
                    <Text style={[styles.tabLabel, active && styles.tabTextActive]}>{m.label}</Text>
                    <Text style={[styles.tabEta, active && styles.tabTextActive]}>
                      {best ? formatDuration(best.etaMinutes) : 'Unavailable'}
                    </Text>
                  </Pressable>
                );
              })}
            </View>

            <Text style={styles.source}>
              About {trips.straightLineMiles} mi in a straight line.
              {current?.ok && current.trafficSource ? ` ${current.trafficSource}` : ''}
            </Text>

            {current && !current.ok && (
              <Text style={styles.error}>{current.error ?? 'No route available for this mode.'}</Text>
            )}

            <ScrollView style={{ maxHeight: 200 }} showsVerticalScrollIndicator={false}>
              {routes.map((r, i) => (
                <RouteCard
                  key={r.id} route={r} mode={mode} isBest={i === 0}
                  selected={r.id === selectedId}
                  onPress={() => setSelectedId(r.id)}
                />
              ))}
            </ScrollView>
          </>
        ) : (
          <Text style={styles.hint}>
            Type an address or use your location to compare driving, walking, and cycling.
          </Text>
        )}

        {error && <Text style={styles.error}>{error}</Text>}

        <Pressable
          style={[styles.button, loading && { opacity: 0.6 }]}
          onPress={search}
          accessibilityRole="button"
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>{trips ? 'Refresh routes' : 'Find routes'}</Text>
          )}
        </Pressable>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.fog },
  top: { position: 'absolute', top: 0, left: 0, right: 0, paddingHorizontal: space.lg, paddingTop: space.sm, zIndex: 10 },
  locate: {
    alignSelf: 'flex-start', marginTop: space.sm, backgroundColor: colors.paper, borderRadius: radius.lg,
    paddingVertical: 8, paddingHorizontal: 14,
    elevation: 4, shadowColor: colors.ink, shadowOpacity: 0.15, shadowRadius: 8, shadowOffset: { width: 0, height: 2 },
  },
  locateText: { ...type.caption, color: colors.ink, fontWeight: '700' },
  locationNotice: {
    ...type.caption, color: '#806000', backgroundColor: '#FFF3CD', marginTop: space.sm,
    marginLeft: space.xs, paddingVertical: space.xs, paddingHorizontal: space.sm, borderRadius: radius.sm,
  },
  sheet: {
    position: 'absolute', bottom: 0, left: 0, right: 0, zIndex: 10,
    backgroundColor: colors.fog, borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg,
    paddingHorizontal: space.lg, paddingTop: space.sm,
    elevation: 12, shadowColor: colors.ink, shadowOpacity: 0.2, shadowRadius: 16, shadowOffset: { width: 0, height: -4 },
  },
  grabber: { alignSelf: 'center', width: 40, height: 5, borderRadius: 3, backgroundColor: '#C5CDD4', marginBottom: space.md },
  tabs: { flexDirection: 'row', gap: space.sm, marginBottom: space.sm },
  tab: { flex: 1, backgroundColor: colors.paper, borderRadius: radius.md, paddingVertical: 10, alignItems: 'center' },
  tabActive: { backgroundColor: colors.ink },
  tabLabel: { ...type.caption, color: colors.inkSoft, fontWeight: '700' },
  tabEta: { ...type.heading, color: colors.ink, marginTop: 2 },
  tabTextActive: { color: '#fff' },
  source: { ...type.caption, color: colors.inkSoft, marginBottom: space.md },
  resolvedPlace: { ...type.caption, color: colors.ink, marginBottom: space.xs },
  placeHint: { ...type.caption, color: colors.inkSoft, marginTop: space.xs, marginBottom: space.sm },
  hint: { ...type.body, color: colors.inkSoft, marginBottom: space.md },
  error: { ...type.body, color: colors.heavy, marginBottom: space.md },
  button: { backgroundColor: colors.ink, borderRadius: radius.md, paddingVertical: 16, alignItems: 'center', marginTop: space.xs, marginBottom: space.sm },
  buttonText: { ...type.heading, color: '#fff' },
});