// Where the backend (app.py) is running.
// Web browser on the same PC: http://localhost:3000
// Phone or emulator later: set EXPO_PUBLIC_API_URL to your PC's address, e.g. http://192.168.1.20:3000
export const API_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:3000';