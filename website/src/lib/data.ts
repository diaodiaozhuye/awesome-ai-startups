import fs from "fs";
import path from "path";
import type { ProductDetail, ProductIndex, Stats, Category } from "./types";

const DATA_DIR = path.join(process.cwd(), "..", "data");
const PRODUCTS_DIR = path.join(DATA_DIR, "products");

export function getAllProducts(): ProductIndex {
  const indexPath = path.join(DATA_DIR, "index.json");
  const raw = fs.readFileSync(indexPath, "utf-8");
  return JSON.parse(raw) as ProductIndex;
}

export function getProductBySlug(slug: string): ProductDetail {
  if (!/^[a-z0-9-]+$/.test(slug)) {
    throw new Error(`Invalid slug: ${slug}`);
  }
  const filePath = path.join(PRODUCTS_DIR, `${slug}.json`);
  const raw = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(raw) as ProductDetail;
}

export function getStats(): Stats {
  const statsPath = path.join(DATA_DIR, "stats.json");
  const raw = fs.readFileSync(statsPath, "utf-8");
  return JSON.parse(raw) as Stats;
}

export function getAllSlugs(): string[] {
  const files = fs.readdirSync(PRODUCTS_DIR);
  return files
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.replace(".json", ""));
}

export function getCategories(): Category[] {
  const catPath = path.join(DATA_DIR, "categories.json");
  const raw = fs.readFileSync(catPath, "utf-8");
  const data = JSON.parse(raw);
  return data.categories as Category[];
}
