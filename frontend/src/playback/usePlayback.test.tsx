import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { usePlayback } from "./usePlayback";

describe("usePlayback", () => {
  let callbacks: Map<number, FrameRequestCallback>;
  let nextId: number;

  beforeEach(() => {
    callbacks = new Map();
    nextId = 1;
    vi.stubGlobal(
      "requestAnimationFrame",
      vi.fn((callback: FrameRequestCallback) => {
        const id = nextId++;
        callbacks.set(id, callback);
        return id;
      }),
    );
    vi.stubGlobal(
      "cancelAnimationFrame",
      vi.fn((id: number) => callbacks.delete(id)),
    );
  });

  afterEach(() => vi.unstubAllGlobals());

  function animationFrame(timestamp: number) {
    const pending = [...callbacks.entries()];
    callbacks.clear();
    act(() => pending.forEach(([, callback]) => callback(timestamp)));
  }

  it.each([
    [0.5, 0.5],
    [1, 1],
    [2, 2],
    [4, 4],
  ] as const)("advances at %s× simulation time", (speed, expectedTime) => {
    const { result } = renderHook(() => usePlayback([0, 0.5, 1, 2, 4]));
    act(() => {
      result.current.setSpeed(speed);
      result.current.play();
    });
    animationFrame(0);
    animationFrame(1000);
    expect(result.current.time).toBe(expectedTime);
  });

  it("pauses, resumes and skips invisible fine-step frames", () => {
    const { result } = renderHook(() => usePlayback([0, 0.1, 0.2, 0.3, 1]));
    act(() => result.current.play());
    animationFrame(0);
    animationFrame(350);
    expect(result.current.time).toBe(0.3);
    act(() => result.current.pause());
    animationFrame(900);
    expect(result.current.time).toBe(0.3);
    act(() => result.current.play());
    animationFrame(1000);
    animationFrame(1100);
    expect(result.current.time).toBe(0.3);
  });

  it("stops on a short tail and restarts from the first frame at the end", () => {
    const { result } = renderHook(() => usePlayback([0, 0.5, 0.75]));
    act(() => result.current.play());
    animationFrame(0);
    animationFrame(750);
    expect(result.current.time).toBe(0.75);
    expect(result.current.playing).toBe(false);

    act(() => result.current.play());
    expect(result.current.time).toBe(0);
    expect(result.current.playing).toBe(true);
  });

  it("pauses on manual first, last, previous, next and scrub operations", () => {
    const { result } = renderHook(() => usePlayback([0, 0.5, 1]));
    act(() => result.current.next());
    expect(result.current.time).toBe(0.5);
    act(() => result.current.last());
    expect(result.current.time).toBe(1);
    act(() => result.current.previous());
    expect(result.current.time).toBe(0.5);
    act(() => result.current.first());
    expect(result.current.time).toBe(0);
    act(() => result.current.seekNearestTime(0.8));
    expect(result.current.time).toBe(1);
    expect(result.current.playing).toBe(false);
  });
});
