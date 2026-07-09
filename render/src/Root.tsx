import { Composition } from "remotion";
import { TierListVideo } from "./TierListVideo";
import { editplanSchema, type Editplan } from "./schema";

// Minimal placeholder props so the composition is browsable in Studio before a real
// editplan is supplied via --props. Real dimensions/duration come from calculateMetadata.
const placeholder: Editplan = {
  videoId: "placeholder",
  fps: 30,
  width: 720,
  height: 1280,
  durationInFrames: 90,
  backgroundSrc: "",
  layout: { videoScale: 1.0, videoTranslateY: -60, boardTopRatio: 0.5, captionBaselineRatio: 0.44, showCaptions: true },
  tiers: [
    { label: "S", color: "#FF7F7F" },
    { label: "A", color: "#FFBF7F" },
    { label: "B", color: "#FFDF7F" },
    { label: "C", color: "#FFFF7F" },
    { label: "D", color: "#BFFF7F" },
  ],
  captions: [],
  items: [],
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="TierList"
      component={TierListVideo}
      schema={editplanSchema}
      defaultProps={placeholder}
      fps={30}
      width={720}
      height={1280}
      durationInFrames={90}
      calculateMetadata={({ props }) => ({
        durationInFrames: props.durationInFrames || 90,
        width: props.width || 720,
        height: props.height || 1280,
        fps: props.fps || 30,
      })}
    />
  );
};
