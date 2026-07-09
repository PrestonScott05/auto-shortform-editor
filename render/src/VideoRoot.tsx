import type { Editplan } from "./schema";
import { TierListVideo } from "./TierListVideo";
import { StandardVideo } from "./StandardVideo";

/** Dispatches to the right template component based on the editplan's classification. */
export const VideoRoot: React.FC<Editplan> = (plan) => {
  return plan.template === "tierlist" ? <TierListVideo {...plan} /> : <StandardVideo {...plan} />;
};
