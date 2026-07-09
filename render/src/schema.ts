import { z } from "zod";

export const wordSchema = z.object({
  w: z.string(),
  startFrame: z.number(),
  endFrame: z.number(),
});

export const captionSchema = z.object({
  text: z.string(),
  startFrame: z.number(),
  endFrame: z.number(),
  words: z.array(wordSchema),
});

export const itemSchema = z.object({
  id: z.string(),
  name: z.string(),
  image: z.string().nullable(),
  tier: z.string(),
  slotIndex: z.number(),
  introFrame: z.number(),
  ratedFrame: z.number(),
});

export const tierSchema = z.object({ label: z.string(), color: z.string() });

export const layoutSchema = z.object({
  videoScale: z.number(),
  videoTranslateY: z.number(),
  boardTopRatio: z.number(),
  captionBaselineRatio: z.number(),
  showCaptions: z.boolean().default(true),
  captionColor: z.string().default("#FFFFFF"),
  captionActiveColor: z.string().default("#FFE14D"),
  captionFont: z.string().default("Arial Black, Arial, sans-serif"),
  captionSize: z.number().default(44),
});

export const cutSegmentSchema = z.object({
  sourceStartFrame: z.number(),
  sourceEndFrame: z.number(),
  timelineStartFrame: z.number(),
});

export const titleCardSchema = z.object({
  text: z.string(),
  startFrame: z.number(),
  endFrame: z.number(),
});

export const editplanSchema = z.object({
  videoId: z.string(),
  template: z.enum(["tierlist", "standard"]).default("tierlist"),
  fps: z.number(),
  width: z.number(),
  height: z.number(),
  durationInFrames: z.number(),
  backgroundSrc: z.string(),
  layout: layoutSchema,
  tiers: z.array(tierSchema).default([]),
  captions: z.array(captionSchema),
  items: z.array(itemSchema).default([]),
  cutSegments: z.array(cutSegmentSchema).default([]),
  titleCard: titleCardSchema.nullable().default(null),
});

export type Editplan = z.infer<typeof editplanSchema>;
export type Item = z.infer<typeof itemSchema>;
