tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "error": "#ba1a1a",
        "on-error": "#ffffff",
        "error-container": "#ffdad6",
        "on-error-container": "#93000a",

        "background": "#f8f9ff",
        "on-background": "#0b1c30",
        "surface": "#f8f9ff",
        "on-surface": "#0b1c30",
        "on-surface-variant": "#45474c",
        "surface-bright": "#f8f9ff",
        "surface-dim": "#cbdbf5",
        "surface-variant": "#d3e4fe",
        "surface-tint": "#545f73",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#eff4ff",
        "surface-container": "#e5eeff",
        "surface-container-high": "#dce9ff",
        "surface-container-highest": "#d3e4fe",
        "inverse-surface": "#213145",
        "inverse-on-surface": "#eaf1ff",
        "inverse-primary": "#bcc7de",
        "outline": "#75777d",
        "outline-variant": "#c5c6cd",

        "primary": "#091426",
        "on-primary": "#ffffff",
        "primary-container": "#1e293b",
        "on-primary-container": "#8590a6",
        "primary-fixed": "#d8e3fb",
        "primary-fixed-dim": "#bcc7de",
        "on-primary-fixed": "#111c2d",
        "on-primary-fixed-variant": "#3c475a",

        "secondary": "#0058be",
        "on-secondary": "#ffffff",
        "secondary-container": "#2170e4",
        "on-secondary-container": "#fefcff",
        "secondary-fixed": "#d8e2ff",
        "secondary-fixed-dim": "#adc6ff",
        "on-secondary-fixed": "#001a42",
        "on-secondary-fixed-variant": "#004395",

        "tertiary": "#001815",
        "on-tertiary": "#ffffff",
        "tertiary-container": "#002f2a",
        "on-tertiary-container": "#28a094",
        "tertiary-fixed": "#89f5e7",
        "tertiary-fixed-dim": "#6bd8cb",
        "on-tertiary-fixed": "#00201d",
        "on-tertiary-fixed-variant": "#005049"
      },

      borderRadius: {
        DEFAULT: "0.125rem",
        lg: "0.25rem",
        xl: "0.5rem",
        full: "0.75rem"
      },

      spacing: {
        "space-2xs": "0.125rem",
        "space-xs": "0.25rem",
        "space-sm": "0.5rem",
        "space-md": "0.75rem",
        "space-lg": "1rem",
        "space-xl": "1.5rem",
        "space-2xl": "2rem",
        "gutter": "0.75rem",
        "gutter-desktop": "1rem",
        "margin": "1rem",
        "margin-desktop": "1.5rem"
      },

      fontFamily: {
        "headline-xl": ["Hanken Grotesk"],
        "headline-lg": ["Hanken Grotesk"],
        "headline-lg-mobile": ["Hanken Grotesk"],
        "headline-sm": ["Hanken Grotesk"],
        "body-lg": ["Inter"],
        "body-md": ["Inter"],
        "body-sm": ["Inter"],
        "label-md": ["Inter"],
        "label-sm": ["Inter"],
        "data-mono": ["JetBrains Mono"],
        "data-mono-sm": ["JetBrains Mono"]
      },

      fontSize: {
        "headline-xl": ["2rem", { lineHeight: "2.5rem", letterSpacing: "-0.02em", fontWeight: "700" }],
        "headline-lg": ["1.5rem", { lineHeight: "2rem", letterSpacing: "-0.015em", fontWeight: "600" }],
        "headline-lg-mobile": ["1.25rem", { lineHeight: "1.75rem", letterSpacing: "-0.01em", fontWeight: "600" }],
        "headline-sm": ["1.125rem", { lineHeight: "1.5rem", letterSpacing: "-0.01em", fontWeight: "600" }],
        "body-lg": ["1rem", { lineHeight: "1.5rem", letterSpacing: "0em", fontWeight: "400" }],
        "body-md": ["0.875rem", { lineHeight: "1.25rem", letterSpacing: "0em", fontWeight: "400" }],
        "body-sm": ["0.75rem", { lineHeight: "1rem", letterSpacing: "0.01em", fontWeight: "400" }],
        "label-md": ["0.8125rem", { lineHeight: "1rem", letterSpacing: "0.015em", fontWeight: "600" }],
        "label-sm": ["0.6875rem", { lineHeight: "0.875rem", letterSpacing: "0.04em", fontWeight: "600" }],
        "data-mono": ["0.8125rem", { lineHeight: "1rem", letterSpacing: "-0.01em", fontWeight: "500" }],
        "data-mono-sm": ["0.6875rem", { lineHeight: "0.875rem", letterSpacing: "0em", fontWeight: "500" }]
      }
    }
  }
};