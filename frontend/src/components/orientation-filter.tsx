"use client";

import { RectangleHorizontal, RectangleVertical } from "lucide-react";
import { Orientation } from "@/lib/api";
import { cn } from "@/lib/utils";

type OrientationFilterProps = {
  value: Orientation | null;
  onChange: (value: Orientation | null) => void;
};

const OPTIONS: { value: Orientation; label: string; icon: typeof RectangleHorizontal }[] = [
  { value: "horizontal", label: "Horizontal", icon: RectangleHorizontal },
  { value: "vertical", label: "Vertical", icon: RectangleVertical },
];

export function OrientationFilter({ value, onChange }: OrientationFilterProps) {
  return (
    <div className="flex items-center -mr-2">
      {OPTIONS.map((option) => {
        const Icon = option.icon;
        const isActive = value === option.value;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(isActive ? null : option.value)}
            aria-pressed={isActive}
            aria-label={`Filter ${option.label} images`}
            title={`${option.label} images`}
            className={cn(
              "flex h-9 w-9 items-center justify-center rounded-lg transition-colors",
              isActive
                ? "bg-secondary text-foreground"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Icon className="h-5 w-5" />
          </button>
        );
      })}
    </div>
  );
}
