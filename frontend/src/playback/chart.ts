export interface ChartPoint {
  time: number;
  value: number | null;
}

export interface NumericRange {
  minimum: number;
  maximum: number;
}

export function numericRange(values: readonly (number | null)[]): NumericRange {
  const finite = values.filter(
    (value): value is number => value !== null && Number.isFinite(value),
  );
  if (finite.length === 0) {
    return { minimum: 0, maximum: 1 };
  }
  let minimum = finite[0];
  let maximum = finite[0];
  for (const value of finite.slice(1)) {
    minimum = Math.min(minimum, value);
    maximum = Math.max(maximum, value);
  }
  if (minimum === maximum) {
    const padding = minimum === 0 ? 1 : Math.abs(minimum) * 0.1;
    return { minimum: minimum - padding, maximum: maximum + padding };
  }
  return { minimum, maximum };
}

export function chartLinePath(
  points: readonly ChartPoint[],
  x: (value: number) => number,
  y: (value: number) => number,
): string {
  let path = "";
  let drawing = false;
  for (const point of points) {
    if (point.value === null || !Number.isFinite(point.value)) {
      drawing = false;
      continue;
    }
    path += `${drawing ? "L" : "M"}${x(point.time)} ${y(point.value)}`;
    drawing = true;
  }
  return path;
}

export function linearScale(
  domainMinimum: number,
  domainMaximum: number,
  rangeMinimum: number,
  rangeMaximum: number,
): (value: number) => number {
  const domainSize = domainMaximum - domainMinimum;
  if (domainSize === 0) {
    return () => (rangeMinimum + rangeMaximum) / 2;
  }
  return (value) =>
    rangeMinimum + ((value - domainMinimum) / domainSize) * (rangeMaximum - rangeMinimum);
}

export function categoricalBandPaths<T extends string>(
  values: readonly { start: number; end: number; category: T }[],
  categories: readonly T[],
  x: (value: number) => number,
  top: number,
  height: number,
): Record<T, string> {
  const paths = Object.fromEntries(categories.map((category) => [category, ""])) as Record<
    T,
    string
  >;
  for (const value of values) {
    const left = x(value.start);
    const width = Math.max(x(value.end) - left, 0);
    paths[value.category] += `M${left} ${top}h${width}v${height}h-${width}Z`;
  }
  return paths;
}
