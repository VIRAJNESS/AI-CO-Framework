/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{html,ts}'],
  theme: {
    extend: {
      colors: {
        // Corporate theme — mirrors ai-engine doc_factory palette
        navy: '#0F172A',       // Deep Navy
        sky: '#0284C7',        // Electric Sky
        slateink: '#334155',   // Slate
        emeraldok: '#059669',  // Emerald
        brand: {
          50: '#eef6ff',
          500: '#2563eb',
          600: '#1d4ed8',
          900: '#1e3a5f'
        }
      }
    }
  },
  plugins: []
};
