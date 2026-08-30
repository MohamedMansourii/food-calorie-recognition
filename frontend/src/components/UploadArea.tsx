// Drag-and-drop + file-picker upload area.
// UX pattern ported from Rishabh1925/foodvisionai (MIT), rebuilt without
// its animation/theme dependencies and with client-side validation added.
import { useRef, useState } from "react";

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
      className={`cursor-pointer rounded-2xl border-2 border-dashed p-10 text-center transition-colors sm:p-14
        ${isDragging ? "border-emerald-500 bg-emerald-50" : "border-slate-300 bg-white hover:border-emerald-400"}
        ${disabled ? "pointer-events-none opacity-60" : ""}`}
    >
      <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-2xl">
        📷
      </div>
      <p className="font-medium text-slate-700">
        Drop a meal photo here, or <span className="text-emerald-600 underline">browse</span>
      </p>
      <p className="mt-1 text-sm text-slate-500">JPG, PNG, GIF or WebP — up to {MAX_SIZE_MB} MB</p>
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
