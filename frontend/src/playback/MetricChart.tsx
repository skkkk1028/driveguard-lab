import { useMemo, useRef } from "react";

import { chartLinePath, linearScale, numericRange, type ChartPoint } from "./chart";

const WIDTH = 760;
const HEIGHT = 250;
const PLOT = { left: 58, right: 18, top: 22, bottom: 42 };

export interface ChartSeries {
  id: string;
  label: string;
  color: string;
  points: ChartPoint[];
  dashed?: boolean;
  emphasized?: boolean;
}

export interface ReferenceLine {
  id: string;
  label: string;
  value: number;
  color: string;
  dashed?: boolean;
}

interface MetricChartProps {
  title: string;
  unit: string;
  summary: string;
  duration: number;
  currentTime: number;
  series: ChartSeries[];
  references?: ReferenceLine[];
  onSeek: (time: number) => void;
}

export function MetricChart({
  title,
  unit,
  summary,
  duration,
  currentTime,
  series,
  references = [],
  onSeek,
}: MetricChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const geometry = useMemo(() => {
    const effectiveDuration = duration === 0 ? 1 : duration;
    const values = [
      ...series.flatMap((item) => item.points.map((point) => point.value)),
      ...references.map((reference) => reference.value),
    ];
    const range = numericRange(values);
    const x = linearScale(0, effectiveDuration, PLOT.left, WIDTH - PLOT.right);
    const y = linearScale(range.minimum, range.maximum, HEIGHT - PLOT.bottom, PLOT.top);
    return {
      x,
      y,
      range,
      paths: series.map((item) => ({
        ...item,
        path: chartLinePath(item.points, x, y),
      })),
    };
  }, [duration, references, series]);

  function handlePointer(event: React.MouseEvent<SVGSVGElement>) {
    const bounds = svgRef.current?.getBoundingClientRect();
    if (!bounds || bounds.width === 0) {
      return;
    }
    const viewBoxX = ((event.clientX - bounds.left) / bounds.width) * WIDTH;
    const ratio = Math.min(
      Math.max((viewBoxX - PLOT.left) / (WIDTH - PLOT.left - PLOT.right), 0),
      1,
    );
    onSeek(ratio * duration);
  }

  return (
    <figure className="metric-chart">
      <figcaption>
        <strong>{title}</strong>
        <span>{unit}</span>
      </figcaption>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label={`${title}，点击图表可跳转时间`}
        onClick={handlePointer}
      >
        <title>{`${title}。${summary}`}</title>
        <line className="chart-axis" x1={PLOT.left} y1={PLOT.top} x2={PLOT.left} y2={HEIGHT - PLOT.bottom} />
        <line
          className="chart-axis"
          x1={PLOT.left}
          y1={HEIGHT - PLOT.bottom}
          x2={WIDTH - PLOT.right}
          y2={HEIGHT - PLOT.bottom}
        />
        <text className="chart-axis-label" x={PLOT.left} y={HEIGHT - 16}>0 s</text>
        <text className="chart-axis-label" textAnchor="end" x={WIDTH - PLOT.right} y={HEIGHT - 16}>
          {String(duration)} s
        </text>
        {references.map((reference) => (
          <g key={reference.id}>
            <line
              className="chart-reference"
              x1={PLOT.left}
              x2={WIDTH - PLOT.right}
              y1={geometry.y(reference.value)}
              y2={geometry.y(reference.value)}
              stroke={reference.color}
              strokeDasharray={reference.dashed === false ? undefined : "5 5"}
            />
            <text
              className="chart-reference-label"
              textAnchor="end"
              x={WIDTH - PLOT.right - 4}
              y={geometry.y(reference.value) - 4}
            >
              {reference.label}
            </text>
          </g>
        ))}
        {geometry.paths.map((item) => (
          <path
            key={item.id}
            className={item.emphasized ? "chart-line emphasized" : "chart-line"}
            d={item.path}
            fill="none"
            stroke={item.color}
            strokeDasharray={item.dashed ? "8 5" : undefined}
          />
        ))}
        <line
          className="chart-cursor"
          x1={geometry.x(currentTime)}
          x2={geometry.x(currentTime)}
          y1={PLOT.top}
          y2={HEIGHT - PLOT.bottom}
        />
      </svg>
      <div className="chart-legend" aria-label={`${title}图例`}>
        {series.map((item) => (
          <span key={item.id}>
            <i style={{ backgroundColor: item.color }} className={item.dashed ? "dashed" : ""} />
            {item.label}
          </span>
        ))}
        {references.map((reference) => (
          <span key={reference.id}>
            <i style={{ backgroundColor: reference.color }} className="dashed" />
            {reference.label} {String(reference.value)} {unit}
          </span>
        ))}
      </div>
      <p className="visually-hidden">{summary}</p>
    </figure>
  );
}
