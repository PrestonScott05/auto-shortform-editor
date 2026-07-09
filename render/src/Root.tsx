import { Composition, staticFile } from "remotion";
import { VideoRoot } from "./VideoRoot";
import { editplanSchema, type Editplan } from "./schema";
import { VIDEO_IDS } from "./manifest";

// Minimal placeholder so compositions are valid before calculateMetadata loads real props.
const placeholder: Editplan = {
  videoId: "placeholder",
  template: "tierlist",
  fps: 30,
  width: 720,
  height: 1280,
  durationInFrames: 90,
  backgroundSrc: "",
  layout: {
    videoScale: 1.0,
    videoTranslateY: -115,
    boardTopRatio: 0.57,
    captionBaselineRatio: 0.44,
    showCaptions: true,
    captionColor: "#FFFFFF",
    captionActiveColor: "#FFE14D",
    captionFont: "Arial Black, Arial, sans-serif",
    captionSize: 44,
  },
  tiers: [
    { label: "S", color: "#FF7F7F" },
    { label: "A", color: "#FFBF7F" },
    { label: "B", color: "#FFDF7F" },
    { label: "C", color: "#FFFF7F" },
    { label: "D", color: "#BFFF7F" },
  ],
  captions: [],
  items: [],
  cutSegments: [],
  titleCard: null,
};

async function loadPlan(id: string): Promise<Editplan> {
  const res = await fetch(staticFile(`${id}/editplan.json`));
  return (await res.json()) as Editplan;
}

// Remotion composition ids allow only letters, numbers, and hyphens.
const compId = (id: string) => id.replace(/[^a-zA-Z0-9-]/g, "-");

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Generic composition used by the CLI render/still scripts via --props. Dispatches
          to the right template (tierlist/standard) based on the props it's given. */}
      <Composition
        id="Video"
        component={VideoRoot}
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

      {/* One browsable composition per video; real props loaded from public/<id>/editplan.json. */}
      {VIDEO_IDS.map((id) => (
        <Composition
          key={id}
          id={compId(id)}
          component={VideoRoot}
          schema={editplanSchema}
          defaultProps={placeholder}
          fps={30}
          width={720}
          height={1280}
          durationInFrames={90}
          calculateMetadata={async () => {
            const plan = await loadPlan(id);
            return {
              props: plan,
              durationInFrames: plan.durationInFrames,
              width: plan.width,
              height: plan.height,
              fps: plan.fps,
            };
          }}
        />
      ))}
    </>
  );
};
