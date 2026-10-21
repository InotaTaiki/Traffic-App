import { API_URL } from './config';
import { Mode, RoutesResponse, TripsResponse } from './types';

async function getJson<T>(path: string, params: Record<string, string>): Promise<T> {
  const query = Object.entries(params)
    .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
    .join('&');
  const url = `${API_URL}${path}?${query}`;

  let res: Response;
  try {
    res = await fetch(url);
  } catch {
    throw new Error(`Can't reach the backend at ${API_URL}. Is app.py running?`);
  }

  if (!res.ok) {
    // The backend sends {"detail": "..."} with a readable message.
    let message = `Request failed (${res.status}).`;
    try {
      const body = await res.json();
      if (typeof body?.detail === 'string') message = body.detail;
    } catch {
      // keep the generic message
    }
    throw new Error(message);
  }
  return (await res.json()) as T;
}

// Car, walking, and cycling routes in one call.
export const fetchTrips = (from: string, to: string) =>
  getJson<TripsResponse>('/trips', { from, to });

// One travel mode only.
export const fetchRoutes = (from: string, to: string, mode: Mode = 'car') =>
  getJson<RoutesResponse>('/routes', { from, to, mode });