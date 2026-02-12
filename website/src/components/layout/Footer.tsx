interface FooterProps {
  dict: {
    footer: {
      description: string;
      contribute: string;
      data_updated: string;
    };
  };
}

export function Footer({ dict }: FooterProps) {
  return (
    <footer className="border-t border-border bg-muted/50 mt-16">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-muted-foreground">
            {dict.footer.description}
          </p>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <a
              href="https://github.com/diaodiaozhuye/awesome-ai-startups"
              className="hover:text-foreground transition-colors"
            >
              {dict.footer.contribute}
            </a>
          </div>
        </div>
        <p className="text-xs text-muted-foreground mt-4 text-center">
          MIT License. Data sourced from public information.
        </p>
      </div>
    </footer>
  );
}
