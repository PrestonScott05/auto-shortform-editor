import { AbsoluteFill } from "remotion";
import type { Editplan } from "../schema";
import { boardGeometry } from "./layout";

/** The static tier grid: colored label column + row backgrounds, bottom half of frame. */
export const TierBoard: React.FC<{ plan: Editplan }> = ({ plan }) => {
  const g = boardGeometry(plan);
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top: g.boardTop,
          left: 0,
          width: plan.width,
          height: g.boardHeight,
          backgroundColor: "rgba(17,17,20,0.96)",
          borderTop: "3px solid rgba(255,255,255,0.15)",
        }}
      >
        {plan.tiers.map((t, i) => (
          <div
            key={t.label}
            style={{
              position: "absolute",
              top: i * g.rowH,
              left: 0,
              width: plan.width,
              height: g.rowH,
              borderBottom: "2px solid rgba(0,0,0,0.6)",
              display: "flex",
            }}
          >
            <div
              style={{
                width: g.labelW,
                height: "100%",
                backgroundColor: t.color,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontFamily: "Arial Black, Arial, sans-serif",
                fontWeight: 900,
                fontSize: Math.min(g.rowH * 0.5, 52),
                color: "#111",
              }}
            >
              {t.label}
            </div>
            <div style={{ flex: 1, backgroundColor: "rgba(40,40,46,0.9)" }} />
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
