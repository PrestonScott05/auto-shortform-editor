import { AbsoluteFill } from "remotion";
import type { Editplan } from "./schema";
import { Background } from "./components/Background";
import { TierBoard } from "./components/TierBoard";
import { Items } from "./components/Items";
import { Captions } from "./components/Captions";

export const TierListVideo: React.FC<Editplan> = (plan) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <Background plan={plan} />
      <TierBoard plan={plan} />
      <Items plan={plan} />
      <Captions plan={plan} />
    </AbsoluteFill>
  );
};
