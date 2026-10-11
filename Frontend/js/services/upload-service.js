import { validateImageFiles } from "../utils/validators.js";

export function validateUploads(files, options) {
  return validateImageFiles(files, options);
}

export function previewImage(file) {
  return URL.createObjectURL(file);
}

export function releasePreview(url) {
  URL.revokeObjectURL(url);
}