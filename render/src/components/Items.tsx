import { useState } from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { Editplan, Item } from "../schema";
import { cellRect, stagingRect, type Rect } from "./layout";

const NamePlaceholder: React.FC<{ name: string }> = ({ name }) => (
  <div
    style={{
      width: "100%",
      height: "100%",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: "#bbb",
      fontFamily: "Arial, sans-serif",
      fontSize: 14,
      textAlign: "center",
      padding: 6,
    }}
  >
    {name}
  </div>
);

const MOVE_FRAMES = 20; // duration of the staging -> cell animation

const ItemCard: React.FC<{ plan: Editplan; item: Item }> = ({ plan, item }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const [imgError, setImgError] = useState(false);

  if (frame < item.introFrame) return null;
  const dest = cellRect(plan, item.tier, item.slotIndex);
  if (!dest) return null;
  const stage = stagingRect(plan);

  const moveEnd = item.ratedFrame + MOVE_FRAMES;
  let rect: Rect;

  if (frame < item.ratedFrame) {
    // Staging: pop in at center, showing the whole image.
    const s = spring({ frame: frame - item.introFrame, fps, config: { damping: 14 } });
    rect = { x: stage.x, y: stage.y, size: stage.size * s };
  } else if (frame < moveEnd) {
    // Animate from staging center to the tier cell.
    const p = spring({ frame: frame - item.ratedFrame, fps, durationInFrames: MOVE_FRAMES, config: { damping: 16 } });
    rect = {
      x: interpolate(p, [0, 1], [stage.x, dest.x]),
      y: interpolate(p, [0, 1], [stage.y, dest.y]),
      size: interpolate(p, [0, 1], [stage.size, dest.size]),
    };
  } else {
    rect = dest;
  }

  const half = rect.size / 2;
  return (
    <div
      style={{
        position: "absolute",
        left: rect.x - half,
        top: rect.y - half,
        width: rect.size,
        height: rect.size,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <div
        style={{
          width: rect.size,
          height: rect.size,
          borderRadius: 12,
          overflow: "hidden",
          border: "3px solid #fff",
          boxShadow: "0 6px 18px rgba(0,0,0,0.5)",
          backgroundColor: "#222",
        }}
      >
        {item.image && !imgError ? (
          <Img
            src={staticFile(item.image)}
            onError={() => setImgError(true)}
            style={{ width: "100%", height: "100%", objectFit: "contain" }}
          />
        ) : (
          <NamePlaceholder name={item.name} />
        )}
      </div>
    </div>
  );
};

export const Items: React.FC<{ plan: Editplan }> = ({ plan }) => (
  <AbsoluteFill>
    {plan.items.map((it) => (
      <ItemCard key={it.id} plan={plan} item={it} />
    ))}
  </AbsoluteFill>
);
