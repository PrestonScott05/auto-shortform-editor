import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import type { Editplan } from "../schema";

/** Opening title/hook card: fades and slides in, holds, fades out. */
export const TitleCard: React.FC<{ plan: Editplan }> = ({ plan }) => {
  const frame = useCurrentFrame();
  const card = plan.titleCard;
  if (!card || frame < card.startFrame || frame > card.endFrame) return null;

  const FADE = 12;
  const local = frame - card.startFrame;
  const span = card.endFrame - card.startFrame;
  const opacity = interpolate(local, [0, FADE, span - FADE, span], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const y = interpolate(local, [0, FADE], [20, 0], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", padding: "0 40px" }}>
      <div
        style={{
          opacity,
          transform: `translateY(${y}px)`,
          fontFamily: "Arial Black, Arial, sans-serif",
          fontWeight: 900,
          fontSize: 56,
          color: "#fff",
          textAlign: "center",
          textTransform: "uppercase",
          WebkitTextStroke: "8px #000",
          paintOrder: "stroke fill",
          lineHeight: 1.15,
        }}
      >
        {card.text}
      </div>
    </AbsoluteFill>
  );
};
