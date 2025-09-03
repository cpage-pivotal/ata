/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Define colors directly without CSS variables
                border: 'rgb(226 232 240)', // slate-200
                input: 'rgb(226 232 240)',  // slate-200
                ring: 'rgb(59 130 246)',    // blue-500
                background: 'rgb(255 255 255)', // white
                foreground: 'rgb(15 23 42)',    // slate-900
                primary: {
                    DEFAULT: 'rgb(59 130 246)',   // blue-500
                    foreground: 'rgb(255 255 255)', // white
                },
                secondary: {
                    DEFAULT: 'rgb(241 245 249)',  // slate-100
                    foreground: 'rgb(15 23 42)',  // slate-900
                },
                destructive: {
                    DEFAULT: 'rgb(239 68 68)',    // red-500
                    foreground: 'rgb(255 255 255)', // white
                },
                muted: {
                    DEFAULT: 'rgb(241 245 249)',  // slate-100
                    foreground: 'rgb(100 116 139)', // slate-500
                },
                accent: {
                    DEFAULT: 'rgb(241 245 249)',  // slate-100
                    foreground: 'rgb(15 23 42)',  // slate-900
                },
                popover: {
                    DEFAULT: 'rgb(255 255 255)', // white
                    foreground: 'rgb(15 23 42)', // slate-900
                },
                card: {
                    DEFAULT: 'rgb(255 255 255)', // white
                    foreground: 'rgb(15 23 42)', // slate-900
                },
            },
            borderRadius: {
                lg: '0.5rem',
                md: '0.375rem',
                sm: '0.25rem',
            },
        },
    },
    plugins: [],
}