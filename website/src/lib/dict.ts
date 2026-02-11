/** Strongly-typed dictionary shape matching en.json / zh.json. */

export interface CompanyDict {
  founded: string;
  headquarters: string;
  employees: string;
  funding: string;
  total_raised: string;
  last_round: string;
  valuation: string;
  investors: string;
  team: string;
  products: string;
  social: string;
  open_source: string;
  tags: string;
  overview: string;
  visit: string;
  visit_website: string;
  status: string;
  data_sources: string;
  back_to_list: string;
}

export interface SearchDict {
  title: string;
  placeholder: string;
  results: string;
  no_results: string;
  filters: string;
  category: string;
  country: string;
  clear_filters: string;
}

export interface HomeDict {
  hero_title: string;
  hero_subtitle: string;
  filter_all: string;
  sort_by: string;
  sort_funding: string;
  sort_name: string;
  sort_year: string;
  no_results: string;
}

export interface Dictionary {
  site: { title: string; description: string };
  nav: { home: string; search: string; compare: string; analytics: string; github: string };
  home: HomeDict;
  company: CompanyDict;
  search: SearchDict;
  compare: { title: string; select_prompt: string; add_company: string; remove: string; field: string; no_data: string };
  analytics: { title: string; total_companies: string; total_funding: string; open_source: string; funding_chart: string; category_chart: string; timeline_chart: string; geography_chart: string };
  footer: { description: string; contribute: string; data_updated: string };
}
