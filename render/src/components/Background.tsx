import { AbsoluteFill, OffthreadVideo, staticFile } from "remotion";
import type { Editplan } from "../schema";

/** Source talking head, scaled and shifted up so head + chest stay above the board. */
export const Background: React.FC<{ plan: Editplan }> = ({ plan }) => {
  if (!plan.backgroundSrc) return null;
  return (
    <AbsoluteFill>
      <OffthreadVideo
        src={staticFile(plan.backgroundSrc)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `translateY(${plan.layout.videoTranslateY}px) scale(${plan.layout.videoScale})`,
          transformOrigin: "center top",
        }}
      />
    </AbsoluteFill>
  );
};
