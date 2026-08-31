// Drag-and-drop + file-picker upload area.
// UX pattern ported from Rishabh1925/foodvisionai (MIT), rebuilt without
// its animation/theme dependencies and with client-side validation added.
import { useRef, useState } from "react";
import { CameraIcon } from "./icons";

const MAX_SIZE_MB = 8;
const ACCEPTED = ["image/png", "image/jpeg", "image/gif", "image/webp"];

interface Props {
  onImageSelect: (file: File) => void;
  onError: (message: string) => void;
  disabled?: boolean;
}

export default function UploadArea({ onImageSelect, onError, disabled }: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndSelect = (file: File | undefined) => {
    if (!file) return;
    if (!ACCEPTED.includes(file.type)) {
      onError("Unsupported file type. Please use a JPG, PNG, GIF or WebP image.");
      return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      onError(`File is too large. Maximum size is ${MAX_SIZE_MB} MB.`);
      return;
    }
    onImageSelect(file);
  };

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Upload a meal photo"
      onClick={() => !disabled && inputRef.current?.click()}
      onKeyDown={(e) => e.key === "Enter" && !disabled && inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        if (!disabled) validateAndSelect(e.dataTransfer.files[0]);
      }}
      className={`group cursor-pointer rounded-3xl border-2 border-dashed p-10 text-center shadow-sm transition-all duration-300 sm:p-16
        ${isDragging ? "scale-[1.01] border-emerald-500 bg-emerald-50/80 shadow-lg shadow-emerald-500/10" : "border-slate-300 bg-white/90 hover:border-emerald-400 hover:shadow-md"}
        ${disabled ? "pointer-events-none opacity-60" : ""}`}
    >
      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-100 to-teal-100 text-emerald-700 shadow-inner transition-transform duration-300 group-hover:scale-110">
        <CameraIcon className="h-8 w-8" />
      </div>
      <p className="text-lg font-semibold text-slate-700">
        Drop a meal photo here, or <span className="text-emerald-600 underline decoration-emerald-300 underline-offset-2">browse</span>
      </p>
      <p className="mt-1.5 text-sm text-slate-500">JPG, PNG, GIF or WebP — up to {MAX_SIZE_MB} MB</p>
      <div className="mt-5 flex flex-wrap justify-center gap-1.5 text-xs text-slate-400">
        {["couscous", "pizza", "ojja", "sushi", "brik", "burger"].map((s) => (
          <span key={s} className="rounded-full bg-slate-100 px-2.5 py-1 transition-colors group-hover:bg-emerald-50 group-hover:text-emerald-700">
            {s}
          </span>
        ))}
      </div>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED.join(",")}
        className="hidden"
        onChange={(e) => {
          validateAndSelect(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
    </div>
  );
}
