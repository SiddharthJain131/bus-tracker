/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
            },
            borderRadius: {
                lg: 'var(--radius)',
                md: 'calc(var(--radius) - 2px)',
                sm: 'calc(var(--radius) - 4px)',
                xl: '1rem',
                '2xl': '1.25rem',
            },
            colors: {
                background: 'hsl(var(--background))',
                foreground: 'hsl(var(--foreground))',
                card: {
                    DEFAULT: 'hsl(var(--card))',
                    foreground: 'hsl(var(--card-foreground))'
                },
                popover: {
                    DEFAULT: 'hsl(var(--popover))',
                    foreground: 'hsl(var(--popover-foreground))'
                },
                primary: {
                    DEFAULT: 'hsl(var(--primary))',
                    foreground: 'hsl(var(--primary-foreground))'
                },
                secondary: {
                    DEFAULT: 'hsl(var(--secondary))',
                    foreground: 'hsl(var(--secondary-foreground))'
                },
                muted: {
                    DEFAULT: 'hsl(var(--muted))',
                    foreground: 'hsl(var(--muted-foreground))'
                },
                accent: {
                    DEFAULT: 'hsl(var(--accent))',
                    foreground: 'hsl(var(--accent-foreground))'
                },
                destructive: {
                    DEFAULT: 'hsl(var(--destructive))',
                    foreground: 'hsl(var(--destructive-foreground))'
                },
                border: 'hsl(var(--border))',
                input: 'hsl(var(--input))',
                ring: 'hsl(var(--ring))',
                
                // Custom theme colors
                navy: 'hsl(var(--navy))',
                'accent-blue': 'hsl(var(--accent-blue))',
                'soft-cyan': 'hsl(var(--soft-cyan))',
                lime: 'hsl(var(--lime))',
                charcoal: 'hsl(var(--charcoal))',
                'medium-gray': 'hsl(var(--medium-gray))',
                'light-gray': 'hsl(var(--light-gray))',
                
                // Status colors
                status: {
                    green: 'hsl(var(--status-green))',
                    yellow: 'hsl(var(--status-yellow))',
                    red: 'hsl(var(--status-red))',
                    blue: 'hsl(var(--status-blue))',
                    gray: 'hsl(var(--status-gray))',
                },
                
                chart: {
                    '1': 'hsl(var(--accent-blue))',
                    '2': 'hsl(var(--soft-cyan))',
                    '3': 'hsl(var(--navy))',
                    '4': 'hsl(var(--lime))',
                    '5': 'hsl(var(--status-green))'
                }
            },
            boxShadow: {
                'modern': '0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -1px rgb(0 0 0 / 0.06)',
                'modern-md': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
                'modern-lg': '0 10px 15px -3px rgb(0 0 0 / 0.07), 0 4px 6px -2px rgb(0 0 0 / 0.05)',
                'modern-xl': '0 20px 25px -5px rgb(0 0 0 / 0.07), 0 8px 10px -6px rgb(0 0 0 / 0.05)',
            },
            keyframes: {
                'accordion-down': {
                    from: {
                        height: '0'
                    },
                    to: {
                        height: 'var(--radix-accordion-content-height)'
                    }
                },
                'accordion-up': {
                    from: {
                        height: 'var(--radix-accordion-content-height)'
                    },
                    to: {
                        height: '0'
                    }
                },
                'fade-in': {
                    from: {
                        opacity: '0',
                        transform: 'translateY(10px)'
                    },
                    to: {
                        opacity: '1',
                        transform: 'translateY(0)'
                    }
                },
                'slide-in': {
                    from: {
                        transform: 'translateX(-100%)'
                    },
                    to: {
                        transform: 'translateX(0)'
                    }
                }
            },
            animation: {
                'accordion-down': 'accordion-down 0.2s ease-out',
                'accordion-up': 'accordion-up 0.2s ease-out',
                'fade-in': 'fade-in 0.3s ease-out',
                'slide-in': 'slide-in 0.3s ease-out'
            }
        }
  },
  plugins: [require("tailwindcss-animate")],
};
