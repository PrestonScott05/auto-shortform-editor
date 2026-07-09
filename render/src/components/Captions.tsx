import { AbsoluteFill, useCurrentFrame } from "remotion";
import type { Editplan } from "../schema";

/** Word-level karaoke captions sitting just above the tier board. */
export const Captions: React.FC<{ plan: Editplan }> = ({ plan }) => {
  const frame = useCurrentFrame();
  if (plan.layout.showCaptions === false) return null;
  const active = plan.captions.find((c) => frame >= c.startFrame && frame <= c.endFrame);
  if (!active) return null;

  const y = plan.height * plan.layout.captionBaselineRatio;
  const { captionColor, captionActiveColor, captionFont, captionSize } = plan.layout;
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top: y,
          left: 0,
          width: plan.width,
          display: "flex",
          justifyContent: "center",
          flexWrap: "wrap",
          gap: 10,
          padding: "0 40px",
        }}
      >
        {active.words.map((w, i) => {
          const spoken = frame >= w.startFrame;
          return (
            <span
              key={i}
              style={{
                fontFamily: captionFont,
                fontWeight: 900,
                fontSize: captionSize,
                color: spoken ? captionActiveColor : captionColor,
                WebkitTextStroke: "6px #000",
                paintOrder: "stroke fill",
                textTransform: "uppercase",
                lineHeight: 1.1,
              }}
            >
              {w.w}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
