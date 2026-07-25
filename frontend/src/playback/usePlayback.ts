import { useCallback, useEffect, useRef, useState } from "react";

import { clampIndex, indexAtOrBefore, nearestIndex } from "./model";

export const PLAYBACK_SPEEDS = [0.5, 1, 2, 4] as const;
export type PlaybackSpeed = (typeof PLAYBACK_SPEEDS)[number];

export interface PlaybackController {
  index: number;
  time: number;
  playing: boolean;
  speed: PlaybackSpeed;
  play: () => void;
  pause: () => void;
  first: () => void;
  last: () => void;
  previous: () => void;
  next: () => void;
  seekIndex: (index: number) => void;
  seekNearestTime: (time: number) => void;
  setSpeed: (speed: PlaybackSpeed) => void;
}

export function usePlayback(timeline: readonly number[]): PlaybackController {
  const [index, setIndexState] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState<PlaybackSpeed>(1);
  const indexRef = useRef(0);

  const updateIndex = useCallback(
    (nextIndex: number) => {
      const clamped = clampIndex(nextIndex, timeline.length);
      indexRef.current = clamped;
      setIndexState((current) => (current === clamped ? current : clamped));
    },
    [timeline.length],
  );

  const pause = useCallback(() => setPlaying(false), []);
  const seekIndex = useCallback(
    (nextIndex: number) => {
      setPlaying(false);
      updateIndex(nextIndex);
    },
    [updateIndex],
  );
  const seekNearestTime = useCallback(
    (time: number) => seekIndex(nearestIndex(timeline, time)),
    [seekIndex, timeline],
  );
  const first = useCallback(() => seekIndex(0), [seekIndex]);
  const last = useCallback(() => seekIndex(timeline.length - 1), [seekIndex, timeline.length]);
  const previous = useCallback(() => seekIndex(indexRef.current - 1), [seekIndex]);
  const next = useCallback(() => seekIndex(indexRef.current + 1), [seekIndex]);
  const play = useCallback(() => {
    if (timeline.length <= 1) {
      return;
    }
    if (indexRef.current >= timeline.length - 1) {
      updateIndex(0);
    }
    setPlaying(true);
  }, [timeline.length, updateIndex]);

  useEffect(() => {
    if (!playing || timeline.length <= 1) {
      return undefined;
    }
    let animationFrame = 0;
    let previousTimestamp: number | null = null;
    let simulatedTime = timeline[indexRef.current];
    const endTime = timeline[timeline.length - 1];

    const animate = (timestamp: number) => {
      if (previousTimestamp === null) {
        previousTimestamp = timestamp;
      } else {
        simulatedTime += ((timestamp - previousTimestamp) / 1000) * speed;
        previousTimestamp = timestamp;
        const nextIndex = indexAtOrBefore(timeline, Math.min(simulatedTime, endTime));
        updateIndex(nextIndex);
        if (simulatedTime >= endTime) {
          setPlaying(false);
          return;
        }
      }
      animationFrame = requestAnimationFrame(animate);
    };

    animationFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrame);
  }, [playing, speed, timeline, updateIndex]);

  return {
    index,
    time: timeline[index] ?? 0,
    playing,
    speed,
    play,
    pause,
    first,
    last,
    previous,
    next,
    seekIndex,
    seekNearestTime,
    setSpeed,
  };
}
