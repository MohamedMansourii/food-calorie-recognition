/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** HF Space id (owner/name); when set, recognition goes through the Space. */
  readonly VITE_SPACE_ID?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
