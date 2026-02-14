import Fuse, { type IFuseOptions } from "fuse.js";
import type { ProductIndexEntry } from "./types";

const fuseOptions: IFuseOptions<ProductIndexEntry> = {
  keys: [
    { name: "name", weight: 2 },
    { name: "name_zh", weight: 1.5 },
    { name: "company_name", weight: 1 },
    { name: "description", weight: 1 },
    { name: "description_zh", weight: 0.8 },
    { name: "category", weight: 1 },
    { name: "product_type", weight: 0.8 },
    { name: "tags", weight: 0.8 },
    { name: "country", weight: 0.5 },
    { name: "city", weight: 0.5 },
  ],
  threshold: 0.4,
  includeScore: true,
};

export function createSearchIndex(products: ProductIndexEntry[]) {
  return new Fuse(products, fuseOptions);
}
