export type TrafficLevel = 'clear' | 'slow' | 'heavy';
export type IncidentKind = 'accident' | 'construction' | 'closure' | 'event' | 'hazard';
export type Mode = 'car' | 'walk' | 'bike';

export interface Incident {
  id: string;
  kind: IncidentKind;
  label: string;
  delayMinutes: number;
  lat: number;
  lng: number;
  source?: string;
}

export interface RouteOption {
  id: string;
  name: string;
  etaMinutes: number;
  freeFlowMinutes?: number;
  distanceMiles: number;
  arrivalTime: string;
  traffic: TrafficLevel;
  reliability: 'steady' | 'variable';
  minutesSaved?: number;
  incidents: Incident[];
  geometry: [number, number][]; // [lng, lat] pairs
}

export interface Place {
  lat: number;
  lng: number;
  name: string;
}

export interface RoutesResponse {
  generatedAt: string;
  mode?: Mode;
  trafficSource: string;
  origin: Place;
  destination: Place;
  routes: RouteOption[];
}

// One travel mode inside a /trips response. If ok is false, error says why.
export interface ModeResult {
  ok: boolean;
  error?: string;
  trafficSource?: string;
  routes?: RouteOption[];
}

export interface TripsResponse {
  generatedAt: string;
  straightLineMiles: number;
  origin: Place;
  destination: Place;
  modes: Record<Mode, ModeResult>;
}

export interface RouteMapProps {
  routes: RouteOption[];
  selectedId: string | null;
  origin?: Place;
  destination?: Place;
  onSelect: (id: string) => void;
}