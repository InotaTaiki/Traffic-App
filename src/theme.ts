// Palette: a printed-map feel with San Francisco's International Orange as the one loud color.
export const colors = {
  ink: '#12263A',        // primary text, buttons
  inkSoft: '#5B6B7A',    // secondary text
  fog: '#E9EDF0',        // map background / dividers
  paper: '#FAFBFB',      // cards and sheets
  orange: '#E8553D',     // selected route, incidents, primary accent
  bay: '#2B6CB0',        // alternative routes
  clear: '#2E8B6A',      // light traffic
  slow: '#E0A526',       // moderate traffic
  heavy: '#C23B2E',      // heavy traffic
};

export const radius = { sm: 8, md: 14, lg: 24 };
export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24 };

export const type = {
  title: { fontSize: 28, fontWeight: '800' as const, letterSpacing: -0.5 },
  eta: { fontSize: 32, fontWeight: '800' as const, letterSpacing: -1 },
  heading: { fontSize: 17, fontWeight: '700' as const },
  body: { fontSize: 15, fontWeight: '500' as const },
  caption: { fontSize: 13, fontWeight: '500' as const },
};