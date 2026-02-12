import { getAllProducts, getCategories } from "@/lib/data";
import { getDictionary } from "@/lib/i18n";
import { ProductGrid } from "@/components/product/ProductGrid";
import type { Locale } from "@/lib/types";

export default async function HomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const dict = await getDictionary(locale as Locale);
  const { products, total } = getAllProducts();
  const categories = getCategories();

  return (
    <div>
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4">{dict.home.hero_title}</h1>
        <p className="text-lg text-muted-foreground">
          {dict.home.hero_subtitle.replace("{count}", String(total))}
        </p>
      </div>
      <ProductGrid
        products={products}
        categories={categories}
        locale={locale as Locale}
        dict={dict}
      />
    </div>
  );
}
