import L from 'leaflet';
import React, { useEffect, useRef } from 'react';
import { StyleSheet, View } from 'react-native';
import { colors } from '../theme';
import { RouteMapProps } from '../types';

// Browser map: Leaflet with free OpenStreetMap tiles (no API key). Metro uses this file on web
// and RouteMap.tsx on phones.

// Free tiles with no key and no account. OpenStreetMap's public tile server is fine for development
// and light use. Read https://operations.osmfoundation.org/policies/tiles/ before any real launch.
const TILES = {
  url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  options: { maxZoom: 19, attribution: '&copy; OpenStreetMap contributors' },
};

function ensureLeafletCss() {
  if (document.getElementById('leaflet-css')) return;
  const link = document.createElement('link');
  link.id = 'leaflet-css';
  link.rel = 'stylesheet';
  link.href = `https://unpkg.com/leaflet@${L.version}/dist/leaflet.css`;
  // If that host is blocked, try a second one.
  link.onerror = () => {
    link.onerror = null;
    link.href = `https://cdn.jsdelivr.net/npm/leaflet@${L.version}/dist/leaflet.css`;
  };
  document.head.appendChild(link);
}

// The backend sends [lng, lat]. Leaflet wants [lat, lng].
const toLatLng = (coords: [number, number][]) =>
  coords.map(([lng, lat]) => [lat, lng] as [number, number]);

export function RouteMap({ routes, selectedId, origin, destination, onSelect }: RouteMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerRef = useRef<L.LayerGroup | null>(null);

  // Create the map once.
  useEffect(() => {
    ensureLeafletCss();
    const el = containerRef.current;
    if (!el) return;

    const map = L.map(el, { zoomControl: false }).setView([37.7749, -122.4194], 12);
    L.control.zoom({ position: 'topright' }).addTo(map);

    L.tileLayer(TILES.url, TILES.options).addTo(map);

    layerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;

    const observer = new ResizeObserver(() => map.invalidateSize());
    observer.observe(el);
    return () => {
      observer.disconnect();
      map.remove();
      mapRef.current = null;
      layerRef.current = null;
    };
  }, []);

  // Zoom to fit when a new set of routes arrives (leaving room for the search card and sheet).
  useEffect(() => {
    const map = mapRef.current;
    if (!map || routes.length === 0) return;
    const points = routes.flatMap((r) => toLatLng(r.geometry));
    if (points.length === 0) return;
    map.fitBounds(L.latLngBounds(points), {
      paddingTopLeft: [40, 150],
      paddingBottomRight: [40, 500],
    });
  }, [routes]);

  // Redraw lines and markers when the routes or the selection change.
  useEffect(() => {
    const layer = layerRef.current;
    if (!layer) return;
    layer.clearLayers();

    // Selected route last, so it sits on top.
    const ordered = [...routes].sort(
      (a, b) => Number(a.id === selectedId) - Number(b.id === selectedId),
    );
    for (const r of ordered) {
      const selected = r.id === selectedId;
      L.polyline(toLatLng(r.geometry), {
        color: selected ? colors.orange : colors.bay,
        weight: selected ? 8 : 5,
        opacity: selected ? 1 : 0.55,
      })
        .on('click', () => onSelect(r.id))
        .addTo(layer);
    }

    const seen = new Set<string>();
    for (const r of routes) {
      for (const i of r.incidents) {
        if (seen.has(i.id)) continue;
        seen.add(i.id);
        L.circleMarker([i.lat, i.lng], {
          radius: 9, color: '#fff', weight: 3, fillColor: colors.heavy, fillOpacity: 1,
        })
          .bindTooltip(`${i.label} (+${i.delayMinutes} min)`)
          .addTo(layer);
      }
    }

    if (origin) {
      L.circleMarker([origin.lat, origin.lng], {
        radius: 9, color: colors.bay, weight: 4, fillColor: '#fff', fillOpacity: 1,
      }).addTo(layer);
    }
    if (destination) {
      L.circleMarker([destination.lat, destination.lng], {
        radius: 9, color: '#fff', weight: 3, fillColor: colors.orange, fillOpacity: 1,
      }).addTo(layer);
    }
  }, [routes, selectedId, origin, destination, onSelect]);

  // zIndex 0 keeps Leaflet's internal layers (which use z-index up to 1000) from painting
  // on top of the search card and bottom sheet.
  return (
    <View style={[StyleSheet.absoluteFill, { zIndex: 0 }]}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
    </View>
  );
}