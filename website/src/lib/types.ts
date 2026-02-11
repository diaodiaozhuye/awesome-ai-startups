export interface Headquarters {
  city: string;
  state?: string;
  country: string;
  country_code?: string;
}

export interface Funding {
  total_raised_usd?: number;
  last_round?: string;
  last_round_date?: string;
  valuation_usd?: number;
  investors?: string[];
}

export interface Founder {
  name: string;
  title?: string;
  linkedin?: string;
}

export interface Team {
  employee_count_range?: string;
  founders?: Founder[];
}

export interface Social {
  github?: string;
  twitter?: string;
  linkedin?: string;
  crunchbase?: string;
}

export interface Product {
  name: string;
  description?: string;
  url?: string;
}

export interface CompanyMeta {
  added_date?: string;
  last_updated?: string;
  sources?: string[];
  data_quality_score?: number;
}

export interface Company {
  slug: string;
  name: string;
  name_zh?: string;
  description: string;
  description_zh?: string;
  website: string;
  category: string;
  tags?: string[];
  founded_year: number;
  headquarters: Headquarters;
  funding?: Funding;
  team?: Team;
  social?: Social;
  products?: Product[];
  open_source?: boolean;
  status?: string;
  meta?: CompanyMeta;
}

export interface CompanyIndexEntry {
  slug: string;
  name: string;
  name_zh?: string;
  description: string;
  description_zh?: string;
  website: string;
  category: string;
  tags?: string[];
  founded_year: number;
  open_source?: boolean;
  status?: string;
  country: string;
  country_code: string;
  city: string;
  total_raised_usd: number;
  last_round: string;
  valuation_usd: number;
  employee_count_range: string;
}

export interface CompanyIndex {
  total: number;
  companies: CompanyIndexEntry[];
}

export interface StatEntry {
  label: string;
  count: number;
}

export interface FundingLeaderEntry {
  slug: string;
  name: string;
  total_raised_usd: number;
  valuation_usd: number;
}

export interface Stats {
  generated_at: string;
  total_companies: number;
  by_category: StatEntry[];
  by_country: StatEntry[];
  by_founded_year: StatEntry[];
  by_status: StatEntry[];
  funding_leaderboard: FundingLeaderEntry[];
  total_funding_usd: number;
  open_source_count: number;
  recently_added: { slug: string; name: string; added_date: string }[];
}

export interface Category {
  id: string;
  name: string;
  name_zh: string;
  icon: string;
}

export type Locale = "en" | "zh";
