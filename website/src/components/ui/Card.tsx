import { cn } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}

export function Card({ children, className, hover = false }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-background p-6",
        hover && "transition-shadow hover:shadow-lg",
        className
      )}
    >
      {children}
    </div>
  );
}
