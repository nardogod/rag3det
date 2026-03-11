import { useEffect, useState } from "react";

interface FloatingDiceProps {
  /** Valor da rolagem (1–6). null = não mostra. */
  value: number | null;
}

const rotations = {
  1: { x: 0, y: 0 },
  2: { x: -90, y: 0 },
  3: { x: 0, y: 90 },
  4: { x: 0, y: -90 },
  5: { x: 90, y: 0 },
  6: { x: 0, y: 180 },
} as const;

export function FloatingDice({ value }: FloatingDiceProps) {
  const [visible, setVisible] = useState(false);
  const [transform, setTransform] = useState<string>("");

  useEffect(() => {
    if (value == null || value < 1 || value > 6) {
      setVisible(false);
      return;
    }
    const base = rotations[value as 1 | 2 | 3 | 4 | 5 | 6];
    const extraX = 360 * (Math.floor(Math.random() * 3) + 2);
    const extraY = 360 * (Math.floor(Math.random() * 3) + 2);
    const finalX = base.x + extraX;
    const finalY = base.y + extraY;
    setTransform(`rotateX(${finalX}deg) rotateY(${finalY}deg)`);
    setVisible(true);
    const timeout = setTimeout(() => setVisible(false), 1200);
    return () => clearTimeout(timeout);
  }, [value]);

  if (!visible || value == null) return null;

  const faceSize = 120;
  const half = faceSize / 2;

  return (
    <div className="pointer-events-none fixed inset-0 z-40 flex items-center justify-center">
      <div
        className="h-[120px] w-[120px]"
        style={{ perspective: "800px" }}
      >
        <div
          className="relative h-full w-full"
          style={{
            transformStyle: "preserve-3d",
            transition: "transform 1.2s cubic-bezier(0.25, 1, 0.5, 1)",
            transform,
          }}
        >
          {/* Face 1 */}
          <div
            className="absolute flex h-[120px] w-[120px] items-center justify-center rounded-2xl border border-black/10 bg-gradient-to-br from-white to-stone-200 shadow-[inset_0_0_20px_rgba(0,0,0,0.08)]"
            style={{
              backfaceVisibility: "hidden",
              transform: `rotateY(0deg) translateZ(${half}px)`,
            }}
          >
            <div className="h-5 w-5 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
          </div>

          {/* Face 2 */}
          <div
            className="absolute h-[120px] w-[120px] rounded-2xl border border-black/10 bg-gradient-to-br from-white to-stone-200 shadow-[inset_0_0_20px_rgba(0,0,0,0.08)]"
            style={{
              backfaceVisibility: "hidden",
              transform: `rotateX(-90deg) translateZ(${half}px)`,
            }}
          >
            <div className="flex h-full w-full justify-between p-3">
              <div className="flex h-full flex-col justify-between">
                <div className="h-5 w-5 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
                <div className="h-5 w-5 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
              </div>
            </div>
          </div>

          {/* Face 3 */}
          <div
            className="absolute h-[120px] w-[120px] rounded-2xl border border-black/10 bg-gradient-to-br from-white to-stone-200 shadow-[inset_0_0_20px_rgba(0,0,0,0.08)]"
            style={{
              backfaceVisibility: "hidden",
              transform: `rotateY(-90deg) translateZ(${half}px)`,
            }}
          >
            <div className="flex h-full w-full justify-between p-3">
              <div className="flex h-full flex-col justify-between">
                <div className="h-5 w-5 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
                <div className="h-5 w-5 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
                <div className="h-5 w-5 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
              </div>
            </div>
          </div>

          {/* Face 4 */}
          <div
            className="absolute h-[120px] w-[120px] rounded-2xl border border-black/10 bg-gradient-to-br from-white to-stone-200 shadow-[inset_0_0_20px_rgba(0,0,0,0.08)]"
            style={{
              backfaceVisibility: "hidden",
              transform: `rotateY(90deg) translateZ(${half}px)`,
            }}
          >
            <div className="grid h-full w-full grid-cols-3 grid-rows-3 p-3">
              <div className="col-start-1 row-start-1 flex items-start justify-start">
                <div className="h-4 w-4 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
              </div>
              <div className="col-start-3 row-start-1 flex items-start justify-end">
                <div className="h-4 w-4 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
              </div>
              <div className="col-start-1 row-start-3 flex items-end justify-start">
                <div className="h-4 w-4 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
              </div>
              <div className="col-start-3 row-start-3 flex items-end justify-end">
                <div className="h-4 w-4 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
              </div>
            </div>
          </div>

          {/* Face 5 */}
          <div
            className="absolute h-[120px] w-[120px] rounded-2xl border border-black/10 bg-gradient-to-br from-white to-stone-200 shadow-[inset_0_0_20px_rgba(0,0,0,0.08)]"
            style={{
              backfaceVisibility: "hidden",
              transform: `rotateX(90deg) translateZ(${half}px)`,
            }}
          >
            <div className="grid h-full w-full grid-cols-3 grid-rows-3 p-3">
              <div className="col-start-1 row-start-1 flex items-start justify-start">
                <div className="h-4 w-4 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
              </div>
              <div className="col-start-3 row-start-1 flex items-start justify-end">
                <div className="h-4 w-4 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
              </div>
              <div className="col-start-2 row-start-2 flex items-center justify-center">
                <div className="h-4 w-4 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
              </div>
              <div className="col-start-1 row-start-3 flex items-end justify-start">
                <div className="h-4 w-4 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
              </div>
              <div className="col-start-3 row-start-3 flex items-end justify-end">
                <div className="h-4 w-4 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
              </div>
            </div>
          </div>

          {/* Face 6 */}
          <div
            className="absolute h-[120px] w-[120px] rounded-2xl border border-black/10 bg-gradient-to-br from-white to-stone-200 shadow-[inset_0_0_20px_rgba(0,0,0,0.08)]"
            style={{
              backfaceVisibility: "hidden",
              transform: `rotateY(180deg) translateZ(${half}px)`,
            }}
          >
            <div className="grid h-full w-full grid-cols-3 grid-rows-3 p-3">
              <div className="col-start-1 row-start-1 flex items-start justify-start">
                <div className="h-4 w-4 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
              </div>
              <div className="col-start-3 row-start-1 flex items-start justify-end">
                <div className="h-4 w-4 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
              </div>
              <div className="col-start-1 row-start-2 flex items-center justify-start">
                <div className="h-4 w-4 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
              </div>
              <div className="col-start-3 row-start-2 flex items-center justify-end">
                <div className="h-4 w-4 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
              </div>
              <div className="col-start-1 row-start-3 flex items-end justify-start">
                <div className="h-4 w-4 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
              </div>
              <div className="col-start-3 row-start-3 flex items-end justify-end">
                <div className="h-4 w-4 rounded-full bg-gradient-to-br from-stone-700 to-black shadow-md" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

