import * as React from "react";

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "card" | "avatar" | "text";
}

const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, variant = "default", ...props }, ref) => {
    const baseClasses = "animate-pulse bg-muted";
    
    const variantClasses = {
      default: "rounded-md",
      card: "rounded-lg",
      avatar: "rounded-full",
      text: "rounded-sm",
    };
    
    return (
      <div
        ref={ref}
        className={`${baseClasses} ${variantClasses[variant]} ${className || ''}`}
        {...props}
      />
    );
  }
);
Skeleton.displayName = "Skeleton";

export { Skeleton };