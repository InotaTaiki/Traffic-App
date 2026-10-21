import React from 'react';
import { RouteMapProps } from '../types';
import { MapPlaceholder } from './MapPlaceholder';

// Phone version. Still the placeholder for now. RouteMap.web.tsx is used in the browser.
export function RouteMap({ routes, selectedId }: RouteMapProps) {
  const index = Math.max(0, routes.findIndex((r) => r.id === selectedId));
  return <MapPlaceholder selectedIndex={index} />;
}