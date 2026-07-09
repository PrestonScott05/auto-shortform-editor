import { AbsoluteFill, OffthreadVideo, Sequence, staticFile } from "remotion";
import type { Editplan } from "./schema";
import { Captions } from "./components/Captions";
import { TitleCard } from "./components/TitleCard";

/** General-purpose template: pause-cut source video stitched back-to-back, captions,
 * an opening title card. No tier board — full-bleed vertical video. */
export const StandardVideo: React.FC<Editplan> = (plan) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {plan.cutSegments.map((seg, i) => (
        <Sequence key={i} from={seg.timelineStartFrame} durationInFrames={seg.sourceEndFrame - seg.sourceStartFrame}>
          <OffthreadVideo
            src={staticFile(plan.backgroundSrc)}
            trimBefore={seg.sourceStartFrame}
            trimAfter={seg.sourceEndFrame}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transform: `translateY(${plan.layout.videoTranslateY}px) scale(${plan.layout.videoScale})`,
              transformOrigin: "center top",
            }}
          />
        </Sequence>
      ))}
      <Captions plan={plan} />
      <TitleCard plan={plan} />
    </AbsoluteFill>
  );
};
