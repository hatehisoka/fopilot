// Єдине джерело оформлення графіків Recharts. Серії — лише з категоріальної
// палітри токенів, жодних дефолтних кольорів Recharts.

export const AXIS_TICK = { fill: "var(--color-text-muted)", fontSize: 12 } as const;
export const GRID_STROKE = "var(--color-border)";
export const BAR_RADIUS = 4;
export const BAR_MAX_SIZE = 44;

export const CATEGORICAL = [
  "var(--color-cat-1)",
  "var(--color-cat-2)",
  "var(--color-cat-3)",
  "var(--color-cat-4)",
  "var(--color-cat-5)",
  "var(--color-cat-6)",
];

export const SERIES_BAR = CATEGORICAL[0];
export const SERIES_LINE = CATEGORICAL[1];
