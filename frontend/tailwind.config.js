/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(0, 0%, 100%)",
        foreground: "hsl(222.2, 47%, 11.1%)",
        card: "hsl(0, 0%, 100%)",
        "card-foreground": "hsl(222.2, 47%, 11.1%)",
        popover: "hsl(0, 0%, 100%)",
        "popover-foreground": "hsl(222.2, 47%, 11.1%)",
        primary: {
          DEFAULT: "hsl(222.2, 47%, 11.1%)",
          foreground: "hsl(210, 40%, 98%)",
        },
        secondary: {
          DEFAULT: "hsl(210, 40%, 96.1%)",
          foreground: "hsl(222.2, 47%, 11.1%)",
        },
        muted: {
          DEFAULT: "hsl(210, 40%, 96.1%)",
          foreground: "hsl(215, 40%, 45.1%)",
        },
        accent: {
          DEFAULT: "hsl(210, 40%, 96.1%)",
          foreground: "hsl(222.2, 47%, 11.1%)",
        },
        destructive: {
          DEFAULT: "hsl(0, 84.2%, 60.2%)",
          foreground: "hsl(210, 40%, 98%)",
        },
        border: "hsl(214.3, 31.8%, 91.1%)",
        input: "hsl(214.3, 31.8%, 91.1%)",
        ring: "hsl(222.2, 84%, 4.2%)",
      },
      borderRadius: {
        lg: "0.5rem",
        md: "0.375rem",
        sm: "0.25rem",
      },
    },
  },
  plugins: [],
}
