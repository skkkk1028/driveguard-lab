import { describe, expect, it } from "vitest";

import { categoricalBandPaths, chartLinePath, linearScale, numericRange } from "./chart";

describe("SVG chart geometry", () => {
  it("breaks a line at null values instead of drawing zero", () => {
    expect(
      chartLinePath(
        [
          { time: 0, value: 2 },
          { time: 1, value: null },
          { time: 2, value: 3 },
          { time: 3, value: 4 },
        ],
        (value) => value * 10,
        (value) => 100 - value,
      ),
    ).toBe("M0 98M20 97L30 96");
  });

  it("creates non-zero ranges for empty, constant, zero and negative data", () => {
    expect(numericRange([])).toEqual({ minimum: 0, maximum: 1 });
    expect(numericRange([0, 0])).toEqual({ minimum: -1, maximum: 1 });
    expect(numericRange([5, 5])).toEqual({ minimum: 4.5, maximum: 5.5 });
    expect(numericRange([-10, -5])).toEqual({ minimum: -10, maximum: -5 });
  });

  it("centres a constant-domain linear scale", () => {
    expect(linearScale(2, 2, 10, 20)(999)).toBe(15);
  });

  it("combines categorical segments into one path per category", () => {
    const paths = categoricalBandPaths(
      [
        { start: 0, end: 1, category: "safe" as const },
        { start: 1, end: 2, category: "danger" as const },
      ],
      ["safe", "danger"] as const,
      (value) => value * 10,
      0,
      5,
    );
    expect(paths.safe).toBe("M0 0h10v5h-10Z");
    expect(paths.danger).toBe("M10 0h10v5h-10Z");
  });
});
