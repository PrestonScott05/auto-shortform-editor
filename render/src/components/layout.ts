import type { Editplan } from "../schema";

export interface Rect {
  x: number;
  y: number;
  size: number;
}

/** Geometry shared by the board and the moving items so they line up exactly. */
export function boardGeometry(plan: Editplan) {
  const boardTop = plan.height * plan.layout.boardTopRatio;
  const boardHeight = plan.height - boardTop;
  const rowH = boardHeight / plan.tiers.length;
  const labelW = 96;
  // Square cells that fill the row height and tile edge-to-edge (tiermaker style).
  const cellSize = rowH;
  return { boardTop, boardHeight, rowH, labelW, cellSize };
}

export function tierRowIndex(plan: Editplan, tier: string): number {
  return plan.tiers.findIndex((t) => t.label.toUpperCase() === tier.toUpperCase());
}

/** Resting cell rectangle for an item in its tier row + slot. */
export function cellRect(plan: Editplan, tier: string, slotIndex: number): Rect | null {
  const idx = tierRowIndex(plan, tier);
  if (idx < 0) return null;
  const g = boardGeometry(plan);
  const rowTop = g.boardTop + idx * g.rowH;
  const x = g.labelW + slotIndex * g.cellSize + g.cellSize / 2;
  const y = rowTop + g.rowH / 2;
  return { x, y, size: g.cellSize };
}

/** Center staging rectangle where a thing is shown (in full) before it is rated. */
export function stagingRect(plan: Editplan): Rect {
  return { x: plan.width / 2, y: plan.height * 0.28, size: 300 };
}
